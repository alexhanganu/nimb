#!/bin/python

'''
1) read folder/archive_file with subjects
3) extract paths for the anat/func/dwi MRIs
4) classify according to BIDS classification
5) create the BIDS-based nimb_classified.json file
6) nimb_classified.json is used by NIMB for dcm2bids conversion
7) and for creating the new_subjects.json for processing

authors:
Alexandru Hanganu
Kim Phuong Pham
'''

import os
from collections import defaultdict
import shutil
import datetime as dt

from classification.classify_definitions import mr_modalities, BIDS_types, mr_types_2exclude
from distribution.distribution_definitions import DEFAULT
from distribution.utilities import get_path, save_json, load_json
from distribution.manage_archive import is_archive, ZipArchiveManagement

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class Classify2_NIMB_BIDS():
    def __init__(self,
                project,
                MAIN_DIR,
                NIMB_tmp,
                ls_subjects = False,
                fix_spaces = False,
                update = False,
                multiple_T1_entries = False,
                flair_t2_add = False):

        self.MAIN_DIR     = MAIN_DIR
        self.NIMB_tmp     = NIMB_tmp
        self.project      = project
        self.ls_dirs      = ls_subjects
        self.update       = update
        self.multiple_T1  = multiple_T1_entries
        self.flair_t2_add = flair_t2_add
        self.MR_type_default = 't1'
        self.fix_spaces   = fix_spaces
        self.spaces_in_paths = list()
        self.main         = dict()
        log.info("classification of new subjects is running ...")


    def run(self):
        self.dir_2classify = self.get_dirs2classify()
        self.main = self.get_dict_4classification()
        for self._dir in self.dir_2classify:
            self.archived = False
            dir_abspath = os.path.join(self.MAIN_DIR, self._dir)
            paths_2mris = self._get_MR_paths(dir_abspath)

            if paths_2mris:
                if self.archived:
                    bids_ids = self.get_bids_ids(paths_2mris)
                    for bids_id in bids_ids:
                        paths_2classify    = self.get_content_per_bids_id(paths_2mris, bids_id)
                        BIDS_classified     = self.classify_2bids(paths_2classify)
                        self.main[bids_id] = BIDS_classified
                        self.main[bids_id]['archived'] = str(dir_abspath)
                else:
                    paths_2classify = paths_2mris
                    BIDS_classified = self.classify_2bids(paths_2classify)
                    self.main[self._dir] = BIDS_classified
                    self.main[self._dir]['archived'] = ''
            else:
                log.info(f'    there are no files or folders in the provided path to read: {dir_abspath}')

        log.info("    saving classification file")
        save_json(self.main, self.f_nimb_classified)
        log.info(f"classification of new subjects is complete, file located at: {self.f_nimb_classified}")
        if self.multiple_T1 == 1:
            from classification.get_mr_params import verify_MRIs_for_similarity
            self.main = verify_MRIs_for_similarity(self.main, self.NIMB_tmp, self.flair_t2_add)
        else:
            self.main = self.keep_only1_T1()

        self.chk_spaces()
        if os.path.exists(self.f_nimb_classified):
            return True, self.main
        else:
            return False, self.main


    def get_bids_ids(self, content):
        bids_ids = list()
        for chemin in content:
            chemin2rd = chemin.split('/')
            if self.project in DEFAULT.project_ids:
                dir2rm = DEFAULT.project_ids[self.project]["dir_from_source"]
                if dir2rm in chemin2rd:
                    chemin2rd.remove(dir2rm)
                else:
                    print(f'    in path: {chemin2rd} there is no expected default dir: {dir2rm}')
            bids_id = chemin2rd[0]
            if bids_id not in bids_ids:
                bids_ids.append(bids_id)
        return bids_ids


    def get_content_per_bids_id(self, content, bids_id):
        return [i for i in content if bids_id in i]


    def classify_2bids(self, paths_2classify):
        ls_MR_paths = self.exclude_MR_types(paths_2classify)
#        print("ls_MR_paths: ", ls_MR_paths)
        ls_sessions, d_paths = self.get_ls_sessions(ls_MR_paths)
#        print(ls_sessions)
        d_sessions = self.classify_by_sessions(ls_sessions)
#        print(d_sessions)
        d_ses_paths, d_ses_params = self.make_dict_sessions_with_paths(d_paths, d_sessions)
#        print(d_ses_paths)
        d_ses_MR_types = self.classify_by_MR_types(d_ses_paths)
#        print(d_ses_MR_types)

        return self.make_BIDS_structure(d_ses_MR_types, d_ses_params)


    def _get_MR_paths(self, dir_abspath):
        self.bids_id = self._dir
        if os.path.isdir(dir_abspath):
            return self.get_paths2dcm_files(dir_abspath)
        if is_archive(dir_abspath):
            self.archived = True
        if self.archived:
            archiver = ZipArchiveManagement(dir_abspath)
            if archiver.chk_if_zipfile():
                content = archiver.zip_file_content()
                return self.get_paths2dcm_files_from_ls(content)
        else:
            log.info('{} not a dir and not an archive'.format(str(dir_abspath)))
            return []


    def get_dict_4classification(self):
        main = dict()
        self.f_nimb_classified = os.path.join(self.MAIN_DIR,
                                            DEFAULT.f_nimb_classified)

        # update the existing file ?
        if os.path.exists(self.f_nimb_classified):
            if self.update:
                print('updating file with ids')
                main = load_json(self.f_nimb_classified)
            os.remove(self.f_nimb_classified)

        # remove nimb_classified file from list of files in MAIN_DIR
        if self.f_nimb_classified in self.dir_2classify:
            self.dir_2classify.remove(self.f_nimb_classified)
        return main


    def get_dirs2classify(self):
        if self.ls_dirs:
            return self.ls_dirs
        else:
            return os.listdir(self.MAIN_DIR)


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
                if ex_type.lower() in mr_path.replace(self.MAIN_DIR,"").lower():
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
        d_ses_paths  = {}
        d_ses_params = {}

        for ses in d_sessions:
            d_ses_paths[ses]  = list()
            d_ses_params[ses] = list()
            if d_sessions[ses]:
                for date in d_sessions[ses]:
                    for chemin in d_paths[date]:
                        if chemin not in d_ses_paths[ses]:
                            d_ses_paths[ses].append(chemin)
                            d_ses_params[ses].append(date)
            else:
                for key in d_paths:
                    for chemin in d_paths[key]:
                        if chemin not in d_ses_paths[ses]:
                            d_ses_paths[ses].append(chemin)
                            d_ses_params[ses].append(key)
        return d_ses_paths, d_ses_params


    def get_MR_types(self, path_subj_to_files):
        mr_found = False
        for mr_type in mr_modalities:
            for mr_name in mr_modalities[mr_type]:
                if mr_name.lower() in path_subj_to_files.lower() and mr_name.lower() not in self._dir.lower():
                    mr_found = True
                    res = mr_type
                    break
            if mr_found:
                break
        if mr_found:
            return res
        else:
            return 'none'


    def classify_by_MR_types(self, d_ses_paths):
        d_ses_MR_types = {}
        for ses in d_ses_paths:
            d_ses_MR_types[ses] = {}
            for mr_path in d_ses_paths[ses]:
                mr_type = self.get_MR_types(mr_path.replace(self.MAIN_DIR,""))
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


    def make_BIDS_structure(self, d_ses_MR_types, d_ses_params):
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
            d_BIDS_structure[ses]['ses-params'] = d_ses_params[ses]
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


    def keep_only1_T1(self):
        for subject in self.main:
            for session in self.main[subject]:
                if 'anat' in self.main[subject][session] and 't1' in self.main[subject][session]['anat']:
                    self.main[subject][session]['anat']['t1'] = self.main[subject][session]['anat']['t1'][:1]
                    if 'flair' in self.main[subject][session]['anat']:
                        self.main[subject][session]['anat'].pop('flair', None)
                    if 't2' in self.main[subject][session]['anat']:
                        self.main[subject][session]['anat'].pop('t2', None)


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
