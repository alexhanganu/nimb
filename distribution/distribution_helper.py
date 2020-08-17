import sys
import shutil
from credentials_path import credentials_home
from os import makedirs, system
import json

from distribution.database import *
# from distribution.check_disk_space import *
# from distribution import SSHHelper


class ErrorMessages:

    def error_classify():
        print("NIMB is not ready to perform the classification. Please check the configuration files.") 
    def error_fsready():
        print("NIMB not ready to perform FreeSurfer processing. Please check the configuration files.") 


class DistributionHelper():

    def __init__(self, projects, locations, installers):

        self.NIMB_HOME = locations["local"]["NIMB_PATHS"]["NIMB_HOME"]
        self.NIMB_tmp = locations["local"]["NIMB_PATHS"]["NIMB_tmp"]
        self.locations = locations
        self.projects = projects

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
        self.make_fs_vars_file()
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
                ErrorMessages.error_classify()
                break
        return ready


    def fs_ready(self):
        if self.locations['local']['FREESURFER']['FreeSurfer_install'] == 1:
            return self.check_freesurfer_ready()
        else:
            return False


    @staticmethod
    def is_setup_vars_folders(is_freesurfer_nim=False,
                              is_nimb_classification=False,
                              is_nimb_fs_stats=False):
        """
        check for configuration parameters, will exit (quit) the programme if the variables are not define
        :param config_file: path to configuration json file
        :param is_freesurfer_nim: True if run nimb freesurfer
        :param is_nimb_classification:
        :param is_nimb_fs_stats:
        :return: True if there is no error, otherwise, return False
        """
        with open(config_file) as file:
            config_dict = json.load(file)
        # check for the USER key
        for key, value in config_dict[DistributionHelper.user].items():
            if len(value) < 1:
                print(f"This {key} must be set because it is empy")
                # sys.exit()
                return False
        # check the NIMB_PATHS
        if is_nimb_classification or is_nimb_classification:
            for key, value in config_dict[DistributionHelper.nimb_path].items():
                if len(value) < 1:
                    print(f"This {key} must be set because it is empy")
                    # sys.exit()
                    return False
        if is_nimb_fs_stats:
            for key, value in config_dict[DistributionHelper.stat_path].items():
                if len(value) < 1:
                    print(f"This {key} must be set because it is empy")
                    # sys.exit()
                    return False
        # if freesurfer install = 1
        fs_install = 'FreeSurfer_install'
        fs_home = "FREESURFER_HOME"
        if config_dict[DistributionHelper.freesurfer][fs_install] == 1:
            if len(config_dict[DistributionHelper.freesurfer][fs_home]) < 1:
                print(f"{fs_home} is missing. It must bedefine in {config_file}")
                return False
            # MRDATA_PATHS must be defined:
            if "MRDATA_PATHS" not in config_dict.keys():
                print(f"MRDATA_PATHS is missing. It must bedefine in f{config_file} when {fs_install} = 1")
                return False
        return True


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


    def make_fs_vars_file(self):
        vars_f = path.join(self.NIMB_HOME,'processing','freesurfer','vars.json')
        with open(vars_f,'w') as jf:
            json.dump(self.locations['local'], jf, indent=4)
            try:
                system("chmod 777 "+path.join(self.NIMB_HOME,'processing','freesurfer','vars.json'))
            except Exception as e:
                print(e)

    @staticmethod
    def get_project_vars(var_name, project):
        """
        get the PROCESSED_FS_DIR
        :param config_file:
        :var_name: like PROCESSED_FS_DIR
        :return: empty string, or values
        """
        # PROJECT_DATA
        if project not in self.projects.keys():
            print("There is no path for project: "+project+" defined. Please check the file: "+path.join(credentials_home, "projects.json"))
            return ""
        return self.projects[project][var_name]
    @staticmethod
    def get_PROCESSED_FS_DIR(config_file =path.join(credentials_home, "local.json")):
        return DistributionHelper.get_MRDATA_PATHS_var("PROCESSED_FS_DIR", config_file)
    @staticmethod
    def get_SOURCE_SUBJECTS_DIR(config_file =path.join(credentials_home, "local.json")):
        return DistributionHelper.get_MRDATA_PATHS_var("SOURCE_SUBJECTS_DIR",config_file)
    @staticmethod
    def get_username_password_cluster_from_sqlite():
        """
        get user name and password from sqlite database
        :return: username, password in string
        """
        clusters = database._get_Table_Data('Clusters', 'all')
        user_name = clusters[list(clusters)[0]]['Username']
        user_password = clusters[list(clusters)[0]]['Password']
        if len(user_name) < 1or len(user_password) < 1:
            print(f"User name or password is not define")
            return False
        return user_name, user_password

    def check_freesurfer_ready(self):
        if not path.exists(path.join(self.vars['local']['FREESURFER']['FREESURFER_HOME'], "MCRv84")):
            print('FreeSurfer must be installed')
            from .setup_freesurfer import SETUP_FREESURFER
            SETUP_FREESURFER(self.vars, self.installers)
        else:
            print('start freesurfer processing')
            return True


    def nimb_stats_ready(self, project):
        """will check if the STATS folder is present and will create if absent
           will return the folder with unzipped stats folder for each subject"""

        if not path.exists(self.vars["local"]["STATS_PATHS"]["STATS_HOME"]):
            makedirs(p)

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
        # interface_cluster.copy_subjects_to_cluster(mri_path, subjects_folder, a_folder)
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

if __name__ == "__main__":
    #DistributionHelper.is_setup_vars_folders(is_nimb_fs_stats=True, is_nimb_classification=True, is_freesurfer_nim=True)
    PROCESSED_FS_DIR = DistributionHelper.get_PROCESSED_FS_DIR(config_file=path.join(credentials_home, "projects.json"))
    SOURCE_SUBJECTS_DIR = DistributionHelper.get_SOURCE_SUBJECTS_DIR(config_file=path.join(credentials_home, "projects.json"))
    user_name,user_password = DistributionHelper.get_username_password_cluster_from_sqlite()
    cluster = "cedar.computecanada.ca"
    subjects = DistributionHelper.get_list_subject_to_be_processed_remote_version("/Users/van/Downloads/tmp/fs","/home/hvt/tmp2",cluster,user_name,user_password)
    print(subjects)
    ssh = getSSHSession(cluster, user_name, user_password)
    # download data from remote
    download_files_from_server(ssh,SOURCE_SUBJECTS_DIR,PROCESSED_FS_DIR)
    ssh.close()

    # send data
    DistributionHelper.send_subject_data(config_file=path.join(credentials_home, "projects.json"))
