# -*- coding: utf-8 -*-


import os
import shutil
import pandas as pd

from stats.db_processing import Table
from distribution.distribution_helper import  DistributionHelper
from distribution.distribution_ready import DistributionReady
from distribution.utilities import load_json, save_json, makedir_ifnot_exist
from distribution.distribution_definitions import get_keys_processed, DEFAULT
from classification.classify_2nimb_bids import Classify2_NIMB_BIDS
from classification.dcm2bids_helper import DCM2BIDS_helper, make_bids_id
from setup.interminal_setup import get_userdefined_paths, get_yes_no
from distribution.manage_archive import is_archive, ZipArchiveManagement
from distribution.logger import LogLVL

# 2ADD:
# chk that group file includes all variables defined in the projects.json file
# chk that is ready to perform stats
# chk if stats were performed. If not - ask if stats are requested.
# if not - ask if FreeSurfer processing is requested by the user. Default - no.


'''
MUST BE ADAPTED according to this understanding:
ID description:
_id_source:  ID as defined in a database.
            It can be same as _id_project, but it is NOT expected
            that source_id will be used for stats
            e.g., in PPMI source_id = 3378
            these IDs are mainly folders of IDs with multiple sessions inside
_id_bids   : ID after using the dcm2bids conversion;
            it is automatically created with the make_bids_id function
            it includes: dcm2bids prefix + source_id + session;
            current dcm2bids prefix = "sub-"
            _id_bids = sub-3378_ses-1
_id_project: ID provided by the user in a grid file.
            e.g., in PPMI _id_project = 3378_session1
            _id_project is expected to be used for stats analysis
            _id_project can be same as _id_bids, if edited by the user
'''



class ProjectManager:
    '''
    projects require assessment of stage. Stages:
    - file with data is present
    - ids are present
    - BIDS is performed, files are present in the BIDS corresponding folders
    -> if not: source for IRM is defined
    - ids are processed with FreeSurfer/ nilearn/ dipy
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
        self._ids_project_col   = self.project_vars['proj_id_col']
        self._ids_bids_col        = self.project_vars['id_col']
        self.NIMB_tmp           = self.local_vars["NIMB_PATHS"]["NIMB_tmp"]

        # self.f_ids_proc_path  = os.path.join(self.materials_DIR,
        #                                      local_vars["NIMB_PATHS"]['file_ids_processed'])

        self.path_stats_dir     = makedir_ifnot_exist(
                                    all_vars.projects[self.project]["STATS_PATHS"]["STATS_HOME"])
        self.materials_dir_pt   = all_vars.projects[self.project]["materials_DIR"][1]
        self.f_ids_name         = self.local_vars["NIMB_PATHS"]['file_ids_processed']
        self.f_ids_abspath      = os.path.join(self.path_stats_dir, self.f_ids_name)
        self.tab                = Table()
        self.distrib_hlp        = DistributionHelper(self.all_vars)
        self.distrib_ready      = DistributionReady(self.all_vars)
        self.df_f_groups        = self.get_df_f_groups()
        self.DICOM_DIR          = self.project_vars["SOURCE_SUBJECTS_DIR"]
        self._ids_all           = dict()

        self.test               = all_vars.params.test
        self.nr_for_testing     = 2


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
        if self.distrib_hlp.get_files_for_stats(self.path_stats_dir,
                                                [f_groups,]):
            f_grid = os.path.join(self.path_stats_dir, f_groups)
            print(f'    file with groups is present: {f_grid}')
            self.df_grid_ok = True
            df_grid = self.tab.get_df(f_grid)
        else:
            self.df_grid_ok = False
            df_grid = self.make_default_grid()
        self._ids_project = df_grid[self._ids_project_col]
        return df_grid


    def make_default_grid(self):
        '''creates the file default.csv
            that will be located in:
            ../nimb/projects.json -> materials_DIR -> ['local', 'PATH_2_DIR']
            ../nimb/projects.json -> STATS_PATHS -> STATS_HOME
            script will update file projects.json
        '''
        print(f'    file with groups is absent; creating default grid file in: {self.path_stats_dir}')
        df = self.tab.get_clean_df()
        df[self._ids_project_col] = ''
        df[self._ids_bids_col] = ''
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

        self.check_processed()
        self.process_mri_data()
        self.extract_statistics()


    def check_new(self):
        print('checking for new subject to be processed')
        self.distrib_hlp.check_new()

    def check_processed(self):
        """
        SITUATIONS:
            only SOURCE_DIR is provided:
                must populate grid.csv
            grid.csv and SOURCE_DIR are provided, _id_projects are different
            grid.csv _id_projects are NOT _id_bids
        ALGO:
            grid and self._ids_project already defined by self.get_df_f_groups()

            if not exists(f_ids.json):
                create f_ids.json
                f_ids.json:{
                    "_id_bids": {
                        "project"    : "ID_in_file_provided_by_user_for_GLM_analysis.tsv",
                        "source"     : "ID_in_source_dir_or_zip_file",
                        "freesurfer" : "ID_after_freesurfer_processing.zip/nii.gz",
                        "nilearn"    : "ID_after_nilearn_processing.zip/nii.gz",
                        "dipy"       : "ID_after_dipy_processing.zip/nii.gz"
                            }
                    }

s            for _id_project in _ids_project:
                _id_bids = get_id_bids(_id_project)
                if _id_bids:
                    for APP in _id_bids:
                        if not APP:
                            add _id_bids to new_subjects.json for processing
                    new_subjects.json = True

            get_id_bids(_id_project):
                if _id_project in f_ids.json:
                    _id_bids = i from f_ids.json for the _id_project
                    chk _id_bids in SOURCE_BIDS_DIR and validate BIDS
                else:
                    if _id_project has BIDS format:
                        if _id_project in SOURCE_BIDS_DIR and validate BIDS:
                        _id_bids = _id_project
                    else:
                        _id_bids = classify_2_bids(_id_project)
                    update f_ids.json with _id_bids for _id_project

            classify_2_bids(_id_project):
                if not nimb_classified.json exists:
                    classify_2nimb SOURCE_DIR
                elif _id_project not in nimb_classified.json:
                    if _id_project in SOURCE_DIR:
                        classify_2nimb SOURCE_DIR
                    else:
                        update f_ids.json with "source" for _id_project as "missing"
                else:
                    _id_bids = classify 2 bids for _id_project

            if new_subjects.json:
                if ast user if to initiate processing is True:
                    initiate processing
        """
        self.get_ids_bids()


    '''
    ID related scripts
    '''

    def get_ids_bids(self):
        """ extract bids ids from the file groups provided by user
        """

        self._ids_missing = list()
        print(f'    reading IDs for project {self.project}')
        if self.df_grid_ok:
            self._ids_bids = list(self.df_f_groups[self._ids_bids_col])
            print(f'{" " * 4}list of ids that are present: {self._ids_bids}')
            self.get_ids_all()
            if self._ids_all:
                self.add_missing_participants()
            else:
                print(f'    file with ids is missing: {self._ids_all}')
                self.populate_f_ids_from_nimb_classified()
            self.chk_ids_processed()
        else:
            if self._ids_missing:
                print(f'{LogLVL.lvl1}missing ids: {self._ids_missing}')
            self.prep_4dcm2bids_classification()


    def get_ids_all(self):
        """
            extract bids ids from the file groups provided by user
        """
        if self.f_ids_in_dir(self.path_stats_dir):
            self._ids_all = load_json(os.path.join(self.path_stats_dir, self.f_ids_name))
        else:
            self._ids_all = dict()
        # print(f'{LogLVL.lvl1} ids all are: {self._ids_all}')


    def f_ids_in_dir(self, path_2groups_f):
        self.f_ids_abspath = os.path.join(path_2groups_f, self.f_ids_name)
        if os.path.exists(self.f_ids_abspath):
            return True
        else:
            return self._ids_file_try2make()


    def _ids_file_try2make(self):
        if self.df_grid_ok:
            _ids_bids = self.df_f_groups[self._ids_bids_col]
            proj_ids = self.df_f_groups[self._ids_project_col]

            if len(_ids_bids) > 0:
                _ids = dict()
                self.make_reading_dirs()
                for _id_bids in _ids_bids:
                    _ids = self.populate_ids_all(_ids, _id_bids)
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


    def populate_ids_all(self, _ids, _id_bids):
        '''tries to populate the _ids_file with corresponding FreeSurfer processed folder
            f_ids includes only the archived folder names
        Args:
            _ids: dict() with _ids_bids as keys and 'fs': fs_ids as as values
        Return:
            newly populated dict()
        '''
        '''
        2DO
        currently - check if dirs are on local
        must add if dirs are on remote
        '''
        _ids[_id_bids] = dict()

        for key in self.keys2chk:
            dir2chk     = self.keys2chk[key][1]
            content2chk = self.content_dirs[key]
            key_nimb    = get_keys_processed(key)
            _ids[_id_bids][key_nimb] = ''
            for _dir in content2chk:
                if _id_bids in _dir:
                    _ids[_id_bids][key_nimb] = _dir
        return _ids


    def chk_ids_processed(self):
            '''
            def check_is_subject_session_in_grid:
                if subject_session not in grid:
                    add subject_session to be processed
                    populate new_subjects.json with dcm2bids versions
                    if dcm2bids not efficient:
                        populate new_subjects with raw DCM
                self.get_ids_classified()
                self.populate_grid()
            '''
            print(f'{LogLVL.lvl1}checking processed ids')
            # for _id_bids in self._ids_all:
            #     for app in self._ids_all[_id_bids]:
            #         print(app)

            # self.prep_4dcm2bids_classification()


    def add_missing_participants(self):
        '''chk if any _id_src from _ids_nimb_classified
            are missing from _ids_all[_id_bids]['source']
            if missing - will add _id_src to _ids_all
            will populate list() self._ids_missing
        '''
        self.get_ids_classified()
        if self._ids_nimb_classified:
            print(f'{LogLVL.lvl1}checking missing participants')
            # print(f'{LogLVL.lvl1} ids classified: {self._ids_nimb_classified}')
            # print(f'{LogLVL.lvl1} ids all: {self._ids_all}')
            ids_all_source = [self._ids_all[i]['source'] for i in self._ids_all.keys()]
            self._ids_missing = [i for i in self._ids_nimb_classified.keys() if i not in ids_all_source]
            for _id_src in self._ids_missing:
                for session in self._ids_nimb_classified[_id_src]:
                    _id_bids, _ = make_bids_id(_id_src, session)
                    self._ids_all[_id_bids]['source'] = _id_src
        else:
            print(f'{LogLVL.lvl1}nimb_classified.json is missing')
        return self._ids_missing


    def get_ids_classified(self):
        src_subjects_dir = self.project_vars["SOURCE_SUBJECTS_DIR"][1]
        new_subjects_dir = self.local_vars["NIMB_PATHS"]["NIMB_NEW_SUBJECTS"]
        f_class_abspath_in_src = os.path.join(src_subjects_dir, DEFAULT.f_nimb_classified)
        f_class_abspath_in_new = os.path.join(new_subjects_dir, DEFAULT.f_nimb_classified)

        if os.path.exists(f_class_abspath_in_src):
            self._ids_nimb_classified = load_json(f_class_abspath_in_src)
        elif os.path.exists(f_class_abspath_in_new):
            self._ids_nimb_classified = load_json(f_class_abspath_in_new)
        else:
            print(f'{" " * 4} file {DEFAULT.f_nimb_classified} is missing in: {src_subjects_dir} or {new_subjects_dir}')
            print(f'{" " * 4} must initiate nimb classifier') #!! initiate classify_2nimb_bids.py
            self._ids_nimb_classified = dict()


    def populate_f_ids_from_nimb_classified(self):
        self._ids_bids_new = list()
        print(f'{LogLVL.lvl1} ids classified: {self._ids_nimb_classified}')
        for _id_src in self._ids_nimb_classified:
            for session in self._ids_nimb_classified[_id_src]:
                _id_bids, _ = make_bids_id(_id_src, session)
                # _id_bids = f'{_id_src}_{session}' #!!!!!!!!!!!!!!!!!!!!!!!!
                self._ids_bids_new.append(_id_bids)

                if _id_bids not in self._ids_all:
                    self._ids_all[_id_bids] = dict()
                self._ids_all[_id_bids][get_keys_processed('src')] = src_id
        self.create_file_ids(self._ids_all)


    def create_file_ids(self, _ids):
        print('creating file with groups {}'.format(self.f_ids_abspath))
        save_json(_ids, self.f_ids_abspath)
        save_json(_ids, os.path.join(self.materials_dir_pt, self.f_ids_name))


    '''
    CLASSIFICATION related scripts
    '''
    def prep_4dcm2bids_classification(self):
        src_dir = self.project_vars['SOURCE_SUBJECTS_DIR'][1]
        ls_source_dirs = self.get_content(src_dir)
        print(f'   there are {len(self.get_content(src_dir))} files found in {src_dir} \
            expected to contain MRI data for project {self.project}')
        if self.test:
            ls_source_dirs = self.get_content(src_dir)[:self.nr_for_testing]

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
        else:
            print(f'    folder with source subjects {src_dir} is empty')


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
            if self.test:
                print(f'        TESTING with {self.nr_for_testing} participants')
                ls_nimb_ids = [i for i in nimb_classified][:self.nr_for_testing]
            for nimb_id in ls_nimb_ids:
                ls_sessions = [i for i in nimb_classified[nimb_id] if i not in ('archived',)]
                for ses in ls_sessions:
                    convert_2bids = self.id_is_bids_converted(nimb_id, ses)
                    if convert_2bids:
                        print('    ready to convert to BIDS')
                        self.bids_classified = self.convert_with_dcm2bids(nimb_id,
                                                            ses,
                                                            nimb_classified[nimb_id])
                        print(f'        bids_classified is: {self.bids_classified}')


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


    def convert_with_dcm2bids(self, nimb_id, ses, nimb_classified_per_id):
        print(f'    starting dcm2bids classification for id: {nimb_id} session: {ses}')
        return DCM2BIDS_helper(self.project_vars,
                        self.project,
                        nimb_classified_per_id = nimb_classified_per_id,
                        DICOM_DIR = self.DICOM_DIR,
                        tmp_dir = self.NIMB_tmp).run(nimb_id, ses)


    def get_content(self, path2chk):
        return os.listdir(path2chk)


    '''
    PROCESSING related scripts
    '''
    def process_mri_data(self):
        print("checking for processing")


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


    '''
    EXTRACT STATISTICS related scripts
    '''
    def extract_statistics(self):
        print("extracting statistics")


    def get_stats_fs(self):
        if self.distrib_ready.chk_if_ready_for_stats():
            PROCESSED_FS_DIR = self.distrib_hlp.prep_4fs_stats()
            if PROCESSED_FS_DIR:
                print('    ready to extract stats from project helper')
        #         self.send_2processing('fs-get-stats')


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


    '''
    GRID related scripts
    '''
    def populate_grid(self):
        # get grid
        # populate
        df = self.get_df_f_groups()
        if self._ids_nimb_classified:
            self.get_ids_all()
            self.populate_f_ids_from_nimb_classified()

            for _id_bids in self._ids_bids_new:
                if _id_bids not in df[self._ids_bids_col]:
                    df.loc[-1] = df.columns.values
                    for col in df.columns.tolist():
                        df.at[-1, col] = ''
                    df.at[-1, self._ids_bids_col] = _id_bids
                    df.index = range(len(df[self._ids_bids_col]))
            # self.tab.save_df(df,
            #     os.path.join(self.path_stats_dir, self.project_vars['fname_groups']))
            print('    NIMB ready to initiate processing of data')
            self.send_2processing('process')
        else:
            print('   file with nimb classified is missing')


    def populate_ids_all_from_remote(self, _ids, _id_bids):
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



    """NEXT 2 scripts are probably not needed anymore, as
    extraction to a temporary folder was integrated integrated into
    DCM2BIDS_helper
    """
    # def get_dir_with_raw_MR_data(self, src_dir, _dir):
    #     if os.path.isdir(os.path.join(src_dir, _dir)):
    #         return src_dir, list(_dir)
    #     elif _dir.endswith('.zip'):
    #         self.dir_new_subjects = self.local_vars["NIMB_PATHS"]["NIMB_NEW_SUBJECTS"]
    #         ls_initial = self.get_content(self.dir_new_subjects)
    #         self.extract_from_archive(src_dir, _dir)
    #         ls_dir_4bids2dcm = [i for i in self.get_content(self.dir_new_subjects) if i not in ls_initial]
    #         return self.dir_new_subjects, ls_dir_4bids2dcm


    # def extract_from_archive(self, src_dir, _dir):
    #     tmp_err_dir  = os.path.join(self.NIMB_tmp, 'tmp_err_classification')
    #     makedir_ifnot_exist(tmp_err_dir)
    #     dir_2extract = self.dir_new_subjects
    #     tmp_dir_2extract = ''
    #     if self.project in DEFAULT.project_ids:
    #         tmp_dir_2extract = os.path.join(self.NIMB_tmp, DEFAULT.nimb_tmp_dir)
    #         makedir_ifnot_exist(tmp_dir_2extract)
    #         dir_2extract = tmp_dir_2extract
    #     ZipArchiveManagement(
    #         os.path.join(src_dir, _dir),
    #         path2xtrct = dir_2extract,
    #         path_err   = tmp_err_dir)
    #     if tmp_dir_2extract:
    #         project_dir = os.path.join(tmp_dir_2extract,
    #                                     DEFAULT.project_ids[self.project]["dir_from_source"])
    #         if os.path.exists(project_dir):
    #             print(f'    this is default project;\
    #                 the corresponding default folder was created in: {project_dir}')
    #             ls_content = self.get_content(project_dir)
    #             for _dir in ls_content:
    #                 nr_left_2cp = len(ls_content[ls_content.index(_dir):])
    #                 print(f'    number of folders left to copy: {nr_left_2cp}')
    #                 src = os.path.join(project_dir, _dir)
    #                 dst = os.path.join(self.dir_new_subjects, _dir)
    #                 print(f'    copying folder: {src} to {dst}')
    #                 shutil.copytree(src, dst)
    #         else:
    #             print(f'    the expected folder: {project_dir} is missing')
    #         print(f'    removing temporary folder: {tmp_dir_2extract}')
    #         shutil.rmtree(tmp_dir_2extract, ignore_errors=True)
    #     if len(self.get_content(tmp_err_dir)) == 0:
    #         shutil.rmtree(tmp_err_dir, ignore_errors=True)
