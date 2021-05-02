# -*- coding: utf-8 -*-

import os
import pandas as pd

from stats.db_processing import Table
from distribution.distribution_helper import  DistributionHelper
from distribution.utilities import makedir_ifnot_exist

class ProjectManager:
    '''
    projects require assessment of stage. Stages:
    - file with data is present
    - ids are present
    - source for IRM is defined
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
        self.location           = self.project_vars['materials_DIR'][0]
        self.materials_dir_path = self.project_vars['materials_DIR'][1]

        self.f_ids_name         = self.local_vars["NIMB_PATHS"]['file_ids_processed']
        # self.f_ids_proc_path = os.path.join(self.materials_DIR,
        #                         local_vars["NIMB_PATHS"]['file_ids_processed'])

        self.FS_SUBJECTS_DIR    = self.local_vars['FREESURFER']['FS_SUBJECTS_DIR']
        self.path_stats_dir     = all_vars.stats_vars["STATS_PATHS"]["STATS_HOME"]
        self.path_fsglm_dir     = all_vars.stats_vars["STATS_PATHS"]["FS_GLM_dir"]
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


    def _ids_file_create(self):
        if self.df_grid_ok:
            from . distribution_definitions import get_keys_processed
            _ids = dict()

            self.groups_df = self.get_df_f_groups()
            bids_ids = self.groups_df[self.bids_id_col]
            for bids_id in bids_ids:
                _ids[bids_id] = dict()
                fs_key = get_keys_processed('fs')
                path_2_processed = os.path.join(self.FS_SUBJECTS_DIR,
                            bids_id)
                if os.path.exists(path_2_processed):
                    _ids[bids_id][fs_key] = path_2_processed
                else:
                    _ids[bids_id][fs_key] = ''
            print(_ids, self.f_ids_name)
            return None# self.f_ids_name
        else:
            pass


    # def run_from_project(self):
    #     if os.path.exists(self.f_ids_proc_path):
    #         return True
    #     else:
    #         self.grid_df = self.tab.get_df(self.files['grid']['file'])
    #         ready, _ids_fsproc = self.get_fs_processed()
    #         if ready:
    #             from distribution.distribution_definitions import get_keys_processed
    #             self.f_ids = dict()

    #             for bids_id in [i for i in list(_ids_fsproc.keys())]:
    #                 self.f_ids[bids_id] = dict()
    #                 fs_key = get_keys_processed('fs')
    #                 fs_id = _ids_fsproc[bids_id][0]
    #                 if fs_id:
    #                     self.f_ids[bids_id][fs_key] = fs_id
    #                 else:
    #                     self.f_ids[bids_id][fs_key] = ''
    #             # d_ids = {self.files['grid']['ids']: [i for i in list(_ids_fsproc.keys())],
    #             #          'freesurfer': [i[0].replace('.zip','') for i in list(_ids_fsproc.values())]}
    #             # fs_proc_df = self.tab.create_df_from_dict(d_ids)
    #             # fs_proc_df = self.tab.change_index(fs_proc_df, self.files['grid']['ids'])
    #             # grid_fs_df_pre = self.tab.change_index(self.grid_df, self.files['grid']['ids'])
    #             # self.f_ids = self.tab.join_dfs(grid_fs_df_pre, fs_proc_df, how='outer')
    #             return self.create_file_ids()
    #         else:
    #             return False


    # def get_fs_processed(self):
    #     '''use ids from the grid_ids
    #        extract processed ids from the FreeSurfer processed folder
    #        parameters present in the name: presence of WM, absence of T2, absence of T1B
    #     '''
    #     _id_fsproc = dict()
    #     fs_processed_all = os.listdir(self.vars.fs_processed_path())
    #     grid_ids = self.grid_df[self.files['grid']['ids']].tolist()
    #     for _id in grid_ids:
    #         for i in fs_processed_all:
    #             if _id in i:
    #                 _id_fsproc = self.populate_dict(_id_fsproc, _id, i)
    #     missing = [i for i in _id_fsproc if not _id_fsproc[i]]
    #     if missing:
    #         print('missing IDs:', len(missing), missing)
    #         return False, missing
    #     else:
    #         return True, _id_fsproc


    # def populate_dict(self, d, cle, val):
    #     if cle not in d:
    #         d[cle] = list()
    #     if val not in d[cle]:
    #         d[cle].append(val)
    #     return d

    # def create_file_ids(self):
    #     print('creating file with groups {}'.format(self.f_ids_proc_path))
    #     self.save_json(self.f_ids, self.f_ids_proc_path)
    #     return True


    def f_ids_in_dir(self, path_2groups_f):
        f_ids_abspath = os.path.join(path_2groups_f, self.f_ids_name)
        if os.path.exists(f_ids_abspath):
            return True
        else:
            if self._ids_file_create():
                return True
            else:
                print('could not create the file with ids')
                return False


    def get_ids_bids(self):
        """ 
            extract bids ids from the file groups provided by user
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

        # chk that all participants underwent Freesurfer processing; IDs of participanta are considered to be BIDS ids (no session)
        # if not - ask if FreeSurfer processing is requested by the user. Default - no.
        # chk that group file includes all variables defined in the projects.json file
        # chk that is ready to perform stats
        # chk if stats were performed. If not - ask if stats are requested.


#         # check that all subjects have corresponding FreeSurfer processed data
#         fs_processed_col = 'path_freesurfer711'
#         irm_source_col = 'path_source'
#         df = pd.read_csv(path.join(self.projects[self.project_name]['materials_DIR'], self.projects[self.proj>
#         ls_miss = df[irm_source_col].tolist()
#         remote_loc = self.get_processing_location('freesurfer')
#         remote_loc = remote_loc[0]
#         # check if self.fs_ready(remote_loc)
# #        host_name = ""
# #        if self.fs_ready():
# #            # 1. install required library and software on the local computer, including freesurfer
# #            self.setting_up_local_computer()
# #            # install freesurfer locally
# #            setup = SETUP_FREESURFER(self.locations)
#         SSHHelper.upload_multiple_files_to_cluster(remote_loc, ls_miss, self.locations[remote_loc]["NIMB_PATHS"]["NIMB_tmp"]

        '''
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

