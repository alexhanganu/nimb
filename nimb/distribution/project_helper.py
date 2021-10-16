# -*- coding: utf-8 -*-


import os
import sys
import shutil
import pandas as pd

from stats.db_processing import Table
from distribution.distribution_helper import  DistributionHelper
from distribution.distribution_ready import DistributionReady
from distribution.utilities import load_json, save_json, makedir_ifnot_exist
from distribution.distribution_definitions import get_keys_processed, DEFAULT, DEFAULTpaths
from classification.classify_2nimb_bids import Classify2_NIMB_BIDS
from classification.dcm2bids_helper import DCM2BIDS_helper 
from setup.interminal_setup import get_userdefined_paths, get_yes_no
from distribution.logger import LogLVL


class ProjectManager:
    '''
    projects require assessment of stage. Stages:
    - file with data is present
    - ids are present
    - BIDS is performed, files are present in the BIDS corresponding folders
    -> if not: source for IRM is defined
    - ids are processed with FreeSurfer/ nilearn/ dipy
    - stats performed
    For missing stages, helper will initiate distribution for the corresponding stage
    Args:
        all_vars
    '''


    def __init__(self, all_vars):

        self.all_vars           = all_vars
        self.local_vars         = all_vars.location_vars['local']
        self.project            = all_vars.params.project
        self.project_vars       = all_vars.projects[self.project]
        self._ids_project_col   = self.project_vars['id_proj_col']
        self._ids_bids_col      = self.project_vars['id_col']
        self.NIMB_tmp           = self.local_vars["NIMB_PATHS"]["NIMB_tmp"]

        # self.f_ids_proc_path  = os.path.join(self.materials_DIR,
        #                                      local_vars["NIMB_PATHS"]['file_ids_processed'])

        self.path_stats_dir     = makedir_ifnot_exist(
                                    all_vars.projects[self.project]["STATS_PATHS"]["STATS_HOME"])
        self.materials_dir_pt   = all_vars.projects[self.project]["materials_DIR"][1]
        self.f_ids_name         = self.local_vars["NIMB_PATHS"]['file_ids_processed']
        self.f_ids_abspath      = os.path.join(self.path_stats_dir, self.f_ids_name)
        self.tab                = Table()
        self.distrib_hlp        = DistributionHelper(self.all_vars)
        self.distrib_ready      = DistributionReady(self.all_vars)
        self.srcdata_dir        = self.project_vars["SOURCE_SUBJECTS_DIR"][1]
        self.BIDS_DIR           = self.project_vars['SOURCE_BIDS_DIR'][1]
        self.new_subjects_dir   = self.local_vars["NIMB_PATHS"]["NIMB_NEW_SUBJECTS"]
        self.dcm2bids           = DCM2BIDS_helper(self.project_vars,
                                                self.project,
                                                DICOM_DIR = self.srcdata_dir,
                                                tmp_dir = self.NIMB_tmp)
        self.apps_all           = DEFAULT.apps_all
        self.get_df_f_groups()
        self.get_ids_all()

        self.test               = all_vars.params.test
        self.nr_for_testing     = 2
        self.new_subjects       = False


    def get_df_f_groups(self):
        '''reading the file with IDs
            this file is provided by the user in:
            ../nimb/projects.json -> fname_groups
            file is tabular (.tab; .csv; .xlsx)
            if file is not provided or not found:
            run: self.make_default_grid()
        '''
        self.df_grid_ok = False
        f_groups = self.project_vars['fname_groups']
        if self.distrib_hlp.get_files_for_stats(self.path_stats_dir,
                                                [f_groups,]):
            f_grid = os.path.join(self.path_stats_dir, f_groups)
            print(f'    file with groups is present: {f_grid}')
            self.df_grid_ok = True
            self.df_grid    = self.tab.get_df(f_grid)
        else:
            self.df_grid_ok = False
            self.df_grid    = self.make_default_grid()
        self._ids_project   = self.df_grid[self._ids_project_col]


    def make_default_grid(self):
        '''creates the file default.csv
            that will be located in:
            ../nimb/projects.json -> materials_DIR -> ['local', 'PATH_2_DIR']
            ../nimb/projects.json -> STATS_PATHS -> STATS_HOME
            script will update file projects.json
        '''
        print(f'    file with groups is absent; creating default grid file in: {self.path_stats_dir}')
        df = self.tab.get_clean_df()
        df[self._ids_project_col] = ''
        df[self._ids_bids_col] = ''
        self.tab.save_df(df,
            os.path.join(self.path_stats_dir, DEFAULT.default_tab_name))
        self.tab.save_df(df,
            os.path.join(self.materials_dir_pt, DEFAULT.default_tab_name))
        self.project_vars['fname_groups']   = DEFAULT.default_tab_name
        self.all_vars.projects[self.project]['fname_groups'] = DEFAULT.default_tab_name
        from setup.get_credentials_home import _get_credentials_home
        credentials_home = _get_credentials_home()
        print(f'        updating project.json at: {credentials_home}')
        save_json(self.all_vars.projects, os.path.join(credentials_home, 'projects.json'))
        return df


    def get_ids_all(self):
        """
        ALGO:
            f_ids is searched in materials.
            f_ids is searched in folder for stats.
            if files are similar:
                continue
            if files are different:
                ask user
                default: use f_ids from materials

        f_ids.json:{
            "_id_bids": {
                "project"    : "ID_in_file_provided_by_user_for_GLM_analysis.tsv",
                "source"     : "ID_in_source_dir_or_zip_file",
                "freesurfer" : "ID_after_freesurfer_processing.zip",
                "nilearn"    : "ID_after_nilearn_processing.zip",
                "dipy"       : "ID_after_dipy_processing.zip"
                    }
            }
            _id_project: ID provided by the user in a grid file.
                        e.g., in PPMI _id_project = 3378_session1
                        _id_project is expected to be used for stats analysis
                        _id_project can be same as _id_bids, if edited by the user
            _id_source:  ID as defined in a database.
                        It can be same as _id_project, but it is NOT expected
                        that source_id will be used for stats
                        e.g., in PPMI source_id = 3378
                        these IDs are mainly folders of IDs with multiple sessions inside
            _id_bids   : ID after using the dcm2bids conversion;
                        it is automatically created with the make_bids_id function
                        it includes: dcm2bids prefix + source_id + session;
                        current dcm2bids prefix = "sub-"
                        _id_bids = sub-3378_ses-1
        """
        self._ids_all = dict()
        _ids_all_main = dict()
        _ids_all_stats = dict()
        if self.f_ids_in_dir(self.materials_dir_pt):
            _ids_all_main = load_json(os.path.join(self.materials_dir_pt, self.f_ids_name))
        if self.f_ids_in_dir(self.path_stats_dir):
            _ids_all_stats = load_json(os.path.join(self.path_stats_dir, self.f_ids_name))

        if _ids_all_main == _ids_all_stats:
            self._ids_all = _ids_all_stats
        else:
            print(f'{LogLVL.lvl1} ids all in the materials folder and stats folder are DIFFERENT')
            print(f'{LogLVL.lvl2} by default - I am using the file from materials folder')
            self._ids_all = _ids_all_main
        if not bool(self._ids_all):
            print(f'{LogLVL.lvl2} file with ids is EMPTY')
        # print(f'{LogLVL.lvl1} ids all are: {self._ids_all}')


    def run(self):
        """
            will run the whole project starting with the file provided in the projects.json -> group
        Args:
            groups file
        Return:
            stats
        """
        print(f'    running pipeline for project: {self.project}')
        do_task = self.all_vars.params.do
        if do_task == 'fs-glm':
            self.run_fs_glm()
        if do_task == 'fs-glm-image':
            self.run_fs_glm(image = True)
        if do_task == 'fs-get-stats':
            self.get_stats_fs()
        elif do_task == 'fs-get-masks':
            self.get_masks()
        elif do_task == 'check-new':
            self.check_new()
        elif do_task == 'classify':
            self.prep_4dcm2bids_classification()
        elif do_task == 'classify-dcm2bids':
            self.classify_with_dcm2bids()

        self.check_ids_from_grid()
        self.check_new()
        self.process_mri_data()
        self.extract_statistics()


    def check_new(self):
        print(f'{LogLVL.lvl1}checking for new subject to be processed')
        self.unprocessed_d = dict()
        self.get_ls_unprocessed_data()
        if len(self.unprocessed_d) > 1:
            self.change_paths_2rawdata()
            print(f'{LogLVL.lvl2}there are {len(self.unprocessed_d)} participants with MRI data to be processed')
            self.distrib_hlp.distribute_4_processing(self.unprocessed_d)
        else:
           print(f'{LogLVL.lvl2}ALL participants with MRI data were processed')


    def change_paths_2rawdata(self):
        for _id_bids in self.unprocessed_d:
            _id_bids_data = self.unprocessed_d[_id_bids]
            if "archived" in _id_bids_data:
                archive = _id_bids_data["archived"]
                _id_bids_data.pop("archived", None)
            for BIDS_type in _id_bids_data:# [i for i in _id_bids_data if i not in ("archived",)]:
                for mr_modality in _id_bids_data[BIDS_type]:
                    _, sub_label, ses_label, _ = self.dcm2bids.is_bids_format(_id_bids)
                    path_2rawdata = os.path.join(self.BIDS_DIR, sub_label, ses_label, BIDS_type)
                    if not os.path.exists(path_2rawdata):
                        print(f"{LogLVL.lvl2}{_id_bids} has no rawdata folder")
                        _id_project = self._ids_all[_id_bids]["project"]
                        _id_bids = self.classify_with_dcm2bids(self._ids_nimb_classified,
                                                                _id = _id_project)

                    _, sub_label, ses_label, _ = self.dcm2bids.is_bids_format(_id_bids)
                    path_2rawdata = self.dcm2bids.get_path_2rawdata(sub_label,
                                                        ses_label,
                                                        BIDS_type,
                                                        mr_modality)
                    if path_2rawdata:
                        self.unprocessed_d[_id_bids][BIDS_type][mr_modality] = [path_2rawdata,]
                    elif archive:
                        self.unprocessed_d[_id_bids][BIDS_type]["archived"] = archive
                    else:
                        print(f"{LogLVL.lvl2}raw data is missing and file is not archived")


    def get_ls_unprocessed_data(self):
        """
        get the list of un-processed subject
        must be absolute path
        :param SOURCE_SUBJECTS_DIR:
        :param PROCESSED_FS_DIR:
        :param project_name: name of the project, cannot be None
        :return: a list of subject to be processed
        """
        print(f"{LogLVL.lvl2}SOURCE_SUBJECTS_DIR is: {self.srcdata_dir}")
        print(f"{LogLVL.lvl2}PROCESSED_FS_DIR is: {self.project_vars['PROCESSED_FS_DIR'][1]}")
        self.get_ids_nimb_classified(self.srcdata_dir)
        if self._ids_nimb_classified:
            self.get_unprocessed_ids_from_nimb_classified()
        else:
            if self.must_run_classify_2nimb_bids:
                print(f'{" " * 4} must initiate nimb classifier')
                _dirs_to_classify = os.listdir(self.srcdata_dir)
                is_classified, nimb_classified = self.run_classify_2nimb_bids(_dirs_to_classify)
                if is_classified:
                    self.get_ids_nimb_classified(self.srcdata_dir)
                    self.get_unprocessed_ids_from_nimb_classified()
                else:
                    print(f"{LogLVL.lvl2}ERROR: classification 2nimb-bids had an error")


    def get_unprocessed_ids_from_nimb_classified(self):
        # print(f'{LogLVL.lvl1}nimb_classified is: {self._ids_nimb_classified}')
        for _id_src in self._ids_nimb_classified:
            ls_sessions = [i for i in  self._ids_nimb_classified[_id_src] if i not in ('archived',)]
            for session in ls_sessions:
                _id_bids, _ = self.dcm2bids.make_bids_id(_id_src, session)
                if _id_bids not in self._ids_all:
                    self.unprocessed_d[_id_bids] = self._ids_nimb_classified[_id_src][session]
                    if "archived" in self._ids_nimb_classified[_id_src]:
                        archive = self._ids_nimb_classified[_id_src]["archived"]
                        self.unprocessed_d[_id_bids]["archived"] = archive
                else:
                    print(f"{LogLVL.lvl2}{_id_bids} registered in file with ids")
                    # MUST check now for each app if was processed for each _id_bids


    def check_ids_from_grid(self):
        """
        ALGO:
            grid and self._ids_project already defined by self.get_df_f_groups()
            self._ids_all created by self.get_ids_all()

            for _id_project in self._ids_project:
                _id_bids = get_id_bids(_id_project)
                if _id_bids:
                    for APP in _id_bids:
                        if not APP:
                            add _id_bids to new_subjects.json for processing
                    new_subjects.json = True

            get_id_bids(_id_project):
                if _id_project in f_ids.json:
                    _id_bids = i from f_ids.json for the _id_project
                    chk _id_bids in BIDS_DIR and validate BIDS
                else:
                    if _id_project has BIDS format:
                        if _id_project in BIDS_DIR and validate BIDS:
                        _id_bids = _id_project
                    else:
                        _id_bids = classify_2_bids(_id_project)
                    update f_ids.json with _id_bids for _id_project

            classify_2_bids(_id_project):
                if not nimb_classified.json exists:
                    classify_2nimb SOURCE_DIR
                elif _id_project not in nimb_classified.json:
                    if _id_project in SOURCE_DIR:
                        classify_2nimb SOURCE_DIR
                    else:
                        remove _id_project from self._ids_project
                else:
                    _id_bids = classify 2 bids for _id_project

            if new_subjects.json:
                if ask OK to initiate processing is True:
                    initiate processing
        """
        self.check_app_processed()
        if self.new_subjects:
            print(f'{LogLVL.lvl1}must initiate processing')

        # self.get_ids_bids()


    def check_app_processed(self):
        for _id_project in self._ids_project:
            _id_bids = self.get_id_bids(_id_project)
            if _id_bids:
                for app in self.apps_all:
                    if not self._ids_all[_id_bids][app]:
                        self.populate_new_subjects(_id_bids, _id_project)
            else:
                print(f'{LogLVL.lvl1} cannot create _id_bids for _id_project: {_id_project}')


    def populate_new_subjects(self, _id_bids, _id_project):
        """ adding new _id_bids to existing new_subjects.json file"""
        print("adding new _id_bids to existing new_subjects.json file")
        self.new_subjects = True
        self.adj_subs2process(get = True)
        _, _, ses_label, _ = self.dcm2bids.is_bids_format(_id_bids)
        self.subs_2process[_id_bids] = self._ids_nimb_classified[_id_project][ses_label]
        self.adj_subs2process(save = True)


    def adj_subs2process(self, get = False, save = False):
        DEFpaths = DEFAULTpaths(self.NIMB_tmp)
        f_subj2process = DEFpaths.f_subj2process_abspath
        if get:
            if os.path.exists(f_subj2process):
                print(f'{" " * 4} file with subs to process is: {f_subj2process}')
                self.subs_2process = load_json(f_subj2process)
            else:
                print(f'{" " * 4} file with subjects to process is missing; creating empty dictionary')
                self.subs_2process = dict()
        elif save:
            save_json(self.subs_2process, f_subj2process)


    def get_id_bids(self, _id_project):
        key_id_project = "project"
        if _id_project in [self._ids_all[i][key_id_project] for i in self._ids_all]:
            _id_bids_ls = [i for i in self._ids_all if self._ids_all[i][key_id_project] == _id_project]
            if len(_ids_bids_ls) > 1:
                print(f'{LogLVL.lvl1}there are multiple _id_bids: {_id_bids_ls}\
                        that correspond to id {_id_project}')
                sys.exit(0)
            else:
                _id_bids = _ids_bids_ls[0]
            _, sub_label, _, _ = self.dcm2bids.is_bids_format(_id_bids)
            if not self.chk_id_bids_in_bids_dir(sub_label):
                _id_bids = classify_2_bids(_id_project)
        else:
            bids_format, sub_label, _, _ = self.dcm2bids.is_bids_format(_id_project)
            if bids_format:
                if self.chk_id_bids_in_bids_dir(sub_label):
                    _id_bids = _id_project
            else:
                _id_bids = classify_2_bids(_id_project)
            self.update_f_ids(_id_bids, "project", _id_project)
            self.save_f_ids()
        return _id_bids


    def chk_id_bids_in_bids_dir(self, _id_bids_sub_label):
        print('checing if _id_bids is present in the provided BIDS_DIR')
        if _id_bids_sub_label in os.listdir(self.BIDS_DIR):
            print(f'{LogLVL.lvl1}id_bids is present in BIDS_DIR')
            # if validate BIDS:
            return True
        else:
            print(f'{LogLVL.lvl1}id_bids ABSENT from BIDS_DIR')
            return False


    '''
    ID related scripts
    '''

    def get_ids_bids(self):
        """ extract bids ids from the file groups provided by user
        """

        self._ids_missing = list()
        print(f'    reading IDs for project {self.project}')
        if self.df_grid_ok:
            self._ids_bids = list(self.df_grid[self._ids_bids_col])
            print(f'{" " * 4}list of ids that are present: {self._ids_bids}')
            if self._ids_all:
                self.add_missing_participants()
            else:
                print(f'    file with ids is missing: {self._ids_all}')
                self.populate_f_ids_from_nimb_classified()
            self.chk_ids_processed()
        else:
            if self._ids_missing:
                print(f'{LogLVL.lvl1}missing ids: {self._ids_missing}')
            self.prep_4dcm2bids_classification()


    def add_missing_participants(self):
        '''chk if any _id_src from _ids_nimb_classified
            are missing from _ids_all[_id_bids]['source']
            if missing - will add _id_src to _ids_all
            will populate list() self._ids_missing
        '''
        self.get_ids_nimb_classified(self.srcdata_dir)
        if self._ids_nimb_classified:
            print(f'{LogLVL.lvl1}checking missing participants')
            # print(f'{LogLVL.lvl1} ids classified: {self._ids_nimb_classified}')
            # print(f'{LogLVL.lvl1} ids all: {self._ids_all}')
            ids_all_source = [self._ids_all[i]['source'] for i in self._ids_all.keys()]
            self._ids_missing = [i for i in self._ids_nimb_classified.keys() if i not in ids_all_source]
            for _id_src in self._ids_missing:
                for session in self._ids_nimb_classified[_id_src]:
                    _id_bids, _ = self.dcm2bids.make_bids_id(_id_src, session)
                    self._ids_all[_id_bids]['source'] = _id_src
        else:
            print(f'{LogLVL.lvl1}nimb_classified.json is missing')
        return self._ids_missing


    def populate_f_ids_from_nimb_classified(self):
        self._ids_bids_new = list()
        print(f'{LogLVL.lvl1} ids classified: {self._ids_nimb_classified}')
        for _id_src in self._ids_nimb_classified:
            for session in self._ids_nimb_classified[_id_src]:
                _id_bids, _ = self.dcm2bids.make_bids_id(_id_src, session)
                self._ids_bids_new.append(_id_bids)

                if _id_bids not in self._ids_all:
                    self._ids_all[_id_bids] = dict()
                self._ids_all[_id_bids][get_keys_processed('src')] = src_id
        self.create_file_ids(self._ids_all)


    def f_ids_in_dir(self, path_2groups_f):
        """
        verifies if file with ids is present in the path_2groups_f
        """

        self.f_ids_abspath = os.path.join(path_2groups_f, self.f_ids_name)
        if os.path.exists(self.f_ids_abspath):
            return True
        else:
            return self._ids_file_try2make()


    def chk_ids_processed(self):
            '''
            def check_is_subject_session_in_grid:
                if subject_session not in grid:
                    add subject_session to be processed
                    populate new_subjects.json with dcm2bids versions
                    if dcm2bids not efficient:
                        populate new_subjects with raw DCM
                self.get_ids_nimb_classified()
                self.populate_grid()
            '''
            print(f'{LogLVL.lvl1}checking processed ids')
            # for _id_bids in self._ids_all:
            #     for app in self._ids_all[_id_bids]:
            #         print(app)

            # self.prep_4dcm2bids_classification()


    def _ids_file_try2make(self):
        print(f'{LogLVL.lvl1}file with ids is MISSING')
        if self.df_grid_ok:
            print(f'{LogLVL.lvl2}trying to create file with ids based on grid file')
            _ids_bids    = self.df_grid[self._ids_bids_col]
            _ids_project = self.df_grid[self._ids_project_col]

            if len(_ids_bids) > 0:
                _ids = dict()
                self.make_reading_dirs()
                for _id_bids in _ids_bids:
                    _ids = self.populate_ids_all(_ids, _id_bids)
                self.create_file_ids(_ids)

            if os.path.exists(self.f_ids_abspath):
                return True
            else:
                print('    could not create the file with ids')
                True
        else:
            print(f'{LogLVL.lvl2}CANNOT create file with ids. Grid file is missing')
            return False


    def make_reading_dirs(self):
        PROCESSED_FS_DIR      = self.project_vars['PROCESSED_FS_DIR'][1]
        PROCESSED_NILEARN_DIR = self.project_vars['PROCESSED_NILEARN_DIR'][1]
        PROCESSED_DIPY_DIR    = self.project_vars['PROCESSED_DIPY_DIR'][1]
        self.keys2chk = {
            'src'    : self.srcdata_dir,
            'fs'     : PROCESSED_FS_DIR,
            'nilearn': PROCESSED_NILEARN_DIR,
            'dipy'   : PROCESSED_DIPY_DIR,
                            }
        self.content_dirs = {}
        for key in self.keys2chk:
            dir2chk = self.keys2chk[key]
            if os.path.exists(dir2chk):
                self.content_dirs[key] = self.get_content(dir2chk)


    def populate_ids_all(self, _ids, _id_bids):
        '''tries to populate the _ids_file with corresponding FreeSurfer processed folder
            f_ids includes only the archived folder names
        Args:
            _ids: dict() with _ids_bids as keys and 'fs': fs_ids as as values
        Return:
            newly populated dict()
        '''
        '''
        2DO
        currently - check if dirs are on local
        must add if dirs are on remote
        '''
        _ids[_id_bids] = dict()

        for key in self.keys2chk:
            dir2chk     = self.keys2chk[key][1]
            content2chk = self.content_dirs[key]
            key_nimb    = get_keys_processed(key)
            _ids[_id_bids][key_nimb] = ''
            for _dir in content2chk:
                if _id_bids in _dir:
                    _ids[_id_bids][key_nimb] = _dir
        return _ids


    def update_f_ids(self, _id_bids, key, _id_2update):
        self.must_save_f_ids = False
        if _id_bids in self._ids_all:
            self._ids_all[_id_bids][key] = _id_2update
            self.must_save_f_ids = True
        else:
            self._ids_all[_id_bids] = {key : _id_2update}
            self.must_save_f_ids = True


    def save_f_ids(self):
        if self.must_save_f_ids:
            save_json(self._ids_all, self.f_ids_abspath)


    def is_nimb_classified(self, _dir):
        is_classified = False
        if os.path.exists(os.path.join(_dir, DEFAULT.f_nimb_classified)):
            is_classified = True
        return is_classified


    def get_ids_nimb_classified(self, _dir):
        f = DEFAULT.f_nimb_classified
        self.must_run_classify_2nimb_bids = False
        self._ids_nimb_classified = dict()

        if self.is_nimb_classified(_dir):
            self._ids_nimb_classified = load_json(os.path.join(_dir, f))
        else:
            self.must_run_classify_2nimb_bids = True
            print(f'{LogLVL.lvl1}file {DEFAULT.f_nimb_classified} is missing in: {_dir}')


    def create_file_ids(self, _ids):
        print('creating file with groups {}'.format(self.f_ids_abspath))
        save_json(_ids, self.f_ids_abspath)
        save_json(_ids, os.path.join(self.materials_dir_pt, self.f_ids_name))


    '''
    CLASSIFICATION related scripts
    '''
    def classify_2_bids(self, _id_project):
        print('classifying to BIDS format')
        self.get_ids_nimb_classified(self.srcdata_dir)
        if self.must_run_classify_2nimb_bids:
            print(f'{" " * 4} must initiate nimb classifier')
            is_classified, nimb_classified = self.run_classify_2nimb_bids(_id_project)
            if is_classified:
                _id_bids = self.classify_with_dcm2bids(nimb_classified)
        elif _id_project not in self._ids_nimb_classified:
            if _id_project in SOURCE_DIR:
                print(f'{" " * 4} must initiate nimb classifier')
                is_classified, nimb_classified = self.run_classify_2nimb_bids(_id_project)
                if is_classified:
                    _id_bids = self.classify_with_dcm2bids(nimb_classified)
            else:
                print(f'{LogLVL.lvl1}id: {_id_project} is missing from source data; it cannot be used for further analysis')
                f_grid = os.path.join(self.path_stats_dir, self.project_vars['fname_groups'])
                print(f'{LogLVL.lvl1}must remove id: {_id_project} from file: {f_grid}')
                self._ids_project.remove(_id_project)
        else:
            _id_bids = self.classify_with_dcm2bids(nimb_classified, _id = _id_project)
        return _id_bids


    def prep_4dcm2bids_classification(self):
        ls_source_dirs = self.get_content(self.srcdata_dir)
        print(f'   there are {len(self.get_content(self.srcdata_dir))} files found in {self.srcdata_dir} \
            expected to contain MRI data for project {self.project}')
        if self.test:
            ls_source_dirs = self.get_content(self.srcdata_dir)[:self.nr_for_testing]

        self.prep_dirs(["SOURCE_BIDS_DIR",
                    "SOURCE_SUBJECTS_DIR"])

        if len(ls_source_dirs) > 0:
            for _dir in ls_source_dirs:
                self.run_classify_2nimb_bids(_dir)
                is_classified, nimb_classified = self.run_classify_2nimb_bids(_dir)
                if is_classified:
                    self.classify_with_dcm2bids(nimb_classified)
        else:
            print(f'    folder with source subjects {self.srcdata_dir} is empty')


    def run_classify_2nimb_bids(self, _dir):
        print(f'{LogLVL.lvl1}classifying folder: {_dir}')
        multi_T1     = self.local_vars['FREESURFER']['multiple_T1_entries']
        add_flair_t2 = self.local_vars['FREESURFER']['flair_t2_add']
        fix_spaces   = self.all_vars.params.fix_spaces
        is_classified, nimb_classified = Classify2_NIMB_BIDS(self.project,
                                                        self.srcdata_dir, self.NIMB_tmp, [_dir,],
                                                        fix_spaces, True,
                                                        multi_T1, add_flair_t2).run()
        return is_classified, nimb_classified


    def prep_dirs(self, ls_dirs):
        ''' define dirs required for BIDS classification
        '''
        print('    it is expected that SOURCE_SUBJECTS_DIR contains unarchived folders or archived (zip) files with MRI data')
        for _dir2chk in ls_dirs:
            _dir = self.project_vars[_dir2chk][1]
            if not os.path.exists(_dir):
                self.project_vars[_dir2chk][0] = 'local'
                self.project_vars[_dir2chk][1] = get_userdefined_paths(f'{_dir2chk} folder',
                                                                      _dir, '',
                                                                      create = False)
                from setup.get_credentials_home import _get_credentials_home
                self.all_vars.projects[self.project] = self.project_vars
                save_json(self.all_vars.projects, os.path.join(_get_credentials_home(), 'projects.json'))


    def classify_with_dcm2bids(self, nimb_classified = False, _id = False):
        if not nimb_classified:
            try:
                nimb_classified = load_json(os.path.join(
                    self.srcdata_dir,
                    DEFAULT.f_nimb_classified))
            except Exception as e:
                print(e)
                print('    nimb_classified file cannot be found at: {self.srcdata_dir}')

        if nimb_classified:
            if _id:
                ls_ids_2convert_2bids = [_id]
            else:
                ls_ids_2convert_2bids = [i for i in nimb_classified]
                if self.test:
                    print(f'        TESTING with {self.nr_for_testing} participants')
                    ls_ids_2convert_2bids = [i for i in nimb_classified][:self.nr_for_testing]
            for _id_from_nimb_classified in ls_ids_2convert_2bids:
                ls_sessions = [i for i in nimb_classified[_id_from_nimb_classified] if i not in ('archived',)]
                for ses in ls_sessions:
                    redy_2convert_2bids = self.id_is_bids_converted(_id_from_nimb_classified, ses)
                    if redy_2convert_2bids:
                        print('    ready to convert to BIDS')
                        self.bids_classified = self.convert_with_dcm2bids(_id_from_nimb_classified,
                                                            ses,
                                                            nimb_classified[_id_from_nimb_classified])
                        print(f'        bids_classified is: {self.bids_classified}')
        if _id:
            _id_bids = self.bids_classified[_id]
            return _id_bids


    def id_is_bids_converted(self, _id_from_nimb_classified, ses):
        bids_dir_location = self.project_vars['SOURCE_BIDS_DIR'][0]
        redy_2convert_2bids = False
        if bids_dir_location == 'local':
            _ids_in_bids_dir = os.listdir(self.BIDS_DIR)
            if _id_from_nimb_classified not in _ids_in_bids_dir:
                redy_2convert_2bids = True
            elif ses not in os.listdir(os.path.join(self.BIDS_DIR, _id_from_nimb_classified)):
                redy_2convert_2bids = True
        else:
            print(f'    bids folder located remotely: {bids_dir_location}')
        return redy_2convert_2bids


    def convert_with_dcm2bids(self, _id_from_nimb_classified, ses, nimb_classified_per_id):
        print(f'    starting dcm2bids classification for id: {_id_from_nimb_classified} session: {ses}')
        return self.dcm2bids.run(_id_from_nimb_classified,
                                ses,
                                nimb_classified_per_id)


    def get_content(self, path2chk):
        return os.listdir(path2chk)


    '''
    PROCESSING related scripts
    '''
    def process_mri_data(self):
        print("checking for processing")


    def get_masks(self):
        if self.distrib_ready.fs_ready():
            print('running mask extraction')
            # self.send_2processing('fs-get-masks')


    def send_2processing(self, task):
        from processing.schedule_helper import Scheduler
        python_run = self.local_vars["PROCESSING"]["python3_run_cmd"]
        NIMB_HOME  = self.local_vars["NIMB_PATHS"]["NIMB_HOME"]
        if task == 'process':
            schedule = Scheduler(self.local_vars)
            cd_cmd   = f'cd {os.path.join(NIMB_HOME, "processing")}'
            cmd      = f'{python_run} processing_run.py -project {self.project}'
            process_type = 'nimb_processing'
            subproc = 'run'
        if task == 'fs-get-stats':
            self.local_vars['PROCESSING']['processing_env']  = "tmux" #must be checked if works with slurm
            schedule = Scheduler(self.local_vars)
            dir_4stats = self.project_vars['STATS_PATHS']["STATS_HOME"]
            cd_cmd   = f'cd {os.path.join(NIMB_HOME, "processing", "freesurfer")}'
            cmd      = f'{python_run} fs_stats2table.py -project {self.project} -stats_dir {dir_4stats}'
            process_type = 'fs_stats'
            subproc = 'get_stats'
        if task == 'fs-get-masks':
            cd_cmd   = f'cd {os.path.join(NIMB_HOME, "processing", "freesurfer")}'
            cmd      = f'{python_run} run_masks.py -project {self.project}'
            process_type = 'fs'
            subproc = 'run_masks'
        print('    sending to scheduler')
        schedule.submit_4_processing(cmd, process_type, subproc, cd_cmd)


    '''
    EXTRACT STATISTICS related scripts
    '''
    def extract_statistics(self):
        print("extracting statistics")


    def get_stats_fs(self):
        if self.distrib_ready.chk_if_ready_for_stats():
            PROCESSED_FS_DIR = self.distrib_hlp.prep_4fs_stats()
            if PROCESSED_FS_DIR:
                print('    ready to extract stats from project helper')
        #         self.send_2processing('fs-get-stats')


    def run_fs_glm(self, image = False):
        '''
        REQUIRES ADJUSTMENT
        '''
        fs_glm_dir   = self.project_vars['STATS_PATHS']["FS_GLM_dir"]
        # fs_glm_dir   = self.stats_vars["STATS_PATHS"]["FS_GLM_dir"]
        fname_groups = self.project_vars['fname_groups']
        if DistributionReady(self.all_vars).chk_if_ready_for_fs_glm():
            GLM_file_path, GLM_dir = DistributionHelper(self.all_vars).prep_4fs_glm(fs_glm_dir,
                                                                        fname_groups)
            FS_SUBJECTS_DIR = self.vars_local['FREESURFER']['FS_SUBJECTS_DIR']
            DistributionReady(self.all_vars).fs_chk_fsaverage_ready(FS_SUBJECTS_DIR)
            if GLM_file_path:
                print('    GLM file path is:',GLM_file_path)
                self.vars_local['PROCESSING']['processing_env']  = "tmux"
                schedule_fsglm = Scheduler(self.vars_local)
                cd_cmd = 'cd {}'.format(path.join(self.NIMB_HOME, 'processing', 'freesurfer'))
                cmd = f'{self.py_run_cmd} fs_glm_runglm.py -project {self.project} -glm_dir {GLM_dir}'
                schedule_fsglm.submit_4_processing(cmd, 'fs_glm','run_glm', cd_cmd)
        if not "export_screen" in self.vars_local['FREESURFER']:
            print("PLEASE check that you can export your screen or you can run screen-based applications. \
                                This is necessary for Freeview and Tksurfer. \
                                Check the variable: export_screen in file {}".format(
                                    "credentials_path.py/nimb/local.json"))
        elif self.vars_local['FREESURFER']["export_screen"] == 0:
            print("Current environment is not ready to export screen. Please define a compute where the screen can \
                                be used for FreeSurfer Freeview and tksurfer")
        if DistributionReady(self.all_vars).fs_ready():
            print('before running the script, remember to source $FREESURFER_HOME')
            cmd = '{} fs_glm_extract_images.py -project {}'.format(self.py_run_cmd, self.project)
            cd_cmd = 'cd '+path.join(self.NIMB_HOME, 'processing', 'freesurfer')
            self.schedule.submit_4_processing(cmd, 'fs_glm','extract_images', cd_cmd)


    '''
    GRID related scripts
    '''
    def populate_grid(self):
        # get grid
        # populate
        df = self.get_df_f_groups()
        if self._ids_nimb_classified:
            self.get_ids_all()
            self.populate_f_ids_from_nimb_classified()

            for _id_bids in self._ids_bids_new:
                if _id_bids not in df[self._ids_bids_col]:
                    df.loc[-1] = df.columns.values
                    for col in df.columns.tolist():
                        df.at[-1, col] = ''
                    df.at[-1, self._ids_bids_col] = _id_bids
                    df.index = range(len(df[self._ids_bids_col]))
            # self.tab.save_df(df,
            #     os.path.join(self.path_stats_dir, self.project_vars['fname_groups']))
            print('    NIMB ready to initiate processing of data')
            self.send_2processing('process')
        else:
            print('   file with nimb classified is missing')


    def populate_ids_all_from_remote(self, _ids, _id_bids):
        '''
        fs_processed_col = 'path_freesurfer711'
        irm_source_col = 'path_source'
        df = pd.read_csv(path.join(self.materials_dir_pt, self.projects[self.proj>
        ls_miss = df[irm_source_col].tolist()
        remote_loc = self.get_processing_location('freesurfer')
        remote_loc = remote_loc[0]
        check if self.fs_ready(remote_loc)
        host_name = ""
        if self.fs_ready():
           # 1. install required library and software on the local computer, including freesurfer
           self.setting_up_local_computer()
           # install freesurfer locally
           setup = SETUP_FREESURFER(self.locations)
        SSHHelper.upload_multiple_files_to_cluster(remote_loc, ls_miss, self.locations[remote_loc]["NIMB_PATHS"]["NIMB_tmp"]
        else:
            logger.debug("Setting up the remote server")
            # --get the name and the address of remote server
            for machine_name, machine_config in self.locations.items():
                if machine_name == 'local': # skip
                    continue
                # a. check the fs_install == 1
                if machine_config['FREESURFER']['FreeSurfer_install'] == 1:
                    host_name = self.projects['LOCATION'][machine_name]
                    self.setting_up_remote_linux_with_freesurfer(host_name=host_name)

        # continue working from below
        # must set SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR before calling: get from project
        # project name get from where?

        machine_PROCESSED_FS_DIR, PROCESSED_FS_DIR = self.get_PROCESSED_FS_DIR()
        machine_SOURCE_SUBJECTS_DIR, SOURCE_SUBJECTS_DIR = self.get_SOURCE_SUBJECTS_DIR()

        self.run_copy_subject_to_cluster(Project)
        logger.debug('Cluster analysis started')
        logger.debug("Cluster analysing running....")
        self.run_processing_on_cluster_2()
        '''

        # return _ids
        pass
