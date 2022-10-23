# -*- coding: utf-8 -*-
import os
import sys
import shutil

from distribution.utilities import save_json, ErrorMessages, makedir_ifnot_exist, get_path
from distribution.setup_miniconda import setup_miniconda
from distribution.setup_freesurfer import SETUP_FREESURFER
from distribution.distribution_definitions import DEFAULT
from processing.schedule_helper import Scheduler
from distribution.manage_archive import ZipArchiveManagement, is_archive
from setup.interminal_setup import get_yes_no, get_userdefined_paths, term_setup
from setup import interminal_setup
from distribution.logger import LogLVL
try:
    from setup import guitk_setup
except ImportError:
    gui_setup = 'term'


class DistributionHelper():

    def __init__(self, all_vars):

        self.all_vars         = all_vars
        self.credentials_home = all_vars.credentials_home # NIMB_HOME/credentials_paths.py
        self.locations        = all_vars.location_vars # credentials_home/local.json + remotes.json
        self.project          = all_vars.params.project
        self.proj_vars        = all_vars.projects[self.project]
        self.test             = all_vars.params.test
        self.local_vars       = self.locations["local"]
        self.NIMB_HOME        = self.local_vars["NIMB_PATHS"]["NIMB_HOME"]
        self.NIMB_tmp         = self.local_vars["NIMB_PATHS"]["NIMB_tmp"]

        # setup folder
        self.setup_folder = "../setup"
        self.git_repo     = "https://github.com/alexhanganu/nimb"


    def distribute_4_processing(self, unprocessed_d = dict()):
        """
        for ls of participants:
            if user approves:
                initiate the processing on local/ remote
        """
        # print(f'{LogLVL.lvl2}{unprocessed_d}')
        self.get_processing_location()
        print(f'{LogLVL.lvl2}locations for processing are: ')
        print(f'{LogLVL.lvl3}{self.locations_4process}')
        # for app in self.locations_4process:
        #     print(f'{LogLVL.lvl2}locations expected for processing: {app}: {self.locations_4process[app]}')
        #     for location in self.locations_4process[app]:
        #         app_storage_dir = self.locations[location][app.upper()][f'{app.upper()}_HOME']
        #         self.get_available_space(location, app_storage_dir)
        # Ask if user wants to include only one machine or all of them
        print(f'{LogLVL.lvl2}!!!!processing will continue ONLY on local. still TESTING')
        location = 'local'
        app = 'freesurfer'
        app_storage_dir = self.locations[location][app.upper()]['SUBJECTS_DIR']
        # self.get_available_space(location, app_storage_dir)
        # self.get_subject_data_volume(unprocessed)
        # self.get_available_space(location, NIMB_NEW_SUBJECTS)
        # if self.get_user_confirmation():
        if not self.test:
            process_type = 'nimb_processing'
            subproc = 'run'
            print(f'    sending to scheduler for app {app}')
            self.make_f_subjects_2b_processed(location, unprocessed_d)
            python_run   = self.local_vars['PROCESSING']["python3_run_cmd"]
            cmd = f'{python_run} processing_run.py -project {self.project}'
            cd_cmd = f'cd {os.path.join(self.NIMB_HOME, "processing")}'
            Scheduler(self.local_vars).submit_4_processing(cmd, process_type, subproc, cd_cmd)
        else:
            print(f'    READY to send to scheduler for app {app}. TESTing active')


    def make_f_subjects_2b_processed(self, location, unprocessed_d):
        NIMB_tmp_loc = self.locations[location]['NIMB_PATHS']['NIMB_tmp']
        f_abspath = os.path.join(NIMB_tmp_loc, DEFAULT.f_subjects2proc)
        print(f'{LogLVL.lvl2}creating file: {f_abspath}')
        # print(unprocessed_d)
        for _id_bids in unprocessed_d:
            unprocessed_d[_id_bids] = self.adjust_paths_2data(NIMB_tmp_loc,
                                                    unprocessed_d[_id_bids])
            print(unprocessed_d[_id_bids])
        save_json(unprocessed_d, f_abspath)


    def adjust_paths_2data(self, NIMB_tmp_loc, _id_bids_data):
        # print("\n","#" *50)
        # print(_id_bids_data)
        for BIDS_type in _id_bids_data:
            path_2archive = ""
            mr_modalities = [i for i in _id_bids_data[BIDS_type] if i not in ("archived",)]
            if "archived" in _id_bids_data[BIDS_type]:
                print(f'{LogLVL.lvl2}{BIDS_type} is archived: {_id_bids_data[BIDS_type]["archived"]}\n')
                path_2archive = _id_bids_data[BIDS_type]["archived"]
            for mr_modality in mr_modalities:
                path_src_all = _id_bids_data[BIDS_type][mr_modality]
                path_src = path_src_all[0]
                if len(path_src_all) > 1:
                    print(f"{LogLVL.lvl2}multiple paths are present. I am using only the first")
                # print(f"{LogLVL.lvl2}path_src is: {path_src}\n")
                new_path = self.get_path_2mr(path_src,
                                            path_2archive,
                                            self.NIMB_tmp)
                # print(f"{LogLVL.lvl2}new path is: {new_path}\n")
                path_src_all = [new_path]
                _id_bids_data[BIDS_type][mr_modality] = path_src_all
                if mr_modality == "dwi":
                    _id_bids_data[BIDS_type]["bval"] = [path_src.replace(".nii.gz", ".bval")]
                    _id_bids_data[BIDS_type]["bvec"] = [path_src.replace(".nii.gz", ".bvec")]

        # print("#" *50)
        return _id_bids_data



    def get_path_2mr(self, path2mr_, path_2archive, tmp_dir = "none"):
        if os.path.exists(path2mr_):
            # print(f'{LogLVL.lvl3} file is unarchived: {path2mr_} and exists')
            return path2mr_
        elif is_archive(path_2archive):
            print(f'{LogLVL.lvl3} archive located at: {path_2archive}')
            if tmp_dir == 'none':
                tmp_dir = os.path.dirname(path_2archive)
            return self.extract_from_archive(path_2archive,
                                             path2mr_,
                                             tmp_dir)
        else:
            print(f'{LogLVL.lvl3} file: {path_2archive} does not seem to be an archive')
            print(f'{LogLVL.lvl3} path: {path2mr_} is NOT a folder')
            return ''


    def extract_from_archive(self, archive_abspath, path2mr_, tmp_dir):
        tmp_dir_xtract = os.path.join(tmp_dir, 'tmp_for_classification')
        tmp_dir_err    = os.path.join(tmp_dir, 'tmp_for_classification_err')
        makedir_ifnot_exist(tmp_dir_xtract)
        makedir_ifnot_exist(tmp_dir_err)
        ZipArchiveManagement(
            archive_abspath,
            path2xtrct = tmp_dir_xtract,
            path_err   = tmp_dir_err,
            dirs2xtrct = [path2mr_,])
        if len(os.listdir(tmp_dir_err)) == 0:
            shutil.rmtree(tmp_dir_err, ignore_errors=True)
        return tmp_dir_xtract


    def get_processing_location(self):
        """
        if freesurfer_install ==1 on local or remote
        :param app as for freesurfer, nilearn, dipy
        :return locations as list
        """
        apps_all = DEFAULT.apps_all
        self.locations_4process = dict()

        for app in apps_all:
            self.locations_4process[app] = list()
            param_install = DEFAULT.apps_instal_param[app]
            for location in self.locations:
                if self.locations[location][app.upper()][param_install] == 1:
                    self.locations_4process[app].append(location)
        return self.locations_4process


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
                loc = term_setup('none').credentials
                chosen_loc.append(loc)
        else:
            pass
            # if multiple locations have freesurfer_install=1: ask user to define which location to choose for processing
            # else ask to change freesurfer_install to 1
        if len(self.locations_4process) > 1:
            return True
        else:
            return False


    def get_subject_data_volume(self, unprocessed):
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
    def get_available_space(self, location):
        """
        1. get the available space on each location
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


    def get_local_remote_dir(self, dir_data, _dir = 'None'):
        location    = dir_data[0]
        dir_abspath = dir_data[1]
        print(f'{LogLVL.lvl2}folder {dir_abspath}')
        print(f'{LogLVL.lvl3}is located on: {location}')
        if location == 'local':
            if not os.path.exists(dir_abspath):
                dir_abspath = get_userdefined_paths(f'{_dir} folder',
                                                    dir_abspath, '', create = False)
                makedir_ifnot_exist(dir_abspath)
                if _dir != 'None':
                    from setup.get_credentials_home import _get_credentials_home
                    if _dir in self.all_vars.projects[self.project]:
                        self.all_vars.projects[self.project][_dir][1] = dir_abspath
                        abs_path_projects = os.path.join(_get_credentials_home(), 'projects.json')
                        save_json(self.all_vars.projects, abs_path_projects)
                    else:
                        print('    folder to change is not located in the projects.json variables')
                else:
                    print('    Folder to change is not defined, cannot create a new one.')
            return True, dir_abspath, 'local'
        else:
            return False, dir_abspath, location


    def get_subj_2classify(self):
        dirs_2classify = list()
        dir_new_subj    = self.locations["local"]["NIMB_PATHS"]["NIMB_NEW_SUBJECTS"]
        sourcedata_location = self.proj_vars['SOURCE_SUBJECTS_DIR'][0]
        sourcedata_dir = self.proj_vars['SOURCE_SUBJECTS_DIR'][1]
        if os.path.exists(dir_new_subj) and os.listdir(dir_new_subj):
            dirs_2classify.append(dir_new_subj)
        if sourcedata_location == 'local'\
            and os.path.exists(sourcedata_dir)\
            and os.listdir(sourcedata_dir):
            dirs_2classify.append(sourcedata_dir)
        if dirs_2classify:
            print('Folders with Subjects to classify are: {}'.format(dirs_2classify))
            return dirs_2classify
        else:
            project_file_abspath = os.path.join(self.credentials_home, 'projects.json')
            print('There were no folders eligible for classificaiton')
            print(f"    Please check the file for setting the projects: {project_file_abspath}")
            return False


    def prep_4stats(self, fs = False):
        """create DIRs for stats (as per setup/stats.json)
           get group file (provided by user)
           return final stats_grid_file that will be used for statistical analysis
        """
        dir_4stats       = makedir_ifnot_exist(self.proj_vars["STATS_PATHS"]["STATS_HOME"])
        fname_groups     = self.proj_vars['fname_groups']
        file_other_stats = []
        file_names = self.proj_vars["STATS_FILES"]
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


    def prep_4fs_stats(self, subjects = list()):
        '''create DIR to store stats files
            check if processed subjects are on the local computer
            if yes:
                copy corresponding stats files to stats DIR
                return OK to perform stats
            else:
                return False
        '''
        dir_4stats       = makedir_ifnot_exist(self.proj_vars["STATS_PATHS"]["STATS_HOME"])
        local, PROCESSED_FS_DIR, _ = self.get_local_remote_dir(self.proj_vars["PROCESSED_FS_DIR"])
        subjects =  os.listdir(PROCESSED_FS_DIR)

        if local:
            fname_groups     = self.proj_vars['fname_groups']
            if self.get_files_for_stats(dir_4stats,
                                       [fname_groups, DEFAULT.f_ids]):
                print("subjects for stats are: ", subjects)
        return self.extract_stats_from_archive(subjects, PROCESSED_FS_DIR)


    def get_files_for_stats(self, path_2copy_files, list_of_files):
        local, materials_dir_path, location = self.get_local_remote_dir(self.proj_vars["materials_DIR"],
                                                                        _dir = "materials_DIR")
        if local:
            for file in list_of_files:
                path2file = os.path.join(materials_dir_path, file)
                if os.path.exists(path2file):
                    print(f'    copying files:')
                    print(f'        {file} to:')
                    print(f'            {path_2copy_files}')
                    shutil.copy(path2file, path_2copy_files)
                else:
                    print(f'        NOTE! file: {file} is absent from path:')
                    print(f'            {path2file}')
        else:
            print('    nimb must access the remote computer: {}'.format(location))
            from distribution import SSHHelper
            SSHHelper.download_files_from_server(location, materials_dir_path, path_2copy_files, list_of_files)
        if os.path.exists(os.path.join(path_2copy_files, list_of_files[-1])):
            return True
        else:
            return self.chk_files_for_stats(list_of_files, path_2copy_files)


    def chk_files_for_stats(self, list_of_files, path_2copy_files): #move to ProjectManager
        f_ids_processed = DEFAULT.f_ids
        f_ids_processed_abspath = os.path.join(path_2copy_files,
                                                f_ids_processed)
        if f_ids_processed in list_of_files and not os.path.exists(f_ids_processed_abspath):
            print(f'        file {f_ids_processed} is missing from folder:')
            print(f'            {path_2copy_files}')
            group_file = self.proj_vars['fname_groups']
            if group_file in list_of_files:
                print(f"        trying to create {f_ids_processed}")
                print(f"            from group file: {group_file}")
                materials_dir_pt = self.proj_vars["materials_DIR"][1]
                f_ids_inmatdir   = os.path.join(materials_dir_pt, DEFAULT.f_ids)
                return f_ids_inmatdir
            else:
                print(f'    ERR! Cannot find group file: {group_file}. Cannot continue.')
                return False


    def extract_stats_from_archive(self, subjects, PROCESSED_FS_DIR):
        '''
        checks if subjects are list() are archived
        extract the "stats" folder of the subject
        '''
        from .manage_archive import is_archive, ZipArchiveManagement
        archived = list()
        for sub in subjects:
            path_2sub = get_path(PROCESSED_FS_DIR, sub)
            if not os.path.isdir(path_2sub):
                if is_archive(sub):
                    archived.append(path_2sub)

        if archived:
            dirs2extract = ['stats',]
            tmp_dir = os.path.join(self.NIMB_tmp, DEFAULT.nimb_tmp_dir)
            makedir_ifnot_exist(tmp_dir)
            PROCESSED_FS_DIR = tmp_dir
            for path_2sub in archived:
                        print('Must extract folder {} for each subject to destination {}'.format('stats', path_2sub))
                        ZipArchiveManagement(path_2sub, 
                                            path2xtrct = tmp_dir, path_err = False,
                                            dirs2xtrct = dirs2extract, log=True)
        return PROCESSED_FS_DIR


    def prep_4fs_glm(self, FS_GLM_dir, fname_groups):
        FS_GLM_dir           = makedir_ifnot_exist(FS_GLM_dir)
        print('INITIATING: preparation to perform GLM with FreeSurfer')
        print('    in the folder:', FS_GLM_dir)
        if not self.get_files_for_stats(FS_GLM_dir,
                                [fname_groups, DEFAULT.f_ids]):
            sys.exit()
        f_GLM_group     = os.path.join(FS_GLM_dir, fname_groups)
        f_ids_processed = os.path.join(FS_GLM_dir, DEFAULT.f_ids)

        SUBJECTS_DIR         = self.locations["local"]['FREESURFER']['SUBJECTS_DIR']
        if os.path.exists(f_GLM_group) and os.path.exists(f_ids_processed):
            from processing.freesurfer.fs_glm_prep import CheckIfReady4GLM
            ready, miss_ls = CheckIfReady4GLM(self.locations["local"]['NIMB_PATHS'],
                                                self.locations["local"]['FREESURFER'],
                                                self.proj_vars,
                                                f_ids_processed,
                                                f_GLM_group,
                                                FS_GLM_dir).chk_if_subjects_ready()
            print(f'    variables used for GLM are: {self.proj_vars["variables_for_glm"]}')
            print(f'    ID column is: {self.proj_vars["id_col"]}')
            print(f'    Group column is: {self.proj_vars["group_col"]}')
            print(f'    variables EXCLUDED from GLM are: {self.proj_vars["other_params"]}')
            print(f'    for details check: credentials_path/projects.py')
            if miss_ls:
                dirs2extract = ['label','surf',]
                print('    ATTENTION! some subjects could be prepared for GLM analysis')
                print(f'        by extracting the folders: {dirs2extract}')
                if get_yes_no('    do you want to prepare the missing subjects? (y/n)') == 1:
                    self.prep_4fs_glm_extract_dirs(miss_ls, SUBJECTS_DIR, dirs2extract)
                    self.prep_4fs_glm(FS_GLM_dir, fname_groups)
                return False
            else:
                print('all ids are present in the analysis folder, ready for glm analysis')
                print('    GLM file path is:',f_GLM_group)
                return f_GLM_group, FS_GLM_dir
        else:
            print('GLM files are missing: {}, {}'.format(f_GLM_group, f_ids_processed))
            return False


    def prep_4fs_glm_extract_dirs(self, ls, SUBJECTS_DIR, dirs2extract):
        from .manage_archive import ZipArchiveManagement
        if self.proj_vars['materials_DIR'][0] == 'local':
            print(f'{LogLVL.lvl2}Extracting folders {dirs2extract} to: {SUBJECTS_DIR}')
            NIMB_PROCESSED_FS = os.path.join(self.locations["local"]['FREESURFER']['NIMB_PROCESSED'])
            for sub in ls:
                zip_file_path = os.path.join(NIMB_PROCESSED_FS, '{}.zip'.format(sub))
                if os.path.exists(zip_file_path):
                    extract = True
                elif self.proj_vars['PROCESSED_FS_DIR'][0] == 'local':
                    zip_file_path = os.path.join(self.proj_vars['PROCESSED_FS_DIR'][1], '{}.zip'.format(sub))
                    if os.path.exists(zip_file_path):
                        extract = True
                if extract:
                    print(f'    participant: {sub}')
                    ZipArchiveManagement(zip_file_path,
                                        path2xtrct = SUBJECTS_DIR,
                                        path_err = self.NIMB_tmp,
                                        dirs2xtrct = dirs2extract,
                                        log=True)
                else:
                    print('{} subject missing from {}'.format(sub, NIMB_PROCESSED_FS))
                print(f'    participants left: {len(ls[ls.index(sub):])}')


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
