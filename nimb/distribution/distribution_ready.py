"""
        - local.json - def-supervisor is not changed in the SBATCH command
        - check that miniconda is installed (is_miniconda_installed). If not:
            - if False: check that local.json-NIMB_PATHS- miniconda_path has permission to install.
                - If True: initiate distribution. setup_minicoda.py
            - If True: check that all miniconda modules are installed.
                    - if False: initiate distribution. setup_minicoda.py
        - check that source FREESURFER_HOME is a valid command
        - chk on local/remote ifa bash command is failed (like wget, curl)
"""
import os, sys
import shutil
from setup.get_vars import Get_Vars
from distribution.utilities import is_writable_directory, is_ENV_defined
from distribution.setup_miniconda import setup_miniconda, is_miniconda_installed, is_conda_module_installed
from distribution.distribution_helper import logger
from distribution.utilities import ErrorMessages, makedir_ifnot_exist
from sys import platform

class DistributionReady():
    """
    This file sole for the READY command.
    """
    local_json = "~/nimb/local.json"
    module_list = ["pandas", "numpy", "xlrd", "xlsxwriter", "paramiko", "dcm2niix", "dcm2bids", "dipy"]
    #modules = open('requirements.txt').readlines()
    def __init__(self, all_vars, projects, project):
        
        self.credentials_home = all_vars.credentials_home # NIMB_HOME/credentials_paths.py
        self.installers       = all_vars.installers # NIMB_HOME/setup/installers.json
        self.locations        = all_vars.location_vars # credentials_home/local.json + remotes.json
        self.stats_vars       = all_vars.stats_vars
        self.projects         = projects # credentials_home/project.json
        self.project_name     = project
        self.NIMB_HOME        = self.locations["local"]["NIMB_PATHS"]["NIMB_HOME"]
        self.NIMB_tmp         = self.locations["local"]["NIMB_PATHS"]["NIMB_tmp"]
        
    def check_ready(self):
        """

        :return: False if there is something wrong
                Otherwise True
        """
        print('inside check_ready')
        self.verify_paths()
        self.is_setup_vars(self.locations['local']['NIMB_PATHS'])
        self.is_setup_vars(self.locations['local']['PROCESSING'])
        # self.get_user_paths_from_terminal()  # to do, which ones are get from user?
        if self.classify_ready():
            print("NIMB ready to perform classification")
        else:
            ErrorMessages.error_classify()
            ready = False
        if self.fs_ready():
            print("NIMB ready to perform FreeSurfer processing")
        else:
            ErrorMessages.error_fsready()
            ready = False

        # mini_conda_path = self.locations['local']['NIMB_PATHS']['miniconda_home']
        # if not is_miniconda_installed():
            # # if has permission to install
            # if not is_writable_directory(mini_conda_path):
                # logger.fatal("miniconda path is not writable. Check the permission.")
                # return False
            # # true: install setup_minicoda.py
            # setup_miniconda(mini_conda_path)
        # else:
            # for module in self.module_list:
                # if not is_conda_module_installed(module):
                    # os.system(
                        # "conda install -y dcm2niix dcm2bids pandas numpy xlrd xlsxwriter paramiko dipy -c conda-forge -c default")
                    # break

        # # check $FREESURFER_HOME  exists
        # # source home
        # os.system("source ~/.bashrc")
        # if not is_ENV_defined("$FREESURFER_HOME"):
            # logger.fatal("$FREESURFER_HOME is not defined")
            # return False

    def get_user_paths_from_terminal(self):
        """
        using terminal to ask for user inputs of variable.
        which one? need discuss.
        :return:
        """
        # 1. get the inputs
        # 2. set the variable from inputs
        # 3. modify other variables
        pass

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
        setup_miniconda(self.locations['local']['NIMB_PATHS']['miniconda_home'])
        

    def verify_paths(self):
        # to verify paths and if not present - create them or return error
        if os.path.exists(self.NIMB_HOME):
            for p in (     self.NIMB_tmp,
                 os.path.join(self.NIMB_tmp, 'mriparams'),
                 os.path.join(self.NIMB_tmp, 'usedpbs'),
                           self.locations['local']['NIMB_PATHS']['NIMB_NEW_SUBJECTS'],
                           self.locations['local']['NIMB_PATHS']['NIMB_PROCESSED_FS'],
                           self.locations['local']['NIMB_PATHS']['NIMB_PROCESSED_FS_error']):
                if not os.path.exists(p):
                    print('creating path ',p)
                    makedir_ifnot_exist(p)

    def is_setup_vars(self, dict):
        """
        check if variables are defined in json
        :param config_file: path to configuration json file
        :return: True if there is no error, otherwise, return False
        """
        for key in dict:
            if type(dict[key]) != int and len(dict[key]) < 1:
                logger.fatal(f"{key} is missing")
                return False
        return True

    def classify_ready(self):
        ready = True
        for p in (self.locations['local']['NIMB_PATHS']['NIMB_NEW_SUBJECTS'],
                  self.NIMB_HOME, self.NIMB_tmp):
            if not os.path.exists(p):
                try:
                    # if path start with ~
                    makedir_ifnot_exist(p)
                except Exception as e:
                    print(e)
            if not os.path.exists(p):
                ready = False
                break
        return ready
        
    def fs_ready(self):
        if self.locations['local']['FREESURFER']['FreeSurfer_install'] == 1:
            if len(self.locations['local']['FREESURFER']['FREESURFER_HOME']) < 1:
                logger.fatal("FREESURFER_HOME is missing.")
                return False
            if not os.path.exists(self.locations['local']['FREESURFER']['FS_SUBJECTS_DIR']):
                    print('creating path ', self.locations['local']['FREESURFER']['FS_SUBJECTS_DIR'])
                    makedir_ifnot_exist(self.locations['local']['FREESURFER']['FS_SUBJECTS_DIR'])
            if self.check_freesurfer_ready():
                return self.fs_chk_fsaverage_ready()
        else:
            return False

    def fs_chk_fsaverage_ready(self):
        self.fs_fsaverage_copy()
        if not os.path.exists(os.path.join(self.locations['local']['FREESURFER']['FS_SUBJECTS_DIR'],'fsaverage', 'xhemi')):
            print('fsaverage or fsaverage/xhemi is missing from SUBJECTS_DIR: {}'.format(self.locations['local']['FREESURFER']['FS_SUBJECTS_DIR']))
            return False
        else:
            return True

    def fs_fsaverage_copy(self):
        if not os.path.exists(os.path.join(self.locations['local']['FREESURFER']['FS_SUBJECTS_DIR'],'fsaverage', 'xhemi')):
            fsaverage_path = os.path.join(self.locations['local']['FREESURFER']['FREESURFER_HOME'], "subjects", "fsaverage")
            shutil.copytree(fsaverage_path, os.path.join(self.vars['local']['FREESURFER']['FS_SUBJECTS_DIR'], 'fsaverage'))

    def check_freesurfer_ready(self):
        """
        check and install freesurfer
        :return:
        """
        ready = False
        if not os.path.exists(os.path.join(self.locations['local']['FREESURFER']['FREESURFER_HOME'], "MCRv84")):
            print('FreeSurfer must be installed')
            from .setup_freesurfer import SETUP_FREESURFER
            SETUP_FREESURFER(self.locations, self.installers)
            ready = True
        else:
            print('start freesurfer processing')
            ready =  True
        return ready
        
    def nimb_stats_ready(self):
        """will check if the STATS folder is present and will create if absent"""

        if not os.path.exists(self.stats_vars["STATS_PATHS"]["STATS_HOME"]):
            makedir_ifnot_exist(self.stats_vars["STATS_PATHS"]["STATS_HOME"])
        return self.is_setup_vars(self.stats_vars)
        
    def check_stats_ready(self):
        """will check if xlsx file for project is provided
           if all variables are provided
           if all paths for stats are created
           if NIMB is ready to perform statistical analysis"""
        ready = False
        file = self.projects[self.project_name]["GLM_file_group"]
        if self.projects[self.project_name]["materials_DIR"][0] == 'local' and os.path.exists(os.path.join(self.projects[self.project_name]["materials_DIR"][1], file)):
            ready = True
        else:
            print("data file is missing or not located on a local folder. Check file {}".format(os.path.join(self.credentials_home, 'projects.json', self.project_name)))
        return ready
