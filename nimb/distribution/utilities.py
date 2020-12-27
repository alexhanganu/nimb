"""
this module contains frequently used commands
"""

import os
from os import makedirs, path, sep
import json
from collections import OrderedDict
import subprocess
import logging
from setup import database

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(module)s %(levelname)s: %(message)s')
logger.setLevel(logging.DEBUG)


def load_json_ordered(file_abspath):
    """ Load a JSON file as ordered dict
    Args:
        file_abspath (str): Path of a JSON file
    Return:
        Dictionnary of the JSON file
    """
    with open(file_abspath, 'r') as f:
        return json.load(f, object_pairs_hook=OrderedDict)

def load_json(file_abspath):
    """ Load a JSON file as UNordered dict
    Args:
        file_abspath (str): Path of a JSON file
    Return:
        Dictionnary of the JSON file
    """
    with open(file_abspath, 'r') as f:
        return json.load(f)

def save_json(data, file_abspath):
    with open(file_abspath, 'w') as f:
        json.dump(data, f, indent=4)

def write_txt(file_abspath, lines, write_type = 'w'):
    with open(file_abspath, write_type) as f:
        for val in lines:
            f.write('{}\n'.format(val))

def chk_if_exists(dir):
        if not path.exists(dir):
            makedirs(dir)
        return dir
def makedir_ifnot_exist(path2chk):
    if path2chk.startswith("~"):
        path = os.path.expanduser(path2chk)
    if not os.path.exists(path2chk):
        os.makedirs(path2chk)

def get_path(link1, link2):
        return path.join(link1, link2).replace(sep, '/')

def is_command_ran_sucessfully(command):
    command = f"""
        {command} > /dev/null
        if [ $? -eq 0 ]; then
            echo "YES"
        else
            echo "NO"
        fi
    """
    print(command)
    result =  is_command_return_okay(command)
    if result is False:
        ErrorMessages.error_bash_command(command)
    return result

def is_command_return_okay(command):
    out = subprocess.getoutput(command)
    print(out)
    if out == "YES":
        return True
    return False

def is_ENV_defined(environment_var):
    command = f'if [[ -v {environment_var} ]] ;then echo "YES"; else echo "NO"; fi'
    return is_command_return_okay(command)


def is_writable_directory(folder_path):
    command = f'if [ -w "{folder_path}" ]; then echo "YES"; else echo "NO"; fi'
    return is_command_return_okay(command)


class ErrorMessages:
    @staticmethod
    def error_classify():
        logger.fatal("NIMB is not ready to perform the classification. Please check the configuration files.")
    @staticmethod
    def error_fsready():
        logger.fatal("NIMB not ready to perform FreeSurfer processing. Please check the configuration files.")
    @staticmethod
    def password():
        logger.fatal("password for remote cluster is missing")
    @staticmethod
    def error_nimb_ready():
        logger.fatal(" NIMB is not set")
    @staticmethod
    def error_stat_path():
        logger.fatal("STATS_PATHS or STATS_HOME is missing")
    @staticmethod
    def error_bash_command(command):
        logger.fatal("ERROR: {command} is fail".format(command=command))
    def error_conda():
        logger.info("conda is missing some modules")

if __name__ == "__main__":
    # x = is_command_ran_sucessfully("which python")
    # print(x)
    is_command_ran_sucessfully("conda install seaborn -y")
