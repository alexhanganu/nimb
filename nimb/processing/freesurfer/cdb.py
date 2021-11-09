#!/bin/python
# 2020.08.25

from os import path, listdir, rename, environ, system
import time, json
import logging

from fs_checker import FreeSurferChecker


environ['TZ'] = 'US/Eastern'
time.tzset()
log = logging.getLogger(__name__)


def Get_DB(NIMB_HOME, NIMB_tmp, process_order):

    db_json_file = path.join(NIMB_tmp, 'db.json')

    log.info("Database file db.json located at: {}".format(NIMB_tmp))
    if path.isfile(db_json_file):
        with open(db_json_file) as db_json_open:
            db = json.load(db_json_open)
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
    f2save = path.join(NIMB_tmp, 'db.json')
    with open(f2save, 'w') as jf:
        json.dump(db, jf, indent=4)
    system('chmod 777 {}'.format(f2save))


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


def Update_DB_new_subjects_and_SUBJECTS_DIR(NIMB_tmp,
                                            db,
                                            vars_freesurfer,
                                            DEFAULT,
                                            atlas_definitions):
    db = chk_subj_in_SUBJECTS_DIR(NIMB_tmp,
                                    db,
                                    vars_freesurfer,
                                    atlas_definitions)
    db = chk_subjects2fs_file(NIMB_tmp,
                                db,
                                vars_freesurfer,
                                atlas_definitions)
    db = chk_new_subjects_json_file(NIMB_tmp,
                                    db,
                                    vars_freesurfer,
                                    DEFAULT,
                                    atlas_definitions)
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
    return db



def chk_subjects2fs_file(NIMB_tmp, db, vars_freesurfer, atlas_definitions):
    log.info('    NEW_SUBJECTS_DIR checking ...')

    base_name =vars_freesurfer["base_name"] 
    long_name = vars_freesurfer["long_name"]

    ls_SUBJECTS_in_long_dirs_processed = get_ls_subjids_in_long_dirs(db)
    chk = FreeSurferChecker(vars_freesurfer, atlas_definitions)

    f_subj2fs = path.join(NIMB_tmp, 'subjects2fs')
    if path.isfile(f_subj2fs):
        ls_subj2fs = ls_from_subj2fs(NIMB_tmp, f_subj2fs)
        for subjid in ls_subj2fs:
            log.info('    adding '+subjid+' to database')
            _id, ses = get_id_long(subjid, db['LONG_DIRS'], base_name, long_name)
            if not chk.checks_from_runfs('registration', _id):
                db = add_subjid_2_DB(NIMB_tmp, subjid, _id, ses, db, ls_SUBJECTS_in_long_dirs_processed)
        log.info('new subjects were added from the subjects folder')
    return db


def chk_new_subjects_json_file(NIMB_tmp, db, vars_freesurfer, DEFAULT, atlas_definitions):

    def ls_from_subj2fs(NIMB_tmp, f_subj2fs):
        ls_subjids = list()
        lines = list(open(f_subj2fs,'r'))
        for val in lines:
            if len(val)>3:
                ls_subjids.append(val.strip('\r\n'))
        rename(f_subj2fs, path.join(NIMB_tmp,'zdone_subjects2fs'))
        log.info('subjects2fs was read')
        return ls_subjids


    log.info('    new_subjects.json checking ...')

    ls_SUBJECTS_in_long_dirs_processed = get_ls_subjids_in_long_dirs(db)
    chk = FreeSurferChecker(vars_freesurfer, atlas_definitions)
    base_name =vars_freesurfer["base_name"] 
    long_name = vars_freesurfer["long_name"]

    f_new_subjects = path.join(NIMB_tmp, DEFAULT.f_new_subjects_fs)
    if path.isfile(f_new_subjects):
        import json
        with open(f_new_subjects) as jfile:
            new_subjects = json.load(jfile)
        for subjid in new_subjects:
            if not chk.checks_from_runfs('registration', subjid):
                if 'anat' in new_subjects[subjid]:
                    if 't1' in new_subjects[subjid]['anat']:
                        if new_subjects[subjid]['anat']['t1']:
                            _id, ses = get_id_long(subjid, db['LONG_DIRS'], base_name, long_name)
                            db['REGISTRATION'][subjid] = dict()
                            db['REGISTRATION'][subjid]['anat'] = new_subjects[subjid]['anat']
                            log.info('        '+subjid+' added to database from new_subjects.json')
                            db = add_subjid_2_DB(NIMB_tmp, subjid, _id, ses, db, ls_SUBJECTS_in_long_dirs_processed)
                        else:
                            db['PROCESSED']['error_registration'].append(subjid)
                            log.info('ERROR: '+subjid+' was read and but was not added to database')
        rename(f_new_subjects, path.join(NIMB_tmp,'znew_subjects_registered_to_db_'+time.strftime("%Y%m%d_%H%M",time.localtime(time.time()))+'.json'))
        log.info('        new subjects were added from the new_subjects.json file')
    return db


def get_registration_files(subjid, db, nimb_dir, NIMB_tmp, flair_t2_add):
        log.info('    '+subjid+' reading registration files')
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
        return t1_ls_f, flair_ls_f, t2_ls_f


def get_registration_cmd(_id, db, nimb_dir, NIMB_tmp, flair_t2_add):
    t1_ls_f, flair_ls_f, t2_ls_f = get_registration_files(_id, db, nimb_dir, NIMB_tmp, flair_t2_add)
    t1_cmd    = ''.join([' -i '+i for i in t1_ls_f])
    flair_cmd = '{}'.format(''.join([' -FLAIR '+i for i in flair_ls_f])) if flair_ls_f != 'none' else ''
    t2_cmd    = '{}'.format(''.join([' -T2 '   +i for i in t2_ls_f]))    if t2_ls_f    != 'none' else ''
    return f"recon-all{t1_cmd}{flair_cmd}{t2_cmd} -s {_id}"
#        return "recon-all{}".format(''.join([' -i '+i for i in t1_ls_f]))+flair_cmd+t2_cmd+' -s '+_id


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


def chk_subj_in_SUBJECTS_DIR(NIMB_tmp, db, vars_freesurfer, atlas_definitions):
    log.info('    SUBJECTS_DIR checking ...')

    base_name          = vars_freesurfer["base_name"]
    long_name          = vars_freesurfer["long_name"]
    SUBJECTS_DIR       = vars_freesurfer["FS_SUBJECTS_DIR"]
    process_order      = vars_freesurfer["process_order"]

    chk = FreeSurferChecker(vars_freesurfer, atlas_definitions)

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

    def add_new_subjid_to_db(subjid, chk, process_order):
        if not chk.IsRunning_chk(subjid):
            for process in process_order[1:]:
                if not chk.checks_from_runfs(process, subjid):
                    log.info('        '+subjid+' sent for DO '+process)
                    db['DO'][process].append(subjid)
                    break
        else:
            log.info('            IsRunning file present, adding to RUNNING '+process_order[1])
            db['RUNNING'][process_order[1]].append(subjid)

    ls_SUBJECTS = sorted([i for i in listdir(SUBJECTS_DIR) if not chk_if_exclude(i)])
    ls_SUBJECTS_in_long_dirs_processed = get_ls_subjids_in_long_dirs(db)
    ls_SUBJECTS_running = get_subjs_running(db, process_order)

    for subjid in ls_SUBJECTS:
        if subjid not in ls_SUBJECTS_in_long_dirs_processed:
            log.info('    '+subjid+' not in PROCESSED')
            _id, longitud = get_id_long(subjid, db['LONG_DIRS'], base_name, long_name)
            log.info('        adding to database: id: '+_id+', long name: '+longitud)
            if _id == subjid:
                subjid = _id+'_'+longitud
                log.info('   no '+long_name+' in '+_id+' Changing name to: '+subjid)
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
                    add_new_subjid_to_db(subjid, chk, process_order)
    return db


def check_that_all_files_are_accessible(ls):
    for file in ls:
        if not path.exists(file):
            ls.remove(file)
    return ls
