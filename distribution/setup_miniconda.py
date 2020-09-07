#!/usr/bin/env python
# coding: utf-8
# 2020.08.13


from os import path, chdir, system, remove
import subprocess
from distribution.utitilies import is_command_ran_sucessfully
# can be improved by using a yml file
def setup_miniconda(NIMB_HOME = "~/nimb"):
    #if is_miniconda_installed():
       # system("conda install -y dcm2niix dcm2bids pandas numpy xlrd xlsxwriter paramiko dipy -c conda-forge -c default")
    #    return
    if not path.exists(path.join(NIMB_HOME,"..", 'miniconda3')):
        chdir(NIMB_HOME)
        # system('curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda3.sh')
        is_command_ran_sucessfully('curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda3.sh')
        system('chmod +x miniconda3.sh')
        system('./miniconda3.sh -b -p ' + path.join(NIMB_HOME, 'miniconda3'))
        remove('miniconda3.sh')
        cmd = 'export PATH=~..' + path.join(NIMB_HOME, 'miniconda3') + '/bin:$PATH >> $HOME/.bashrc'
        system('echo "' + cmd + '"')
        system('/miniconda3/bin/conda init')
        system('./miniconda3/bin/conda config --set report_errors false')
        system('./miniconda3/bin/conda install -y dcm2niix')
        system('./miniconda3/bin/conda install -y dcm2bids')
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
        # must activate the conda environment before using by sourcing the bash profile. Otherwise, does not work
        system("source $HOME/.bashrc")
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

if __name__ == "__main__":
    setup_miniconda(NIMB_HOME = "~/nimb")
