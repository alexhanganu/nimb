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

    def check_new(self):
        from distribution.distribution_check_new import DistributionCheckNew
        unprocessed = DistributionCheckNew(self.projects[self.project_name], self.NIMB_tmp).unprocessed
        if unprocessed:
            print('there are {} subjects to be processed'.format(len(unprocessed)))
            
        """
        - check for provided project, if provided, else - for all projects
        - per projects: check if ~/nimb/projects.json → project → SOURCE_MR is provided.  ==> start
        - create distrib-DATABASE (track files) ~/nimb/projects_status.json:
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
            - if SOURCE_BIDS_DIR is provided: moves the processed subjects to corresponding SOURCE_BIDS_DIR/subject/session/processed_fs folder"""

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
            subjects_to_send = DistributionHelper.get_list_subject_to_be_processed_remote_version(SOURCE_SUBJECTS_DIR=SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR=PROCESSED_FS_DIR, remote = cluster_name)

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
