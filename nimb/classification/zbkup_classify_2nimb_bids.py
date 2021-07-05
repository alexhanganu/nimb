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
import os
from collections import defaultdict
import shutil
import datetime as dt

from classification.classify_definitions import mr_modalities, BIDS_types, mr_types_2exclude
from classification.dcm2bids_helper import DCM2BIDS_helper
from distribution.distribution_definitions import DEFAULT
from distribution.utilities import get_path, save_json, load_json
from distribution.manage_archive import is_archive, ZipArchiveManagement

# from .utils import save_json, load_json #get_path

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class MakeBIDS_subj2process():
    def __init__(self, project,
                DIR_SUBJECTS,
                NIMB_tmp,
                ls_subjects = False,
                fix_spaces = False,
                update = False,
                multiple_T1_entries = False,
                flair_t2_add = False):

        self.DIR_SUBJECTS = DIR_SUBJECTS
        self.NIMB_tmp     = NIMB_tmp
        self.ls_subjects  = ls_subjects
        self.update       = update
        self.multiple_T1_entries  = multiple_T1_entries
        self.flair_t2_add = flair_t2_add
        self.MR_type_default = 't1'
        self.file_nimb_classified = os.path.join(self.DIR_SUBJECTS,
                                                DEFAULT.f_nimb_classified)
        self.fix_spaces = fix_spaces
        self.d_subjects = dict()
        self.spaces_in_paths = list()
        log.info("classification of new subjects is running ...")


    def run(self):
        if self.ls_subjects:
            print('one subject classifying')
            ls_subj_2_classify = self.ls_subjects
        else:
            ls_subj_2_classify = os.listdir(self.DIR_SUBJECTS)

        if os.path.exists(self.file_nimb_classified):
            if self.update:
                print('updating file with ids')
                self.d_subjects = load_json(self.file_nimb_classified)
            os.remove(self.file_nimb_classified)
        if self.file_nimb_classified in ls_subj_2_classify:
            ls_subj_2_classify.remove(self.file_nimb_classified)

        for self.subject in ls_subj_2_classify:
#            print(self.subject)
            self.d_subjects[self.subject] = {}
            path_2mris = self._get_MR_paths(os.path.join(self.DIR_SUBJECTS, self.subject))

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
                log.info("    saving classification file")
                save_json(self.d_subjects, self.file_nimb_classified)
        log.info(f"classification of new subjects is complete, file located at: {self.file_nimb_classified}")
        if self.multiple_T1_entries == 1:
            from classification.get_mr_params import verify_MRIs_for_similarity
            self.d_subjects = verify_MRIs_for_similarity(self.d_subjects, self.NIMB_tmp, self.flair_t2_add)
        else:
            self.d_subjects = self.keep_only1_T1(self.d_subjects)

        self.chk_spaces()
        if os.path.exists(self.file_nimb_classified):
            return True
        else:
            return False


    def chk_spaces(self):
        if self.spaces_in_paths:
            f_paths_spaces = os.path.join(self.NIMB_tmp,'paths_with_spaces.json')
            save_json(self.spaces_in_paths, f_paths_spaces)
            len_spaces = len(self.spaces_in_paths)
            log.info(f'    ATTENTION: ERR: paths of {len_spaces} subjects have spaces \
                and will not be processed by FreeSurfer')
            log.info(f'    ATTENTION: paths with spaces can be found here: {f_paths_spaces}')
            log.info('    ATTENTION: nimb can change spaces to underscores when adding the parameter: -fix-spaces; \
                example: python nimb.py -process classify -project Project -fix-spaces')


    def _get_MR_paths(self, path2subj):
        path_2mris = []
        if is_archive(path2subj):
            print('    tmp: this is an archived file')
            archiver = ZipArchiveManagement(file)
            if archiver.chk_if_zipfile():
                content = archiver.zip_file_content()
                path_2mris = self.get_paths2dcm_files_from_ls(content)
#        if '.zip' in path2subj:
#            print('    tmp: this is an archived file')
#            content = self.chk_if_ziparchive(path2subj)
#            path_2mris = self.get_paths2dcm_files_from_ls(content)
        elif os.path.isdir(path2subj):
            path_2mris = self.get_paths2dcm_files(path2subj)
        else:
            log.info('{} not a dir and not a .zip file'.format(str(path2subj)))
        return path_2mris


#    def chk_if_ziparchive(self, file):
#        archiver = ZipArchiveManagement(file)
#        if archiver.chk_if_zipfile():
#            return archiver.zip_file_content()
#        else:
#            return []


    def get_paths2dcm_files_from_ls(self, ls_content):
        ls_paths = list()
        for val in ls_content:
            if 'dcm' in val or '.nii' in val:
                path_mri = os.path.dirname(val)
                if path_mri not in ls_paths:
                    ls_paths.append(path_mri)
        return ls_paths


    def get_paths2dcm_files(self, path_root):
        '''
        search the path to the .dcm or .nii file
        '''
        ls_paths = list()
        for root, dirs, files in os.walk(path_root):
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
                    log.info('ATENTION: cannot define MRI type: {}'.format(mr_path))
                    # d_ses_MR_types[ses][self.MR_type_default] = list()
                    # d_ses_MR_types[ses][self.MR_type_default].append(mr_path)
                else:
                    log.info(mr_type, mr_path, 'none')
        return d_ses_MR_types


    def subjects_less_f(self, limit, ls_all_raw_subjects):
        ls_subjects = list()
        for folder in ls_all_raw_subjects:
            if len([f for f in os.listdir(SUBJECTS_DIR_RAW+folder)])<limit:
                ls_subjects.append(folder)

        return ls_subjects


    def subjects_nodcm(self, ls_all_raw_subjects):
        ls_subjects = list()
        for folder in ls_all_raw_subjects:
            for file in os.listdir(SUBJECTS_DIR_RAW+folder):
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
            for modalityLabel in d_ses_MR_types[ses]:
                for dataType in BIDS_types:
                    if modalityLabel in BIDS_types[dataType]:
                        if dataType not in d_BIDS_structure[ses]:
                            d_BIDS_structure[ses][dataType] = {}
                        ls_paths = self.check_spaces(d_ses_MR_types[ses][modalityLabel])
                        d_BIDS_structure[ses][dataType][modalityLabel] = ls_paths
                        break
        return d_BIDS_structure


    def check_spaces(self, ls_paths2chk):
        for path2chk in ls_paths2chk:
            if ' ' in path2chk:
                if not self.fix_spaces:
                    self.spaces_in_paths.append(path2chk)
                else:
                    log.info('fix-spaces chosen')
                    new_path = self.spaces_in_path_change(path2chk)
                    ls_paths2chk.remove(path2chk)
                    ls_paths2chk.append(new_path)
                    log.info('new path is: {}'.format(new_path))
        return ls_paths2chk


    def spaces_in_path_change(self, path2chk):
        path2chk_split = path2chk.split(os.sep)
        paths_with_spaces = [i for i in path2chk_split if ' ' in i]
        for path_with_space in paths_with_spaces:
            subdir_ix = path2chk_split.index(path_with_space)
            path2keep = os.sep.join(path2chk_split[:subdir_ix])
            old_path_with_space = os.path.join(path2keep, path_with_space)
            new_path_no_space   = os.path.join(path2keep, path_with_space.replace(' ','_'))
            log.info('moving {} TO:\n     {}'.format(old_path_with_space, new_path_no_space))
            shutil.move(old_path_with_space, new_path_no_space)
            new_path = os.path.join(new_path_no_space, os.sep.join(path2chk_split[subdir_ix+1:]))
        return new_path


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
