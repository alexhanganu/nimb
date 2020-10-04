import os


class DistributionCheckNew():

    def __init__(self, project_vars):
#        super().__init__(all_vars=all_vars, projects=projects, project=project)
        self.project_vars = project_vars
        unprocessed = self.is_all_subject_processed()
        print(len(unprocessed))
        if unprocessed:
            print('there are subjects to be processed')


    def is_all_subject_processed(self):
        """
        1. get the list of un-processed subject
        must be absolute path
        :param SOURCE_SUBJECTS_DIR:
        :param PROCESSED_FS_DIR:
        :return:
        """
        print('SOURCE_SUBJECTS_DIR is: {}, \n PROCESSED_FS_DIR is: {}'.format(self.project_vars['SOURCE_SUBJECTS_DIR'], self.project_vars['PROCESSED_FS_DIR']))
        list_subjects = self._get_list_processed_subjects('SOURCE_SUBJECTS_DIR')
        list_processed = self._get_list_processed_subjects('PROCESSED_FS_DIR')
        print('there are {} subjects in source, and {} in processed'.format(len(list_subjects), len(list_processed)))
        return [i.strip('.zip') for i in list_subjects if i.strip('.zip') not in list_processed]

    def _get_list_processed_subjects(self, DIR):
        ls_dir = []
        if self.project_vars[DIR][0] == 'local':
            path_dir = self.project_vars[DIR][1]
            if os.path.exists(path_dir):
                ls_dir = os.listdir(path_dir)
        else:
            from distribution.SSHHelper import get_remote_list #runCommandOverSSH
            return get_remote_list(self.project_vars[DIR][0]) #runCommandOverSSH(self.project_vars[DIR][0], 'ls {}'.format(self.project_vars[DIR][1]))

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



    # @staticmethod
    def get_available_space(self, SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR):
        """
        1. get the current available space on hard-disk of user                                                                                                            
        2. calculate the list of
                initial script in database -> create_lsmiss  
        :param SOURCE_SUBJECTS_DIR:
        :return:
        """
        # based on availabe space
        to_be_process_subject = DiskspaceUtility.get_subject_to_be_process_with_free_space(un_process_sj)
        #
    @staticmethod
    def helper(ls_output):
        """
        split the outputs of 'ls' to get all file names
        :param ls_output:
        :return:
        """
        return ls_output.split("\n")[0:-1]
    # @staticmethod
    def get_list_subject_to_be_processed_remote_version(self, SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR,
                                                        remote):
        """
        use when SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR, are at two computers
        1. connect to the remote host
        2. get local process subjects
        3. get remote processed subjects
        4. get un-processs subjects from local
        5. get available space on remote computer
        6. get to-be-process subjects
        7. (other functions) send those subjects to the remote server
        :param SOURCE_SUBJECTS_DIR: MUST BE FULL PATHS
        :param PROCESSED_FS_DIR:
        :return: full path of subjects that is not process yet
        """
        ssh_session = SSHHelper.getSSHSession(remote)
        (zip_out, err) = runCommandOverSSH(ssh_session, f" cd {PROCESSED_FS_DIR}; ls *.zip") #
        (gz_out, err) = runCommandOverSSH(ssh_session, f"cd {PROCESSED_FS_DIR}; ls *.gz")
        # at remote
        all_processed_file_remote = DistributionHelper.helper(gz_out) + DistributionHelper.helper(zip_out) # only file name, no path
        # at local
        all_subjects_at_local = ListSubjectHelper.get_all_subjects(SOURCE_SUBJECTS_DIR) # full path
        all_subjects_at_local_short_name = [short_name.split("/")[-1] for short_name in all_subjects_at_local ]
        # get free space remotely
        free_space = DiskspaceUtility.get_free_space_remote(ssh_session)
        to_be_process_subject = set(all_subjects_at_local_short_name) - set(all_processed_file_remote) # not consider space yet
        # consider the space available the remote server
        free_space = min(free_space, 10*1024) # min of 'free space' and 10GB
        to_be_process_subject = DiskspaceUtility.get_subject_upto_size(free_space, to_be_process_subject)

        print("Remote server has {0}MB free, it can stored {1} subjects".format(free_space, len(to_be_process_subject)))
        ssh_session.close()
        return [os.path.join(SOURCE_SUBJECTS_DIR,subject) for subject in to_be_process_subject] # full path


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



'''


def _update_list_processed_subjects(DIR, dir2read):
    Processed_Subjects = {}
    Processed_Subjects[DIR] = []
    MainFolder = _get_folder('Main')
    if path.isfile(MainFolder+'logs/processed_subjects_'+DIR+'.txt'):
        ls = []
        with open(MainFolder+'logs/processed_subjects_'+DIR+'.txt', 'r') as f:
                for line in f:
                    ls.append(line.strip('\n'))
        Processed_Subjects[DIR] = ls[1:]
    Processed_Subjects[DIR].append(dir2read)
    open(MainFolder+'logs/processed_subjects_'+DIR+'.txt','w').close()
    with open(MainFolder+'logs/processed_subjects_'+DIR+'.txt','a') as f:
        f.write(DIR+'\n')
        for subject in Processed_Subjects[DIR]:
            f.write(subject+'\n')



def create_lsmiss(lsmiss):
    MainFolder = _get_folder('Main')
    for DIR in lsmiss:
        if path.isfile(MainFolder+'logs/miss_'+DIR+'.txt'):
            ls = []
            with open(MainFolder+'logs/miss_'+DIR+'.txt','r') as f:
                for line in f:
                    ls.append(line.strip('\n'))
            for value in lsmiss[DIR]:
                if value in ls[1:]:
                    lsmiss[DIR].remove(value)
            for value in ls[1:]:
                if value not in lsmiss[DIR]:
                    lsmiss[DIR].append(value)
            lsmiss[DIR] = sorted(lsmiss[DIR])
        open(MainFolder+'logs/miss_'+DIR+'.txt','w').close()
        with open(MainFolder+'logs/miss_'+DIR+'.txt','a') as f:
            f.write(DIR+'\n')
            for subject in lsmiss[DIR]:
                f.write(subject+'\n')


def _get_lsmiss():
    MainFolder = _get_folder('Main')
    lsmiss = {}
    for file in listdir(MainFolder+'logs/'):
        if 'miss_' in file:
            ls = []
            with open(MainFolder+'logs/'+file, 'r') as f:
                for line in f:
                    ls.append(line.strip('\n'))
            lsmiss[ls[0]] = ls[1:]
    print('lsmiss from get_lsmiss is: ',lsmiss)
    return lsmiss

def _update_lsmiss(DIR, dir2read):
    MainFolder = _get_folder('Main')
    lsmiss = {}
    if path.isfile(MainFolder+'logs/miss_'+DIR+'.txt'):
        ls = []
        with open(MainFolder+'logs/miss_'+DIR+'.txt', 'r') as f:
            for line in f:
                ls.append(line.strip('\n'))
        lsmiss[ls[0]] = ls[1:]
        lsmiss[DIR].remove(dir2read)
        if len(lsmiss[DIR])>0:
            open(MainFolder+'logs/miss_'+DIR+'.txt','w').close()
            with open(MainFolder+'logs/miss_'+DIR+'.txt','a') as f:
                f.write(DIR+'\n')
                for subject in lsmiss[DIR]:
                    f.write(subject+'\n')
        else:
            remove(MainFolder+'logs/miss_'+DIR+'.txt')
    else:
        print(MainFolder+'logs/miss_'+DIR+'.txt'+' is not a file')


def update_ls_subj2fs(SUBJECT_ID):
    #subj2fs file is the list of subjects that need to undergo the FS pipeline processing?
    newlssubj = []
    MainFolder = _get_folder('Main')
    if path.isfile(MainFolder+'logs/subj2fs'):
        lssubj = [line.rstrip('\n') for line in open(MainFolder+'logs/subj2fs')]
        for subjid in lssubj:
            if subjid not in newlssubj:
                newlssubj.append(subjid)
    newlssubj.append(SUBJECT_ID)
    open(MainFolder+'logs/subj2fs','w').close()
    with open(MainFolder+'logs/subj2fs','a') as f:
        for subj in newlssubj:
            f.write(subj+'\n')
'''
