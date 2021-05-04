# -*- coding: utf-8 -*-

import os
import pandas as pd

from stats.db_processing import Table
from distribution.distribution_helper import  DistributionHelper
from distribution.utilities import save_json, makedir_ifnot_exist
from distribution.distribution_definitions import get_keys_processed


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
        self.f_ids_name         = self.local_vars["NIMB_PATHS"]['file_ids_processed']

        # self.f_ids_proc_path = os.path.join(self.materials_DIR,
        #                         local_vars["NIMB_PATHS"]['file_ids_processed'])

        self.path_stats_dir     = all_vars.stats_vars["STATS_PATHS"]["STATS_HOME"]
        self.path_fsglm_dir     = all_vars.stats_vars["STATS_PATHS"]["FS_GLM_dir"]
        self.f_ids_abspath      = os.path.join(self.path_stats_dir, self.f_ids_name)
        self.archive_type       = '.zip'
        self.tab                = Table()
        self.df_f_groups        = self.get_df_f_groups()


    def get_df_f_groups(self):
        self.df_grid_ok = False
        f_groups = self.project_vars['fname_groups']
        dir_4stats       = makedir_ifnot_exist(self.path_stats_dir)
        if DistributionHelper(self.all_vars).get_files_for_stats(dir_4stats,
                                                            [f_groups,]):
            self.df_grid_ok = True
            return self.tab.get_df(os.path.join(dir_4stats, f_groups))
        else:
            self.df_grid_ok = False
            return 'None'


    def run(self):
        """
            will run the whole project starting with the file provided in the projects.json -> group
        Args:
            groups file
        Return:
            stats
        """
        print(f'   running pipeline for project: {self.project}')
        _ids_bids = self.get_ids_bids()
        _ids_all = self.get_ids_all()


    def get_ids_bids(self):
        """ 
            extract bids ids from the file groups provided by user
            !! ATTENTION - bids_id must also comprise the session name
            as defined in the sessions folder of BIDS structure
            current abbreviation is ses_00; this varibale must be changed 
            to allow users to define it
        """
        if self.df_grid_ok:
            return list(self.df_f_groups[self.bids_id_col])
        else:
            return 'None'


    def get_ids_all(self):
        """ 
            extract bids ids from the file groups provided by user
        """
        if self.f_ids_in_dir(self.path_stats_dir):
            return os.path.join(self.path_stats_dir, self.f_ids_name)
        else:
            return 'None'


    def f_ids_in_dir(self, path_2groups_f):
        self.f_ids_abspath = os.path.join(path_2groups_f, self.f_ids_name)
        if os.path.exists(self.f_ids_abspath):
            return True
        else:
            return self._ids_file_try2make()


    def _ids_file_try2make(self):
        if self.df_grid_ok:
            bids_ids = self.df_f_groups[self.bids_id_col]
            self.make_reading_dirs()

            _ids = dict()
            for bids_id in bids_ids:
                _ids = self.populate_ids_all(_ids, bids_id)
            self.create_file_ids(_ids)

            if os.path.exists(self.f_ids_abspath):
                return True
            else:
                print('could not create the file with ids')
                True
        else:
            return False


    def make_reading_dirs(self):
        SOURCE_BIDS_DIR = self.project_vars['SOURCE_BIDS_DIR']
        SOURCE_SUBJECTS_DIR = self.project_vars['SOURCE_SUBJECTS_DIR']
        PROCESSED_FS_DIR = self.project_vars['PROCESSED_FS_DIR']
        PROCESSED_NILEARN_DIR = self.project_vars['PROCESSED_NILEARN_DIR']
        PROCESSED_DIPY_DIR = self.project_vars['PROCESSED_DIPY_DIR']
        self.keys2chk = {
            'src': SOURCE_SUBJECTS_DIR,
            'fs': PROCESSED_FS_DIR,
            'nilearn': PROCESSED_NILEARN_DIR,
            'dipy': PROCESSED_DIPY_DIR,
                            }
        self.content_dirs = {}
        for key in self.keys2chk:
            dir2chk = self.keys2chk[key][1]
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


    def populate_ids_all_from_remote(self, _ids, bids_id):
        '''
        fs_processed_col = 'path_freesurfer711'
        irm_source_col = 'path_source'
        df = pd.read_csv(path.join(self.projects[self.project_name]['materials_DIR'], self.projects[self.proj>
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
        self.save_json(_ids, self.f_ids_abspath)
