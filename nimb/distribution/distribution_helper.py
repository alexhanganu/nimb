# -*- coding: utf-8 -*-
import os
import sys
import shutil

from distribution.utilities import ErrorMessages, makedir_ifnot_exist
from distribution.setup_miniconda import setup_miniconda
from distribution.setup_freesurfer import SETUP_FREESURFER
from setup.interminal_setup import get_yes_no
from setup import interminal_setup
try:
    from setup import guitk_setup
except ImportError:
    gui_setup = 'term'


class DistributionHelper():

    def __init__(self, all_vars, project_vars):

        self.all_vars         = all_vars
        self.credentials_home = all_vars.credentials_home # NIMB_HOME/credentials_paths.py
        self.locations        = all_vars.location_vars # credentials_home/local.json + remotes.json
        self.proj_vars        = project_vars
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
        unprocessed = DistributionCheckNew(self.proj_vars, self.NIMB_tmp).unprocessed
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
                # self.get_available_space() #- compute available disk space on the local and/or remote 
#                (where freesurfer_install ==1) for the folder FS_SUBJECTS_DIR and NIMB_PROCESSED_FS ==> get_free_space_remote
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
        from distribution.check_disk_space import DiskspaceUtility
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
            - continue populating until the volume of subjects + volume of estimated processed subjects 
                (900Mb per subject) is less then 75% of the available disk space
            - populate local.json - NIMB_PATHS - NIMB_NEW_SUBJECTS based on populating rule
            - If there are more than one computer ready to perform freesurfer:
                - send archived subjects to each of them based on the estimated time required to process 
                    one subject and choose the methods that would deliver the lowest estimated time to process.
            - once copied to the NIMB_NEW_SUBJECTS:
                - add subject to distrib-DATABSE → LOCATION → remote_name
                - move subject in distrib-DATABASE → ACTION notprocessed → copied2process
        """
        # to_be_process_subject = DiskspaceUtility.get_subject_upto_size(free_space, to_be_process_subject)
        # return [os.path.join(SOURCE_SUBJECTS_DIR,subject) for subject in to_be_process_subject] # full path
        pass

    def run_processing(self):
        """
            - after all subjects are copied to the NIMB_NEW_SUBJECTS folder: initiate the 
                classifier on the local/remote computer with keys: cd $NIMB_HOME && python nimb.py -process classify
            - wait for the answer; If True and new_subjects.json file was created:
            - start the -process freesurfer
            - after each 2 hours check the local/remote NIMB_PROCESSED_FS and NIMB_PROCESSED_FS_ERROR folders. 
                If not empty: mv (or copy/rm) to the path provided in the ~/nimb/projects.json → project → local 
                    or remote $PROCESSED_FS_DIR folder
            - if SOURCE_BIDS_DIR is provided: moves the processed subjects to 
                corresponding SOURCE_BIDS_DIR/subject/session/processed_fs folder
        """
        pass

    def get_local_remote_dir(self, dir_data):
        if dir_data[0] == 'local':
            print('working folder is: {}'.format(dir_data[1]))
            return dir_data[1]
        else:
            print('folder {} is located on a remote: {}'.format(dir_data[1], dir_data[0]))
            return False

    def get_subj_2classify(self):
        new_subj = self.locations["local"]["NIMB_PATHS"]["NIMB_NEW_SUBJECTS"]
        bids_cred = self.proj_vars['SOURCE_BIDS_DIR']
        source_subj = self.proj_vars['SOURCE_SUBJECTS_DIR']
        SUBJ_2Classify = ''
        if os.listdir(new_subj):
            SUBJ_2Classify = new_subj
        elif bids_cred[0] == 'local' and os.path.exists(bids_cred[1]) and os.listdir(bids_cred[1]):
            SUBJ_2Classify = bids_cred[1]
#        elif bids_cred[0] == 'local' and os.path.exists(bids_cred[1]) and os.listdir(bids_cred[1]):
#            SUBJ_2Classify = bids_cred[1]
#        elif source_subj[0] == 'local' and os.path.exists(source_subj[1]) and os.listdir(source_subj[1]):
#            SUBJ_2Classify = source_subj[1]
        if SUBJ_2Classify:
            print('Folder with Subjects to classify is: {}'.format(SUBJ_2Classify))
            return SUBJ_2Classify
        else:
            print('Could not define the Folder with Subjects to classify. Please adjust the file: {}'.format(
                                                                os.path.join(self.credentials_home, 'projects.json')))
            return False

    def get_files_for_stats(self, path_2copy_files, list_of_files):
        location = self.proj_vars['materials_DIR'][0]
        materials_dir_path = self.proj_vars['materials_DIR'][1]
        if location == 'local':
            for file in list_of_files:
            	path2file = os.path.join(materials_dir_path, file)
            	if os.path.exists(path2file):
	                shutil.copy(path2file, path_2copy_files)
        else:
            print('nimb must access the remote computer: {}'.format(location))
            from distribution import SSHHelper
            SSHHelper.download_files_from_server(location, materials_dir_path, path_2copy_files, list_of_files)
        if os.path.exists(os.path.join(path_2copy_files, list_of_files[-1])):
            return True
        else:
            print(f'files {list_of_files} are not present in the expected folder: {materials_dir_path}')
            return False

    def prep_4stats(self, dir_4stats, fs = False):
        """create DIRs for stats (as per setup/stats.json)
           get group file (provided by user)
           return final stats_grid_file that will be used for statistical analysis
        Args:
            dir_4stats: DIR where stats are saved
        """
        dir_4stats       = makedir_ifnot_exist(dir_4stats)
        fname_groups     = self.proj_vars['fname_groups']
        file_other_stats = []
        file_names = self.all_vars.stats_vars["STATS_FILES"]
        for file in ["fname_fs_all_stats", "fname_func_all_stats", "fname_other_stats"]:
            file_name = self.proj_vars[file]
            if file_name:
                if file_name == "default":
                    file_name = file_names[file]
                file_name = f'{file_name}.{file_names["file_type"]}'
                file_other_stats.append(file_name)
        for file in ["fname_Outcor", "fname_eTIVcor", "fname_NaNcor"]:
            file_name = f'{file_names[file]}.{file_names["file_type"]}'
            file_other_stats.append(file_name)
        if not self.get_files_for_stats(dir_4stats,
                            [fname_groups,]):
            sys.exit()
        self.get_files_for_stats(dir_4stats,
                            file_other_stats)
        return fname_groups

    def prep_4fs_stats(self, dir_4stats):
        '''create DIR to store stats files
            check if processed subjects are on the local computer
            if yes:
                copy corresponding stats files to stats DIR
                return OK to perform stats
            else:
                return False
        Args:
            dir_4stats: DIR where stats are saved
        '''
        dir_4stats       = makedir_ifnot_exist(dir_4stats)
        PROCESSED_FS_DIR = self.get_local_remote_dir(self.proj_vars["PROCESSED_FS_DIR"])
        if PROCESSED_FS_DIR:
            fname_groups     = self.proj_vars['fname_groups']
            f_ids_processed_name = self.locations["local"]["NIMB_PATHS"]['file_ids_processed']
            if not self.get_files_for_stats(dir_4stats,
                                [fname_groups, f_ids_processed_name]):
                sys.exit()
    #     '''
    #     checks if subject is archived
    #     extract the "stats" folder of the subject
    #     '''
    #     sub_path = self.get_path(self.NIMB_PROCESSED_FS, sub)
    #     if not os.path.isdir(sub_path):
    #         if sub.endswith('zip'):
    #             print('Must extract folder {} for each subject to destination {}'.format('stats', sub_path))
    #             ZipArchiveManagement(sub_path, 
    #                                 path2xtrct = self.NIMB_tmp, path_err = False,
    #                                 dirs2xtrct = [self.dir_stats,], log=True)
    #             time.sleep(1)
    #             sub = sub.replace('.zip','')
    #             return self.get_path(self.NIMB_tmp, sub), sub
    #     else:
    #         return sub_path, sub
        return PROCESSED_FS_DIR

    def fs_glm_prep(self, FS_GLM_dir, fname_groups):
        from distribution.project_helper import ProjectManager
        proj_manager         = ProjectManager(self.proj_vars, self.locations["local"])
        FS_GLM_dir           = makedir_ifnot_exist(FS_GLM_dir)
        f_ids_processed_name = proj_manager._ids_file()
                            # self.locations["local"]["NIMB_PATHS"]['file_ids_processed']
        print('fs glm dir is:', FS_GLM_dir)
        if not self.get_files_for_stats(FS_GLM_dir,
                                [fname_groups, f_ids_processed_name]):
            sys.exit()
        f_GLM_group     = os.path.join(FS_GLM_dir, fname_groups)
        f_ids_processed = os.path.join(FS_GLM_dir, f_ids_processed_name)

        SUBJECTS_DIR         = self.locations["local"]['FREESURFER']['FS_SUBJECTS_DIR']
        if os.path.exists(f_GLM_group) and os.path.exists(f_ids_processed):
            from processing.freesurfer.fs_glm_prep import CheckIfReady4GLM
            ready, miss_ls = CheckIfReady4GLM(self.locations["local"]['NIMB_PATHS'], 
                                                    self.locations["local"]['FREESURFER'], 
                                                    self.proj_vars, 
                                                    f_ids_processed, 
                                                    f_GLM_group,
                                                    FS_GLM_dir).chk_if_subjects_ready()
            print(f'variables used for GLM are: {self.proj_vars["variables_for_glm"]}')
            print(f'    ID columns is: {self.proj_vars["id_col"]}')
            print(f'    Group column is: {self.proj_vars["group_col"]}')
            print(f'variables EXCLUDED from GLM are: {self.proj_vars["other_params"]}')
            print(f'    for details check: credentials_path/projects.py')
            if miss_ls:
                print('some subjects are missing, nimb must extract their surf and label folders')
                if get_yes_no('do you want to prepare the missing subjects for glm analysis? (y/n)') == 1:
                    dirs2extract = ['label','surf',]
                    self.fs_glm_prep_extract_dirs(miss_ls, SUBJECTS_DIR, dirs2extract)
                return False
            else:
                print('all ids are present in the analysis folder, ready for glm analysis')
                return f_GLM_group, FS_GLM_dir
        else:
            print('GLM files are missing: {}, {}'.format(f_GLM_group, f_ids_processed))
            return False

    def fs_glm_prep_extract_dirs(self, ls, SUBJECTS_DIR, dirs2extract):
        from .manage_archive import ZipArchiveManagement
        if self.proj_vars['materials_DIR'][0] == 'local':
            NIMB_PROCESSED_FS = os.path.join(self.locations["local"]['NIMB_PATHS']['NIMB_PROCESSED_FS'])
            for sub in ls:
                zip_file_path = os.path.join(NIMB_PROCESSED_FS, '{}.zip'.format(sub))
                if os.path.exists(zip_file_path):
                    extract = True
                elif self.proj_vars['PROCESSED_FS_DIR'][0] == 'local':
                    zip_file_path = os.path.join(self.proj_vars['PROCESSED_FS_DIR'][1], '{}.zip'.format(sub))
                    if os.path.exists(zip_file_path):
                        extract = True
                if extract:
                    print('Extracting folders {} for subject {}, to destination {}'.format(dirs2extract, sub, SUBJECTS_DIR))
                    ZipArchiveManagement(zip_file_path, path2xtrct = SUBJECTS_DIR,
                                        path_err = self.NIMB_tmp, dirs2xtrct = dirs2extract,
                                        log=True)
                else:
                    print('{} subject missing from {}'.format(sub, NIMB_PROCESSED_FS))

    def run_processing_on_cluster_2(self):
        '''
        execute the python a/crun.py on the remote cluster
        :return:
        '''
        # version 2: add username, password, and command line to run here
        from distribution import SSHHelper
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
        from distribution import SSHHelper
        clusters = database._get_Table_Data('Clusters', 'all')
        cname = [clusters.keys()][0]
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
        cmd_git = f" cd ~; git clone {self.git_repo}; "
        cmd_install_miniconda = "python nimb/distribution/setup_miniconda.py; "
        cmd_run_setup = " cd nimb/setup; python nimb.py -process ready"

        cmd_run_crun_on_cluster = load_python_3 + cmd_git + cmd_install_miniconda + cmd_run_setup
        print("command: " + cmd_run_crun_on_cluster)
        # todo: how to know if the setting up is failed?
        print("Setting up the remote cluster")
        from distribution import SSHHelper
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
        from distribution import SSHHelper
        ssh_session = SSHHelper.getSSHSession(remote_id)
        stdin, stdout, stderr = ssh_session.exec_command('ls '+path_dst)
        ls_copy = [line.strip('\n') for line in stdout]
        sftp = ssh_session.open_sftp()
        for val in ls_copy:
            size_src = SSHHelper.get_size_on_remote(ssh_session, os.path.join(path_dst, val))
            print('left to copy: ',len(ls_copy[ls_copy.index(val):]))
            SSHHelper.download_files_from_server(ssh_session, remote_path, local_destination)
            size_dst = os.path.getsize(path_src+'/'+val)
            if size_dst == size_src:
                print('        copy ok')
                #SSHHelper.remove_on_remote(os.path.join(path_dst, val))
            else:
                print('copy error, retrying ...')
        ssh_session.close()



    # def get_project_vars(self, var_name, project):
    #     """
    #     get the PROCESSED_FS_DIR
    #     :param config_file:
    #     :var_name: like PROCESSED_FS_DIR
    #     :return: empty string, or values
    #     """
    #     # PROJECT_DATA
    #     if project not in self.projects.keys():
    #         print("There is no path for project: {} defined. Please check the file: {}".format(
    #                                 project, os.path.join(self.credentials_home, "projects.json")))
    #         return ""
    #     return self.projects[project][var_name]