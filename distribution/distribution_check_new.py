from .distribution_helper import DistributionHelper
import os
class DistributionCheckNew(DistributionHelper):

    def read(self):

        if self.project_name:
            # check that project
            self.check_project(self.project_name)

        else: # check all project
            # get all project names

            for prj in self.projects['PROJECTS']:

                pass

    def check_project(self):
        SOURCE_MR = self.
        if os.path.isdir(self.projects['project1']['SOURCE_SUBJECTS_DIR']):
            # check if all subject is project: call
            # self.is_all_subject_processed(self.get_SOURCE_SUBJECTS_DIR()) == modify it
        else:
            # get the list: call the function here

        pass

"""
    - process CHECK_NEW
        - if project is provided by user: check per project
        - else: check for all projects
        - per projects: check if ~/nimb/projects.json → project → SOURCE_MR is provided.
        - If yes: check that all subjects were processed.
        - If not: get the list of subjects in SOURCE_SUBJECTS_DIR (archived zip or .gz) that didn’t undergo the FreeSurfer (missing in $PROCESSED_FS_DIR), get_list_subject_to_be_processed_remote() (verify: {“ppmi”: “SOURCE_SUBJECTS_DIR” : [elm, ‘/home_je/hanganua/database/loni_ppmi/source/mri]; “PROCESSED_FS_DIR” : [elm, ‘home_je/hanganua/database/loni_ppmi/processed_fs]})
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