#!/bin/python
# 2020.07.23

from os import path, listdir, remove, getenv, rename, mkdir, environ, system, chdir
import time, shutil, json
import logging

import logging
log = logging.getLogger(__name__)
environ['TZ'] = 'US/Eastern'
time.tzset()


def Get_DB(NIMB_HOME, NIMB_tmp, process_order):

    ''' 
    DataBase has a py structure so that in the future it can be easily transfered to an sqlite database
    '''

    dbjson = dict()
    db_json_file = path.join(NIMB_tmp, 'db.json')

    print("NIMB_tmp is:" + NIMB_tmp)
    if path.isfile(db_json_file):
        with open(db_json_file) as db_json_open:
            db = json.load(db_json_open)
        shutil.copy(path.join(NIMB_tmp, 'db.json'), path.join(NIMB_HOME, 'tmp', 'db.json'))
    else:
        db = dict()
        for action in ['DO','RUNNING',]:
            db[action] = {}
            for process in process_order:
                db[action][process] = []
        db['RUNNING_JOBS'] = {}
        db['LONG_DIRS'] = {}
        db['LONG_TPS'] = {}
        db['REGISTRATION'] = {}
        db['ERROR_QUEUE'] = {}
        db['PROCESSED'] = {'cp2local':[],}
        for process in process_order:
            db['PROCESSED']['error_'+process] = []

    return db


def Update_DB(db, NIMB_tmp):
    with open(path.join(NIMB_tmp, 'db.json'), 'w') as jf:
        json.dump(db, jf, indent=4)



def Update_status_log(NIMB_tmp, cmd, update=True):
    print(cmd)
    file = path.join(NIMB_tmp, 'status.log')
    if not update:
        print('cleaning status file', file)
        open(file,'w').close()

    dthm = time.strftime('%Y/%m/%d %H:%M')
    with open(file, 'a') as f:
        f.write(dthm+' '+cmd+'\n')


def Update_running(NIMB_tmp, cmd):
    file = path.join(NIMB_tmp, 'running_'+'_')
    if cmd == 1:
        if path.isfile(file+'0'):
            rename(file+'0', file+'1')
        else:
            open(file+'1', 'w').close()
    else:
        if path.isfile(file+'1'):
            rename(file+'1', file+'0')


def get_ls_subjids_in_long_dirs(db):
    lsall = []
    for _id in db['LONG_DIRS']:
        lsall = lsall + db['LONG_DIRS'][_id]
        for subjid in db['LONG_DIRS'][_id]:
                if subjid not in lsall:
                    lsall.append(subjid)
        for process in db['PROCESSED']:
            for subjid in db['PROCESSED'][process]:
                if subjid not in lsall:
                    lsall.append(subjid)
    return lsall


def check_that_all_files_are_accessible(ls):
	for file in ls:
		if not path.exists(file):
			ls.remove(file)
	return ls


def Update_DB_new_subjects_and_SUBJECTS_DIR(NIMB_tmp, SUBJECTS_DIR, db, process_order, base_name, long_name, freesurfer_version, masks):

    db = chk_subj_in_SUBJECTS_DIR(SUBJECTS_DIR, NIMB_tmp, db, process_order, base_name, long_name, freesurfer_version, masks)
    db = chk_subjects2fs_file(SUBJECTS_DIR, NIMB_tmp, db, base_name, long_name, freesurfer_version, masks)
    db = chk_new_subjects_json_file(SUBJECTS_DIR, NIMB_tmp, db, freesurfer_version, masks)
    return db




def add_subjid_2_DB(NIMB_tmp, subjid, _id, ses, db, ls_SUBJECTS_in_long_dirs_processed):
    if subjid not in ls_SUBJECTS_in_long_dirs_processed:
        if _id not in db['LONG_DIRS']:
            db['LONG_DIRS'][_id] = []
            db['LONG_TPS'][_id] = []
        db['LONG_TPS'][_id].append(ses)
        db['LONG_DIRS'][_id].append(subjid)
        db['DO']['registration'].append(subjid)
    else:
        log.info('ERROR: '+subjid+' in database! new one cannot be registered')
        Update_status_log(NIMB_tmp, 'ERROR: '+subjid+' in database! new one cannot be registered')
    return db



def chk_subjects2fs_file(SUBJECTS_DIR, NIMB_tmp, db, base_name, long_name, freesurfer_version, masks):
    log.info('    NEW_SUBJECTS_DIR checking ...')
    Update_status_log(NIMB_tmp, '    NEW_SUBJECTS_DIR checking ...')

    ls_SUBJECTS_in_long_dirs_processed = get_ls_subjids_in_long_dirs(db)
    from crunfs import checks_from_runfs

    f_subj2fs = path.join(NIMB_tmp, 'subjects2fs')
    if path.isfile(f_subj2fs):
        ls_subj2fs = ls_from_subj2fs(NIMB_tmp, f_subj2fs)
        for subjid in ls_subj2fs:
            log.info('    adding '+subjid+' to database')
            Update_status_log(NIMB_tmp, '    adding '+subjid+' to database')
            _id, ses = get_id_long(subjid, db['LONG_DIRS'], base_name, long_name)
            if not checks_from_runfs(SUBJECTS_DIR, 'registration',_id, freesurfer_version, masks):
                db = add_subjid_2_DB(NIMB_tmp, subjid, _id, ses, db, ls_SUBJECTS_in_long_dirs_processed)
        log.info('new subjects were added from the subjects folder')
        Update_status_log(NIMB_tmp, 'new subjects were added from the subjects folder')
    return db



def chk_new_subjects_json_file(SUBJECTS_DIR, NIMB_tmp, db, freesurfer_version, masks):

    def ls_from_subj2fs(NIMB_tmp, f_subj2fs):
        ls_subjids = list()
        lines = list(open(f_subj2fs,'r'))
        for val in lines:
            if len(val)>3:
                ls_subjids.append(val.strip('\r\n'))
        rename(f_subj2fs, path.join(NIMB_tmp,'zdone_subjects2fs'))
        log.info('subjects2fs was read')
        Update_status_log(NIMB_tmp, 'subjects2fs was read')
        return ls_subjids


    log.info('    new_subjects.json checking ...')
    Update_status_log(NIMB_tmp, '    new_subjects.json checking ...')

    ls_SUBJECTS_in_long_dirs_processed = get_ls_subjids_in_long_dirs(db)
    from crunfs import checks_from_runfs

    f_new_subjects = path.join(NIMB_tmp,"new_subjects.json")
    if path.isfile(f_new_subjects):
        import json
        with open(f_new_subjects) as jfile:
            data = json.load(jfile)
        for _id in data:
            if not checks_from_runfs(SUBJECTS_DIR, 'registration',_id, freesurfer_version, masks):
                for ses in data[_id]:
                    if 'anat' in data[_id][ses]:
                        if 't1' in data[_id][ses]['anat']:
                            if data[_id][ses]['anat']['t1']:
                                subjid = _id+'_'+ses
                                db['REGISTRATION'][subjid] = dict()
                                db['REGISTRATION'][subjid]['anat'] = data[_id][ses]['anat']
                                log.info('        '+subjid+' added to database from new_subjects.json')
                                Update_status_log(NIMB_tmp, '        '+subjid+' added to database from new_subjects.json')
                                db = add_subjid_2_DB(NIMB_tmp, subjid, _id, ses, db, ls_SUBJECTS_in_long_dirs_processed)
                            else:
                                db['PROCESSED']['error_registration'].append(subjid)
                                log.info('ERROR: '+_id+' was read and but was not added to database')
                                Update_status_log(NIMB_tmp, 'ERROR: '+_id+' was read and but was not added to database')
        rename(f_new_subjects, path.join(NIMB_tmp,'znew_subjects_registered_to_db_'+time.strftime("%Y%m%d_%H%M",time.localtime(time.time()))+'.json'))
        log.info('        new subjects were added from the new_subjects.json file')
        Update_status_log(NIMB_tmp, '        new subjects were added from the new_subjects.json file')
    return db


def get_registration_files(subjid, db, nimb_dir, NIMB_tmp, flair_t2_add):
        log.info('    '+subjid+' reading registration files')
        Update_status_log(NIMB_tmp, '    '+subjid+' reading registration files')
        t1_ls_f = db['REGISTRATION'][subjid]['anat']['t1']
        flair_ls_f = 'none'
        t2_ls_f = 'none'
        if 'flair' in db['REGISTRATION'][subjid]['anat'] and flair_t2_add == 1:
            if db['REGISTRATION'][subjid]['anat']['flair']:
                flair_ls_f = db['REGISTRATION'][subjid]['anat']['flair']
        if 't2' in db['REGISTRATION'][subjid]['anat'] and flair_t2_add == 1:
            if db['REGISTRATION'][subjid]['anat']['t2'] and flair_ls_f == 'none':
                t2_ls_f = db['REGISTRATION'][subjid]['anat']['t2']
        log.info('        from db[\'REGISTRATION\']')
        Update_status_log(NIMB_tmp, '        from db[\'REGISTRATION\']')
        return t1_ls_f, flair_ls_f, t2_ls_f



def get_id_long(subjid, LONG_DIRS, base_name, long_name):
        _id = 'none'
        for key in LONG_DIRS:
            if subjid in LONG_DIRS[key]:
                _id = key
                longitud = subjid.replace(_id+'_','')
                break
        if base_name in subjid:
            subjid = subjid.replace(base_name,'').split('.',1)[0]
        if _id == 'none':
            _id = subjid
            if long_name in subjid:
                longitud = subjid[subjid.find(long_name):]
                _id = subjid.replace('_'+longitud,'')
            else:
                longitud = long_name+str(1)
        return _id, longitud



def chk_subj_in_SUBJECTS_DIR(SUBJECTS_DIR, NIMB_tmp, db, process_order, base_name, long_name, freesurfer_version, masks):
    log.info('    SUBJECTS_DIR checking ...')
    Update_status_log(NIMB_tmp, '    SUBJECTS_DIR checking ...')

    from crunfs import chkIsRunning, checks_from_runfs

    def chk_if_exclude(subjid):
        exclude = False
        ls_2_exclude = ['bert','average','README','sample-00','cvs_avg35']
        for value in ls_2_exclude:
            if value in subjid:
                exclude = True
                break
        return exclude

    def get_subjs_running(db, process_order):
        ls_subj_running = []
        for ACTION in ('DO', 'RUNNING',):
            for process in process_order:
                for subjid in db[ACTION][process]:
                    if subjid not in ls_subj_running:
                        ls_subj_running.append(subjid)
        return ls_subj_running

    def add_new_subjid_to_db(subjid, process_order, NIMB_tmp, freesurfer_version, masks):
        if not chkIsRunning(SUBJECTS_DIR, subjid):
            for process in process_order[1:]:
                if not checks_from_runfs(SUBJECTS_DIR, process, subjid, freesurfer_version, masks):
                    log.info('        '+subjid+' sent for DO '+process)
                    Update_status_log(NIMB_tmp, '        '+subjid+' sent for DO '+process)
                    db['DO'][process].append(subjid)
                    break
        else:
            log.info('            IsRunning file present, adding to RUNNING '+process_order[1])
            Update_status_log(NIMB_tmp, '            IsRunning file present, adding to RUNNING '+process_order[1])
            db['RUNNING'][process_order[1]].append(subjid)

    ls_SUBJECTS = sorted([i for i in listdir(SUBJECTS_DIR) if not chk_if_exclude(i)])
    ls_SUBJECTS_in_long_dirs_processed = get_ls_subjids_in_long_dirs(db)
    ls_SUBJECTS_running = get_subjs_running(db, process_order)

    for subjid in ls_SUBJECTS:
        if subjid not in ls_SUBJECTS_in_long_dirs_processed:
            log.info('    '+subjid+' not in PROCESSED')
            Update_status_log(NIMB_tmp, '    '+subjid+' not in PROCESSED')
            _id, longitud = get_id_long(subjid, db['LONG_DIRS'], base_name, long_name)
            log.info('        adding to database: id: '+_id+', long name: '+longitud)
            Update_status_log(NIMB_tmp, '        adding to database: id: '+_id+', long name: '+longitud)
            if _id == subjid:
                subjid = _id+'_'+longitud
                log.info('   no '+long_name+' in '+_id+' Changing name to: '+subjid)
                Update_status_log(NIMB_tmp, '   no '+long_name+' in '+_id+' Changing name to: '+subjid)
                rename(path.join(SUBJECTS_DIR,_id), path.join(SUBJECTS_DIR,subjid))
            if _id not in db['LONG_DIRS']:
                db['LONG_DIRS'][_id] = list()
            if _id in db['LONG_DIRS']:
                if subjid not in db['LONG_DIRS'][_id]:
                    # log.info('        '+subjid+' to LONG_DIRS[\''+_id+'\']')
                    db['LONG_DIRS'][_id].append(subjid)
            if _id not in db['LONG_TPS']:
                # log.info('    adding '+_id+' to LONG_TPS')
                db['LONG_TPS'][_id] = list()
            if _id in db['LONG_TPS']:
                if longitud not in db['LONG_TPS'][_id]:
                    # log.info('    adding '+longitud+' to LONG_TPS[\''+_id+'\']')
                    db['LONG_TPS'][_id].append(longitud)
            if base_name not in subjid:
                if subjid not in ls_SUBJECTS_running:
                    add_new_subjid_to_db(subjid, process_order, NIMB_tmp, freesurfer_version, masks)
    return db



def get_batch_jobs_status(cuser, cusers_list):

    def get_jobs(jobs, queue):

        for line in queue[1:]:
                vals = list(filter(None,line.split(' ')))
                if vals[0] not in jobs:
                    jobs[vals[0]] = vals[4]
        return jobs


    import subprocess

    jobs = dict()
    for cuser in cusers_list:
        queue = list(filter(None,subprocess.run(['squeue','-u',cuser], stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')))
        jobs.update(get_jobs(jobs, queue))

    return jobs
