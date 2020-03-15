#!/bin/python
#Alexandru Hanganu, 2019 Nov 15

from os import path, listdir, remove, rename
from pathlib import Path
import time, shutil
from var import cscratch_dir, max_nr_running_batches, process_order, base_name
import crunfs, cdb, cwalltime

_, dir_home , _, SUBJECTS_DIR , processed_SUBJECTS_DIR, _ = cdb.get_vars()


def get_len_Queue_Running():
    len_QueueRunning = 0
    for process in db['RUNNING']:
        len_QueueRunning = len_QueueRunning+len(db['RUNNING'][process])
    for process in db['QUEUE']:
        len_QueueRunning = len_QueueRunning+len(db['QUEUE'][process])
    return len_QueueRunning


class Get_cmd:

    def registration(subjid, t1_f, flair_f, t2_f):
            cmd = "recon-all "
            for _t1 in t1_f:
                cmd = cmd+" -i "+_t1
            if flair_f != 'none':
                for _flair in flair_f:
                    cmd = cmd+' -FLAIR '+_flair
            if t2_f != 'none':
                for _t2 in t2_f:
                    cmd = cmd+' -T2 '+_t2
            cmd = cmd+' -s '+subjid

            return cmd

    def recon(_id): return "recon-all -all -s %s" % _id

    def recbase(id_base, ls_tps):
            cmd = "recon-all -base %s" % id_base
            for tp in ls_tps:
                cmd = cmd+' -tp '+tp
            cmd = cmd+' -all'

            return cmd

    def reclong(_id, id_base): return "recon-all -long %s %s -all" % (_id, id_base)

    def qcache(_id): return "recon-all -qcache -s %s" % _id

    def brstem(_id): return "recon-all -s %s -brainstem-structures" % _id

    def hip(_id): return "recon-all -s %s -hippocampal-subfields-T1" % _id



def check_error(subjid, process):
    if crunfs.chkIsRunning(subjid):
        remove(SUBJECTS_DIR+subjid+'/scripts/IsRunning.lh+rh')

    if not crunfs.checks_from_runfs(process, subjid):
        print(subjid,' ',process,' finished with error')

    if not crunfs.chkreconf_if_without_error(subjid):
        print(subjid,' exited with ERRORS')
        _id = 'none'
        for key in db['LONG_DIRS']:
            if subjid in db['LONG_DIRS'][key]:
                _id = key
                break
        if _id != 'none':
            db['PROCESSED']['error_'+process].remove(subjid)
            db['LONG_DIRS'][_id].remove(subjid)
            db['LONG_TPS'][_id].remove(subjid.replace(_id,''))
            rename(SUBJECTS_DIR+subjid,SUBJECTS_DIR+'error_'+subjid)
            db['PROCESSED']['cp2local'].append('error_'+subjid)
            if len(db['LONG_DIRS'][_id])==0:
                db['LONG_DIRS'].pop(_id, None)
                db['LONG_TPS'].pop(_id, None)
        else:
            print('can\'t find the id')


    if 'fsaverage' not in listdir(SUBJECTS_DIR):
        print(subjid,' fsaverage is missing')

    if 'xhemi' not in listdir(SUBJECTS_DIR+'fsaverage'):
        print(subjid,' fsaverage/xhemi is mising')





def Get_status_for_subjid_in_queue(subjid, all_running):
    job_id = str(db['RUNNING_JOBS'][subjid])
    if job_id in all_running:
        return all_running[job_id]
    else:
        return 'none'



def do(process):

    lsd = list()
    for val in db['DO'][process]:
        lsd.append(val)

    for subjid in lsd:
        if get_len_Queue_Running()<= max_nr_running_batches:
            db['DO'][process].remove(subjid)
            if process == 'registration':
                    if not crunfs.chksubjidinfs(subjid):
                        #t1_f, flair_f, t2_f = c_tmp_libs.get_t1_flair_t2_from_subjects2process(subjid)
                        t1_ls_f, flair_ls_f, t2_ls_f = cdb.get_registration_files(subjid, db['LONG_DIRS'])
                        job_id = crunfs.makesubmitpbs(Get_cmd.registration(subjid, t1_ls_f, flair_ls_f, t2_ls_f), subjid, process, cwalltime.Get_walltime(process))
                        db['RUNNING_JOBS'][subjid] = job_id
                        db['QUEUE'][process].append(subjid)
            if process == 'recon':
                        if 'fsaverage' in listdir(SUBJECTS_DIR) and 'xhemi' in listdir(SUBJECTS_DIR+'fsaverage'):
                            job_id = crunfs.makesubmitpbs(Get_cmd.recon(subjid), subjid, 'recon', cwalltime.Get_walltime('recon'))
                            db['RUNNING_JOBS'][subjid] = job_id
                            db['QUEUE'][process].append(subjid)
                        else:
                            cdb.Update_status_log('ERROR: fsaverage or xhemi is MISSING: '+subjid)
                            db['PROCESSED']['error_recon'].append(subjid)
                            check_error(subjid, process)
            if process == 'qcache':
                        job_id = crunfs.makesubmitpbs(Get_cmd.qcache(subjid), subjid, process, cwalltime.Get_walltime(process))
                        db['RUNNING_JOBS'][subjid] = job_id
                        db['QUEUE'][process].append(subjid)
            elif process == 'brstem':
                        job_id = crunfs.makesubmitpbs(Get_cmd.brstem(subjid), subjid, process, cwalltime.Get_walltime(process))
                        db['RUNNING_JOBS'][subjid] = job_id
                        db['QUEUE'][process].append(subjid)
            elif process == 'hip':
                        job_id = crunfs.makesubmitpbs(Get_cmd.hip(subjid), subjid, process, cwalltime.Get_walltime(process))
                        db['RUNNING_JOBS'][subjid] = job_id
                        db['QUEUE'][process].append(subjid)
            elif process == 'masks':
                        db['RUNNING'][process].append(subjid)
                        cdb.Update_status_log('RUNNING masks for: '+subjid)
                        cdb.Update_DB(db)
                        crunfs.run_make_masks(subjid)
            cdb.Update_status_log('RUNNING '+process+' for: '+subjid)
    cdb.Update_DB(db)



def queue(process, all_running):
    ACTION = 'QUEUE'
    cdb.Update_status_log(ACTION+' '+process)
	
    lsq = list()
    for val in db[ACTION][process]:
        lsq.append(val)

    for subjid in lsq:
        if subjid in db['RUNNING_JOBS']:
            status = Get_status_for_subjid_in_queue(subjid, all_running)
            if status =='R' or status == 'none':
                if base_name in subjid:
                    print(' reading ',process,subjid,' subjid is long or base ')
                    if crunfs.checks_from_runfs('registration', subjid):
                        print(subjid,' status: ',status,'; moving from '+ACTION+' '+process+' to RUNNING '+process)
                        cdb.Update_status_log('moving '+subjid+' from '+ACTION+' '+process+' to RUNNING '+process)
                        db[ACTION][process].remove(subjid)
                        db['RUNNING'][process].append(subjid)
                    elif status == 'none' and not crunfs.checks_from_runfs('registration',subjid):
                        db[ACTION][process].remove(subjid)
                        db['PROCESSED']['error_'+process].append(subjid)
                        check_error(subjid, 'recon')
                else:
                    print(subjid,' status: ',status,'; moving from '+ACTION+' '+process+' to RUNNING '+process)
                    cdb.Update_status_log('moving '+subjid+' from '+ACTION+' '+process+' to RUNNING '+process)
                    db[ACTION][process].remove(subjid)
                    db['RUNNING'][process].append(subjid)
        else:
            print(subjid,'    queue, NOT in RUNNING_JOBS')
            if base_name in subjid:
                print(' reading ',process,subjid,' subjid is long or base ')
                if crunfs.checks_from_runfs('registration',subjid):
                    if crunfs.chkIsRunning(subjid):
                        cdb.Update_status_log('moving '+subjid+' from '+ACTION+' '+process+' to RUNNING '+process)
                        db[ACTION][process].remove(subjid)
                        db['RUNNING'][process].append(subjid)
            else:
                if crunfs.chkIsRunning(subjid) or crunfs.checks_from_runfs(process, subjid):
                    cdb.Update_status_log('moving '+subjid+' from '+ACTION+' '+process+' to RUNNING '+process)
                    db[ACTION][process].remove(subjid)
                    db['RUNNING'][process].append(subjid)
    cdb.Update_DB(db)






def running(process, all_running):
    ACTION = 'RUNNING'
    cdb.Update_status_log(ACTION+' '+process)
	
    lsr = list()
    for val in db[ACTION][process]:
        lsr.append(val)	
	
    for subjid in lsr:
        if subjid in db['RUNNING_JOBS']:
            status = Get_status_for_subjid_in_queue(subjid, all_running)
            if status == 'none':
                db[ACTION][process].remove(subjid)
                db['RUNNING_JOBS'].pop(subjid, None)
                if base_name in subjid:
                    print(' reading ',process,subjid,' subjid is long or base ')
                    if crunfs.chkIsRunning(subjid) or not crunfs.checks_from_runfs('recon', subjid):
                        db['PROCESSED']['error_recon'].append(subjid)
                        check_error(subjid, 'recon')
                else:
                    if not crunfs.chkIsRunning(subjid) and crunfs.checks_from_runfs(process, subjid):
                        if process != process_order[-1]:
                            next_process = process_order[process_order.index(process)+1]
                            if not crunfs.checks_from_runfs(next_process, subjid):
                                db['DO'][next_process].append(subjid)
                                cdb.Update_status_log('        moving '+subjid+' from '+ACTION+' '+process+' to DO '+next_process)
                            else:
                                db[ACTION][next_process].append(subjid)
                                cdb.Update_status_log('        moving '+subjid+' from '+ACTION+' '+process+' to '+ACTION+' '+next_process)
                        else:
                            cdb.Update_status_log(subjid+' processing DONE')
                    else:
                        db['PROCESSED']['error_'+process].append(subjid)
                        check_error(subjid, process)
        else:
            print(subjid,'    running, NOT in RUNNING_JOBS')
            if not crunfs.chkIsRunning(subjid):
                db[ACTION][process].remove(subjid)
                if base_name in subjid:
                    print(' reading ',process,subjid,' subjid is long or base ')
                    if not crunfs.checks_from_runfs('recon', subjid):
                        db['PROCESSED']['error_recon'].append(subjid)
                        check_error(subjid, 'recon')
                else:
                    if crunfs.checks_from_runfs(process, subjid):
                        if process != process_order[-1]:
                            next_process = process_order[process_order.index(process)+1]
                            if not crunfs.checks_from_runfs(next_process, subjid):
                                db['DO'][next_process].append(subjid)
                                cdb.Update_status_log('        moving '+subjid+' from '+ACTION+' '+process+' to DO '+next_process)
                            else:
                                db[ACTION][next_process].append(subjid)
                                cdb.Update_status_log('        moving '+subjid+' from '+ACTION+' '+process+' to '+ACTION+' '+next_process)
                        else:
                            cdb.Update_status_log(subjid+' processing DONE')
                    else:
                        db['PROCESSED']['error_'+process].append(subjid)
                        check_error(subjid, process)
            else:
                        db['PROCESSED']['error_'+process].append(subjid)
                        check_error(subjid, process)
    cdb.Update_DB(db)




def long_check_groups(_id):
    ls = db['LONG_DIRS'][_id]
    LONG_TPS = db['LONG_TPS'][_id]
    if len(LONG_TPS)>1:
        All_cross_ids_done = list()
        for ses in LONG_TPS:
            if _id+ses in ls and crunfs.checks_from_runfs(process_order[-1], _id+ses):
                All_cross_ids_done.append(_id+ses)

        if len(All_cross_ids_done) == len(LONG_TPS):
            base_f = _id+base_name
            if base_f in ls:
                if base_f not in db['QUEUE']['recon'] and base_f not in db['PROCESSED']['error_recon'] and not crunfs.chkIsRunning(base_f):
                    if crunfs.checks_from_runfs('recon', base_f):
                        All_long_ids_done = list()
                        for ses in LONG_TPS:
                            long_f = _id+ses+'.long.'+_id+base_name
                            if long_f not in ls:
                                job_id = crunfs.makesubmitpbs(Get_cmd.reclong(_id+ses, _id+base_name), _id+ses, 'reclong', cwalltime.Get_walltime('reclong'))
                                db['RUNNING_JOBS'][long_f] = job_id
                                db['QUEUE']['recon'].append(long_f)
                                db['LONG_DIRS'][_id].append(long_f)
                            elif crunfs.checks_from_runfs('registration',long_f):
                                if crunfs.checks_from_runfs('recon', long_f):
                                    All_long_ids_done.append(long_f)
                                else:
                                    db['PROCESSED']['error_recon'].append(long_f)
                                    check_error(long_f, 'recon')
                            else:
                                db['PROCESSED']['error_recon'].append(long_f)
                                check_error(long_f, 'recon')

                        if len(All_long_ids_done) == len(LONG_TPS):
                            print('        ','moving to CP2LOCAL ',_id)
                            cdb.Update_status_log('moving '+_id+' to cp2local')
                            for subjid in ls:
                                db['PROCESSED']['cp2local'].append(subjid)            
                            db['LONG_DIRS'].pop(_id, None)
                            db['LONG_TPS'].pop(_id, None)
                            print('        ',_id,'moved to cp2local')
                    else:
                        db['PROCESSED']['error_recon'].append(base_f)
                        check_error(base_f, 'recon')
            else:
                job_id = crunfs.makesubmitpbs(Get_cmd.recbase(base_f, All_cross_ids_done), base_f, 'recbase', cwalltime.Get_walltime('recbase'))
                db['RUNNING_JOBS'][base_f] = job_id
                db['LONG_DIRS'][_id].append(base_f)
                db['QUEUE']['recon'].append(base_f)
    else:
        if crunfs.checks_from_runfs('registration', ls[0]):
            if crunfs.checks_from_runfs(process_order[-1], ls[0]):
                print('        ','last process done ',process_order[-1])
                print('        ','moving to CP2LOCAL ',_id)
                cdb.Update_status_log('moving '+_id+' to cp2local')
                db['PROCESSED']['cp2local'].append(ls[0])            
                db['LONG_DIRS'].pop(_id, None)
                db['LONG_TPS'].pop(_id, None)
        else:
            print(process_order[-1], ' for ',ls[0],' not finished ')
    cdb.Update_DB(db)



# def long_check_pipeline(all_running):
#     lsq_long = list()
#     for val in db['RUNNING_LONG']['queue']:
#         lsq_long.append(val)	


#     for subjid in lsq_long:
#         if subjid in db['RUNNING_JOBS']:
#             status = Get_status_for_subjid_in_queue(subjid, all_running)
#             if status =='R' or status == 'none' and crunfs.checks_from_runfs('registration',subjid):
#                 print('       ',subjid,' status: ',status,'; moving from queue to running')
#                 cdb.Update_status_log('moving '+subjid+' from queue to running')
#                 db['RUNNING_LONG']['queue'].remove(subjid)
#                 db['RUNNING']['recon'].append(subjid)
#             elif status == 'none' and not crunfs.checks_from_runfs('registration',subjid):
#                 db['RUNNING_LONG']['queue'].remove(subjid)
#                 db['PROCESSED']['error_recon'].append(subjid)
#                 check_error(subjid, 'recon')
#         else:
#             print(subjid,'    queue, NOT in RUNNING_JOBS')
#             if crunfs.checks_from_runfs('registration',subjid):
#                 if crunfs.chkIsRunning(subjid):
#                     cdb.Update_status_log('moving '+subjid+' from long_QUEUE to long_RUNNING')
#                     db['RUNNING_LONG']['queue'].remove(subjid)
#                     db['RUNNING']['recon'].append(subjid)
#                 elif crunfs.checks_from_runfs('recon', subjid):
#                     cdb.Update_status_log(subjid+' long recon DONE')
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
#                 if crunfs.chkIsRunning(subjid) or not crunfs.checks_from_runfs('recon', subjid):
#                     db['PROCESSED']['error_recon'].append(subjid)
#                     check_error(subjid, 'recon')
#         else:
#             print('    ',subjid,'    queue, NOT in RUNNING_JOBS')
#             if not crunfs.chkIsRunning(subjid):
#                 db['RUNNING_LONG']['running'].remove(subjid)
#                 if not crunfs.checks_from_runfs('recon', subjid):
#                     db['PROCESSED']['error_recon'].append(subjid)
#                     check_error(subjid, 'recon')
#     cdb.Update_DB(db)

def move_processed_subjects():
    processed_subjects = list()
    for subject in db['PROCESSED']['cp2local']:
        processed_subjects.append(subject)
    for subject in processed_subjects:
        print('    moving from cp2local ', subject)
        shutil.copytree(SUBJECTS_DIR+subject, processed_SUBJECTS_DIR+subject)
        size_src = sum(f.stat().st_size for f in Path(SUBJECTS_DIR+subject).glob('**/*') if f.is_file())
        size_dst = sum(f.stat().st_size for f in Path(processed_SUBJECTS_DIR+subject).glob('**/*') if f.is_file())
        if size_src == size_dst:
            print(subject,' copied correctly, ',size_src, size_dst)
            shutil.rmtree(SUBJECTS_DIR+subject)
            db['PROCESSED']['cp2local'].remove(subject)
        else:
            print('    something went wrong, not copied correctly', size_src, size_dst)
    print('moving DONE')
    cdb.Update_DB(db)



def run():
    cdb.Update_DB(db)
    all_running = cdb.get_batch_jobs_status()

    for process in process_order:
        if len(db['QUEUE'][process])>0:
            print('queue loop')
            queue(process, all_running)
        if len(db['RUNNING'][process])>0:
            print('running loop')
            running(process,all_running)
        if len(db['DO'][process])>0:
            print('do loop')
            do(process)
			
    # print('long check pipeline started') #
    # long_check_pipeline(all_running)

    ls_long_dirs = list()
    for key in db['LONG_DIRS']:
        ls_long_dirs.append(key)

    for _id in ls_long_dirs:
        if get_len_Queue_Running()<= max_nr_running_batches:
            print(_id,': checking subjects') #
            long_check_groups(_id)

    print('finished checking database')
    move_processed_subjects()


def check_active_tasks(db):
    active_subjects = 0
    error = 0
    for process in process_order:
        error = error + len(db['PROCESSED']['error_'+process])
    for _id in db['LONG_DIRS']:
        active_subjects = active_subjects + len(db['LONG_DIRS'][_id])
    #finished = error + len(db['PROCESSED']['cp2local'])
    #for ACTION in ('DO', 'QUEUE', 'RUNNING',):
    #    for process in db[ACTION]:
    #        active_subjects = active_subjects + len(db[ACTION][process])
    #active_subjects = active_subjects-(finished)
    #if active_subjects == 0:
    #    for _id in db['LONG_DIRS']:
    #        active_subjects = active_subjects + len(db['LONG_DIRS'][_id])

    cdb.Update_status_log('\n                 '+str(active_subjects)+'\n                 '+str(error)+' error')
    return active_subjects


def Count_TimeSleep():
    for process in db['QUEUE']:
        if len(db['QUEUE'][process])>0:
            time2sleep = 1800
            break
    if len(db['RUNNING']['hip'])>0 or len(db['RUNNING']['brstem'])>0 or len(db['RUNNING']['qcache'])>0:
        time2sleep = 3600
    elif len(db['RUNNING']['recon'])>0:
        time2sleep = 7200
    else:
        time2sleep = 100
    return time2sleep



print('updating status')
cdb.Update_status_log('',False)

print('pipeline started')
cdb.Update_running(1)

print('reading database')
db = cdb.Get_DB()

print('reading files SUBJECTS_DIR, subj2fs')
db = cdb.Update_DB_from_SUBJECTS_DIR_subj2fs(db)

cdb.Update_DB(db)


active_subjects = check_active_tasks(db)
count_run = 0
while active_subjects >0 and count_run<10: # to rm
    time_to_sleep = Count_TimeSleep()
    count_run += 1
    cdb.Update_status_log('restarting run, '+str(count_run))
    run()
    print('sleeping: ',time_to_sleep)
    cdb.Update_status_log('waiting before next run '+str(time_to_sleep))

    time.sleep(time_to_sleep)
    active_subjects = check_active_tasks(db)

cdb.Update_running(0)
cdb.Update_status_log('ALL TASKS FINISHED')
