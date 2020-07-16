#!/bin/python
# 2020.07.14

from os import path, listdir, remove, rename, system, chdir, environ
try:
    from pathlib import Path
except ImportError as e:
    cdb.Update_status_log(e)
import time, shutil
from var import max_nr_running_batches, process_order, base_name, DO_LONG, freesurfer_version, batch_walltime, submit_cmd, NIMB_HOME, nimb_dir, nimb_scratch_dir, SUBJECTS_DIR, processed_SUBJECTS_DIR, processing_env, archive_processed
import crunfs, cdb, cwalltime
from cbuild_stamp import nimb_version

environ['TZ'] = 'US/Eastern'
time.tzset()



def get_len_Queue_Running():
	len_QueueRunning = 0
	for process in db['RUNNING']:
		len_QueueRunning = len_QueueRunning+len(db['RUNNING'][process])
	for process in db['QUEUE']:
		len_QueueRunning = len_QueueRunning+len(db['QUEUE'][process])
	return len_QueueRunning


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
    def masks(_id): return "cd "+nimb_dir+"\npython run_masks.py {}".format(_id)



def Get_status_for_subjid_in_queue(subjid, all_running):
	job_id = str(db['RUNNING_JOBS'][subjid])
	if job_id in all_running:
		return all_running[job_id]
	else:
		return 'none'



def do(process):
    ACTION = 'DO'
    cdb.Update_status_log(ACTION+' '+process)

    lsd = list()
    for val in db['DO'][process]:
        lsd.append(val)

    for subjid in lsd:
        if get_len_Queue_Running()<= max_nr_running_batches:
            db['DO'][process].remove(subjid)
            if process == 'registration':
                if not crunfs.chksubjidinfs(subjid):
                    t1_ls_f, flair_ls_f, t2_ls_f = cdb.get_registration_files(subjid, db['LONG_DIRS'])
                    # job_id = crunfs.submit_4_processing(processing_env, cmd, subjid, run, walltime)
                    job_id = crunfs.makesubmitpbs(submit_cmd, Get_cmd.registration(subjid, t1_ls_f, flair_ls_f, t2_ls_f), subjid, process, cwalltime.Get_walltime(process))
                else:
                    job_id = 'none'
            elif process == 'recon':
                job_id = crunfs.makesubmitpbs(submit_cmd, Get_cmd.recon(subjid), subjid, process, cwalltime.Get_walltime(process))
                cdb.move_mrparams(subjid)
            elif process == 'autorecon1':
                job_id = crunfs.makesubmitpbs(submit_cmd, Get_cmd.autorecon1(subjid), subjid, process, cwalltime.Get_walltime(process))
            elif process == 'autorecon2':
                job_id = crunfs.makesubmitpbs(submit_cmd, Get_cmd.autorecon2(subjid), subjid, process, cwalltime.Get_walltime(process))
            elif process == 'autorecon3':
                job_id = crunfs.makesubmitpbs(submit_cmd, Get_cmd.autorecon3(subjid), subjid, process, cwalltime.Get_walltime(process))
            elif process == 'qcache':
                job_id = crunfs.makesubmitpbs(submit_cmd, Get_cmd.qcache(subjid), subjid, process, cwalltime.Get_walltime(process))
            elif process == 'brstem':
                job_id = crunfs.makesubmitpbs(submit_cmd, Get_cmd.brstem(subjid), subjid, process, cwalltime.Get_walltime(process))
            elif process == 'hip':
                job_id = crunfs.makesubmitpbs(submit_cmd, Get_cmd.hip(subjid), subjid, process, cwalltime.Get_walltime(process))
            elif process == 'tha':
                job_id = crunfs.makesubmitpbs(submit_cmd, Get_cmd.tha(subjid), subjid, process, cwalltime.Get_walltime(process))
            elif process == 'masks':
                job_id = crunfs.makesubmitpbs(submit_cmd, Get_cmd.masks(subjid), subjid, process, cwalltime.Get_walltime(process))
            if job_id != 'none':
                db['RUNNING_JOBS'][subjid] = job_id
                db['QUEUE'][process].append(subjid)
                try:
                    cdb.Update_status_log('                                   submited id: '+str(job_id))
                except Exception as e:
                    cdb.Update_status_log('        err in do: '+e)
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
            if crunfs.checks_from_runfs('registration',subjid):
                if status =='R' or status == 'none':
                    cdb.Update_status_log('    '+subjid+' moving from '+ACTION+' to RUNNING '+process)
                    db[ACTION][process].remove(subjid)
                    db['RUNNING'][process].append(subjid)
            elif status == 'none':
                db[ACTION][process].remove(subjid)
                cdb.Update_status_log('    '+subjid+' '+process+' moving to ERROR')
                db['PROCESSED']['error_'+process].append(subjid)
            else:
                cdb.Update_status_log('    '+subjid+'    is NOT registered yet')
        else:
            cdb.Update_status_log('    '+subjid+'    queue, NOT in RUNNING_JOBS')
            db[ACTION][process].remove(subjid)
                cdb.Update_status_log('    '+subjid+' '+process+' moving to ERROR')
                db['PROCESSED']['error_'+process].append(subjid)
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
                    cdb.Update_status_log(' reading '+process+subjid+' subjid is long or base ')
                    if crunfs.chkIsRunning(subjid) or not crunfs.checks_from_runfs('recon', subjid):
                        cdb.Update_status_log('    '+subjid+' '+process+' moving to ERROR')
                        db['PROCESSED']['error_recon'].append(subjid)
                else:
                    if not crunfs.chkIsRunning(subjid) and crunfs.checks_from_runfs(process, subjid):
                        if process != process_order[-1]:
                            next_process = process_order[process_order.index(process)+1]
                            if not crunfs.checks_from_runfs(next_process, subjid):
                                db['DO'][next_process].append(subjid)
                                cdb.Update_status_log('    '+subjid+' moving from '+ACTION+' '+process+' to DO '+next_process)
                            else:
                                db[ACTION][next_process].append(subjid)
                                cdb.Update_status_log('    '+subjid+' moving from '+ACTION+' '+process+' to '+ACTION+' '+next_process)
                        else:
                            cdb.Update_status_log('    '+subjid+' processing DONE')
                    else:
                        cdb.Update_status_log('   '+subjid+' '+process+' moving to ERROR because status is: '+status+', and IsRunning is present')
                        db['PROCESSED']['error_'+process].append(subjid)
        else:
            cdb.Update_status_log('    '+subjid+' NOT in RUNNING_JOBS')
            if not crunfs.chkIsRunning(subjid):
                db[ACTION][process].remove(subjid)
                if base_name in subjid:
                    cdb.Update_status_log(' reading '+process+subjid+' subjid is long or base ')
                    if not crunfs.checks_from_runfs('recon', subjid):
                        cdb.Update_status_log('   '+subjid+' recon, moving to ERROR')
                        db['PROCESSED']['error_recon'].append(subjid)
                else:
                    if crunfs.checks_from_runfs(process, subjid):
                        if process != process_order[-1]:
                            next_process = process_order[process_order.index(process)+1]
                            if not crunfs.checks_from_runfs(next_process, subjid):
                                db['DO'][next_process].append(subjid)
                                cdb.Update_status_log('    '+subjid+' moving from '+ACTION+' '+process+' to DO '+next_process)
                            else:
                                db[ACTION][next_process].append(subjid)
                                cdb.Update_status_log('    '+subjid+' moving from '+ACTION+' '+process+' to '+ACTION+' '+next_process)
                        else:
                            cdb.Update_status_log('    '+subjid+' processing DONE')
                    else:
                        cdb.Update_status_log('   '+subjid+' '+process+' moving to ERROR')
                        db['PROCESSED']['error_'+process].append(subjid)
            else:
                db[ACTION][process].remove(subjid)
                cdb.Update_status_log('   '+subjid+' '+process+' moving to error_'+process)
                db['PROCESSED']['error_'+process].append(subjid)
    cdb.Update_DB(db)




def long_check_groups(_id):
    ls = db['LONG_DIRS'][_id]
    LONG_TPS = db['LONG_TPS'][_id]
    if DO_LONG and len(LONG_TPS)>1:
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
                                    cdb.Update_status_log(long_f+' moving to error_recon')
                                    db['PROCESSED']['error_recon'].append(long_f)
                            else:
                                cdb.Update_status_log(long_f+' moving to error_recon')
                                db['PROCESSED']['error_recon'].append(long_f)

                        if len(All_long_ids_done) == len(LONG_TPS):
                            cdb.Update_status_log(_id+' moving to cp2local')
                            for subjid in ls:
                                cdb.Update_status_log('moving '+subjid+' cp2local')
                                db['PROCESSED']['cp2local'].append(subjid)            
                            db['LONG_DIRS'].pop(_id, None)
                            db['LONG_TPS'].pop(_id, None)
                            cdb.Update_status_log('        '+_id+'moved to cp2local')
                    else:
                        cdb.Update_status_log(base_f+' moving to error_recon')
                        db['PROCESSED']['error_recon'].append(base_f)
            else:
                job_id = crunfs.makesubmitpbs(Get_cmd.recbase(base_f, All_cross_ids_done), base_f, 'recbase', cwalltime.Get_walltime('recbase'))
                db['RUNNING_JOBS'][base_f] = job_id
                db['LONG_DIRS'][_id].append(base_f)
                db['QUEUE']['recon'].append(base_f)
    else:
        for subjid in ls:
            if crunfs.checks_from_runfs('registration', subjid):
                if crunfs.checks_from_runfs(process_order[-1], subjid):
                    cdb.Update_status_log('        last process done '+process_order[-1])
                    cdb.Update_status_log('        moving to CP2LOCAL ')
                    db['PROCESSED']['cp2local'].append(subjid)            
                    db['LONG_DIRS'].pop(_id, None)
                    db['LONG_TPS'].pop(_id, None)
            else:
                cdb.Update_status_log('        '+subjid+' was not registered')
                db['LONG_DIRS'].pop(_id, None)
                db['LONG_TPS'].pop(_id, None)
    cdb.Update_DB(db)



def check_error():
	cdb.Update_status_log('ERROR checking')

	for process in process_order:
		if db['PROCESSED']['error_'+process]:
			lserr = list()
			for val in db['PROCESSED']['error_'+process]:
				lserr.append(val)	
			for subjid in lserr:
				cdb.Update_status_log('    '+subjid)
				if path.exists(path.join(SUBJECTS_DIR,subjid)):
					if crunfs.chkIsRunning(subjid):
						cdb.Update_status_log('            removing IsRunning file')
						remove(path.join(SUBJECTS_DIR,subjid,'scripts','IsRunning.lh+rh'))
					cdb.Update_status_log('        checking the recon-all-status.log for error for: '+process)
					crunfs.chkreconf_if_without_error(subjid)
					cdb.Update_status_log('        checking if all files were created for: '+process)
					if not crunfs.checks_from_runfs(process, subjid):
						cdb.Update_status_log('            some files were not created. Excluding subject from pipeline.')
						fs_error = crunfs.fs_find_error(subjid)
						_id, _ = cdb.get_id_long(subjid, db['LONG_DIRS'])
						if _id != 'none':
							try:
								db['LONG_DIRS'][_id].remove(subjid)
								db['LONG_TPS'][_id].remove(subjid.replace(_id+'_',''))
								if len(db['LONG_DIRS'][_id])==0:
									db['LONG_DIRS'].pop(_id, None)
									db['LONG_TPS'].pop(_id, None)
							except Exception as e:
								cdb.Update_status_log('        ERROR, id not found in LONG_DIRS; '+str(e))
						else:
							cdb.Update_status_log('        ERROR, '+subjid+' is absent from LONG_DIRS')
						if fs_error:
							new_name = 'error_'+fs_error+'_'+subjid
						else:
							new_name = 'error_'+process+'_'+subjid
						move_processed_subjects(subjid, 'error_'+process, new_name)
					else:
						cdb.Update_status_log('            all files were created for process: '+process)
						db['PROCESSED']['error_'+process].remove(subjid)
						db['RUNNING'][process].append(subjid)
						cdb.Update_status_log('        moving from error_'+process+' to RUNNING '+process)
				else:
					cdb.Update_status_log('    not in SUBJECTS_DIR')
					db['PROCESSED']['error_'+process].remove(subjid)
				cdb.Update_DB(db)



def move_processed_subjects(subject, db_source, new_name):
    cdb.Update_status_log('    '+subject+' moving from '+db_source)
    size_src = sum(f.stat().st_size for f in Path(path.join(SUBJECTS_DIR,subject)).glob('**/*') if f.is_file())
    shutil.move(path.join(SUBJECTS_DIR,subject), path.join(processed_SUBJECTS_DIR,subject))
    db['PROCESSED'][db_source].remove(subject)
    cdb.Update_DB(db)
    size_dst = sum(f.stat().st_size for f in Path(processed_SUBJECTS_DIR+subject).glob('**/*') if f.is_file())
    if new_name:
        cdb.Update_status_log('        renaming'+subject+' to '+new_name)
        rename(path.join(processed_SUBJECTS_DIR,subject),path.join(processed_SUBJECTS_DIR,new_name))
        subject = new_name
    if size_src != size_dst:
        cdb.Update_status_log('        ERROR in moving, not moved correctly '+str(size_src)+' '+str(size_dst))
        subject = 'error_moving'+subject
        rename(path.join(processed_SUBJECTS_DIR,subject),path.join(processed_SUBJECTS_DIR,subject))
    cdb.Update_status_log('        moving DONE')
    if archive_processed:
        cdb.Update_status_log('        archiving ...')
        system('zip -r -q -m '+path.join(processed_SUBJECTS_DIR,subject+'.zip')+' '+path.join(processed_SUBJECTS_DIR,subject))



def run():
    cdb.Update_DB(db)
    all_running = cdb.get_batch_jobs_status()

    for process in process_order[::-1]:
        if len(db['QUEUE'][process])>0:
            queue(process, all_running)
        if len(db['RUNNING'][process])>0:
            running(process,all_running)
        if len(db['DO'][process])>0:
            do(process)

    # print('long check pipeline started') #
    # long_check_pipeline(all_running)

    cdb.Update_status_log('CHECKING subjects')
    ls_long_dirs = list()
    for key in db['LONG_DIRS']:
        ls_long_dirs.append(key)

    for _id in ls_long_dirs:
        if get_len_Queue_Running()<= max_nr_running_batches:
            cdb.Update_status_log('    '+_id)
            long_check_groups(_id)

    check_error()

    cdb.Update_status_log('MOVING the processed')

    # processed_subjects = list()
    # for subject in db['PROCESSED']['cp2local']: # [::-1]
    #     processed_subjects.append(subject)
    for subject in db['PROCESSED']['cp2local'][::-1]:# processed_subjects:
        move_processed_subjects(subject, 'cp2local', '')


def check_active_tasks(db):
    active_subjects = 0
    error = 0
    for process in process_order:
        error = error + len(db['PROCESSED']['error_'+process])
    for _id in db['LONG_DIRS']:
        active_subjects = active_subjects + len(db['LONG_DIRS'][_id])
    active_subjects = active_subjects+len(db['PROCESSED']['cp2local'])
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
    time2sleep = 300 # 5 minutes
    if get_len_Queue_Running() >= max_nr_running_batches:
        cdb.Update_status_log('queue and running: '+str(get_len_Queue_Running())+' max: '+str(max_nr_running_batches))
        time2sleep = 1500 # 25 minutes
        # for process in db['QUEUE']:
        #     if len(db['QUEUE'][process])>0:
        #         time2sleep = 1500 # 25 minutes
        #         break
        # if 'autorecon2' in db['RUNNING']:
        #     if len(db['RUNNING']['autorecon2']) + len(db['RUNNING']['autorecon3']) >= max_nr_running_batches:
        #         time2sleep = 1500
        # elif 'recon' in db['RUNNING'] and len(db['RUNNING']['recon']) >= max_nr_running_batches:
        #         time2sleep = 1500
        # elif 'hip' in db['RUNNING'] and len(db['RUNNING']['hip'])>0 or 'brstem' in db['RUNNING'] and len(db['RUNNING']['brstem'])>0 or 'qcache' in db['RUNNING'] and len(db['RUNNING']['qcache'])>0:
        #     time2sleep = 1500
    return time2sleep


if crunfs.FS_ready(SUBJECTS_DIR):
    print('updating status')
    cdb.Update_status_log('\n\n\n\n========nimb version: '+nimb_version,True)

    t0 = time.time()
    time_elapsed = 0
    count_run = 0

    cdb.Update_status_log('pipeline started')
    cdb.Update_running(1)

    cdb.Update_status_log('reading database')
    db = cdb.Get_DB()

    cdb.Update_status_log('reading SUBJECTS_DIR, subj2fs for new subjects')
    db = cdb.Update_DB_new_subjects_and_SUBJECTS_DIR(db)
    cdb.Update_DB(db)
    active_subjects = check_active_tasks(db)

    # extracting 15 minutes from the maximum time for the batch to run
    # since it is expected that less then 15 minutes will be required for the pipeline to perform all the steps
    # while the batch is running, and start new batch
    batch_hour = str(int(batch_walltime.split(':')[0])-1).zfill(2)
    max_batch_running = batch_hour+':'+str(int(batch_walltime.split(':')[1])+30)

    while active_subjects >0 and time.strftime("%H:%M",time.gmtime(time_elapsed)) < max_batch_running:
        count_run += 1
        cdb.Update_status_log('restarting run, '+str(count_run))
        cdb.Update_status_log('elapsed time: '+time.strftime("%H:%M",time.gmtime(time_elapsed))+' max walltime: '+batch_walltime[:-6])
        if count_run % 5 == 0:
            cdb.Update_status_log('reading SUBJECTS_DIR, subj2fs for new subjects')
            db = cdb.Update_DB_new_subjects_and_SUBJECTS_DIR(db)
            cdb.Update_DB(db)
        run()

        time_to_sleep = Count_TimeSleep()
        cdb.Update_status_log('\n\nWAITING. \nNext run at: '+str(time.strftime("%H:%M",time.localtime(time.time()+time_to_sleep))))
        time.sleep(time_to_sleep)

        time_elapsed = time.time() - t0
        active_subjects = check_active_tasks(db)

    if active_subjects == 0:
        cdb.Update_running(0)
        cdb.Update_status_log('ALL TASKS FINISHED')
    else:
        shutil.copy(path.join(nimb_scratch_dir,'db.json'),path.join(NIMB_HOME,'db.json'))
        cdb.Update_status_log('Sending new batch to scheduler')
        chdir(nimb_dir)
        system('python nimb.py')


'''THIS script was used for the longitudinal analysis. It has changed and it should not be needed now, but a longitudinal analysis must be made to confirm'''

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
#         else:
#             print('    ',subjid,'    queue, NOT in RUNNING_JOBS')
#             if not crunfs.chkIsRunning(subjid):
#                 db['RUNNING_LONG']['running'].remove(subjid)
#                 if not crunfs.checks_from_runfs('recon', subjid):
#                     db['PROCESSED']['error_recon'].append(subjid)
#     cdb.Update_DB(db)

