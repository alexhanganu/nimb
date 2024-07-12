#!/bin/python
# 2021.11.08

import os
from os import path, system, chdir, environ, rename, remove, listdir
from pathlib import Path
import time
import shutil
import logging
import fs_err_helper
from fs_definitions import FSProcesses, fs_version

environ['TZ'] = 'US/Eastern'
time.tzset()

"""For quality control
Euler numbers to detect outlier datasets for exclusion
1. Rosen, A. F., Roalf, D. R., Ruparel, K., Blake, J., Seelaus, K., Villa, L. P., ... & Satterthwaite, T. D. (2018). Quantitative assessment of structural image quality. Neuroimage, 169, 407-418.
2. de Lange, A. M. G., Kaufmann, T., Quintana, D. S., Winterton, A., Andreassen, O. A., Westlye, L. T., & Ebmeier, K. P. (2021). Prominent health problems, socioeconomic deprivation, and higher brain age in lonely and isolated individuals: A population-based study. Behavioural Brain Research, 414, 113510.
else:
    run:
        mri_segstats --qa-stats subject subject.qa.dat
        It will generate the QA .dat file.
        This will have 20 numbers in it.
        Output has 17 items: (1) 
                subjectname, (2) number of control points, (3) number of WM 
                voxels erased, (4) number of WM voxels filled, (5) number of 
                brainmask.mgz voxels erased (relative to brainmask.auto.mgz), 
                (6) number of brainmask.mgz voxels cloned, (7) number of 
                aseg.mgz voxels changed, (8) number of holes in lh.orig.nofix,
                (9) number of holes in rh.orig.nofix, (10) total number of 
                holes, (11) ratio of number of voxels in brainmask.mgz to the 
                eTIV, (12) mean norm.mgz in WM voxels, (13) spatial std of 
                WM,(14) min WM, (15) max WM, (16) range WM, (17) WM SNR (mean/
                std). The WM statistics are computed from a WM mask in 
                aparc+aseg.mgz eroded by 3 voxels. The WM statistics are 
                "robust" meaning that the top and bottom 2% are excluded 
                before computing the stats. (18) Mean gray/white percent 
                contrast, (19) Spatial stddev of G/W percent contrast, (20) 
                CNR = 18/19.
        Run:
            mri_segstats --help to see what they are.
            I usually use #20 (CNR)
            Run it for all subjects,
            then sort by CNR,
            then examine the worse subjects
to run Local Gyrification index:
https://surfer.nmr.mgh.harvard.edu/fswiki/LGI
run:
    recon-all -s <subj> -localGI
for this you will need:
        that the ?h.pial surface files exist in the subject's <subj>/surf directory
        You will need $FREESURFER_HOME/matlab in your matlab path set up in your ~/matlab/starup.m script. 
To generate statistics on ROIs, for example:
mri_segstats --annot <subj> lh aparc --i $SUBJECTS_DIR/<subj>/surf/lh.pial_lgi --sum lh.aparc.pial_lgi.stats

mri_segstats --slabel <subj> lh $SUBJECTS_DIR/subject/label/lh.cortex --i

$SUBJECTS_DIR/<subj>/surf/lh.pial_lgi –excluded 0 --sum lh.aparc.pial_lgi.stats

in the file lh.aparc.pial_lgi.stats, the variable that is reporting the gyrification index is The "Mean" column
"""


def get_cmd(process, _id, id_base = '', ls_tps = []):
    if process == 'registration':
        return db_manage.get_registration_cmd(_id, db,
                                            vars_app["flair_t2_add"])
    elif process == "qcache":
        chdir = f"cd {os.path.join(SUBJECTS_DIR, _id, 'stats')}\n"
        qa_cmd = f"mri_segstats --qa-stats {_id} {_id}.qa.dat\n"
        return chdir + qa_cmd + Procs.cmd(process, _id, id_base, ls_tps)
    elif process == 'masks':
        chdir = f"cd {os.path.join(NIMB_HOME, 'processing', 'freesurfer')}\n"
        return chdir + Procs.cmd(process, _id, id_base, ls_tps)

    else:
        return Procs.cmd(process, _id, id_base, ls_tps)


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
        log.info(f'            job_id for subject {subjid} inferred, probable jobids: {str(probable_jobids[0])}')
        if len(probable_jobids)>1:
            running_jobs[subjid] = 0
        else:
            running_jobs[subjid] = probable_jobids[0]
        return running_jobs, 'PD'
    else:
        return running_jobs, 'none'


def running(process, scheduler_jobs):
    ACTION = 'RUNNING'
    log.info(f'{ACTION} {process}')
    lsr = db[ACTION][process].copy()
    for subjid in lsr:
        db['RUNNING_JOBS'], status, job_id = Get_status_for_subjid_in_queue(db['RUNNING_JOBS'], subjid, scheduler_jobs)
        if status == 'none':
            db[ACTION][process].remove(subjid)
            if subjid in db['RUNNING_JOBS']:
                db['RUNNING_JOBS'].pop(subjid, None)
            if vars_app["base_name"] in subjid:
                log.info(f'    reading {process}, {subjid} is long or base ')
                if chk2.chk(subjid, app, vars_app, 'isrunning') or not chk2.chk(subjid, app, vars_app, 'recon'):
                        log.info(f'    {subjid}, {process} -> ERROR, IsRunning or not all files created')
                        db['ERROR_QUEUE'][subjid] = schedule.get_time_end_of_walltime(process)
                        db['PROCESSED']['error_recon'].append(subjid)
            else:
                if not chk2.chk(subjid, app, vars_app, 'isrunning') and chk2.chk(subjid, app, vars_app, process):
                    if process != process_order[-1]:
                        next_process = process_order[process_order.index(process)+1]
                        if not chk2.chk(subjid, app, vars_app, next_process):
                            db['DO'][next_process].append(subjid)
                            log.info(f'    {subjid}, {ACTION} {process} -> DO {next_process}')
                            if processing_env == 'tmux':
                                schedule.kill_tmux_session(job_id)
                        else:
                            db[ACTION][next_process].append(subjid)
                            log.info(f'    {subjid}, {ACTION} {process} -> {ACTION} {next_process}')
                    else:
                        log.info(f'    {subjid} processing DONE')
                else:
                    log.info(f'    {subjid}, {process} -> ERROR; IsRunning, status= {status}')
                    db['ERROR_QUEUE'][subjid] = schedule.get_time_end_of_walltime(process)
                    db['PROCESSED']['error_'+process].append(subjid)
    db[ACTION][process].sort()
    dbmain[app] = db
    db_manage.update_db(dbmain)


def do(process):
    ACTION = 'DO'
    log.info(f'{ACTION} {process}')

    lsd = db[ACTION][process].copy()

    for subjid in lsd:
        if len_Running()<= vars_processing["max_nr_running_batches"]:
            db[ACTION][process].remove(subjid)
            cmd = get_cmd(process, subjid)
            job_id = schedule.submit_4_processing(cmd, subjid, process)
            db['RUNNING_JOBS'][subjid] = job_id
            db['RUNNING'][process].append(subjid)
            try:
                log.info(f'    {subjid} submited id: {str(job_id)}')
            except Exception as e:
                log.info(f'    {subjid} err in do: {str(e)}')
    db[ACTION][process].sort()
    dbmain[app] = db
    db_manage.update_db(dbmain)


def check_error(scheduler_jobs, process):
    log.info('ERROR checking {}'.format(process))

    if db['PROCESSED']['error_'+process]:
            lserr = db['PROCESSED']['error_'+process].copy()
            for subjid in lserr:
                log.info('    {}'.format(subjid))
                if subjid not in db["ERROR_QUEUE"] and path.exists(path.join(SUBJECTS_DIR, subjid)): #path.exists was added due to moving the subjects too early; requires adjustment
                    chk2.chk(subjid, app, vars_app, 'isrunning', rm = True)
                    log.info('        checking the recon-all-status.log for error for: {}'.format(process))
                    fs_err_helper.chkreconf_if_without_error(NIMB_tmp, subjid, SUBJECTS_DIR)
                    log.info('        checking if all files were created for: {}'.format(process))
                    if not chk2.chk(subjid, app, vars_app, process):
                            log.info('            some files were not created and recon-all-status has errors.')
                            log_f = Procs.log(process)
                            log_file = os.path.join(SUBJECTS_DIR, subjid, log_f)
                            fs_error = fs_err_helper.fs_find_error(log_file)
                            solved = False
                            if fs_error:
                                solve = fs_err_helper.solve_error(log_file, fs_error)
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
                                        new_name = f'err_{subjid}_noreg'
                                        log.info('            solved: {} but subjid is missing from db[REGISTRATION]'.format(solve))
                                elif solve == "run_mri_concat_pass_orig_to_recon_all":
                                    solved = True
                                    file_2concat = path.join(SUBJECTS_DIR, subjid, "mri/orig/001.mgz")
                                    cmd = f"mri_concat {file_2concat} --rms --o {file_2concat}"
                                    process = "mri_concat"
                                    job_id = schedule.submit_4_processing(cmd, subjid, process)
                                    db['RUNNING_JOBS'][subjid] = job_id
                                    db['PROCESSED']['error_'+process].remove(subjid)
                                    db['RUNNING']["registration"].append(subjid)
                                elif solve == "rm_multi_origmgz":
                                    solved = True
                                    orig_path = path.join(SUBJECTS_DIR, subjid, "mri/orig")
                                    files_2rm = [i for i in listdir(orig_path) if i != "001.mgz"]
                                    for file in files_2rm:
                                        remove(path.join(orig_path, file))
                                    db['PROCESSED']['error_'+process].remove(subjid)
                                    db['DO'][process].append(subjid)
                                elif solve == "add_careg":
                                    cmd = get_cmd(process, subjid) + " -careg"
                                    job_id = schedule.submit_4_processing(cmd, subjid, process)
                                    db['RUNNING_JOBS'][subjid] = job_id
                                    db['PROCESSED']['error_'+process].remove(subjid)
                                    db['RUNNING'][process].append(subjid)
                                    solved = True
                                    try:
                                        log.info('            {} submited id: {}'.format(subjid, str(job_id)))
                                    except Exception as e:
                                        log.info('        {} err in do: {}'.format(subjid, str(e)))
                                else:
                                    new_name = f'err_{subjid}_{fs_error}'
                                    log.info('            not solved')
                            else:
                                new_name = f'err_{subjid}_{process}'
                            if not solved:
                                log.info('            Excluding {} from pipeline'.format(subjid))
                                bids_format, _id, ses, run_label = is_bids_format(subjid)
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
                        elif not chk2.chk(subjid, app, vars_app, 'isrunning') or db['ERROR_QUEUE'][subjid] < schedule.get_time_end_of_walltime('now'):
                            log.info('    removing from ERROR_QUEUE')
                            db['ERROR_QUEUE'].pop(subjid, None)
                    else:
                        log.info('    not in SUBJECTS_DIR')
                        db['PROCESSED']['error_'+process].remove(subjid)
                db['PROCESSED']['error_'+process].sort()
                dbmain[app] = db
                db_manage.update_db(dbmain)



def long_check_groups(_id):
    ls = db['LONG_DIRS'][_id]
    LONG_TPS = db['LONG_TPS'][_id]
    if vars_app["DO_LONG"] == 1 and len(LONG_TPS)>1:
        All_cross_ids_done = list()
        for ses in LONG_TPS:
            if _id+ses in ls and chk2.chk(_id+ses, app, vars_app, process_order[-1]):
                All_cross_ids_done.append(_id+ses)

        if len(All_cross_ids_done) == len(LONG_TPS):
            base_f = _id+vars_app["base_name"]
            if base_f in ls:
                if base_f not in db['RUNNING']['recon'] and base_f not in db['PROCESSED']['error_recon'] and not chk2.chk(base_f, app, vars_app, 'isrunning'):
                    if chk2.chk(base_f, app, vars_app, "recon"):
                        All_long_ids_done = list()
                        for ses in LONG_TPS:
                            long_f = _id+ses+'.long.'+_id+vars_app["base_name"]
                            if long_f not in ls:
                                cmd = get_cmd('reclong', _id+ses, id_base = _id+vars_app["base_name"])
                                job_id = schedule.submit_4_processing(cmd, _id+ses, 'reclong')
                                db['RUNNING_JOBS'][long_f] = job_id
                                db['RUNNING']['recon'].append(long_f)
                                db['LONG_DIRS'][_id].append(long_f)
                            elif chk2.chk(long_f, app, vars_app, 'registration'):
                                if chk2.chk(long_f,app, vars_app, 'recon'):
                                    All_long_ids_done.append(long_f)
                                else:
                                    log.info(long_f+' moving to error_recon')
                                    db['ERROR_QUEUE'][subjid] = schedule.get_time_end_of_walltime(process)
                                    db['PROCESSED']['error_recon'].append(long_f)
                            else:
                                log.info(long_f+' moving to error_recon')
                                db['ERROR_QUEUE'][subjid] = schedule.get_time_end_of_walltime(process)
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
                        db['ERROR_QUEUE'][subjid] = schedule.get_time_end_of_walltime(process)
                        db['PROCESSED']['error_recon'].append(base_f)
            else:
                cmd = get_cmd('recbase', base_f, ls_tps = All_cross_ids_done)
                job_id = schedule.submit_4_processing(cmd, base_f, 'recbase')
                db['RUNNING_JOBS'][base_f] = job_id
                db['LONG_DIRS'][_id].append(base_f)
                db['RUNNING']['recon'].append(base_f)
    else:
        for subjid in ls:
            if subjid not in db["RUNNING_JOBS"]:
                if chk2.chk(subjid, app, vars_app, 'registration'):
                    if chk2.chk(subjid, app, vars_app, process_order[-1]):
                        log.info(f'    {subjid}: last process done {process_order[-1]}')
                        if subjid in db['RUNNING'][process_order[-1]]:
                            db['RUNNING'][process_order[-1]].remove(subjid)
                        if chk2.chk(subjid, app, vars_app, 'all_done'):
                            log.info('        all processes done, moving to CP2LOCAL')
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
                            log.info(f'        {subjid}: missing from db[REGISTRATION]')
    dbmain[app] = db
    db_manage.update_db(dbmain)


def move_processed_subjects(subject, db_source, new_name):
    # moving the file with mr parameters, created with mri_info
    file_mrparams = path.join(NIMB_tmp, 'mriparams', '{}_mrparams'.format(subject))
    if path.isfile(file_mrparams):
        shutil.move(file_mrparams, path.join(SUBJECTS_DIR, subject, 'stats'))

    # copying the processed folder to the temporary nimb storage folder
    log.info(f'    {subject} preparing to move from {db_source}')
    _dir_store = vars_app["NIMB_PROCESSED"]
    cp_src_path = path.join(SUBJECTS_DIR, subject)
    cmd_mv = f'mv {cp_src_path} {_dir_store}\n'
    size_src = sum(f.stat().st_size for f in Path(cp_src_path).glob('**/*') if f.is_file())
    log.info(f'        initial size of folder is: {size_src}')

    cmd_zip = ""
    cmd_rename = ""
    if new_name:
        _dir_store = vars_app["NIMB_ERR"]
        rename_err = path.join(SUBJECTS_DIR, new_name)
        cmd_rename = f'mv {cp_src_path} {rename_err}\n'
        cmd_mv     = f'mv {rename_err} {_dir_store}\n'
    if vars_processing["archive_processed"] == 1:
        cmd_zip = f'zip -r -m {subject}.zip {subject}'

    log.info(f'        sending to scheduler to:')
    if cmd_rename:
        log.info(f'            rename {subject} to: {new_name}')
        log.info(f'            mv {new_name} to: {_dir_store}')
    else:
        log.info(f'            mv {subject} to: {_dir_store}')

    if cmd_zip:
        log.info(f'            archive')
    cmd = cmd_rename + cmd_mv + cmd_zip
    cd_cmd = f'cd {_dir_store}'
    job_id = schedule.submit_4_processing(cmd, subject, 'moving',
                                 cd_cmd,
                                 activate_fs = False,
                                 python_load = False)
    db['RUNNING_JOBS'][subject] = job_id
    dbmain[app] = db
    db_manage.update_db(dbmain)
    try:
        log.info(f'        {subject} submited id: {str(job_id)}')
    except Exception as e:
        log.info(f'        {subject} err in do: {str(e)}')


def loop_run():
    dbmain[app] = db
    db_manage.update_db(dbmain)

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
    for subproces in db['PROCESSED']:
        for subject in db['PROCESSED'][subproces][::-1]:
            if len_Running()<= vars_processing["max_nr_running_batches"]:
                if time_now() < max_batch_running:
                    if os.path.exists(os.path.join(SUBJECTS_DIR, subject)):
                        if subject not in db['RUNNING_JOBS']\
                        or not [i for i in db['RUNNING_JOBS'] if "err_"+subject in i]:
                            move_processed_subjects(subject, subproces, '')
                    else:
                        db['PROCESSED'][subproces].remove(subject)
                        if subject in db['RUNNING_JOBS']:
                            db['RUNNING_JOBS'].pop(subject, None)
    dbmain[app] = db
    db_manage.update_db(dbmain)


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


def time_now():
    time_elapsed = time.time() - t0
    return time.strftime("%H:%M:%S",time.gmtime(time_elapsed))


def time_max_running_get(batch_walltime,
                        time_2remove):
    batch_walltime_time_format = time.mktime(time.strptime(batch_walltime,"%H:%M:%S"))
    # remove a period of time in order to allow time to restart the pipeline:
    new_batch_walltime = time.localtime(batch_walltime_time_format - time_2remove)
    return time.strftime('%H:%M:%S',new_batch_walltime)


def run():

    global db_manage, dbmain, db, app, Procs, schedule, log, chk2, vars_app, vars_processing, vars_nimb, NIMB_HOME, NIMB_tmp, SUBJECTS_DIR, max_walltime, process_order, processing_env, t0, max_batch_running

    vars_app        = vars_local[app.upper()]
    vars_processing = vars_local["PROCESSING"]
    vars_nimb       = vars_local["NIMB_PATHS"]
    processing_env  = vars_local["PROCESSING"]["processing_env"]

    NIMB_HOME       = vars_nimb["NIMB_HOME"]
    NIMB_tmp        = vars_nimb["NIMB_tmp"]
    max_walltime    = vars_processing["max_walltime"]
    SUBJECTS_DIR    = vars_app["SUBJECTS_DIR"]
    Procs           = FSProcesses(vars_app["FREESURFER_HOME"], vars_app["version"])
    process_order   = ["registration"] + Procs.process_order()
    vars_app['process_order'] = process_order
    chk2            = CHECKER(atlas_definitions)

    version, _, _, _= fs_version(vars_app["FREESURFER_HOME"])
    if version != "7.3.2":
        chk2            = CHECKER(atlas_definitions, version)
    schedule        = Scheduler(vars_local)


    log.info('pipeline started')
    t0           = time.time()
    Update_running(NIMB_tmp, 1)

    log.info('reading database')
    db_manage = AppDBManage(vars_local, DEFAULT, atlas_definitions)
    dbmain = db_manage.get_db(app, vars_app)
    db = dbmain[app]

    log.info('NEW SUBJECTS searching:')
    db = db_manage.chk_new_subj(db, app, vars_app)
    dbmain[app] = db
    db_manage.update_db(dbmain)


    # extracting 40 minutes from the maximum time for the batch to run
    # since it is expected that less then 35 minutes will be required for the pipeline to perform all the steps
    # while the batch is running, and start new batch
    max_batch_running = time_max_running_get(vars_processing["batch_walltime"], 2400)

    count_run    = 0
    active_subjects = check_active_tasks(db)
    while active_subjects >0 and time_now() < max_batch_running:
        count_run += 1
        log.info('restarting run, '+str(count_run))
        log.info(f"elapsed time is: {time_now()}, max time is: {max_batch_running}")
        if count_run % 5 == 0:
            log.info('NEW SUBJECTS searching:')
            db = db_manage.chk_new_subj(db, app, vars_app)

            dbmain[app] = db
            db_manage.update_db(dbmain)
        loop_run()

        time_to_sleep = Count_TimeSleep()
        log.info('\n\nWAITING. \nNext run at: '+str(time.strftime("%H:%M",time.localtime(time.time()+time_to_sleep))))
        time_left = time.strftime("%H:%M:%S",time.gmtime(time.time() - t0 + time_to_sleep))
        if time_left < max_batch_running:
            print(f"!! time left {time_left}is less then allowed by scheduler: {max_batch_running}")
        time.sleep(time_to_sleep)

        active_subjects = check_active_tasks(db)

    if active_subjects == 0:
        Update_running(NIMB_tmp, 0)
        log.info('ALL TASKS FINISHED')
    else:
        cd_cmd = 'cd {}'.format(path.join(NIMB_HOME, 'processing', 'freesurfer'))
        cmd = f'{vars_processing["python3_run_cmd"]} crun.py'
        log.info(f'Sending new batch to scheduler with cd_cmd: {cd_cmd} ')
        schedule.submit_4_processing(cmd,'nimb_freesurfer','run',
                                     cd_cmd,
                                     activate_fs = False,
                                     python_load = True)


if __name__ == "__main__":

    app = 'freesurfer'
    from pathlib import Path
    import sys

    top = Path(__file__).resolve().parents[2]
    sys.path.append(str(top))

    from setup.get_vars import Get_Vars
    from distribution.logger import Log
    from distribution.distribution_definitions import DEFAULT
    from processing.atlases import atlas_definitions
    from classification.dcm2bids_helper import is_bids_format
    from processing.app_db import AppDBManage
    from processing.checker import CHECKER

    getvars = Get_Vars()
    vars_local = getvars.location_vars['local']
    log = Log(vars_local['NIMB_PATHS']['NIMB_tmp']).logger

    from processing.schedule_helper import Scheduler

    run()
