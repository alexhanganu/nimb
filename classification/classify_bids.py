#!/bin/python
"""
authors:
Alexandru Hanganu
Kim Phuong Pham
"""

'''
1) read the folder with subjects
3) extract paths for the anat MRIs
4) classify according to BIDS classification
5) create the BIDS json file that will be used by NIMB for processing
6)
'''

from os import path, listdir, getenv, walk
from collections import defaultdict
from sys import platform

import datetime as dt
import time, json

from classify_definitions import mr_modalities, BIDS_types, mr_types_2exclude

class MakeBIDS_subj2process():
    def __init__(self, DIR_SUBJECTS,
                NIMB_tmp,
                multiple_T1_entries = False,
                flair_t2_add = False):
        self.DIR_SUBJECTS = DIR_SUBJECTS
        self.NIMB_tmp  = NIMB_tmp
        self.multiple_T1_entries  = multiple_T1_entries
        self.flair_t2_add  = flair_t2_add
        self.d_subjects = dict()
        print("classification of new subjects is running ...")

    def run(self):
        for subject in listdir(self.DIR_SUBJECTS):#[-18:-17]:
#            print(subject)
            self.d_subjects[subject] = {}
            path_2mris = self._get_MR_paths(path.join(self.DIR_SUBJECTS, subject))
            ls_MR_paths = self.exclude_MR_types(path_2mris)
#            print("ls_MR_paths: ", ls_MR_paths)
            ls_sessions, d_paths = self.get_ls_sessions(ls_MR_paths)
#            print(ls_sessions)
            d_sessions = self.classify_by_sessions(ls_sessions)
#            print(d_sessions)
            dict_sessions_paths = self.make_dict_sessions_with_paths(d_paths, d_sessions)
            d_ses_MR_types = self.classify_by_MR_types(dict_sessions_paths)
            d_BIDS_structure = self.make_BIDS_structure(d_ses_MR_types)
#            print(d_BIDS_structure)
            self.d_subjects[subject] = d_BIDS_structure
            self.save_json(self.DIR_SUBJECTS, "all_subjects", self.d_subjects)
        print("classification of new subjects is complete")
        if self.multiple_T1_entries == 1:
            from classification.get_mr_params import verify_MRIs_for_similarity
            self.d_subjects = verify_MRIs_for_similarity(self.d_subjects, self.NIMB_tmp, self.flair_t2_add)
        else:
            self.d_subjects = self.keep_only1_T1(self.d_subjects)

        f_new_subjects = path.join(self.NIMB_tmp,'new_subjects.json')
        self.save_json(self.NIMB_tmp, f_new_subjects, self.d_subjects)
        if path.exists(path.join(self.NIMB_tmp, f_new_subjects)):
            return True
        else:
            return False

    def _get_MR_paths(self, path2subj):
        if '.zip' in path2subj:
            content = self.chk_if_ziparchive(path2subj)
            path_2mris = self.get_paths2dcm_files_from_ls(content)
        elif path.isdir(path2subj):
            path_2mris = self.get_paths2dcm_files_from_DIR(path2subj)
        else:
            print(path2subj,' not a dir and not a .zip file')
            path_2mris = []
        return path_2mris

    def chk_if_ziparchive(self, file):
        from distribution.manage_archive import ZipArchiveManagement
        unzip = ZipArchiveManagement(file)
        if unzip.chk_if_zipfile():
            return unzip.zip_file_content()
        else:
            return []

    def get_paths2dcm_files_from_ls(self, ls_content):
        ls_paths = list()
        for val in ls_content:
            if 'dcm' in val or '.nii' in val:
                path_mri = path.dirname(val)
                if path_mri not in ls_paths:
                    ls_paths.append(path_mri)
        return ls_paths

    def get_paths2dcm_files_from_DIR(self, path_root):
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
        
    def exclude_MR_types(self, ls):
        ls_iter = ls.copy()
        for mr_path in ls_iter:
            for ex_type in mr_types_2exclude:
                if ex_type.lower() in mr_path.lower():
                    ls.remove(mr_path)
                    break
        return ls

    def validate_if_date(self, date_text):
        try:
            date = dt.datetime.strptime(date_text, '%Y-%m-%d_%H_%M_%S.%f')
            return True
        except ValueError:
            return False

    def get_ls_sessions(self, ls):
        # add types
        d_paths = defaultdict(list)
        ls_sessions = list()

        for mr_path in ls:
            # add date to sessions
            for date in mr_path.split('/')[2:]:
                if self.validate_if_date(date):
                    if date not in ls_sessions:
                        ls_sessions.append(date)
                    break
            # add paths by date and type
            for mr_name_ls in mr_modalities.values():
                for mr_name in mr_name_ls:
                    if mr_name.lower() in mr_path.lower():
                        d_paths[date].append(mr_path)
        return ls_sessions, d_paths
    
    def classify_by_sessions(self, ls):
        d = {}
        oneday = dt.timedelta(days=1)
        n = 1
        ses_name = 'ses-'+str(n).zfill(2)
        d[ses_name] = list()
        for ses in sorted(ls):
            if len(d[ses_name])<1:
                d[ses_name].append(ses)
            else:
                date_new = dt.datetime.strptime(ses, '%Y-%m-%d_%H_%M_%S.%f')
                date_before = dt.datetime.strptime(d[ses_name][0], '%Y-%m-%d_%H_%M_%S.%f')
                if date_new-date_before < oneday:
                    d[ses_name].append(ses)
                else:
                    n +=1
                    ses_name = 'ses-'+str(n).zfill(2)
                    d[ses_name] = list()
                    d[ses_name].append(ses)
        return d

    def make_dict_sessions_with_paths(self, d_paths, d_sessions):
        d_ses_paths = {}

        for ses in d_sessions:
            d_ses_paths[ses] = list()
            if d_sessions[ses]:
                for date in d_sessions[ses]:
                    for path in d_paths[date]:
                        if path not in d_ses_paths[ses]:
                            d_ses_paths[ses].append(path)
            else:
                for key in d_paths:
                    for path in d_paths[key]:
                        if path not in d_ses_paths[ses]:
                            d_ses_paths[ses].append(path)
        return d_ses_paths

    def get_MR_types(self, mr_path):
        mr_found = False
        for mr_type in mr_modalities:
            for mr_name in mr_modalities[mr_type]:
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

    def classify_by_MR_types(self, dict_sessions_paths):
        d_ses_MR_types = {}
        for ses in dict_sessions_paths:
            d_ses_MR_types[ses] = {}
            for mr_path in dict_sessions_paths[ses]:
                mr_type = self.get_MR_types(mr_path)
                if mr_type != 'none':
                    if mr_type not in d_ses_MR_types[ses]:
                        d_ses_MR_types[ses][mr_type] = list()
                    d_ses_MR_types[ses][mr_type].append(mr_path)
                else:
                    print(mr_type,mr_path,'none')
        return d_ses_MR_types


    def subjects_less_f(self, limit, ls_all_raw_subjects):
        ls_subjects = list()
        for folder in ls_all_raw_subjects:
            if len([f for f in listdir(SUBJECTS_DIR_RAW+folder)])<limit:
                ls_subjects.append(folder)

        return ls_subjects

    def subjects_nodcm(self, ls_all_raw_subjects):
        ls_subjects = list()
        for folder in ls_all_raw_subjects:
            for file in listdir(SUBJECTS_DIR_RAW+folder):
                if not file.endswith('.dcm'):
                    ls_subjects.append(folder)
                    break
        return ls_subjects

    def subj_no_t1(self, ls_all_raw_subjects):
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

    def make_BIDS_structure(self, d_ses_MR_types):
        d_BIDS_structure = {}
        for ses in d_ses_MR_types:
            d_BIDS_structure[ses] = {}
            for key in d_ses_MR_types[ses]:
                for group in BIDS_types:
                    if key in BIDS_types[group]:
                        if group not in d_BIDS_structure[ses]:
                            d_BIDS_structure[ses][group] = {}
                        d_BIDS_structure[ses][group][key] = d_ses_MR_types[ses][key]
                        break
        return d_BIDS_structure

    def keep_only1_T1(self, d_subjects):
        for subject in d_subjects:
            for session in d_subjects[subject]:
                if 'anat' in d_subjects[subject][session] and 't1' in d_subjects[subject][session]['anat']:
                    d_subjects[subject][session]['anat']['t1'] = d_subjects[subject][session]['anat']['t1'][:1]
                    if 'flair' in d_subjects[subject][session]['anat']:
                        d_subjects[subject][session]['anat'].pop('flair', None)
                    if 't2' in d_subjects[subject][session]['anat']:
                        d_subjects[subject][session]['anat'].pop('t2', None)
        return d_subjects

    def save_json(self, NIMB_tmp, file, dictionary):
        with open(path.join(NIMB_tmp, file),'w') as f:
            json.dump(dictionary, f, indent=4)

# ===============================================================
# ===============================================================
# BELOW can be removed after the class is confirmed to be working
# ===============================================================
# ===============================================================


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
	# add types
	mr_modalities = {'t1': ['t1', 'spgr', 'rage', ],
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
		for mr_name_ls in mr_modalities.values():
			for mr_name in mr_name_ls:
				if mr_name.lower() in mr_path.lower():
					d_paths[date].append(mr_path)
	return ls_sessions, d_paths

def classify_by_sessions(ls):
	d = {}
	oneday = dt.timedelta(days=1)
	n = 1
	ses_name = 'ses-'+str(n).zfill(2)
	d[ses_name] = list()
	for ses in sorted(ls):
		if len(d[ses_name])<1:
			d[ses_name].append(ses)
		else:
			date_new = dt.datetime.strptime(ses, '%Y-%m-%d_%H_%M_%S.%f')
			date_before = dt.datetime.strptime(d[ses_name][0], '%Y-%m-%d_%H_%M_%S.%f')
			if date_new-date_before < oneday:
				d[ses_name].append(ses)
			else:
				n +=1
				ses_name = 'ses-'+str(n).zfill(2)
				d[ses_name] = list()
				d[ses_name].append(ses)
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
	mr_modalities = {'t1':['t1','spgr','rage',],
				'flair':['flair',],
				't2':['t2',],
				'dwi':('hardi','dti','diffus',),
				'rsfmri':['resting_state_fmri','rsfmri',],
				'fieldmap':['field_map','field_mapping','fieldmap',]}
	mr_found = False
	for mr_type in mr_modalities:
		for mr_name in mr_modalities[mr_type]:
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


def make_BIDS_structure(d_ses_MR_types):
	BIDS_types = {'anat':['t1','flair','t2'],'dwi':['dwi','bval','bvec'],'func':['rsfmri','fieldmap',]}
	d_BIDS_structure = {}
	for ses in d_ses_MR_types:
		d_BIDS_structure[ses] = {}
		for key in d_ses_MR_types[ses]:
			for group in BIDS_types:
				if key in BIDS_types[group]:
					if group not in d_BIDS_structure[ses]:
						d_BIDS_structure[ses][group] = {}
					d_BIDS_structure[ses][group][key] = d_ses_MR_types[ses][key]
					break
	return d_BIDS_structure


def keep_only1_T1(d_subjects):
    for subject in d_subjects:
        for session in d_subjects[subject]:
            if 'anat' in d_subjects[subject][session] and 't1' in d_subjects[subject][session]['anat']:
                d_subjects[subject][session]['anat']['t1'] = d_subjects[subject][session]['anat']['t1'][:1]
                if 'flair' in d_subjects[subject][session]['anat']:
                    d_subjects[subject][session]['anat'].pop('flair', None)
                if 't2' in d_subjects[subject][session]['anat']:
                    d_subjects[subject][session]['anat'].pop('t2', None)
    return d_subjects


def save_json(NIMB_tmp, file, dictionary):
    with open(path.join(NIMB_tmp, file),'w') as f:
        json.dump(dictionary, f, indent=4)


def get_dict_MR_files2process(DIR_SUBJECTS, NIMB_tmp, multiple_T1_entries, flair_t2_add):
    """
    # only search for 2 numbers
    :return:
    """
    from .get_mr_params import verify_MRIs_for_similarity

    print("classification of new subjects is running ...")
    d_subjects = dict()
    for subject in listdir(DIR_SUBJECTS):
        d_subjects[subject] = {}
        ls_MR_paths = exclude_MR_types(get_paths2dcm_files(path.join(DIR_SUBJECTS,subject)))
        #print("ls_MR_paths: ", ls_MR_paths)
        ls_sessions, d_paths = get_ls_sessions(ls_MR_paths)
        #print(ls_sessions)
        d_sessions = classify_by_sessions(ls_sessions)
        #print(d_sessions)
        dict_sessions_paths = make_dict_sessions_with_paths(d_paths, d_sessions)
        d_ses_MR_types = classify_by_MR_types(dict_sessions_paths)
        d_BIDS_structure = make_BIDS_structure(d_ses_MR_types)
        #print(d_BIDS_structure)
        d_subjects[subject] = d_BIDS_structure
        save_json(DIR_SUBJECTS, "all_subjects", d_subjects)
    print("classification of new subjects is complete")
    if multiple_T1_entries == 1:
        from get_mr_params import verify_MRIs_for_similarity
        d_subjects = verify_MRIs_for_similarity(d_subjects, NIMB_tmp, flair_t2_add)
    else:
        d_subjects = keep_only1_T1(d_subjects)

    f_new_subjects = path.join(NIMB_tmp,'new_subjects.json')
    save_json(NIMB_tmp, f_new_subjects, d_subjects)
    if path.exists(path.join(NIMB_tmp, f_new_subjects)):
        return True
    else:
        return False
