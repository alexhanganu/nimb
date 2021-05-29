# -*- coding: utf-8 -*-

test = False
nr_participants_for_testing = 2

import os
import pandas as pd

from stats.db_processing import Table
from distribution.distribution_helper import  DistributionHelper
from distribution.distribution_ready import DistributionReady
from distribution.utilities import load_json, save_json, makedir_ifnot_exist
from distribution.distribution_definitions import get_keys_processed, DEFAULT
from classification.classify_bids import MakeBIDS_subj2process
from setup.interminal_setup import get_userdefined_paths, get_yes_no


# 2ADD:
# chk that group file includes all variables defined in the projects.json file
# chk that is ready to perform stats
# chk if stats were performed. If not - ask if stats are requested.
# if not - ask if FreeSurfer processing is requested by the user. Default - no.


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
        self.archive_type       = '.zip'
        self.tab                = Table()
        self.distrib_hlp        = DistributionHelper(self.all_vars)
        self.distrib_ready      = DistributionReady(self.all_vars)
        self.df_f_groups        = self.get_df_f_groups()
        self.DICOM_DIR          = self.project_vars["SOURCE_SUBJECTS_DIR"]


    def get_df_f_groups(self):
        self.df_grid_ok = False
        f_groups = self.project_vars['fname_groups']
        dir_4stats       = makedir_ifnot_exist(self.path_stats_dir)
        if self.distrib_hlp.get_files_for_stats(dir_4stats,
                                                [f_groups,]):
            self.df_grid_ok = True
            return self.tab.get_df(os.path.join(dir_4stats, f_groups))
        else:
            self.df_grid_ok = False
            return self.make_default_grid()


    def make_default_grid(self):
        print('here',self.path_stats_dir)
        df = self.tab.get_clean_df()
        df[self.bids_id_col] = ''
        self.tab.save_df(df,
            os.path.join(self.path_stats_dir, DEFAULT.default_tab_name))
        self.tab.save_df(df,
            os.path.join(self.materials_dir_pt, DEFAULT.default_tab_name))
        self.project_vars['fname_groups']   = DEFAULT.default_tab_name
        self.all_vars.projects[self.project]['fname_groups'] = DEFAULT.default_tab_name
        from setup.get_credentials_home import _get_credentials_home
        save_json(self.all_vars.projects, os.path.join(_get_credentials_home(), 'projects.json'))
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
        if do_task == 'fs-get-stats':
            self.get_stats_fs()
        elif do_task == 'fs-get-masks':
            self.get_masks()
        elif do_task == 'check-new':
            self.check_new()

        # self.get_ids_bids()
        # self.get_ids_all()


    def check_new(self):
        print('checking for new subject to be processed')
        self.distrib_hlp.check_new()


    def get_ids_bids(self):
        """
            extract bids ids from the file groups provided by user
            !! ATTENTION - bids_id must also comprise the session name
            as defined in the sessions folder of BIDS structure
            current abbreviation is ses_00; this variable must be changed
            to allow users to define it
        """
        if self.df_grid_ok:
            self._ids_bids = list(self.df_f_groups[self.bids_id_col])
            self.chk_missing_participants()
        else:
            self.prep_4dcm2bids_classification()


    def chk_missing_participants(self):
        print('    ids present: ',self._ids_bids)
        self.get_ids_all()
        if not self._ids_all:
            if self.get_ids_classified():
                self.populate_f_ids_from_nimb_classified()
            else:
                self.prep_4dcm2bids_classification()
        else:
            print('    file with all ids is missing')



    def prep_4dcm2bids_classification(self):
        self.prep_dirs(["SOURCE_BIDS_DIR",
                    "SOURCE_SUBJECTS_DIR"])

        from distribution.manage_archive import ZipArchiveManagement as archive
        self.archive = archive

        src_dir = self.project_vars['SOURCE_SUBJECTS_DIR'][1]
        ls_source_dirs = os.listdir(src_dir)
        if test:
            ls_source_dirs = os.listdir(src_dir)[:nr_participants_for_testing]
        if len(ls_source_dirs) > 0:
            for _dir in ls_source_dirs:
                self.DICOM_DIR, ls_dir_4bids2dcm = self.get_dir_with_raw_MR_data(src_dir, _dir)
                for dir_ready in ls_dir_4bids2dcm:
                    MakeBIDS_subj2process(self.DICOM_DIR,
                                        self.NIMB_tmp,
                                        ls_dir_4bids2dcm,
                                        self.all_vars.params.fix_spaces,
                                        True,
                                        self.local_vars['FREESURFER']['multiple_T1_entries'],
                                        self.local_vars['FREESURFER']['flair_t2_add']).run()
                    # from classification.dcm2bids_helper import DCM2BIDS_helper
                    # DCM2BIDS_helper(self.project_vars,
                    #                 self.project,
                    #                 DICOM_DIR = self.DICOM_DIR,
                    #                 dir_2classfy = dir_ready)

            self.get_ids_classified()
            self.populate_grid()
        else:
            print(f'    folder with source subjects {src_dir} is empty')


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


    def populate_grid(self):
        # get grid
        # popualte
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
            f_new_subjects = os.path.join(self.NIMB_tmp, DEFAULT.f_subjects2proc)
            save_json(self._ids_classified, f_new_subjects)
            print('    NIMB initiates processing of data')
            self.send_2processing('process')
        else:
            print('   file with nimb classified is missing')


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
        self.schedule.submit_4_processing(cmd, process_type, subproc, cd_cmd)


    def get_dir_with_raw_MR_data(self, src_dir, _dir):
        if _dir.endswith('.zip'):
            dir_2extract = self.local_vars["NIMB_PATHS"]["NIMB_NEW_SUBJECTS"]
            tmp_err_dir  = os.path.join(self.NIMB_tmp, 'tmp_err_dcm2bids')
            makedir_ifnot_exist(dir_2extract)
            makedir_ifnot_exist(tmp_err_dir)
            ls_initial = self.get_content(dir_2extract)
            if self.project in DEFAULT.project_ids:
                chemin_2chk = os.path.join(dir_2extract, DEFAULT.project_ids[self.project]["dir_from_source"])
                if os.path.exists(chemin_2chk):
                    ls_initial = self.get_content(chemin_2chk)
            self.archive(
                os.path.join(src_dir, _dir),
                path2xtrct = dir_2extract,
                path_err   = tmp_err_dir,
                )
            if self.project in DEFAULT.project_ids:
                if os.path.exists(chemin_2chk):
                    dir_2extract = chemin_2chk
            ls_dir_4bids2dcm = [i for i in os.listdir(dir_2extract) if i not in ls_initial]
        elif os.path.isdir(os.path.join(src_dir, _dir)):
            dir_2extract = src_dir
            ls_dir_4bids2dcm = list(_dir)
        return dir_2extract, ls_dir_4bids2dcm


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
        else:
            self._ids_all = dict()


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
                self.content_dirs[key] = os.listdir(dir2chk)


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


    def create_file_ids(self, _ids):
        print('creating file with groups {}'.format(self.f_ids_abspath))
        save_json(_ids, self.f_ids_abspath)
        save_json(_ids, os.path.join(self.materials_dir_pt, self.f_ids_name))
