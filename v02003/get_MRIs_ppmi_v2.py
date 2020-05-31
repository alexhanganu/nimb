#!/bin/python
# created based on the get_MRIs_adni.py
#Alexandru Hanganu 20200107
'''
1) read the folder with subjects SUBJECTS_DIR_RAW
3) extract paths for the anat MRIs
4) classify according to BIDS classification
5) create the BIDS json file that will be used by NIMB on the cluster
6)
'''

project = 'ppmi'

from os import path, listdir, getenv, walk
from sys import platform
if platform == 'linux' or platform == 'linux2':
	path_home = getenv('HOME')+'/projects/def-hanganua/'+project
	path_scratch = getenv('SCRATCH')
	SUBJECTS_DIR_RAW = path_home+'/source/mri_unzipped'
if platform == 'win32':
	p = input('please write the path of mri_unzipped: ')
	if path.isdir(p):
		path_home = p
		SUBJECTS_DIR_RAW = p

if platform == 'darwin':
	# p = input('please write the path') #'/Users/van/Downloads/git/ppmi_data'
	SUBJECTS_DIR_RAW = path_home = '/Users/van/Downloads/git/ppmi_data'
import datetime as dt
import time, json

print('PATH_HOME is: ',path_home)
# ?print('PATH_SCRATCH is: ',path_scratch)

#f_with_downloaded_ids = '/materials/1.ls_subjects_downloaded.txt' # file with id of the downloaded participants
if platform == 'linux' or platform == 'linux2' :
	f_new_subjects = '/home/hvt/projects/def-hanganua/hvt_ppmi_tmp' + '/new_subjects.json'
	logf = path_scratch+'/log_'+project+'_'+str(time.strftime('%Y%m%d_%H_%M',time.localtime()))+'.txt'
	open(logf,'w')
if platform == 'darwin':
	f_new_subjects = '/Users/van/Downloads/git/ppmi_data' + '/new_subjects.json'
if platform == 'win32':
	f_new_subjects = 'new_subjects.json'

def adni_get_list_downloaded_subjects(file):
	subjects = list()
	for line in open(file,'r').readlines():
		if 'DOWNLOAD' not in line and len(line)>2:
			for subject in line.strip('\n\r').split(','):
				if len(subject)>1:
					subjects.append(subject)
	return subjects


def get_paths2dcm_files(path_root):
	ls_paths = list()
	for root, dirs, files in walk(path_root):
		for file in files:
			if '.dcm' in file:
				dir_path = root.replace('\\','/')
				dir_src = dir_path+'/'+sorted(listdir(dir_path))[0]
				ls_paths.append(dir_src)
				break
			if '.nii' in file:
				dir_src = root.replace('\\','/')+'/'+file
				ls_paths.append(dir_src)
				break
	return ls_paths



def exclude_MR_types(ls):
	exclude_MR_types = ['calibration','localizer','loc','moco','perfusion','tse',
						'survey','scout','hippo','cbf','isotropic','fractional',
						'pasl','multi_reset','dual_echo','gre','average_dc',]
	ls_iter = ls.copy()
	for mr_path in ls_iter:
		for ex_type in exclude_MR_types:
			if ex_type.lower() in mr_path.lower():
				ls.remove(mr_path)
				break
	return ls



def validate_if_date(date_text):
	try:
		date = dt.datetime.strptime(date_text, '%Y-%m-%d_%H_%M_%S.%f')
		return True
	except ValueError:
		return False



def get_ls_sessions(ls):
	d_paths = {}
	ls_sessions = list()
	for mr_path in ls:
		for date in mr_path.split('/')[2:]:
			if validate_if_date(date):
				d_paths[date] = mr_path
				if date not in ls_sessions:
					ls_sessions.append(date)
	return ls_sessions, d_paths


def classify_by_sessions(ls):
	d = {}
	oneday = dt.timedelta(days=1)
	n = 1
	d['ses-'+str(n)] = list()
	for ses in sorted(ls):
		if len(d['ses-'+str(n)])<1:
			d['ses-'+str(n)].append(ses)
		else:
			date_new = dt.datetime.strptime(ses, '%Y-%m-%d_%H_%M_%S.%f')
			date_before = dt.datetime.strptime(d['ses-'+str(n)][0], '%Y-%m-%d_%H_%M_%S.%f')
			if date_new-date_before < oneday:
				d['ses-'+str(n)].append(ses)
			else:
				n +=1
				d['ses-'+str(n)] = list()
				d['ses-'+str(n)].append(ses)
	return d


def make_dict_sessions_with_paths(d_paths, d_sessions):
	d_ses_paths = {}
	for ses in d_sessions:
		d_ses_paths[ses] = list()
		for date in d_sessions[ses]:
			if d_paths[date] not in d_ses_paths[ses]:
				d_ses_paths[ses].append(d_paths[date])
	return d_ses_paths


def get_MR_types(mr_path):
	mr_types = {'t1':['t1','spgr','rage',],
				'flair':['flair',],
				't2':['t2',],
				'dwi':('hardi','dti','diffus',),
				'rsfmri':['resting_state_fmri','rsfmri',],
				'fieldmap':['field_map','field_mapping','fieldmap',]}
	mr_found = False
	for mr_type in mr_types:
		for mr_name in mr_types[mr_type]:
			if mr_name.lower() in mr_path.lower():
				mr_found = True
				res = mr_type
				break
		if mr_found:
			break
	if mr_found:
		return res
	else:
		return 'none'



def classify_by_MR_types(dict_sessions_paths):
	d_ses_MR_types = {}
	for ses in dict_sessions_paths:
		d_ses_MR_types[ses] = {}
		for mr_path in dict_sessions_paths[ses]:
			mr_type = get_MR_types(mr_path)
			if mr_type != 'none':
				if mr_type not in d_ses_MR_types[ses]:
					d_ses_MR_types[ses][mr_type] = list()
				d_ses_MR_types[ses][mr_type].append(mr_path)
			else:
				print(mr_type,mr_path,'none')
	return d_ses_MR_types



def make_BIDS_structure(d_ses_MR_types):
	BIDS_groups = {'anat':['t1','flair','t2'],'dwi':['dwi','bval','bvec'],'func':['rsfmri','fieldmap',]}
	d_BIDS_structure = {}
	for ses in d_ses_MR_types:
		d_BIDS_structure[ses] = {}
		for key in d_ses_MR_types[ses]:
			for group in BIDS_groups:
				if key in BIDS_groups[group]:
					if group not in d_BIDS_structure[ses]:
						d_BIDS_structure[ses][group] = {}
					d_BIDS_structure[ses][group][key] = d_ses_MR_types[ses][key]
					break
	return d_BIDS_structure



def get_dict_MR_files2process():
	"""
	# only search for 2 number
	:return:
	"""
	d_subjects = dict()
	#for subject in ls_subjects:
		#if subject in listdir(SUBJECTS_DIR_RAW):
	for subject in listdir(SUBJECTS_DIR_RAW):
			if subject.startswith("."):
				continue
			d_subjects[subject] = {}
			ls_MR_paths = exclude_MR_types(get_paths2dcm_files(SUBJECTS_DIR_RAW+'/'+subject))
			print(ls_MR_paths)
			ls_sessions, d_paths = get_ls_sessions(ls_MR_paths)
			print(ls_sessions)
			d_sessions = classify_by_sessions(ls_sessions)
			print(d_sessions)
			dict_sessions_paths = make_dict_sessions_with_paths(d_paths, d_sessions)
			d_ses_MR_types = classify_by_MR_types(dict_sessions_paths)
			d_BIDS_structure = make_BIDS_structure(d_ses_MR_types)
			print(d_BIDS_structure)
			d_subjects[subject] = d_BIDS_structure
	return d_subjects




def log(message):
	with open(logf,'a') as f:
		if type(message) == str:
			f.write(message)
		if type(message) == list:
			f.write('      ')
			for val in message:
				f.write(val+'\t')
			f.write('\n')

		
		
		
def chk_visual(d_subjects, mr_type, start):
	'''code specifically for ADNI db'''
	for subj in d_subjects:
		print('\n\n',subj)
		log('\n\n'+subj+'\n')
		for ses in d_subjects[subj]:
			print(' ',ses)
			log('  '+ses+'\n')
			if mr_type != 'all':
				if 'anat' in d_subjects[subj][ses]:
					if mr_type in d_subjects[subj][ses]['anat']:
						print('   '+mr_type)
						log('    '+mr_type+'\n')
						for key in d_subjects[subj][ses]['anat'][mr_type]:
							print('     ',key.split('/')[start:])
							log((key.split('/')[start:]))
			else:
				for BIDS_type in d_subjects[subj][ses]:
					log('    '+BIDS_type+'\n')
					for mr_type in d_subjects[subj][ses][BIDS_type]:
						log('      '+mr_type+'\n')
						for key in d_subjects[subj][ses][BIDS_type][mr_type]:
							print('     ',key.split('/')[start:])
							log((key.split('/')[start:]))



#ls_subjects = adni_get_list_downloaded_subjects(path_home+f_with_downloaded_ids)
d_subjects = get_dict_MR_files2process()
with open(f_new_subjects,'w') as f:
	json.dump(d_subjects, f, indent=4)

#chk_visual(d_subjects, 't1',8)
#chk_visual(d_subjects, 't2',8)
#chk_visual(d_subjects, 'flair',8)
#chk_visual(d_subjects, 'all',8)


'''
def adni_get_dict_downloaded_subjects(file):
	
	#reading the subjects from the f_with_downloaded_ids file, these are the subjects
	#that were downloaded from the ADNI website. Sending all subjects to a dict "subjects"
	#structure is: 'DOWNLOAD 19 -1631, 19.4 Gb, 10hrs':['subject','subject',...]
	
	d_downloaded_subjects = dict()
    
	with open(file,'r') as f:
		for line in f:
			if 'DOWNLOAD' in line:
				file_name = line.strip('\n')
				d_downloaded_subjects[file_name] = list()
			else:
				d_downloaded_subjects[file_name].append(line.strip('\n'))
	return d_downloaded_subjects

#d_subjects = adni_get_dict_downloaded_subjects(path_home+f_with_downloaded_ids)


def subjects_less_f(limit, ls_all_raw_subjects):
    ls_subjects = list()
    for folder in ls_all_raw_subjects:
        if len([f for f in listdir(SUBJECTS_DIR_RAW+folder)])<limit:
            ls_subjects.append(folder)

    return ls_subjects

def subjects_nodcm(ls_all_raw_subjects):
    ls_subjects = list()
    for folder in ls_all_raw_subjects:
        for file in listdir(SUBJECTS_DIR_RAW+folder):
            if not file.endswith('.dcm'):
                ls_subjects.append(folder)
                break
    return ls_subjects

def subj_no_t1(ls_all_raw_subjects):
    ls_subjects = list()
    for folder in ls_all_raw_subjects:
        if '_flair' in folder:
                if folder.replace('_flair','_t1') in ls_all_raw_subjects:
                    pass
                else:
                    ls_subjects.append(folder)
        if '_t2' in folder:
                if folder.replace('_t2','_t1') in ls_all_raw_subjects:
                    pass
                else:
                    ls_subjects.append(folder)
    return ls_subjects


def check_folder():
	ls_subjects_no_t1 = subj_no_t1(listdir(SUBJECTS_DIR_RAW))
	ls_subjects_nodcm = subjects_nodcm(listdir(SUBJECTS_DIR_RAW))
	ls_subjects_less = subjects_less_f(35, listdir(SUBJECTS_DIR_RAW))
	ls_subjects_incomplete = ls_subjects_no_t1 + [i for i in ls_subjects_nodcm if i not in 
		ls_subjects_no_t1] + [i for i in ls_subjects_less if i not in ls_subjects_no_t1]
	print(len(ls_subjects_no_t1), len(ls_subjects_nodcm), len(ls_subjects_less)))
	print(len(ls_subjects_incomplete))

'''





'''script reads the 'nacc_tp_sorted.csv' and creates the file
..._dirs_to_process.csv that has the folders to be copied and 
the new names to classify - t1, flair, dwi.
'''
'''
from os import listdir, chdir, path, mkdir, walk
import pandas

PATH = 'C:/Users/Jessica/Documents/s2019-NPS-db/'
fs = 'freesurfer_nacc/'


dirs_dst = {'dst': fs+'raw/','tmp' : fs+'tmp/','dst2' : fs+'raw2/',}
chdir(PATH+fs)
for dir in dirs_dst:
    if not path.isdir(PATH+dirs_dst[dir]):
        mkdir(PATH+dirs_dst[dir])
chdir(PATH+dirs_dst['tmp'])

db = 'nacc_tp_sorted.csv'
df = pandas.read_csv(PATH+db)
db_classified = 'nacc_dirs_classified.csv'
tp_classified = 'nacc_dirs_tp_classified.csv'
sub_dirs_classified = 'nacc_sub_dirs_per_id.csv'

mri_types_and_names = {'T1':['T1','FSPGR','Fspgr','SPGR','MPRAGE'],
             'FLAIR':['FLAIR','flair','Flair',],
             'T2':['T2','T2*',],
             'DWI':['HARDI','DTI','Dti',]}
endings = {'T1':'_t1','FLAIR':'_flair','T2':'_t2','DWI':'_dwi'}





#from dcm_read import ReadDcmMetadata, chk_if_f_is_dcm
# details: some DTI have blip_up and blip_down
# add module to check folder for non-dcm files ?

class NACCRenameClassify():

    def __init__(self):
        self.error_id_folders = []
        self.classif_tp_id_f = {}
        self.classif_id_tp_f = {}
        self.ls_f_per_id = {}
        for row in range(0,len(df['id'])):
            print(row)
            ls_id_mri = df.iloc[row].tolist()
            id = ls_id_mri[0]
            log('\nID: '+str(id)+'; row: '+str(row)+'; ')
            for dir_id in listdir(PATH+dirs_dst['dst2']):
                if id in dir_id:
                    self.classif_id_tp_f[dir_id] = {}
                    log('dir_id: '+str(dir_id)+':')
                    self.Read_dir_id(dir_id, [i for i in ls_id_mri[1:] if type(i) == str])
        self.dict2csv()
        print("DONE")


    def chk_zip_to_folders(self, ls_files, ls_folders):
        if len(ls_files) == len(ls_folders):
            answer = True
        else:
            print('length is different')
            answer = False
        return answer
    def check_dir_name(self, dir):
        dir_name = ''
        for mri_type in mri_types_and_names:
            for name in mri_types_and_names[mri_type]:
                if name in dir:
                    dir_name = id+'_'+fname+'_tp'+str(tp)+endings[mri_type]
        return dir_name
    def dict2csv(self):
        d_dirs_to_process = dict()
        for tp in self.classif_tp_id_f:
            d_dirs_to_process[tp] = dict()
            for mri_type in mri_types_and_names:
                d_dirs_to_process[tp][mri_type] = dict()
                for id in self.classif_tp_id_f[tp]:
                    for dir in self.classif_tp_id_f[tp][id]:
                        if mri_type == self.classif_tp_id_f[tp][id][dir]['classified_as']:
                            d_dirs_to_process[tp][mri_type][self.classif_tp_id_f[tp][id][dir]['new_dir_name']] = self.classif_tp_id_f[tp][id][dir]['dir2copy']
        for tp in d_dirs_to_process:
            df_dirs_to_process = pandas.DataFrame.from_dict(d_dirs_to_process[tp])
            df_dirs_to_process.to_csv(PATH+tp+'_'+'dirs_to_process.csv')

	    # 
	        # for tp in self.ls_f_per_id:
            # df = pandas.DataFrame.from_dict(self.ls_f_per_id[tp]).transpose()
            # df.to_csv(PATH+tp+'_'+sub_dirs_classified)
        # for tp in self.classif_tp_id_f:
            # for id in self.classif_tp_id_f[tp]:
                # for file_name in self.classif_tp_id_f[tp][id]:
                    # for mri_type in ['T1',]:#mri_types_and_names:
                        # for name in mri_types_and_names[mri_type]:
                            # if name in file_name:
                                # df_tmp = pandas.DataFrame(self.classif_tp_id_f[tp][id][file_name], index=[id])
                                # if not path.isfile('C:/Users/Jessica/Desktop/tmp.csv'):
                                    # df_metadata = df_tmp.copy()
                                    # df_metadata.to_csv('C:/Users/Jessica/Desktop/tmp.csv')
                                # else:
                                    # df_metadata = 
                                    # df_metadata[:1] = df_tmp.iloc[:1]
                                    # print(df_metadata)
                                    
                                #df_metadata.to_csv(PATH+'metadata/'+tp+'_'+mri_type+'_'+id+'_metadata.csv')
        # df = pandas.DataFrame.from_dict(self.classif_id_tp_f).transpose()
        # df.to_csv(PATH+tp_classified)
    def populate_tp(self, ls_tp_dirs, dir_id):
        for tp_dir in ls_tp_dirs:
            tp = tp_dir[:3]
            if tp not in self.classif_tp_id_f:
                self.classif_tp_id_f[tp] = {}
            if tp not in self.ls_f_per_id:
                self.ls_f_per_id[tp] = {}
            if tp not in self.classif_id_tp_f[dir_id]:
                self.classif_id_tp_f[dir_id][tp] = {}
            if dir_id not in self.ls_f_per_id[tp]:
                self.ls_f_per_id[tp][dir_id] = {}
            if dir_id not in self.classif_tp_id_f[tp]:
                self.classif_tp_id_f[tp][dir_id] = {}
    def populate_ls_sub_dirs(self, path_dir_id, dir_id):
        ls_tp_dirs = listdir(path_dir_id)
        for tp_dir in ls_tp_dirs:
            tp = tp_dir[:3]
            n = 1
            for sub_dir in listdir(path_dir_id+tp_dir):
                for root, dirs, files in walk(path_dir_id+tp_dir+'/'+sub_dir):# traverse root directory, and list directories as dirs and files as files
                    for file in files:
                        if '.dcm' in file:
                            dir_src = root.replace('\\','/')
                            self.ls_f_per_id[tp][dir_id][n] = dir_src.replace(path_dir_id+tp_dir+'/','')
                            break
                        elif len(listdir(root)) > 10:
                            path_f_dcm = root.replace('\\','/')+'/'+listdir(root)[0]
                            if chk_if_f_is_dcm(path_f_dcm):
                                dir_src = root.replace('\\','/')
                                self.ls_f_per_id[tp][dir_id][n] = dir_src.replace(path_dir_id+tp_dir+'/','')
                                break
                n+= 1
    def populate_d(self, dir_id, tp, sub_dir):
        self.classif_tp_id_f[tp][dir_id][dir_id+'_'+sub_dir] = {}
        subgroups = ('classified_as','new_dir_name','dir_description','dcm_file','dir2copy')
        for subgroup in subgroups:
            self.classif_tp_id_f[tp][dir_id][dir_id+'_'+sub_dir][subgroup] = ''
    def get_dcm_f(self, path_sub_dir, dir_id, tp, sub_dir):
        path_f_dcm = 'NONE'
        for root, dirs, files in walk(path_sub_dir):# traverse root directory, and list directories as dirs and files as files
            for file in files:
                if '.dcm' in file[-4:]:
                    self.populate_d(dir_id, tp, sub_dir)
                    dir_src = root.replace('\\','/')
                    path_f_dcm = dir_src+'/'+file
                    self.classif_tp_id_f[tp][dir_id][dir_id+'_'+sub_dir]['dir2copy'] = dir_src
                    self.classif_tp_id_f[tp][dir_id][dir_id+'_'+sub_dir]['dcm_file'] = path_f_dcm
                    break
                elif len(root)>10:
                    path_f_dcm = root.replace('\\','/')+'/'+listdir(root)[0]
                    if chk_if_f_is_dcm(path_f_dcm):
                        self.populate_d(dir_id, tp, sub_dir)
                        dir_src = root.replace('\\','/')
                        self.classif_tp_id_f[tp][dir_id][dir_id+'_'+sub_dir]['dir2copy'] = dir_src
                        self.classif_tp_id_f[tp][dir_id][dir_id+'_'+sub_dir]['dcm_file'] = path_f_dcm
                        break
        return path_f_dcm

    def classify_folder(self, dir_id, tp, sub_dir):
        for mri_type in mri_types_and_names:
            for name in mri_types_and_names[mri_type]:
                if name in self.classif_tp_id_f[tp][dir_id][dir_id+'_'+sub_dir]['metadata']['SeriesDescription']:
                    dir_end = endings[mri_type]
                    self.classif_tp_id_f[tp][dir_id][dir_id+'_'+sub_dir]['classified_as'] = mri_type
                    self.classif_tp_id_f[tp][dir_id][dir_id+'_'+sub_dir]['new_dir_name'] = dir_id+'_'+tp+dir_end
                    self.classif_id_tp_f[dir_id][tp][dir_id+'_'+sub_dir] = dir_end
                    break			
    def Read_dir_id(self, dir_id, ls_files):
        path_dir_id = PATH+dirs_dst['dst2']+dir_id+'/'
        ls_tp_dirs = listdir(path_dir_id)
        if self.chk_zip_to_folders(ls_files, ls_tp_dirs):
            self.populate_tp(ls_tp_dirs, dir_id)
            print('  ',dir_id, ' length ok')
            self.populate_ls_sub_dirs(path_dir_id, dir_id)
            for tp_dir in ls_tp_dirs:
                tp = tp_dir[:3]
                for sub_dir in listdir(path_dir_id+tp_dir):
                    path_sub_dir = path_dir_id+tp_dir+'/'+sub_dir
                    if path.isfile(path_sub_dir):
                        print('  path is file', path_sub_dir)
                        f_dcm = self.get_dcm_f(path_dir_id, dir_id, tp, tp_dir)
                        if f_dcm != 'NONE':
                            self.Read_tp_dirs(path_dir_id, dir_id, tp, tp_dir, f_dcm)
                            break
                    else:
                        f_dcm = self.get_dcm_f(path_sub_dir, dir_id, tp, sub_dir)
                        if f_dcm != 'NONE':
                            self.Read_tp_dirs(path_sub_dir, dir_id, tp, sub_dir, f_dcm)
        else:
            self.error_id_folders.append(dir_id)
            pass
    def Read_tp_dirs(self, path_sub_dir, dir_id, tp, sub_dir, f_dcm):
        read_metadata = ReadDcmMetadata(f_dcm)
        metadata = read_metadata.metadata
        self.classif_tp_id_f[tp][dir_id][dir_id+'_'+sub_dir]['metadata'] = metadata
        self.classify_folder(dir_id, tp, sub_dir)



def chk_nii():
    import shutil
    for dir_id in listdir(PATH+dirs_dst['dst2']):
        for root, dirs, files in walk(PATH+dirs_dst['dst2']+dir_id+'/'):# traverse root directory, and list directories as dirs and files as files
            for file in files:
                if '.nii' in file:
                    path_f_dcm = root.replace('\\','/')+'/'+file
                    print('moving: ',dir_id, ' ',file)
                    shutil.move(path_f_dcm, PATH+fs+'raw_nii.gz/'+dir_id+'_'+file)

def move_files():
    import pandas as pd
    import shutil

    for tp in range(2,10):
            df = pd.read_csv(PATH+'tp'+str(tp)+'_dirs_to_process.csv')
            for col in df.columns[1:]:
                df_col = df[[df.columns[0],col]].dropna()
                for row in range(0,len(df_col[col])):
                    name = df_col.iloc[row,0]
                    f = df_col.iloc[row,1]
                    print(f, PATH+dirs_dst['dst']+name)
                    try:
                        shutil.move(f, PATH+dirs_dst['dst']+name)
                    except FileNotFoundError:
                        pass



# chk_nii()
# NACCRenameClassify()
# move_files()

def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in walk(start_path):
        for f in filenames:
            fp = path.join(dirpath, f)
            total_size += path.getsize(fp)
    return total_size

def rm_empty_folder():
    import shutil
    for DIR in listdir(PATH+dirs_dst['dst2']):
        size = get_size(PATH+dirs_dst['dst2']+DIR)
        if size == 0:
            print('deleting ',DIR)
            shutil.rmtree(PATH+dirs_dst['dst2']+DIR)
        for subDIR in listdir(PATH+dirs_dst['dst2']+DIR):
            size_subdir = get_size(PATH+dirs_dst['dst2']+DIR+'/'+subDIR)
            if size == 0:
                print('deleting ',DIR)
                shutil.rmtree(PATH+dirs_dst['dst2']+DIR)

# rm_empty_folder()

'''
