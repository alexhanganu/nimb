#!/bin/python
# 2020.08.04


'''
add FS QA tools to rm scans with low SNR (Koh et al 2017)
https://surfer.nmr.mgh.harvard.edu/fswiki/QATools
'''
print_all_subjects = False


from os import path, listdir, remove, rename, system, chdir, environ
import time, shutil
import json
from datetime import datetime, timedelta


if path.isfile('vars.json'):
    with open('vars.json') as vars_json:
        vars = json.load(vars_json)
else:
    print('ERROR: vars.json file MISSING')
try:
    from pathlib import Path
except ImportError as e:
    cdb.Update_status_log(e)

cuser                   = vars["USER"]["user"]
cusers_list             = vars["USER"]["users_list"]
nimb_dir                = vars["NIMB_PATHS"]["NIMB_HOME"]
NIMB_HOME               = vars["NIMB_PATHS"]["NIMB_HOME"]
nimb_scratch_dir        = vars["NIMB_PATHS"]["NIMB_tmp"]
NIMB_tmp                = vars["NIMB_PATHS"]["NIMB_tmp"]
processed_SUBJECTS_DIR  = vars["NIMB_PATHS"]["NIMB_PROCESSED_FS"]
NIMB_PROCESSED_FS_error = vars["NIMB_PATHS"]["NIMB_PROCESSED_FS_error"]

SUBMIT                  = vars["PROCESSING"]["SUBMIT"]
processing_env          = vars["PROCESSING"]["processing_env"]
max_nr_running_batches  = vars["PROCESSING"]["max_nr_running_batches"]
text4_scheduler         = vars["PROCESSING"]["text4_scheduler"]
batch_walltime_cmd      = vars["PROCESSING"]["batch_walltime_cmd"]
batch_walltime          = vars["PROCESSING"]["batch_walltime"]
batch_output_cmd        = vars["PROCESSING"]["batch_output_cmd"]
max_walltime            = vars["PROCESSING"]["max_walltime"]
archive_processed       = vars["PROCESSING"]["archive_processed"]

freesurfer_version      = vars["FREESURFER"]["freesurfer_version"]
SUBJECTS_DIR            = vars["FREESURFER"]["FS_SUBJECTS_DIR"]
export_FreeSurfer_cmd   = vars["FREESURFER"]["export_FreeSurfer_cmd"]
source_FreeSurfer_cmd   = vars["FREESURFER"]["source_FreeSurfer_cmd"]
process_order           = vars["FREESURFER"]["process_order"]
flair_t2_add            = vars["FREESURFER"]["flair_t2_add"]
masks                   = vars["FREESURFER"]["masks"]
DO_LONG                 = vars["FREESURFER"]["DO_LONG"]
base_name               = vars["FREESURFER"]["base_name"]
long_name               = vars["FREESURFER"]["long_name"]

if DO_LONG == 1:
    DO_LONG = True
else:
    DO_LONG = False
if flair_t2_add == 1:
    flair_t2_add = True
else:
    flair_t2_add = False
if SUBMIT == 1:
    SUBMIT = True
else:
    SUBMIT = False
if archive_processed == 1:
    archive_processed = True
else:
    archive_processed = False



import crunfs, cdb, cwalltime


print('SUBMITTING is: ', SUBMIT)

scheduler_params = {'NIMB_HOME'            : nimb_dir,
                    'NIMB_tmp'             : nimb_scratch_dir,
                    'SUBJECTS_DIR'         : SUBJECTS_DIR,
                    'text4_scheduler'      : text4_scheduler,
                    'batch_walltime_cmd'   : batch_walltime_cmd,
                    'batch_output_cmd'     : batch_output_cmd,
                    'export_FreeSurfer_cmd': export_FreeSurfer_cmd,
                    'source_FreeSurfer_cmd': source_FreeSurfer_cmd,
                    'SUBMIT'               : SUBMIT}


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
    def brstem(_id): return 'segmentBS.sh {}'.format(_id) if freesurfer_version>6 else 'recon-all -s {} -brainstem-structures'.format(_id)
    def hip(_id): return 'segmentHA_T1.sh {}'.format(_id) if freesurfer_version>6 else 'recon-all -s {} -hippocampal-subfields-T1'.format(_id)
    def tha(_id): return "segmentThalamicNuclei.sh {}".format(_id)
    def masks(_id): return "cd "+path.join(nimb_dir,'processing','freesurfer')+"\npython run_masks.py {}".format(_id)



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
    cdb.Update_status_log(nimb_scratch_dir, ACTION+' '+process)

    lsr = db[ACTION][process].copy()

    for subjid in lsr:
        if subjid in db['RUNNING_JOBS']:
            status = Get_status_for_subjid_in_queue(subjid, all_running)
            if status == 'none':
                db[ACTION][process].remove(subjid)
                db['RUNNING_JOBS'].pop(subjid, None)
                if base_name in subjid:
                    cdb.Update_status_log(nimb_scratch_dir, ' reading '+process+subjid+' subjid is long or base ')
                    if crunfs.chkIsRunning(SUBJECTS_DIR, subjid):
                        cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' '+process+' moving to ERROR because IsRunning present')
                        db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                        db['PROCESSED']['error_recon'].append(subjid)
                else:
                    if not crunfs.chkIsRunning(SUBJECTS_DIR, subjid) and crunfs.checks_from_runfs(SUBJECTS_DIR, process, subjid, freesurfer_version, masks):
                        if process != process_order[-1]:
                            next_process = process_order[process_order.index(process)+1]
                            if not crunfs.checks_from_runfs(SUBJECTS_DIR, next_process, subjid, freesurfer_version, masks):
                                db['DO'][next_process].append(subjid)
                                cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' moving from '+ACTION+' '+process+' to DO '+next_process)
                            else:
                                db[ACTION][next_process].append(subjid)
                                cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' moving from '+ACTION+' '+process+' to '+ACTION+' '+next_process)
                        else:
                            cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' processing DONE')
                    else:
                        cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' '+process+' moving to ERROR because status is: '+status+', and IsRunning is present')
                        db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                        db['PROCESSED']['error_'+process].append(subjid)
        else:
            cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' NOT in RUNNING_JOBS')
            db[ACTION][process].remove(subjid)
            if not crunfs.chkIsRunning(SUBJECTS_DIR, subjid):
                if base_name in subjid:
                    cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+process+' subjid is long or base ')
                    if not crunfs.checks_from_runfs(SUBJECTS_DIR, 'recon', subjid, freesurfer_version, masks):
                        cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' recon, moving to ERROR because not all files were created')
                        db['PROCESSED']['error_recon'].append(subjid)
                else:
                    if crunfs.checks_from_runfs(SUBJECTS_DIR, process, subjid, freesurfer_version, masks):
                        if process != process_order[-1]:
                            next_process = process_order[process_order.index(process)+1]
                            if not crunfs.checks_from_runfs(SUBJECTS_DIR, next_process, subjid, freesurfer_version, masks):
                                db['DO'][next_process].append(subjid)
                                cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' moving from '+ACTION+' '+process+' to DO '+next_process)
                            else:
                                db[ACTION][next_process].append(subjid)
                                cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' moving from '+ACTION+' '+process+' to '+ACTION+' '+next_process)
                        else:
                            cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' processing DONE')
                    else:
                        cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' '+process+' moving to ERROR, because not all files were created')
                        db['PROCESSED']['error_'+process].append(subjid)
            else:
                cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' '+process+' moving to ERROR because not in RUNNING_JOBS and IsRunning is present')
                db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                db['PROCESSED']['error_'+process].append(subjid)
    db[ACTION][process].sort()
    cdb.Update_DB(db, nimb_scratch_dir)



def do(process):
    ACTION = 'DO'
    cdb.Update_status_log(nimb_scratch_dir, ACTION+' '+process)

    lsd = db[ACTION][process].copy()

    for subjid in lsd:
        cdb.Update_status_log(nimb_scratch_dir, '   '+subjid)
        if len_Running()<= max_nr_running_batches:
            db[ACTION][process].remove(subjid)
            if process == 'registration':
                if not crunfs.checks_from_runfs(SUBJECTS_DIR, 'registration',subjid, freesurfer_version, masks):
                    t1_ls_f, flair_ls_f, t2_ls_f = cdb.get_registration_files(subjid, db, nimb_dir, nimb_scratch_dir, flair_t2_add)
                    # job_id = crunfs.submit_4_processing(processing_env, cmd, subjid, run, walltime)
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
                cdb.Update_status_log(nimb_scratch_dir, '                                   submited id: '+str(job_id))
            except Exception as e:
                cdb.Update_status_log(nimb_scratch_dir, '        err in do: '+e)
    db[ACTION][process].sort()
    cdb.Update_DB(db, nimb_scratch_dir)


def check_error():
    cdb.Update_status_log(nimb_scratch_dir, 'ERROR checking')

    for process in process_order:
        if db['PROCESSED']['error_'+process]:
            lserr = db['PROCESSED']['error_'+process].copy()
            for subjid in lserr:
                cdb.Update_status_log(nimb_scratch_dir, '    '+subjid)
                if subjid not in db["ERROR_QUEUE"] and path.exists(path.join(SUBJECTS_DIR, subjid)): #path.exists was added due to moving the subjects too early; requires adjustment
                    crunfs.IsRunning_rm(SUBJECTS_DIR, subjid)
                    cdb.Update_status_log(nimb_scratch_dir, '        checking the recon-all-status.log for error for: '+process)
                    crunfs.chkreconf_if_without_error(NIMB_tmp, subjid, SUBJECTS_DIR)
                    cdb.Update_status_log(nimb_scratch_dir, '        checking if all files were created for: '+process)
                    if not crunfs.checks_from_runfs(SUBJECTS_DIR, process, subjid, freesurfer_version, masks):
                            cdb.Update_status_log(nimb_scratch_dir, '            some files were not created and recon-all-status has errors.')
                            fs_error = crunfs.fs_find_error(subjid, SUBJECTS_DIR, NIMB_tmp)
                            solved = False
                            if fs_error:
                                solve = crunfs.solve_error(subjid, fs_error, SUBJECTS_DIR, NIMB_tmp)
                                if solve == 'continue':
                                    solved = True
                                    db['PROCESSED']['error_'+process].remove(subjid)
                                    db['DO'][process].append(subjid)
                                    cdb.Update_status_log(nimb_scratch_dir, '        moving from error_'+process+' to DO '+process)
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
                                        cdb.Update_status_log(nimb_scratch_dir, '        		removing '+subjid+' from '+SUBJECTS_DIR)
                                        system('rm -r '+path.join(SUBJECTS_DIR, subjid))
                                        cdb.Update_status_log(nimb_scratch_dir, '        moving from error_'+process+' to RUNNING registration')
                                    else:
                                        cdb.Update_status_log(nimb_scratch_dir, '            solved: '+solve+' but subjid is missing from db[REGISTRATION]')
                                else:
                                    new_name = 'error_'+fs_error+'_'+subjid
                                    cdb.Update_status_log(nimb_scratch_dir, '            not solved')
                            else:
                                new_name = 'error_'+process+'_'+subjid
                            if not solved:
                                cdb.Update_status_log(nimb_scratch_dir, '            Excluding '+subjid+' from pipeline')
                                _id, _ = cdb.get_id_long(subjid, db['LONG_DIRS'], base_name, long_name)
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
                                            cdb.Update_status_log(nimb_scratch_dir, '        missing from db[REGISTRATION]')
                                    except Exception as e:
                                        cdb.Update_status_log(nimb_scratch_dir, '        ERROR, id not found in LONG_DIRS; '+str(e))
                                else:
                                    cdb.Update_status_log(nimb_scratch_dir, '        ERROR, '+subjid+' is absent from LONG_DIRS')
                                move_processed_subjects(subjid, 'error_'+process, new_name)
                    else:
                            cdb.Update_status_log(nimb_scratch_dir, '            all files were created for process: '+process)
                            db['PROCESSED']['error_'+process].remove(subjid)
                            db['RUNNING'][process].append(subjid)
                            cdb.Update_status_log(nimb_scratch_dir, '        moving from error_'+process+' to RUNNING '+process)
                else:
                    if subjid in db["ERROR_QUEUE"]:
                        cdb.Update_status_log(nimb_scratch_dir, '    '+db['ERROR_QUEUE'][subjid]+' '+str(format(datetime.now(), "%Y%m%d_%H%M")))
                        if db['ERROR_QUEUE'][subjid] < str(format(datetime.now(), "%Y%m%d_%H%M")):
                            cdb.Update_status_log(nimb_scratch_dir, '    removing from ERROR_QUEUE')
                            db['ERROR_QUEUE'].pop(subjid, None)
                    else:
                        cdb.Update_status_log(nimb_scratch_dir, '    not in SUBJECTS_DIR')
                        db['PROCESSED']['error_'+process].remove(subjid)
                db['PROCESSED']['error_'+process].sort()
                cdb.Update_DB(db, nimb_scratch_dir)



def long_check_groups(_id):
    ls = db['LONG_DIRS'][_id]
    LONG_TPS = db['LONG_TPS'][_id]
    if DO_LONG and len(LONG_TPS)>1:
        All_cross_ids_done = list()
        for ses in LONG_TPS:
            if _id+ses in ls and crunfs.checks_from_runfs(SUBJECTS_DIR, process_order[-1], _id+ses, freesurfer_version, masks):
                All_cross_ids_done.append(_id+ses)

        if len(All_cross_ids_done) == len(LONG_TPS):
            base_f = _id+base_name
            if base_f in ls:
                if base_f not in db['RUNNING']['recon'] and base_f not in db['PROCESSED']['error_recon'] and not crunfs.chkIsRunning(SUBJECTS_DIR, base_f):
                    if crunfs.checks_from_runfs(SUBJECTS_DIR, 'recon', base_f, freesurfer_version, masks):
                        All_long_ids_done = list()
                        for ses in LONG_TPS:
                            long_f = _id+ses+'.long.'+_id+base_name
                            if long_f not in ls:
                                job_id = crunfs.makesubmitpbs(Get_cmd.reclong(_id+ses, _id+base_name), _id+ses, 'reclong', cwalltime.Get_walltime('reclong'), scheduler_params)
                                db['RUNNING_JOBS'][long_f] = job_id
                                db['RUNNING']['recon'].append(long_f)
                                db['LONG_DIRS'][_id].append(long_f)
                            elif crunfs.checks_from_runfs(SUBJECTS_DIR, 'registration',long_f, freesurfer_version, masks):
                                if crunfs.checks_from_runfs(SUBJECTS_DIR, 'recon', long_f, freesurfer_version, masks):
                                    All_long_ids_done.append(long_f)
                                else:
                                    cdb.Update_status_log(nimb_scratch_dir, long_f+' moving to error_recon, STEP 6')
                                    db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                                    db['PROCESSED']['error_recon'].append(long_f)
                            else:
                                cdb.Update_status_log(nimb_scratch_dir, long_f+' moving to error_recon, step 7')
                                db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                                db['PROCESSED']['error_recon'].append(long_f)

                        if len(All_long_ids_done) == len(LONG_TPS):
                            cdb.Update_status_log(nimb_scratch_dir, _id+' moving to cp2local')
                            for subjid in ls:
                                cdb.Update_status_log(nimb_scratch_dir, 'moving '+subjid+' cp2local from LONG')
                                db['PROCESSED']['cp2local'].append(subjid)
                            db['LONG_DIRS'].pop(_id, None)
                            db['LONG_TPS'].pop(_id, None)
                            if subjid in db['REGISTRATION']:
                                db['REGISTRATION'].pop(subjid, None)
                            if subjid in db['RUNNING_JOBS']:
                                db['RUNNING_JOBS'].pop(subjid, None)
                            else:
                                cdb.Update_status_log(nimb_scratch_dir, '        missing from db[REGISTRATION]')
                            cdb.Update_status_log(nimb_scratch_dir, '        '+_id+'moved to cp2local')
                    else:
                        cdb.Update_status_log(nimb_scratch_dir, base_f+' moving to error_recon, step 8')
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
                if crunfs.checks_from_runfs(SUBJECTS_DIR, 'registration', subjid, freesurfer_version, masks):
                   if crunfs.checks_from_runfs(SUBJECTS_DIR, process_order[-1], subjid, freesurfer_version, masks):
                        if subjid in db['RUNNING'][process_order[-1]]:
                            db['RUNNING'][process_order[-1]].remove(subjid)
                        if chk_if_all_done(SUBJECTS_DIR, subjid, process_order, NIMB_tmp, freesurfer_version, masks):
                            cdb.Update_status_log(nimb_scratch_dir, '            last process done '+process_order[-1]+' moving to CP2LOCAL')
                            db['PROCESSED']['cp2local'].append(subjid)
                            db['LONG_DIRS'].pop(_id, None)
                            db['LONG_TPS'].pop(_id, None)
                            if subjid in db['REGISTRATION']:
                                db['REGISTRATION'].pop(subjid, None)
                            else:
                                cdb.Update_status_log(nimb_scratch_dir,'        missing from db[REGISTRATION]')
                        else:
                            db['PROCESSED']['error_'+process_order[1]].append(subjid)
                else:
                    cdb.Update_status_log(nimb_scratch_dir, '        '+subjid+' was not registered')
                    if subjid not in db['DO']['registration'] and subjid not in db['RUNNING']['registration']:
                        db['LONG_DIRS'].pop(_id, None)
                        db['LONG_TPS'].pop(_id, None)
                        if subjid in db['REGISTRATION']:
                            db['REGISTRATION'].pop(subjid, None)
                        else:
                            cdb.Update_status_log(nimb_scratch_dir, '        missing from db[REGISTRATION]')
    cdb.Update_DB(db, nimb_scratch_dir)



def move_processed_subjects(subject, db_source, new_name):
    file_mrparams = path.join(nimb_scratch_dir,'mriparams',subject+'_mrparams')
    if path.isfile(file_mrparams):
        shutil.move(file_mrparams, path.join(SUBJECTS_DIR, subject, 'stats'))
    cdb.Update_status_log(nimb_scratch_dir, '    '+subject+' copying from '+db_source)
    size_src = sum(f.stat().st_size for f in Path(path.join(SUBJECTS_DIR, subject)).glob('**/*') if f.is_file())
    if not new_name:
        shutil.copytree(path.join(SUBJECTS_DIR, subject), path.join(processed_SUBJECTS_DIR, subject))
        size_dst = sum(f.stat().st_size for f in Path(path.join(processed_SUBJECTS_DIR, subject)).glob('**/*') if f.is_file())
        if size_src == size_dst:
            db['PROCESSED'][db_source].remove(subject)
            cdb.Update_DB(db, nimb_scratch_dir)
            cdb.Update_status_log(nimb_scratch_dir, '    copied correctly, removing from SUBJECTS_DIR')
            shutil.rmtree(path.join(SUBJECTS_DIR, subject))
            if archive_processed:
                cdb.Update_status_log(nimb_scratch_dir, '        archiving ...')
                chdir(processed_SUBJECTS_DIR)
                system('zip -r -q -m '+subject+'.zip '+subject)
        else:
            cdb.Update_status_log(nimb_scratch_dir, '        ERROR in moving, not moved correctly '+str(size_src)+' '+str(size_dst))
            shutil.rmtree(path.join(processed_SUBJECTS_DIR, subject))
    else:
        cdb.Update_status_log(nimb_scratch_dir, '        renaming '+subject+' to '+new_name+', moving to processed error')
        shutil.move(path.join(SUBJECTS_DIR, subject), path.join(NIMB_PROCESSED_FS_error, new_name))
        db['PROCESSED'][db_source].remove(subject)
    cdb.Update_status_log(nimb_scratch_dir, '        moving DONE')



def run():
    cdb.Update_DB(db, nimb_scratch_dir)
    all_running = cdb.get_batch_jobs_status(cuser, cusers_list)

    for process in process_order[::-1]:
        if len(db['RUNNING'][process])>0:
            running(process,all_running)
        if len(db['DO'][process])>0:
            do(process)

    check_error()

    cdb.Update_status_log(nimb_scratch_dir, 'CHECKING subjects')
    ls_long_dirs = list()
    for key in db['LONG_DIRS']:
            ls_long_dirs.append(key)

    for _id in ls_long_dirs:
        if print_all_subjects:
            cdb.Update_status_log(nimb_scratch_dir, '    '+_id+': '+str(db['LONG_DIRS'][_id]))
        long_check_groups(_id)


    cdb.Update_status_log(nimb_scratch_dir, 'MOVING the processed')
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
    cdb.Update_status_log(nimb_scratch_dir, '\n                 '+str(active_subjects)+'\n                 '+str(error)+' error')
    return active_subjects



def  len_Running():
    len_Running = 0
    for process in db['RUNNING']:
        len_Running = len_Running+len(db['RUNNING'][process])
    return len_Running


def Count_TimeSleep():
    time2sleep = 600 # 10 minutes
    if len_Running() >= max_nr_running_batches:
        cdb.Update_status_log(nimb_scratch_dir, 'queue and running: '+str(len_Running())+' max: '+str(max_nr_running_batches))
        time2sleep = 1800 # 30 minutes
    return time2sleep


if crunfs.FS_ready(SUBJECTS_DIR):
    print('updating status')
    cdb.Update_status_log(nimb_scratch_dir, '\n\n\n\n========nimb version: ',True)

    t0 = time.time()
    time_elapsed = 0
    count_run = 0

    cdb.Update_status_log(nimb_scratch_dir, 'pipeline started')
    cdb.Update_running(nimb_dir, cuser, 1)

    cdb.Update_status_log(nimb_scratch_dir, 'reading database')
    db = cdb.Get_DB(nimb_dir, nimb_scratch_dir, process_order)

    cdb.Update_status_log(nimb_scratch_dir, 'NEW SUBJECTS searching:')
    db = cdb.Update_DB_new_subjects_and_SUBJECTS_DIR(nimb_scratch_dir, SUBJECTS_DIR,db, process_order, base_name, long_name, freesurfer_version, masks)
    cdb.Update_DB(db, nimb_scratch_dir)
    active_subjects = check_active_tasks(db)

    # extracting 40 minutes from the maximum time for the batch to run
    # since it is expected that less then 35 minutes will be required for the pipeline to perform all the steps
    # while the batch is running, and start new batch
    max_batch_running = time.strftime('%H:%M:%S',time.localtime(time.mktime(time.strptime(batch_walltime,"%H:%M:%S"))-2400))

    while active_subjects >0 and time.strftime("%H:%M:%S",time.gmtime(time_elapsed)) < max_batch_running:
        count_run += 1
        cdb.Update_status_log(nimb_scratch_dir, 'restarting run, '+str(count_run))
        cdb.Update_status_log(nimb_scratch_dir, 'elapsed time: '+time.strftime("%H:%M",time.gmtime(time_elapsed))+' max walltime: '+batch_walltime[:-6])
        if count_run % 5 == 0:
            cdb.Update_status_log(nimb_scratch_dir, 'NEW SUBJECTS searching:')
            db = cdb.Update_DB_new_subjects_and_SUBJECTS_DIR(nimb_scratch_dir, SUBJECTS_DIR, db, process_order, base_name, long_name, freesurfer_version, masks)
            cdb.Update_DB(db, nimb_scratch_dir)
        run()

        time_to_sleep = Count_TimeSleep()
        cdb.Update_status_log(nimb_scratch_dir, '\n\nWAITING. \nNext run at: '+str(time.strftime("%H:%M",time.localtime(time.time()+time_to_sleep))))

        try:
            shutil.copy(path.join(nimb_scratch_dir,'db.json'),path.join(NIMB_HOME,'processing','freesurfer','db.json'))
            system('chmod 777 '+path.join(NIMB_HOME,'processing','freesurfer','db.json'))
        except Exception as e:
            cdb.Update_status_log(nimb_scratch_dir, str(e))

        time_elapsed = time.time() - t0
#        if time.strftime("%H:%M:%S",time.gmtime(time_elapsed+time_to_sleep)) < max_batch_running:
#                  batch gets closed by the scheduler, trying to calculate time left until batch is finished,
#                  line if was creating an infinitie loop, without the time.sleep, might have been related to missing :%S in strpftime
#                  commented now, needs to be checked

        time.sleep(time_to_sleep)

        time_elapsed = time.time() - t0
        active_subjects = check_active_tasks(db)

    if active_subjects == 0:
        cdb.Update_running(nimb_scratch_dir, cuser, 0)
        cdb.Update_status_log(nimb_scratch_dir, 'ALL TASKS FINISHED')
    else:
        cdb.Update_status_log(nimb_scratch_dir, 'Sending new batch to scheduler')
        chdir(nimb_dir)
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

