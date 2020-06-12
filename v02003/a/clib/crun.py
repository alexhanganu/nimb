#!/bin/python
# 2020.06.12

from os import path, listdir, remove, rename, system, chdir
from pathlib import Path
import time, shutil
from var import cscratch_dir, max_nr_running_batches, process_order, base_name, DO_LONG, freesurfer_version, max_walltime, submit_cmd
import crunfs, cdb, cwalltime, var

_, nimb_dir, _, SUBJECTS_DIR , processed_SUBJECTS_DIR, _, _ , _ = var.get_vars()


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

    def autorecon(_id, lvl): return "recon-all -autorecon%s -s %s" % (lvl, _id)

    def recon(_id): return "recon-all -all -s %s" % _id

    def recbase(id_base, ls_tps):
            cmd = "recon-all -base %s" % id_base
            for tp in ls_tps:
                cmd = cmd+' -tp '+tp
            cmd = cmd+' -all'

            return cmd

    def reclong(_id, id_base): return "recon-all -long %s %s -all" % (_id, id_base)

    def qcache(_id): return "recon-all -qcache -s %s" % _id

    def brstem(_id): 
        if freesurfer_version>6:
            return 'segmentBS.sh {}'.format(_id)
        else:
            return "recon-all -s %s -brainstem-structures" % _id

    def hip(_id):
        if freesurfer_version>6:
            return 'segmentHA_T1.sh {}'.format(_id)
        else:
            return "recon-all -s %s -hippocampal-subfields-T1" % _id

    def tha(_id): return "segmentThalamicNuclei.sh %s" % _id




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
                        t1_ls_f, flair_ls_f, t2_ls_f = cdb.get_registration_files(subjid, db['LONG_DIRS'])
                        job_id = crunfs.makesubmitpbs(Get_cmd.registration(subjid, t1_ls_f, flair_ls_f, t2_ls_f), subjid, process, cwalltime.Get_walltime(process))
                        db['RUNNING_JOBS'][subjid] = job_id
                        db['QUEUE'][process].append(subjid)
                        cdb.Update_status_log('submit batch '+subjid+', '+process+', '+str(job_id))

            if process == 'recon':
                            job_id = crunfs.makesubmitpbs(Get_cmd.recon(subjid), subjid, 'recon', cwalltime.Get_walltime('recon'))
                            db['RUNNING_JOBS'][subjid] = job_id
                            db['QUEUE'][process].append(subjid)
                            cdb.Update_status_log('submit batch '+subjid+', '+process+', '+str(job_id))
            if process == 'autorecon1':
                            job_id = crunfs.makesubmitpbs(Get_cmd.autorecon(subjid, '1'), subjid, 'autorecon1', cwalltime.Get_walltime('autorecon1'))
                            db['RUNNING_JOBS'][subjid] = job_id
                            db['QUEUE'][process].append(subjid)
                            cdb.Update_status_log('submit batch '+subjid+', '+process+', '+str(job_id))
            if process == 'autorecon2':
                            job_id = crunfs.makesubmitpbs(Get_cmd.autorecon(subjid, '2'), subjid, 'autorecon2', cwalltime.Get_walltime('autorecon2'))
                            db['RUNNING_JOBS'][subjid] = job_id
                            db['QUEUE'][process].append(subjid)
                            cdb.Update_status_log('submit batch '+subjid+', '+process+', '+str(job_id))
            if process == 'autorecon3':
                            job_id = crunfs.makesubmitpbs(Get_cmd.autorecon(subjid, '3'), subjid, 'autorecon3', cwalltime.Get_walltime('autorecon3'))
                            db['RUNNING_JOBS'][subjid] = job_id
                            db['QUEUE'][process].append(subjid)
                            cdb.Update_status_log('submit batch '+subjid+', '+process+', '+str(job_id))
            if process == 'qcache':
                        job_id = crunfs.makesubmitpbs(Get_cmd.qcache(subjid), subjid, process, cwalltime.Get_walltime(process))
                        db['RUNNING_JOBS'][subjid] = job_id
                        db['QUEUE'][process].append(subjid)
                        cdb.Update_status_log('submit batch '+subjid+', '+process+', '+str(job_id))
            elif process == 'brstem':
                        job_id = crunfs.makesubmitpbs(Get_cmd.brstem(subjid), subjid, process, cwalltime.Get_walltime(process))
                        db['RUNNING_JOBS'][subjid] = job_id
                        db['QUEUE'][process].append(subjid)
                        cdb.Update_status_log('submit batch '+subjid+', '+process+', '+str(job_id))
            elif process == 'hip':
                        job_id = crunfs.makesubmitpbs(Get_cmd.hip(subjid), subjid, process, cwalltime.Get_walltime(process))
                        db['RUNNING_JOBS'][subjid] = job_id
                        db['QUEUE'][process].append(subjid)
                        cdb.Update_status_log('submit batch '+subjid+', '+process+', '+str(job_id))
            elif process == 'tha':
                        job_id = crunfs.makesubmitpbs(Get_cmd.tha(subjid), subjid, process, cwalltime.Get_walltime(process))
                        db['RUNNING_JOBS'][subjid] = job_id
                        db['QUEUE'][process].append(subjid)
                        cdb.Update_status_log('submit batch '+subjid+', '+process+', '+str(job_id))
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
            if crunfs.checks_from_runfs('registration',subjid):
                if status =='R' or status == 'none':
                    print(subjid,' status: ',status,'; moving from '+ACTION+' '+process+' to RUNNING '+process)
                    cdb.Update_status_log('moving '+subjid+' from '+ACTION+' '+process+' to RUNNING '+process)
                    db[ACTION][process].remove(subjid)
                    db['RUNNING'][process].append(subjid)
            elif status == 'none':
                db[ACTION][process].remove(subjid)
                cdb.Update_status_log('moving '+subjid+' to error_'+process)
                db['PROCESSED']['error_'+process].append(subjid)
            else:
                print(subjid,' is NOT registered yet !!!!!!!')
                cdb.Update_status_log(subjid+'    is NOT registered yet !!!!!!!!!!!!!!!!!!!!!!!!!!!')
        else:
            print(subjid,'    queue, NOT in RUNNING_JOBS')
            cdb.Update_status_log(subjid+'    queue, NOT in RUNNING_JOBS !!!!!!!!!!!!!!!!!!!!!!!!!!!')
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
                        cdb.Update_status_log('moving '+subjid+' to error_'+process)
                        print('moving '+subjid+' to error_'+process)
                        db['PROCESSED']['error_recon'].append(subjid)
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
                        cdb.Update_status_log('moving '+subjid+' to error_'+process)
                        print('moving '+subjid+' to error_'+process)
                        db['PROCESSED']['error_'+process].append(subjid)
        else:
            cdb.Update_status_log('    '+subjid+'    running, NOT in RUNNING_JOBS')
            print('    ',subjid,'    running, NOT in RUNNING_JOBS')
            if not crunfs.chkIsRunning(subjid):
                db[ACTION][process].remove(subjid)
                if base_name in subjid:
                    print(' reading ',process,subjid,' subjid is long or base ')
                    if not crunfs.checks_from_runfs('recon', subjid):
                        cdb.Update_status_log('moving '+subjid+' to error_recon')
                        db['PROCESSED']['error_recon'].append(subjid)
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
                        cdb.Update_status_log('moving '+subjid+' to error_'+process)
                        db['PROCESSED']['error_'+process].append(subjid)
            else:
                db[ACTION][process].remove(subjid)
                cdb.Update_status_log('moving '+subjid+' to error_'+process)
                print('moving '+subjid+' to error_'+process)
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
                                    cdb.Update_status_log('moving '+long_f+' to error_recon')
                                    db['PROCESSED']['error_recon'].append(long_f)
                            else:
                                cdb.Update_status_log('moving '+long_f+' to error_recon')
                                db['PROCESSED']['error_recon'].append(long_f)

                        if len(All_long_ids_done) == len(LONG_TPS):
                            print('        ','moving to CP2LOCAL ',_id)
                            cdb.Update_status_log('moving '+_id+' to cp2local')
                            for subjid in ls:
                                cdb.Update_status_log('moving '+subjid+' cp2local')
                                db['PROCESSED']['cp2local'].append(subjid)            
                            db['LONG_DIRS'].pop(_id, None)
                            db['LONG_TPS'].pop(_id, None)
                            print('        ',_id,'moved to cp2local')
                    else:
                        cdb.Update_status_log('moving '+base_f+' to error_recon')
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
                    print('        ','last process done ',process_order[-1])
                    print('        ','moving to CP2LOCAL ',_id)
                    cdb.Update_status_log('moving '+_id+' to cp2local')
                    db['PROCESSED']['cp2local'].append(subjid)            
                    db['LONG_DIRS'].pop(_id, None)
                    db['LONG_TPS'].pop(_id, None)
            else:
                print(process_order[-1], ' for ',subjid,' not finished ')
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


def check_error():
	for process in process_order:
		if db['PROCESSED']['error_'+process]:
			lserr = list()
			for val in db['PROCESSED']['error_'+process]:
				lserr.append(val)	
			for subjid in lserr:
				print('    ',subjid)
				if path.exists(SUBJECTS_DIR+subjid):
					if crunfs.chkIsRunning(subjid):
						print('            removing IsRunning file')
						remove(SUBJECTS_DIR+subjid+'/scripts/IsRunning.lh+rh')
					print('        checking if all files were created for: '+process)
					if not crunfs.checks_from_runfs(process, subjid):
						print('            some files were not created. Excluding subject from pipeline.')
						db['PROCESSED']['error_'+process].remove(subjid)
						_id, _ = cdb.get_id_long(subjid, db['LONG_DIRS'])
						if _id != 'none':
							try:
								db['LONG_DIRS'][_id].remove(subjid)
								db['LONG_TPS'][_id].remove(subjid.replace(_id+'_',''))
								if len(db['LONG_DIRS'][_id])==0:
									db['LONG_DIRS'].pop(_id, None)
									db['LONG_TPS'].pop(_id, None)
							except ValueError as e:
								print('    ERROR, ',subjid,' was found in LONG_DIRS; ',e)
						else:
							print('    ERROR, ',subjid,' is absent from LONG_DIRS')
						error_name = 'error_'+subjid
						rename(SUBJECTS_DIR+subjid,SUBJECTS_DIR+error_name)
						cdb.Update_status_log('moving '+error_name+' to cp2local')
						db['PROCESSED']['cp2local'].append(error_name)
					else:
						print('            all files were created for process: ', process)
					print('        checking the recon-all.log for error for: ',process)
					if not crunfs.chkreconf_if_without_error(subjid):
						print('            recon-all.log file exited with ERRORS. Please check the file')
				else:
					print('    not in SUBJECTS_DIR')
	#ls of errors:
	# ERROR: MultiRegistration::loadMovables: images have different voxel sizes.
	# Currently not supported, maybe first make conform?
	# Debug info: size(1) = 1.05469, 1.05469, 1.2   size(0) = 1, 1, 1.2
	# MultiRegistration::loadMovables: voxel size is different /scratch/hanganua/fs-subjects/011_S_0021_ses-6/mri/orig/002.mgz




def move_processed_subjects():
    processed_subjects = list()
    for subject in db['PROCESSED']['cp2local']:
        processed_subjects.append(subject)
    for subject in processed_subjects:
        print('    moving from cp2local ', subject)
        cdb.Update_status_log('    moving from cp2local '+subject)
        size_src = sum(f.stat().st_size for f in Path(SUBJECTS_DIR+subject).glob('**/*') if f.is_file())
        shutil.move(SUBJECTS_DIR+subject, processed_SUBJECTS_DIR+subject)
        db['PROCESSED']['cp2local'].remove(subject)
        cdb.Update_DB(db)
        size_dst = sum(f.stat().st_size for f in Path(processed_SUBJECTS_DIR+subject).glob('**/*') if f.is_file())
        if size_src == size_dst:
            print('    ',subject,' moved correctly, ',size_src, size_dst)
            cdb.Update_status_log('    '+subject+' moved correctly, '+str(size_src)+' '+str(size_dst))
        else:
            print('    something was wrong, not moved correctly', size_src, size_dst)
            cdb.Update_status_log('    something went wrong, not moved correctly '+str(size_src)+' '+str(size_dst))

    print('moving DONE')



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

    print('\n\n checking the ERRORS')
    check_error()
    print('finished checking the ERRORS')

    print('\n\n moving  the processed')
    move_processed_subjects()
    print('finished checking the processed')


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
    time2sleep = 100
    if get_len_Queue_Running() >= max_nr_running_batches:
        cdb.Update_status_log('queue and running: '+get_len_Queue_Running()+' max: '+max_nr_running_batches)
        for process in db['QUEUE']:
            if len(db['QUEUE'][process])>0:
                time2sleep = 1800
                break
        if 'autorecon2' in db['RUNNING']:
            if len(db['RUNNING']['autorecon2']) + len(db['RUNNING']['autorecon3']) >= max_nr_running_batches:
                time2sleep = 7200
        elif 'recon' in db['RUNNING'] and len(db['RUNNING']['recon']) >= max_nr_running_batches:
                time2sleep = 7200
        elif 'hip' in db['RUNNING'] and len(db['RUNNING']['hip'])>0 or 'brstem' in db['RUNNING'] and len(db['RUNNING']['brstem'])>0 or 'qcache' in db['RUNNING'] and len(db['RUNNING']['qcache'])>0:
            time2sleep = 3600
    return time2sleep


if crunfs.FS_ready(SUBJECTS_DIR):
    print('updating status')
    cdb.Update_status_log('',True)

    if max_walltime > '24:00:00':
        max_walltime = '03:00:00'

    t0 = time.time()
    time_elapsed = 0
    count_run = 0

    print('pipeline started')
    cdb.Update_running(1)

    print('reading database')
    db = cdb.Get_DB()

    print('reading files SUBJECTS_DIR, subj2fs')
    db = cdb.Update_DB_new_subjects_and_SUBJECTS_DIR(db)
    cdb.Update_DB(db)
    active_subjects = check_active_tasks(db)


    while active_subjects >0 and time.strftime("%H",time.gmtime(time_elapsed)) < max_walltime[:-6]:
        time_to_sleep = Count_TimeSleep()
        count_run += 1
        cdb.Update_status_log('restarting run, '+str(count_run))
        run()
        print('waiting. Next run at: ',str(time.strftime("%H:%M",time.gmtime(time.time()+time_to_sleep))))
        cdb.Update_status_log('waiting. Next run at: '+str(time.strftime("%H:%M",time.gmtime(time.time()+time_to_sleep))))

        time.sleep(time_to_sleep)
        time_elapsed = time.time() - t0
        cdb.Update_status_log('    elapsed time: '+time.strftime("%H",time.gmtime(time_elapsed))+' max walltime: '+max_walltime[:-6])

        if count_run % 5 == 0:
            print('reading files SUBJECTS_DIR, subj2fs')
            db = cdb.Update_DB_new_subjects_and_SUBJECTS_DIR(db)

        active_subjects = check_active_tasks(db)

    if active_subjects == 0:
        cdb.Update_running(0)
        cdb.Update_status_log('ALL TASKS FINISHED')
    else:
        cdb.Update_status_log('Sending new batch to scheduler')
        chdir(nimb_dir)
        system(submit_cmd+' run.sh')

