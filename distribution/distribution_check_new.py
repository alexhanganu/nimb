import os


class DistributionCheckNew():

    def __init__(self, project_vars, NIMB_tmp):
        self.project_vars = project_vars
        self.NIMB_tmp     = NIMB_tmp
        self.unprocessed  = self.is_all_subject_processed()

    def check_projects(self, project_name=None):
        """
        todo: project_name is never none because it has default value! must correct this one later via getting project name
        if project_name is None, means that user does not input the project name, it will check for all projects
        :param project_name: None or user input project
        :return:
        """
        # check if ~/nimb/projects.json → project → SOURCE_MR is provided; if not: ask user

        if project_name:
            self.check_single_project(project_name=project_name)
        else: # check all project
            for project_name in self.projects['PROJECT']:
                self.check_single_project(project_name=project_name)


    def is_all_subject_processed(self):
        """
        get the list of un-processed subject
        must be absolute path
        :param SOURCE_SUBJECTS_DIR:
        :param PROCESSED_FS_DIR:
        :param project_name: name of the project, cannot be None
        :return: a list of subject to be processed
        """
        print('SOURCE_SUBJECTS_DIR is: {}, \n PROCESSED_FS_DIR is: {}'.format(self.project_vars['SOURCE_SUBJECTS_DIR'], self.project_vars['PROCESSED_FS_DIR']))
        ls_subj_bids = self._get_ls_subjects('SOURCE_BIDS_DIR')
        if not ls_subj_bids:
            list_subjects = self._get_source_subj()
        list_processed = self._get_ls_subjects('PROCESSED_FS_DIR')
        print('there are {} subjects in source, and {} in processed'.format(len(list_subjects), len(list_processed)))
        return [i.strip('.zip') for i in list_subjects if i.strip('.zip') not in list_processed]
        
            # # self.is_all_subject_processed(self.get_SOURCE_SUBJECTS_DIR()) == modify it
            # # local version
            # machine, source_fs = self.get_SOURCE_SUBJECTS_DIR()
            # _, process_fs = self.get_PROCESSED_FS_DIR()
            # to_be_processed = []
            # if machine == "local":
                # if not self.is_all_subject_processed(source_fs, process_fs): # test this function
                    # #get the list of subjects in SOURCE_SUBJECTS_DIR
                    # to_be_processed = self.get_list_subject_to_be_processed_local_version(source_fs,process_fs)

            # else:# remote version: source is at remote
                # # go to the remote server to check
                # host = self.projects['LOCATION'][machine]
                # to_be_processed = self.get_list_subject_to_be_processed_remote_version(source_fs, process_fs,remote_id)

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
        # (zip_out, err) = runCommandOverSSH(ssh_session, f" cd {PROCESSED_FS_DIR}; ls *.zip") #
        # (gz_out, err) = runCommandOverSSH(ssh_session, f"cd {PROCESSED_FS_DIR}; ls *.gz")
        # # at remote
        # all_processed_file_remote = DistributionHelper.helper(gz_out) + DistributionHelper.helper(zip_out) # only file name, no path
        # # at local
        # all_subjects_at_local = ListSubjectHelper.get_all_subjects(SOURCE_SUBJECTS_DIR) # full path
        # all_subjects_at_local_short_name = [short_name.split("/")[-1] for short_name in all_subjects_at_local ]

    def _get_source_subj(self):
        DIR = 'SOURCE_SUBJECTS_DIR'
        file_nimb_subj = 'nimb_subjects.json'
        if self.project_vars[DIR][0] == 'local':
            path_dir = self.project_vars[DIR][1]
            if os.path.exists(os.path.join(path_dir, file_nimb_subj)):
                return [i for i in self.read_json_f(os.path.join(path_dir, file_nimb_subj)).keys()]
            else:
                self.initiate_classify(self.project_vars[DIR][1])
        else:
                from distribution.SSHHelper import download_files_from_server
                try:
                    download_files_from_server(self.project_vars[DIR][0],
                                            os.path.join(self.project_vars[DIR][1],file_nimb_subj),
                                            self.NIMB_tmp)
                    return [i for i in self.read_json_f(os.path.join(self.NIMB_tmp, file_nimb_subj)).keys()]
                except Exception as e:
                    print(e)
                    return []

    def initiate_classify(self, SOURCE_SUBJECTS_DIR):
        from classification.classify_bids import MakeBIDS_subj2process
        MakeBIDS_subj2process(SOURCE_SUBJECTS_DIR,
                self.NIMB_tmp,
                multiple_T1_entries = False,
                flair_t2_add = False).run()

    def read_json_f(self, f):
        import json
        with open(f, 'r') as f:
            return json.load(f)


    @staticmethod
    def helper(ls_output):
        """
        split the outputs of 'ls' to get all file names
        :param ls_output:
        :return:
        """
        return ls_output.split("\n")[0:-1]



#if __name__ == "__main__":
    """

    """
    # this is to verify verify:
    # {“adni”: “SOURCE_SUBJECTS_DIR” : ['beluga', '/home/$USER/projects/def-hanganua/databases/loni_adni/source/mri'];
    # “PROCESSED_FS_DIR” : ['beluga', 'home/$USER/projects/def-hanganua/databases/loni_adni/processed_fs7']}
    # distribution = DistributionCheckNew()
#    pass

