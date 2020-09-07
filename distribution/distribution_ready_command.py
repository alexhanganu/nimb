from .distribution_helper import DistributionHelper
import os, sys
from setup.get_vars import Get_Vars
from distribution.utitilies import is_writable_directory, is_conda_module_installed, is_ENV_defined
from distribution.setup_miniconda import setup_miniconda, is_miniconda_installed
from distribution.distribution_helper import logger
class DistributionReady(DistributionHelper):
    """
    This file sole for the READY command.
    """
    local_json = "~/nimb/local.json"
    module_list = ["dcm2niix", "dcm2bids", "pandas", "numpy", "xlrd", "xlsxwriter", "paramiko", "dipy"]
    def check_ready(self):
        """

        :return: False if there is something wrong
                Otherwise True
        """
        if not os.path.isfile(self.local_json):
            vars = Get_Vars() # to make it create loca.json, is it good to be here?
        self.verify_paths() # check NIMB_PATHS and create folder if not exist
        self.get_user_paths_from_terminal() # to do, which ones are get from user?
        if not is_miniconda_installed():
            # if has permission to install
            mini_conda_path = self.locations['local']['NIMB_PATHS']['miniconda_home']
            if not is_writable_directory(mini_conda_path):
                logger.fatal("miniconda path is not writable. Check the permission.")
                return False
            # true: install setup_minicoda.py
            setup_miniconda(self.NIMB_HOME)
        else:
            for module in self.module_list:
                if not is_conda_module_installed(module):
                    os.system(
                        "conda install -y dcm2niix dcm2bids pandas numpy xlrd xlsxwriter paramiko dipy -c conda-forge -c default")
                    break

        # check $FREESURFER_HOME  exists
        # source home
        os.system("source ~/.bashrc")
        if not is_ENV_defined("$FREESURFER_HOME"):
            logger.fatal("$FREESURFER_HOME is not defined")
            return False


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
"""

        - check that ~/nimb/local.json file is present
            - if not - create (currently get_vars is doing this): done in other parts
        - from ~/nimb/local.json check that folders NIMB_PATHS are present; if not - makedirs - still not working (20200901)
        - make terminal survey to allow user to define paths ==> todo 1
        - local.json - def-supervisor is not changed in the SBATCH command
        - check that miniconda is installed (is_miniconda_installed). If not:
            - if False: check that local.json-NIMB_PATHS- miniconda_path has permission to install.
                - If True: initiate distribution. setup_minicoda.py
            - If True: check that all miniconda modules are installed.
                    - if False: initiate distribution. setup_minicoda.py
        - check that source FREESURFER_HOME is a valid command
        - chk on local/remote ifa bash command is failed (like wget, curl)
        - distribution_helper is calling the self.get_username_password_cluster_from_sqlite().
         This should be put in SSHHelper in order to aim to call the functions only once.
          It can be called upon with a function SSHHelper.ready() 
          which would check if all cluster vars are ready; 
          or could be put as rediness checking when instantiating the SSHHelper class.
"""