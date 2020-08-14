#2020 jan 15

from sys import platform, modules
import os, threading, time, shutil
from os import listdir, system, path, makedirs, getcwd, remove, chdir

from distribution.lib import database

win_netframework_download_address = 'https://www.microsoft.com/en-us/download/details.aspx?id=48137'
win_visualstudio_download_address = 'http://landinghub.visualstudio.com/visual-cpp-build-tools'
win_visualstudio_download_address2 = 'https://www.visualstudio.com/thank-you-downloading-visual-studio/?sku=BuildTools&rel=15'

def SETUP_APP():
    MainFolder = database._get_folder('Main')
    if not os.path.exists(MainFolder+'logs/'):
        makedirs(MainFolder+'logs/')
    if not os.path.exists(MainFolder+'processed/'):
        makedirs(MainFolder+'processed/')
    if not os.path.exists(MainFolder+'raw_t1/'):
        makedirs(MainFolder+'raw_t1/')
    if not os.path.exists(MainFolder+'statistics/'):
        makedirs(MainFolder+'statistics/')
    if not os.path.exists(MainFolder+'statistics/stats/'):
        makedirs(MainFolder+'statistics/stats/')
    if platform in ["linux", "linux2"]:
        os.system(f"chmod -R 777 {MainFolder}")
        # must use python3
    #!!!!!!!!!!! modules works only when soft imported. Otherwise - the answer is showing that module is missing.
    if platform == 'win32':
        if 'version_dotcom_Net_Framework < 4.6' not in modules:
            print('Net Framework 4.6 or higher is needed; go to: '+win_netframework_download_address)
        if 'Microsoft Visual C++ 14.0' not in modules:
            print('Microsoft Visual Studio is required, get it with: '+win_visualstudio_download_address)
            system(win_visualstudio_download_address2)
        if 'psftp' not in modules:
            print('please install putty: '+win_putty_download_address)
            # system('set PATH=%PATH%C:\Program Files\PuTTY\psftp')
    if 'pip' not in modules:
        path = []
        system('echo %PATH% >> path_ls.txt')
        with open('path_ls.txt','r') as f:
            for line in f:
                path = line.strip('\n')
        path_ls = path.split(';')
        ls_py_path = []
        for path in path_ls:
            if 'Python' in path:
                ls_py_path.append(path)
        for path in ls_py_path:
            if '\Scripts' not in path:
                if os.path.exists(path):
                    if os.path.exists(path.replace(' ','')+'\Scripts'):
                        if any('pip' in i for i in listdir(path.replace(' ','')+'\Scripts')):
                            pip_path = path
                            print(pip_path)
                            # system('set PATH=%PATH%;'+pip_path')
                            # system('python -m pip install --upgrade pip')
    if 'pandas' not in modules:
        system('pip3 install pandas')
    if 'xlrd' not in modules:
        system('pip3 install xlrd')
    if 'xlsxwriter' not in modules:
        system('pip3 install xlsxwriter')
    if 'pydicom' not in modules:
        system('pip3 install pydicom')
    if 'pandas' and 'xlrd' and 'xlsxwriter' and 'pip' in modules:
        setup = True
    else:
        setup = False
    return setup


def create_setup_cluster_file(cname, cuser, cmaindir, cscratch_dir, supervisor_ccri, pwd, file):
    freesurfer_download_address = freesurfer71_centos7_download_address

    #batch_file_header, batch_walltime_cmd, max_walltime, batch_output_cmd, pbs_file_FS_setup, avail_processes, max_nr_running_batches, submit_cmd = database.Commands_cluster_scheduler(cname,cuser, supervisor_ccri)
    # text4_scheduler = '","'.join(batch_file_header)
    # text_FS_scheduler = '","'.join(pbs_file_FS_setup)
    # ls_process_order = '","'.join(avail_processes)

    py_file_header = ('#!/usr/bin/env python','# coding: utf-8')
    setup_file_content = ('import os','import shutil','\n''cmaindir=\"'+cmaindir+'\"',
                        '\n'
                        'pbs_files_and_content = {\'run.pbs\':(\'cd '+cmaindir+'\',\'python a/crun.py\')}',
                        # 'pbs_file_header = (\"'+text4_scheduler+'\")',
                        # 'pbs_file_FS_setup = (\"'+text_FS_scheduler+'\")',
                        '\n'
                        'if not os.path.exists(cmaindir+\'subjects/\'):','    os.makedirs(cmaindir+\'subjects/\')',
                        'if not os.path.exists(cmaindir+\'a/\'):','    os.makedirs(cmaindir+\'a/\')',
                        'if not os.path.exists(cscratch_dir+\'a_tmp/\'):','    os.makedirs(cscratch_dir+\'a_tmp/\')',
                        'if os.path.exists(cmaindir+\'crun.py\'):',
                        '    shutil.move(cmaindir+\'crun.py\', cmaindir+\'a/crun.py\')',
                        '    shutil.move(cmaindir+\'crunfs.py\', cmaindir+\'a/crunfs.py\')',
                        '    shutil.move(cmaindir+\'cdb.py\', cmaindir+\'a/cdb.py\')',
                        '\n'
                        'if not os.path.exists(cmaindir+\'a/__init__.py\'):',
                        '    open(cmaindir+\'a/__init__.py\',\'w\').close()',
                        '    with open(cmaindir+\'a/__init__.py\',\'a\') as f:',
                        '        f.write(\'__all__ = [\"crun, crunfs, cdb, cwalltime,var"]\')',
                        'open(cmaindir+\'a/var.py\',\'w\').close()',
                        'with open(cmaindir+\'a/var.py\',\'a\') as f:',
                        '        f.write(\'#!/bin/python\\n\')',
                        '        f.write(\'cname=\"'+cname+'\"\\n\')',
                        '        f.write(\'cuser=\"'+cuser+'\"\\n\')',
                        '        f.write(\'supervisor_ccri=\"'+supervisor_ccri+'\"\\n\')',
                        '        f.write(\'cmaindir=\"'+cmaindir+'\"\\n\')',
                        '        f.write(\'cscratch_dir=\"'+cscratch_dir+'\"\\n\')',
                        # '        f.write(\'text_4_scheduler=(\"'+text4_scheduler+'\")\\n\')',
                        # '        f.write(\'batch_walltime_cmd=(\"'+batch_walltime_cmd+'\")\\n\')',
                        # '        f.write(\'max_walltime=(\"'+max_walltime+'\")\\n\')',
                        # '        f.write(\'batch_output_cmd=(\"'+batch_output_cmd+'\")\\n\')',
                        # '        f.write(\'pbs_file_FS_setup=(\"'+text_FS_scheduler+'\")\\n\')',
                        # '        f.write(\'submit_cmd=(\"'+submit_cmd+'\")\\n\')',
                        # '        f.write(\'process_order='+ls_process_order+'\\n\')',
                        # '        f.write(\'max_nr_running_batches=(\"'+str(max_nr_running_batches)+'\")\\n\')',
                        '\n'
                        'for file in pbs_files_and_content:',
                        '    with open(cmaindir+\'a/\'+file,\'w\') as f:',
                        '        for line in pbs_file_header:',
                        '            f.write(line+\'\\n\')',
                        '        f.write(\'\\n\')',
                        '        for line in pbs_file_FS_setup:',
                        '            f.write(line+\'\\n\')',
                        '        f.write(\'\\n\')',
                        '        for line in pbs_files_and_content[file]:',
                        '            f.write(line+\'\\n\')',
                        '\n'
                        'if not os.path.exists(cmaindir+\'freesurfer/\'):',
                        '    os.chdir(cmaindir)',
                        '    os.system(\'curl "'+freesurfer_download_address+'" -o "freesurfer_installation.tar.gz" \')',
                        '    while not os.path.isfile(cmaindir+\'freesurfer_installation.tar.gz\'):',
                        '        time.sleep(1000)',
                        '    os.system(\'tar xvf freesurfer_installation.tar.gz\')',
                        '    os.remove(\'freesurfer_installation.tar.gz\')',
                        'shutil.move(cmaindir+\'.license\', cmaindir+\'freesurfer/.license\')',
                        'if not os.path.exists(cmaindir+\'freesurfer/MCRv80\'):',
                        '    os.chdir(cmaindir+\'freesurfer\')',
                        '    os.system(\'curl "'+matlab_FS_install_cmd_long+'" -o "matlab_runtime.tar.gz" \')',
                        '    while not os.path.isfile(cmaindir+\'freesurfer/matlab_runtime.tar.gz\'):',
                        '        time.sleep(30)',
                        '    os.system(\'tar xvf matlab_runtime.tar.gz\')',
                        '    os.remove(\'matlab_runtime.tar.gz\')',
                        'print(\'SETUP FINISHED\')',)

                        #os.system(\'curl -O https://repo.continuum.io/archive/Anaconda3-5.0.1-Linux-x86_64.sh \')',
                        #os.system(\'bash '+cmaindir+'Anaconda3-5.0.1-Linux-x86_64.sh\')',
                        #os.system(\'\')',
                        #print('yes')
                        #os.system(\'\')',
                        #print('yes')
                        #os.system(\'anaconda3/bin/conda install -c conda-forge dipy \')',
                        #print('y')
                        #nipype doesn\'t work
                        #os.system(\'anaconda3/bin/conda install -channel conda-forge nipype \')',

    open(pwd+file,'w').close()
    with open(pwd+file, 'a') as f:
        for line in py_file_header:
            f.write(line+'\n')
        f.write('\n')
        for line in setup_file_content:
            f.write(line+'\n')


def setup_pbs_file(pwd,cname,supervisor_ccri,cmaindir):
    batch_file_header, _, _, _, _ = database.Commands_cluster_scheduler(cname,supervisor_ccri)

    open(pwd+'a/clib/run_setup.pbs','w').close()
    with open(pwd+'a/clib/run_setup.pbs','a') as f:
                for line in batch_file_header:
                    f.write(line+'\n')
                f.write('\n')
                f.write('cd '+cmaindir+'\n')
                f.write('python setup_cluster_file.py\n')
                f.write('rm setup_cluster_file.py\n')
                f.write('rm run_setup.pbs\n')


def SETUP_CLUSTER(cname, cuser, caddress, cmaindir, cscratch_dir, cpw, supervisor_ccri):
    print('SETTING UP THE CLUSTER')
    pwd = getcwd().replace(path.sep, '/')+'/'

    create_setup_cluster_file(cname, cuser, cmaindir, cscratch_dir, supervisor_ccri, pwd, 'a/clib/setup_cluster_file.py')
    setup_pbs_file(pwd,cname,supervisor_ccri,cmaindir)
    files2cp = ('crun.py','crunfs.py','cdb.py','.license','setup_cluster_file.py','run_setup.pbs')

    ccmd_qsub = 'qsub '+cmaindir+'run_setup.pbs'
    ccmd_python = 'python '+cmaindir+'setup_cluster_file.py'

    if platform == 'linux' or platform == 'linux2':
        for file in files2cp:
            system('sshpass -p '+cpw+' scp '+pwd+'a/clib/'+file+' '+cuser+'@'+caddress+':'+cmaindir+file)
        time.sleep(5)
        system('sshpass -p '+cpw+' ssh -t '+cuser+'@'+caddress+' '+ccmd_qsub)

    elif platform == 'darwin':
        system('sftp '+cuser+'@'+caddress)
        time.sleep(10)
        for file in files2cp:
            system('put '+pwd+'a/clib/'+file+' '+cmaindir+file)
        system('quit\n')
        time.sleep(5)
        cmd = ('ssh '+cuser+'@'+caddress+' nohup '+ccmd_qsub)
        system(cmd)
    elif platform == 'win32':
        open(pwd+'a/clib/psftpcsetup.scr','w').close()
        with open(pwd+'a/clib/psftpcsetup.scr','a') as scr:
            scr.write('cd '+cmaindir+'\n')
            for file in files2cp:
                scr.write('put '+pwd+'a/clib/'+file+' '+cmaindir+file+'\n')
            scr.write('quit\n')
        cmd = ('psftp '+cuser+'@'+caddress+' -pw '+cpw+' -b '+pwd+'/a/clib/psftpcsetup.scr')
        system(cmd)
        time.sleep(5)
        remove(pwd+'a/clib/psftpcsetup.scr')
        open(pwd+'a/clib/crun_qsub.scr','w').close()
        with open(pwd+'a/clib/crun_qsub.scr','a') as scr:
            scr.write(ccmd_python)
        cmd = ('putty.exe -ssh -2 '+cuser+'@'+caddress+' -pw '+cpw+' -m '+pwd+'a/clib/crun_qsub.scr')
        system(cmd)
        remove(pwd+'a/clib/crun_qsub.scr')

    remove(pwd+'a/clib/setup_cluster_file.py')
    remove(pwd+'a/clib/run_setup.pbs')
    print('FINISHED SETTING UP THE CLUSTER')
    

def SETUP_LOCAL(local_maindir):
    print('SETTING UP LOCAL')
    pwd = getcwd().replace(path.sep, '/')+'/'
    system('sudo chmod 777 '+local_maindir) # why sudo here?
    # check if sudo is needed, what happens if user is not in sudo group ==> script failed
    # if sudo fail, run the normal command, for now, not check if command fails
    system('chmod 777 ' + local_maindir)  # why sudo here?
    # notes: default mode of makedir is 777
    if not path.exists(local_maindir+'a/'):
        makedirs(local_maindir+'a/')
    if not path.exists(local_maindir+'a/lib/'):
        makedirs(local_maindir+'a/lib/')
    if not path.exists(local_maindir+'a/res/'):
        makedirs(local_maindir+'a/res/')
    if not path.exists(local_maindir+'a/res/log/'):
        makedirs(local_maindir+'a/res/log/')
    if not path.exists(local_maindir+'a/res/pbs/'):
        makedirs(local_maindir+'a/res/pbs/')
    if not path.exists(local_maindir+'a/res/stats/'):
        makedirs(local_maindir+'a/res/stats/')
    if not path.exists(local_maindir+'a/__init__.py'):
        open(local_maindir+'a/__init__.py','w').close()
        with open(local_maindir+'a/__init__.py','a') as f:
            f.write('__all__ = [\"local_run, local_runfs\"]')
    # force the mode=777 recursive for all sub-folders
    # todo: check the needed of this chmod +R 777 later within the documents
    # just make sure its mode is 777 for all files, in case of fire!
    system('sudo chmod -R 777 ' + local_maindir)
    # in case that the user is not in sudo group, run again
    system('chmod -R 777 ' + local_maindir)
    shutil.copy('a/lib/local_run.py', local_maindir+'a/local_run.py')
    shutil.copy('a/lib/local_runfs.py', local_maindir+'a/local_runfs.py')
    shutil.copy('a/lib/local_db.py', local_maindir+'a/local_db.py')
    clusters = database._get_credentials('all')
    clusters_data = []
    for cred in clusters:
        clusters_data[cred] = []
        clusters_data[cred].append(clusters[cred][0])
        clusters_data[cred].append(clusters[cred][1])
        clusters_data[cred].append(clusters[cred][2])
        clusters_data[cred].append(clusters[cred][4])
    open(local_maindir+'a/lib/clusters_data.py','w').close()
    with open(local_maindir+'a/lib/clusters_data.py', 'a') as f:
        f.write('clusters_data={')
        for cred in clusters_data:
            f.write('\''+cred+'\':[')
            for value in clusters_data[cred]:
                f.write('\''+value+'\',')
            f.write(']')
        f.write('}')
    if not path.exists(local_maindir+'a/lib/__init__.py'):
        open(local_maindir+'a/lib/__init__.py','w').close()
        with open(local_maindir+'a/lib/__init__.py','a') as f:
            f.write('__all__ = []')
    if not path.exists(local_maindir+'a/lib/var.py'):
        open(local_maindir+'a/lib/var.py','w').close()
        with open(local_maindir+'a/lib/var.py','a') as f:
            f.write('#!/bin/python\n')
            f.write('local_maindir=\''+local_maindir+'\'')
    r = system('curl -V')
    if r == 32512:
        system('sudo apt install curl')
        print('y')
    if not path.exists(local_maindir+'freesurfer/'):
        chdir(local_maindir)
        system('curl '+freesurfer_download_address+' -o freesurfer_installation.tar.gz')
        while not path.isfile(local_maindir+'freesurfer_installation.tar.gz'):
            time.sleep(1000)
        system('tar xvf freesurfer_installation.tar.gz')
        remove('freesurfer_installation.tar.gz')
        shutil.move(pwd+'a/clib/.license', local_maindir+'freesurfer/.license')
    if not path.exists(local_maindir+'freesurfer/MCRv80'):
            chdir(local_maindir+'freesurfer')
            system('curl '+matlab_runtime_download_address+' -o matlab_runtime.tar.gz')
            while not path.isfile(local_maindir+'freesurfer/matlab_runtime.tar.gz'):
                time.sleep(30)
            system('tar xvf matlab_runtime.tar.gz')
            remove('matlab_runtime.tar.gz')
    system('sudo apt-get install sshpass')
    system('sudo yum install sshpass')
    chdir(local_maindir)
    system('sudo apt-get install tcsh')
    system('echo \'export FREESURFER_HOME='+local_maindir+'freesurfer\' >> ~/.bashrc')
    system('echo \'source $FREESURFER_HOME/SetUpFreeSurfer.sh\' >> ~/.bashrc')
    if not path.exists(local_maindir+'fsl'):
        system('curl https://fsl.fmrib.ox.ac.uk/fsldownloads/fslinstaller.py -o fslinstaller.py')
        while not path.isfile(local_maindir+'fslinstaller.py'):
                time.sleep(30)
        system('python fslinstaller.py')
        print('')
        remove('fslinstaller.py')
    #system('git clone https://github.com/nipy/dipy.git')
    #chdir(local_maindir+'dipy')
    #system('sudo python setup.py install')
    #system('sudo python setup.py build_ext --inplace')
    #system('echo \'export PYTHONPATH='+local_maindir+'dipy:$PYTHONPATH\' >> ~/.bashrc')
    #system('sudo apt-get install python-dev python-setuptools')
    #print('y')
    #system('sudo apt-get install python-numpy python-scipy')
    #system('sudo apt-get install cython')
    #system('sudo apt install python-pip')
    #print('y')
    #system('sudo pip install nibabel')
    system('sudo apt-get install python-nipype')
    print('y')
    system('pip3 install --user nipy') #http://nipy.org/nipy/users/installation.html
    #system('sudo apt-get install git')
    #print('y')
    #system('sudo apt-get install cmake')
    #print('y')
    #system('git clone git://github.com/stnava/ANTs.git') #http://advants.sourceforge.net/Developer/installation.html
    #system('mkdir '+local_maindir+'antsbin/')
    #chdir(local_maindir+'antsbin')
    #system('cmake ../ANTs')
    #system('cmake')
    #print('c')
    #print('g')
    #print('exit to terminal')
    #system('make -j 4')
    #system('curl https://github.com/stnava/ANTs/tarball/master -o ants.tar.zip')
    print('FINISHED SETTING UP LOCAL')


def SETUP_LOCAL_v2(local_maindir):
    # -y for silent install
    install_manager = 'apt-get -y'
    import platform
    if 'centos' in platform.platform():
        install_manager = "yum -y"

    print('SETTING UP LOCAL v2')
    pwd = getcwd().replace(path.sep, '/')+'/'
    system('sudo chmod 777 '+local_maindir) # why sudo here?

    system('chmod 777 ' + local_maindir)  # if sudo fail
    # notes: default mode of makedir is 777
    if not path.exists(local_maindir+'a/'):
        makedirs(local_maindir+'a/')
    if not path.exists(local_maindir+'a/lib/'):
        makedirs(local_maindir+'a/lib/')
    system('sudo chmod -R 777 ' + local_maindir)
    # in case that the user is not in sudo group, run again
    system('chmod -R 777 ' + local_maindir)
    shutil.copy('a/lib/local_run.py', local_maindir+'a/local_run.py')
    shutil.copy('a/lib/local_runfs.py', local_maindir+'a/local_runfs.py')
    shutil.copy('a/lib/local_db.py', local_maindir+'a/local_db.py')
    r = system('curl -V')
    if r == 32512:
        system(f'sudo {install_manager} install curl ')
        print('y')
    if not path.exists(local_maindir+'freesurfer/'):
        chdir(local_maindir)
        system('curl '+freesurfer_download_address+' -o freesurfer_installation.tar.gz')
        while not path.isfile(local_maindir+'freesurfer_installation.tar.gz'):
            time.sleep(1000)
        system('tar xvf freesurfer_installation.tar.gz')
        remove('freesurfer_installation.tar.gz')
        shutil.move(pwd+'a/clib/.license', local_maindir+'freesurfer/.license')
    if not path.exists(local_maindir+'freesurfer/MCRv80'):
            chdir(local_maindir+'freesurfer')
            system('curl '+matlab_runtime_download_address+' -o matlab_runtime.tar.gz')
            while not path.isfile(local_maindir+'freesurfer/matlab_runtime.tar.gz'):
                time.sleep(30)
            system('tar xvf matlab_runtime.tar.gz')
            remove('matlab_runtime.tar.gz')
    system(f'sudo {install_manager}  install sshpass')
    # system('sudo yum install sshpass -y')
    chdir(local_maindir)
    system(f'sudo {install_manager}  install tcsh')
    system('echo \'export FREESURFER_HOME='+local_maindir+'freesurfer\' >> ~/.bashrc')
    system('echo \'source $FREESURFER_HOME/SetUpFreeSurfer.sh\' >> ~/.bashrc')
    if not path.exists(local_maindir+'fsl'):
        system('curl https://fsl.fmrib.ox.ac.uk/fsldownloads/fslinstaller.py -o fslinstaller.py')
        while not path.isfile(local_maindir+'fslinstaller.py'):
                time.sleep(30)
        system('python fslinstaller.py')
        print('')
        remove('fslinstaller.py')
    system(f'sudo {install_manager}  install python-nipype ')
    print('y')
    system('pip3 install --user nipy')
    system("pip3 install scp paramiko")
    system("pip3 install xlsxwriter xlrd ")
    print('FINISHED SETTING UP LOCAL')
