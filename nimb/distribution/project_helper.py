# -*- coding: utf-8 -*-

test = False
nr_participants_for_testing = 2

import os
import shutil
import pandas as pd

from stats.db_processing import Table
from distribution.distribution_helper import  DistributionHelper
from distribution.distribution_ready import DistributionReady
from distribution.utilities import load_json, save_json, makedir_ifnot_exist
from distribution.distribution_definitions import get_keys_processed, DEFAULT
from classification.classify_2nimb_bids import Classify2_NIMB_BIDS
from classification.dcm2bids_helper import DCM2BIDS_helper
from setup.interminal_setup import get_userdefined_paths, get_yes_no
from distribution.manage_archive import is_archive, ZipArchiveManagement

# 2ADD:
# chk that group file includes all variables defined in the projects.json file
# chk that is ready to perform stats
# chk if stats were performed. If not - ask if stats are requested.
# if not - ask if FreeSurfer processing is requested by the user. Default - no.


'''
MUST BE ADAPTED according this this understanding:
ID description:
project_id: ID provided by the user in a grid file.
            project_id = ID1 (in PPMI nimb_id = 3378)
nimb_id   : ID based on provided MR data, 
            nimb_id name does NOT include the session; 
            e.g. ID1 (in PPMI nimb_id = 3378)
bids_id   : ID after using the dcm2bids conversion;
            it includes the session;
            e.g.: sub-ID1_ses-1 (in PPMI nimb_id = 3378_ses-1)
'''

class ProjectManager:
    '''
    projects require assessment of stage. Stages:
    - file with data is present
    - ids are present
    - BIDS is performed, files are present in the BIDS corresponding folders
    -> if not: source for IRM is defined
    - ids are processed with FreeSurfer/ nilearn, DWI
    - stats performed
    For missing stages, helper will initiate distribution for the corresponding stage
    Args:
        all_vars
    '''


    def __init__(self, all_vars):

        self.all_vars           = all_vars
        self.local_vars         = all_vars.location_vars['local']
        self.project            = all_vars.params.project
        self.project_vars       = all_vars.projects[self.project]
        self.bids_id_col        = self.project_vars['id_col']
        self.NIMB_tmp           = self.local_vars["NIMB_PATHS"]["NIMB_tmp"]

        # self.f_ids_proc_path  = os.path.join(self.materials_DIR,
        #                                      local_vars["NIMB_PATHS"]['file_ids_processed'])

        self.path_stats_dir     = all_vars.projects[self.project]["STATS_PATHS"]["STATS_HOME"]
        self.materials_dir_pt   = all_vars.projects[self.project]["materials_DIR"][1]
        self.f_ids_name         = self.local_vars["NIMB_PATHS"]['file_ids_processed']
        self.f_ids_abspath      = os.path.join(self.path_stats_dir, self.f_ids_name)
        self.tab                = Table()
        self.distrib_hlp        = DistributionHelper(self.all_vars)
        self.distrib_ready      = DistributionReady(self.all_vars)
        self.df_f_groups        = self.get_df_f_groups()
        self.DICOM_DIR          = self.project_vars["SOURCE_SUBJECTS_DIR"]
        self._ids_all           = dict()


    def get_df_f_groups(self):
        '''reading the file with IDs
            this file is provided by the user in:
            ../nimb/projects.json -> fname_groups
            file is tabular (.csv; .xlsx)
            if file is not provided or not found:
            run: self.make_default_grid()
        '''
        self.df_grid_ok = False
        f_groups = self.project_vars['fname_groups']
        dir_4stats       = makedir_ifnot_exist(self.path_stats_dir)
        if self.distrib_hlp.get_files_for_stats(dir_4stats,
                                                [f_groups,]):
            f_grid = os.path.join(dir_4stats, f_groups)
            print(f'    file with groups is present: {f_grid}')
            self.df_grid_ok = True
            return self.tab.get_df(f_grid)
        else:
            self.df_grid_ok = False
            return self.make_default_grid()


    def make_default_grid(self):
        '''creates the file default.csv
            that will be located in:
            ../nimb/projects.json -> materials_DIR -> ['local', 'PATH_2_DIR']
            ../nimb/projects.json -> STATS_PATHS -> STATS_HOME
            script will update file projects.json
        '''
        print(f'    file with groups is absent; creating default grid file in: {self.path_stats_dir}')
        df = self.tab.get_clean_df()
        df[self.bids_id_col] = ''
        self.tab.save_df(df,
            os.path.join(self.path_stats_dir, DEFAULT.default_tab_name))
        self.tab.save_df(df,
            os.path.join(self.materials_dir_pt, DEFAULT.default_tab_name))
        self.project_vars['fname_groups']   = DEFAULT.default_tab_name
        self.all_vars.projects[self.project]['fname_groups'] = DEFAULT.default_tab_name
        from setup.get_credentials_home import _get_credentials_home
        credentials_home = _get_credentials_home()
        print(f'        updating project.json at: {credentials_home}')
        save_json(self.all_vars.projects, os.path.join(credentials_home, 'projects.json'))
        return df


    def run(self):
        """
            will run the whole project starting with the file provided in the projects.json -> group
        Args:
            groups file
        Return:
            stats
        """
        print(f'    running pipeline for project: {self.project}')
        do_task = self.all_vars.params.do
        if do_task == 'fs-glm':
            self.run_fs_glm()
        if do_task == 'fs-glm-image':
            self.run_fs_glm(image = True)
        if do_task == 'fs-get-stats':
            self.get_stats_fs()
        elif do_task == 'fs-get-masks':
            self.get_masks()
        elif do_task == 'check-new':
            self.check_new()
        elif do_task == 'classify':
            self.prep_4dcm2bids_classification()
        elif do_task == 'classify-dcm2bids':
            self.classify_with_dcm2bids()

        self.get_ids_bids()
        self.get_ids_all()


    def check_new(self):
        print('checking for new subject to be processed')
        self.distrib_hlp.check_new()


    '''
    CLASSIFICATION related scripts
    '''
    def prep_4dcm2bids_classification(self):
        src_dir = self.project_vars['SOURCE_SUBJECTS_DIR'][1]
        ls_source_dirs = self.get_content(src_dir)
        print(f'   there are {len(self.get_content(src_dir))} files found in {src_dir} \
            expected to contain MRI data for project {self.project}')
        if test:
            ls_source_dirs = self.get_content(src_dir)[:nr_participants_for_testing]

        self.prep_dirs(["SOURCE_BIDS_DIR",
                    "SOURCE_SUBJECTS_DIR"])

        if len(ls_source_dirs) > 0:
            multi_T1     = self.local_vars['FREESURFER']['multiple_T1_entries']
            add_flair_t2 = self.local_vars['FREESURFER']['flair_t2_add']
            fix_spaces   = self.all_vars.params.fix_spaces
            for _dir in ls_source_dirs:
                print(f'   classifying folder: {_dir}')
                is_classified, nimb_classified = Classify2_NIMB_BIDS(self.project,
                                                                src_dir, self.NIMB_tmp, [_dir,],
                                                                fix_spaces, True,
                                                                multi_T1, add_flair_t2).run()
                if is_classified:
                    self.classify_with_dcm2bids(nimb_classified)
                    '''
                    def check_is_subject_session_in_grid:
                        if subject_session not in grid:
                            add subject_session to be processed
                            populate new_subjects.json with dcm2bids versions
                            if dcm2bids not efficient:
                                populate new_subjects with raw DCM
                    '''

#            self.get_ids_classified()
#            self.populate_grid()
        else:
            print(f'    folder with source subjects {src_dir} is empty')


    def id_is_bids_converted(self, nimb_id, ses):
        bids_dir_location = self.project_vars['SOURCE_BIDS_DIR'][0]
        convert_2bids = False
        if bids_dir_location == 'local':
            bids_dir_abspath = self.project_vars['SOURCE_BIDS_DIR'][1]
            ls_bids_converted = os.listdir(bids_dir_abspath)
            if nimb_id not in ls_bids_converted:
                convert_2bids = True
            elif ses not in os.listdir(os.path.join(bids_dir_abspath, nimb_id)):
                convert_2bids = True
        else:
            print(f'    bids folder located remotely: {bids_dir_location}')
        return convert_2bids


    def classify_with_dcm2bids(self, nimb_classified = False):
        if not nimb_classified:
            src_dir = self.project_vars['SOURCE_SUBJECTS_DIR'][1]
            try:
                nimb_classified = load_json(os.path.join(
                    src_dir,
                    DEFAULT.f_nimb_classified))
            except Exception as e:
                print(e)
                print('    nimb_classified file cannot be found at: {src_dir}')

        if nimb_classified:
            ls_nimb_ids = [i for i in nimb_classified]
            if test:
                print(f'        TESTING with {nr_participants_for_testing} participants')
                ls_nimb_ids = [i for i in nimb_classified][:nr_participants_for_testing]
            for nimb_id in ls_nimb_ids[:1]:#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                ls_sessions = [i for i in nimb_classified[nimb_id] if i not in ('archived',)]
                for ses in ls_sessions:
                    convert_2bids = self.id_is_bids_converted(nimb_id, ses)
                    if convert_2bids:
                        print('    ready to convert to BIDS')
                        bids_classified = self.convert_with_dcm2bids(nimb_id,
                                                            ses,
                                                            nimb_classified[nimb_id])
                        print(f'        bids_classified is: {bids_classified}')


    def convert_with_dcm2bids(self, nimb_id, ses, nimb_classified_per_id):
        print(f'    starting dcm2bids classification for id: {nimb_id} session: {ses}')
        return DCM2BIDS_helper(self.project_vars,
                        self.project,
                        nimb_classified_per_id = nimb_classified_per_id,
                        DICOM_DIR = self.DICOM_DIR,
                        tmp_dir = self.NIMB_tmp).run(nimb_id, ses)


    def get_dir_with_raw_MR_data(self, src_dir, _dir):
        if os.path.isdir(os.path.join(src_dir, _dir)):
            return src_dir, list(_dir)
        elif _dir.endswith('.zip'):
            self.dir_new_subjects = self.local_vars["NIMB_PATHS"]["NIMB_NEW_SUBJECTS"]
            ls_initial = self.get_content(self.dir_new_subjects)
            self.extract_from_archive(src_dir, _dir)
            ls_dir_4bids2dcm = [i for i in self.get_content(self.dir_new_subjects) if i not in ls_initial]
            return self.dir_new_subjects, ls_dir_4bids2dcm


    def extract_from_archive(self, src_dir, _dir):
        tmp_err_dir  = os.path.join(self.NIMB_tmp, 'tmp_err_classification')
        makedir_ifnot_exist(tmp_err_dir)
        dir_2extract = self.dir_new_subjects
        tmp_dir_2extract = ''
        if self.project in DEFAULT.project_ids:
            tmp_dir_2extract = os.path.join(self.NIMB_tmp, DEFAULT.nimb_tmp_dir)
            makedir_ifnot_exist(tmp_dir_2extract)
            dir_2extract = tmp_dir_2extract
        ZipArchiveManagement(
            os.path.join(src_dir, _dir),
            path2xtrct = dir_2extract,
            path_err   = tmp_err_dir)
        if tmp_dir_2extract:
            project_dir = os.path.join(tmp_dir_2extract,
                                        DEFAULT.project_ids[self.project]["dir_from_source"])
            if os.path.exists(project_dir):
                print(f'    this is default project;\
                    the corresponding default folder was created in: {project_dir}')
                ls_content = self.get_content(project_dir)
                for _dir in ls_content:
                    nr_left_2cp = len(ls_content[ls_content.index(_dir):])
                    print(f'    number of folders left to copy: {nr_left_2cp}')
                    src = os.path.join(project_dir, _dir)
                    dst = os.path.join(self.dir_new_subjects, _dir)
                    print(f'    copying folder: {src} to {dst}')
                    shutil.copytree(src, dst)
            else:
                print(f'    the expected folder: {project_dir} is missing')
            print(f'    removing temporary folder: {tmp_dir_2extract}')
            shutil.rmtree(tmp_dir_2extract, ignore_errors=True)
        if len(self.get_content(tmp_err_dir)) == 0:
            shutil.rmtree(tmp_err_dir, ignore_errors=True)


    '''
    PROCESSING related scripts
    '''
    def run_fs_glm(self, image = False):
        '''
        REQUIRES ADJUSTMENT
        '''
        fs_glm_dir   = self.project_vars['STATS_PATHS']["FS_GLM_dir"]
        # fs_glm_dir   = self.stats_vars["STATS_PATHS"]["FS_GLM_dir"]
        fname_groups = self.project_vars['fname_groups']
        if DistributionReady(self.all_vars).chk_if_ready_for_fs_glm():
            GLM_file_path, GLM_dir = DistributionHelper(self.all_vars).prep_4fs_glm(fs_glm_dir,
                                                                        fname_groups)
            FS_SUBJECTS_DIR = self.vars_local['FREESURFER']['FS_SUBJECTS_DIR']
            DistributionReady(self.all_vars).fs_chk_fsaverage_ready(FS_SUBJECTS_DIR)
            if GLM_file_path:
                print('    GLM file path is:',GLM_file_path)
                self.vars_local['PROCESSING']['processing_env']  = "tmux"
                schedule_fsglm = Scheduler(self.vars_local)
                cd_cmd = 'cd {}'.format(path.join(self.NIMB_HOME, 'processing', 'freesurfer'))
                cmd = f'{self.py_run_cmd} fs_glm_runglm.py -project {self.project} -glm_dir {GLM_dir}'
                schedule_fsglm.submit_4_processing(cmd, 'fs_glm','run_glm', cd_cmd)
        if not "export_screen" in self.vars_local['FREESURFER']:
            print("PLEASE check that you can export your screen or you can run screen-based applications. \
                                This is necessary for Freeview and Tksurfer. \
                                Check the variable: export_screen in file {}".format(
                                    "credentials_path.py/nimb/local.json"))
        elif self.vars_local['FREESURFER']["export_screen"] == 0:
            print("Current environment is not ready to export screen. Please define a compute where the screen can \
                                be used for FreeSurfer Freeview and tksurfer")
        if DistributionReady(self.all_vars).fs_ready():
            print('before running the script, remember to source $FREESURFER_HOME')
            cmd = '{} fs_glm_extract_images.py -project {}'.format(self.py_run_cmd, self.project)
            cd_cmd = 'cd '+path.join(self.NIMB_HOME, 'processing', 'freesurfer')
            self.schedule.submit_4_processing(cmd, 'fs_glm','extract_images', cd_cmd)


    def get_stats_fs(self):
        if self.distrib_ready.chk_if_ready_for_stats():
            PROCESSED_FS_DIR = self.distrib_hlp.prep_4fs_stats()
            if PROCESSED_FS_DIR:
                print('    ready to extract stats from project helper')
        #         self.send_2processing('fs-get-stats')


    def get_masks(self):
        if self.distrib_ready.fs_ready():
            print('running mask extraction')
            # self.send_2processing('fs-get-masks')


    def send_2processing(self, task):
        from processing.schedule_helper import Scheduler
        python_run = self.local_vars["PROCESSING"]["python3_run_cmd"]
        NIMB_HOME  = self.local_vars["NIMB_PATHS"]["NIMB_HOME"]
        if task == 'process':
            schedule = Scheduler(self.local_vars)
            cd_cmd   = f'cd {os.path.join(NIMB_HOME, "processing")}'
            cmd      = f'{python_run} processing_run.py -project {self.project}'
            process_type = 'nimb_processing'
            subproc = 'run'
        if task == 'fs-get-stats':
            self.local_vars['PROCESSING']['processing_env']  = "tmux" #must be checked if works with slurm
            schedule = Scheduler(self.local_vars)
            dir_4stats = self.project_vars['STATS_PATHS']["STATS_HOME"]
            cd_cmd   = f'cd {os.path.join(NIMB_HOME, "processing", "freesurfer")}'
            cmd      = f'{python_run} fs_stats2table.py -project {self.project} -stats_dir {dir_4stats}'
            process_type = 'fs_stats'
            subproc = 'get_stats'
        if task == 'fs-get-masks':
            cd_cmd   = f'cd {os.path.join(NIMB_HOME, "processing", "freesurfer")}'
            cmd      = f'{python_run} run_masks.py -project {self.project}'
            process_type = 'fs'
            subproc = 'run_masks'
        print('    sending to scheduler')
        schedule.submit_4_processing(cmd, process_type, subproc, cd_cmd)


    def get_content(self, path2chk):
        return os.listdir(path2chk)


    def prep_dirs(self, ls_dirs):
        ''' define dirs required for BIDS classification
        '''
        print('    it is expected that SOURCE_SUBJECTS_DIR contains unarchived folders or archived (zip) files with MRI data')
        for _dir2chk in ls_dirs:
            _dir = self.project_vars[_dir2chk][1]
            if not os.path.exists(_dir):
                self.project_vars[_dir2chk][0] = 'local'
                self.project_vars[_dir2chk][1] = get_userdefined_paths(f'{_dir2chk} folder',
                                                                      _dir, '',
                                                                      create = False)
                from setup.get_credentials_home import _get_credentials_home
                self.all_vars.projects[self.project] = self.project_vars
                save_json(self.all_vars.projects, os.path.join(_get_credentials_home(), 'projects.json'))


    def get_ids_all(self):
        """
            extract bids ids from the file groups provided by user
        """
        if self.f_ids_in_dir(self.path_stats_dir):
            self._ids_all = load_json(os.path.join(self.path_stats_dir, self.f_ids_name))


    def f_ids_in_dir(self, path_2groups_f):
        self.f_ids_abspath = os.path.join(path_2groups_f, self.f_ids_name)
        if os.path.exists(self.f_ids_abspath):
            return True
        else:
            return self._ids_file_try2make()


    def _ids_file_try2make(self):
        if self.df_grid_ok:
            bids_ids = self.df_f_groups[self.bids_id_col]

            if len(bids_ids) > 0:
                _ids = dict()
                self.make_reading_dirs()
                for bids_id in bids_ids:
                    _ids = self.populate_ids_all(_ids, bids_id)
                self.create_file_ids(_ids)

            if os.path.exists(self.f_ids_abspath):
                return True
            else:
                print('    could not create the file with ids')
                True
        else:
            return False


    def make_reading_dirs(self):
        SOURCE_BIDS_DIR       = self.project_vars['SOURCE_BIDS_DIR'][1]
        SOURCE_SUBJECTS_DIR   = self.project_vars['SOURCE_SUBJECTS_DIR'][1]
        PROCESSED_FS_DIR      = self.project_vars['PROCESSED_FS_DIR'][1]
        PROCESSED_NILEARN_DIR = self.project_vars['PROCESSED_NILEARN_DIR'][1]
        PROCESSED_DIPY_DIR    = self.project_vars['PROCESSED_DIPY_DIR'][1]
        self.keys2chk = {
            'src'    : SOURCE_SUBJECTS_DIR,
            'fs'     : PROCESSED_FS_DIR,
            'nilearn': PROCESSED_NILEARN_DIR,
            'dipy'   : PROCESSED_DIPY_DIR,
                            }
        self.content_dirs = {}
        for key in self.keys2chk:
            dir2chk = self.keys2chk[key]
            if os.path.exists(dir2chk):
                self.content_dirs[key] = self.get_content(dir2chk)


    def populate_ids_all(self, _ids, bids_id):
        '''tries to populate the _ids_file with corresponding FreeSurfer processed folder
            f_ids includes only the archived folder names
        Args:
            _ids: dict() with bids_ids as keys and 'fs': fs_ids as as values
        Return:
            newly populated dict()
        '''
        '''
        2DO
        currently - check if dirs are on local
        must add if dirs are on remote
        '''
        _ids[bids_id] = dict()

        for key in self.keys2chk:
            dir2chk     = self.keys2chk[key][1]
            content2chk = self.content_dirs[key]
            key_nimb    = get_keys_processed(key)
            _ids[bids_id][key_nimb] = ''
            for _dir in content2chk:
                if bids_id in _dir:
                    _ids[bids_id][key_nimb] = _dir
        return _ids


    '''
    ID related scripts
    '''
    def get_ids_bids(self):
        """
            extract bids ids from the file groups provided by user
            !! ATTENTION - bids_id must also comprise the session name
            as defined in the sessions folder of BIDS structure
            current abbreviation is ses_00; this variable must be changed
            to allow users to define it
        """
        print(f'    reading IDs for project {self.project}')
        if self.df_grid_ok:
            self._ids_bids = list(self.df_f_groups[self.bids_id_col])
            print(f'    list of ids that are present: {self._ids_bids}')
            print(f'    checking for missing participants')
            self.chk_missing_participants()
        else:
            self.prep_4dcm2bids_classification()


    def chk_missing_participants(self):
        self.get_ids_all()
        if not self._ids_all:
            print(f'    file with ids is missing: {self._ids_all}')
            if self.get_ids_classified():
                self.populate_f_ids_from_nimb_classified()
            else:
                self.prep_4dcm2bids_classification()


    def get_ids_classified(self):
        src_subjects_dir = self.project_vars["SOURCE_SUBJECTS_DIR"][1]
        new_subjects_dir = self.local_vars["NIMB_PATHS"]["NIMB_NEW_SUBJECTS"]
        f_class_abspath_in_src = os.path.join(src_subjects_dir, DEFAULT.f_nimb_classified)
        f_class_abspath_in_new = os.path.join(new_subjects_dir, DEFAULT.f_nimb_classified)

        if os.path.exists(f_class_abspath_in_src):
            self._ids_classified = load_json(f_class_abspath_in_src)
        elif os.path.exists(f_class_abspath_in_new):
            self._ids_classified = load_json(f_class_abspath_in_new)
        else:
            print('    file with nimb classified is missing')
            self._ids_classified = dict()


    def populate_f_ids_from_nimb_classified(self):
        self.get_ids_all()
        self.bids_ids_new = list()
        # print(self._ids_classified)
        for src_id in self._ids_classified:
            for session in self._ids_classified[src_id]:
                bids_id = f'{src_id}_{session}'
                self.bids_ids_new.append(bids_id)

                if bids_id not in self._ids_all:
                    self._ids_all[bids_id] = dict()
                self._ids_all[bids_id][get_keys_processed('src')] = src_id
        self.create_file_ids(self._ids_all)


    def create_file_ids(self, _ids):
        print('creating file with groups {}'.format(self.f_ids_abspath))
        save_json(_ids, self.f_ids_abspath)
        save_json(_ids, os.path.join(self.materials_dir_pt, self.f_ids_name))


    '''
    GRID related scripts
    '''
    def populate_grid(self):
        # get grid
        # populate
        df = self.get_df_f_groups()
        if self._ids_classified:
            self.populate_f_ids_from_nimb_classified()

            for bids_id in self.bids_ids_new:
                if bids_id not in df[self.bids_id_col]:
                    df.loc[-1] = df.columns.values
                    for col in df.columns.tolist():
                        df.at[-1, col] = ''
                    df.at[-1, self.bids_id_col] = bids_id
                    df.index = range(len(df[self.bids_id_col]))
            # self.tab.save_df(df,
            #     os.path.join(self.path_stats_dir, self.project_vars['fname_groups']))
            print('    NIMB ready to initiate processing of data')
            self.send_2processing('process')
        else:
            print('   file with nimb classified is missing')


    def populate_ids_all_from_remote(self, _ids, bids_id):
        '''
        fs_processed_col = 'path_freesurfer711'
        irm_source_col = 'path_source'
        df = pd.read_csv(path.join(self.materials_dir_pt, self.projects[self.proj>
        ls_miss = df[irm_source_col].tolist()
        remote_loc = self.get_processing_location('freesurfer')
        remote_loc = remote_loc[0]
        check if self.fs_ready(remote_loc)
        host_name = ""
        if self.fs_ready():
           # 1. install required library and software on the local computer, including freesurfer
           self.setting_up_local_computer()
           # install freesurfer locally
           setup = SETUP_FREESURFER(self.locations)
        SSHHelper.upload_multiple_files_to_cluster(remote_loc, ls_miss, self.locations[remote_loc]["NIMB_PATHS"]["NIMB_tmp"]
        else:
            logger.debug("Setting up the remote server")
            # --get the name and the address of remote server
            for machine_name, machine_config in self.locations.items():
                if machine_name == 'local': # skip
                    continue
                # a. check the fs_install == 1
                if machine_config['FREESURFER']['FreeSurfer_install'] == 1:
                    host_name = self.projects['LOCATION'][machine_name]
                    self.setting_up_remote_linux_with_freesurfer(host_name=host_name)

        # continue working from below
        # must set SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR before calling: get from project
        # project name get from where?

        machine_PROCESSED_FS_DIR, PROCESSED_FS_DIR = self.get_PROCESSED_FS_DIR()
        machine_SOURCE_SUBJECTS_DIR, SOURCE_SUBJECTS_DIR = self.get_SOURCE_SUBJECTS_DIR()

        self.run_copy_subject_to_cluster(Project)
        logger.debug('Cluster analysis started')
        logger.debug("Cluster analysing running....")
        self.run_processing_on_cluster_2()
        '''

        # return _ids
        pass
