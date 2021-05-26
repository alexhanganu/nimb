#!/bin/python
# 2020.09.10

import os
from os import path, system, chdir, environ, rename, listdir
import time
import shutil
import json

environ['TZ'] = 'US/Eastern'
time.tzset()


def Get_status_for_subjid_in_queue(running_jobs, subjid, scheduler_jobs):
    if subjid in running_jobs:
        job_id = str(running_jobs[subjid])
        if job_id in scheduler_jobs:
           status = scheduler_jobs[job_id][1]
        else:
           status = 'none'
    else:
        running_jobs, status = try_to_infer_jobid(running_jobs, subjid, scheduler_jobs)
        job_id = '0'
    return running_jobs, status, job_id

def try_to_infer_jobid(running_jobs, subjid, scheduler_jobs):
    probable_jobids = [i for i in scheduler_jobs if scheduler_jobs[i][0] in subjid]
    if probable_jobids:
        log.info('            job_id for subject {} inferred, probable jobids: {}'.format(subjid, str(probable_jobids[0])))
        if len(probable_jobids)>1:
            running_jobs[subjid] = 0
        else:
            running_jobs[subjid] = probable_jobids[0]
        return running_jobs, 'PD'
    else:
        return running_jobs, 'none'


def running(process, scheduler_jobs):
    ACTION = 'RUNNING'
    log.info('{} {}'.format(ACTION, process))
    lsr = db[ACTION][process].copy()
    for subjid in lsr:
        db['RUNNING_JOBS'], status, job_id = Get_status_for_subjid_in_queue(db['RUNNING_JOBS'], subjid, scheduler_jobs)
        if status == 'none':
            db[ACTION][process].remove(subjid)
            if subjid in db['RUNNING_JOBS']:
                db['RUNNING_JOBS'].pop(subjid, None)
            if vars_freesurfer["base_name"] in subjid:
                log.info('    reading {}, {} is long or base '.format(process, subjid))
                chk
                if chk.IsRunning_chk(subjid) or not chk.checks_from_runfs('recon', subjid):
                # if fs_checker.chkIsRunning(SUBJECTS_DIR, subjid) or not fs_checker.checks_from_runfs(SUBJECTS_DIR, 'recon', subjid, vars_freesurfer["freesurfer_version"], vars_freesurfer["masks"]):  #2RM
                        log.info('    {}, {} -> ERROR, IsRunning or not all files created'.format(subjid, process))
                        db['ERROR_QUEUE'][subjid] = schedule.get_time_end_of_walltime(process) #str(format(datetime.now()+timedelta(hours=datetime.strptime(Get_walltime(process), '%H:%M:%S').hour), "%Y%m%d_%H%M"))  #2RM
                        db['PROCESSED']['error_recon'].append(subjid)
            else:
                if not chk.IsRunning_chk(subjid) and chk.checks_from_runfs(process, subjid):
                # if not fs_checker.chkIsRunning(SUBJECTS_DIR, subjid) and fs_checker.checks_from_runfs(SUBJECTS_DIR, process, subjid, vars_freesurfer["freesurfer_version"], vars_freesurfer["masks"]):  #2RM
                    if process != process_order[-1]:
                        next_process = process_order[process_order.index(process)+1]
                        if not chk.checks_from_runfs(next_process, subjid):
                        # if not fs_checker.checks_from_runfs(SUBJECTS_DIR, next_process, subjid, vars_freesurfer["freesurfer_version"], vars_freesurfer["masks"]):  #2RM
                            db['DO'][next_process].append(subjid)
                            log.info('    {}, {} {} -> DO {}'.format(subjid, ACTION, process, next_process))
                            if processing_env == 'tmux':
                                schedule.kill_tmux_session(job_id)
                        else:
                            db[ACTION][next_process].append(subjid)
                            log.info('    {}, {} {} -> {} {}'.format(subjid, ACTION, process, ACTION, next_process))
                    else:
                        log.info('    {} processing DONE'.format(subjid))
                else:
                    log.info('    {}, {} -> ERROR; IsRunning, status= {}'.format(subjid, process, status))
                    db['ERROR_QUEUE'][subjid] = schedule.get_time_end_of_walltime(process) #str(format(datetime.now()+timedelta(hours=datetime.strptime(Get_walltime(process), '%H:%M:%S').hour), "%Y%m%d_%H%M")) #2RM
                    db['PROCESSED']['error_'+process].append(subjid)
    db[ACTION][process].sort()
    proc_db.Update_DB(db, NIMB_tmp)



def move_processed_subjects(subject, db_source, new_name):
    file_mrparams = path.join(NIMB_tmp, 'mriparams', '{}_mrparams'.format(subject))
    if path.isfile(file_mrparams):
        shutil.move(file_mrparams, path.join(SUBJECTS_DIR, subject, 'stats'))
    log.info('    {} copying from {}'.format(subject, db_source))
    size_src = sum(f.stat().st_size for f in Path(path.join(SUBJECTS_DIR, subject)).glob('**/*') if f.is_file())
    shutil.copytree(path.join(SUBJECTS_DIR, subject), path.join(vars_nimb["NIMB_PROCESSED_FS"], subject))
    size_dst = sum(f.stat().st_size for f in Path(path.join(vars_nimb["NIMB_PROCESSED_FS"], subject)).glob('**/*') if f.is_file())
    if size_src == size_dst:
        db['PROCESSED'][db_source].remove(subject)
        proc_db.Update_DB(db, NIMB_tmp)
        shutil.rmtree(path.join(SUBJECTS_DIR, subject))
        if vars_processing["archive_processed"] == 1:
            log.info('        archiving ...')
            # chdir(vars_nimb["NIMB_PROCESSED_FS"])
            # system('zip -r -q -m {}.zip {}'.format(subject, subject))
            cd_cmd = 'cd {}'.format(vars_nimb["NIMB_PROCESSED_FS"])
            cmd = 'zip -r -q -m {}.zip {}'.format(subject, subject)
            schedule.submit_4_processing(cmd,'nimb','archiving', cd_cmd,
                                        activate_fs = False,
                                        python_load = False)
        if new_name:
            log.info('        renaming {} to {}, moving to {}'.format(subject, new_name, vars_nimb["NIMB_PROCESSED_FS_error"]))
            shutil.move(path.join(vars_nimb["NIMB_PROCESSED_FS"], '{}.zip'.format(subject)),
                        path.join(vars_nimb["NIMB_PROCESSED_FS_error"], '{}.zip'.format(new_name)))
    else:
        log.info('        ERROR in moving, not moved correctly {} {}'.format(str(size_src), str(size_dst)))
        shutil.rmtree(path.join(vars_nimb["NIMB_PROCESSED_FS"], subject))


def loop_run():
    proc_db.Update_DB(db, NIMB_tmp)
    # scheduler_jobs = get_jobs_status(vars_local["USER"]["user"]) #2RM
    scheduler_jobs = schedule.get_jobs_status(vars_local["USER"]["user"], db['RUNNING_JOBS'])

    for process in process_order[::-1]:
        if len(db['RUNNING'][process])>0:
            running(process, scheduler_jobs)
        if len(db['DO'][process])>0:
            do(process)

    for process in process_order:
        check_error(scheduler_jobs, process)

    log.info('CHECKING subjects')
    ls_long_dirs = list()
    for key in db['LONG_DIRS']:
        ls_long_dirs.append(key)

    for _id in ls_long_dirs:
        long_check_groups(_id)


    log.info('MOVING the processed')
    for subject in db['PROCESSED']['cp2local'][::-1]:
        move_processed_subjects(subject, 'cp2local', '')


def check_active_tasks(db):
    active_subjects = 0
    error = 0
    for process in process_order:
        error = error + len(db['PROCESSED']['error_'+process])
    for _id in db['LONG_DIRS']:
        active_subjects = active_subjects + len(db['LONG_DIRS'][_id])
    active_subjects = active_subjects+len(db['PROCESSED']['cp2local'])
    log.info('\n                 '+str(active_subjects)+'\n                 '+str(error)+' error')
    return active_subjects



def  len_Running():
    return len([i for process in db['RUNNING'].values() for i in process])


def Count_TimeSleep():
    time2sleep = 600 # 10 minutes
    len_all_running_jobs = len_Running()
    log.info('running: '+str(len_all_running_jobs)+' max: '+str(vars_processing["max_nr_running_batches"]))
    if len_all_running_jobs >= vars_processing["max_nr_running_batches"]:
        time2sleep = 1800 # 30 minutes
    return time2sleep


def Update_running(NIMB_tmp, cmd):
    file = path.join(NIMB_tmp, 'processing_running_')
    if cmd == 1:
        if path.isfile('{}0'.format(file)):
            rename('{}0'.format(file), '{}1'.format(file))
        else:
            open('{}1'.format(file), 'w').close()
    else:
        if path.isfile('{}1'.format(file)):
            rename('{}1'.format(file), '{}0'.format(file))


def run_processing(all_vars, logger):

    #defining working variables
    project     = all_vars.params.project
    vars_local  = all_vars.location_vars['local']
    log         = logger #logging.getLogger(__name__)

    # defining files and paths
    materials_dir_pt = all_vars.projects[project]["materials_DIR"][1]

    # global db, schedule, log, chk, vars_local, vars_freesurfer, fs_ver, vars_processing, vars_nimb, NIMB_HOME, NIMB_tmp, SUBJECTS_DIR, max_walltime, process_order, processing_env

#     vars_freesurfer = vars_local["FREESURFER"]
#     vars_processing = vars_local["PROCESSING"]
#     vars_nimb       = vars_local["NIMB_PATHS"]
#     processing_env  = vars_local["PROCESSING"]["processing_env"]

#     NIMB_HOME       = vars_nimb["NIMB_HOME"]
#     NIMB_tmp        = vars_nimb["NIMB_tmp"]
#     max_walltime    = vars_processing["max_walltime"]
#     SUBJECTS_DIR    = vars_freesurfer["FS_SUBJECTS_DIR"]
#     fs_ver          = FreeSurferVersion(vars_freesurfer["freesurfer_version"]).fs_ver()
#     chk             = FreeSurferChecker(vars_freesurfer)
#     schedule        = Scheduler(vars_local)

    t0           = time.time()
    time_elapsed = 0
    count_run    = 0

    log.info('    processing pipeline started')
    Update_running(NIMB_tmp, 1)

    log.info('    processing database reading')
    DBc = DB(all_vars)
    db = DBc.get_db()
    print(db)

    log.info('    NEW SUBJECTS searching:')    
    db = DBc.Update_DB_new_subjects(db)
    print(db)
#     proc_db.Update_DB(db, NIMB_tmp)
#     active_subjects = check_active_tasks(db)

#     # extracting 40 minutes from the maximum time for the batch to run
#     # since it is expected that less then 35 minutes will be required for the pipeline to perform all the steps
#     # while the batch is running, and start new batch
#     max_batch_running = time.strftime('%H:%M:%S',time.localtime(time.mktime(time.strptime(vars_processing["batch_walltime"],"%H:%M:%S")) - 2400))

#     while active_subjects >0 and time.strftime("%H:%M:%S",time.gmtime(time_elapsed)) < max_batch_running:
#         count_run += 1
#         log.info('restarting run, '+str(count_run))
#         log.info('elapsed time: '+time.strftime("%H:%M",time.gmtime(time_elapsed))+' max walltime: '+vars_processing["batch_walltime"][:-6])
#         if count_run % 5 == 0:
#             log.info('NEW SUBJECTS searching:')
#             db = proc_db.Update_DB_new_subjects_and_SUBJECTS_DIR(NIMB_tmp,
#                                                             db,
#                                                             vars_freesurfer,
#                                                             DEFAULT)
#             proc_db.Update_DB(db, NIMB_tmp)
#         loop_run()

#         time_to_sleep = Count_TimeSleep()
#         log.info('\n\nWAITING. \nNext run at: '+str(time.strftime("%H:%M",time.localtime(time.time()+time_to_sleep))))

#         time_elapsed = time.time() - t0
# #        if time.strftime("%H:%M:%S",time.gmtime(time_elapsed+time_to_sleep)) < max_batch_running:
# #                  batch gets closed by the scheduler, trying to calculate time left until batch is finished,
# #                  line if was creating an infinitie loop, without the time.sleep, might have been related to missing :%S in strpftime

#         time.sleep(time_to_sleep)

#         time_elapsed = time.time() - t0
#         active_subjects = check_active_tasks(db)

#     if active_subjects == 0:
#         Update_running(NIMB_tmp, 0)
#         log.info('ALL TASKS FINISHED')
#     else:
#         python_run = self.local_vars["PROCESSING"]["python3_run_cmd"]
#         NIMB_HOME  = self.local_vars["NIMB_PATHS"]["NIMB_HOME"]
#         cd_cmd     = f'cd {os.path.join(NIMB_HOME, "processing")}'
#         cmd        = f'{python_run} processing_run.py -project {project}'
#         log.info(f'    Sending new processing batch to scheduler with cd_cmd: {cd_cmd} ')
#         schedule.submit_4_processing(cmd, 'nimb_processing','run', cd_cmd)



class DB:

    def __init__(self, all_vars):
        self.log      = logger #logging.getLogger(__name__)
        self.project  = all_vars.params.project
        vars_nimb     = all_vars.location_vars['local']['NIMB_PATHS']
        self.NIMB_tmp = vars_nimb['NIMB_tmp']


    def get_db(self):
        '''
        PROJECTS  : {'project_name: [subj1, subj2]'}
        PROCESS_FS: {'subj1': 'local', 'subj2': 'remote1', 'subj3': 'remote2'}
        PROCESS_NL: {'subj1': 'local', 'subj2': 'remote1', 'subj3': 'remote2'}
        PROCESS_DP: {'subj1': 'local', 'subj2': 'remote1', 'subj3': 'remote2'}
        PROCESSED : {"cp2storage": [], "error":[]}
        '''

        df_f_name = 'processing_db.json'
        db_f = os.path.join(self.NIMB_tmp, df_f_name)

        self.log.info(f"Database file: {db_f}")
        if os.path.isfile(db_f):
            with open(db_f) as db_f_open:
                db = json.load(db_f_open)
        else:
            db = dict()
            db['PROJECTS'] = {}
            db['PROCESSED'] = {"cp2storage": [], "error":[]}
            apps = ('FS', 'NL', 'DP')
            for app in apps:
                db[f'PROCESS_{app}'] = {}
        return db


    def get_ids(self, all_vars):
        '''extract list of subjects to process'''
        distrib_hlp      = DistributionHelper(all_vars)
        vars_local       = all_vars.location_vars['local']
        f_ids_name       = vars_local["NIMB_PATHS"]['file_ids_processed']
        new_subjects_dir = vars_local["NIMB_PATHS"]["NIMB_NEW_SUBJECTS"]
        path_stats_dir   = all_vars.projects[self.project]["STATS_PATHS"]["STATS_HOME"]

        f_ids_abspath    = os.path.join(path_stats_dir, f_ids_name)
        f_classif_in_src = os.path.join(new_subjects_dir, DEFAULT.f_nimb_classified)
        self._ids_all         = dict()
        self._ids_classified  = dict()

        if distrib_hlp.get_files_for_stats(path_stats_dir, [f_ids_name,]):
            self._ids_all        = load_json(f_ids_abspath)
        if os.path.exists(f_classif_in_src):
            self._ids_classified = load_json(f_classif_in_src)
        else:
            print(f'    file with nimb classified ids is MISSING in: {new_subjects_dir}')


    def Update_DB_new_subjects(self, db):
        if self.project not in db['PROJECTS']:
            self.get_ids(all_vars)
            db['PROJECTS'][self.project] = list(self._ids_all.keys())
            self.populate_db()


    def populate_db(self):
        for bids_id in self._ids_all:
            if self._ids_all[_bids_id][get_keys_processed('src')]:
                self.add_2db(bids_id, app)


    def add_2db(self, bids_id, app):
        ses = bids_id[-6:]
        _id = bids_id.replace(f'_{ses}','')
        print(_id, ses)
        if not self._ids_all[bids_id[get_keys_processed('fs')]]:
            if 'anat' in self._ids_classified[_id][ses]:
                print('    ready to add to FS processing')

        if not self._ids_all[bids_id[get_keys_processed('nilearn')]]:
            if 'anat' in self._ids_classified[_id][ses] and
                'func' in self._ids_classified[_id][ses]:
                print('    ready to add to NILEARN processing')

        if not self._ids_all[bids_id[get_keys_processed('dipy')]]:
            if 'anat' in self._ids_classified[_id][ses] and
                'dwi' in self._ids_classified[_id][ses]:
                print('    ready to add to DIPY processing')


    def get_registration_files(self, subjid, db, nimb_dir, NIMB_tmp, flair_t2_add):
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
            self.log.info('        from db[\'REGISTRATION\']')
            return t1_ls_f, flair_ls_f, t2_ls_f


    # def Update_DB(self, db, NIMB_tmp):
    #     f2save = path.join(NIMB_tmp, 'db.json')
    #     with open(f2save, 'w') as jf:
    #         json.dump(db, jf, indent=4)
    #     system('chmod 777 {}'.format(f2save))


    # def add_subjid_2_DB(self, NIMB_tmp, subjid, _id, ses, db, ls_SUBJECTS_in_long_dirs_processed):
    #     if subjid not in ls_SUBJECTS_in_long_dirs_processed:
    #         if _id not in db['LONG_DIRS']:
    #             db['LONG_DIRS'][_id] = []
    #             db['LONG_TPS'][_id] = []
    #         db['LONG_TPS'][_id].append(ses)
    #         db['LONG_DIRS'][_id].append(subjid)
    #         db['DO']['registration'].append(subjid)
    #     else:
    #         self.log.info('ERROR: '+subjid+' in database! new one cannot be registered')
    #     return db



    # def chk_subjects2fs_file(self, NIMB_tmp, db, vars_freesurfer):
    #     self.log.info('    NEW_SUBJECTS_DIR checking ...')

    #     base_name =vars_freesurfer["base_name"] 
    #     long_name = vars_freesurfer["long_name"]

    #     ls_SUBJECTS_in_long_dirs_processed = get_ls_subjids_in_long_dirs(db)
    #     from fs_checker import FreeSurferChecker
    #     chk = FreeSurferChecker(vars_freesurfer)

    #     f_subj2fs = path.join(NIMB_tmp, 'subjects2fs')
    #     if path.isfile(f_subj2fs):
    #         ls_subj2fs = ls_from_subj2fs(NIMB_tmp, f_subj2fs)
    #         for subjid in ls_subj2fs:
    #             self.log.info('    adding '+subjid+' to database')
    #             _id, ses = get_id_long(subjid, db['LONG_DIRS'], base_name, long_name)
    #             if not chk.checks_from_runfs('registration', _id):
    #                 db = add_subjid_2_DB(NIMB_tmp, subjid, _id, ses, db, ls_SUBJECTS_in_long_dirs_processed)
    #         self.log.info('new subjects were added from the subjects folder')
    #     return db


    # def chk_new_subjects_json_file(self, NIMB_tmp, db, vars_freesurfer, DEFAULT):

    #     def ls_from_subj2fs(NIMB_tmp, f_subj2fs):
    #         ls_subjids = list()
    #         lines = list(open(f_subj2fs,'r'))
    #         for val in lines:
    #             if len(val)>3:
    #                 ls_subjids.append(val.strip('\r\n'))
    #         rename(f_subj2fs, path.join(NIMB_tmp,'zdone_subjects2fs'))
    #         self.log.info('subjects2fs was read')
    #         return ls_subjids


    #     self.log.info('    new_subjects.json checking ...')

    #     ls_SUBJECTS_in_long_dirs_processed = get_ls_subjids_in_long_dirs(db)
    #     from fs_checker import FreeSurferChecker
    #     chk = FreeSurferChecker(vars_freesurfer)

    #     f_new_subjects = path.join(NIMB_tmp, DEFAULT.f_subjects2proc)#"new_subjects.json")
    #     if path.isfile(f_new_subjects):
    #         import json
    #         with open(f_new_subjects) as jfile:
    #             data = json.load(jfile)
    #         for _id in data:
    #             if not chk.checks_from_runfs('registration', _id):
    #                 for ses in data[_id]:
    #                     if 'anat' in data[_id][ses]:
    #                         if 't1' in data[_id][ses]['anat']:
    #                             if data[_id][ses]['anat']['t1']:
    #                                 subjid = _id+'_'+ses
    #                                 db['REGISTRATION'][subjid] = dict()
    #                                 db['REGISTRATION'][subjid]['anat'] = data[_id][ses]['anat']
    #                                 log.info('        '+subjid+' added to database from new_subjects.json')
    #                                 db = add_subjid_2_DB(NIMB_tmp, subjid, _id, ses, db, ls_SUBJECTS_in_long_dirs_processed)
    #                             else:
    #                                 db['PROCESSED']['error_registration'].append(subjid)
    #                                 log.info('ERROR: '+_id+' was read and but was not added to database')
    #         rename(f_new_subjects, path.join(NIMB_tmp,'znew_subjects_registered_to_db_'+time.strftime("%Y%m%d_%H%M",time.localtime(time.time()))+'.json'))
    #         self.log.info('        new subjects were added from the new_subjects.json file')
    #     return db


    # def get_id_long(self, subjid, LONG_DIRS, base_name, long_name):
    #         _id = 'none'
    #         for key in LONG_DIRS:
    #             if subjid in LONG_DIRS[key]:
    #                 _id = key
    #                 longitud = subjid.replace(_id+'_','')
    #                 break
    #         if base_name in subjid:
    #             subjid = subjid.replace(base_name,'').split('.',1)[0]
    #         if _id == 'none':
    #             _id = subjid
    #             if long_name in subjid:
    #                 longitud = subjid[subjid.find(long_name):]
    #                 _id = subjid.replace('_'+longitud,'')
    #             else:
    #                 longitud = long_name+str(1)
    #         return _id, longitud


    # def chk_subj_in_SUBJECTS_DIR(self, NIMB_tmp, db, vars_freesurfer):
    #     self.log.info('    SUBJECTS_DIR checking ...')

    #     base_name          = vars_freesurfer["base_name"]
    #     long_name          = vars_freesurfer["long_name"]
    #     SUBJECTS_DIR       = vars_freesurfer["FS_SUBJECTS_DIR"]
    #     process_order      = vars_freesurfer["process_order"]

    #     from fs_checker import FreeSurferChecker
    #     chk = FreeSurferChecker(vars_freesurfer)

    #     def chk_if_exclude(subjid):
    #         exclude = False
    #         ls_2_exclude = ['bert','average','README','sample-00','cvs_avg35']
    #         for value in ls_2_exclude:
    #             if value in subjid:
    #                 exclude = True
    #                 break
    #         return exclude

    #     def get_subjs_running(self, db, process_order):
    #         ls_subj_running = []
    #         for ACTION in ('DO', 'RUNNING',):
    #             for process in process_order:
    #                 for subjid in db[ACTION][process]:
    #                     if subjid not in ls_subj_running:
    #                         ls_subj_running.append(subjid)
    #         return ls_subj_running

    #     def add_new_subjid_to_db(self, subjid, chk, process_order):
    #         if not chk.IsRunning_chk(subjid):
    #             for process in process_order[1:]:
    #                 if not chk.checks_from_runfs(process, subjid):
    #                     self.log.info('        '+subjid+' sent for DO '+process)
    #                     db['DO'][process].append(subjid)
    #                     break
    #         else:
    #             self.log.info('            IsRunning file present, adding to RUNNING '+process_order[1])
    #             db['RUNNING'][process_order[1]].append(subjid)

    #     ls_SUBJECTS = sorted([i for i in listdir(SUBJECTS_DIR) if not chk_if_exclude(i)])
    #     ls_SUBJECTS_in_long_dirs_processed = get_ls_subjids_in_long_dirs(db)
    #     ls_SUBJECTS_running = get_subjs_running(db, process_order)

    #     for subjid in ls_SUBJECTS:
    #         if subjid not in ls_SUBJECTS_in_long_dirs_processed:
    #             self.log.info('    '+subjid+' not in PROCESSED')
    #             _id, longitud = get_id_long(subjid, db['LONG_DIRS'], base_name, long_name)
    #             self.log.info('        adding to database: id: '+_id+', long name: '+longitud)
    #             if _id == subjid:
    #                 subjid = _id+'_'+longitud
    #                 self.log.info('   no '+long_name+' in '+_id+' Changing name to: '+subjid)
    #                 rename(path.join(SUBJECTS_DIR,_id), path.join(SUBJECTS_DIR,subjid))
    #             if _id not in db['LONG_DIRS']:
    #                 db['LONG_DIRS'][_id] = list()
    #             if _id in db['LONG_DIRS']:
    #                 if subjid not in db['LONG_DIRS'][_id]:
    #                     # log.info('        '+subjid+' to LONG_DIRS[\''+_id+'\']')
    #                     db['LONG_DIRS'][_id].append(subjid)
    #             if _id not in db['LONG_TPS']:
    #                 # log.info('    adding '+_id+' to LONG_TPS')
    #                 db['LONG_TPS'][_id] = list()
    #             if _id in db['LONG_TPS']:
    #                 if longitud not in db['LONG_TPS'][_id]:
    #                     # log.info('    adding '+longitud+' to LONG_TPS[\''+_id+'\']')
    #                     db['LONG_TPS'][_id].append(longitud)
    #             if base_name not in subjid:
    #                 if subjid not in ls_SUBJECTS_running:
    #                     add_new_subjid_to_db(subjid, chk, process_order)
    #     return db


    def check_that_all_files_are_accessible(self, ls):
        for file in ls:
            if not path.exists(file):
                ls.remove(file)
        return ls



def get_parameters(projects):
    """get parameters for nimb"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-project", required=False,
        default=projects[0],
        choices = projects,
        help="names of projects located in credentials_path.py/nimb/projects.json -> PROJECTS",
    )

    params = parser.parse_args()
    return params


if __name__ == "__main__":


    try:
        from pathlib import Path
    except ImportError as e:
        print('please install pathlib')
        sys.exit(e)
    import argparse
    import sys
    import logging

    top = Path(__file__).resolve().parents[1]
    sys.path.append(str(top))

    from setup.get_vars import Get_Vars
    from distribution.distribution_helper import  DistributionHelper
    from distribution.logger import Log
    from distribution.distribution_definitions import DEFAULT, get_keys_processed
    from distribution.utilities import load_json, save_json, makedir_ifnot_exist
    from processing import processing_db as proc_db
    from processing.schedule_helper import Scheduler, get_jobs_status
    from stats.db_processing import Table

    project_ids = Get_Vars().get_projects_ids()
    params      = get_parameters(project_ids)
    all_vars    = Get_Vars(params)

    NIMB_tmp    = all_vars.location_vars['local']['NIMB_PATHS']['NIMB_tmp']
    fs_version  = all_vars.location_vars['local']['FREESURFER']['freesurfer_version']
    logger      = Log(NIMB_tmp, fs_version).logger
    run_processing(all_vars, logger)



