#!/bin/python
# Kim Phuong Pham 20200628;  Alexandru Hanganu 20200107


'''
1) read the folder with subjects SUBJECTS_DIR_RAW
3) extract paths for the anat MRIs
4) classify according to BIDS classification
5) create the BIDS json file that will be used by NIMB on the cluster
6)
'''


from os import path, listdir, getenv, walk
from collections import defaultdict
from sys import platform

import datetime as dt
import time, json


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



# def get_ls_sessions(ls):
# 	d_paths = {}
# 	ls_sessions = list()
#
# 	for mr_path in ls:
# 		for date in mr_path.split('/')[2:]:
# 			if validate_if_date(date):
# 				d_paths[date] = mr_path
# 				if date not in ls_sessions:
# 					ls_sessions.append(date)
# 	return ls_sessions, d_paths

# Kp_note:
# Current: Extract 1 path by day
# -> Output: Only get the first path found and skip other types in the same day
# New: Add Extract more path by day + type

def get_ls_sessions(ls):
	# add types
	mr_types = {'t1': ['t1', 'spgr', 'rage', ],
				'flair': ['flair', ],
				't2': ['t2', ],
				'dwi': ('hardi', 'dti', 'diffus',),
				'rsfmri': ['resting_state_fmri', 'rsfmri', ],
				'fieldmap': ['field_map', 'field_mapping', 'fieldmap', ]}
	d_paths = defaultdict(list)
	ls_sessions = list()

	for mr_path in ls:
		# add date to sessions
		for date in mr_path.split('/')[2:]:
			if validate_if_date(date):
				if date not in ls_sessions:
		 			ls_sessions.append(date)
				break
		# add paths by date and type
		for mr_name_ls in mr_types.values():
			for mr_name in mr_name_ls:
				if mr_name.lower() in mr_path.lower():
					d_paths[date].append(mr_path)
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
			for path in d_paths[date]:
				if path not in d_ses_paths[ses]:
					d_ses_paths[ses].append(path)
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



def get_dict_MR_files2process(SUBJECTS_DIR_RAW, NIMB_tmp):
	"""
	# only search for 2 number
	:return:
	"""
	f_new_subjects = path.join(NIMB_tmp,'new_subjects.json')

	d_subjects = dict()
	for subject in listdir(SUBJECTS_DIR_RAW):
			d_subjects[subject] = {}
			ls_MR_paths = exclude_MR_types(get_paths2dcm_files(SUBJECTS_DIR_RAW+'/'+subject))
			print("ls_MR_paths: ", ls_MR_paths)
			ls_sessions, d_paths = get_ls_sessions(ls_MR_paths)
			#print(ls_sessions)
			d_sessions = classify_by_sessions(ls_sessions)
			#print(d_sessions)
			dict_sessions_paths = make_dict_sessions_with_paths(d_paths, d_sessions)
			d_ses_MR_types = classify_by_MR_types(dict_sessions_paths)
			d_BIDS_structure = make_BIDS_structure(d_ses_MR_types)
			#print(d_BIDS_structure)
			d_subjects[subject] = d_BIDS_structure
			print("d_subjects:", d_subjects)
	with open(f_new_subjects,'w') as f:
		json.dump(d_subjects, f, indent=4)

