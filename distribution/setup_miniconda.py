#!/usr/bin/env python
# coding: utf-8
# 2020.08.13

    from os import path, chdir, system, remove

def setup_miniconda(NIMB_HOME):

    if not path.exists(path.join(NIMB_HOME, 'miniconda3')):
        chdir(NIMB_HOME)
        system('curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda3.sh')
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
        system('./miniconda3/bin/conda install -y glob')
        system('./miniconda3/bin/conda install -y shutil')
        system('./miniconda3/bin/conda install -y pandas')
        system('./miniconda3/bin/conda install -y numpy')
        system('./miniconda3/bin/conda install -y scipy')
        system('./miniconda3/bin/conda install -y xlrd')
        system('./miniconda3/bin/conda install -y paramiko')
        system('./miniconda3/bin/conda install -y openpyxl')
        system('./miniconda3/bin/conda install -y xlsxwriter')
    print(
        'FINISHED Installing miniconda3 with dcm2niix, dcm2bids, pandas, numpy, xlrd, xlsxwriter, paramiko, dipy')
