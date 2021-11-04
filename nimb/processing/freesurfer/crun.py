#!/bin/python
# 2020.09.10

from os import path, system, chdir, environ, rename
from pathlib import Path
import time
import shutil
import logging
import cdb, fs_err_helper, fs_checker
from fs_checker import FreeSurferChecker
from fs_definitions import FreeSurferVersion, process_order

environ['TZ'] = 'US/Eastern'
time.tzset()

class get_cmd():

    def __init__(self, process, _id, id_base = '', ls_tps = []):
        if process == 'registration':
            self.cmd = self.registration(_id)
        if process == 'recbase':
            self.cmd = "recon-all -base {0}{1} -all".format(_id, ''.join([' -tp '+i for i in ls_tps]))
        if process == 'reclong':
            self.cmd = "recon-all -long {0} {1} -all".format(_id, id_base)
        if process == 'recon':
            self.cmd = "recon-all -all -s {}".format(_id)
        if process == 'autorecon1':
            self.cmd = "recon-all -autorecon1 -s {}".format(_id)
        if process == 'autorecon2':
            self.cmd = "recon-all -autorecon2 -s {}".format(_id)
        if process == 'autorecon3':
            self.cmd = "recon-all -autorecon3 -s {}".format(_id)
        if process == 'qcache':
            self.cmd = "recon-all -qcache -s {}".format(_id)
        if process == 'brstem':
            self.cmd = 'segmentBS.sh {}'.format(_id) if fs_ver > '6' else 'recon-all -s {} -brainstem-structures'.format(_id)
        if process == 'hip':
            self.cmd = 'segmentHA_T1.sh {}'.format(_id) if fs_ver > '6' else 'recon-all -s {} -hippocampal-subfields-T1'.format(_id)
        if process == 'tha':
            self.cmd = "segmentThalamicNuclei.sh {}".format(_id)
        if process == 'hypotha':
            self.cmd = "mri_segment_hypothalamic_subunits --s {}".format(_id)
        if process == 'masks':
            self.cmd = "cd {}\npython run_masks.py {}".format(path.join(NIMB_HOME, 'processing', 'freesurfer'), _id)

    def registration(self, _id):
        t1_ls_f, flair_ls_f, t2_ls_f = cdb.get_registration_files(_id, db, NIMB_HOME, NIMB_tmp, vars_freesurfer["flair_t2_add"])
        t1_cmd    = ''.join([' -i '+i for i in t1_ls_f])
        flair_cmd = '{}'.format(''.join([' -FLAIR '+i for i in flair_ls_f])) if flair_ls_f != 'none' else ''
        t2_cmd    = '{}'.format(''.join([' -T2 '   +i for i in t2_ls_f]))    if t2_ls_f    != 'none' else ''
        return "recon-all{}{}{} -s {}".format(t1_cmd, flair_cmd, t2_cmd, _id)
#        return "recon-all{}".format(''.join([' -i '+i for i in t1_ls_f]))+flair_cmd+t2_cmd+' -s '+_id

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
    cdb.Update_DB(db, NIMB_tmp)


def do(process):
    ACTION = 'DO'
    log.info('{} {}'.format(ACTION, process))

    lsd = db[ACTION][process].copy()

    for subjid in lsd:
        if len_Running()<= vars_processing["max_nr_running_batches"]:
            db[ACTION][process].remove(subjid)
            cmd = get_cmd(process, subjid).cmd
            job_id = schedule.submit_4_processing(cmd, subjid, process)
            db['RUNNING_JOBS'][subjid] = job_id
            db['RUNNING'][process].append(subjid)
            try:
                log.info('            {} submited id: {}'.format(subjid, str(job_id)))
            except Exception as e:
                log.info('        {} err in do: '.format(subjid, str(e)))
    db[ACTION][process].sort()
    cdb.Update_DB(db, NIMB_tmp)


def check_error(scheduler_jobs, process):
    log.info('ERROR checking {}'.format(process))

    if db['PROCESSED']['error_'+process]:
            lserr = db['PROCESSED']['error_'+process].copy()
            for subjid in lserr:
                log.info('    {}'.format(subjid))
                if subjid not in db["ERROR_QUEUE"] and path.exists(path.join(SUBJECTS_DIR, subjid)): #path.exists was added due to moving the subjects too early; requires adjustment
                    chk.IsRunning_rm(subjid)
                    # fs_checker.IsRunning_rm(SUBJECTS_DIR, subjid)
                    log.info('        checking the recon-all-status.log for error for: {}'.format(process))
                    fs_err_helper.chkreconf_if_without_error(NIMB_tmp, subjid, SUBJECTS_DIR)
                    log.info('        checking if all files were created for: {}'.format(process))
                    if not chk.checks_from_runfs(process, subjid):
                    # if not fs_checker.checks_from_runfs(SUBJECTS_DIR, process, subjid, vars_freesurfer["freesurfer_version"], vars_freesurfer["masks"]):
                            log.info('            some files were not created and recon-all-status has errors.')
                            fs_error = fs_err_helper.fs_find_error(subjid, SUBJECTS_DIR, NIMB_tmp, process, fs_ver)
                            solved = False
                            if fs_error:
                                solve = fs_err_helper.solve_error(subjid, fs_error, SUBJECTS_DIR, NIMB_tmp)
                                if solve == 'continue':
                                    solved = True
                                    db['PROCESSED']['error_'+process].remove(subjid)
                                    db['DO'][process].append(subjid)
                                    log.info('        moving from error_{} to DO {}'.format(process, process))
                                elif solve == 'repeat_reg':
                                    if subjid in db['REGISTRATION']:
                                        solved = True
                                        db['REGISTRATION'][subjid]['anat']['t1'] = db['REGISTRATION'][subjid]['anat']['t1'][:1]
                                        if 'flair' in db['REGISTRATION'][subjid]['anat']:
                                                db['REGISTRATION'][subjid]['anat'].pop('flair', None)
                                        if 't2' in db['REGISTRATION'][subjid]['anat']:
                                                db['REGISTRATION'][subjid]['anat'].pop('t2', None)
                                        db['PROCESSED']['error_'+process].remove(subjid)
                                        db['DO']["registration"].append(subjid)
                                        log.info('              removing {} from {}'.format(subjid, SUBJECTS_DIR))
                                        system('rm -r '+path.join(SUBJECTS_DIR, subjid))
                                        log.info('        moving from error_{} to RUNNING registration'.format(process))
                                    else:
                                        new_name = 'err_noreg_{}'.format(subjid)
                                        log.info('            solved: {} but subjid is missing from db[REGISTRATION]'.format(solve))
                                else:
                                    new_name = 'err_{}_{}'.format(fs_error, subjid)
                                    log.info('            not solved')
                            else:
                                new_name = 'err_{}_{}'.format(process, subjid)
                            if not solved:
                                log.info('            Excluding {} from pipeline'.format(subjid))
                                _id, _ = cdb.get_id_long(subjid, db['LONG_DIRS'], vars_freesurfer["base_name"], vars_freesurfer["long_name"])
                                if _id != 'none':
                                    try:
                                        db['LONG_DIRS'][_id].remove(subjid)
                                        db['LONG_TPS'][_id].remove(subjid.replace(_id+'_',''))
                                        if len(db['LONG_DIRS'][_id])==0:
                                            db['LONG_DIRS'].pop(_id, None)
                                            db['LONG_TPS'].pop(_id, None)
                                        if subjid in db['REGISTRATION']:
                                            db['REGISTRATION'].pop(subjid, None)
                                        else:
                                            log.info('        missing from db[REGISTRATION]')
                                    except Exception as e:
                                        log.info('        ERROR, id not found in LONG_DIRS; {}'.format(str(e)))
                                else:
                                    log.info('        ERROR, {} is absent from LONG_DIRS'.format(subjid))
                                move_processed_subjects(subjid, 'error_'+process, new_name)
                    else:
                            log.info('            all files were created for process: {}'.format(process))
                            db['PROCESSED']['error_'+process].remove(subjid)
                            db['RUNNING'][process].append(subjid)
                            log.info('        moving from error_{} to RUNNING {}'.format(process, process))
                else:
                    if subjid in db["ERROR_QUEUE"]:
                        db['RUNNING_JOBS'], status, job_id = Get_status_for_subjid_in_queue(db['RUNNING_JOBS'], subjid, scheduler_jobs)
                        log.info('     waiting until: {}'.format(db['ERROR_QUEUE'][subjid]))
                        if status != 'none' and subjid in db['RUNNING_JOBS']:
                            log.info('     status is: {}, error_{}-> RUNNING {}'.format(status, process, process))
                            db['ERROR_QUEUE'].pop(subjid, None)
                            db['PROCESSED']['error_'+process].remove(subjid)
                            db['RUNNING'][process].append(subjid)
                        elif not chk.IsRunning_chk(subjid) or db['ERROR_QUEUE'][subjid] < schedule.get_time_end_of_walltime('now'): # str(format(datetime.now(), "%Y%m%d_%H%M")): #2RM
                        # elif not fs_checker.chkIsRunning(SUBJECTS_DIR, subjid) or db['ERROR_QUEUE'][subjid] < str(format(datetime.now(), "%Y%m%d_%H%M")): #2RM
                            log.info('    removing from ERROR_QUEUE')
                            db['ERROR_QUEUE'].pop(subjid, None)
                    else:
                        log.info('    not in SUBJECTS_DIR')
                        db['PROCESSED']['error_'+process].remove(subjid)
                db['PROCESSED']['error_'+process].sort()
                cdb.Update_DB(db, NIMB_tmp)



def long_check_groups(_id):
    ls = db['LONG_DIRS'][_id]
    LONG_TPS = db['LONG_TPS'][_id]
    if vars_freesurfer["DO_LONG"] == 1 and len(LONG_TPS)>1:
        All_cross_ids_done = list()
        for ses in LONG_TPS:
            if _id+ses in ls and chk.checks_from_runfs(process_order[-1], _id+ses):
            # if _id+ses in ls and fs_checker.checks_from_runfs(SUBJECTS_DIR, process_order[-1], _id+ses, vars_freesurfer["freesurfer_version"], vars_freesurfer["masks"]): #2RM
                All_cross_ids_done.append(_id+ses)

        if len(All_cross_ids_done) == len(LONG_TPS):
            base_f = _id+vars_freesurfer["base_name"]
            if base_f in ls:
                if base_f not in db['RUNNING']['recon'] and base_f not in db['PROCESSED']['error_recon'] and not chk.IsRunning_chk(base_f):
                # if base_f not in db['RUNNING']['recon'] and base_f not in db['PROCESSED']['error_recon'] and not fs_checker.chkIsRunning(SUBJECTS_DIR, base_f): #2RM
                    if chk.checks_from_runfs('recon', base_f):
                    # if fs_checker.checks_from_runfs(SUBJECTS_DIR, 'recon', base_f, vars_freesurfer["freesurfer_version"], vars_freesurfer["masks"]): #2RM
                        All_long_ids_done = list()
                        for ses in LONG_TPS:
                            long_f = _id+ses+'.long.'+_id+vars_freesurfer["base_name"]
                            if long_f not in ls:
                                cmd = get_cmd('reclong', _id+ses, id_base = _id+vars_freesurfer["base_name"]).cmd
                                job_id = schedule.submit_4_processing(cmd, _id+ses, 'reclong')
                                db['RUNNING_JOBS'][long_f] = job_id
                                db['RUNNING']['recon'].append(long_f)
                                db['LONG_DIRS'][_id].append(long_f)
                            elif chk.checks_from_runfs('registration', long_f):
                            # elif fs_checker.checks_from_runfs(SUBJECTS_DIR, 'registration',long_f, vars_freesurfer["freesurfer_version"], vars_freesurfer["masks"]): #2RM
                                if chk.checks_from_runfs('recon', long_f):
                                # if fs_checker.checks_from_runfs(SUBJECTS_DIR, 'recon', long_f, vars_freesurfer["freesurfer_version"], vars_freesurfer["masks"]): #2RM
                                    All_long_ids_done.append(long_f)
                                else:
                                    log.info(long_f+' moving to error_recon')
                                    db['ERROR_QUEUE'][subjid] = schedule.get_time_end_of_walltime(process) #str(format(datetime.now()+timedelta(hours=datetime.strptime(Get_walltime(process), '%H:%M:%S').hour), "%Y%m%d_%H%M")) #2RM
                                    db['PROCESSED']['error_recon'].append(long_f)
                            else:
                                log.info(long_f+' moving to error_recon')
                                db['ERROR_QUEUE'][subjid] = schedule.get_time_end_of_walltime(process) #str(format(datetime.now()+timedelta(hours=datetime.strptime(Get_walltime(process), '%H:%M:%S').hour), "%Y%m%d_%H%M")) #2RM
                                db['PROCESSED']['error_recon'].append(long_f)

                        if len(All_long_ids_done) == len(LONG_TPS):
                            log.info(_id+' moving to cp2local')
                            for subjid in ls:
                                log.info('moving '+subjid+' cp2local from LONG')
                                db['PROCESSED']['cp2local'].append(subjid)
                            db['LONG_DIRS'].pop(_id, None)
                            db['LONG_TPS'].pop(_id, None)
                            if subjid in db['REGISTRATION']:
                                db['REGISTRATION'].pop(subjid, None)
                            if subjid in db['RUNNING_JOBS']:
                                db['RUNNING_JOBS'].pop(subjid, None)
                            else:
                                log.info('        missing from db[REGISTRATION]')
                            log.info('        '+_id+' moved to cp2local')
                    else:
                        log.info(base_f+' moving to error_recon, step 8')
                        db['ERROR_QUEUE'][subjid] = schedule.get_time_end_of_walltime(process) #str(format(datetime.now()+timedelta(hours=datetime.strptime(Get_walltime(process), '%H:%M:%S').hour), "%Y%m%d_%H%M")) #2RM
                        db['PROCESSED']['error_recon'].append(base_f)
            else:
                cmd = get_cmd('recbase', base_f, ls_tps = All_cross_ids_done).cmd
                job_id = schedule.submit_4_processing(cmd, base_f, 'recbase')
                db['RUNNING_JOBS'][base_f] = job_id
                db['LONG_DIRS'][_id].append(base_f)
                db['RUNNING']['recon'].append(base_f)
    else:
        for subjid in ls:
            if subjid not in db["RUNNING_JOBS"]:
                if chk.checks_from_runfs('registration', subjid):
                # if fs_checker.checks_from_runfs(SUBJECTS_DIR, 'registration', subjid, vars_freesurfer["freesurfer_version"], vars_freesurfer["masks"]): #2RM
                   if chk.checks_from_runfs(process_order[-1], subjid):
                   # if fs_checker.checks_from_runfs(SUBJECTS_DIR, process_order[-1], subjid, vars_freesurfer["freesurfer_version"], vars_freesurfer["masks"]): #2RM
                        log.info('            last process done '+process_order[-1])
                        if subjid in db['RUNNING'][process_order[-1]]:
                            db['RUNNING'][process_order[-1]].remove(subjid)
                        if chk.chk_if_all_done(subjid):
                        # if fs_checker.chk_if_all_done(SUBJECTS_DIR, subjid, process_order, NIMB_tmp, vars_freesurfer["freesurfer_version"], vars_freesurfer["masks"]): #2RM
                            log.info('            all processes done, moving to CP2LOCAL')
                            db['PROCESSED']['cp2local'].append(subjid)
                            db['LONG_DIRS'].pop(_id, None)
                            db['LONG_TPS'].pop(_id, None)
                            if subjid in db['REGISTRATION']:
                                db['REGISTRATION'].pop(subjid, None)
                            else:
                                log.info('        missing from db[REGISTRATION]')
                        else:
                            db['PROCESSED']['error_'+process_order[1]].append(subjid)
                else:
                    log.info('        '+subjid+' was not registered')
                    if subjid not in db['DO']['registration'] and subjid not in db['RUNNING']['registration']:
                        db['LONG_DIRS'].pop(_id, None)
                        db['LONG_TPS'].pop(_id, None)
                        if subjid in db['REGISTRATION']:
                            db['REGISTRATION'].pop(subjid, None)
                        else:
                            log.info('        missing from db[REGISTRATION]')
    cdb.Update_DB(db, NIMB_tmp)


def move_processed_subjects(subject, db_source, new_name):
    # moving the file with mr parameters, created with mri_info
    file_mrparams = path.join(NIMB_tmp, 'mriparams', '{}_mrparams'.format(subject))
    if path.isfile(file_mrparams):
        shutil.move(file_mrparams, path.join(SUBJECTS_DIR, subject, 'stats'))

    # copying the processed folder to the temporary nimb storage folder
    log.info('    {} copying from {}'.format(subject, db_source))
    _dir_store = vars_nimb["NIMB_PROCESSED_FS"]
    cp_src_path = path.join(SUBJECTS_DIR, subject)
    cp_dst_path = path.join(_dir_store, subject)
    shutil.copytree(cp_src_path, cp_dst_path)

    # extracting the initial size of the folder to copy, to verify with the copied size
    # if both sizes are similar, source is removed
    # if a new name due to error - was assigned, folder is renamed
    # if user requested archiving - archiving is performed.
    size_src = sum(f.stat().st_size for f in Path(cp_src_path).glob('**/*') if f.is_file())
    size_dst = sum(f.stat().st_size for f in Path(cp_dst_path).glob('**/*') if f.is_file())
    if size_src == size_dst:
        db['PROCESSED'][db_source].remove(subject)
        cdb.Update_DB(db, NIMB_tmp)
        shutil.rmtree(cp_src_path)
        if new_name:
            log.info('        renaming {} to {}, moving to {}'.format(subject, new_name, vars_nimb["NIMB_PROCESSED_FS_error"]))
            _dir_store = vars_nimb["NIMB_PROCESSED_FS_error"]
            subject    = new_name
            cp_dst_err = path.join(_dir_store, subject)
            shutil.move(cp_dst_path, cp_dst_err)
        if vars_processing["archive_processed"] == 1:
            log.info('        archiving ...')
            cd_cmd = 'cd {}'.format(_dir_store)
            cmd = 'zip -r -q -m {}.zip {}'.format(subject, subject)
            schedule.submit_4_processing(cmd,'nimb','archiving', cd_cmd,
                                        activate_fs = False,
                                        python_load = False)
    else:
        log.info('        ERROR in moving, not moved correctly {} {}'.format(str(size_src), str(size_dst)))
        shutil.rmtree(path.join(vars_nimb["NIMB_PROCESSED_FS"], subject))


def loop_run():
    cdb.Update_DB(db, NIMB_tmp)
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
    file = path.join(NIMB_tmp, DEFAULT.f_running_fs)
    if cmd == 1:
        if path.isfile('{}0'.format(file)):
            rename('{}0'.format(file), '{}1'.format(file))
        else:
            open('{}1'.format(file), 'w').close()
    else:
        if path.isfile('{}1'.format(file)):
            rename('{}1'.format(file), '{}0'.format(file))

def run(varslocal, logger):

    global db, schedule, log, chk, vars_local, vars_freesurfer, fs_ver, vars_processing, vars_nimb, NIMB_HOME, NIMB_tmp, SUBJECTS_DIR, max_walltime, process_order, processing_env
    
    vars_local      = varslocal
    vars_freesurfer = vars_local["FREESURFER"]
    vars_processing = vars_local["PROCESSING"]
    vars_nimb       = vars_local["NIMB_PATHS"]
    processing_env  = vars_local["PROCESSING"]["processing_env"]

    NIMB_HOME       = vars_nimb["NIMB_HOME"]
    NIMB_tmp        = vars_nimb["NIMB_tmp"]
    max_walltime    = vars_processing["max_walltime"]
    SUBJECTS_DIR    = vars_freesurfer["FS_SUBJECTS_DIR"]
    # process_order   = vars_freesurfer["process_order"] #importing from fs_definitions
    fs_ver          = FreeSurferVersion(vars_freesurfer["freesurfer_version"]).fs_ver()
    log             = logger #logging.getLogger(__name__)
    chk             = FreeSurferChecker(vars_freesurfer)
    schedule        = Scheduler(vars_local)

    t0           = time.time()
    time_elapsed = 0
    count_run    = 0

    log.info('pipeline started')
    Update_running(NIMB_tmp, 1)

    log.info('reading database')
    db = cdb.Get_DB(NIMB_HOME, NIMB_tmp, process_order)

    log.info('NEW SUBJECTS searching:')
    db = cdb.Update_DB_new_subjects_and_SUBJECTS_DIR(NIMB_tmp,
                                                    db,
                                                    vars_freesurfer,
                                                    DEFAULT)
    cdb.Update_DB(db, NIMB_tmp)
    active_subjects = check_active_tasks(db)

    # extracting 40 minutes from the maximum time for the batch to run
    # since it is expected that less then 35 minutes will be required for the pipeline to perform all the steps
    # while the batch is running, and start new batch
    max_batch_running = time.strftime('%H:%M:%S',time.localtime(time.mktime(time.strptime(vars_processing["batch_walltime"],"%H:%M:%S")) - 2400))

    while active_subjects >0 and time.strftime("%H:%M:%S",time.gmtime(time_elapsed)) < max_batch_running:
        count_run += 1
        log.info('restarting run, '+str(count_run))
        log.info('elapsed time: '+time.strftime("%H:%M",time.gmtime(time_elapsed))+' max walltime: '+vars_processing["batch_walltime"][:-6])
        if count_run % 5 == 0:
            log.info('NEW SUBJECTS searching:')
            db = cdb.Update_DB_new_subjects_and_SUBJECTS_DIR(NIMB_tmp,
                                                            db,
                                                            vars_freesurfer,
                                                            DEFAULT)
            cdb.Update_DB(db, NIMB_tmp)
        loop_run()

        time_to_sleep = Count_TimeSleep()
        log.info('\n\nWAITING. \nNext run at: '+str(time.strftime("%H:%M",time.localtime(time.time()+time_to_sleep))))

        time_elapsed = time.time() - t0
#        if time.strftime("%H:%M:%S",time.gmtime(time_elapsed+time_to_sleep)) < max_batch_running:
#                  batch gets closed by the scheduler, trying to calculate time left until batch is finished,
#                  line if was creating an infinitie loop, without the time.sleep, might have been related to missing :%S in strpftime

        time.sleep(time_to_sleep)

        time_elapsed = time.time() - t0
        active_subjects = check_active_tasks(db)

    if active_subjects == 0:
        Update_running(NIMB_tmp, 0)
        log.info('ALL TASKS FINISHED')
    else:
        cd_cmd = 'cd {}'.format(path.join(NIMB_HOME, 'processing', 'freesurfer'))
        cmd = '{} crun.py'.format(vars_processing["python3_run_cmd"])
        log.info('Sending new batch to scheduler with cd_cmd: {} '.format(cd_cmd))
        schedule.submit_4_processing(cmd,'nimb','run', cd_cmd,
                                    activate_fs = False,
                                    python_load = True)



if __name__ == "__main__":

    from pathlib import Path
    import sys

    top = Path(__file__).resolve().parents[2]
    sys.path.append(str(top))

    from setup.get_vars import Get_Vars
    from distribution.logger import Log
    from distribution.distribution_definitions import DEFAULT
    getvars = Get_Vars()
    vars_local = getvars.location_vars['local']
    # Log(vars_local['NIMB_PATHS']['NIMB_tmp'],
    #     vars_local['FREESURFER']['freesurfer_version'])
    logger = Log(vars_local['NIMB_PATHS']['NIMB_tmp'],
                 vars_local['FREESURFER']['freesurfer_version']).logger

    from processing.schedule_helper import Scheduler, get_jobs_status

    run(vars_local, logger)

