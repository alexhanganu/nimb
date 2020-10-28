#!/usr/bin/env python3
# coding: utf-8
# 2020.08.13

import sys

print(sys.version)
from os import path, chdir, system, remove, makedirs
import subprocess
from os.path import expanduser


def is_command_ran_sucessfully(command):
    command = """
        {0} > /dev/null
        if [ $? -eq 0 ]; then
            echo "YES"
        else
            echo "NO"
        fi
        """.format(command)
    print(command)
    result =  is_command_return_okay(command)
    if result is False:
        print("ERROR: {0} is fail".format(command))
    return result
def is_command_return_okay(command):
    out = subprocess.getoutput(command)
    print(out)
    if out.strip() == "YES":
        print("yessss")
        return True
    return False

def setup_miniconda(miniconda_home):
    """
    :param miniconda_home: it is the prefix of miniconda, for example /users/test/demo, it then
    creates the miniconda3 folder like this   /users/test/demo/miniconda3
    :return:
    """
    # if any system() return non-zero number, quit the application and raise error?
    miniconda_home = expanduser(miniconda_home)
    if not path.exists(miniconda_home):
        makedirs(miniconda_home)

    chdir(path.join(miniconda_home, '..'))
    is_command_ran_sucessfully(
        'curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda3.sh')
    system('chmod +x miniconda3.sh')
    system('./miniconda3.sh -b -p ' + path.join(miniconda_home,"miniconda3"))
    # remove('miniconda3.sh')
    cmd = 'export PATH=' + path.join(miniconda_home,'miniconda3') + '/bin:$PATH >> $HOME/.bashrc'
    cmd = """echo  'export PATH="{0}/bin:$PATH"' >> $HOME/.bashrc""".format(path.join(miniconda_home,'miniconda3'))
    print(cmd)
    print("*"*10)
    system(cmd)
    # make sure install python 3.7
    conda_bin = path.join(miniconda_home,'miniconda3/bin/conda')
    system(f'{conda_bin} install -y python=3.7')
    system(f'{conda_bin} init')
    system(f'{conda_bin} update -y conda')
    system(f'{conda_bin} config --set report_errors false')
    system(f'{conda_bin} install -y -c conda-forge dcm2niix')
    system(f'{conda_bin} install -y -c conda-forge dipy')
    system(f'{conda_bin} install -y -c conda-forge nilearn')
    system(f'{conda_bin} install -y -c conda-forge nipype')
    system(f'{conda_bin} install -y glob')
    system(f'{conda_bin} install -y shutil')
    system(f'{conda_bin} install -y pandas')
    system(f'{conda_bin} install -y numpy')
    system(f'{conda_bin} install -y scipy')
    system(f'{conda_bin} install -y xlrd')
    system(f'{conda_bin} install -y paramiko')
    system(f'{conda_bin} install -y openpyxl')
    system(f'{conda_bin} install -y xlsxwriter')
    system(f'{conda_bin} install -y xlrd')
    system(f'{conda_bin} install -y -c conda-forge nipy')
    system(f'{conda_bin} install -y -c conda-forge PyInquirer')
    # must activate the conda environment before using by sourcing the bash profile. Otherwise, does not work
    system("source $HOME/.bashrc")
    try:
        system(f'{conda_bin} install -y -c conda-forge dcm2bids')
    except Exception as e:
        print(e)
    print(
        'FINISHED Installing miniconda3 with dcm2niix, dcm2bids, pandas, numpy, xlrd, xlsxwriter, paramiko, dipy')
    # return True


def check_that_modules_are_installed():
    print('checking that modules are installed')


def is_miniconda_installed():
    """
    check if miniconda/anaconda is installed in the system:
        it will check the existing of conda command
    the default path of miniconda shoule be /miniconda3/bin/conda
    :return:
        - True: miniconda is installed
        - False otherwise
    """
    command = "source $HOME/.bashrc > dev/null; command -v conda"  # check if conand exisit in the path
    out = subprocess.getoutput(command)
    # print(command, out)
    if len(out) < 1:
        return False
    return True


def is_conda_module_installed(module_name):
    command = "conda list | grep {0}".format(module_name)
    out = subprocess.getoutput(command)
    # print(command, out)
    if len(out) < 1:
        return False
    return True


if __name__ == "__main__":
    miniconda_home = NIMB_HOME = "~/tmp1"
    setup_miniconda(miniconda_home)
