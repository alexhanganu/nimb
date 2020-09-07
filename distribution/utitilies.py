"""
this module contains common commands that use freqently
"""
import subprocess
import os
from distribution.distribution_helper import logger

def makedir_version2(path):
    if path.startswith("~"):
        path = os.path.expanduser(path)
    os.makedirs(path)

def is_ENV_defined(environment_var):
    command = f'if [[ -v {environment_var} ]] ;then echo "YES"; else echo "NO"; fi'
    out = subprocess.getoutput(command)
    if out == "YES":
        return True
    return False

def is_conda_module_installed(module_name):
    command = f"conda list | grep {module_name}"
    return is_command_okay(command)

def is_writable_directory(folder_path):
    command = f'if [ -w "{folder_path}" ]; then echo "YES"; else echo "NO"; fi'
    out = subprocess.getoutput(command)
    if out == "YES":
        return True
    return False

def is_command_okay(command):
    """
    :return:
        - True:
        - False: output is empy

    example:
        is_command_okay("conda list | grep pandas")
        return True if pandas exists, False otherwise
    """
    command = command
    out = subprocess.getoutput(command)
    # print(command, out)
    if len(out) < 1:
        return False
    return True


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