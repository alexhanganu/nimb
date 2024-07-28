#!/bin/python
# 2020.08.25

import os
import time
import json
import logging

from processing.checker import CHECKER
from classification.dcm2bids_helper import is_bids_format

os.environ['TZ'] = 'US/Eastern'
time.tzset()
log = logging.getLogger(__name__)


class AppDBManage:

    def __init__(self,
                vars_local,
                app,
                DEFAULT,
                atlas_definitions):
        self.NIMB_HOME    = vars_local["NIMB_PATHS"]["NIMB_HOME"]
        self.NIMB_tmp     = vars_local["NIMB_PATHS"]["NIMB_tmp"]
        self.ses_abrevs   = vars_local["NIMB_PATHS"]["long_abbrevs"]
        self.chk          = CHECKER(vars_local[app.upper()], app, atlas_definitions)
        self.DEF          = DEFAULT
        self.db_file      = os.path.join(self.NIMB_tmp, f"db_{app}.json")
        log.info(f"        Database file is: {self.db_file}")


    def get_db(self, app, vars_app):
        if os.path.isfile(self.db_file):
            with open(self.db_file) as db_open:
                db = json.load(db_open)
        else:
            db = dict()
            proc_order = vars_app["process_order"]
            if app not in db:
                db[app] = {}
            for action in ['DO','RUNNING',]:
                db[app][action] = {}
                for process in proc_order:
                    db[app][action][process] = []
            db[app]['REGISTRATION'] = {}
            db[app]['RUNNING_JOBS'] = {}
            db[app]['LONG_DIRS'] = {}
            db[app]['LONG_TPS'] = {}
            db[app]['ERROR_QUEUE'] = {}
            db[app]['PROCESSED'] = {'cp2local':[],}
            for process in proc_order:
                db[app]['PROCESSED']['error_'+process] = []
        return db


    def update_db(self, db):
        with open(self.db_file, 'w') as jf:
            json.dump(db, jf, indent=4)
        os.system('chmod 777 {}'.format(self.db_file))


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


    def chk_new_subj(self, db, app, app_vars):
        self.app        = app
        self.app_vars   = app_vars
        self.proc_order = app_vars["process_order"]
        self.base_name  = app_vars["base_name"]

        db = self.json_file_chk(db)
        db = self.SUBJECTS_DIR_chk(db)
        return db


    def json_file_chk(self, db):
        self.f_new_subjs  = self.DEF.app_files[self.app]["new_subjects"]
        f_new_subjects = os.path.join(self.NIMB_tmp, self.f_new_subjs)
        log.info(f'    new_subjects.json checking ...:{f_new_subjects}')

        if os.path.isfile(f_new_subjects):
            with open(f_new_subjects) as jfile:
                new_subjects = json.load(jfile)
            ls_SUBJECTS_in_long_dirs_processed = self.get_ls_subjids_in_long_dirs(db)
            for subjid in new_subjects:
                if not self.chk.chk(subjid, 'registration'):
                    if 'anat' in new_subjects[subjid]:
                        if 't1' in new_subjects[subjid]['anat']:
                            if new_subjects[subjid]['anat']['t1']:
                                bids_format, _id, ses, run_label = is_bids_format(subjid)
                                if not bids_format:
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
            os.rename(f_new_subjects, os.path.join(self.NIMB_tmp, ren_name))
            log.info('        all new subjects were added from '+f_new_subjects)
        return db


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


    def get_id_long(self, subjid, LONG_DIRS):
        print(f'    subject id : {subjid} is NOT BIDS format')
        _id = 'none'
        for key in LONG_DIRS:
            if subjid in LONG_DIRS[key]:
                _id = key
                ses_label = subjid.replace(_id+'_','')
                break
        if self.base_name in subjid:
            subjid = subjid.replace(self.base_name,'').split('.',1)[0]
        if _id == 'none':
            _id = subjid
            ses_label = ''
            for ses in self.ses_abrevs:
                if ses in subjid:
                    ses_label = subjid[subjid.find(ses):]
                    _id = subjid.replace('_'+ses_label,'')
                    break
            if not ses_label:
                ses_label = self.ses_abrevs[0]+str(1).zfill(2)
        return _id, ses_label


    def get_subjs_running(self, db):
        ls_subj_running = []
        for ACTION in ('DO', 'RUNNING',):
            for process in self.proc_order:
                for subjid in db[ACTION][process]:
                    if subjid not in ls_subj_running:
                        ls_subj_running.append(subjid)
        return ls_subj_running



    def add_new_subjid_to_db(self, subjid, db):
        if not self.chk.chk(subjid,  'isrunning'):
            for process in self.proc_order[1:]:
                if not self.chk.chk(subjid, process):
                    log.info('        '+subjid+' sent for DO '+process)
                    db['DO'][process].append(subjid)
                    break
        else:
            log.info('            IsRunning file present, adding to RUNNING '+self.proc_order[1])
            db['RUNNING'][self.proc_order[1]].append(subjid)
        return db


    def SUBJECTS_DIR_chk(self, db):
        log.info('    SUBJECTS_DIR checking ...')
        self.SUBJECTS_DIR = self.app_vars["SUBJECTS_DIR"]
        files_2rm = ['bert', 'V1_average', 'README',
                     'fsaverage', 'fsaverage3', 'fsaverage4',
                     'fsaverage5', 'fsaverage6', 'fsaverage_sym',
                     'sample-001.mgz', 'sample-002.mgz',
                     'lh.EC_average', 'rh.EC_average',
                      'cvs_avg35', 'cvs_avg35_inMNI152']
        subj_2add = [i for i in os.listdir(self.SUBJECTS_DIR) if i not in files_2rm]

        for subjid in sorted(subj_2add):
            if subjid not in self.get_ls_subjids_in_long_dirs(db):
                log.info(f'    {subjid} not in PROCESSED')
                bids_format, _id, ses, run_label = is_bids_format(subjid)
                if not bids_format:
                    _id, ses = self.get_id_long(subjid, db['LONG_DIRS'])
                log.info(f'        adding to database: id: {_id}, long name: {ses}')
                if _id == subjid:
                    subjid = _id+'_'+ses
                    log.info('   no '+ses+' in '+_id+' Changing name to: '+subjid)
                    os.rename(os.path.join(self.SUBJECTS_DIR, _id),
                              os.path.join(self.SUBJECTS_DIR, subjid))
                if _id not in db['LONG_DIRS']:
                    db['LONG_DIRS'][_id] = list()
                if subjid not in db['LONG_DIRS'][_id]:
                    # log.info('        '+subjid+' to LONG_DIRS[\''+_id+'\']')
                    db['LONG_DIRS'][_id].append(subjid)
                if _id not in db['LONG_TPS']:
                    # log.info('    adding '+_id+' to LONG_TPS')
                    db['LONG_TPS'][_id] = list()
                if ses not in db['LONG_TPS'][_id]:
                    # log.info('    adding '+ses+' to LONG_TPS[\''+_id+'\']')
                    db['LONG_TPS'][_id].append(ses)
                if self.base_name not in subjid:
                    if subjid not in self.get_subjs_running(db):
                        db = self.add_new_subjid_to_db(subjid, db)
        return db


    def check_that_all_files_are_accessible(self, ls):
        for file in ls:
            if not os.path.exists(file):
                ls.remove(file)
        return ls
