#!/bin/python
# 2020.08.25

from os import path, listdir, rename, environ, system
import os
import time
import json
import logging
from fs_checker import FreeSurferChecker

environ['TZ'] = 'US/Eastern'
time.tzset()
log = logging.getLogger(__name__)


# process_order, ls_long_abrevs

class DBManage:

    def __init__(self,
                vars_local,
                vars_app,
                DEFAULT,
                atlas_definitions):
        self.NIMB_HOME      = vars_local["NIMB_PATHS"]["NIMB_HOME"]
        self.NIMB_tmp       = vars_local["NIMB_PATHS"]["NIMB_tmp"]
        self.SUBJECTS_DIR   = vars_app["NL_SUBJECTS_DIR"]
        self.chk            = FreeSurferChecker(vars_freesurfer, atlas_definitions)

        db_f_name           = DEFAULT.app_files["nilearn"]["db"]
        self.db_file        = os.path.join(self.NIMB_tmp, db_f_name)
        self.f_new_subjs    = DEFAULT.f_new_subjects_fs


    def get_db(self):
        log.info(f"        Database file is: {self.db_file}")
        if path.isfile(self.db_file):
            with open(self.db_file) as db_open:
                db = json.load(db_open)
        else:
            db = dict()
            for action in ['DO','RUNNING',]:
                db[action] = {}
                for process in self.process_order:
                    db[action][process] = []
            db['REGISTRATION'] = {}
            db['RUNNING_JOBS'] = {}
            db['LONG_DIRS'] = {}
            db['LONG_TPS'] = {}
            db['ERROR_QUEUE'] = {}
            db['PROCESSED'] = {'cp2local':[],}
            for process in self.process_order:
                db['PROCESSED']['error_'+process] = []
        return db


    def Update_DB(self, db):
        with open(self.db_file, 'w') as jf:
            json.dump(db, jf, indent=4)
        system('chmod 777 {}'.format(self.db_file))


    def get_registration_files(self, _id, db, flair_t2_add):
            log.info('    '+_id+' reading registration files')
            t1_ls_f = db['REGISTRATION'][_id]['anat']['t1']
            flair_ls_f = 'none'
            t2_ls_f = 'none'
            if 'flair' in db['REGISTRATION'][_id]['anat'] and flair_t2_add == 1:
                if db['REGISTRATION'][_id]['anat']['flair']:
                    flair_ls_f = db['REGISTRATION'][_id]['anat']['flair']
            if 't2' in db['REGISTRATION'][_id]['anat'] and flair_t2_add == 1:
                if db['REGISTRATION'][_id]['anat']['t2'] and flair_ls_f == 'none':
                    t2_ls_f = db['REGISTRATION'][_id]['anat']['t2']
            return t1_ls_f, flair_ls_f, t2_ls_f


    def get_registration_cmd(self, _id, db, flair_t2_add):
        t1_ls_f, flair_ls_f, t2_ls_f = self.get_registration_files(_id, db, flair_t2_add)
        t1_cmd    = ''.join([' -i '+i for i in t1_ls_f])
        flair_cmd = ''
        t2_cmd    = ''
        if flair_ls_f != 'none':
            flair_cmd = '{}'.format(''.join([' -FLAIR '+i for i in flair_ls_f]))
        if t2_ls_f != 'none':
            t2_cmd = '{}'.format(''.join([' -T2 '   +i for i in t2_ls_f]))
        return f"recon-all{t1_cmd}{flair_cmd}{t2_cmd} -s {_id}"


    def add_subjid_2_DB(self, subjid, _id, ses, db, ls_SUBJECTS_in_long_dirs_processed):
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


    def get_ls_subjids_in_long_dirs(self, db):
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


    def chk_new_subjects_json_file(self, db):
        log.info('    new_subjects.json checking ...')

        ls_SUBJECTS_in_long_dirs_processed = self.get_ls_subjids_in_long_dirs(db)
        f_new_subjects = os.path.join(self.NIMB_tmp, self.f_new_subjs)
        if os.path.isfile(f_new_subjects):
            with open(f_new_subjects) as jfile:
                new_subjects = json.load(jfile)
            for subjid in new_subjects:
                if not self.chk.checks_from_runfs('registration', subjid):
                    if 'anat' in new_subjects[subjid]:
                        if 't1' in new_subjects[subjid]['anat']:
                            if new_subjects[subjid]['anat']['t1']:
                                _id, ses = self.get_id_long(subjid, db['LONG_DIRS'])
                                db['REGISTRATION'][subjid] = dict()
                                db['REGISTRATION'][subjid]['anat'] = new_subjects[subjid]['anat']
                                log.info('        '+subjid+' added to database from '+f_new_subjects)
                                db = self.add_subjid_2_DB(subjid, _id, ses, db, ls_SUBJECTS_in_long_dirs_processed)
                            else:
                                db['PROCESSED']['error_registration'].append(subjid)
                                log.info('ERROR: '+subjid+' was read and but was not added to database')
            time_now = time.strftime("%Y%m%d_%H%M",time.localtime(time.time()))
            ren_name = 'znew_subjects_registered_to_db_'+time_now+'.json'
            rename(f_new_subjects, os.path.join(self.NIMB_tmp, ren_name))
            log.info('        all new subjects were added from '+f_new_subjects)
        return db


    def get_id_long(self, subjid, LONG_DIRS):
            _id = 'none'
            for key in LONG_DIRS:
                if subjid in LONG_DIRS[key]:
                    _id = key
                    longitud = subjid.replace(_id+'_','')
                    break
            if self.base_name in subjid:
                subjid = subjid.replace(self.base_name,'').split('.',1)[0]
            if _id == 'none':
                _id = subjid
                longitud = long_name+str(1)
                for long_name in self.ls_long_abrevs:
                    if long_name in subjid:
                        longitud = subjid[subjid.find(long_name):]
                        _id = subjid.replace('_'+longitud,'')
                        break
            return _id, longitud


    def get_subjs_running(self, db):
        ls_subj_running = []
        for ACTION in ('DO', 'RUNNING',):
            for process in self.process_order:
                for subjid in db[ACTION][process]:
                    if subjid not in ls_subj_running:
                        ls_subj_running.append(subjid)
        return ls_subj_running



    def add_new_subjid_to_db(self, subjid):
        if not self.chk.IsRunning_chk(subjid):
            for process in self.process_order[1:]:
                if not self.chk.checks_from_runfs(process, subjid):
                    log.info('        '+subjid+' sent for DO '+process)
                    db['DO'][process].append(subjid)
                    break
        else:
            log.info('            IsRunning file present, adding to RUNNING '+self.process_order[1])
            db['RUNNING'][self.process_order[1]].append(subjid)


    def chk_subj_in_SUBJECTS_DIR(self, db, vars_freesurfer, atlas_definitions):
        log.info('    SUBJECTS_DIR checking ...')
        ls_SUBJECTS = self.get_ls_subjects_in_fs_subj_dir()
        for subjid in ls_SUBJECTS:
            if subjid not in self.get_ls_subjids_in_long_dirs(db):
                log.info('    '+subjid+' not in PROCESSED')
                _id, longitud = self.get_id_long(subjid, db['LONG_DIRS'])
                log.info('        adding to database: id: '+_id+', long name: '+longitud)
                if _id == subjid:
                    subjid = _id+'_'+longitud
                    log.info('   no '+longitud+' in '+_id+' Changing name to: '+subjid)
                    rename(path.join(self.SUBJECTS_DIR, _id), path.join(self.SUBJECTS_DIR, subjid))
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
                if self.base_name not in subjid:
                    if subjid not in self.get_subjs_running(db):
                        self.add_new_subjid_to_db(subjid)
        return db


    def get_ls_subjects_in_fs_subj_dir(self):
        files_in_SUBJECTS_DIR = ['bert','average','README','sample-00','cvs_avg35']
        ls = sorted([i for i in listdir(self.SUBJECTS_DIR) if i not in files_in_SUBJECTS_DIR])
        return ls


    def check_that_all_files_are_accessible(self, ls):
        for file in ls:
            if not path.exists(file):
                ls.remove(file)
        return ls
