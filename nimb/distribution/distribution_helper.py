import shutil
from os import system, path, listdir, environ, remove
from distribution.utilities import ErrorMessages, makedir_ifnot_exist
from distribution.setup_miniconda import setup_miniconda
from distribution.setup_freesurfer import SETUP_FREESURFER
from setup import interminal_setup
try:
    from setup import guitk_setup
except ImportError:
    gui_setup = 'term'

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
        """
        check for missing subjects
        if user approves, initiats the processing on local/ remote
        """
        from distribution.distribution_check_new import DistributionCheckNew
        unprocessed = DistributionCheckNew(self.projects[self.project_name], self.NIMB_tmp).unprocessed
#        unprocessed = ['adni_test1','adni_test2']
#        if unprocessed:
#            print('there are {} subjects to be processed'.format(len(unprocessed)))
#            analysis = 'freesurfer'
#            self.locations_4process = self.get_processing_location(analysis)
            # tell user the number of machines  ready to perform the analysis (local + remote)
#            print('there are {} locations ready to perform the {} analysis'.format(len(self.locations_4process), analysis))
            # Ask if user wants to include only one machine or all of them
#            if self.get_userdefined_location(): # If user chooses at least one machine for analysis:
#                print(self.locations_4process)
                # self.get_subject_data(unprocessed)
                # self.get_available_space() #- compute available disk space on the local and/or remote (where freesurfer_install ==1) for the folder FS_SUBJECTS_DIR and NIMB_PROCESSED_FS ==> get_free_space_remote
#                if self.get_user_confirmation():
#                    self.make_processing_database()
#                    self.run_processing()

    def get_processing_location(self, app):
        """
        if freesurfer_install ==1 on local or remote
        :param app as for freesurfer, nilearn, dipy
        :return locations as list
        """
        loc = list()
        if app == 'freesurfer':
            for location in self.locations:
                print(location)
                if self.locations[location]["FREESURFER"]["FreeSurfer_install"] == 1:
                    loc.append(location)
        return loc

    def get_userdefined_location(self):
        """
        if len(locations) == 0:
            user is asked to change freesurfer_install to 1 for any location or
            user is asked to provide a new machine
        else, user is asked to chose the machine or all machines to
        be used for the processing
        :param locations ready to perform analysis
        :return locations chosen by the user
        """
        from setup.term_questionnaire import PyInqQuest
        chosen_loc = list()
        if len(self.locations_4process) == 0:
                loc = interminal_setup.term_setup('none').credentials
                chosen_loc.append(loc)
        else:
            pass
            # if multiple locations have freesurfer_install=1: ask user to define which location to choose for processing
            # else ask to change freesurfer_install to 1
        if len(self.locations_4process) > 1:
            return True
        else:
            return False

    def get_subject_data(self, unprocessed):
        """
        it is expected that
        for each subject to be processed (in unprocessed):
        compute volume of data (T1s, Flairs, rsfMRIs, DWIs
        :param number of subjects to be processed, from SOURCE_SUBJECTS_DIR:
        :return: dict {subject: {app: volume_data_of_subj, expected_volume: volume_nr}}
        """
        res = True
        return res


    # @staticmethod
    def get_available_space(self):
        """
        1. get the available space on each remote chosen by the user to perform the processing
        :param self.locations_4process:
        :return: dict volume for each location in the NEW_SUBJECTS dir
        """
        # based on availabe space
        print(self.locations_4process)
        # free_space = DiskspaceUtility.get_free_space_remote(ssh_session)
        # # consider the space available the remote server
        # free_space = min(free_space, 10*1024) # min of 'free space' and 10GB
        to_be_process_subject = DiskspaceUtility.get_subject_to_be_process_with_free_space(un_process_sj)
        #

    def get_user_confirmation(self):
        """
        tell user:
        * number of subjects te be processed
        * estimated volumes
        * estimated time the processing will take plase
        * ask user if accept to start processing the subjects
        """
        continue_processing = False
        # print("Remote server has {0}MB free, it can stored {1} subjects".format(free_space, len(to_be_process_subject)))
        return continue_processing

    def make_processing_database(self):
        """
                - create distrib-DATABASE (track files) ~/nimb/project-name_status.json:
            - ACTION = notprocessed:[], copied2process:[]
            - LOCATION = local:[], remote_name1:[], remote_name_n:[]
            add each subjects to:
            - distrib-DATABASE[ACTION][notprocessed].append(subject)
            - distrib-DATABASE[LOCATION][local/remote_name].append(subject)
        - populating rule:
            - continue populating until the volume of subjects + volume of estimated processed subjects (900Mb per subject) is less then 75% of the available disk space
            - populate local.json → NIMB_PATHS → NIMB_NEW_SUBJECTS based on populating rule
            - If there are more than one computer ready to perform freesurfer:
                - send archived subjects to each of them based on the estimated time required to process one subject and choose the methods that would deliver the lowest estimated time to process.
            - once copied to the NIMB_NEW_SUBJECTS:
                - add subject to distrib-DATABSE → LOCATION → remote_name
                - move subject in distrib-DATABASE → ACTION notprocessed → copied2process
        """
        # to_be_process_subject = DiskspaceUtility.get_subject_upto_size(free_space, to_be_process_subject)
        # return [os.path.join(SOURCE_SUBJECTS_DIR,subject) for subject in to_be_process_subject] # full path
        pass

    def run_processing(self):
        """
            - after all subjects are copied to the NIMB_NEW_SUBJECTS folder: initiate the classifier on the local/remote computer with keys: cd $NIMB_HOME && python nimb.py -process classify
            - wait for the answer; If True and new_subjects.json file was created:
            - start the -process freesurfer
            - after each 2 hours check the local/remote NIMB_PROCESSED_FS and NIMB_PROCESSED_FS_ERROR folders. If not empty: mv (or copy/rm) to the path provided in the ~/nimb/projects.json → project → local or remote $PROCESSED_FS_DIR folder
            - if SOURCE_BIDS_DIR is provided: moves the processed subjects to corresponding SOURCE_BIDS_DIR/subject/session/processed_fs folder
        """
        pass


    def get_stats_dir(self):
        """will return the folder with unzipped stats folder for each subject"""
        if any('.zip' in i for i in listdir(PROCESSED_FS_DIR)):
            NIMB_PROCESSED_FS = path.join(self.locations["local"]['NIMB_PATHS']['NIMB_PROCESSED_FS'])
            logger.info('Must extract folder {} for each subject to destination {}'.format('stats', NIMB_PROCESSED_FS))
            self.extract_dirs([path.join(PROCESSED_FS_DIR, i) for i in listdir(PROCESSED_FS_DIR) if '.zip' in i],
                            NIMB_PROCESSED_FS,
                            ['stats',])
            return NIMB_PROCESSED_FS
        else:
            return self.projects[self.project_name]["PROCESSED_FS_DIR"]
        print('perform statistical analysis')

    def extract_dirs(self, ls_zip_files, path2xtrct, dirs2extract):
        from .manage_archive import ZipArchiveManagement
        for zip_file_path in ls_zip_files:
            ZipArchiveManagement(
                    zip_file_path, 
                    path2xtrct = path2xtrct, path_err = False,
                    dirs2xtrct = dirs2extract, log=True)

    def get_subj_2classify(self):
        bids_cred = self.projects[self.project_name]['SOURCE_BIDS_DIR']
        source_subj = self.projects[self.project_name]['SOURCE_SUBJECTS_DIR']
        if bids_cred[0] == 'local' and path.exists(bids_cred[1]) and listdir(bids_cred[1]):
            SUBJ_2Classify = bids_cred[1]
        elif source_subj[0] == 'local' and path.exists(source_subj[1]) and listdir(source_subj[1]):
            SUBJ_2Classify = source_subj[1]
        elif listdir(self.locations["local"]['NIMB_PATHS']['NIMB_NEW_SUBJECTS']):
            SUBJ_2Classify = self.locations["local"]['NIMB_PATHS']['NIMB_NEW_SUBJECTS']
        if SUBJ_2Classify:
            logger.info('Folder with Subjects to classify is: {}'.format(SUBJ_2Classify))
            return SUBJ_2Classify
        else:
            logger.info('Could not define the Folder with Subjects to classify is. Please adjust the file: {}'.format(path.join(self.credentials_home, 'projects.json')))
            return False

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

    def fs_glm_prep(self, dir_2chk):
        from processing.freesurfer.fs_glm_prep import CheckIfReady4GLM
        miss = CheckIfReady4GLM(self.projects[self.project_name],
                                dir_2chk).miss
        if miss:
            print('starting subject preparation for glm')
            self.fs_glm_prep_extract_dirs(list(miss.values()))
        else:
            return True

    def fs_glm_prep_extract_dirs(self, ls):
        dirs2extract = ['label','surf',]
        NIMB_PROCESSED_FS = path.join(self.locations["local"]['NIMB_PATHS']['NIMB_PROCESSED_FS'])
        not_exist = [i for i in ls if not path.exists(i)]
        if not_exist:
            logger.info('{} subject paths do not exist'.format(len(not_exist)))
            ls = [i for i in ls if path.exists(i)]
        logger.info('Must extract folders {} for {} subjects, to destination {}'.format(dirs2extract, len(ls), NIMB_PROCESSED_FS))
        self.extract_dirs([i for i in ls if '.zip' in i],
                          NIMB_PROCESSED_FS, dirs2extract)

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
            setup = SETUP_FREESURFER(self.locations)
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
        # if content of subject to be processed, in SOURCE_SUBJECTS_DIR is NOT archived:
        #     - archive and copy to local/remote.json → Nimb_PATHS → NIMB_NEW_SUBECTS.
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


# if __name__ == "__main__":
    # distribution = DistributionHelper(projects,
                                               # locations)
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
