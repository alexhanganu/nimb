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
from distribution.setup_miniconda import (setup_miniconda, is_miniconda_installed,
                                        is_conda_module_installed, check_that_modules_are_installed)
from distribution.utilities import ErrorMessages, makedir_ifnot_exist
from sys import platform
from setup.interminal_setup import get_yes_no

class DistributionReady():
    def __init__(self, all_vars, proj_vars, log):

        self.credentials_home = all_vars.credentials_home # NIMB_HOME/credentials_paths.py
        self.locations        = all_vars.location_vars # credentials_home/local.json + remotes.json
        self.stats_vars       = all_vars.stats_vars
        self.proj_vars        = proj_vars # credentials_home/project.json
        self.NIMB_HOME        = self.locations["local"]["NIMB_PATHS"]["NIMB_HOME"]
        self.NIMB_tmp         = self.locations["local"]["NIMB_PATHS"]["NIMB_tmp"]
        self.logger           = log

    def check_ready(self):
        """

        :return: False if there is something wrong
                Otherwise True
        """
        if self.classify_ready():
            self.logger("NIMB ready to perform classification")
        else:
            ErrorMessages.error_classify()
            ready = False
        if self.fs_ready():
            self.logger("NIMB ready to perform FreeSurfer processing")
        else:
            ErrorMessages.error_fsready()
            ready = False
        conda_home = self.locations['local']['NIMB_PATHS']['conda_home']
        self.logger('checking conda at: {}'.format(conda_home))
        if not is_miniconda_installed(conda_home):
            # # if has permission to install
            # if not is_writable_directory(conda_home):
                # self.logger.fatal("miniconda path is not writable. Check the permission.")
                # return False
            # # true: install setup_minicoda.py
            if get_yes_no('do you want to try and install conda? (may take up to 30 minutes) (y/n)') == 1:
                setup_miniconda(conda_home, self.NIMB_HOME)
        if check_that_modules_are_installed(conda_home, self.NIMB_HOME):
            self.logger("conda has all modules installed")
        else:
            ErrorMessages.error_conda()
            return False

        # # check $FREESURFER_HOME  exists
        # # source home
        # os.system("source ~/.bashrc")
        # if not is_ENV_defined("$FREESURFER_HOME"):
            # self.logger.fatal("$FREESURFER_HOME is not defined")
            # return False
    def chk_if_modules_are_installed(self, module_list):
        '''
        scripts checks that modules are installed inside the python environement
        Args:
            modules_list: list with required modules to be checked
        Return:
            True if all modules are installed, else Fale
        '''
        installed = True
        modules = []
        miss = []
        for module in module_list:
            try:
                modules.append(__import__(module))
            except ImportError as e:
                self.logger(e)
                self.logger(f'module {module} is not installed. Cannot continue process')
                miss.append(module)
        if miss:
            installed = False
        return installed, miss

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
            self.logger("Currently only support setting up on Ubuntu-based system")
            # do the job here
            self.setting_up_local_linux_with_freesurfer()
        elif platform in ["win32"]:
            self.logger("The system is not fully supported in Windows OS. The application quits now .")
            exit()
        else: # like freebsd,
            self.logger("This platform is not supported")
            exit()

    def setting_up_local_linux_with_freesurfer(self):
        """
        install miniconda and require library
        :return:
        """
        setup_miniconda(self.locations['local']['NIMB_PATHS']['conda_home'])

    def classify_ready(self):
        ready = True
        for p in (self.locations['local']['NIMB_PATHS']['NIMB_NEW_SUBJECTS'],
                  self.NIMB_HOME, self.NIMB_tmp):
            if not os.path.exists(p):
                try:
                    # if path start with ~
                    makedir_ifnot_exist(p)
                except Exception as e:
                    self.logger(e)
            if not os.path.exists(p):
                ready = False
                break
        return ready
        
    def fs_ready(self):
        if self.locations['local']['FREESURFER']['FreeSurfer_install'] == 1:
            if len(self.locations['local']['FREESURFER']['FREESURFER_HOME']) < 1:
                self.logger.fatal("FREESURFER_HOME is missing.")
                return False
            if self.check_freesurfer_ready():
                SUBJECTS_DIR = self.locations['local']['FREESURFER']['FS_SUBJECTS_DIR']
                if not os.path.exists(SUBJECTS_DIR):
                        self.logger('    creating path {}'.format(SUBJECTS_DIR))
                        makedir_ifnot_exist(SUBJECTS_DIR)
                return self.fs_chk_fsaverage_ready(SUBJECTS_DIR)
        else:
            return False

    def fs_chk_fsaverage_ready(self, SUBJECTS_DIR):
        self.fs_fsaverage_copy(SUBJECTS_DIR)
        if not os.path.exists(os.path.join(SUBJECTS_DIR,'fsaverage', 'xhemi')):
            self.logger('fsaverage or fsaverage/xhemi is missing from SUBJECTS_DIR: {}'.format(SUBJECTS_DIR))
            return False
        else:
            return True

    def fs_fsaverage_copy(self, SUBJECTS_DIR):
        if not os.path.exists(os.path.join(SUBJECTS_DIR, 'fsaverage', 'xhemi')):
            fsaverage_path = os.path.join(self.locations['local']['FREESURFER']['FREESURFER_HOME'], "subjects", "fsaverage")
            shutil.copytree(fsaverage_path, os.path.join(SUBJECTS_DIR, 'fsaverage'))

    def check_freesurfer_ready(self):
        """
        check and install freesurfer
        :return:
        """
        ready = False
        if not os.path.exists(os.path.join(self.locations['local']['FREESURFER']['FREESURFER_HOME'], "MCRv84")):
            from .setup_freesurfer import SETUP_FREESURFER
            SETUP_FREESURFER(self.locations)
            ready = True
        else:
            ready =  True
        return ready

    def chk_if_ready_for_fs_glm(self):
        ready = True
        modules_list = ['pandas', 'xlrd', 'openpyxl', 'pathlib']
        if self.fs_ready():
            if not self.chk_if_modules_are_installed(modules_list):
                ready = False
        else:
            ready = False
        return ready     
        
    def chk_if_ready_for_stats(self):
        """will check if xlsx file for project is provided
           if all variables are provided
           if all paths for stats are created
           if NIMB is ready to perform statistical analysis"""
        ready = True
        modules_list = ['pandas', 'xlrd', 'openpyxl', 'pathlib']
        if self.fs_ready():
            if not self.chk_if_modules_are_installed(modules_list):
                ready = False
        else:
            ready = False
        return ready     

