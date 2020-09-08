"""
this module contains common commands that use freqently
"""
try:
    from distribution.distribution_helper import logger
except Exception as e:
    print(e)
import subprocess
import os, logging
from distribution import database

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(module)s %(levelname)s: %(message)s')
logger.setLevel(logging.DEBUG)


def get_username_password(cluster_name):
    """
    given the clustername, get its username and password
    :param cluster_name: name of the cluster, it must be the same as inside sqlite database and json files. There must be a
        cluster_name.json
    :return: username and password if existed, or None, None
    """
    clusters = database._get_Table_Data('Clusters', 'all')
    if not cluster_name in clusters.keys():
        logger.fatal(cluster_name + " is not exisited in the sqlite dabase. Please input its values")
        return None, None
    return clusters[cluster_name]['Username'], clusters[cluster_name]['Password']


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

def makedir_version2(path):
    if path.startswith("~"):
        path = os.path.expanduser(path)
    os.makedirs(path)

def is_ENV_defined(environment_var):
    command = f'if [[ -v {environment_var} ]] ;then echo "YES"; else echo "NO"; fi'
    return is_command_return_okay(command)

def is_conda_module_installed(module_name):
    command = f"conda list | grep {module_name}"
    out = subprocess.getoutput(command)
    # print(command, out)
    if len(out) < 1:
        return False
    return True

def is_writable_directory(folder_path):
    command = f'if [ -w "{folder_path}" ]; then echo "YES"; else echo "NO"; fi'
    return is_command_return_okay(command)

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
    @staticmethod
    def error_bash_command(command):
        logger.fatal("ERROR: {command} is fail".format(command=command))

if __name__ == "__main__":
    # x = is_command_ran_sucessfully("which python")
    # print(x)
    is_command_ran_sucessfully("conda install seaborn -y")