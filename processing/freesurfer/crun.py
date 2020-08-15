#!/bin/python
# 2020.08.04

print_all_subjects = False

from os import path, listdir, remove, rename, system, chdir, environ
import json

if path.isfile('vars.json'):
    with open('vars.json') as vars_json:
        vars = json.load(vars_json)
else:
    print('ERROR: vars.json file MISSING')


NIMB_HOME               = vars["NIMB_PATHS"]["NIMB_HOME"]
NIMB_tmp                = vars["NIMB_PATHS"]["NIMB_tmp"]
max_walltime            = vars["PROCESSING"]["max_walltime"]
SUBJECTS_DIR            = vars["FREESURFER"]["FS_SUBJECTS_DIR"]
process_order           = vars["FREESURFER"]["process_order"]



import time, shutil
from datetime import datetime, timedelta
import logging
import crunfs, cdb, cwalltime
from logger import Log

Log(NIMB_tmp)
log = logging.getLogger(__name__)


try:
    from pathlib import Path
except ImportError as e:
    log.info(e)


scheduler_params = {'NIMB_HOME'            : NIMB_HOME,
                    'NIMB_tmp'             : NIMB_tmp,
                    'SUBJECTS_DIR'         : SUBJECTS_DIR,
                    'text4_scheduler'      : vars["PROCESSING"]["text4_scheduler"],
                    'batch_walltime_cmd'   : vars["PROCESSING"]["batch_walltime_cmd"],
                    'batch_output_cmd'     : vars["PROCESSING"]["batch_output_cmd"],
                    'export_FreeSurfer_cmd': vars["FREESURFER"]["export_FreeSurfer_cmd"],
                    'source_FreeSurfer_cmd': vars["FREESURFER"]["source_FreeSurfer_cmd"],
                    'SUBMIT'               : vars["PROCESSING"]["SUBMIT"]}


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
    def brstem(_id): return 'segmentBS.sh {}'.format(_id) if vars["FREESURFER"]["freesurfer_version"]>6 else 'recon-all -s {} -brainstem-structures'.format(_id)
    def hip(_id): return 'segmentHA_T1.sh {}'.format(_id) if vars["FREESURFER"]["freesurfer_version"]>6 else 'recon-all -s {} -hippocampal-subfields-T1'.format(_id)
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
    cdb.Update_status_log(NIMB_tmp, ACTION+' '+process)

    lsr = db[ACTION][process].copy()

    for subjid in lsr:
        if subjid in db['RUNNING_JOBS']:
            status = Get_status_for_subjid_in_queue(subjid, all_running)
            if status == 'none':
                db[ACTION][process].remove(subjid)
                db['RUNNING_JOBS'].pop(subjid, None)
                if vars["FREESURFER"]["base_name"] in subjid:
                    log.info(' reading '+process+subjid+' subjid is long or base ')
                    cdb.Update_status_log(NIMB_tmp, ' reading '+process+subjid+' subjid is long or base ')
                    if crunfs.chkIsRunning(SUBJECTS_DIR, subjid):
                        log.info('    '+subjid+' '+process+' moving to ERROR because IsRunning present')
                        cdb.Update_status_log(NIMB_tmp, '    '+subjid+' '+process+' moving to ERROR because IsRunning present')
                        db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                        db['PROCESSED']['error_recon'].append(subjid)
                else:
                    if not crunfs.chkIsRunning(SUBJECTS_DIR, subjid) and crunfs.checks_from_runfs(SUBJECTS_DIR, process, subjid, vars["FREESURFER"]["freesurfer_version"], vars["FREESURFER"]["masks"]):
                        if process != process_order[-1]:
                            next_process = process_order[process_order.index(process)+1]
                            if not crunfs.checks_from_runfs(SUBJECTS_DIR, next_process, subjid, vars["FREESURFER"]["freesurfer_version"], vars["FREESURFER"]["masks"]):
                                db['DO'][next_process].append(subjid)
                                log.info('    '+subjid+' moving from '+ACTION+' '+process+' to DO '+next_process)
                                cdb.Update_status_log(NIMB_tmp, '    '+subjid+' moving from '+ACTION+' '+process+' to DO '+next_process)
                            else:
                                db[ACTION][next_process].append(subjid)
                                log.info('    '+subjid+' moving from '+ACTION+' '+process+' to '+ACTION+' '+next_process)
                                cdb.Update_status_log(NIMB_tmp, '    '+subjid+' moving from '+ACTION+' '+process+' to '+ACTION+' '+next_process)
                        else:
                            log.info('    '+subjid+' processing DONE')
                            cdb.Update_status_log(NIMB_tmp, '    '+subjid+' processing DONE')
                    else:
                        log.info('    '+subjid+' '+process+' moving to ERROR because status is: '+status+', and IsRunning is present')
                        cdb.Update_status_log(NIMB_tmp, '    '+subjid+' '+process+' moving to ERROR because status is: '+status+', and IsRunning is present')
                        db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                        db['PROCESSED']['error_'+process].append(subjid)
        else:
            log.info('    '+subjid+' NOT in RUNNING_JOBS')
            cdb.Update_status_log(NIMB_tmp, '    '+subjid+' NOT in RUNNING_JOBS')
            db[ACTION][process].remove(subjid)
            if not crunfs.chkIsRunning(SUBJECTS_DIR, subjid):
                if vars["FREESURFER"]["base_name"] in subjid:
                    log.info('    '+subjid+process+' subjid is long or base ')
                    cdb.Update_status_log(NIMB_tmp, '    '+subjid+process+' subjid is long or base ')
                    if not crunfs.checks_from_runfs(SUBJECTS_DIR, 'recon', subjid, vars["FREESURFER"]["freesurfer_version"], vars["FREESURFER"]["masks"]):
                        log.info('    '+subjid+' recon, moving to ERROR because not all files were created')
                        cdb.Update_status_log(NIMB_tmp, '    '+subjid+' recon, moving to ERROR because not all files were created')
                        db['PROCESSED']['error_recon'].append(subjid)
                else:
                    if crunfs.checks_from_runfs(SUBJECTS_DIR, process, subjid, vars["FREESURFER"]["freesurfer_version"], vars["FREESURFER"]["masks"]):
                        if process != process_order[-1]:
                            next_process = process_order[process_order.index(process)+1]
                            if not crunfs.checks_from_runfs(SUBJECTS_DIR, next_process, subjid, vars["FREESURFER"]["freesurfer_version"], vars["FREESURFER"]["masks"]):
                                db['DO'][next_process].append(subjid)
                                log.info('    '+subjid+' moving from '+ACTION+' '+process+' to DO '+next_process)
                                cdb.Update_status_log(NIMB_tmp, '    '+subjid+' moving from '+ACTION+' '+process+' to DO '+next_process)
                            else:
                                db[ACTION][next_process].append(subjid)
                                log.info('    '+subjid+' moving from '+ACTION+' '+process+' to '+ACTION+' '+next_process)
                                cdb.Update_status_log(NIMB_tmp, '    '+subjid+' moving from '+ACTION+' '+process+' to '+ACTION+' '+next_process)
                        else:
                            log.info('    '+subjid+' processing DONE')
                            cdb.Update_status_log(NIMB_tmp, '    '+subjid+' processing DONE')
                    else:
                        log.info('    '+subjid+' '+process+' moving to ERROR, because not all files were created')
                        cdb.Update_status_log(NIMB_tmp, '    '+subjid+' '+process+' moving to ERROR, because not all files were created')
                        db['PROCESSED']['error_'+process].append(subjid)
            else:
                log.info('    '+subjid+' '+process+' moving to ERROR because not in RUNNING_JOBS and IsRunning is present')
                cdb.Update_status_log(NIMB_tmp, '    '+subjid+' '+process+' moving to ERROR because not in RUNNING_JOBS and IsRunning is present')
                db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                db['PROCESSED']['error_'+process].append(subjid)
    db[ACTION][process].sort()
    cdb.Update_DB(db, NIMB_tmp)


def do(process):
    ACTION = 'DO'
    log.info(ACTION+' '+process)
    cdb.Update_status_log(NIMB_tmp, ACTION+' '+process)

    lsd = db[ACTION][process].copy()

    for subjid in lsd:
        cdb.Update_status_log(NIMB_tmp, '   '+subjid)
        if len_Running()<= vars["PROCESSING"]["max_nr_running_batches"]:
            db[ACTION][process].remove(subjid)
            if process == 'registration':
                if not crunfs.checks_from_runfs(SUBJECTS_DIR, 'registration',subjid, vars["FREESURFER"]["freesurfer_version"], vars["FREESURFER"]["masks"]):
                    t1_ls_f, flair_ls_f, t2_ls_f = cdb.get_registration_files(subjid, db, NIMB_HOME, NIMB_tmp, vars["FREESURFER"]["flair_t2_add"])
                    # job_id = crunfs.submit_4_processing(vars["PROCESSING"]["processing_env"], cmd, subjid, run, walltime)
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
                cdb.Update_status_log(NIMB_tmp, '                                   submited id: '+str(job_id))
            except Exception as e:
                log.info('        err in do: '+e)
                cdb.Update_status_log(NIMB_tmp, '        err in do: '+e)
    db[ACTION][process].sort()
    cdb.Update_DB(db, NIMB_tmp)


def check_error():
    log.info('ERROR checking')
    cdb.Update_status_log(NIMB_tmp, 'ERROR checking')

    for process in process_order:
        if db['PROCESSED']['error_'+process]:
            lserr = db['PROCESSED']['error_'+process].copy()
            for subjid in lserr:
                log.info('    '+subjid)
                cdb.Update_status_log(NIMB_tmp, '    '+subjid)
                if subjid not in db["ERROR_QUEUE"] and path.exists(path.join(SUBJECTS_DIR, subjid)): #path.exists was added due to moving the subjects too early; requires adjustment
                    crunfs.IsRunning_rm(SUBJECTS_DIR, subjid)
                    log.info('        checking the recon-all-status.log for error for: '+process)
                    cdb.Update_status_log(NIMB_tmp, '        checking the recon-all-status.log for error for: '+process)
                    crunfs.chkreconf_if_without_error(NIMB_tmp, subjid, SUBJECTS_DIR)
                    log.info('        checking if all files were created for: '+process)
                    cdb.Update_status_log(NIMB_tmp, '        checking if all files were created for: '+process)
                    if not crunfs.checks_from_runfs(SUBJECTS_DIR, process, subjid, vars["FREESURFER"]["freesurfer_version"], vars["FREESURFER"]["masks"]):
                            log.info('            some files were not created and recon-all-status has errors.')
                            cdb.Update_status_log(NIMB_tmp, '            some files were not created and recon-all-status has errors.')
                            fs_error = crunfs.fs_find_error(subjid, SUBJECTS_DIR, NIMB_tmp)
                            solved = False
                            if fs_error:
                                solve = crunfs.solve_error(subjid, fs_error, SUBJECTS_DIR, NIMB_tmp)
                                if solve == 'continue':
                                    solved = True
                                    db['PROCESSED']['error_'+process].remove(subjid)
                                    db['DO'][process].append(subjid)
                                    log.info('        moving from error_'+process+' to DO '+process)
                                    cdb.Update_status_log(NIMB_tmp, '        moving from error_'+process+' to DO '+process)
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
                                        log.info('        		removing '+subjid+' from '+SUBJECTS_DIR)
                                        cdb.Update_status_log(NIMB_tmp, '        		removing '+subjid+' from '+SUBJECTS_DIR)
                                        system('rm -r '+path.join(SUBJECTS_DIR, subjid))
                                        log.info('        moving from error_'+process+' to RUNNING registration')
                                        cdb.Update_status_log(NIMB_tmp, '        moving from error_'+process+' to RUNNING registration')
                                    else:
                                        log.info('            solved: '+solve+' but subjid is missing from db[REGISTRATION]')
                                        cdb.Update_status_log(NIMB_tmp, '            solved: '+solve+' but subjid is missing from db[REGISTRATION]')
                                else:
                                    new_name = 'error_'+fs_error+'_'+subjid
                                    log.info('            not solved')
                                    cdb.Update_status_log(NIMB_tmp, '            not solved')
                            else:
                                new_name = 'error_'+process+'_'+subjid
                            if not solved:
                                log.info('            Excluding '+subjid+' from pipeline')
                                cdb.Update_status_log(NIMB_tmp, '            Excluding '+subjid+' from pipeline')
                                _id, _ = cdb.get_id_long(subjid, db['LONG_DIRS'], vars["FREESURFER"]["base_name"], vars["FREESURFER"]["long_name"])
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
                                            cdb.Update_status_log(NIMB_tmp, '        missing from db[REGISTRATION]')
                                    except Exception as e:
                                        log.info('        ERROR, id not found in LONG_DIRS; '+str(e))
                                        cdb.Update_status_log(NIMB_tmp, '        ERROR, id not found in LONG_DIRS; '+str(e))
                                else:
                                    log.info('        ERROR, '+subjid+' is absent from LONG_DIRS')
                                    cdb.Update_status_log(NIMB_tmp, '        ERROR, '+subjid+' is absent from LONG_DIRS')
                                move_processed_subjects(subjid, 'error_'+process, new_name)
                    else:
                            log.info('            all files were created for process: '+process)
                            cdb.Update_status_log(NIMB_tmp, '            all files were created for process: '+process)
                            db['PROCESSED']['error_'+process].remove(subjid)
                            db['RUNNING'][process].append(subjid)
                            log.info('        moving from error_'+process+' to RUNNING '+process)
                            cdb.Update_status_log(NIMB_tmp, '        moving from error_'+process+' to RUNNING '+process)
                else:
                    if subjid in db["ERROR_QUEUE"]:
                        log.info('    '+db['ERROR_QUEUE'][subjid]+' '+str(format(datetime.now(), "%Y%m%d_%H%M")))
                        cdb.Update_status_log(NIMB_tmp, '    '+db['ERROR_QUEUE'][subjid]+' '+str(format(datetime.now(), "%Y%m%d_%H%M")))
                        if db['ERROR_QUEUE'][subjid] < str(format(datetime.now(), "%Y%m%d_%H%M")):
                            log.info('    removing from ERROR_QUEUE')
                            cdb.Update_status_log(NIMB_tmp, '    removing from ERROR_QUEUE')
                            db['ERROR_QUEUE'].pop(subjid, None)
                    else:
                        log.info('    not in SUBJECTS_DIR')
                        cdb.Update_status_log(NIMB_tmp, '    not in SUBJECTS_DIR')
                        db['PROCESSED']['error_'+process].remove(subjid)
                db['PROCESSED']['error_'+process].sort()
                cdb.Update_DB(db, NIMB_tmp)



def long_check_groups(_id):
    ls = db['LONG_DIRS'][_id]
    LONG_TPS = db['LONG_TPS'][_id]
    if vars["FREESURFER"]["DO_LONG"] == 1 and len(LONG_TPS)>1:
        All_cross_ids_done = list()
        for ses in LONG_TPS:
            if _id+ses in ls and crunfs.checks_from_runfs(SUBJECTS_DIR, process_order[-1], _id+ses, vars["FREESURFER"]["freesurfer_version"], vars["FREESURFER"]["masks"]):
                All_cross_ids_done.append(_id+ses)

        if len(All_cross_ids_done) == len(LONG_TPS):
            base_f = _id+vars["FREESURFER"]["base_name"]
            if base_f in ls:
                if base_f not in db['RUNNING']['recon'] and base_f not in db['PROCESSED']['error_recon'] and not crunfs.chkIsRunning(SUBJECTS_DIR, base_f):
                    if crunfs.checks_from_runfs(SUBJECTS_DIR, 'recon', base_f, vars["FREESURFER"]["freesurfer_version"], vars["FREESURFER"]["masks"]):
                        All_long_ids_done = list()
                        for ses in LONG_TPS:
                            long_f = _id+ses+'.long.'+_id+vars["FREESURFER"]["base_name"]
                            if long_f not in ls:
                                job_id = crunfs.makesubmitpbs(Get_cmd.reclong(_id+ses, _id+vars["FREESURFER"]["base_name"]), _id+ses, 'reclong', cwalltime.Get_walltime('reclong'), scheduler_params)
                                db['RUNNING_JOBS'][long_f] = job_id
                                db['RUNNING']['recon'].append(long_f)
                                db['LONG_DIRS'][_id].append(long_f)
                            elif crunfs.checks_from_runfs(SUBJECTS_DIR, 'registration',long_f, vars["FREESURFER"]["freesurfer_version"], vars["FREESURFER"]["masks"]):
                                if crunfs.checks_from_runfs(SUBJECTS_DIR, 'recon', long_f, vars["FREESURFER"]["freesurfer_version"], vars["FREESURFER"]["masks"]):
                                    All_long_ids_done.append(long_f)
                                else:
                                    log.info(long_f+' moving to error_recon')
                                    cdb.Update_status_log(NIMB_tmp, long_f+' moving to error_recon')
                                    db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                                    db['PROCESSED']['error_recon'].append(long_f)
                            else:
                                log.info(long_f+' moving to error_recon')
                                cdb.Update_status_log(NIMB_tmp, long_f+' moving to error_recon')
                                db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                                db['PROCESSED']['error_recon'].append(long_f)

                        if len(All_long_ids_done) == len(LONG_TPS):
                            log.info(_id+' moving to cp2local')
                            cdb.Update_status_log(NIMB_tmp, _id+' moving to cp2local')
                            for subjid in ls:
                                log.info('moving '+subjid+' cp2local from LONG')
                                cdb.Update_status_log(NIMB_tmp, 'moving '+subjid+' cp2local from LONG')
                                db['PROCESSED']['cp2local'].append(subjid)
                            db['LONG_DIRS'].pop(_id, None)
                            db['LONG_TPS'].pop(_id, None)
                            if subjid in db['REGISTRATION']:
                                db['REGISTRATION'].pop(subjid, None)
                            if subjid in db['RUNNING_JOBS']:
                                db['RUNNING_JOBS'].pop(subjid, None)
                            else:
                                log.info('        missing from db[REGISTRATION]')
                                cdb.Update_status_log(NIMB_tmp, '        missing from db[REGISTRATION]')
                            log.info('        '+_id+'moved to cp2local')
                            cdb.Update_status_log(NIMB_tmp, '        '+_id+'moved to cp2local')
                    else:
                        log.info(base_f+' moving to error_recon, step 8')
                        cdb.Update_status_log(NIMB_tmp, base_f+' moving to error_recon, step 8')
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
                if crunfs.checks_from_runfs(SUBJECTS_DIR, 'registration', subjid, vars["FREESURFER"]["freesurfer_version"], vars["FREESURFER"]["masks"]):
                   if crunfs.checks_from_runfs(SUBJECTS_DIR, process_order[-1], subjid, vars["FREESURFER"]["freesurfer_version"], vars["FREESURFER"]["masks"]):
                        log.info('            last process done '+process_order[-1])
                        cdb.Update_status_log(NIMB_tmp, '            last process done '+process_order[-1])
                        if subjid in db['RUNNING'][process_order[-1]]:
                            db['RUNNING'][process_order[-1]].remove(subjid)
                        if crunfs.chk_if_all_done(SUBJECTS_DIR, subjid, process_order, NIMB_tmp, vars["FREESURFER"]["freesurfer_version"], vars["FREESURFER"]["masks"]):
                            log.info('            all processes done, moving to CP2LOCAL')
                            cdb.Update_status_log(NIMB_tmp, '            all processes done, moving to CP2LOCAL')
                            db['PROCESSED']['cp2local'].append(subjid)
                            db['LONG_DIRS'].pop(_id, None)
                            db['LONG_TPS'].pop(_id, None)
                            if subjid in db['REGISTRATION']:
                                db['REGISTRATION'].pop(subjid, None)
                            else:
                                log.info('        missing from db[REGISTRATION]')
                                cdb.Update_status_log(NIMB_tmp,'        missing from db[REGISTRATION]')
                        else:
                            db['PROCESSED']['error_'+process_order[1]].append(subjid)
                else:
                    log.info('        '+subjid+' was not registered')
                    cdb.Update_status_log(NIMB_tmp, '        '+subjid+' was not registered')
                    if subjid not in db['DO']['registration'] and subjid not in db['RUNNING']['registration']:
                        db['LONG_DIRS'].pop(_id, None)
                        db['LONG_TPS'].pop(_id, None)
                        if subjid in db['REGISTRATION']:
                            db['REGISTRATION'].pop(subjid, None)
                        else:
                            log.info('        missing from db[REGISTRATION]')
                            cdb.Update_status_log(NIMB_tmp, '        missing from db[REGISTRATION]')
    cdb.Update_DB(db, NIMB_tmp)



def move_processed_subjects(subject, db_source, new_name):
    file_mrparams = path.join(NIMB_tmp,'mriparams',subject+'_mrparams')
    if path.isfile(file_mrparams):
        shutil.move(file_mrparams, path.join(SUBJECTS_DIR, subject, 'stats'))
    log.info('    '+subject+' copying from '+db_source)
    cdb.Update_status_log(NIMB_tmp, '    '+subject+' copying from '+db_source)
    size_src = sum(f.stat().st_size for f in Path(path.join(SUBJECTS_DIR, subject)).glob('**/*') if f.is_file())
    if not new_name:
        shutil.copytree(path.join(SUBJECTS_DIR, subject), path.join(vars["NIMB_PATHS"]["NIMB_PROCESSED_FS"], subject))
        size_dst = sum(f.stat().st_size for f in Path(path.join(vars["NIMB_PATHS"]["NIMB_PROCESSED_FS"], subject)).glob('**/*') if f.is_file())
        if size_src == size_dst:
            db['PROCESSED'][db_source].remove(subject)
            cdb.Update_DB(db, NIMB_tmp)
            log.info('    copied correctly, removing from SUBJECTS_DIR')
            cdb.Update_status_log(NIMB_tmp, '    copied correctly, removing from SUBJECTS_DIR')
            shutil.rmtree(path.join(SUBJECTS_DIR, subject))
            if vars["PROCESSING"]["archive_processed"] == 1:
                log.info('        archiving ...')
                cdb.Update_status_log(NIMB_tmp, '        archiving ...')
                chdir(vars["NIMB_PATHS"]["NIMB_PROCESSED_FS"])
                system('zip -r -q -m '+subject+'.zip '+subject)
        else:
            log.info('        ERROR in moving, not moved correctly '+str(size_src)+' '+str(size_dst))
            cdb.Update_status_log(NIMB_tmp, '        ERROR in moving, not moved correctly '+str(size_src)+' '+str(size_dst))
            shutil.rmtree(path.join(vars["NIMB_PATHS"]["NIMB_PROCESSED_FS"], subject))
    else:
        log.info('        renaming '+subject+' to '+new_name+', moving to processed error')
        cdb.Update_status_log(NIMB_tmp, '        renaming '+subject+' to '+new_name+', moving to processed error')
        shutil.move(path.join(SUBJECTS_DIR, subject), path.join(vars["NIMB_PATHS"]["NIMB_PROCESSED_FS_error"], new_name))
        db['PROCESSED'][db_source].remove(subject)
    log.info('        moving DONE')
    cdb.Update_status_log(NIMB_tmp, '        moving DONE')



def run():
    cdb.Update_DB(db, NIMB_tmp)
    all_running = cdb.get_batch_jobs_status(vars["USER"]["user"], vars["USER"]["users_list"])

    for process in process_order[::-1]:
        if len(db['RUNNING'][process])>0:
            running(process,all_running)
        if len(db['DO'][process])>0:
            do(process)

    check_error()

    log.info('CHECKING subjects')
    cdb.Update_status_log(NIMB_tmp, 'CHECKING subjects')
    ls_long_dirs = list()
    for key in db['LONG_DIRS']:
            ls_long_dirs.append(key)

    for _id in ls_long_dirs:
        if print_all_subjects:
            log.info('    '+_id+': '+str(db['LONG_DIRS'][_id]))
            cdb.Update_status_log(NIMB_tmp, '    '+_id+': '+str(db['LONG_DIRS'][_id]))
        long_check_groups(_id)


    log.info('MOVING the processed')
    cdb.Update_status_log(NIMB_tmp, 'MOVING the processed')
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
    cdb.Update_status_log(NIMB_tmp, '\n                 '+str(active_subjects)+'\n                 '+str(error)+' error')
    return active_subjects



def  len_Running():
    len_Running = 0
    for process in db['RUNNING']:
        len_Running = len_Running+len(db['RUNNING'][process])
    return len_Running


def Count_TimeSleep():
    time2sleep = 600 # 10 minutes
    if len_Running() >= vars["PROCESSING"]["max_nr_running_batches"]:
        log.info('running: '+str(len_Running())+' max: '+str(vars["PROCESSING"]["max_nr_running_batches"]))
        cdb.Update_status_log(NIMB_tmp, 'running: '+str(len_Running())+' max: '+str(vars["PROCESSING"]["max_nr_running_batches"]))
        time2sleep = 1800 # 30 minutes
    return time2sleep


if crunfs.FS_ready(SUBJECTS_DIR):
    print('updating status')

    t0 = time.time()
    time_elapsed = 0
    count_run = 0

    log.info('pipeline started')
    cdb.Update_status_log(NIMB_tmp, 'pipeline started')
    cdb.Update_running(NIMB_HOME, vars["USER"]["user"], 1)

    log.info('reading database')
    cdb.Update_status_log(NIMB_tmp, 'reading database')
    db = cdb.Get_DB(NIMB_HOME, NIMB_tmp, process_order)

    log.info('NEW SUBJECTS searching:')
    cdb.Update_status_log(NIMB_tmp, 'NEW SUBJECTS searching:')
    db = cdb.Update_DB_new_subjects_and_SUBJECTS_DIR(NIMB_tmp, SUBJECTS_DIR,db, process_order, vars["FREESURFER"]["base_name"], vars["FREESURFER"]["long_name"], vars["FREESURFER"]["freesurfer_version"], vars["FREESURFER"]["masks"])
    cdb.Update_DB(db, NIMB_tmp)
    active_subjects = check_active_tasks(db)

    # extracting 40 minutes from the maximum time for the batch to run
    # since it is expected that less then 35 minutes will be required for the pipeline to perform all the steps
    # while the batch is running, and start new batch
    max_batch_running = time.strftime('%H:%M:%S',time.localtime(time.mktime(time.strptime(vars["PROCESSING"]["batch_walltime"],"%H:%M:%S"))-2400))

    while active_subjects >0 and time.strftime("%H:%M:%S",time.gmtime(time_elapsed)) < max_batch_running:
        count_run += 1
        log.info('restarting run, '+str(count_run))
        log.info('elapsed time: '+time.strftime("%H:%M",time.gmtime(time_elapsed))+' max walltime: '+vars["PROCESSING"]["batch_walltime"][:-6])
        cdb.Update_status_log(NIMB_tmp, 'restarting run, '+str(count_run))
        cdb.Update_status_log(NIMB_tmp, 'elapsed time: '+time.strftime("%H:%M",time.gmtime(time_elapsed))+' max walltime: '+vars["PROCESSING"]["batch_walltime"][:-6])
        if count_run % 5 == 0:
            log.info('NEW SUBJECTS searching:')
            cdb.Update_status_log(NIMB_tmp, 'NEW SUBJECTS searching:')
            db = cdb.Update_DB_new_subjects_and_SUBJECTS_DIR(NIMB_tmp, SUBJECTS_DIR, db, process_order, vars["FREESURFER"]["base_name"], vars["FREESURFER"]["long_name"], vars["FREESURFER"]["freesurfer_version"], vars["FREESURFER"]["masks"])
            cdb.Update_DB(db, NIMB_tmp)
        run()

        time_to_sleep = Count_TimeSleep()
        log.info('\n\nWAITING. \nNext run at: '+str(time.strftime("%H:%M",time.localtime(time.time()+time_to_sleep))))
        cdb.Update_status_log(NIMB_tmp, '\n\nWAITING. \nNext run at: '+str(time.strftime("%H:%M",time.localtime(time.time()+time_to_sleep))))

        try:
            shutil.copy(path.join(NIMB_tmp,'db.json'),path.join(NIMB_HOME,'tmp','db.json'))
            system('chmod 777 '+path.join(NIMB_HOME,'processing','freesurfer','db.json'))
        except Exception as e:
            log.info(str(e))
            cdb.Update_status_log(NIMB_tmp, str(e))

        time_elapsed = time.time() - t0
#        if time.strftime("%H:%M:%S",time.gmtime(time_elapsed+time_to_sleep)) < max_batch_running:
#                  batch gets closed by the scheduler, trying to calculate time left until batch is finished,
#                  line if was creating an infinitie loop, without the time.sleep, might have been related to missing :%S in strpftime
#                  commented now, needs to be checked

        time.sleep(time_to_sleep)

        time_elapsed = time.time() - t0
        active_subjects = check_active_tasks(db)

    if active_subjects == 0:
        cdb.Update_running(NIMB_tmp, vars["USER"]["user"], 0)
        log.info('ALL TASKS FINISHED')
        cdb.Update_status_log(NIMB_tmp, 'ALL TASKS FINISHED')
    else:
        log.info('Sending new batch to scheduler')
        cdb.Update_status_log(NIMB_tmp, 'Sending new batch to scheduler')
        chdir(NIMB_HOME)
        system('python processing/freesurfer/start_fs_pipeline.py')


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

