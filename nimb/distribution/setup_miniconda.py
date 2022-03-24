#!/usr/bin/env python3
# coding: utf-8
# 2020.08.13


from os import path, chdir, system, remove, makedirs
from os.path import expanduser
import sys
import subprocess

install_miniconda3 = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"


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

def setup_miniconda(conda_home, NIMB_HOME):
    """
    :param miniconda_home: it is the prefix of miniconda, for example /users/test/demo, it then
    creates the miniconda3 folder like this   /users/test/demo/miniconda3
    :return:
    """
    # if any system() return non-zero number, quit the application and raise error?
    conda_home = expanduser(conda_home)
    if not path.exists(conda_home):
        makedirs(conda_home)

    chdir(path.join(conda_home, '..'))
    is_command_ran_sucessfully(
        'curl {} -o miniconda3.sh'.format(install_miniconda3))
    system('chmod +x miniconda3.sh')
    system('./miniconda3.sh -b -p ' + conda_home)
    # remove('miniconda3.sh')
    cmd = 'export PATH=' + conda_home + '/bin:$PATH >> $HOME/.bashrc'
    cmd = """echo  'export PATH="{0}/bin:$PATH"' >> $HOME/.bashrc""".format(conda_home)
    print(cmd)
    print("*"*10)
    system(cmd)
    system(f'{conda_bin} install -y python=3.7')
    system(f'{conda_bin} init')
    system(f'{conda_bin} update -y conda')
    system(f'{conda_bin} config --set report_errors false')
    check_that_modules_are_installed(conda_home, NIMB_HOME)
    print('FINISHED Installing miniconda3')

def install_conda_module(conda_home, NIMB_HOME, module):
    conda_bin = path.join(conda_home,'bin/conda')
    forge_list = ['dcm2bids', 'dcm2niix', 'dipy', 'nilearn', 'submitit']
    print('installing module: {}'.format(module))
    if module not in forge_list:
        system(f'{conda_bin} install -y {module}')
        # system(f'{conda_bin} install -y shutil')
        # system(f'{conda_bin} install -y pandas')
        # system(f'{conda_bin} install -y xlrd')
        # system(f'{conda_bin} install -y xlsxwriter')
        # system(f'{conda_bin} install -y openpyxl')
        # system(f'{conda_bin} install -y numpy')
        # system(f'{conda_bin} install -y scipy')
        # system(f'{conda_bin} install -y paramiko')
        # system(f'{conda_bin} install -y scp')
        # system(f'{conda_bin} install -y prompt_toolkit')
    elif module == 'xlsxwriter':
        system(f'{conda_bin} install -y -c conda-forge/label/gcc7 {module}')
    else:
        system(f'{conda_bin} install -y -c conda-forge {module}')
    # must activate the conda environment before using by sourcing the bash profile. Otherwise, does not work
    system("source $HOME/.bashrc")

def check_that_modules_are_installed(conda_home, NIMB_HOME):
    print('checking that modules are installed')
    miss = list()
    for module in get_modules(NIMB_HOME):
        if not is_conda_module_installed(module):
            miss.append(module)
            install_conda_module(conda_home, NIMB_HOME, module)
    if miss:
        print('some modules were not installed in conda. Please run again nimb or try to install manually')
        return False
    else:
        return True


def get_modules(NIMB_HOME):
    modules = list()
    requirements = path.join(NIMB_HOME, '../requirements.txt')
    for val in open(requirements).readlines():
        if '>=' in val:
            module = val[:val.find('>')]
        elif '==' in val:
            module = val[:val.find('=')]
        modules.append(module)
    return modules

def is_miniconda_installed(conda_home):
    """
    check if miniconda/anaconda is installed in the system:
        it will check the existing of conda command
    the default path of miniconda shoule be /miniconda3/bin/conda
    :return:
        - True: miniconda is installed
        - False otherwise
    """
    if path.exists(conda_home):
        command = "source $HOME/.bashrc > dev/null; command -v conda"  # check if conda exists in the path
        out = subprocess.getoutput(command)
        # print(command, out)
        if len(out) < 1:
            return False
        return True
    else:
        return False


def is_conda_module_installed(module_name):
    command = "conda list | grep {0}".format(module_name)
    out = subprocess.getoutput(command)
    # print(command, out)
    if len(out) < 1:
        return False
    return True


if __name__ == "__main__":
    conda_home = NIMB_HOME = "~/tmp1"
    setup_miniconda(conda_home)
