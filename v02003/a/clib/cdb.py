#!/bin/python
#Alexandru Hanganu, 2019 November 15
from os import path, listdir, remove, getenv, rename
from var import process_order, LONGITUDINAL_DEFINITION, base_name
import time, shutil


def get_vars():
    from var import cname, cusers_list, cscratch_dir
    cuser = 'not_defined'
    for user in cusers_list:
        if user in getenv('HOME'):
            cuser = user
            break
    else:
        print('ERROR - user not defined')

    if cname=='beluga':
        working_DIR = '/home/'+cuser+'/projects/def-'+cuser+'/'
        dir_home=working_DIR+'a/'
        dir_scratch=cscratch_dir+cuser+'/a_tmp/'
        SUBJECTS_DIR = cscratch_dir+cuser+'/fs-subjects/'
        processed_SUBJECTS_DIR = cscratch_dir+cuser+'/subjects_processed/'
        dir_new_subjects=working_DIR+'subjects/'
    else:
        print(cname, 'variables not defined for this cluster')

    return cuser, dir_home, dir_scratch, SUBJECTS_DIR, processed_SUBJECTS_DIR, dir_new_subjects

cuser, dir_home , dir_scratch, SUBJECTS_DIR, _, _ = get_vars()


def Get_DB():

    db = dict()

    if path.isfile(dir_scratch+'db'):
        shutil.copy(dir_scratch+'db',dir_home+'db.py')
        time.sleep(2)
        from db import DO, QUEUE, RUNNING, RUNNING_JOBS, LONG_DIRS, LONG_TPS, PROCESSED
        db['DO'] = DO
        db['QUEUE'] = QUEUE
        db['RUNNING'] = RUNNING
        db['RUNNING_JOBS'] = RUNNING_JOBS
        db['LONG_DIRS'] = LONG_DIRS
        db['LONG_TPS'] = LONG_TPS
        db['PROCESSED'] = PROCESSED
        time.sleep(2)
        remove(dir_home+'db.py')
    else:
        for action in ['DO','QUEUE','RUNNING',]:
            db[action] = {}
            for process in process_order:
                db[action][process] = []
        db['RUNNING_JOBS'] = {}
        db['LONG_DIRS'] = {}
        db['LONG_TPS'] = {}
        for process in process_order:
            db['PROCESSED']['error_'+process] = []
        db['PROCESSED'] = {'cp2local':[],}
    return db


def Update_DB(d):
    file = dir_scratch+'db'
    open(file,'w').close()
    with open(file,'a') as f:
        for key in d:
            if key != 'RUNNING_JOBS':
                f.write(key+'= {')
                for subkey in d[key]:
                    f.write('\''+subkey+'\':[')
                    for value in sorted(d[key][subkey]):
                        f.write('\''+value+'\',')
                    f.write('],')
                f.write('}\n')
            else:
                f.write(key+'= {')
                for subkey in d[key]:
                    f.write('\''+subkey+'\':'+str(d[key][subkey])+',')
                f.write('}\n')



def Update_status_log(cmd, update=True):
    file = dir_scratch+'status.log'
    if not update:
        print('cleaning status file', file)
        open(file,'w').close()

    dthm = time.strftime('%Y/%m/%d %H:%M')
    with open(file,'a') as f:
        f.write(dthm+' '+cmd+'\n')


def Update_running(cmd):
    file = dir_scratch+'running_'
	
    if cmd == 1:
        if path.isfile(file+'0'):
            rename(file+'0',file+'1')
        else:
            open(file+'1','w').close()
    else:
        if path.isfile(file+'1'):
            rename(file+'1',file+'0')


def get_ls_subjids_in_long_dirs(db):
    lsall = []
    for _id in db['LONG_DIRS']:
        for subjid in db['LONG_DIRS'][_id]:
                if subjid not in lsall:
                    lsall.append(subjid)
        for process in db['PROCESSED']:
            for subjid in db['PROCESSED'][process]:
                if subjid not in lsall:
                    lsall.append(subjid)
    return lsall




def get_registration_files(subjid, d_LONG_DIRS):
    f = dir_home+"new_subjects_registration.json"
    if path.isfile(f):
        import json

        with open(f) as jfile:
            data = json.load(jfile)

        for _id in d_LONG_DIRS:
            if subjid in d_LONG_DIRS[_id]:
                _id = _id
                ses = subjid.replace(_id+'_',"")
                break
            else:
                _id = 'none'
        print(_id, ses)

        if _id != 'none':
            t1_ls_f = data[_id][ses]['anat']['t1']
            flair_ls_f = 'none'
            t2_ls_f = 'none'
            if 'flair' in data[_id][ses]['anat']:
                if data[_id][ses]['anat']['flair']:
                    flair_ls_f = data[_id][ses]['anat']['flair']
            if 't2' in data[_id][ses]['anat']:
                if data[_id][ses]['anat']['t2']:
                    t2_ls_f = data[_id][ses]['anat']['t2']
#        rename(f, dir_home+'new_subjects_registration.json')
        Update_status_log(subjid+' registration files were read')
    return t1_ls_f, flair_ls_f, t2_ls_f




def Update_DB_from_SUBJECTS_DIR_subj2fs(db):

    d = chk_subj_in_SUBJECTS_DIR(db)
    d = chk_new_subjects(db)
    d = chk_subj2fs(db)
    print('done checking SUBJECTS_DIR, subj2fs, subj2restart, subj2rm')

    return db


def chk_new_subjects(db):

    from crunfs import chksubjidinfs

    f = dir_home+"new_subjects.json"
    if path.isfile(f):
        import json
        ls_SUBJECTS_in_long_dirs_processed = get_ls_subjids_in_long_dirs(db)

        with open(f) as jfile:
            data = json.load(jfile)
        for _id in data:
            if not chksubjidinfs(_id):
                for ses in data[_id]:
                    subjid = _id+'_'+ses
                    if subjid not in ls_SUBJECTS_in_long_dirs_processed:
                        if 'anat' in data[_id][ses]:
                            if 't1' in data[_id][ses]['anat']:
                                if data[_id][ses]['anat']['t1']:
                                    if _id not in db['LONG_DIRS']:
                                        db['LONG_DIRS'][_id] = []
                                        db['LONG_TPS'][_id] = []
                                    db['LONG_TPS'][_id].append(ses)
                                    db['LONG_DIRS'][_id].append(subjid)
                                    db['DO']['registration'].append(subjid)
                                else:
                                    db['PROCESSED']['error_registration'].append(subjid)
                                    Update_status_log('ERROR: subj2fs was read and wasn\'t added to database')
                    else:
                        Update_status_log('ERROR: '+subjid+' in database! new one cannot be registered')
        rename(f, dir_home+'new_subjects_registration.json')
        Update_status_log('new subjects database was read')
    return db



def chk_subj_in_SUBJECTS_DIR(db):
    print('checking SUBJECTS_DIR ...')

    from crunfs import chkIsRunning, checks_from_runfs

    def chk_if_exclude(subjid):
        exclude = False
        ls_2_exclude = ['bert','average','README','sample-00','cvs_avg35']
        for value in ls_2_exclude:
            if value in subjid:
                exclude = True
                break
        return exclude

    def get_id(subjid):
        subjid = subjid.replace(base_name,'').split('.',1)[0]
        _id = subjid
        long_name = 'none'
        for long_tp in LONGITUDINAL_DEFINITION:
            if long_tp in subjid:
                _id = subjid.replace(long_tp,'')
                long_name = long_tp
                break
        return _id, long_name

    def get_subjs_running(db):
        ls_subj_running = []
        for ACTION in ('DO', 'QUEUE', 'RUNNING',):
            for process in process_order:
                for subjid in db[ACTION][process]:
                    if subjid not in ls_subj_running:
                        ls_subj_running.append(subjid)
        return ls_subj_running

    def add_new_subjid_to_db(subjid):
        if not chkIsRunning(subjid):
            for process in process_order[1:]:
                if not checks_from_runfs(process, subjid):
                    db['DO'][process].append(subjid)
                    break
        else:
                db['RUNNING'][process_order[1]].append(subjid)


    ls_SUBJECTS = sorted([i for i in listdir(SUBJECTS_DIR) if not chk_if_exclude(i)])
    ls_SUBJECTS_in_long_dirs_processed = get_ls_subjids_in_long_dirs(db)
    ls_SUBJECTS_running = get_subjs_running(db)

    for subjid in ls_SUBJECTS:
        if subjid not in ls_SUBJECTS_in_long_dirs_processed:
            _id, long_name = get_id(subjid)
            print(_id, subjid,' not in LONG_DIRS or PROCESSED')
            if _id in db['LONG_DIRS']:
                if subjid not in db['LONG_DIRS'][_id]:
                    db['LONG_DIRS'][_id].append(subjid)
                if _id not in db['LONG_TPS']:
                    db['LONG_TPS'][_id] = []
                if long_name != 'none' and long_name not in db['LONG_TPS'][_id]:
                    db['LONG_TPS'][_id].append(long_name)
            else:
                db['LONG_DIRS'][_id] = [subjid,]
                db['LONG_TPS'][_id] = []
                if long_name != 'none':
                    db['LONG_TPS'][_id].append(long_name)#+',')
            if base_name not in subjid:
                if subjid not in ls_SUBJECTS_running:
                    add_new_subjid_to_db(subjid)
    return db


def chk_subj2fs(db):
    if path.isfile(dir_home+"subj2fs"):
        from crunfs import chksubjidinfs

        with open(dir_home+"subj2fs",'rt') as readls:
            for line in readls:
                if not chksubjidinfs(line.strip('\r\n')):
                    db['DO']['registration'].append(line.strip('\r\n'))
                else:
                    db['PROCESSED']['error_registration'].append(line.strip('\r\n'))
                    Update_status_log('ERROR: subj2fs was read and wasn\'t added to database')
        remove(dir_home+'subj2fs')
        Update_status_log('subj2fs was read')
    return db



def get_batch_jobs_status():
    from var import cname
    import subprocess

    queue = list(filter(None,subprocess.run(['squeue','-u',cuser], stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')))

    jobs = dict()
    for line in queue[1:]:
            vals = list(filter(None,line.split(' ')))
            jobs[vals[0]] = vals[4]

    return jobs
