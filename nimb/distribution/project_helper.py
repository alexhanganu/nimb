'''
projects require assessment of stage. Stages:
- file with data is present
- ids are present
- source for IRM is defined
- ids are processed with FreeSurfer/ nilearn, DWI
- stats performed
For missing stages, helper will initiate distribution for the corresponding stage
Args:
    project variables
Return:
    True, False
'''

import os
import pandas as pd

from stats.db_processing import Table
from distribution.distribution_helper import  DistributionHelper

class ProjectManager:
    def __init__(self,
                project,
                project_vars,
                local_vars,
                stats_vars):
        self.local_vars         = local_vars
        self.project            = project
        self.f_groups           = project_vars['fname_groups']
        self.bids_id_col        = project_vars['id_col']
        self.location           = project_vars['materials_DIR'][0]
        self.materials_dir_path = project_vars['materials_DIR'][1]

        self.f_ids_name         = self.local_vars["NIMB_PATHS"]['file_ids_processed']
        self.FS_SUBJECTS_DIR    = self.local_vars['FREESURFER']['FS_SUBJECTS_DIR']
        self.path_stats_dir     = stats_vars["STATS_PATHS"]["STATS_HOME"]
        self.path_fsglm_dir     = stats_vars["STATS_PATHS"]["FS_GLM_dir"]
        self.tab                = Table()
        # self.Dist               = DistributionHelper()
        self.run()

    # def get_files_for_stats(self, path_2copy_files, list_of_files): # moving to project_helper
    #     location = self.proj_vars['materials_DIR'][0]
    #     materials_dir_path = self.proj_vars['materials_DIR'][1]
    #     if location == 'local':
    #         for file in list_of_files:
    #             path2file = os.path.join(materials_dir_path, file)
    #             if os.path.exists(path2file):
    #                 shutil.copy(path2file, path_2copy_files)
    #     else:
    #         print('nimb must access the remote computer: {}'.format(location))
    #         from distribution import SSHHelper
    #         SSHHelper.download_files_from_server(location, materials_dir_path, path_2copy_files, list_of_files)
    #     if os.path.exists(os.path.join(path_2copy_files, list_of_files[-1])):
    #         return True
    #     else:
    #         return self.chk_files_for_stats(list_of_files, path_2copy_files)

    def get_groups_file(self):
        if self.location == 'local':
            self.groups_df = self.tab.get_df(os.path.join(self.materials_dir_path, self.f_groups))
        else:
            print('nimb must access the remote computer: {}'.format(self.location))
            from distribution import SSHHelper
            SSHHelper.download_files_from_server(self.location, self.materials_dir_path, self.path_fsglm_dir, [self.f_groups,])
            path_2file = os.path.join(self.path_fsglm_dir, self.f_groups)
            if os.path.exists(path_2file):
                self.groups_df = self.tab.get_df(path_2file)
            else:
                self.groups_df = None

    def _ids_file(self):
        from . distribution_definitions import get_keys_processed
        _ids = dict()
        self.get_groups_file()
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

    def f_ids_in_dir(self, path_2groups_f):
        # print(self.path_2copy_files)
        if os.path.exists(os.path.join(
                    path_2groups_f,
                    self.f_ids_name)):
            return True
        else:
            if self._ids_file():
                return True
            else:
                print('could not create the file with ids')
                return False

    def get_ids(self):
        """ check that group file is provided in the nimb_tmp/projects/project/stats dir
        chk that group file is present at the provided path
        chk that column group in present in the file"""
        file = 

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
        _ids_bids = self.get_ids()
        # chk that all participants underwent Freesurfer processing; IDs of participanta are considered to be BIDS ids (no session)
        # if not - ask if FreeSurfer processing is requested by the user. Default - no.
        # chk that group file includes all variables defined in the projects.json file
        # chk that is ready to perform stats
        # chk if stats were performed. If not - ask if stats are requested.


#         # check that all subjects have corresponding FreeSurfer processed data
#         id_col           = self.projects[self.project_name]['id_col']
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

