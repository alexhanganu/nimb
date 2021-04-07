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
import pandas as pd
from .SSHHelper import RemoteConnManager

class ProjectManager:
    def __init__(self,
                project_vars,
                local_vars):
        self.proj_vars  = project_vars
        self.local_vars = local_vars
        print('isnide1')

        # self.run()

    def _ids_file(self):
        print('isnide')
        f_ids_name = self.local_vars["NIMB_PATHS"]['file_ids_processed']
        import distribution_definitions
        _ids = dict()
        for key in distribution_definitions.ids_processed:
            key_name = distribution_definitions.get_ids_processed(key)
            _ids[key_name] = ''
        print(_ids, f_ids_name)
        
        return f_ids_name

#     def run(self):
#         """
#             will run the whole project starting with the file provided in the projects.json -> group
#         Args:
#             groups file
#         Return:
#             stats
#         """
#         print('running projects {}'.format(self.project))

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

