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

from os import path, listdir, getenv, walk, system
from collections import defaultdict
from sys import platform

import datetime as dt
import time, json
import logging

from .classify_definitions import mr_modalities, BIDS_types, mr_types_2exclude
from .utils import get_path, save_json


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class MakeBIDS_subj2process():
    def __init__(self, DIR_SUBJECTS,
                NIMB_tmp,
                multiple_T1_entries = False,
                flair_t2_add = False):
        self.DIR_SUBJECTS = DIR_SUBJECTS
        self.NIMB_tmp  = NIMB_tmp
        self.multiple_T1_entries  = multiple_T1_entries
        self.flair_t2_add  = flair_t2_add
        self.MR_type_default = 't1'
        self.d_subjects = dict()
        log.info("classification of new subjects is running ...")

    def run(self):
        for self.subject in listdir(self.DIR_SUBJECTS):
#            print(self.subject)
            self.d_subjects[self.subject] = {}
            path_2mris = self._get_MR_paths(path.join(self.DIR_SUBJECTS, self.subject))
            if path_2mris:
                ls_MR_paths = self.exclude_MR_types(path_2mris)
#                print("ls_MR_paths: ", ls_MR_paths)
                ls_sessions, d_paths = self.get_ls_sessions(ls_MR_paths)
#                print(ls_sessions)
                d_sessions = self.classify_by_sessions(ls_sessions)
#                print(d_sessions)
                dict_sessions_paths = self.make_dict_sessions_with_paths(d_paths, d_sessions)
#                print(dict_sessions_paths)
                d_ses_MR_types = self.classify_by_MR_types(dict_sessions_paths)
#                print(d_ses_MR_types)
                d_BIDS_structure = self.make_BIDS_structure(d_ses_MR_types)
#                print(d_BIDS_structure)
                self.d_subjects[self.subject] = d_BIDS_structure
                save_json(self.d_subjects, path.join(self.DIR_SUBJECTS, "all_subjects"))
#                self.save_json(self.DIR_SUBJECTS, "all_subjects", self.d_subjects)
        log.info("classification of new subjects is complete")
        if self.multiple_T1_entries == 1:
            from classification.get_mr_params import verify_MRIs_for_similarity
            self.d_subjects = verify_MRIs_for_similarity(self.d_subjects, self.NIMB_tmp, self.flair_t2_add)
        else:
            self.d_subjects = self.keep_only1_T1(self.d_subjects)

        f_new_subjects = path.join(self.NIMB_tmp,'new_subjects.json')
        save_json(self.d_subjects, f_new_subjects)
#        self.save_json(self.NIMB_tmp, f_new_subjects, self.d_subjects)
        if path.exists(path.join(self.NIMB_tmp, f_new_subjects)):
            return True
        else:
            return False

    def _get_MR_paths(self, path2subj):
        if '.zip' in path2subj:
            content = self.chk_if_ziparchive(path2subj)
            path_2mris = self.get_paths2dcm_files_from_ls(content)
        elif path.isdir(path2subj):
            path_2mris = self.get_paths2dcm_files(path2subj)
        else:
            log.info('{} not a dir and not a .zip file'.format(str(path2subj)))
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


    def get_paths2dcm_files(self, path_root):
        '''
        search the path to the .dcm or .nii file
        '''
        ls_paths = list()
        for root, dirs, files in walk(path_root):
            for file in sorted(files):
                if file.endswith('.dcm'):
                    dir_src = get_path(root, file)
                    ls_paths.append(dir_src)
                    break
                if file.endswith('.nii'):
                    dir_src = get_path(root, file)
                    ls_paths.append(dir_src)
                    break
        return ls_paths

        
    def exclude_MR_types(self, ls):
        ls_iter = ls.copy()
        for mr_path in ls_iter:
            for ex_type in mr_types_2exclude:
                if ex_type.lower() in mr_path.replace(self.DIR_SUBJECTS,"").lower():
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
                else:
                    date = ''
            # add paths by date and type
            for mr_name_ls in mr_modalities.values():
                for mr_name in mr_name_ls:
                    if mr_name.lower() in mr_path.lower():
                        d_paths[date].append(mr_path)
            if not d_paths:
                log.info('ATENTION: cannot define MRI type. Considering as T1w: {}'.format(mr_path))
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
                    for chemin in d_paths[date]:
                        if chemin not in d_ses_paths[ses]:
                            d_ses_paths[ses].append(chemin)
            else:
                for key in d_paths:
                    for chemin in d_paths[key]:
                        if chemin not in d_ses_paths[ses]:
                            d_ses_paths[ses].append(chemin)
        return d_ses_paths

    def get_MR_types(self, path_subj_to_files):
        mr_found = False
        for mr_type in mr_modalities:
            for mr_name in mr_modalities[mr_type]:
                if mr_name.lower() in path_subj_to_files.lower() and mr_name.lower() not in self.subject.lower():
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
                mr_type = self.get_MR_types(mr_path.replace(self.DIR_SUBJECTS,""))
                if mr_type != 'none':
                    if mr_type not in d_ses_MR_types[ses]:
                        d_ses_MR_types[ses][mr_type] = list()
                    d_ses_MR_types[ses][mr_type].append(mr_path)
                elif self.MR_type_default not in d_ses_MR_types[ses]:
                    log.info('ATENTION: cannot define MRI type. Considering as T1w: {}'.format(mr_path))
                    d_ses_MR_types[ses][self.MR_type_default] = list()
                    d_ses_MR_types[ses][self.MR_type_default].append(mr_path)
                else:
                    log.info(mr_type, mr_path, 'none')
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
