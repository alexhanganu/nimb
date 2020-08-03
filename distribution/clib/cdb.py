#!/bin/python
# 2020.06.26

from os import path, listdir, remove, getenv, rename, mkdir, environ, system, chdir
from distribution.clib.var import process_order, long_name, base_name, cusers_list, cuser, nimb_dir, nimb_scratch_dir, SUBJECTS_DIR
import time, shutil

environ['TZ'] = 'US/Eastern'
time.tzset()



def Get_DB():

    db = dict()
    print("nimb_scratch_dir is:" + nimb_scratch_dir)
    # change to local dev folder instead of supervisor folder due to no-writing-file permission
    if path.isfile(nimb_scratch_dir+'db'):
        shutil.copy(nimb_scratch_dir+'db',nimb_dir+'db.py')
        system('chmod 777 '+nimb_dir+'db.py')
        time.sleep(2)
        from db import DO, QUEUE, RUNNING, RUNNING_JOBS, LONG_DIRS, LONG_TPS, PROCESSED
        db['DO'] = DO
        db['QUEUE'] = QUEUE
        db['RUNNING'] = RUNNING
        db['RUNNING_JOBS'] = RUNNING_JOBS
        db['LONG_DIRS'] = LONG_DIRS
        db['LONG_TPS'] = LONG_TPS
        db['PROCESSED'] = PROCESSED
        time.sleep(2)
        remove(nimb_dir+'db.py')
    else:
        for action in ['DO','QUEUE','RUNNING',]:
            db[action] = {}
            for process in process_order:
                db[action][process] = []
        db['RUNNING_JOBS'] = {}
        db['LONG_DIRS'] = {}
        db['LONG_TPS'] = {}
        db['PROCESSED'] = {'cp2local':[],}
        for process in process_order:
            db['PROCESSED']['error_'+process] = []
    return db


def Update_DB(d):
    file = nimb_scratch_dir+'db'
    open(file,'w').close()
    with open(file,'a') as f:
        for key in d:
            if key != 'RUNNING_JOBS':
                f.write(key+'= {')
                for subkey in d[key]:
                    f.write('\''+subkey+'\':[')
                    for value in sorted(d[key][subkey]):
                        f.write('\''+value+'\',')
                    f.write('],')
                f.write('}\n')
            else:
                f.write(key+'= {')
                for subkey in d[key]:
                    f.write('\''+subkey+'\':'+str(d[key][subkey])+',')
                f.write('}\n')



def Update_status_log(cmd, update=True):
    print(cmd)
    file = nimb_scratch_dir+'status.log'
    if not update:
        print('cleaning status file', file)
        open(file,'w').close()

    dthm = time.strftime('%Y/%m/%d %H:%M')
    with open(file,'a') as f:
        f.write(dthm+' '+cmd+'\n')


def Update_running(cmd):
    file = nimb_scratch_dir+'running_'
	
    if cmd == 1:
        if path.isfile(file+'0'):
            rename(file+'0',file+'1')
        else:
            open(file+'1','w').close()
    else:
        if path.isfile(file+'1'):
            rename(file+'1',file+'0')


def get_ls_subjids_in_long_dirs(db):
    lsall = []
    for _id in db['LONG_DIRS']:
        for subjid in db['LONG_DIRS'][_id]:
                if subjid not in lsall:
                    lsall.append(subjid)
        for process in db['PROCESSED']:
            for subjid in db['PROCESSED'][process]:
                if subjid not in lsall:
                    lsall.append(subjid)
    return lsall


def get_RUNNING_JOBS(type):
    lsall = []
    if type == 'tmux':
        for val in db['RUNNING_JOBS'].keys():
            if 'tmux' in val:
                lsall.append(val)
    return sorted(lsall)



def verify_vox_size_values(vox_size):
    vox = True
    if type(vox_size) == list:
        if len(vox_size) == 3:
            for val in vox_size:
                if '.' not in val:
                    vox=False
                    break
        else:
            vox=False
    else:
        vox=False
    return vox



def vox_higher_main(vox_size, main_vox_size):
	res = True
	vox_1 = float(vox_size[0])*float(vox_size[1])*float(vox_size[2])
	vox_2 = float(main_vox_size[0])*float(main_vox_size[1])*float(main_vox_size[2])
	if vox_1<vox_2:
		res = False
	return res


def get_MR_file_params(file):
	tmp_f = nimb_scratch_dir+'tmp'
	vox_size = 'none'
	chdir(nimb_dir)
	system('./mri_info '+file+' >> '+tmp_f)
	if path.isfile(tmp_f):
		lines = list(open(tmp_f,'r'))
		try:
			vox_size = [x.strip('\n') for x in lines if 'voxel sizes' in x][0].split(' ')[-3:]
			vox_size = [x.replace(',','') for x in vox_size]
			Update_status_log('            voxel size is: '+str(vox_size))
		except IndexError as e:
			Update_status_log('            voxel size is: '+str(e))
		try:
			TR_TE_TI = [x.strip('\n') for x in lines if 'TR' in x][0].split(',')
			TR = TR_TE_TI[0].split(' ')[-2]
			TE = TR_TE_TI[1].split(' ')[-2]
			TI = TR_TE_TI[2].split(' ')[-2]
			flip_angle = TR_TE_TI[3].split(' ')[-2]
			Update_status_log('            TR is: '+str(TR))
			Update_status_log('            TE is: '+str(TE))
			Update_status_log('            TI is: '+str(TI))
			Update_status_log('            flip angle is: '+str(flip_angle))
		except IndexError as e:
			Update_status_log('            TR,TE,TI, flip angle : '+str(e))
		try:
			field_strength = [x.strip('\n') for x in lines if 'FieldStrength' in x][0].split(',')[0].replace('       FieldStrength: ','')
			Update_status_log('            field strength is: '+str(field_strength))
		except IndexError as e:
			Update_status_log('            field_strength : '+str(e))
		try:
			matrix = [x.strip('\n') for x in lines if 'dimensions' in x][0].split(',')[0].replace('    dimensions: ','')
			Update_status_log('            matrix is: '+str(matrix))
		except IndexError as e:
			Update_status_log('            matrix : '+str(e))
		try:
			fov = [x.strip('\n') for x in lines if 'fov' in x][0].split(',')[0].replace('           fov: ','')
			Update_status_log('            fov is: '+str(fov))
		except IndexError as e:
			Update_status_log('            fov : '+str(e))			
		remove(tmp_f)
	return vox_size


def keep_files_similar_params(t1_ls_f, flair_ls_f, t2_ls_f):
    main_vox_size = 'none'
    for file in t1_ls_f:
        Update_status_log('        reading MR data for T1 file: '+file)
        vox_size = get_MR_file_params(file)
        if vox_size:
            if verify_vox_size_values(vox_size):
                Update_status_log('        current voxel size is: '+str(vox_size))
                if main_vox_size == 'none':
                    main_vox_size = vox_size
                else:
                    if vox_size != main_vox_size:
                        if vox_higher_main(vox_size, main_vox_size):
                          t1_ls_f.remove(file)
                        else:
                            main_vox_size = vox_size                            
        Update_status_log('        main voxel size is: '+str(main_vox_size))
    if flair_ls_f != 'none':
        for file in flair_ls_f:
            Update_status_log('        reading MR data for FLAIR file: '+file)
            vox_size = get_MR_file_params(file)
            Update_status_log('        main voxel size is: '+str(main_vox_size))
            Update_status_log('        current voxel size is: '+str(vox_size))
            if vox_size != main_vox_size:
                flair_ls_f.remove(file)
                Update_status_log('        FLAIR file not added to analysis; voxel size is different')
    if len(flair_ls_f) <1:
        flair_ls_f = 'none'
    if t2_ls_f != 'none':
        for file in t2_ls_f:
            Update_status_log('        reading MR data for T2 file: '+file)
            vox_size = get_MR_file_params(file)
            Update_status_log('        main voxel size is: '+str(main_vox_size))
            Update_status_log('        current voxel size is: '+str(vox_size))
            if vox_size != main_vox_size:
                t2_ls_f.remove(file)
                Update_status_log('        T2 file not added to analysis; voxel size is different')
    if len(t2_ls_f) <1:
        t2_ls_f = 'none'
    return t1_ls_f, flair_ls_f, t2_ls_f



def Update_DB_new_subjects_and_SUBJECTS_DIR(db):

    d = chk_subj_in_SUBJECTS_DIR(db)
    d = chk_subjects_folder(db)
    d = chk_new_subjects_json_file(db)
    Update_status_log('done checking SUBJECTS_DIR, subjects folder and new_subjects.json')
    return db



def add_subjid_2_DB(_id, ses, db, ls_SUBJECTS_in_long_dirs_processed):
        subjid = _id+'_'+ses
        if subjid not in ls_SUBJECTS_in_long_dirs_processed:
            if _id not in db['LONG_DIRS']:
                db['LONG_DIRS'][_id] = []
                db['LONG_TPS'][_id] = []
            db['LONG_TPS'][_id].append(ses)
            db['LONG_DIRS'][_id].append(subjid)
            db['DO']['registration'].append(subjid)
        else:
            Update_status_log('ERROR: '+subjid+' in database! new one cannot be registered')
        return db




def chk_subjects_folder(db):
    Update_status_log('checking for new subjects in the subjects folder...')

    ls_SUBJECTS_in_long_dirs_processed = get_ls_subjids_in_long_dirs(db)
    from distribution.clib.crunfs import checks_from_runfs

    f_subj2fs = nimb_dir+"subj2fs"
    if path.isfile(f_subj2fs):
        ls_subj2fs = ls_from_subj2fs(f_subj2fs)
        for subjid in ls_subj2fs:
            Update_status_log('    adding '+subjid+' to database')
            _id, ses = get_id_long(subjid, db['LONG_DIRS'])
            if not checks_from_runfs('registration',_id):
                db = add_subjid_2_DB(_id, ses, db, ls_SUBJECTS_in_long_dirs_processed)
        Update_status_log('new subjects were added from the subjects folder')
    return db



def chk_new_subjects_json_file(db):
    Update_status_log('checking for new subjects ...')

    ls_SUBJECTS_in_long_dirs_processed = get_ls_subjids_in_long_dirs(db)
    from distribution.clib.crunfs import checks_from_runfs

    f_new_subjects = nimb_dir+"new_subjects.json"
    if path.isfile(f_new_subjects):
        import json
        with open(f_new_subjects) as jfile:
            data = json.load(jfile)
        for _id in data:
            if not checks_from_runfs('registration',_id):
                for ses in data[_id]:
                    if 'anat' in data[_id][ses]:
                        if 't1' in data[_id][ses]['anat']:
                            if data[_id][ses]['anat']['t1']:
                                db = add_subjid_2_DB(_id, ses, db, ls_SUBJECTS_in_long_dirs_processed)
                            else:
                                db['PROCESSED']['error_registration'].append(subjid)
                                Update_status_log('ERROR: '+_id+' was read and but was not added to database')
        rename(f_new_subjects, nimb_dir+'new_subjects_registration_paths.json')
        Update_status_log('new subjects were added from the new_subjects.json file')
    return db




def get_registration_files(subjid, d_LONG_DIRS):
    f = nimb_dir+"new_subjects_registration_paths.json"#!!!! json file must be archived when finished
    if path.isfile(f):
        import json

        with open(f) as jfile:
            data = json.load(jfile)

        for _id in d_LONG_DIRS:
            if subjid in d_LONG_DIRS[_id]:
                _id = _id
                ses = subjid.replace(_id+'_',"")
                break
            # else:
            #     _id = 'none'
            #     print(_id,' not in LONG_DIRS, please CHECK the database')
        Update_status_log('    '+subjid+'\n        id is: '+_id+', ses is: '+ses)

        if _id != 'none':
            t1_ls_f = data[_id][ses]['anat']['t1']
            flair_ls_f = 'none'
            t2_ls_f = 'none'
            if 'flair' in data[_id][ses]['anat']:
                if data[_id][ses]['anat']['flair']:
                    flair_ls_f = data[_id][ses]['anat']['flair']
            if 't2' in data[_id][ses]['anat']:
                if data[_id][ses]['anat']['t2']:
                    t2_ls_f = data[_id][ses]['anat']['t2']
        Update_status_log('        registration files were read')

    t1_ls_f, flair_ls_f, t2_ls_f = keep_files_similar_params(t1_ls_f, flair_ls_f, t2_ls_f)

    return t1_ls_f, flair_ls_f, t2_ls_f






def ls_from_subj2fs(f_subj2fs):
    ls_subjids = list()
    lines = list(open(f_subj2fs,'r'))
    for val in lines:
        if len(val)>3:
            ls_subjids.append(val.strip('\r\n'))
    rename(nimb_dir+'subj2fs', nimb_dir+'zdone_subj2fs')
    Update_status_log('subj2fs was read')
    return ls_subjids



def get_id_long(subjid, LONG_DIRS):
        _id = 'none'
        for key in LONG_DIRS:
            if subjid in LONG_DIRS[key]:
                _id = key
                longitud = subjid.replace(_id+'_','')
                break
        if base_name in subjid:
            subjid = subjid.replace(base_name,'').split('.',1)[0]
        if _id == 'none':
            _id = subjid
            if long_name in subjid:
                longitud = subjid[subjid.find(long_name):]
                _id = subjid.replace('_'+longitud,'')
            else:
                longitud = long_name+str(1)
        return _id, longitud



def chk_subj_in_SUBJECTS_DIR(db):
    Update_status_log('checking SUBJECTS_DIR ...')

    from distribution.clib.crunfs import chkIsRunning, checks_from_runfs

    def chk_if_exclude(subjid):
        exclude = False
        ls_2_exclude = ['bert','average','README','sample-00','cvs_avg35']
        for value in ls_2_exclude:
            if value in subjid:
                exclude = True
                break
        return exclude

    def get_subjs_running(db):
        ls_subj_running = []
        for ACTION in ('DO', 'QUEUE', 'RUNNING',):
            for process in process_order:
                for subjid in db[ACTION][process]:
                    if subjid not in ls_subj_running:
                        ls_subj_running.append(subjid)
        return ls_subj_running

    def add_new_subjid_to_db(subjid):
        if not chkIsRunning(subjid):
            for process in process_order[1:]:
                if not checks_from_runfs(process, subjid):
                    Update_status_log('        '+subjid+' sent for '+process)
                    db['DO'][process].append(subjid)
                    break
        else:
            Update_status_log('            IsRunning file present, adding to '+process_order[1])
            db['RUNNING'][process_order[1]].append(subjid)

    if not path.isdir(SUBJECTS_DIR):
        mkdir(SUBJECTS_DIR)
    ls_SUBJECTS = sorted([i for i in listdir(SUBJECTS_DIR) if not chk_if_exclude(i)])
    ls_SUBJECTS_in_long_dirs_processed = get_ls_subjids_in_long_dirs(db)
    ls_SUBJECTS_running = get_subjs_running(db)

    for subjid in ls_SUBJECTS:
        if subjid not in ls_SUBJECTS_in_long_dirs_processed:
            Update_status_log('    '+subjid+' not in PROCESSED')
            _id, longitud = get_id_long(subjid, db['LONG_DIRS'])
            Update_status_log('        adding to database: id: '+_id+', long name: '+longitud)
            if _id == subjid:
                subjid = _id+'_'+longitud
                Update_status_log('   no '+long_name+' in '+_id+' Changing name to: '+subjid)
                rename(SUBJECTS_DIR+_id, SUBJECTS_DIR+subjid)
            if _id not in db['LONG_DIRS']:
                db['LONG_DIRS'][_id] = list()
            if _id in db['LONG_DIRS']:
                if subjid not in db['LONG_DIRS'][_id]:
                    # Update_status_log('        '+subjid+' to LONG_DIRS[\''+_id+'\']')
                    db['LONG_DIRS'][_id].append(subjid)
            if _id not in db['LONG_TPS']:
                # Update_status_log('    adding '+_id+' to LONG_TPS')
                db['LONG_TPS'][_id] = list()
            if _id in db['LONG_TPS']:
                if longitud not in db['LONG_TPS'][_id]:
                    # Update_status_log('    adding '+longitud+' to LONG_TPS[\''+_id+'\']')
                    db['LONG_TPS'][_id].append(longitud)
            if base_name not in subjid:
                if subjid not in ls_SUBJECTS_running:
                    add_new_subjid_to_db(subjid)
    return db



def get_batch_jobs_status():

    def get_jobs(jobs, queue):

        for line in queue[1:]:
                vals = list(filter(None,line.split(' ')))
                if vals[0] not in jobs:
                    jobs[vals[0]] = vals[4]
        return jobs


    import subprocess

    jobs = dict()
    for cuser in cusers_list:
        queue = list(filter(None,subprocess.run(['squeue','-u',cuser], stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')))
        jobs = get_jobs(jobs, queue)

    return jobs



def get_diskusage_report():
    '''script to read the available space
    on compute canada clusters
    the command diskusage_report is used'''

    def get_diskspace(diskusage, queue):

        for line in queue[1:]:
                vals = list(filter(None,line.split(' ')))
                diskusage[vals[0]] = vals[4][:-5].strip('k')
        return diskusage


    import subprocess

    diskusage = dict()
    for cuser in cusers_list:
        queue = list(filter(None,subprocess.run(['diskusage_report'], stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')))
        diskusage = get_diskspace(diskusage, queue)

    return diskusage


def get_mask_codes(structure):
    structure_codes = {'left_hippocampus':17,'right_hippocampus':53,
                    'left_thalamus':10,'right_thalamus':49,'left_caudate':11,'right_caudate':50,
                    'left_putamen':12,'right_putamen':51,'left_pallidum':13,'right_pallidum':52,
                    'left_amygdala':18,'right_amygdala':54,'left_accumbens':26,'right_accumbens':58,
                    'left_hippocampus_CA2':550,'right_hippocampus_CA2':500,
                    'left_hippocampus_CA1':552,'right_hippocampus_CA1':502,
                    'left_hippocampus_CA4':556,'right_hippocampus_CA4':506,
                    'left_hippocampus_fissure':555,'right_hippocampus_fissure':505,
                    'left_amygdala_subiculum':557,'right_amygdala_subiculum':507,
                    'left_amygdala_presubiculum':554,'right_amygdala_presubiculum':504,}
    return structure_codes[structure]





# from os import system
# system('squeue -u hanganua > batch_queue')


# import pandas as pd

# if cluster == 'beluga':
#     df = pd.read_csv(file, sep=' ')

#     df.drop(df.iloc[:, 0:8], inplace=True, axis=1)
#     df.drop(df.iloc[:, 1:3], inplace=True, axis=1)
#     df.drop(df.iloc[:, 1:14], inplace=True, axis=1)

#     job_ids = df.iloc[:,0].tolist()
#     batch_files = df.iloc[:,1].dropna().tolist()+df.iloc[:,2].dropna().tolist()
    
#     start_batch_cmd = 'sbatch '
#     cacel_batch_cmd = 'scancel -i '

# elif cluster == 'helios':
#     df= pd.read_csv(file, sep='\t')
    
#     new = df.iloc[:,0].str.split("  ", n = 5, expand = True)
#     ls = list()
#     for val in new.iloc[:,0]:
#         ls.append(val)
#     job_ids = ls[3:]
#     #data["First Name"]= new[0]  
#     #data["Last Name"]= new[1] 
#     #data.drop(columns =["Name"], inplace = True)

#     start_batch_cmd = 'msub '
#     cacel_batch_cmd = 'qdel '

# print(job_ids)
# print(batch_files)

#for _id in job_ids:
#            print('canceling job: ',_id)
#            system(cacel_batch_cmd+_id)


# from time import sleep
#    sleep(10)
#    for file in batch_files:
#         print('starting job: ',file)
#         system(start_batch_cmd+file)