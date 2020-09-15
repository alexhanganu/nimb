from .distribution_helper import DistributionHelper
import os

from .utilities import get_username_password


class DistributionCheckNew(DistributionHelper):

    def __init__(self, all_vars, projects, project):
        super().__init__(all_vars=all_vars, projects=projects, project=project)
    def ready(self):
        self.check_projects(self.project_name)
        # if self.project_name:
        #     # check that project
        #     self.check_projects(self.project_name)
        #
        # else: # check all project
        #     # get all project names
        #     for prj in self.projects['PROJECTS']:
        #
        #         pass

    def check_projects(self, project_name=None):
        """
        todo: project_name is never none because it has default value! must correct this one later via getting project name
        if project_name is None, means that user does not input the project name, it will check for all projects
        :param project_name: None or user input project
        :return:
        """
        if project_name:
            self.check_single_project(project_name=project_name)
        else: # check all project
            for project_name in self.projects['PROJECT']:
                self.check_single_project(project_name=project_name)

    def check_single_project(self, project_name):
        """
        return the list of subjects to be processed, works on both local and remote computer
        :param project_name: name of the project, cannot be None
        :return: a list of subject to be processed
        """
        if project_name and os.path.isdir(self.projects[self.project_name]['SOURCE_SUBJECTS_DIR']): # if there is project input by user
            # check if all subject is project: call
            # self.is_all_subject_processed(self.get_SOURCE_SUBJECTS_DIR()) == modify it
            # local version
            machine, source_fs = self.get_SOURCE_SUBJECTS_DIR()
            _, process_fs = self.get_PROCESSED_FS_DIR()
            to_be_processed = []
            if machine == "local":
                if not self.is_all_subject_processed(source_fs, process_fs): # test this function
                    #get the list of subjects in SOURCE_SUBJECTS_DIR
                    to_be_processed = self.get_list_subject_to_be_processed_local_version(source_fs,process_fs)

            else:# remote version: source is at remote
                # go to the remote server to check
                host = self.projects['LOCATION'][machine]
                to_be_processed = self.get_list_subject_to_be_processed_remote_version(source_fs, process_fs,remote_id)
        return to_be_processed

if __name__ == "__main__":
    """

    """
    # this is to verify verify:
    # {“ppmi”: “SOURCE_SUBJECTS_DIR” : [elm, ‘/home_je/hanganua/database/loni_ppmi/source/mri];
    # “PROCESSED_FS_DIR” : [elm, ‘home_je/hanganua/database/loni_ppmi/processed_fs]}
    # cannot connect to ELM, time-out or wrong pass??
    # distribution = DistributionCheckNew()
    pass

"""
    - process CHECK_NEW
        - if project is provided by user: check per project
        - else: check for all projects

        - per projects: check if ~/nimb/projects.json → project → SOURCE_MR is provided.  ==> start
        - If yes: check that all subjects were processed.
        - If not: get the list of subjects in SOURCE_SUBJECTS_DIR (archived zip or .gz) that didn’t undergo the FreeSurfer (missing in $PROCESSED_FS_DIR), 
        get_list_subject_to_be_processed_remote() 
        (verify: {“ppmi”: “SOURCE_SUBJECTS_DIR” : [elm, ‘/home_je/hanganua/database/loni_ppmi/source/mri]; “PROCESSED_FS_DIR” : [elm, ‘home_je/hanganua/database/loni_ppmi/processed_fs]})
        - create distrib-DATABASE (track files) ~/nimb/distribution.json:
            - ACTION = notprocessed, copied2process
            - LOCATION = local, remote_name1, remote_name2, remote_name_n
            - add unprocessed subjects to distrib-DATABASE → ACTION=notprocessed
        - compute the number of subjects to be processed, volume of each subject, add volume of processed data.
        - compute available disk space on the local or remote (where freesurfer_install ==1) for the folder FS_SUBJECTS_DIR and NIMB_PROCESSED_FS ==> get_free_space_remote
        - populating rule: 
            - continue populating until the volume of subjects + volume of estimated processed subjects (900Mb per subject) is less then 75% of the available disk space
        - if freesurfer_install ==1 on local:
            - populate local.json → NIMB_PATHS → NIMB_NEW_SUBJECTS based on populating rule
        - if freesurfer_install ==1 on remote: NOW: notes: the first remote machine in projects.json that has fs_install==1 is selected, the rest is ignored
            - if content of subject to be processed, in SOURCE_SUBJECTS_DIR is NOT archived:
                - archive and copy to local/remote.json → Nimb_PATHS → NIMB_NEW_SUBECTS.
            - If there are more than one computer and all where checked and are ready to perform freesurfer:
                - send archived subjects to each of them in equal amount
            - once copied to the NIMB_NEW_SUBJECTS:
                - unarchive + rm the archive + compute the volume of the unarchived subject folder
                - add subject to distrib-DATABSE → LOCATION → remote_name
                - move subject in distrib-DATABASE → ACTION notprocessed → copied2process
            - after all subjects are copied to the NIMB_NEW_SUBJECTS folder: initiate the classifier on the local/remote computer with keys: cd $NIMB_HOME && python nimb.py -process classify
            - wait for the answer; If True and new_subjects.json file was created:
            - start the -process freesurfer
            - after each 2 hours check the local/remote NIMB_PROCESSED_FS and NIMB_PROCESSED_FS_ERROR folders. If not empty: mv (or copy/rm) to the path provided in the ~/nimb/projects.json → project → local or remote $PROCESSED_FS_DIR folder
            - if SOURCE_BIDS_DIR is provided: moves the processed subjects to corresponding SOURCE_BIDS_DIR/subject/session/processed_fs folder
"""
