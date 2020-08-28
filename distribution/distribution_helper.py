import sys
import shutil
from os import makedirs, system, path, listdir
import logging
from distribution import database
from setup.get_vars import Get_Vars
from distribution.setup_miniconda import setup_miniconda
from distribution.setup_freesurfer import SETUP_FREESURFER

from distribution.check_disk_space import *
from distribution import SSHHelper

# -- for logging, instead of using print --
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(module)s %(levelname)s: %(message)s')
logger.setLevel(logging.DEBUG)
# --


class ErrorMessages:
    @staticmethod
    def error_classify():
        print("NIMB is not ready to perform the classification. Please check the configuration files.")
        logger.fatal("NIMB is not ready to perform the classification. Please check the configuration files.")

    @staticmethod
    def error_fsready():
        print("NIMB not ready to perform FreeSurfer processing. Please check the configuration files.")
        logger.fatal("NIMB not ready to perform FreeSurfer processing. Please check the configuration files.")

    @staticmethod
    def password():
        print("password to login to remote cluster is missing")
        logger.fatal("password to login to remote cluster is missing")

    @staticmethod
    def error_nimb_ready():
        print(" NIMB is not yet set up")
        logger.fatal(" NIMB is not yet set up")
    @staticmethod
    def error_stat_path():
        logger.fatal("STATS_PATHS or STATS_HOME is missing")
        print("STATS_PATHS is missing")

class DistributionHelper():

    def __init__(self, credentials_home, projects, locations, installers, project):

        self.NIMB_HOME = locations["local"]["NIMB_PATHS"]["NIMB_HOME"]
        self.NIMB_tmp = locations["local"]["NIMB_PATHS"]["NIMB_tmp"]
        self.locations = locations # ưlocal, remote] json configuration
        self.projects = projects # project.json
        self.credentials_home = credentials_home
        self.project_name = project
        # self.var = Get_Vars().get_default_vars()
        self.user_name, self.user_password = self.get_username_password_cluster_from_sqlite()


    def get_username_password_cluster_from_sqlite(self):
        """
        get user name and password from sqlite database
        :return: username, password in string
        """
        try:
            clusters = database._get_Table_Data('Clusters', 'all')
            user_name = clusters[list(clusters)[0]]['Username']
            user_password = clusters[list(clusters)[0]]['Password']
            return user_name, user_password
            if len(user_name) < 1or len(user_password) < 1:
                ErrorMessages.password()
                return False
        except TypeError:
            return 'none', 'none'

# =========================================
# UNITE:
# ready, classify_ready, fs_ready and verify_paths must be put together in the is_setup_vars_folders


    def is_setup_vars_folders(self,is_freesurfer_nim=False,
                              is_nimb_classification=False,
                              is_nimb_fs_stats=False):
        """
        check if those variables are defined in json or not
        for example check NIMB_PATHS exists in the local.json
        :param config_file: path to configuration json file
        :param is_freesurfer_nim: True if run nimb freesurfer
        :param is_nimb_classification:
        :param is_nimb_fs_stats:
        :return: True if there is no error, otherwise, return False
        """
        # check path exisits and create path if needed
        self.verify_paths()

        if is_nimb_classification or is_freesurfer_nim:
            if "NIMB_PATHS" not in self.locations['local'].keys():
                logger.fatal("NIMB_PATHS is missing")
                # sys.exit()
                return False
            for key, val in self.locations['local']:
                if len(val) < 1:
                    logger.fatal(f"{key} is missing")
                    return False
        if is_nimb_fs_stats:
            if "STATS_PATHS" not in self.locations['local'].keys():
                ErrorMessages.error_stat_path()
                return False
            if "STATS_HOME" not in self.locations['local']['STATS_PATHS']:
                ErrorMessages.error_stat_path()
                return False

        if self.locations['local']['FREESURFER']['FreeSurfer_install'] == 1:
            if len(self.locations['local']['FREESURFER']['FREESURFER_HOME']) < 1:
                logger.fatal("FREESURFER_HOME is missing.")
                return False
            if "MRDATA_PATHS" not in self.locations['local'].keys():
                logger.fatal("MRDATA_PATHS is missing.")
                return False
        return True
    def ready(self):
        """
        verify if NIMB is ready to be used
        :return: bool
        """
        ready = True
        if not self.classify_ready():
            ErrorMessages.error_classify()
            ready = False
        else:
            print("NIMB ready to perform classification")
        if not self.fs_ready():
            ErrorMessages.error_fsready()
            ready = False
        else:
            print("NIMB ready to perform FreeSurfer processing")
        return ready

    def classify_ready(self):
        ready = True
        for p in (self.locations['local']['NIMB_PATHS']['NIMB_NEW_SUBJECTS'],
                  self.NIMB_HOME,self.NIMB_tmp):
            if not path.exists(p):
                try:
                    makedirs(p)
                except Exception as e:
                    print(e)
            if not path.exists(p):
                ready = False
                break
        return ready

    def exisit_or_created(self, folder_name):
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)

    def fs_ready(self):
        if self.locations['local']['FREESURFER']['FreeSurfer_install'] == 1:
            if self.fs_chk_folders_ready():
                return self.check_freesurfer_ready()
        else:
            return False

    def fs_chk_folders_ready(self):
        if 'fsaverage' in listdir(self.locations['local']['FREESURFER']['FS_SUBJECTS_DIR']):
            if 'xhemi' in listdir(path.join(self.locations['local']['FREESURFER']['FS_SUBJECTS_DIR'],'fsaverage')):
                return True
            else:
                print(' fsaverage/xhemi is missing')
                return False
        else:
             print(' fsaverage is missing in SUBJECTS_DIR')
             return False


    def verify_paths(self):
        # to verify paths and if not present - create them or return error
        if path.exists(self.vars['local']['NIMB_PATHS']['NIMB_HOME']):
            for p in (     self.NIMB_tmp,
                 path.join(self.NIMB_tmp, 'mriparams'),
                 path.join(self.NIMB_tmp, 'usedpbs'),
                           self.vars['local']['NIMB_PATHS']['NIMB_NEW_SUBJECTS'],
                           self.vars['local']['NIMB_PATHS']['NIMB_PROCESSED_FS'],
                           self.vars['local']['NIMB_PATHS']['NIMB_PROCESSED_FS_error']):
                if not path.exists(p):
                    print('creating path ',p)
                    makedirs(p)
        if path.exists(self.vars['local']['FREESURFER']['FREESURFER_HOME']):
            if not path.exists(self.vars['local']['FREESURFER']['FS_SUBJECTS_DIR']):
                    print('creating path ',p)
                    makedirs(self.vars['local']['FREESURFER']['FS_SUBJECTS_DIR'])
                    system("cp -r"+path.join(self.vars['local']['FREESURFER']['FREESURFER_HOME'], "subjects", "fsaverage")+" "+self.vars['local']['FREESURFER']['FS_SUBJECTS_DIR'])
# UNITE until here
# =========================================

    def get_project_vars(self, var_name, project):
        """
        get the PROCESSED_FS_DIR
        :param config_file:
        :var_name: like PROCESSED_FS_DIR
        :return: empty string, or values
        """
        # PROJECT_DATA
        if project not in self.projects.keys():
            print("There is no path for project: "+project+" defined. Please check the file: "+path.join(self.credentials_home, "projects.json"))
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

    def get_installers_json(self, installers_file = "../setup/installers.json"):
        """
        read the installers.json configuration
        :param installers_file:
        :return: None or the dictionary from json file
        """
        if not path.isfile(installers_file):
            print("installer file is not defined")
            return None
        with open(installers_file, 'rt') as file:
            installers = json.load(file)
        return installers


    def run(self, Project):
        """
        # todo: need to find a location for this function
        :param Project:
        :return:
        """
        # 0 check the variables
        # if FreeSurfer_install = 1:
        if self.fs_ready():
            # 1. install required library and software on the local computer, including freesurfer
            self.setting_up_local_computer()
            # install freesurfer locally
            installers = self.get_installers_json(installers_file="../setup/installers.json")
            setup = SETUP_FREESURFER(self.locations,installers=installers)
        else:
            logger.debug("Setting up the remote server")
            # 2. check and install required library on remote computer
            self.setting_up_remote_linux_with_freesurfer()

        print("get list of un-process subject. to be send to the server")
        # must set SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR before calling
        # DistributionHelper.get_list_subject_to_be_processed_remote_version(SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR)
        # how this part work?
        # status.set('Copying data to cluster ')
        logger.debug('Copying data to cluster ')
        #  copy subjects to cluster
        self.run_copy_subject_to_cluster(Project)
        # status.set('Cluster analysis started')
        # status.set("Cluster analysing running....")
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


    def check_freesurfer_ready(self):
        """
        check and install freesurfer
        :return:
        """
        ready = False
        if not path.exists(path.join(self.locations['local']['FREESURFER']['FREESURFER_HOME'], "MCRv84")):
            print('FreeSurfer must be installed')
            from .setup_freesurfer import SETUP_FREESURFER
            SETUP_FREESURFER(self.vars, self.installers)
            ready = True
        else:
            print('start freesurfer processing')
            ready =  True
        return ready


    def nimb_stats_ready(self, project):
        """will check if the STATS folder is present and will create if absent
           will return the folder with unzipped stats folder for each subject"""

        if not path.exists(self.locations["local"]["STATS_PATHS"]["STATS_HOME"]):
            makedirs(self.locations["local"]["STATS_PATHS"]["STATS_HOME"])

        PROCESSED_FS_DIR = self.projects[project]["PROCESSED_FS_DIR"]
        
        if any('.zip' in i for i in listdir(PROCESSED_FS_DIR)):
            from .manage_archive import ZipArchiveManagement
            zipmanager = ZipArchiveManagement()
            tmp_dir = path.join(self.NIMB_tmp, 'tmp_subject_stats')
            if not path.exists(tmp_dir):
                makedirs(tmp_dir)
            zipmanager.extract_archive(PROCESSED_FS_DIR, ['stats',], tmp_dir)
            return tmp_dir
        else:
            return PROCESSED_FS_DIR
        print('perform statistical analysis')


    def fs_glm(self):

        print('start freesurfer GLM')

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

    def setting_up_remote_linux_with_freesurfer(self):
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
        clusters = database._get_Table_Data('Clusters', 'all')
        # user_name = clusters[list(clusters)[0]]['Username']
        # user_password = clusters[list(clusters)[0]]['Password']
        git_repo = "https://github.com/alexhanganu/nimb"
        # get the nimb_home at remote server
        load_python_3 = 'module load python/3.7.4;'
        cmd_git = f" cd ~; git clone {git_repo};  "
        cmd_run_setup = " cd nimb/setup; python nimb.py -process ready"

        cmd_run_crun_on_cluster = load_python_3 + cmd_git + cmd_run_setup
        print("command: " + cmd_run_crun_on_cluster)
        host_name = clusters[list(clusters)[0]]['remote_address']
        # todo: how to know if the setting up is failed?
        print("Setting up the remote cluster")
        SSHHelper.running_command_ssh_2(host_name=host_name, user_name=self.user_name,
                                    user_password=self.user_password,
                                    cmd_run_crun_on_cluster=cmd_run_crun_on_cluster)


    @staticmethod
    def is_all_subject_processed(SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR):
        """
        must be absolute path
        :param SOURCE_SUBJECTS_DIR:
        :param PROCESSED_FS_DIR:
        :return:
        """
        un_process_sj = ListSubjectHelper.get_to_be_processed_subject_local(SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR)
        if len(un_process_sj) > 0:
            return True
        return False

    @staticmethod
    def get_list_subject_to_be_processed_local_version(SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR):
        """
        both SOURCE_SUBJECTS_DIR and PROCESSED_FS_DIR is inside a single computer (i.e., local pc)

        1. get the list of un-processed subject
        2. get the current available space on hard-disk of user
        2. calculate the list of
		initial script in database -> create_lsmiss
        :param SOURCE_SUBJECTS_DIR:
        :return:
        """
        # get the list of unprocessed subjects
        un_process_sj = ListSubjectHelper.get_to_be_processed_subject_local(SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR)
        un_process_sj = [os.path.join(SOURCE_SUBJECTS_DIR,file) for file in un_process_sj ]
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
    @staticmethod
    def get_list_subject_to_be_processed_remote_version(SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR,
                                                        remote_host, remote_username, remote_password):
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
        ssh_session = getSSHSession(remote_host, remote_username, remote_password)
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
            for remote_name, remote_add in config_dict['REMOTE'].items(): # get the first only
                cluster_name = remote_name
                cluster_address = remote_add
                break
            # 3. open the {cluster_name}.json
            cluster_config_dict = DistributionHelper.load_configuration_json(f"../setup/{cluster_name}.json")
            send_path = cluster_config_dict['NIMB_PATHS']['NIMB_NEW_SUBJECTS']
            # upload all files to send path
            # 1. get all the subject file path, using exisit helper method
            PROCESSED_FS_DIR = DistributionHelper.get_PROCESSED_FS_DIR(f"../setup/{cluster_name}.json")
            SOURCE_SUBJECTS_DIR = DistributionHelper.get_SOURCE_SUBJECTS_DIR(f"../setup/{cluster_name}.json")
            user_name, user_password = DistributionHelper.get_username_password_cluster_from_sqlite()
            subjects_to_send = DistributionHelper.get_list_subject_to_be_processed_remote_version(SOURCE_SUBJECTS_DIR=SOURCE_SUBJECTS_DIR,
                                                                                                  PROCESSED_FS_DIR=PROCESSED_FS_DIR,
                                                                                                  remote_host=cluster_address,
                                                                                                  remote_username=user_name,
                                                                                                  remote_password=user_password)

            ssh_session = getSSHSession(remote_host=cluster_address, remote_username=user_name, remote_password=user_password)
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
    def check_status_of_free_surfer():
        """
        not implement yet
        :return:
        """
        raise NotImplementedError

    @staticmethod
    def download_processed_subject(local_destination, remote_path, remote_host, remote_username, remote_password):
        """
        Download from processed folder back to local
        :param local_destination: place to stored downloaded files and folders
        :param remote_path:
        :param remote_host:
        :param remote_username:
        :param remote_password:
        :return: None
        """
        ssh_session = getSSHSession(remote_host, remote_username, remote_password)
        download_files_from_server(ssh_session, remote_path, local_destination)
        ssh_session.close()

    @staticmethod
    def move_processed_to_storage():
        '''
        this script is a copy paste, it must be adapted. Storage folder (i.e., for ADNI is beluga../projects/../adni)
        '''
        HOST = 'beluga.calculquebec.ca'
        '''
        username = 'string' # username to access the remote computer
        mot_de_pass = 'string' # password to access the remote computer
        HOST = 'name.address.com' # host name of the remote computer
        '''

        from os import listdir, system, mkdir, path, chdir, getuid, getenv, environ, remove
        import shutil, getpass, time
        import paramiko
        environ['TZ'] = 'US/Eastern'
        time.tzset()
        dthm = time.strftime('%Y%m%d_%H%M')

        path_credentials = path.join('/home',username) # path to the txt-like file named "credentials" that will contain the follow$
        path_log = path.join(path.join('/home',username,'projects','def-hanganua'), 'scripts', 'scp_log.txt') # path where a log file will be stored tha$
        path_src = path.join(path.join('/home',username,'projects','def-hanganua'), 'subjects_processed') # path that contains the files or folders t$
        path_dst_dir = path.join(path.join('/home',username,'projects','def-hanganua'), 'adni', 'processed_fs') # on beluga

        path_scratch = path.join('/scratch',username)
        path_processed = path.join(path_projects,'subjects_processed')


        shutil.copy(path.join(path_credentials,'credentials'), path.dirname(path.abspath(__file__))+'/credentials.py')
        try:
                from credentials import mot_de_pass
                remove(path.dirname(path.abspath(__file__))+'/credentials.py')
        except ImportError:
                print('file with credentials was not found')
                raise SystemExit()

        def _get_client(HOST, username, mot_de_pass):
            # setting up the remote connection
            client = paramiko.SSHClient()
            host_keys = client.load_system_host_keys()
            return client.connect(HOST, username=username, password=mot_de_pass)

        def get_ls2copy(client, path_dst, path_src):
            # retrieving the list of files in the source folder
            ls_src = [i for i in listdir(path_src) if '.zip' in i]
            # retrieving the list of files in the destination folder
            ls_dst = list()
            stdin, stdout, stderr = client.exec_command('ls '+path_dst)
            for line in stdout:
                    ls_dst.append(line.strip('\n'))
            return [i for i in ls_src if i not in ls_dst]

        def cp2remote_rm_from_local(client, ls_copy, path_src, username, HOST, path_dst, path_log):
            # copying the files
            ls_copy_error = list()
            sftp = client.open_sftp()
            for val in ls_copy:
                    size_src = path.getsize(path_src+'/'+val)
                    # sftp.put(path_src+'/'+val, path_dst)
                    print('left to copy: ',len(ls_copy[ls_copy.index(val):]))
                    system('scp '+path_src+'/'+val+' '+username+'@'+HOST+':'+path_dst)
                    size_dst = sftp.stat(path_dst+'/'+val).st_size
                    if size_dst != size_src:
                            print('        copy error')
                            ls_copy_error.append(val)
                    else:
                            remove(path_src+'/'+val)
            saving_ls2log(ls_copy_error, path_log)

        def saving_ls2log(ls_copy_error, path_log):
            print('copy error: ',ls_copy_error)
            with open(path_log,'w') as f:
                    for val in ls_copy_error:
                            f.write(val+'\n')

        client = _get_client(HOST, username, mot_de_pass)
        ls_copy = get_ls2copy(client, path_dst, path_src)
        cp2remote_rm_from_local(client, ls_copy, path_src, username, HOST, path_dst)
        client.close()


    def runstats(Project_Data, Project):
        try:
            os.system('python nimb.py -process fs-glm')
            status.set('performing freesurfer whole brain GLM analysis')
        except Exception as e:
            print(e)
            pass
        
    def cstatus():
        try:
            clusters = database._get_Table_Data('Clusters', 'all')
            from distribution.SSHHelper import check_cluster_status
            cuser = clusters[0][1]
            caddress = clusters[0][2]
            cpw = clusters[0][5]
            cmaindir = clusters[0][3]
            status.set('Checking the Cluster')
            status.set('There are '
                   + str(check_cluster_status(cuser,
                                              caddress, cpw, cmaindir)[0])
                   + ' sessions and '
                   + str(check_cluster_status(cuser,
                                              caddress, cpw, cmaindir)[1])
                   + ' are queued')
        except FileNotFoundError:
            setupcredentials()
            clusters = database._get_Table_Data('Clusters', 'all')
            cstatus()


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
    # ssh = getSSHSession(cluster, user_name, user_password)
    # # download data from remote
    # download_files_from_server(ssh,SOURCE_SUBJECTS_DIR,PROCESSED_FS_DIR)
    # ssh.close()

    # # send data
    # DistributionHelper.send_subject_data(config_file=path.join(credentials_home, "projects.json"))
    
    
    
    
'''


MainFolder = database._get_folder('Main')
DIRs_INCOMING = database._get_folder('MRI')

dirrawdata = MainFolder+'raw_t1/'

def chklog():
    print('testing check log')
    n2del=('.DS_Store','Thumbs.db','results.txt', 'notes.txt')
    lsmri = {}
    Processed_Subjects = {}
    for DIR in DIRs_INCOMING:
        ls = listdir(DIRs_INCOMING[DIR])
        for n in n2del:
            if n in ls:
                ls.remove(n)
        lsmri[DIR] = sorted(ls)
        Processed_Subjects[DIR] = database._get_list_processed_subjects(DIR)
    lsmiss = {}
    for DIR in lsmri:
        lsmiss[DIR] = [x for x in lsmri[DIR] if x not in Processed_Subjects[DIR]]
    return lsmiss


def predict_error(src, dst):   #code by Mithril
    if path.exists(dst):
        src_isdir = path.isdir(src)
        dst_isdir = path.isdir(dst)
        if src_isdir and dst_isdir:
            pass
        elif src_isdir and not dst_isdir:
            yield {dst:'src is dir but dst is file.'}
        elif not src_isdir and dst_isdir:
            yield {dst:'src is file but dst is dir.'}
        else:
            yield {dst:'already exists a file with same name in dst'}

    if path.isdir(src):
        for item in listdir(src):
            s = path.join(src, item)
            d = path.join(dst, item)
            for e in predict_error(s, d):
                yield e

def copytree(src, dst, symlinks=False, ignore=None, overwrite=False): #code by Mithril
#    would overwrite if src and dst are both file
#    but would not use folder overwrite file, or viceverse

    if not overwrite:
        errors = list(predict_error(src, dst))
        if errors:
            raise Exception('copy would overwrite some file, error detail:%s' % errors)

    if not path.exists(dst):
        makedirs(dst)
        shutil.copystat(src, dst)
    lst = listdir(src)
    if ignore:
        excl = ignore(src, lst)
        lst = [x for x in lst if x not in excl]
    for item in lst:
        s = path.join(src, item)
        d = path.join(dst, item)
        if symlinks and path.islink(s):
            if path.lexists(d):
                remove(d)
            symlink(readlink(s), d)
            try:
                st = lstat(s)
                mode = stat.S_IMODE(st.st_mode)
                lchmod(d, mode)
            except:
                pass  # lchmod not available
        elif path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            if not overwrite:
                if path.exists(d):
                    continue
            shutil.copy2(s, d)

def copy(src, dst):
    if path.isdir(dst):
        if len(listdir(src)) == len(listdir(dst)):
            print(time.strftime('%Y-%m-%d, %H:%M', time.localtime())+' '+dst+' folder already exists')
            with open(MainFolder+'logs/log_copylog.txt', 'a') as f:
                f.write('          folder already exists'+' '+dst+' '+time.strftime('%Y-%m-%d, %H:%M', time.localtime())+'\n')
            sum1 = sum(path.getsize(src+'/'+f) for f in listdir(src) if path.isfile(src+'/'+f))
            sum2 = sum(path.getsize(dst+'/'+f) for f in listdir(dst) if path.isfile(dst+'/'+f))
            if sum1 == sum2:
                f1 = listdir(src)
                f2 = listdir(dst)
                if f1[0] == f2[0]:
                    print('files similar, folders similar in size')
                    with open(MainFolder+'logs/log_copylog.txt', 'a') as f:
                        f.write('          folder already exists, files similar, '+' '+dst+' '+time.strftime('%Y-%m-%d, %H:%M', time.localtime())+'\n')
                else:
                    print('!!!!!!!!!!!!!!!FILES DIFFER')
                    with open(MainFolder+'logs/log_copylog.txt', 'a') as f:
                        f.write('          folder already exists, !!!!!!!!!!!!!!!FILES DIFFER'+' '+dst+' '+time.strftime('%Y-%m-%d, %H:%M', time.localtime())+'\n')

            else:
                print('DIFFERENT DATA', sum1, sum2)
                with open(MainFolder+'logs/log_copylog.txt', 'a') as f:
                    f.write('          folder already exists, DIFFERENT DATA'+' '+dst+' '+time.strftime('%Y-%m-%d, %H:%M', time.localtime())+'\n')

        else:
            print(time.strftime('%Y-%m-%d, %H:%M', time.localtime())+' ERRROR !!! file '+dst+' exists and differs from source')
            with open(MainFolder+'logs/log_copylog.txt', 'a') as f:
                f.write('          ERRROR !!! folder exists and differs from source'+dst+' '+time.strftime('%Y-%m-%d, %H:%M', time.localtime())+'\n')
            f1 = listdir(src)
            f2 = listdir(dst)
            if f1[0] == f2[0]:
                print('files similar')
                if len(listdir(src)) > len(listdir(dst)):
                    print('          ATTENTION!!! SOURCE folder has more files than DESTINATION folder and the first file names are similar, copying'+' '+src+' TO '+dst)
                    with open(MainFolder+'logs/log_copylog.txt', 'a') as f:
                        f.write('\n'+time.strftime('%Y-%m-%d, %H:%M', time.localtime())+'          ATTENTION!!! SOURCE folder has more files than DESTINATION folder and the first file names are similar, COPYING'+' '+src+' TO '+dst+'\n')
                    print('removing '+dst)
                    for file in listdir(dst):
                        remove(dst+'/'+file)
                    copytree(src,dst)
                else:
                    print('          ATTENTION!!! SOURCE folder has fewer files than DESTINATION folder, I will pass')
                    with open(MainFolder+'logs/log_copylog.txt', 'a') as f:
                        f.write('          ATTENTION!!! SOURCE folder has fewer files than DESTINATION folder, I will pass\n')
            else:
                print('!!!!!!!!!!!!!!!FILES DIFFER')
                dst_v2 = dst+'_v2'
                copytree(src,dst_v2)            
    else:
        print('copying'+' '+src+' TO '+dst)
        with open(MainFolder+'logs/log_copylog.txt', 'a') as f:
            f.write('\n'+time.strftime('%Y-%m-%d, %H:%M', time.localtime())+' COPYING'+' '+src+' TO '+dst+'\n')
        copytree(src,dst)


def define_SUBJID(DIR, id):
    name=('PDMCI','PD-MCI','PD_MCI', 'pdmci')
    SESSION_names = ['B','C']
    LONGITUDINAL_DEFINITION = ['T2','T3']

    if DIR == 'INCOMING':
                for n in name:
                    if any(n in i for i in id):
                        id=id[0]
                        pos_mci_in_id=[i for i, s in enumerate(id) if 'I' in s]
                        SUBJECT_NR=id[pos_mci_in_id[0]+1:]
                        SUBJECT_NR = SUBJECT_NR.replace('-','').replace('_','')
                        if SUBJECT_NR[0] =='0':
                            SUBJECT_NR = SUBJECT_NR[1:]
                session_ = ''
                for session in SESSION_names:
                    if session in SUBJECT_NR:
                        position = [i for i, s in enumerate(SUBJECT_NR) if session in s]
                        SUBJECT_NR = SUBJECT_NR.replace(SUBJECT_NR[position[0]], '')
                        session_ = session
                for LONG in LONGITUDINAL_DEFINITION:
                            if LONG in SUBJECT_NR:
                                longitudinal = True
                                longitudinal_name = LONG
                                break
                            else:
                                longitudinal = False
                if longitudinal:
                    SUBJECT_NR = SUBJECT_NR.replace(longitudinal_name, '')
                    SUBJECT_ID = 'pdmci'+SUBJECT_NR+longitudinal_name
                    FILE_name = SUBJECT_ID+session_
                else:
                    SUBJECT_ID = 'pdmci'+SUBJECT_NR
                    FILE_name = SUBJECT_ID+session_
    else:
                SUBJECT_ID = id[0].replace(' ','_')
                FILE_name = SUBJECT_ID

    database.update_ls_subj2fs(SUBJECT_ID)

    return(FILE_name)


def copy_T1_and_Flair_files(DIR, dir2read, lsdir, FILE_name):
    MR_T1 = ('IR-FSPGR','IRFSPGR','CCNA','MPRAGE','MPRage')
    MR_Flair = ('Flair','FLAIR')
    MR_PURE = ('PURE','PU')

    for T1 in MR_T1:
                if any(T1 in i for i in lsdir):
                    positionT1=[i for i, s in enumerate(lsdir) if T1 in s]
                    ls_pos_fT12cp = []
                    for posT1 in positionT1:
                        for PURE in MR_PURE:
                            if PURE in lsdir[posT1]:
                                if posT1 not in ls_pos_fT12cp:
                                    ls_pos_fT12cp.append(posT1)
                            elif T1 == 'MPRAGE' or T1 == 'MPRage':
                                if posT1 not in ls_pos_fT12cp:
                                    ls_pos_fT12cp.append(posT1)
                    if len(ls_pos_fT12cp) == 1:
                        if '.dcm' in listdir(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[ls_pos_fT12cp[0]])[0]:
                            src_T1=(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[ls_pos_fT12cp[0]])
                            dst_T1 = (dirrawdata+FILE_name+'_t1')
                            print(src_T1, dst_T1)
                            if path.isdir(src_T1):
                                copy(src_T1,dst_T1)
                                with open(MainFolder+'logs/f2cp','a') as f:
                                    f.write(FILE_name+'_t1'+'\n')
                            else:
                                print(src_T1+' is not a folder')
                        else:
                            ls_subDIRs = listdir(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[ls_pos_fT12cp[0]])
                            if len(ls_subDIRs) == 1:
                                    if '.dcm' in listdir(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[ls_pos_fT12cp[0]]+'/'+ls_subDIRs[0])[0]:
                                        src_T1=(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[ls_pos_fT12cp[0]]+'/'+ls_subDIRs[0])
                                        dst_T1 = (dirrawdata+FILE_name+'_t1')
                                        if path.isdir(src_T1):
                                            print(src_T1, dst_T1)
                                            copy(src_T1,dst_T1)
                                            with open(MainFolder+'logs/f2cp','a') as f:
                                                f.write(FILE_name+'_t1'+'\n')
                                        else:
                                            print(src_T1+' is not a folder')
                            else:
                                for subDIR in ls_subDIRs:
                                    if '.dcm' in listdir(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[ls_pos_fT12cp[0]]+'/'+subDIR)[0]:
                                        src_T1=(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[ls_pos_fT12cp[0]]+'/'+subDIR)
                                        dst_T1 = (dirrawdata+FILE_name+'_t1')
                                        if path.isdir(src_T1):
                                            print(src_T1, dst_T1)
                                            copy(src_T1,dst_T1)
                                            with open(MainFolder+'logs/f2cp','a') as f:
                                                f.write(FILE_name+'_t1'+'\n')
                                        else:
                                            print(src_T1+' is not a folder')
                    else:
                        n = 1
                        for pos_f2cp in ls_pos_fT12cp:
                            src_T1=(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[pos_f2cp])
                            if len(listdir(src_T1)) > 170:
                                v = '_v'+str(n)
                                dst_T1 = (dirrawdata+FILE_name+'_t1'+v)
                                print(src_T1, dst_T1)
                                if path.isdir(src_T1):
                                    copy(src_T1,dst_T1)
                                    with open(MainFolder+'logs/f2cp','a') as f:
                                        f.write(FILE_name+'_t1'+v+'\n')
                                else:
                                    print(src_T1+' is not a folder')
                                n += 1

    for Flair in MR_Flair:
                if any(Flair in i for i in lsdir):
                    position_Flair=[i for i, s in enumerate(lsdir) if Flair in s]
                    ls_pos_fFlair2cp = []
                    for posFlair in position_Flair:
                        for PURE in MR_PURE:
                            if PURE in lsdir[posFlair]:
                                if 'FLB' not in lsdir[posFlair]:
                                    if posFlair not in ls_pos_fFlair2cp:
                                        ls_pos_fFlair2cp.append(posFlair)
                        if len(ls_pos_fFlair2cp) == 0:
                            if MR_PURE[0] and MR_PURE[1] not in lsdir[posFlair]:
                                if len(position_Flair) == 1:
                                    ls_pos_fFlair2cp.append(posFlair)
                    if len(ls_pos_fFlair2cp) == 1:
                        src_Flair=(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[ls_pos_fFlair2cp[0]])
                        dst_Flair = (dirrawdata+FILE_name+'_flair')
                        print(src_Flair, dst_Flair)
                        if path.isdir(src_Flair):
                            copy(src_Flair,dst_Flair)
                            with open(MainFolder+'logs/f2cp','a') as f:
                                f.write(FILE_name+'_flair'+'\n')
                        else:
                            print(src_Flair+' is not a folder')
                    else:
                        n = 1
                        for pos_f2cp in ls_pos_fFlair2cp:
                            v = '_v'+str(n)
                            src_Flair=(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[pos_f2cp])
                            dst_Flair = (dirrawdata+FILE_name+'_flair'+v)
                            print(src_Flair, dst_Flair)
                            if path.isdir(src_Flair):
                                copy(src_Flair,dst_Flair)
                                with open(MainFolder+'logs/f2cp','a') as f:
                                    f.write(FILE_name+'_flair'+v+'\n')
                            else:
                                print(src_Flair+' is not a folder')
                            n+= 1
    print('FINISHED copying T1 and Flair for all subjects')


def copy_T1_file(DIR, dir2read, FILE_name):
    src_T1=(DIRs_INCOMING[DIR]+dir2read)
    if len(listdir(src_T1)) > 170:
                                dst_T1 = (dirrawdata+FILE_name+'_t1')
                                print(src_T1, dst_T1)
                                if path.isdir(src_T1):
                                    copy(src_T1,dst_T1)
                                    with open(MainFolder+'logs/f2cp','a') as f:
                                        f.write(FILE_name+'_t1'+'\n')
                                else:
                                    print(src_T1+' is not a folder')


def cpt1flair():
#    will copy the t1 and flair files from the Incoming folder to the
#    MainFolder raw_t1 folder based on the logmiss.xlsx file

    lsmiss = database._get_lsmiss()

    for DIR in lsmiss:
        for dir2read in lsmiss[DIR]:
            if path.isdir(DIRs_INCOMING[DIR]+dir2read):
                if len(listdir(DIRs_INCOMING[DIR]+dir2read))>0:
                    id=[dir2read]
                    FILE_name = define_SUBJID(DIR, id)
                    if '.dcm' in listdir(DIRs_INCOMING[DIR]+dir2read)[0]:
                        print('1 lvl: file name is: '+str(FILE_name))
                        copy_T1_file(DIR, dir2read, FILE_name)
                    elif len(listdir(DIRs_INCOMING[DIR]+dir2read)) ==1 and '.dcm' in listdir(DIRs_INCOMING[DIR]+dir2read+'/'+listdir(DIRs_INCOMING[DIR]+dir2read)[0])[0]:
                        print('1a lvl: file name is: '+str(FILE_name))
                        dir2cp = dir2read+'/'+listdir(DIRs_INCOMING[DIR]+dir2read)[0]
                        copy_T1_file(DIR, dir2cp, FILE_name)                  
                    else:
                        print('2 lvl: file name is: '+str(FILE_name))
                        lsdir = listdir(DIRs_INCOMING[DIR]+dir2read)
                        copy_T1_and_Flair_files(DIR, dir2read, lsdir, FILE_name)
                    database._update_list_processed_subjects(DIR, dir2read)
                else:
                    print(dir2read+' is empty')
            else:
                print(dir2read+' is not a folder; skipping')
            database._update_lsmiss(DIR, dir2read)

def cp2cluster():
#    will copy the t1 and flair folders from the raw_t1 to the cluster
#    in the "subjects" folder. Removes the logmiss.xlsx, subj2fs, f2cp files

    from sys import platform
    from distribution.lib.SSHHelper import start_cluster


    def platform_linux_darwin(cuser, caddress, subj2cp, dirs2cp, cmaindir):
            ls_complete_name = []
            system('sftp '+cuser+'@'+caddress)
            time.sleep(10)
            for dir2cp in dirs2cp:
                    system('mkdir subjects/'+dir2cp)
                    for file in listdir(MainFolder+'/'+dir2cp):
                        system('put '+MainFolder+'/'+dir2cp+'/'+file+' '+'subjects/'+dir2cp)
                    dir = dirrawdata+dir2cp
                    ls_complete_name.append(dir)
            onename_dirs2cp = ' '.join(ls_complete_name)
            system('scp -r '+onename_dirs2cp+' '+cuser+'@'+caddress+':'+cmaindir+'subjects/')
            system('put '++subj2cp+' '+cmaindir+'a/')
            system('exit')


    def platform_win(cuser, caddress, subj2cp, dirs2cp, cmaindir, cpw):
            print(MainFolder)
            open(MainFolder+'logs/psftpcp2cluster.scr','w').close()
            with open(MainFolder+'logs/psftpcp2cluster.scr','a') as scr:
                scr.write('put -r '+subj2cp+' '+cmaindir+'a/subj2fs\n')
            with open(MainFolder+'logs/psftpcp2cluster.scr','a') as scr:
                for dir2cp in dirs2cp:
                    scr.write('put -r '+dirrawdata+dir2cp+' '+cmaindir+'subjects/'+dir2cp+'\n')
            time.sleep(1)
            system('psftp '+cuser+'@'+caddress+' -pw '+cpw+' -b '+MainFolder+'logs/psftpcp2cluster.scr')
            #remove(MainFolder+'logs/psftpcp2cluster.scr')

    #print((MainFolder+'logs/subj2fs');
    MainFolder = "Z:/iugm_hoangvantien/nimb_01908/project1/"
    if path.isfile("Z:/iugm_hoangvantien/nimb_01908/project1/logs/subj2fs"):
        lssubj = [line.rstrip('\n') for line in open(MainFolder+'logs/subj2fs')]
        if len(lssubj)>1:
            print(str(len(lssubj))+' subjects need to be processed')
        dirs2cp = [line.rstrip('\n') for line in open(MainFolder+'logs/f2cp')]
        clusters = database._get_credentials('all')
        if len(clusters) == 1:
            for cred in clusters:
                cname = cred
                cuser = clusters[cred][0]
                caddress = clusters[cred][1]
                cmaindir = clusters[cred][2]
                cpw = clusters[cred][4]
                if platform == 'darwin' or platform == 'linux' or platform == 'linux2':
                    platform_linux_darwin(cuser, caddress, 'subj2fs', dirs2cp, cmaindir)
                elif platform == 'win32':
                    platform_win(cuser, caddress, 'subj2fs', dirs2cp, cmaindir, cpw)
            start_cluster()
        elif len(clusters) > 1:
            nr_clusters = len(clusters)
            nr_of_subjects_2_cp = int(len(lssubj)/nr_clusters)
            f_nr = 0
            val2start_count = 0
            val2end_count = nr_of_subjects_2_cp
            for cred in clusters:
                cuser = clusters[cred][0]
                caddress = clusters[cred][1]
                cmaindir = clusters[cred][2]
                tmp_dirs2cp = []
                with open(MainFolder+'logs/f2cp','a') as f:
                    with open(MainFolder+'logs/subj2fs'+str(f_nr),'a') as f2:
                            for subj in lssubj[val2start_count:val2end_count]:
                                f2.write(subj+'\n')
                                for dir in dirs2cp:
                                    if subj in dir:
                                        tmp_dirs2cp.append(dir)
                if platform == 'darwin' or platform == 'linux' or platform == 'linux2':
                    platform_linux_darwin(cuser, caddress, MainFolder+'subj2fs'+str(f_nr), tmp_dirs2cp, cmaindir)
                elif platform == 'win32':
                    platform_win(cuser, caddress, MainFolder+'subj2fs'+str(f_nr), tmp_dirs2cp, cmaindir)
                rename(MainFolder+'subj2fs'+str(f_nr), MainFolder+'logs/zold.subj2fs'+str(f_nr)+'_'+str(time.strftime('%Y%m%d', time.localtime())))
                val2start_count = val2start_count +nr_of_subjects_2_cp
                val2end_count = val2end_count + nr_of_subjects_2_cp
                if val2end_count < len(lssubj):
                    pass
                else:
                     val2end_count = len(lssubj)
                f_nr += 1
            start_cluster()

        #rename(MainFolder+'logs/subj2fs', MainFolder+'logs/zold.subj2fs'+str(time.strftime('%Y%m%d', time.localtime())))
        #rename(MainFolder+'logs/f2cp', MainFolder+'logs/zold.f2cp'+str(time.strftime('%Y%m%d', time.localtime())))

    else:
        print('no subj2fs file, no subjects to copy to cluster')

#
def cpFromCluster():
    """
    it copy the files from the cluster to the local folder
    the remote location : source dir: is in the configuration, how?
    the local location : dest dir: is in the configuration also

    :return: None, nothing
    """
    # todo: for now, only working on windows
    # def platform_linux_darwin(cuser, caddress, cmaindir):
    #         ls_complete_name = []
    #         system('sftp '+cuser+'@'+caddress)
    #         time.sleep(10)
    #         for dir2cp in listdir():
    #             system('get '+cmaindir+'/freesurfer/subjects/'+dir2cp+' '+MainFolder+'/processed/')
    #         system('exit')
    #     # system('scp '+cuser+'@'+caddress+':'+cmaindir+'status_cluster '+freesurfer+'logs/')

    def platform_win(cuser, caddress, cmaindir,cpw):
        print(MainFolder)
        file = MainFolder+'logs/psftpcpdb_from_cluster.scr'
        open(file, 'w').close()
        with open(file,'a') as f:
            f.write('get '+cmaindir+'a/db.py a/db.py\n') # this is the batch command: get a/db.py a/db.py
            f.write('quit')
        count = 0
        system('psftp '+cuser+'@'+caddress+' -pw '+cpw+' -b '+file)
        while count <4 and not path.exists('a/db.py'):
            time.sleep(2)
            count += 1
        #remove(file)
        if path.exists('a/db.py'):
            from a.db import PROCESSED # so cmaindir folder is the current folder :)
            if len(PROCESSED['cp2local']) > 0:
                file2cp = MainFolder+'logs/cp_processed_from_cluster.scr'
                open(file2cp, 'w').close()
                with open(file2cp,'a') as f:
                    for subjid in PROCESSED['cp2local']:
                        f.write('get '+cmaindir+'freesurfer/subjects/'+subjid+' '+MainFolder+'processed/\n')
                system('psftp '+cuser+'@'+caddress+' -pw '+cpw+' -b '+file2cp)
                #remove(file2cp)

    clusters = database._get_credentials('all')
    ssh_session = getSSHSession(host_name, user_name, user_password)
    scp = SCPClient(ssh_session.get_transport())
    ftp_client = ssh_session.open_sftp()

    if len(clusters) == 1:
        for cred in clusters:
            cuser = clusters[cred]['Username']
            caddress = clusters[cred]['remote_address']
            cmaindir = clusters[cred]['HOME']
            cpw =  clusters[cred]['Password']
            from sys import platform
            # platform_linux_darwin(cuser, caddress, cmaindir)
            # platform_win(cuser, caddress, cmaindir,cpw)
            # 1. download a/a.db to a/a.db
            remote_path = os.path.join(cmaindir,'a/db.py')
            # remote path is ????/projects/def-hanganua/a/db.py: subject folder
            current_path = pathlib.Path(__file__).parents[1] # it is v02003/a

            print(current_path)
            local_path = os.path.join(current_path,'db.py') #MainFolder+'processed/'
            print((remote_path,local_path))
            # local path is processed in this folder
            ftp_client.get(remote_path,local_path)
            print("downloaded {0} to {1}".format(remote_path, local_path))
            # 2. after download a.db
            if not path.exists('a/db.py'):
                print("a/db.py file does not exist")
                return
            # here db.py exist
            # todo: get user to input path to subject folder
            # set the cmaindir values: it is the location that contains the subjects
            result, _ = runCommandOverSSH(ssh_session, "echo $FREESURFER_HOME")
            if result:
                path_to_subjects = result
            else:
                print("Please set the FREESURFER_HOME in cluster environment to free surfer home."
                      " Try to search for subjects folder in ~/subjects ")
                result, _ = runCommandOverSSH(ssh_session, "file ~/subjects")
                if 'No such file or directory' in result:
                    print("The set the location of subjects: either is ~/subjects or FREESURFER_HOME/subjects before "
                          "downloading results")
                    return
            # path_to_subjects = '/home/hvt/projects/def-hanganua/' # for debug purpose
            MainFolder = "./" # current folder of the scripts
            from a.db import PROCESSED
            if len(PROCESSED['cp2local']) > 0:
                # file2cp = MainFolder+'logs/cp_processed_from_cluster.scr'
                # open(file2cp, 'w').close()
                ftp_client = ssh_session.open_sftp()
                for subjid in PROCESSED['cp2local']:
                    remote_path = os.path.join(path_to_subjects,'subjects/',subjid)
                    local_path = os.path.join(MainFolder,'processed/', subjid)
                    print("___", remote_path, local_path)
                    ftp_client.get(remote_path,local_path)
                    print("downloaded {0} to {1}".format(remote_path, local_path))
            # scp.close()
            ssh_session.close()
'''

if __name__ == "__main__":
    d = DistributionHelper()
    if d.is_setup_vars_folders(is_freesurfer_nim=True, is_nimb_fs_stats=True, is_nimb_classification=False): # True
        pass