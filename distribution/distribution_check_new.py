import os
from distribution.distribution_helper import DistributionHelper
from setup.get_vars import Get_Vars
from nimb import get_parameters, NIMB
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(module)s %(levelname)s: %(message)s')
# logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)
#configuration


class DistributionCheckNew():

    def __init__(self, project_vars, projects, project_name, NIMB_tmp):
        self.projects = projects
        self.project_vars = project_vars  # dictionary about 1 project
        self.NIMB_tmp = NIMB_tmp
        self.unprocessed = self.is_all_subject_processed()

    def __init__(self, projects, project_name):
        """
        :param projects: json configuration of all projects, get from NIMB
        :param project_name:
        """
        self.projects = projects
        self.project_name = project_name
        self.project_vars = self.projects[project_name]  # dictionary about 1 project
        # self.unprocessed = self.is_all_subject_processed()

    def set_project(self, project_name, project_config):
        """

        :param project_name: name of the project, e.g., project1
        :param project_config: configuration dictionary of that project, like project1 in projects.json
        :return:
        """
        self.project_name = project_name
        self.project_config = project_config

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
        else:  # check all project
            for project_name in self.projects['PROJECT']:
                self.check_single_project(project_name=project_name)

    def is_all_subject_processed(self):
        to_be_process = self.get_all_un_processed_subjects()
        if len(to_be_process) > 1:
            return True
        return False

    def get_all_un_processed_subjects(self):
        """
        get the list of un-processed subject
        must be absolute path
        :param SOURCE_SUBJECTS_DIR:
        :param PROCESSED_FS_DIR:
        :param project_name: name of the project, cannot be None
        :return: a list of subject to be processed
        """
        print('SOURCE_SUBJECTS_DIR is: {}, \n PROCESSED_FS_DIR is: {}'.format(self.project_vars['SOURCE_SUBJECTS_DIR'],
                                                                              self.project_vars['PROCESSED_FS_DIR']))
        list_subjects = self._get_ls_subjects('SOURCE_SUBJECTS_DIR')
        # if not ls_subj_bids:
        #     list_subjects = self._get_source_subj()
        list_processed = self._get_ls_subjects('PROCESSED_FS_DIR')
        print('there are {} subjects in source, and {} in processed'.format(len(list_subjects), len(list_processed)))
        print(len(set(list_subjects) - set(list_processed)))
        unprocessed_subject =  [i.strip('.zip') for i in list_subjects if i.strip('.zip') not in list_processed]
        self.unprocessed_subject = unprocessed_subject
        return unprocessed_subject

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

    def _get_ls_subjects(self, DIR="SOURCE_SUBJECTS_DIR"):
        """
        get list of subjects in a folder
        default will get all subjects in SOURCE_SUBJECTS_DIR
        :param DIR: folder has subjects, default is SOURCE_SUBJECTS_DIR
        :return: list of subject
        """
        logger.info("get all subjects in " + DIR)
        if self.project_vars[DIR][0] == 'local':
            path_dir = self.project_vars[DIR][1]
            if os.path.exists(path_dir):
                return os.listdir(path_dir)
            else:
                return []
        else:  # if remote
            from distribution.SSHHelper import runCommandOverSSH
            return runCommandOverSSH(remote=self.project_vars[DIR][0], \
                                     command='ls {}'.format(self.project_vars[DIR][1])).split('\n')

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
                                           os.path.join(self.project_vars[DIR][1], file_nimb_subj),
                                           self.NIMB_tmp)
                return [i for i in self.read_json_f(os.path.join(self.NIMB_tmp, file_nimb_subj)).keys()]
            except Exception as e:
                print(e)
                return []

    def initiate_classify(self, SOURCE_SUBJECTS_DIR):
        from classification.classify_bids import MakeBIDS_subj2process
        MakeBIDS_subj2process(SOURCE_SUBJECTS_DIR,
                              self.NIMB_tmp,
                              multiple_T1_entries=False,
                              flair_t2_add=False).run()

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

    def process_data_local(self):
        pass
    def process_data_remote(self):
        pass

if __name__ == "__main__":

    # {“adni”: “SOURCE_SUBJECTS_DIR” : ['beluga', '/home/$USER/projects/def-hanganua/databases/loni_adni/source/mri'];
    # “PROCESSED_FS_DIR” : ["beluga", "home/$USER/projects/def-hanganua/databases/loni_adni/processed_fs7"]}
    all_vars = Get_Vars()
    projects = all_vars.projects
    params = get_parameters([i for i in projects.keys() if 'EXPLANATION' not in i and 'LOCATION' not in i])
    app = NIMB(params.process, "adni", projects, all_vars)
    check_new = DistributionCheckNew(app.projects, app.project)
    # a = check_new.is_all_subject_processed()
    to_be_processed = check_new.get_all_un_processed_subjects()



