import shutil
from os import system, path, listdir, environ, remove
from distribution.utilities import ErrorMessages, makedir_ifnot_exist
from distribution.setup_miniconda import setup_miniconda
from distribution.setup_freesurfer import SETUP_FREESURFER

from distribution.check_disk_space import *
from distribution import SSHHelper
import logging

# -- for logging, instead of using print --
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# --

class DistributionHelper():

    def __init__(self, all_vars, projects, project):

        self.credentials_home = all_vars.credentials_home # NIMB_HOME/credentials_paths.py
        self.installers       = all_vars.installers # NIMB_HOME/setup/installers.json
        self.locations        = all_vars.location_vars # credentials_home/local.json + remotes.json
        self.stats_vars       = all_vars.stats_vars
        self.projects         = projects # credentials_home/project.json
        self.project_name     = project
        self.NIMB_HOME        = self.locations["local"]["NIMB_PATHS"]["NIMB_HOME"]
        self.NIMB_tmp         = self.locations["local"]["NIMB_PATHS"]["NIMB_tmp"]

        # setup folder
        self.setup_folder = "../setup"
        self.git_repo = "https://github.com/alexhanganu/nimb"

    def get_stats_dir(self):
        """will return the folder with unzipped stats folder for each subject"""
        PROCESSED_FS_DIR = self.projects[self.project_name]["PROCESSED_FS_DIR"]

        if any('.zip' in i for i in listdir(PROCESSED_FS_DIR)):
            from .manage_archive import ZipArchiveManagement
            zipmanager = ZipArchiveManagement()
            tmp_dir = path.join(self.NIMB_tmp, 'tmp_subject_stats')
            if not path.exists(tmp_dir):
                makedir_ifnot_exist(tmp_dir)
            zipmanager.extract_archive(PROCESSED_FS_DIR, ['stats',], tmp_dir)
            return tmp_dir
        else:
            return PROCESSED_FS_DIR
        print('perform statistical analysis')


    def get_project_vars(self, var_name, project):
        """
        get the PROCESSED_FS_DIR
        :param config_file:
        :var_name: like PROCESSED_FS_DIR
        :return: empty string, or values
        """
        # PROJECT_DATA
        if project not in self.projects.keys():
            print("There is no path for project: "+project+" defined. Please check the file: {}".format(path.join(self.credentials_home, "projects.json")))
            return ""
        return self.projects[project][var_name]

    def get_PROCESSED_FS_DIR(self):
        """

        :return: like ["local","/home/username/database/source/mri"],
        """
        machine, path =  self.projects[self.project_name]['PROCESSED_FS_DIR']
        return machine, path

    def get_SOURCE_SUBJECTS_DIR(self):
        """

        :return: machine and path in that machine like ["local","/home/username/database/source/mri"],
        """
        machine, path =  self.projects[self.project_name]['SOURCE_SUBJECTS_DIR']
        return machine, path


    def run(self, Project):
        """
        # todo: need to find a location for this function
        :param Project:
        :return:
        """
        # 0 check the variables
        # if FreeSurfer_install = 1:
        host_name = ""
        if self.fs_ready():
            # 1. install required library and software on the local computer, including freesurfer
            self.setting_up_local_computer()
            # install freesurfer locally
            setup = SETUP_FREESURFER(self.locations,installers=self.installers)
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


    def run_processing_on_cluster_2(self):
        '''
        execute the python a/crun.py on the remote cluster
        :return:
        '''
        # version 2: add username, password, and command line to run here
        clusters = database._get_Table_Data('Clusters', 'all')

        # project_folder = clusters[list(clusters)[0]]['HOME']
        cmd_run = " python a/crun.py -submit false" #submit=true
        load_python_3 = 'module load python/3.7.4;'
        cmd_run_crun_on_cluster = load_python_3 +"cd " + "/home/hvt/" + "; " + cmd_run
        print("command: "+ cmd_run_crun_on_cluster)
        host_name = clusters[list(clusters)[0]]['remote_address'] #

        print("Start running the the command via SSH in cluster: python a/crun.py")
        SSHHelper.running_command_ssh_2(host_name=host_name, user_name=self.user_name,
                                    user_password=self.user_password,
                                    cmd_run_crun_on_cluster=cmd_run_crun_on_cluster)

    def run_copy_subject_to_cluster(Project):
        '''
        copy the subjects from subject json file to cluster
        :param Project: the json file of that project
        :return: None
        '''
        # todo: how to get the active cluster for this project

        clusters = database._get_Table_Data('Clusters', 'all')
        cname = [*clusters.keys()][0]
        project_folder = clusters[cname]['HOME']
        a_folder = clusters[cname]['App_DIR']
        subjects_folder = clusters[cname]['Subjects_raw_DIR']
        # the json path is getting from mri path,
        mri_path = database._get_Table_Data('Projects', Project)[Project]['mri_dir']
        print(mri_path)
        print("subject json: " + mri_path)
        SSHHelper.copy_subjects_to_cluster(mri_path, subjects_folder, a_folder)


    def setting_up_local_computer(self):
        if platform.startswith('linux'):
            print("Currently only support setting up on Ubuntu-based system")
            # do the job here
            self.setting_up_local_linux_with_freesurfer()
        elif platform in ["win32"]:
            print("The system is not fully supported in Windows OS. The application quits now .")
            exit()
        else: # like freebsd,
            print("This platform is not supported")
            exit()
    def setting_up_local_linux_with_freesurfer(self):
        """
        install miniconda and require library
        :return:
        """
        setup_miniconda(self.NIMB_HOME)

    def setting_up_remote_linux_with_freesurfer(self, host_name):
        # go the remote server by ssh, enter the $HOME (~) folder
        # execute following commands
        # 0. prepare the python load the python 3.7.4
        # 1. git clone the repository to NIMB_HOME
        # 2. run the python file remote_setupv2.py
        #   a. get the remote name and address
        #   b. get the username password
        #   c. load the load python command
        #   d. connect ssh
        #   e. git clone
        #   f. setup freesurfer
        #   g. setup miniconda
        #   h. run the command to process ready
        # get the nimb_home at remote server
        load_python_3 = 'module load python/3.7.4; module load python/3.8.2;' # python 2 is okay, need to check
        cmd_git = f" cd ~; git clone {self.git_repo};  "
        cmd_install_miniconda = "python nimb/distribution/setup_miniconda.py; "
        cmd_run_setup = " cd nimb/setup; python nimb.py -process ready"

        cmd_run_crun_on_cluster = load_python_3 + cmd_git + cmd_install_miniconda + cmd_run_setup
        print("command: " + cmd_run_crun_on_cluster)
        # todo: how to know if the setting up is failed?
        print("Setting up the remote cluster")
        SSHHelper.running_command_ssh_2(host_name=host_name, user_name=self.user_name,
                                    user_password=self.user_password,
                                    cmd_run_crun_on_cluster=cmd_run_crun_on_cluster)

    @staticmethod
    def load_configuration_json(config_file ="../setup/local.json"):
        # todo: this method is going to be abandon later: reason stop
        # using static method
        with open(config_file) as file:
            config_dict = json.load(file)
        return config_dict
    @staticmethod
    def send_subject_data(config_file ="../setup/local.json"):
        """
        copy the subject to NIMB_NEW_SUBJECTS
        it can be on local computer
        or remote compyuter
        the list of subject is get by get_list_subject_to_be_processed_local_version for local
        and get_list_subject_to_be_processed_remote_version for remote
        :param config_file:
        :return:
        """
        # read all the json configruation files
        # check if it is FreeSurfer_install
        # if is local.json
        # send to NIMB_NEW_SUBJECTS
        # if remoe
        # send to NIMB_NEW_SUBECTS, choose the first remote
        # 1. read the local configuration files
        config_dict = DistributionHelper.load_configuration_json(config_file)
        if config_dict[DistributionHelper.freesurfer]["FreeSurfer_install"] == 1:
            send_path =  config_dict['NIMB_PATHS']['NIMB_NEW_SUBJECTS']
            # copy subject to this path, using shutil
            # todo: re-test the local part
            PROCESSED_FS_DIR = DistributionHelper.get_PROCESSED_FS_DIR(config_file=config_file)
            SOURCE_SUBJECTS_DIR = DistributionHelper.get_SOURCE_SUBJECTS_DIR(config_file=config_file)
            subjects = DistributionHelper.get_list_subject_to_be_processed_local_version(SOURCE_SUBJECTS_DIR=SOURCE_SUBJECTS_DIR,
                                                                                         PROCESSED_FS_DIR=PROCESSED_FS_DIR)
            for sj in subjects:
                shutil.copy(sj,send_path)
            return send_path
        elif config_dict[DistributionHelper.freesurfer]["FreeSurfer_install"] == 0: # check on remote cluster
            if "REMOTE" not in config_dict.keys():
                print("There is no remote server!")
                return
            # 2. get the first remote cluster
            for remote_name in [i for i in config_dict['LOCATION'] if i != 'local']: # get the first only
                cluster_name = remote_name
                break
            # 3. open the {cluster_name}.json
            cluster_config_dict = DistributionHelper.load_configuration_json(f"../setup/{cluster_name}.json")
            send_path = cluster_config_dict['NIMB_PATHS']['NIMB_NEW_SUBJECTS']
            # upload all files to send path
            # 1. get all the subject file path, using exisit helper method
            PROCESSED_FS_DIR = DistributionHelper.get_PROCESSED_FS_DIR(f"../setup/{cluster_name}.json")
            SOURCE_SUBJECTS_DIR = DistributionHelper.get_SOURCE_SUBJECTS_DIR(f"../setup/{cluster_name}.json")
            subjects_to_send = DistributionHelper.get_list_subject_to_be_processed_remote_version(SOURCE_SUBJECTS_DIR=SOURCE_SUBJECTS_DIR,
                                                                                                  PROCESSED_FS_DIR=PROCESSED_FS_DIR,
                                                                                                  remote = cluster_name)

            ssh_session = SSHHelper.getSSHSession(remote=cluster_name)
            # call upload_multiple_files_to_cluster for them
            SSHHelper.upload_multiple_files_to_cluster(ssh_session=ssh_session,dest_folder=send_path,file_list=subjects_to_send)
            #

            return send_path
            # 4. upload the subjects to that path
    @staticmethod
    def upload_subject_to_remote(local_path, remote_path, remote_host, remote_username, remote_password):
        # call the ssh helper to upload the file
        # to NIMB_NEW_SUBJECTS
        # SSHHelper.copy_subjects_to_cluster(mri_path, subjects_folder, a_folder)
        # upload_multiple_files_to_cluster()

        raise NotImplementedError
        pass

    @staticmethod
    def download_processed_subject(local_destination, remote_id, remote_path):
        """
        Download from processed folder back to local
        :param local_destination: place to stored downloaded files and folders
        :param remote_path:
        :param remote_host:
        :param remote_username:
        :param remote_password:
        :return: None
        """
        ssh_session = SSHHelper.getSSHSession(remote_id)
        stdin, stdout, stderr = ssh_session.exec_command('ls '+path_dst)
        ls_copy = [line.strip('\n') for line in stdout]
        sftp = ssh_session.open_sftp()
        for val in ls_copy:
                    size_src = SSHHelper.get_size_on_remote(ssh_session, path.join(path_dst, val))
                    print('left to copy: ',len(ls_copy[ls_copy.index(val):]))
                    SSHHelper.download_files_from_server(ssh_session, remote_path, local_destination)
                    size_dst = path.getsize(path_src+'/'+val)
                    if size_dst == size_src:
                        print('        copy ok')
                        #SSHHelper.remove_on_remote(path.join(path_dst, val))
                    else:
                        print('copy error, retrying ...')
        ssh_session.close()


    def StopAllActiveTasks():
        from distribution.SSHHelper import delete_all_running_tasks_on_cluster
        clusters = database._get_Table_Data('Clusters', 'all')
        delete_all_running_tasks_on_cluster(
            clusters[0][1], clusters[0][2], clusters[0][5], clusters[0][3])


# if __name__ == "__main__":
    # distribution = DistributionHelper(projects,
                                               # locations,
                                               # installers)
    # #DistributionHelper.is_setup_vars_folders(is_nimb_fs_stats=True, is_nimb_classification=True, is_freesurfer_nim=True)
    # user_name,user_password = DistributionHelper.get_username_password_cluster_from_sqlite()
    # cluster = "cedar.computecanada.ca"
    # subjects = DistributionHelper.get_list_subject_to_be_processed_remote_version("/Users/van/Downloads/tmp/fs","/home/hvt/tmp2",cluster,user_name,user_password)
    # print(subjects)
    # ssh = SSHHelper.getSSHSession(cluster, user_name, user_password)
    # # download data from remote
    # download_files_from_server(ssh,SOURCE_SUBJECTS_DIR,PROCESSED_FS_DIR)
    # ssh.close()

    # # send data
    # DistributionHelper.send_subject_data(config_file=path.join(credentials_home, "projects.json"))

if __name__ == "__main__":
    d = DistributionHelper()
    if d.is_setup_vars_folders(is_freesurfer_nim=True, is_nimb_fs_stats=True, is_nimb_classification=False): # True
        pass



    # def ready(self): #ALL READY MOVED TO DISTRIBUTION_READY
        # """
        # verify if NIMB is ready to be used
        # :return: bool
        # """
        # ready = True
        # self.verify_paths()
        # self.is_setup_vars(self.locations['local']['NIMB_PATHS'])
        # self.is_setup_vars(self.locations['local']['PROCESSING'])
        # if self.classify_ready():
            # print("NIMB ready to perform classification")
        # else:
            # ErrorMessages.error_classify()
            # ready = False
        # if self.fs_ready():
            # print("NIMB ready to perform FreeSurfer processing")
        # else:
            # ErrorMessages.error_fsready()
            # ready = False
        # return ready

    # def is_setup_vars(self, dict):
        # """
        # check if variables are defined in json
        # :param config_file: path to configuration json file
        # :return: True if there is no error, otherwise, return False
        # """
        # for key in dict:
            # if type(dict[key]) != int and len(dict[key]) < 1:
                # logger.fatal(f"{key} is missing")
                # return False
        # return True

    # def verify_paths(self):
        # # to verify paths and if not present - create them or return error
        # if path.exists(self.locations['local']['NIMB_PATHS']['NIMB_HOME']):
            # for p in (     self.NIMB_tmp,
                 # path.join(self.NIMB_tmp, 'mriparams'),
                 # path.join(self.NIMB_tmp, 'usedpbs'),
                           # self.locations['local']['NIMB_PATHS']['NIMB_NEW_SUBJECTS'],
                           # self.locations['local']['NIMB_PATHS']['NIMB_PROCESSED_FS'],
                           # self.locations['local']['NIMB_PATHS']['NIMB_PROCESSED_FS_error']):
                # if not path.exists(p):
                    # print('creating path ',p)
                    # makedir_ifnot_exist(p)

    # def classify_ready(self):
        # ready = True
        # for p in (self.locations['local']['NIMB_PATHS']['NIMB_NEW_SUBJECTS'],
                  # self.NIMB_HOME,self.NIMB_tmp):
            # if not path.exists(p):
                # try:
                    # # if path start with ~
                    # makedir_ifnot_exist(p)
                # except Exception as e:
                    # print(e)
            # if not path.exists(p):
                # ready = False
                # break
        # return ready

    # def fs_ready(self):
        # if self.locations['local']['FREESURFER']['FreeSurfer_install'] == 1:
            # if len(self.locations['local']['FREESURFER']['FREESURFER_HOME']) < 1:
                # logger.fatal("FREESURFER_HOME is missing.")
                # return False
            # if not path.exists(self.locations['local']['FREESURFER']['FS_SUBJECTS_DIR']):
                    # print('creating path ', self.locations['local']['FREESURFER']['FS_SUBJECTS_DIR'])
                    # makedir_ifnot_exist(self.locations['local']['FREESURFER']['FS_SUBJECTS_DIR'])
            # if self.check_freesurfer_ready():
                # return self.fs_chk_fsaverage_ready()
        # else:
            # return False

    # def fs_chk_fsaverage_ready(self):
        # self.fs_fsaverage_copy()
        # if not path.exists(path.join(self.locations['local']['FREESURFER']['FS_SUBJECTS_DIR'],'fsaverage', 'xhemi')):
            # print('fsaverage or fsaverage/xhemi is missing from SUBJECTS_DIR: {}'.format(self.locations['local']['FREESURFER']['FS_SUBJECTS_DIR']))
            # return False
        # else:
            # return True

    # def fs_fsaverage_copy(self):
        # if not path.exists(path.join(self.locations['local']['FREESURFER']['FS_SUBJECTS_DIR'],'fsaverage', 'xhemi')):
            # fsaverage_path = path.join(self.locations['local']['FREESURFER']['FREESURFER_HOME'], "subjects", "fsaverage")
            # shutil.copytree(fsaverage_path, path.join(self.vars['local']['FREESURFER']['FS_SUBJECTS_DIR'], 'fsaverage'))

    # def check_freesurfer_ready(self):
        # """
        # check and install freesurfer
        # :return:
        # """
        # ready = False
        # if not path.exists(path.join(self.locations['local']['FREESURFER']['FREESURFER_HOME'], "MCRv84")):
            # print('FreeSurfer must be installed')
            # from .setup_freesurfer import SETUP_FREESURFER
            # SETUP_FREESURFER(self.locations, self.installers)
            # ready = True
        # else:
            # print('start freesurfer processing')
            # ready =  True
        # return ready
        
        
    # def check_stats_ready(self):
        # """will check if xlsx file for project is provided
           # if all variables are provided
           # if all paths for stats are created
           # if NIMB is ready to perform statistical analysis"""
        # ready = False
        # file = self.projects[self.project_name]["GLM_file_group"]
        # if self.projects[self.project_name]["materials_DIR"][0] == 'local' and path.exists(path.join(self.projects[self.project_name]["materials_DIR"][1], file)):
            # ready = True
        # else:
            # print("data file is missing or not located on a local folder. Check file {}".format(path.join(self.credentials_home, 'projects.json', self.project_name)))
        # return ready
