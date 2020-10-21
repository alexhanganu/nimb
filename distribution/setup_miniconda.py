#!/usr/bin/env python
# coding: utf-8
# 2020.08.13


from os import path, chdir, system, remove
import subprocess
from distribution.utilities import is_command_ran_sucessfully
# can be improved by using a yml file

# maybe we try to install all using requirements and check?
system('pip install -r {}'.format(path.join(path.dirname(path.abspath(__file__)), '..', 'requirements.txt')))

def setup_miniconda(miniconda_home):
    #if is_miniconda_installed():
       # system("conda install -y dcm2niix dcm2bids pandas numpy xlrd xlsxwriter paramiko dipy -c conda-forge -c default")
    #    return
    if not path.exists(miniconda_home):
        chdir(path.join(miniconda_home, '..')
        # system('curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda3.sh')
        is_command_ran_sucessfully('curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda3.sh')
        system('chmod +x miniconda3.sh')
        system('./miniconda3.sh -b -p ' + path.join(miniconda_home))
        remove('miniconda3.sh')
        cmd = 'export PATH=~..' + path.join(miniconda_home) + '/bin:$PATH >> $HOME/.bashrc'
        system('echo "' + cmd + '"')
        system('./miniconda3/bin/conda init')
        system('./miniconda3/bin/conda update -y conda')
        system('./miniconda3/bin/conda config --set report_errors false')
        system('./miniconda3/bin/conda install -y -c conda-forge dcm2niix')
        system('./miniconda3/bin/conda install -y -c conda-forge dipy')
        system('./miniconda3/bin/conda install -y -c conda-forge nilearn')
        system('./miniconda3/bin/conda install -y -c conda-forge nipype')
        system('./miniconda3/bin/conda install -y glob')
        system('./miniconda3/bin/conda install -y shutil')
        system('./miniconda3/bin/conda install -y pandas')
        system('./miniconda3/bin/conda install -y numpy')
        system('./miniconda3/bin/conda install -y scipy')
        system('./miniconda3/bin/conda install -y xlrd')
        system('./miniconda3/bin/conda install -y paramiko')
        system('./miniconda3/bin/conda install -y openpyxl')
        system('./miniconda3/bin/conda install -y xlsxwriter')
        system('./miniconda3/bin/conda install -y xlrd')
        system('./miniconda3/bin/conda install -y -c conda-forge nipy')
        system('./miniconda3/bin/conda install -y -c conda-forge PyInquirer')
        # must activate the conda environment before using by sourcing the bash profile. Otherwise, does not work
        system("source $HOME/.bashrc")
    try:
            system('./miniconda3/bin/conda install -y -c conda-forge dcm2bids')
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
    command = "source $HOME/.bashrc > dev/null; command -v conda" # check if conand exisit in the path
    out = subprocess.getoutput(command)
    # print(command, out)
    if len(out) < 1:
        return False
    return True

def is_conda_module_installed(module_name):
    command = f"conda list | grep {module_name}"
    out = subprocess.getoutput(command)
    # print(command, out)
    if len(out) < 1:
        return False
    return True

if __name__ == "__main__":
    miniconda_home = NIMB_HOME = "~/nimb" 
    setup_miniconda(miniconda_home)
