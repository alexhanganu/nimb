#!/bin/python
# 2020.07.23

'''
add FS QA tools to rm scans with low SNR (Koh et al 2017)
https://surfer.nmr.mgh.harvard.edu/fswiki/QATools
'''
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

cuser                  = vars["USER"]["user"]
cusers_list            = vars["USER"]["users_list"]
nimb_dir               = vars["NIMB_PATHS"]["NIMB_HOME"]
NIMB_HOME              = vars["NIMB_PATHS"]["NIMB_HOME"]
nimb_scratch_dir       = vars["NIMB_PATHS"]["NIMB_tmp"]
NIMB_tmp               = vars["NIMB_PATHS"]["NIMB_tmp"]
processed_SUBJECTS_DIR = vars["NIMB_PATHS"]["NIMB_PROCESSED_FS"]

SUBMIT                 = vars["PROCESSING"]["SUBMIT"]
processing_env         = vars["PROCESSING"]["processing_env"]
max_nr_running_batches = vars["PROCESSING"]["max_nr_running_batches"]
text4_scheduler        = vars["PROCESSING"]["text4_scheduler"]
batch_walltime_cmd     = vars["PROCESSING"]["batch_walltime_cmd"]
batch_walltime         = vars["PROCESSING"]["batch_walltime"]
batch_output_cmd       = vars["PROCESSING"]["batch_output_cmd"]
max_walltime           = vars["PROCESSING"]["max_walltime"]
archive_processed      = vars["PROCESSING"]["archive_processed"]

freesurfer_version     = vars["FREESURFER"]["freesurfer_version"]
SUBJECTS_DIR           = vars["FREESURFER"]["FS_SUBJECTS_DIR"]
export_FreeSurfer_cmd  = vars["FREESURFER"]["export_FreeSurfer_cmd"]
source_FreeSurfer_cmd  = vars["FREESURFER"]["source_FreeSurfer_cmd"]
process_order          = vars["FREESURFER"]["process_order"]
flair_t2_add           = vars["FREESURFER"]["flair_t2_add"]
masks                  = vars["FREESURFER"]["masks"]
DO_LONG                = vars["FREESURFER"]["DO_LONG"]
base_name              = vars["FREESURFER"]["base_name"]
long_name              = vars["FREESURFER"]["long_name"]

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



def queue(process, all_running):
    '''
    logic: subject is Not in running - gets status none, is moved to running
            subject is PD in running - stays.
    '''
    ACTION = 'QUEUE'
    cdb.Update_status_log(nimb_scratch_dir, ACTION+' '+process)

#    lsq = list()
#    for val in db[ACTION][process]:
#        lsq.append(val)
    lsq = db[ACTION][process].copy()

    for subjid in lsq:
        status = 'none'
        # if subjid in db['RUNNING_JOBS']:
        status = Get_status_for_subjid_in_queue(subjid, all_running)
        # if crunfs.checks_from_runfs(SUBJECTS_DIR, 'registration',subjid, freesurfer_version, masks):
        if status =='R' or status == 'none':
                    cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' moving from '+ACTION+' to RUNNING '+process)
                    db[ACTION][process].remove(subjid)
                    db['RUNNING'][process].append(subjid)
            # else:
            #     cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+'    is NOT registered yet')
        # else:
        #     cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' queue, NOT in RUNNING_JOBS')
        #     cdb.Update_status_log(nimb_scratch_dir, '        moving from '+ACTION+' to RUNNING '+process)
        #     db[ACTION][process].remove(subjid)
        #     db['RUNNING'][process].append(subjid)
    db[ACTION][process].sort()
    cdb.Update_DB(db, nimb_scratch_dir)




def running(process, all_running):
    ACTION = 'RUNNING'
    cdb.Update_status_log(nimb_scratch_dir, ACTION+' '+process)

#    lsr = list()
#    for val in db[ACTION][process]:
#        lsr.append(val)	
    lsr = db[ACTION][process].copy()

    for subjid in lsr:
        if subjid in db['RUNNING_JOBS']:
            status = Get_status_for_subjid_in_queue(subjid, all_running)
            if status == 'none':
                db[ACTION][process].remove(subjid)
                db['RUNNING_JOBS'].pop(subjid, None)
                if base_name in subjid:
                    cdb.Update_status_log(nimb_scratch_dir, ' reading '+process+subjid+' subjid is long or base ')
                    if crunfs.chkIsRunning(SUBJECTS_DIR, subjid) or not crunfs.checks_from_runfs(SUBJECTS_DIR, 'recon', subjid, freesurfer_version, masks):
                        cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' '+process+' moving to ERROR, step 1')
#                        db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
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
                        cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' '+process+' moving to ERROR because status is: '+status+', and IsRunning is present, step 2')
#                        db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                        db['PROCESSED']['error_'+process].append(subjid)
        else:
            cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' NOT in RUNNING_JOBS')
            if not crunfs.chkIsRunning(SUBJECTS_DIR, subjid):
                db[ACTION][process].remove(subjid)
                if base_name in subjid:
                    cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+process+' subjid is long or base ')
                    if not crunfs.checks_from_runfs(SUBJECTS_DIR, 'recon', subjid, freesurfer_version, masks):
                        cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' recon, moving to ERROR, step 3')
#                        db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
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
                        cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' '+process+' moving to ERROR, step 4')
#                        db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                        db['PROCESSED']['error_'+process].append(subjid)
            else:
                db[ACTION][process].remove(subjid)
                cdb.Update_status_log(nimb_scratch_dir, '    '+subjid+' '+process+' moving to error_'+process+' step5')
#                db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                db['PROCESSED']['error_'+process].append(subjid)
    db[ACTION][process].sort()
    cdb.Update_DB(db, nimb_scratch_dir)



def do(process):
    ACTION = 'DO'
    cdb.Update_status_log(nimb_scratch_dir, ACTION+' '+process)

#    lsd = list()
#    for val in db[ACTION][process]:
#        lsd.append(val)
    lsd = db[ACTION][process].copy()

    for subjid in lsd:
        cdb.Update_status_log(nimb_scratch_dir, '   '+subjid)
        if get_len_Queue_Running()<= max_nr_running_batches:
            db[ACTION][process].remove(subjid)
            if process == 'registration':
                if not crunfs.checks_from_runfs(SUBJECTS_DIR, 'registration',subjid, freesurfer_version, masks):
                    t1_ls_f, flair_ls_f, t2_ls_f = cdb.get_registration_files(subjid, db, nimb_dir, nimb_scratch_dir, flair_t2_add)
# ================ START changing to submit_4_processing, in order to add tmux, started testing 20200722, ah
                    # job_id = crunfs.submit_4_processing(processing_env, cmd, subjid, run, walltime)
# ================ END
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
            db['QUEUE'][process].append(subjid)
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
                if path.exists(path.join(SUBJECTS_DIR,subjid)):
                    cdb.Update_status_log(nimb_scratch_dir, '        checking the recon-all-status.log for error and if all files were created for: '+process)
                    if not crunfs.chkreconf_if_without_error(NIMB_tmp, subjid, SUBJECTS_DIR):
                        if not crunfs.checks_from_runfs(SUBJECTS_DIR, process, subjid, freesurfer_version, masks):
# ================ START NEW CODE that needs to be verified, started testing 20200722, ah
                            cdb.Update_status_log(nimb_scratch_dir, '            some files were not created and recon-all-status has errors. Excluding subject from pipeline.')
                            fs_error = crunfs.fs_find_error(subjid, SUBJECTS_DIR, NIMB_tmp)
                            solved = False
                            if fs_error:
                                solve = crunfs.solve_error(subjid, fs_error, SUBJECTS_DIR)
                                if solve == 'continue':
                                    solved = True
                                    db['PROCESSED']['error_'+process].remove(subjid)
                                    db['RUNNING'][process].append(subjid)
                                    cdb.Update_status_log(nimb_scratch_dir, '        moving from error_'+process+' to RUNNING '+process)
                                elif subjid in db['REGISTRATION']:
                                    if solve == 'voxreg' or solve == 'errorigmgz':
                                        solved = True
                                        db['REGISTRATION'][subjid]['anat']['t1'] = db['REGISTRATION'][subjid]['anat']['t1'][:1]
                                        if 'flair' in db['REGISTRATION'][subjid]['anat']:
                                                db['REGISTRATION'][subjid]['anat'].pop('flair', None)
                                        if 't2' in db['REGISTRATION'][subjid]['anat']:
                                                db['REGISTRATION'][subjid]['anat'].pop('t2', None)
                                        db['PROCESSED']['error_'+process].remove(subjid)
                                        db['DO']["registration"].append(subjid)
                                        cdb.Update_status_log(nimb_scratch_dir, '        moving from error_'+process+' to RUNNING registratoin')
                                else:
                                    new_name = 'error_'+fs_error+'_'+subjid
                                    cdb.Update_status_log(nimb_scratch_dir, '            '+solve+', maybe subjid is missing from db[REGISTRATION]. Excluding subject from pipeline.')
                            else:
                                new_name = 'error_'+process+'_'+subjid
# ================ END NEW CODE that needs to be verified
                            if not solved:
                                if crunfs.chkIsRunning(SUBJECTS_DIR, subjid):
                                    cdb.Update_status_log(nimb_scratch_dir, '            removing IsRunning file')
                                    remove(path.join(SUBJECTS_DIR,subjid,'scripts','IsRunning.lh+rh'))
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
                            cdb.Update_status_log(nimb_scratch_dir, '            recon-all-status.log finished without error: '+process)
                            db['PROCESSED']['error_'+process].remove(subjid)
                            db['RUNNING'][process].append(subjid)
                            cdb.Update_status_log(nimb_scratch_dir, '        moving from error_'+process+' to RUNNING '+process)
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
                if base_f not in db['QUEUE']['recon'] and base_f not in db['PROCESSED']['error_recon'] and not crunfs.chkIsRunning(SUBJECTS_DIR, base_f):
                    if crunfs.checks_from_runfs(SUBJECTS_DIR, 'recon', base_f, freesurfer_version, masks):
                        All_long_ids_done = list()
                        for ses in LONG_TPS:
                            long_f = _id+ses+'.long.'+_id+base_name
                            if long_f not in ls:
                                job_id = crunfs.makesubmitpbs(Get_cmd.reclong(_id+ses, _id+base_name), _id+ses, 'reclong', cwalltime.Get_walltime('reclong'), scheduler_params)
                                db['RUNNING_JOBS'][long_f] = job_id
                                db['QUEUE']['recon'].append(long_f)
                                db['LONG_DIRS'][_id].append(long_f)
                            elif crunfs.checks_from_runfs(SUBJECTS_DIR, 'registration',long_f, freesurfer_version, masks):
                                if crunfs.checks_from_runfs(SUBJECTS_DIR, 'recon', long_f, freesurfer_version, masks):
                                    All_long_ids_done.append(long_f)
                                else:
                                    cdb.Update_status_log(nimb_scratch_dir, long_f+' moving to error_recon, STEP 6')
#                                    db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                                    db['PROCESSED']['error_recon'].append(long_f)
                            else:
                                cdb.Update_status_log(nimb_scratch_dir, long_f+' moving to error_recon, step 7')
#                                db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                                db['PROCESSED']['error_recon'].append(long_f)

                        if len(All_long_ids_done) == len(LONG_TPS):
                            cdb.Update_status_log(nimb_scratch_dir, _id+' moving to cp2local')
                            for subjid in ls:
                                cdb.Update_status_log(nimb_scratch_dir, 'moving '+subjid+' cp2local')
                                db['PROCESSED']['cp2local'].append(subjid)
                            db['LONG_DIRS'].pop(_id, None)
                            db['LONG_TPS'].pop(_id, None)
                            if subjid in db['REGISTRATION']:
                                db['REGISTRATION'].pop(subjid, None)
                            else:
                                cdb.Update_status_log(nimb_scratch_dir, '        missing from db[REGISTRATION]')
                            cdb.Update_status_log(nimb_scratch_dir, '        '+_id+'moved to cp2local')
                    else:
                        cdb.Update_status_log(nimb_scratch_dir, base_f+' moving to error_recon, step 8')
#                        db['ERROR_QUEUE'][subjid] = str(format(datetime.now()+timedelta(hours=datetime.strptime(cwalltime.Get_walltime(process, max_walltime), '%H:%M:%S').hour), "%Y%m%d_%H%M"))
                        db['PROCESSED']['error_recon'].append(base_f)
            else:
                job_id = crunfs.makesubmitpbs(Get_cmd.recbase(base_f, All_cross_ids_done), base_f, 'recbase', cwalltime.Get_walltime('recbase'), scheduler_params)
                db['RUNNING_JOBS'][base_f] = job_id
                db['LONG_DIRS'][_id].append(base_f)
                db['QUEUE']['recon'].append(base_f)
    else:
        for subjid in ls:
            cdb.Update_status_log(nimb_scratch_dir, '        '+subjid)
            if crunfs.checks_from_runfs(SUBJECTS_DIR, 'registration', subjid, freesurfer_version, masks):
                if crunfs.checks_from_runfs(SUBJECTS_DIR, process_order[-1], subjid, freesurfer_version, masks):
                    cdb.Update_status_log(nimb_scratch_dir, '            last process done '+process_order[-1]+' moving to CP2LOCAL')
                    db['PROCESSED']['cp2local'].append(subjid)
                    db['LONG_DIRS'].pop(_id, None)
                    db['LONG_TPS'].pop(_id, None)
                    if subjid in db['REGISTRATION']:
                        db['REGISTRATION'].pop(subjid, None)
                    else:
                        cdb.Update_status_log(nimb_sratch_dir,'        missing from db[REGISTRATION]')
            else:
                cdb.Update_status_log(nimb_scratch_dir, '        '+subjid+' was not registered')
                db['LONG_DIRS'].pop(_id, None)
                db['LONG_TPS'].pop(_id, None)
                if subjid in db['REGISTRATION']:
                    db['REGISTRATION'].pop(subjid, None)
                else:
                    cdb.Update_status_log(nimb_scratch_dir, '        missing from db[REGISTRATION]')
    cdb.Update_DB(db, nimb_scratch_dir)



def move_processed_subjects(subject, db_source, new_name):
    cdb.Update_status_log(nimb_scratch_dir, '    '+subject+' moving from '+db_source)
    file_mrparams = path.join(nimb_scratch_dir,'mriparams',subject+'_mrparams')
    if path.isfile(file_mrparams):
        shutil.move(file_mrparams, path.join(SUBJECTS_DIR, subject, 'stats'))
    size_src = sum(f.stat().st_size for f in Path(path.join(SUBJECTS_DIR,subject)).glob('**/*') if f.is_file())
    shutil.move(path.join(SUBJECTS_DIR,subject), path.join(processed_SUBJECTS_DIR,subject))
    db['PROCESSED'][db_source].remove(subject)
    cdb.Update_DB(db, nimb_scratch_dir)
    size_dst = sum(f.stat().st_size for f in Path(path.join(processed_SUBJECTS_DIR,subject)).glob('**/*') if f.is_file())

    if size_src == size_dst and archive_processed and new_name == '':
        cdb.Update_status_log(nimb_scratch_dir, '        archiving ...')
        chdir(processed_SUBJECTS_DIR)
        system('zip -r -q -m '+subject+'.zip '+subject)
    if new_name:
        cdb.Update_status_log(nimb_scratch_dir, '        renaming'+subject+' to '+new_name)
        rename(path.join(processed_SUBJECTS_DIR,subject),path.join(processed_SUBJECTS_DIR,new_name))
        subject = new_name
    if size_src != size_dst:
        cdb.Update_status_log(nimb_scratch_dir, '        ERROR in moving, not moved correctly '+str(size_src)+' '+str(size_dst))
        rename(path.join(processed_SUBJECTS_DIR,subject),path.join(processed_SUBJECTS_DIR,'error_moving_'+subject))
    cdb.Update_status_log(nimb_scratch_dir, '        moving DONE')



def run():
    cdb.Update_DB(db, nimb_scratch_dir)
    all_running = cdb.get_batch_jobs_status(cuser, cusers_list)

    for process in process_order[::-1]:
        if len(db['QUEUE'][process])>0:
            queue(process, all_running)
        if len(db['RUNNING'][process])>0:
            running(process,all_running)
        if len(db['DO'][process])>0:
            do(process)

    check_error()

# ================ START it is unclear why the len_Queue limitation was added and why it is not primary
#                        with it, subjects are not moved to cp2local if processing is still undergoing
#                        started testing 20200722, ah
#    if get_len_Queue_Running()<= max_nr_running_batches:
    cdb.Update_status_log(nimb_scratch_dir, 'CHECKING subjects')
    ls_long_dirs = list()
    for key in db['LONG_DIRS']:
            ls_long_dirs.append(key)

    for _id in ls_long_dirs:
#        if get_len_Queue_Running()<= max_nr_running_batches:
# ================ END
            cdb.Update_status_log(nimb_scratch_dir, '    '+_id)
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



def get_len_Queue_Running():
    len_QueueRunning = 0
    for process in db['RUNNING']:
        len_QueueRunning = len_QueueRunning+len(db['RUNNING'][process])
    for process in db['QUEUE']:
        len_QueueRunning = len_QueueRunning+len(db['QUEUE'][process])
    return len_QueueRunning


def Count_TimeSleep():
    time2sleep = 300 # 5 minutes
    if get_len_Queue_Running() >= max_nr_running_batches:
        cdb.Update_status_log(nimb_scratch_dir, 'queue and running: '+str(get_len_Queue_Running())+' max: '+str(max_nr_running_batches))
        time2sleep = 1200 # 20 minutes
    return time2sleep


if crunfs.FS_ready(SUBJECTS_DIR):
    print('updating status')
    cdb.Update_status_log(nimb_scratch_dir, '\n\n\n\n========nimb version: ',True)

    t0 = time.time()
    time_elapsed = 0
    count_run = 0

    cdb.Update_status_log(nimb_scratch_dir, 'pipeline started')
    cdb.Update_running(nimb_scratch_dir, 1)

    cdb.Update_status_log(nimb_scratch_dir, 'reading database')
    db = cdb.Get_DB(nimb_dir, nimb_scratch_dir, process_order)

    cdb.Update_status_log(nimb_scratch_dir, 'NEW SUBJECTS searching:')
    db = cdb.Update_DB_new_subjects_and_SUBJECTS_DIR(nimb_scratch_dir, SUBJECTS_DIR,db, process_order, base_name, long_name, freesurfer_version, masks)
    cdb.Update_DB(db, nimb_scratch_dir)
    active_subjects = check_active_tasks(db)

    # extracting 20 minutes from the maximum time for the batch to run
    # since it is expected that less then 15 minutes will be required for the pipeline to perform all the steps
    # while the batch is running, and start new batch
    max_batch_running = time.strftime('%H:%M:%S',time.localtime(time.mktime(time.strptime(batch_walltime,"%H:%M:%S"))-1200))

    while active_subjects >0 and time.strftime("%H:%M",time.gmtime(time_elapsed)) < max_batch_running:
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
# ================ START NEW CODE, to save a db version that would be accessible to all users, started testing 20200722, ah
        # try:
        #     shutil.copy(path.join(nimb_scratch_dir,'db.json'),path.join(NIMB_HOME,'db.json'))
        #     system('chmod 777 '+path.join(NIMB_HOME,'db.json'))
        # except Exception as e:
        #     cdb.Update_status_log(nimb_scratch_dir, str(e))
# ================ END NEW CODE that needs to be verified; There seem to be writing permission limitations
# ================ START NEW CODE, batch gets closed by the scheduler, trying to calculate time left until batch is finished, started testing 20200722, ah
        time_elapsed = time.time() - t0
        if time.strftime("%H:%M",time.gmtime(time_elapsed+time_to_sleep)) < max_batch_running:
            time.sleep(time_to_sleep)
# ================ END NEW CODE that needs to be verified

        time_elapsed = time.time() - t0
        active_subjects = check_active_tasks(db)

    if active_subjects == 0:
        cdb.Update_running(nimb_scratch_dir, 0)
        cdb.Update_status_log(nimb_scratch_dir, 'ALL TASKS FINISHED')
    else:
        cdb.Update_status_log(nimb_scratch_dir, 'Sending new batch to scheduler')
        chdir(nimb_dir)
        system('python processing/freesurfer/start_fs_pipeline.py')
        # system('sbatch run.sh')


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



# OLD VERSION before the DB bug
# def check_error():
#     cdb.Update_status_log(nimb_scratch_dir, 'ERROR checking')

#     for process in process_order:
#         if db['PROCESSED']['error_'+process]:
#             lserr = list()
#             for val in db['PROCESSED']['error_'+process]:
#                 lserr.append(val)   
#             for subjid in lserr:
#                 cdb.Update_status_log(nimb_scratch_dir, '    '+subjid)
#                 if path.exists(SUBJECTS_DIR+subjid):
#                     if crunfs.chkIsRunning(SUBJECTS_DIR, subjid):
#                         cdb.Update_status_log(nimb_scratch_dir, '            removing IsRunning file')
#                         remove(path.join(SUBJECTS_DIR,subjid,'scripts','IsRunning.lh+rh'))
#                     cdb.Update_status_log(nimb_scratch_dir, '        checking the recon-all-status.log for error for: '+process)
#                     crunfs.chkreconf_if_without_error(subjid)
#                     cdb.Update_status_log(nimb_scratch_dir, '        checking if all files were created for: '+process)
#                     if not crunfs.checks_from_runfs(SUBJECTS_DIR, process, subjid):
#                         cdb.Update_status_log(nimb_scratch_dir, '            some files were not created. Excluding subject from pipeline.')
#                         db['PROCESSED']['error_'+process].remove(subjid)
#                         _id, _ = cdb.get_id_long(subjid, db['LONG_DIRS'])
#                         if _id != 'none':
#                             try:
#                                 db['LONG_DIRS'][_id].remove(subjid)
#                                 db['LONG_TPS'][_id].remove(subjid.replace(_id+'_',''))
#                                 if len(db['LONG_DIRS'][_id])==0:
#                                     db['LONG_DIRS'].pop(_id, None)
#                                     db['LONG_TPS'].pop(_id, None)
#                             except ValueError as e:
#                                 cdb.Update_status_log(nimb_scratch_dir, '        ERROR, id not found in LONG_DIRS; '+e)
#                         else:
#                             cdb.Update_status_log(nimb_scratch_dir, '        ERROR, '+subjid+' is absent from LONG_DIRS')
#                         cdb.Update_status_log(nimb_scratch_dir, '        '+subjid+' moving to cp2local')
#                         db['PROCESSED']['cp2local'].append(subjid)
#                     else:
#                         cdb.Update_status_log(nimb_scratch_dir, '            all files were created for process: '+process)
#                         db['PROCESSED']['error_'+process].remove(subjid)
#                         db['RUNNING'][process].append(subjid)
#                         cdb.Update_status_log(nimb_scratch_dir, '    moving from error_'+process+' to RUNNING '+process)
#                 else:
#                     cdb.Update_status_log(nimb_scratch_dir, '    not in SUBJECTS_DIR')
#                 cdb.Update_DB(db, nimb_scratch_dir)
