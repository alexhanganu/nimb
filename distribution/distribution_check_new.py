import os


class DistributionCheckNew():

    def __init__(self, project_vars, NIMB_tmp):
        self.project_vars = project_vars
        self.NIMB_tmp     = NIMB_tmp
        self.unprocessed  = self.is_all_subject_processed()


    def is_all_subject_processed(self):
        """
        1. get the list of un-processed subject
        must be absolute path
        :param SOURCE_SUBJECTS_DIR:
        :param PROCESSED_FS_DIR:
        :return:
        """
        print('SOURCE_SUBJECTS_DIR is: {}, \n PROCESSED_FS_DIR is: {}'.format(self.project_vars['SOURCE_SUBJECTS_DIR'], self.project_vars['PROCESSED_FS_DIR']))
        ls_subj_bids = self._get_ls_subjects('SOURCE_BIDS_DIR')
        if not ls_subj_bids:
            list_subjects = self._get_source_subj()
        list_processed = self._get_ls_subjects('PROCESSED_FS_DIR')
        print('there are {} subjects in source, and {} in processed'.format(len(list_subjects), len(list_processed)))
        return [i.strip('.zip') for i in list_subjects if i.strip('.zip') not in list_processed]

    def _get_ls_subjects(self, DIR):
        if self.project_vars[DIR][0] == 'local':
            path_dir = self.project_vars[DIR][1]
            if os.path.exists(path_dir):
                return os.listdir(path_dir)
            else:
                return dict()
        else:
            from distribution.SSHHelper import runCommandOverSSH
            return runCommandOverSSH(self.project_vars[DIR][0],
                                     'ls {}'.format(self.project_vars[DIR][1])).split('\n') 

    def _get_source_subj(self):
        DIR = 'SOURCE_SUBJECTS_DIR'
        file_nimb_subj = 'nimb_subjects.json'
        if self.project_vars[DIR][0] == 'local':
            path_dir = self.project_vars[DIR][1]
            if os.path.exists(path_dir):
                return [i for i in self.read_json_f(os.path.join(path_dir, file_nimb_subj)).keys()]
            else:
                from distribution.SSHHelper import download_files_from_server
                try:
                    download_files_from_server(self.project_vars[DIR][0],
                                            os.path.join(self.project_vars[DIR][1],file_nimb_subj),
                                            self.NIMB_tmp):                
                    return [i for i in self.read_json_f(os.path.join(self.NIMB_tmp, file_nimb_subj)).keys()]
                except Exception as e:
                    print(e)
                    return []

    def read_json_f(self, f):
        import json
        open(f, 'r') as f:
            return json.load(f)

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


if __name__ == "__main__":
    """

    """
    # this is to verify verify:
    # {“adni”: “SOURCE_SUBJECTS_DIR” : ['beluga', '/home/$USER/projects/def-hanganua/databases/loni_adni/source/mri'];
    # “PROCESSED_FS_DIR” : ['beluga', 'home/$USER/projects/def-hanganua/databases/loni_adni/processed_fs7']}
    # distribution = DistributionCheckNew()
    pass
