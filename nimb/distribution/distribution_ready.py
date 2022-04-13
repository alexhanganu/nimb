"""
        - local.json - def-supervisor is not changed in the SBATCH command
"""
import os
import shutil
from sys import platform

from setup.get_vars import Get_Vars
from distribution.utilities import is_writable_directory, is_ENV_defined
from distribution.setup_miniconda import (setup_miniconda, is_miniconda_installed,
                                        is_conda_module_installed, check_that_modules_are_installed)
from distribution.utilities import ErrorMessages, makedir_ifnot_exist
from distribution.distribution_definitions import DEFAULT
from setup.interminal_setup import get_yes_no


class DistributionReady():

    def __init__(self, all_vars):

        self.credentials_home = all_vars.credentials_home # NIMB_HOME/credentials_paths.py
        self.locations        = all_vars.location_vars # credentials_home/local.json + remotes.json
        self.stats_vars       = all_vars.stats_vars
        self.proj_vars        = all_vars.projects[all_vars.params.project] # credentials_home/project.json
        self.NIMB_HOME        = self.locations["local"]["NIMB_PATHS"]["NIMB_HOME"]
        self.NIMB_tmp         = self.locations["local"]["NIMB_PATHS"]["NIMB_tmp"]


    def check_ready(self):
        """

        :return: False if there is something wrong
                Otherwise True
        """
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
        conda_home = self.locations['local']['NIMB_PATHS']['conda_home']
        python3_run_cmd = self.locations['local']['PROCESSING']['python3_run_cmd']
        if conda_home in python3_run_cmd:
            print('    conda is used to run python. checking conda at: {}'.format(conda_home))
            if not is_miniconda_installed(conda_home):
                # # if has permission to install
                # if not is_writable_directory(conda_home):
                    # print("miniconda path is not writable. Check the permission.")
                    # return False
                # # true: install setup_minicoda.py
                if get_yes_no('do you want to try and install conda? (may take up to 30 minutes) (y/n)') == 1:
                    setup_miniconda(conda_home, self.NIMB_HOME)
            if check_that_modules_are_installed(conda_home, self.NIMB_HOME):
                print("    conda has all modules installed")
            else:
                ErrorMessages.error_conda()
                return False
        else:
            print(f"    using {python3_run_cmd} as command to run python")


        # # check $FREESURFER_HOME  exists
        # # source home
        # os.system("source ~/.bashrc")
        # if not is_ENV_defined("$FREESURFER_HOME"):
            # print("$FREESURFER_HOME is not defined")
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
                print(e)
                print(f'module {module} is not installed. Cannot continue process')
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
                    print(e)
            if not os.path.exists(p):
                ready = False
                break
        return ready


    def fs_ready(self):
        if self.locations['local']['FREESURFER']['install'] == 1:
            print('FreeSurfer is set to be installed on local computer')
            if len(self.locations['local']['FREESURFER']['FREESURFER_HOME']) < 1:
                print("FREESURFER_HOME is missing. Please define FREESURFER_HOME in the nimb/local.json file")
                return False
            if self.check_freesurfer_ready():
                SUBJECTS_DIR = self.locations['local']['FREESURFER']['SUBJECTS_DIR']
                if not os.path.exists(SUBJECTS_DIR):
                    print('    creating path {}'.format(SUBJECTS_DIR))
                    makedir_ifnot_exist(SUBJECTS_DIR)
                return self.fs_chk_fsaverage_ready(SUBJECTS_DIR)
        else:
            print('FreeSurfer is not installed yet. Please define FreeSurfer_install to 1 in the nimb/local.json file')
            return False


    def fs_chk_fsaverage_ready(self, SUBJECTS_DIR):
        self.fs_fsaverage_copy(SUBJECTS_DIR)
        if not os.path.exists(os.path.join(SUBJECTS_DIR,'fsaverage', 'xhemi')):
            print('fsaverage or fsaverage/xhemi is missing from SUBJECTS_DIR: {}'.format(SUBJECTS_DIR))
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
            SETUP_FREESURFER(self.locations, DEFAULT)
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
        modules_list = ['pandas', 'xlsxwriter', 'xlrd',
                        'openpyxl', 'pathlib', 'sklearn',
                        'matplotlib', 'seaborn']
        if not self.chk_if_modules_are_installed(modules_list):
            print('some python modules are missing: pandas, xlsxwriter, xlrd, openpyxl, pathlib')
            ready = False
        if not self.proj_vars["fname_groups"]:
            print(f'group file is missing. Please check file: {self.credentials_home}/nimb/projects.json')
            ready = False
        return ready
