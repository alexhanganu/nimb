#!/bin/python
#Alexandru Hanganu, 2017 June 27

from os import system, path, remove
import time
from sys import platform
from . import SSHHelper
from . import database
freesurfer = database._get_folder('Main')

def start_cluster():
    clusters = database._get_credentials('all')
    for cred in clusters:
        cuser = clusters[cred][0]
        caddress = clusters[cred][1]
        cmaindir = clusters[cred][2]
        cpw = clusters[cred][4]
        if caddress == 'helios.calculquebec.ca':
            submitting_cmd = 'msub'
        else:
            submitting_cmd = 'qsub'
        ccmd_qsub = (submitting_cmd+' '+cmaindir+'a/run.pbs')
        if platform == 'darwin' or platform == 'linux' or platform == 'linux2':
            cmd = ('ssh '+cuser+'@'+caddress+' nohup '+ccmd_qsub)
            system(cmd)
            print('Cluster analysis started')
        elif platform == 'win32':
            open(freesurfer+'crun_qsub.scr','w').close()
            with open(freesurfer+'crun_qsub.scr','a') as scr:
                scr.write(ccmd_qsub)
            cmd = ('putty.exe -ssh -2 '+cuser+'@'+caddress+' -pw '+cpw+' -m '+freesurfer+'crun_qsub.scr')
            system(cmd)
            remove(freesurfer+'crun_qsub.scr')
            print('Cluster analysis started on: ', cred)


def get_db_from_cluster():
    clusters = database._get_credentials('all')
    for cred in clusters:
                cname = cred
                cuser = clusters[cred][0]
                caddress = clusters[cred][1]
                cmaindir = clusters[cred][2]
                chomedir = clusters[cred][3]
                cpw = clusters[cred][4]
                supervisor_ccri = clusters[cred][5]

    import time

    if platform == 'darwin' or platform == 'linux' or platform == 'linux2':
        cmd = ('ssh '+cuser+'@'+caddress+' nohup '+'qstat -u '+cuser+' >> status_cluster')
        system(cmd)
        time.sleep(1)
        cmd = ('scp '+cuser+'@'+caddress+':'+cmaindir+'status_cluster '+freesurfer+'logs/')
        system(cmd)
        cmd = ('ssh '+cuser+'@'+caddress+' nohup '+'rm '+cmaindir+'status_cluster')
        system(cmd)
        while not path.exists(freesurfer+'logs/status_cluster'):
            time.sleep(1)
    elif platform == 'win32':
        print(cuser, cname, caddress, cmaindir, chomedir, cpw, supervisor_ccri)
        # with open(freesurfer+'psftpcpdb.scr','a') as scr:
            # scr.write('get /scratch/'+cuser+'/a_tmp/db '+'C:/Users/Jessica/Desktop/\n')
            # scr.write('quit')
        # cmd = ('psftp '+cuser+'@'+caddress+' -pw '+cpw+' -b '+freesurfer+'psftpcpdb.scr')
        # system(cmd)
        # remove(freesurfer+'psftpcpdb.scr')

        # count = 0
        # while count <4 and not path.exists(freesurfer+'logs/status_cluster'):
            # time.sleep(2)
            # system(cmd)
            # count += 1
        # if count == 3 and not path.exists(freesurfer+'logs/status_cluster'):
            # open(freesurfer+'logs/psftpcpstatus.scr','w').close()
            # with open(freesurfer+'logs/psftpcpstatus.scr','a') as scr:
                # scr.write('get '+chomedir+'status_cluster '+freesurfer+'logs/status_cluster\n')
                # scr.write('del '+chomedir+'status_cluster\n')
                # scr.write('quit')
            # cmd = ('psftp '+cuser+'@'+caddress+' -pw '+cpw+' -b '+freesurfer+'logs/psftpcpstatus.scr')
		
        # remove(freesurfer+'logs/psftpcpstatus.scr')



def get_cluster_status_file():
    clusters = database._get_credentials('all')
    for cred in clusters:
                cname = cred
                cuser = clusters[cred][0]
                caddress = clusters[cred][1]
                cmaindir = clusters[cred][2]
                chomedir = clusters[cred][3]
                cpw = clusters[cred][4]
                supervisor_ccri = clusters[cred][5]

    import time

    if platform == 'darwin' or platform == 'linux' or platform == 'linux2':
        cmd = ('ssh '+cuser+'@'+caddress+' nohup '+'qstat -u '+cuser+' >> status_cluster')
        system(cmd)
        time.sleep(1)
        cmd = ('scp '+cuser+'@'+caddress+':'+cmaindir+'status_cluster '+freesurfer+'logs/')
        system(cmd)
        cmd = ('ssh '+cuser+'@'+caddress+' nohup '+'rm '+cmaindir+'status_cluster')
        system(cmd)
        while not path.exists(freesurfer+'logs/status_cluster'):
            time.sleep(1)
    elif platform == 'win32':
        with open(freesurfer+'logs/check_cluster_status.scr','a') as scr:
            scr.write('qstat -u '+cuser+' >> status_cluster')
        cmd = ('putty.exe -ssh -2 '+cuser+'@'+caddress+' -pw '+cpw+' -m '+freesurfer+'logs/check_cluster_status.scr')
        system(cmd)
        remove(freesurfer+'logs/check_cluster_status.scr')
        with open(freesurfer+'logs/psftpcpstatus.scr','a') as scr:
            scr.write('get '+cmaindir+'status_cluster '+freesurfer+'logs/status_cluster\n')
            scr.write('del '+cmaindir+'status_cluster\n')
            scr.write('quit')
        cmd = ('psftp '+cuser+'@'+caddress+' -pw '+cpw+' -b '+freesurfer+'logs/psftpcpstatus.scr')

        count = 0
        while count <4 and not path.exists(freesurfer+'logs/status_cluster'):
            time.sleep(2)
            system(cmd)
            count += 1
        if count == 3 and not path.exists(freesurfer+'logs/status_cluster'):
            open(freesurfer+'logs/psftpcpstatus.scr','w').close()
            with open(freesurfer+'logs/psftpcpstatus.scr','a') as scr:
                scr.write('get '+chomedir+'status_cluster '+freesurfer+'logs/status_cluster\n')
                scr.write('del '+chomedir+'status_cluster\n')
                scr.write('quit')
            cmd = ('psftp '+cuser+'@'+caddress+' -pw '+cpw+' -b '+freesurfer+'logs/psftpcpstatus.scr')
		
        remove(freesurfer+'logs/psftpcpstatus.scr')


def check_cluster_status():
    get_cluster_status_file()
    while not path.exists(freesurfer+'logs/status_cluster'):
        time.sleep(2)
    try:
        import pandas as pd
    except ImportError:
        pass

    nr_of_running_tasks = 0
    nr_qued = 0
    if path.getsize(freesurfer+'logs/status_cluster')>0:
        data = pd.read_fwf(freesurfer+'logs/status_cluster')
        data.columns = data.iloc[2]
        data = data.drop(data.index[[0,1,2,3]])
        data = data.reset_index(drop=True)
        data.drop(['Username', 'Queue', 'Jobname', 'SessID', 'NDS','TSK','Memory'], axis=1, inplace=True)
        nr_of_running_tasks = 0
        nr_qued =0
        for value in data['S']:
            if value == 'Q':
                nr_qued += 1
            elif value == 'R':
                nr_of_running_tasks += 1

    return(nr_of_running_tasks, nr_qued)


def delete_all_running_tasks_on_cluster(cuser, caddress, cpw, cmaindir):
    get_cluster_status_file()
    while not path.exists(freesurfer+'logs/status_cluster'):
        time.sleep(2)

    try:
        import pandas as pd
    except ImportError:
        pass

    lsjob2del = []
    if path.getsize(freesurfer+'logs/status_cluster')>0:
        data = pd.read_fwf(freesurfer+'logs/status_cluster')
        data.columns = data.iloc[2]
        data = data.drop(data.index[[0,1,2,3]])
        data = data.reset_index(drop=True)
        data.drop(['Username', 'Queue', 'SessID', 'NDS','TSK','Memory'], axis=1, inplace=True)
        for value in data['Job ID']:
            lsjob2del.append(value)

        with open(freesurfer+'logs/del_tasks.scr', 'a') as f:
            for value in lsjob2del:
                f.write('qdel '+value+'\n')
        cmd = ('putty.exe -ssh -2 '+cuser+'@'+caddress+' -pw '+cpw+' -m '+freesurfer+'logs/del_tasks.scr')
        system(cmd)
        remove(freesurfer+'logs/del_tasks.scr')


def delete_specific_tasks_on_cluster(cuser, caddress, cpw, cmaindir, text2search):
    get_cluster_status_file()
    while not path.exists(freesurfer+'logs/status_cluster'):
        time.sleep(2)

    try:
        import pandas as pd
    except ImportError:
        pass

    lsjob2del = []
    if path.getsize(freesurfer+'logs/status_cluster')>0:
        data = pd.read_fwf(freesurfer+'logs/status_cluster')
        data.columns = data.iloc[2]
        data = data.drop(data.index[[0,1,2,3]])
        data = data.reset_index(drop=True)
        data.drop(['Username', 'Queue', 'SessID', 'NDS','TSK','Memory'], axis=1, inplace=True)

        for value in data['Jobname']:
            if text2search in value:
                lsjob2del.append(data.loc[data.loc[data['Jobname']==value].index[0], 'Job ID'])

        with open(freesurfer+'logs/del_tasks.scr', 'a') as f:
            for value in lsjob2del:
                f.write('qdel '+value+'\n')
        cmd = ('putty.exe -ssh -2 '+cuser+'@'+caddress+' -pw '+cpw+' -m '+freesurfer+'logs/del_tasks.scr')
        system(cmd)
        remove(freesurfer+'logs/del_tasks.scr')

def check_active_tasks_being_on_cluster(cmaindir):
    try:
        import pandas as pd
    except ImportError:
        pass
    if path.getsize(cmaindir+'status_cluster')>0:
        data = pd.read_fwf(cmaindir+'status_cluster')
        data.columns = data.iloc[2]
        data = data.drop(data.index[[0,1,2,3]])
        data = data.reset_index(drop=True)
        data.drop(['Username', 'Queue', 'Jobname', 'SessID', 'NDS','TSK','Memory'], axis=1, inplace=True)
        nr_of_running_tasks = 0
        nr_qued =0
        for value in data['S']:
            if value == 'Q':
                nr_qued += 1
            elif value == 'R':
                nr_of_running_tasks += 1
    return(nr_of_running_tasks, nr_qued)


def delete_locally_specific_tasks_from_cluster(text2search):
    try:
        import pandas as pd
    except ImportError:
        pass
    lsjob2del = []
    if path.getsize('status')>0:
        data = pd.read_fwf('status')
        data.columns = data.iloc[2]
        data = data.drop(data.index[[0,1,2,3]])
        data = data.reset_index(drop=True)
        data.drop(['Username', 'Queue', 'SessID', 'NDS','TSK','Memory'], axis=1, inplace=True)
        for value in data['Jobname']:
            if text2search in value:
                lsjob2del.append(data.loc[data.loc[data['Jobname']==value].index[0], 'Job ID'])
        with open('del_tasks', 'a') as f:
            for value in lsjob2del:
                f.write('qdel '+value+'\n')
				
				

# def cpfromcluster():
    '''
    copies the statistical data files for each subject from the cluster
    brings them to "statistics/stats" folder and initiates the xtrctdata2xlsx script
    '''
    # cname, cuser, caddress, cmaindir, chomedir, cpw, supervisor_ccri = database._get_credentials()
    # import shutil
    # from sys import platform

    # if not os.path.exists(freesurfer+"statistics/stats/"):
        # os.mkdir(freesurfer+"statistics/stats/")
    # dirstats=(freesurfer+"statistics/stats/")
    #dirstatsfs=(freesurfer+"statistics/statsfs/")
	
    #!!!!!!!!!!!!!CHK if copying stats from cluster will NOT delete any data from local

    # if platform == 'darwin' or platform == 'linux' or platform == 'linux2':
        # from sys import modules
        # if 'sshpass' in modules:
            # system('sshpass -p '+cpw+' scp -r '+cuser+'@'+caddress+':'+cmaindir+'a/res/stats/'+' '+dirstats)
        # else:
            # system('scp -r '+cuser+'@'+caddress+':'+cmaindir+'a/res/stats/'+' '+dirstatsfs)

    # elif platform == 'win32':
        # pwd = os.getcwd().replace(os.path.sep, '/')
        # open('a/win/psftprun.scr','w').close()
        # with open('a/win/psftprun.scr','a') as scr:
            # scr.write('get -r '+cmaindir+'a/res/stats/'+' '+dirstatsfs+'\n')
            # # scr.write('mkdir '+cmaindir+'a/res/copiedstats/\n')
            # # scr.write('cd '+cmaindir+'a/res/stats/\n')
            # # scr.write('mv * '+cmaindir+'a/res/copiedstats/\n')
            # scr.write('quit\n')
        # cmd = ('psftp '+cuser+'@'+caddress+' -pw '+cpw+' -b '+pwd+'/a/win/psftprun.scr')
        # os.system(cmd)
        # while not os.path.exists(dirstatsfs+'subjstats.txt'):
            # time.sleep(5)
        # os.remove(pwd+'/a/win/psftprun.scr')
    # shutil.move(dirstatsfs+'subjstats.txt', PATHstats+'subjstatsfs.txt')

    # lssubjid=[]
    # with open(freesurfer+'statistics/subjstats.txt','rt') as readls:
        # for line in readls:
            # lssubjid.append(line.rstrip('\n'))

def copy_subjects_to_cluster(subjects_json_file_path, cluster_subject_folder, a_folder):
    '''
    copy all the subjects in the subject json file to the cluster using paramiko
    :param subjects_json_file_path: path to the json file of subjects
    :param cluster_subject_folder: the destination folder at server
    :param a_folder: path to 'a' folder
    :return: None
    '''
    SSHHelper.upload_all_subjects(subjects_json_file_path, cluster_subject_folder, a_folder)

