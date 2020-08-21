#!/bin/python
# 2020.08.04

print_all_subjects = False

from os import path, system, chdir, environ
import time, shutil
from datetime import datetime, timedelta
import logging
import crunfs, cdb, cwalltime
from logger import Log






# Log(NIMB_tmp)
# log = logging.getLogger(__name__)


#scheduler_params = {'NIMB_HOME'            : NIMB_HOME,
#                    'NIMB_tmp'             : NIMB_tmp,
#                    'SUBJECTS_DIR'         : SUBJECTS_DIR,
#                    'text4_scheduler'      : vars["PROCESSING"]["text4_scheduler"],
#                    'batch_walltime_cmd'   : vars["PROCESSING"]["batch_walltime_cmd"],
#                    'batch_output_cmd'     : vars["PROCESSING"]["batch_output_cmd"],
#                    'export_FreeSurfer_cmd': vars["FREESURFER"]["export_FreeSurfer_cmd"],
#                    'source_FreeSurfer_cmd': vars["FREESURFER"]["source_FreeSurfer_cmd"],
#                    'SUBMIT'               : vars["PROCESSING"]["SUBMIT"]}


environ['TZ'] = 'US/Eastern'
time.tzset()


class Get_cmd:

    def registration(subjid, t1_f, flair_f, t2_f):
        flair_cmd = '{}'.format(''.join([' -FLAIR '+i for i in flair_f])) if flair_f != 'none' else ''
        t2_cmd = '{}'.format(''.join([' -T2 '+i for i in t2_f])) if t2_f != 'none' else ''
        return "recon-all{}".format(''.join([' -i '+i for i in t1_f]))+flair_cmd+t2_cmd+' -s '+subjid

    def recbase(id_base, ls_tps): return "recon-all -base {0}{1} -all".format(id_base, ''.join([' -tp '+i for i in ls_tps]))
    def reclong(_id, id_base): return "recon-all -long {0} {1} -all".format(_id, id_base)

    def recon(_id): return "recon-all -all -s {}".format(_id)
    def autorecon1(_id): return "recon-all -autorecon1 -s {}".format(_id)
    def autorecon2(_id): return "recon-all -autorecon2 -s {}".format(_id)
    def autorecon3(_id): return "recon-all -autorecon3 -s {}".format(_id)
    def qcache(_id): return "recon-all -qcache -s {}".format(_id)
    def brstem(_id): return 'segmentBS.sh {}'.format(_id) if vars_local["FREESURFER"]["freesurfer_version"]>6 else 'recon-all -s {} -brainstem-structures'.format(_id)
    def hip(_id): return 'segmentHA_T1.sh {}'.format(_id) if vars_local["FREESURFER"]["freesurfer_version"]>6 else 'recon-all -s {} -hippocampal-subfields-T1'.format(_id)
    def tha(_id): return "segmentThalamicNuclei.sh {}".format(_id)
    def masks(_id): return "cd "+path.join(NIMB_HOME,'processing','freesurfer')+"\npython run_masks.py {}".format(_id)



def Get_status_for_subjid_in_queue(subjid, all_running):
    if subjid in db['RUNNING_JOBS']:
        job_id = str(db['RUNNING_JOBS'][subjid])
        if job_id in all_running:
           return all_running[job_id]
        else:
           return 'none'
    else:
        return 'none'



def running(process, all_running):
    ACTION = 'RUNNING'
    log.info(ACTION+' '+process)

    lsr = db[ACTION][process].copy()

    for subjid in lsr:
        if subjid in db['RUNNING_JOBS']:
            status = Get_status_for_subjid_in_queue(subjid, all_running)
            if status == 'none':
                db[ACTION][process].remove(subjid)
                db['RUNNING_JOBS'].pop(subjid, None)
                if vars_local["FREESURFER"]["base_name"] in subjid:
                    log.info('    reading '+process+', '+subjid+' subjid is long or base ')
                    if crunfs.chkIsRunning(SUBJECTS_DIR, subjid):
                        log.info('    '+subjid+', '+process+' -> ERROR, IsRunning')
                        db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                        db['PROCESSED']['error_recon'].append(subjid)
                else:
                    if not crunfs.chkIsRunning(SUBJECTS_DIR, subjid) and crunfs.checks_from_runfs(SUBJECTS_DIR, process, subjid, vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"]):
                        if process != process_order[-1]:
                            next_process = process_order[process_order.index(process)+1]
                            if not crunfs.checks_from_runfs(SUBJECTS_DIR, next_process, subjid, vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"]):
                                db['DO'][next_process].append(subjid)
                                log.info('    '+subjid+', '+ACTION+' '+process+' -> DO '+next_process)
                            else:
                                db[ACTION][next_process].append(subjid)
                                log.info('    '+subjid+', '+ACTION+' '+process+' -> '+ACTION+' '+next_process)
                        else:
                            log.info('    '+subjid+' processing DONE')
                    else:
                        log.info('    '+subjid+', '+process+' -> ERROR; IsRunning, status= '+status)
                        db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                        db['PROCESSED']['error_'+process].append(subjid)
        else:
            log.info('    '+subjid+' NOT in RUNNING_JOBS')
            db[ACTION][process].remove(subjid)
            if not crunfs.chkIsRunning(SUBJECTS_DIR, subjid):
                if vars_local["FREESURFER"]["base_name"] in subjid:
                    log.info('    reading '+process+', '+subjid+' subjid is long or base ')
                    if not crunfs.checks_from_runfs(SUBJECTS_DIR, 'recon', subjid, vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"]):
                        log.info('    '+subjid+' recon, -> ERROR, not all files were created')
                        db['PROCESSED']['error_recon'].append(subjid)
                else:
                    if crunfs.checks_from_runfs(SUBJECTS_DIR, process, subjid, vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"]):
                        if process != process_order[-1]:
                            next_process = process_order[process_order.index(process)+1]
                            if not crunfs.checks_from_runfs(SUBJECTS_DIR, next_process, subjid, vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"]):
                                db['DO'][next_process].append(subjid)
                                log.info('    '+subjid+', '+ACTION+' '+process+' -> DO '+next_process)
                            else:
                                db[ACTION][next_process].append(subjid)
                                log.info('    '+subjid+', '+ACTION+' '+process+' -> '+ACTION+' '+next_process)
                        else:
                            log.info('    '+subjid+' processing DONE')
                    else:
                        log.info('    '+subjid+' '+process+' -> ERROR, not all files were created')
                        db['PROCESSED']['error_'+process].append(subjid)
            else:
                log.info('    '+subjid+' '+process+' -> ERROR, not in RUNNING_JOBS, IsRunning')
                db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                db['PROCESSED']['error_'+process].append(subjid)
    db[ACTION][process].sort()
    cdb.Update_DB(db, NIMB_tmp)


def do(process):
    ACTION = 'DO'
    log.info(ACTION+' '+process)

    lsd = db[ACTION][process].copy()

    for subjid in lsd:
        log.info('   '+subjid)
        if len_Running()<= vars_local["PROCESSING"]["max_nr_running_batches"]:
            db[ACTION][process].remove(subjid)
            if process == 'registration':
                if not crunfs.checks_from_runfs(SUBJECTS_DIR, 'registration',subjid, vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"]):
                    t1_ls_f, flair_ls_f, t2_ls_f = cdb.get_registration_files(subjid, db, NIMB_HOME, NIMB_tmp, vars_local["FREESURFER"]["flair_t2_add"])
                    # job_id = crunfs.submit_4_processing(vars_local["PROCESSING"]["processing_env"], cmd, subjid, run, walltime)
                    job_id = crunfs.makesubmitpbs(Get_cmd.registration(subjid, t1_ls_f, flair_ls_f, t2_ls_f), subjid, process, cwalltime.Get_walltime(process, max_walltime), scheduler_params)
                else:
                    job_id = 0
            elif process == 'recon':
                job_id = crunfs.makesubmitpbs(Get_cmd.recon(subjid), subjid, process, cwalltime.Get_walltime(process, max_walltime), scheduler_params)
            elif process == 'autorecon1':
                job_id = crunfs.makesubmitpbs(Get_cmd.autorecon1(subjid), subjid, process, cwalltime.Get_walltime(process, max_walltime), scheduler_params)
            elif process == 'autorecon2':
                job_id = crunfs.makesubmitpbs(Get_cmd.autorecon2(subjid), subjid, process, cwalltime.Get_walltime(process, max_walltime), scheduler_params)
            elif process == 'autorecon3':
                job_id = crunfs.makesubmitpbs(Get_cmd.autorecon3(subjid), subjid, process, cwalltime.Get_walltime(process, max_walltime), scheduler_params)
            elif process == 'qcache':
                job_id = crunfs.makesubmitpbs(Get_cmd.qcache(subjid), subjid, process, cwalltime.Get_walltime(process, max_walltime), scheduler_params)
            elif process == 'brstem':
                job_id = crunfs.makesubmitpbs(Get_cmd.brstem(subjid), subjid, process, cwalltime.Get_walltime(process, max_walltime), scheduler_params)
            elif process == 'hip':
                job_id = crunfs.makesubmitpbs(Get_cmd.hip(subjid), subjid, process, cwalltime.Get_walltime(process, max_walltime), scheduler_params)
            elif process == 'tha':
                job_id = crunfs.makesubmitpbs(Get_cmd.tha(subjid), subjid, process, cwalltime.Get_walltime(process, max_walltime), scheduler_params)
            elif process == 'masks':
                job_id = crunfs.makesubmitpbs(Get_cmd.masks(subjid), subjid, process, cwalltime.Get_walltime(process, max_walltime), scheduler_params)
            db['RUNNING_JOBS'][subjid] = job_id
            db['RUNNING'][process].append(subjid)
            try:
                log.info('                                   submited id: '+str(job_id))
            except Exception as e:
                log.info('        err in do: '+str(e))
    db[ACTION][process].sort()
    cdb.Update_DB(db, NIMB_tmp)


def check_error():
    log.info('ERROR checking')

    for process in process_order:
        if db['PROCESSED']['error_'+process]:
            lserr = db['PROCESSED']['error_'+process].copy()
            for subjid in lserr:
                log.info('    '+subjid)
                if subjid not in db["ERROR_QUEUE"] and path.exists(path.join(SUBJECTS_DIR, subjid)): #path.exists was added due to moving the subjects too early; requires adjustment
                    crunfs.IsRunning_rm(SUBJECTS_DIR, subjid)
                    log.info('        checking the recon-all-status.log for error for: '+process)
                    crunfs.chkreconf_if_without_error(NIMB_tmp, subjid, SUBJECTS_DIR)
                    log.info('        checking if all files were created for: '+process)
                    if not crunfs.checks_from_runfs(SUBJECTS_DIR, process, subjid, vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"]):
                            log.info('            some files were not created and recon-all-status has errors.')
                            fs_error = crunfs.fs_find_error(subjid, SUBJECTS_DIR, NIMB_tmp)
                            solved = False
                            if fs_error:
                                solve = crunfs.solve_error(subjid, fs_error, SUBJECTS_DIR, NIMB_tmp)
                                if solve == 'continue':
                                    solved = True
                                    db['PROCESSED']['error_'+process].remove(subjid)
                                    db['DO'][process].append(subjid)
                                    log.info('        moving from error_'+process+' to DO '+process)
                                elif solve == 'voxreg' or solve == 'errorigmgz':
                                    if subjid in db['REGISTRATION']:
                                        solved = True
                                        db['REGISTRATION'][subjid]['anat']['t1'] = db['REGISTRATION'][subjid]['anat']['t1'][:1]
                                        if 'flair' in db['REGISTRATION'][subjid]['anat']:
                                                db['REGISTRATION'][subjid]['anat'].pop('flair', None)
                                        if 't2' in db['REGISTRATION'][subjid]['anat']:
                                                db['REGISTRATION'][subjid]['anat'].pop('t2', None)
                                        db['PROCESSED']['error_'+process].remove(subjid)
                                        db['DO']["registration"].append(subjid)
                                        log.info('              removing '+subjid+' from '+SUBJECTS_DIR)
                                        system('rm -r '+path.join(SUBJECTS_DIR, subjid))
                                        log.info('        moving from error_'+process+' to RUNNING registration')
                                    else:
                                        log.info('            solved: '+solve+' but subjid is missing from db[REGISTRATION]')
                                else:
                                    new_name = 'error_'+fs_error+'_'+subjid
                                    log.info('            not solved')
                            else:
                                new_name = 'error_'+process+'_'+subjid
                            if not solved:
                                log.info('            Excluding '+subjid+' from pipeline')
                                _id, _ = cdb.get_id_long(subjid, db['LONG_DIRS'], vars_local["FREESURFER"]["base_name"], vars_local["FREESURFER"]["long_name"])
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
                                        log.info('        ERROR, id not found in LONG_DIRS; '+str(e))
                                else:
                                    log.info('        ERROR, '+subjid+' is absent from LONG_DIRS')
                                move_processed_subjects(subjid, 'error_'+process, new_name)
                    else:
                            log.info('            all files were created for process: '+process)
                            db['PROCESSED']['error_'+process].remove(subjid)
                            db['RUNNING'][process].append(subjid)
                            log.info('        moving from error_'+process+' to RUNNING '+process)
                else:
                    if subjid in db["ERROR_QUEUE"]:
                        log.info('     waiting until: '+db['ERROR_QUEUE'][subjid])
                        if db['ERROR_QUEUE'][subjid] < str(format(datetime.now(), "%Y%m%d_%H%M")):
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
    if vars_local["FREESURFER"]["DO_LONG"] == 1 and len(LONG_TPS)>1:
        All_cross_ids_done = list()
        for ses in LONG_TPS:
            if _id+ses in ls and crunfs.checks_from_runfs(SUBJECTS_DIR, process_order[-1], _id+ses, vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"]):
                All_cross_ids_done.append(_id+ses)

        if len(All_cross_ids_done) == len(LONG_TPS):
            base_f = _id+vars_local["FREESURFER"]["base_name"]
            if base_f in ls:
                if base_f not in db['RUNNING']['recon'] and base_f not in db['PROCESSED']['error_recon'] and not crunfs.chkIsRunning(SUBJECTS_DIR, base_f):
                    if crunfs.checks_from_runfs(SUBJECTS_DIR, 'recon', base_f, vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"]):
                        All_long_ids_done = list()
                        for ses in LONG_TPS:
                            long_f = _id+ses+'.long.'+_id+vars_local["FREESURFER"]["base_name"]
                            if long_f not in ls:
                                job_id = crunfs.makesubmitpbs(Get_cmd.reclong(_id+ses, _id+vars_local["FREESURFER"]["base_name"]), _id+ses, 'reclong', cwalltime.Get_walltime('reclong'), scheduler_params)
                                db['RUNNING_JOBS'][long_f] = job_id
                                db['RUNNING']['recon'].append(long_f)
                                db['LONG_DIRS'][_id].append(long_f)
                            elif crunfs.checks_from_runfs(SUBJECTS_DIR, 'registration',long_f, vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"]):
                                if crunfs.checks_from_runfs(SUBJECTS_DIR, 'recon', long_f, vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"]):
                                    All_long_ids_done.append(long_f)
                                else:
                                    log.info(long_f+' moving to error_recon')
                                    db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                                    db['PROCESSED']['error_recon'].append(long_f)
                            else:
                                log.info(long_f+' moving to error_recon')
                                db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
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
                        db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                        db['PROCESSED']['error_recon'].append(base_f)
            else:
                job_id = crunfs.makesubmitpbs(Get_cmd.recbase(base_f, All_cross_ids_done), base_f, 'recbase', cwalltime.Get_walltime('recbase'), scheduler_params)
                db['RUNNING_JOBS'][base_f] = job_id
                db['LONG_DIRS'][_id].append(base_f)
                db['RUNNING']['recon'].append(base_f)
    else:
        for subjid in ls:
            if subjid not in db["RUNNING_JOBS"]:
                if crunfs.checks_from_runfs(SUBJECTS_DIR, 'registration', subjid, vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"]):
                   if crunfs.checks_from_runfs(SUBJECTS_DIR, process_order[-1], subjid, vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"]):
                        log.info('            last process done '+process_order[-1])
                        if subjid in db['RUNNING'][process_order[-1]]:
                            db['RUNNING'][process_order[-1]].remove(subjid)
                        if crunfs.chk_if_all_done(SUBJECTS_DIR, subjid, process_order, NIMB_tmp, vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"]):
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
    file_mrparams = path.join(NIMB_tmp,'mriparams',subject+'_mrparams')
    if path.isfile(file_mrparams):
        shutil.move(file_mrparams, path.join(SUBJECTS_DIR, subject, 'stats'))
    log.info('    '+subject+' copying from '+db_source)
    size_src = sum(f.stat().st_size for f in Path(path.join(SUBJECTS_DIR, subject)).glob('**/*') if f.is_file())
    if not new_name:
        shutil.copytree(path.join(SUBJECTS_DIR, subject), path.join(vars_local["NIMB_PATHS"]["NIMB_PROCESSED_FS"], subject))
        size_dst = sum(f.stat().st_size for f in Path(path.join(vars_local["NIMB_PATHS"]["NIMB_PROCESSED_FS"], subject)).glob('**/*') if f.is_file())
        if size_src == size_dst:
            db['PROCESSED'][db_source].remove(subject)
            cdb.Update_DB(db, NIMB_tmp)
            log.info('    copied correctly, removing from SUBJECTS_DIR')
            shutil.rmtree(path.join(SUBJECTS_DIR, subject))
            if vars_local["PROCESSING"]["archive_processed"] == 1:
                log.info('        archiving ...')
                chdir(vars_local["NIMB_PATHS"]["NIMB_PROCESSED_FS"])
                system('zip -r -q -m '+subject+'.zip '+subject)
        else:
            log.info('        ERROR in moving, not moved correctly '+str(size_src)+' '+str(size_dst))
            shutil.rmtree(path.join(vars_local["NIMB_PATHS"]["NIMB_PROCESSED_FS"], subject))
    else:
        log.info('        renaming '+subject+' to '+new_name+', moving to processed error')
        shutil.move(path.join(SUBJECTS_DIR, subject), path.join(vars_local["NIMB_PATHS"]["NIMB_PROCESSED_FS_error"], new_name))
        db['PROCESSED'][db_source].remove(subject)
    log.info('        moving DONE')



def loop_run():
    cdb.Update_DB(db, NIMB_tmp)
    all_running = cdb.get_batch_jobs_status(vars_local["USER"]["user"], vars_local["USER"]["users_list"])

    for process in process_order[::-1]:
        if len(db['RUNNING'][process])>0:
            running(process,all_running)
        if len(db['DO'][process])>0:
            do(process)

    check_error()

    log.info('CHECKING subjects')
    ls_long_dirs = list()
    for key in db['LONG_DIRS']:
            ls_long_dirs.append(key)

    for _id in ls_long_dirs:
        if print_all_subjects:
            log.info('    '+_id+': '+str(db['LONG_DIRS'][_id]))
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
    len_Running = 0
    for process in db['RUNNING']:
        len_Running = len_Running+len(db['RUNNING'][process])
    return len_Running


def Count_TimeSleep():
    time2sleep = 600 # 10 minutes
    if len_Running() >= vars_local["PROCESSING"]["max_nr_running_batches"]:
        log.info('running: '+str(len_Running())+' max: '+str(vars_local["PROCESSING"]["max_nr_running_batches"]))
        time2sleep = 1800 # 30 minutes
    return time2sleep


def run(varslocal):   
    print('updating status')

    global vars_local, NIMB_HOME, NIMB_tmp, SUBJECTS_DIR, max_walltime, process_order, scheduler_params
    vars_local       = varslocal
    NIMB_HOME        = vars_local["NIMB_PATHS"]["NIMB_HOME"]
    NIMB_tmp         = vars_local["NIMB_PATHS"]["NIMB_tmp"]
    max_walltime     = vars_local["PROCESSING"]["max_walltime"]
    SUBJECTS_DIR     = vars_local["FREESURFER"]["FS_SUBJECTS_DIR"]
    process_order    = vars_local["FREESURFER"]["process_order"]
    scheduler_params = {'NIMB_HOME'            : NIMB_HOME,
                        'NIMB_tmp'             : NIMB_tmp,
                        'SUBJECTS_DIR'         : SUBJECTS_DIR,
                        'text4_scheduler'      : vars_local["PROCESSING"]["text4_scheduler"],
                        'batch_walltime_cmd'   : vars_local["PROCESSING"]["batch_walltime_cmd"],
                        'batch_output_cmd'     : vars_local["PROCESSING"]["batch_output_cmd"],
                        'export_FreeSurfer_cmd': vars_local["FREESURFER"]["export_FreeSurfer_cmd"],
                        'source_FreeSurfer_cmd': vars_local["FREESURFER"]["source_FreeSurfer_cmd"],
                        'SUBMIT'               : vars_local["PROCESSING"]["SUBMIT"]}

    Log(NIMB_tmp)
    log = logging.getLogger(__name__)

    try:
        from pathlib import Path
    except ImportError as e:
        log.info(e)
    
    t0 = time.time()
    time_elapsed = 0
    count_run = 0

    log.info('pipeline started')
    cdb.Update_running(NIMB_tmp, 1)

    log.info('reading database')
    db = cdb.Get_DB(NIMB_HOME, NIMB_tmp, process_order)

    log.info('NEW SUBJECTS searching:')
    db = cdb.Update_DB_new_subjects_and_SUBJECTS_DIR(NIMB_tmp, SUBJECTS_DIR,db, process_order, vars_local["FREESURFER"]["base_name"], vars_local["FREESURFER"]["long_name"], vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"])
    cdb.Update_DB(db, NIMB_tmp)
    active_subjects = check_active_tasks(db)

    # extracting 40 minutes from the maximum time for the batch to run
    # since it is expected that less then 35 minutes will be required for the pipeline to perform all the steps
    # while the batch is running, and start new batch
    max_batch_running = time.strftime('%H:%M:%S',time.localtime(time.mktime(time.strptime(vars_local["PROCESSING"]["batch_walltime"],"%H:%M:%S"))-2400))

    while active_subjects >0 and time.strftime("%H:%M:%S",time.gmtime(time_elapsed)) < max_batch_running:
        count_run += 1
        log.info('restarting run, '+str(count_run))
        log.info('elapsed time: '+time.strftime("%H:%M",time.gmtime(time_elapsed))+' max walltime: '+vars_local["PROCESSING"]["batch_walltime"][:-6])
        if count_run % 5 == 0:
            log.info('NEW SUBJECTS searching:')
            db = cdb.Update_DB_new_subjects_and_SUBJECTS_DIR(NIMB_tmp, SUBJECTS_DIR, db, process_order, vars_local["FREESURFER"]["base_name"], vars_local["FREESURFER"]["long_name"], vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"])
            cdb.Update_DB(db, NIMB_tmp)
        loop_run()

        time_to_sleep = Count_TimeSleep()
        log.info('\n\nWAITING. \nNext run at: '+str(time.strftime("%H:%M",time.localtime(time.time()+time_to_sleep))))

        time_elapsed = time.time() - t0
#        if time.strftime("%H:%M:%S",time.gmtime(time_elapsed+time_to_sleep)) < max_batch_running:
#                  batch gets closed by the scheduler, trying to calculate time left until batch is finished,
#                  line if was creating an infinitie loop, without the time.sleep, might have been related to missing :%S in strpftime
#                  commented now, needs to be checked

        time.sleep(time_to_sleep)

        time_elapsed = time.time() - t0
        active_subjects = check_active_tasks(db)

    if active_subjects == 0:
        cdb.Update_running(NIMB_tmp, 0)
        log.info('ALL TASKS FINISHED')
    else:
        log.info('Sending new batch to scheduler')
        cdb.Update_status_log(NIMB_tmp, 'Sending new batch to scheduler')
        import start_fs_pipeline
        start_fs_pipeline.start_fs_pipeline(vars_local)
#        chdir(NIMB_HOME)
#        system('python processing/freesurfer/start_fs_pipeline.py')




if __name__ == "__main__":

    import sys
    from pathlib import Path

    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[2]
    sys.path.append(str(top))

    from setup.get_vars import Get_Vars
    getvars = Get_Vars()
    run(getvars.location_vars['local'])



#    from get_username import _get_username
#    import json
#    try:
#        credentials_home = str(open('../../credentials_path').readlines()[0]).replace("~","/home/"+_get_username())
#        with open(path.join(credentials_home, 'local.json')) as local_vars:
#            vars = json.load(local_vars)
#    except Exception as e: 
#        print(e, 'ERROR: credential file or local.json file is MISSING')


        
'''THIS script was used for the longitudinal analysis. It has changed and it should not be needed now, but a longitudinal analysis must be made to confirm'''

# def long_check_pipeline(all_running):
#     lsq_long = list()
#     for val in db['RUNNING_LONG']['queue']:
#         lsq_long.append(val)	


#     for subjid in lsq_long:
#         if subjid in db['RUNNING_JOBS']:
#             status = Get_status_for_subjid_in_queue(subjid, all_running)
#             if status =='R' or status == 'none' and crunfs.checks_from_runfs(SUBJECTS_DIR, 'registration',subjid):
#                 print('       ',subjid,' status: ',status,'; moving from queue to running')
#                 cdb.Update_status_log(nimb_scratch_dir, 'moving '+subjid+' from queue to running')
#                 db['RUNNING_LONG']['queue'].remove(subjid)
#                 db['RUNNING']['recon'].append(subjid)
#             elif status == 'none' and not crunfs.checks_from_runfs(SUBJECTS_DIR, 'registration',subjid):
#                 db['RUNNING_LONG']['queue'].remove(subjid)
#                 db['PROCESSED']['error_recon'].append(subjid)
#         else:
#             print(subjid,'    queue, NOT in RUNNING_JOBS')
#             if crunfs.checks_from_runfs(SUBJECTS_DIR, 'registration',subjid):
#                 if crunfs.chkIsRunning(SUBJECTS_DIR, subjid):
#                     cdb.Update_status_log(nimb_scratch_dir, 'moving '+subjid+' from long_QUEUE to long_RUNNING')
#                     db['RUNNING_LONG']['queue'].remove(subjid)
#                     db['RUNNING']['recon'].append(subjid)
#                 elif crunfs.checks_from_runfs(SUBJECTS_DIR, 'recon', subjid):
#                     cdb.Update_status_log(nimb_scratch_dir, subjid+' long recon DONE')
#                     db['RUNNING_LONG']['queue'].remove(subjid)

#     lsr_long = list()
#     for val in db['RUNNING_LONG']['running']:
#         lsr_long.append(val)

#     LOOP was sent to RUNNING/recon
#     for subjid in lsr_long:
#         if subjid in db['RUNNING_JOBS']:
#             status = Get_status_for_subjid_in_queue(subjid, all_running)
#             if status == 'none':
#                 db['RUNNING_LONG']['running'].remove(subjid)
#                 db['RUNNING_JOBS'].pop(subjid, None)
#                 if crunfs.chkIsRunning(SUBJECTS_DIR, subjid) or not crunfs.checks_from_runfs(SUBJECTS_DIR, 'recon', subjid):
#                     db['PROCESSED']['error_recon'].append(subjid)
#         else:
#             print('    ',subjid,'    queue, NOT in RUNNING_JOBS')
#             if not crunfs.chkIsRunning(SUBJECTS_DIR, subjid):
#                 db['RUNNING_LONG']['running'].remove(subjid)
#                 if not crunfs.checks_from_runfs(SUBJECTS_DIR, 'recon', subjid):
#                     db['PROCESSED']['error_recon'].append(subjid)
#     cdb.Update_DB(db, nimb_scratch_dir)

