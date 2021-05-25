#!/bin/python
# 2020.09.10

import os
from os import path, system, chdir, environ, rename
import time
import shutil

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
    file = path.join(NIMB_tmp, 'running_')
    if cmd == 1:
        if path.isfile('{}0'.format(file)):
            rename('{}0'.format(file), '{}1'.format(file))
        else:
            open('{}1'.format(file), 'w').close()
    else:
        if path.isfile('{}1'.format(file)):
            rename('{}1'.format(file), '{}0'.format(file))


def run_processing(varslocal, logger):


    # self.project - must be defined
    print('    initiating processing')

#     global db, schedule, log, chk, vars_local, vars_freesurfer, fs_ver, vars_processing, vars_nimb, NIMB_HOME, NIMB_tmp, SUBJECTS_DIR, max_walltime, process_order, processing_env
    
#     vars_local      = varslocal
#     vars_freesurfer = vars_local["FREESURFER"]
#     vars_processing = vars_local["PROCESSING"]
#     vars_nimb       = vars_local["NIMB_PATHS"]
#     processing_env  = vars_local["PROCESSING"]["processing_env"]

#     NIMB_HOME       = vars_nimb["NIMB_HOME"]
#     NIMB_tmp        = vars_nimb["NIMB_tmp"]
#     max_walltime    = vars_processing["max_walltime"]
#     SUBJECTS_DIR    = vars_freesurfer["FS_SUBJECTS_DIR"]
#     process_order   = vars_freesurfer["process_order"]
#     fs_ver          = FreeSurferVersion(vars_freesurfer["freesurfer_version"]).fs_ver()
#     log             = logger #logging.getLogger(__name__)
#     chk             = FreeSurferChecker(vars_freesurfer)
#     schedule        = Scheduler(vars_local)

#     t0           = time.time()
#     time_elapsed = 0
#     count_run    = 0

#     log.info('    processing pipeline started')
#     Update_running(NIMB_tmp, 1)

#     log.info('    processing database reading')
#     db = proc_db.Get_DB(NIMB_HOME, NIMB_tmp, process_order)

#     log.info('    NEW SUBJECTS searching:')
#     db = proc_db.Update_DB_new_subjects_and_SUBJECTS_DIR(NIMB_tmp,
#                                                     db,
#                                                     vars_freesurfer,
#                                                     DEFAULT)
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
#         cmd        = f'{python_run} processing_run.py -project {self.project}'
#         log.info(f'    Sending new processing batch to scheduler with cd_cmd: {cd_cmd} ')
#         schedule.submit_4_processing(cmd, 'nimb_processing','run', cd_cmd)


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

    top = Path(__file__).resolve().parents[2]
    sys.path.append(str(top))

    from setup.get_vars import Get_Vars
    from distribution.logger import Log
    from distribution.distribution_definitions import DEFAULT
    from distribution.utilities import load_json, save_json
    from processing import processing_db as proc_db
    from processing.schedule_helper import Scheduler, get_jobs_status
    from stats.db_processing import Table

    all_vars    = Get_Vars()
    project_ids = all_vars.project_ids
    params      = get_parameters(project_ids)

    NIMB_tmp    = all_vars.location_vars['local']['NIMB_PATHS']['NIMB_tmp']
    fs_version  = all_vars.location_vars['local']['FREESURFER']['freesurfer_version']
    logger      = Log(NIMB_tmp, fs_version).logger

    vars_local  = all_vars.location_vars['local']
    run_processing(vars_local, logger)
