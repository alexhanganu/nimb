"""
this module contains frequently used commands
"""
import os
import sys
from os import makedirs, path, sep

import shutil
import json
from collections import OrderedDict
import subprocess
import logging
import pathlib

from setup import database

log = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(module)s %(levelname)s: %(message)s')
log.setLevel(logging.DEBUG)


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


def save_json(data, file_abspath, print_space = 4, ensure_ascii = False):
    print(f'{" " * print_space}saving new file: {file_abspath}')
    with open(file_abspath, 'w') as f:
        json.dump(data, f, indent=4)
    os.system('chmod 777 {}'.format(file_abspath))


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
        path2chk = path.expanduser(path2chk)
    if not path.exists(path2chk):
        try:
            makedirs(path2chk)
        except (OSError, IOError) as e:
            print(e)
            return None
    return path2chk


def get_path(link1, link2):
        return path.join(link1, link2).replace(sep, '/')


def is_command_return_okay(command):
    out = subprocess.getoutput(command)
    print(out)
    if out == "YES":
        return True
    return False


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


def is_ENV_defined(environment_var):
    command = f'if [[ -v {environment_var} ]] ;then echo "YES"; else echo "NO"; fi'
    return is_command_return_okay(command)


def is_writable_directory(folder_path):
    """
        unix method to check that folder is writable
    """
    command = f'if [ -w "{folder_path}" ]; then echo "YES"; else echo "NO"; fi'
    return is_command_return_okay(command)


def chk_dir_is_writable(folder):
    """
        difficult question because has to apply to different OS
        answer of zak and Kawu at:
        stackoverflow.com/questions/2113427/determining-whether-a-directory-is-writeable
    """
    import tempfile
    import errno

    try:
        testfile = tempfile.TemporaryFile(dir = folder)
        testfile.close()
    except (OSError, IOError) as e:
        if e.errno == errno.EACCES or e.errno == errno.EEXIST:
            return False
        e.filename = folder
        raise
    return True


def chk_dir_is_writable_in_unix(folder):
    """
        answer of Joe Koberg and BioGeek at:
        stackoverflow.com/questions/2113427/determining-whether-a-directory-is-writeable
        this solution is UNIX only
    """
    uid = os.geteuid()
    gid = os.getegid()
    s = os.stat(folder)
    mode = s[stat.ST_MODE]
    return (
     ((s[stat.ST_UID] == uid) and (mode & stat.S_IWUSR)) or
     ((s[stat.ST_GID] == gid) and (mode & stat.S_IWGRP)) or
     (mode & stat.S_IWOTH)
     )


def chk_file_is_writable(file_abspath):
    """
        answer of Rohaq at:
        stackoverflow.com/questions/2113427/determining-whether-a-directory-is-writeable
    """
    try:
        filehandle = open(file_abspath, 'w' )
    except IOError:
        print(f'Unable to write to file {file_abspath}')
        return False
    return True


class ErrorMessages:
    @staticmethod
    def error_classify():
        log.fatal("NIMB is not ready to perform the classification. Please check the configuration files.")
    @staticmethod
    def error_fsready():
        log.fatal("NIMB not ready to perform FreeSurfer processing. Please check the configuration files.")
    @staticmethod
    def password():
        log.fatal("password for remote cluster is missing")
    @staticmethod
    def error_nimb_ready():
        log.fatal(" NIMB is not set")
    @staticmethod
    def error_stat_path():
        log.fatal("STATS_PATHS or STATS_HOME is missing")
    @staticmethod
    def error_bash_command(command):
        log.fatal("ERROR: {command} is fail".format(command=command))
    def error_conda():
        log.info("conda is missing some modules")

def copy_rm_dir(source_data,
                target,
                rm = False):
    """copies a dir
        checks if copy was performed correctly
        if rm = True:
            deleted the source dir
    Args:
        source_data: absolute path to dir of file to be copied
        target: asolute path to new dir/file where to copy
            ATTENTION: must include also the new dir/file name
        rm: bool; If True: will remove the source dir / file
    Return:
        bool: True = copy performed correctly
    """
    if not os.path.exists(target):
        log.info(f'    copying/moving {source_data} to: {target}')
        shutil.copytree(source_data, target)

        # extracting the initial size of the folder to copy, to verify with the copied size
        # if both sizes are similar, source is removed
        # if a new name due to error - was assigned, folder is renamed
        # if user requested archiving - archiving is performed.
        size_src = sum(f.stat().st_size for f in pathlib.Path(source_data).glob('**/*') if f.is_file())
        size_dst = sum(f.stat().st_size for f in pathlib.Path(target).glob('**/*') if f.is_file())
        if size_src == size_dst:
            shutil.rmtree(source_data)
        return True
    else:
        log.info(f'    ERR: cannot copy, {target} exists')
        return False

