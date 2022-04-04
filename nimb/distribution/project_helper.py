# -*- coding: utf-8 -*-


import os
import sys

from stats.db_processing import Table
from distribution.distribution_helper import  DistributionHelper
from distribution.distribution_ready import DistributionReady
from distribution import utilities
from distribution.utilities import load_json, save_json, makedir_ifnot_exist
from distribution.distribution_definitions import get_keys_processed, DEFAULT, DEFAULTpaths
from classification.classify_2nimb_bids import Classify2_NIMB_BIDS
from classification.dcm2bids_helper import DCM2BIDS_helper
from setup.interminal_setup import get_userdefined_paths, get_yes_no
from distribution.logger import LogLVL


"""
ALGO: (created based on the loni-ppmi dataset)
Situations:
    (1) all _ids_bids from grid file were processed with APP:
    (2) _ids_project are present, but not _ids_bids
    (3) some _ids_bids must be processed OR
        all _ids_bids were processed:
        (3.stats) User wants stats: Do Stats
        (3.glm) User wants FS-GLM: Do FS-GLM
    (4) Check for new data in rawdata _dir and sourcedata _dir

Grid get or make
f_ids get or make
f_nimb_classified get or make

verify_ids_are_bids_standard:
    has BIDS structure name?
        and has corresponding _dir in rawdata ?
            and _dir in rawdata is BIDS validated?
1:
    for _id_bids from grid column with _ids_bids:
        verify_ids_are_bids_standard
        yes:
            populate f_ids with apps from rawdata/derivatives
        no:
            move _id_bids to _ids_project_col
        get list _ids_bids with missing APP processed for each APP
        list missing present. Save the list
        make True (will be run by 3)
2:
    for _id_project from grid column with _ids_project:
        verify_ids_are_bids_standard
        if yes:
            _ids_project are moved to the _ids_bids column
        is present in nimb_classified?
        yes:
            add to list for dcm2bids classification
        no:
            has a corresponding MRI _dir in sourcedata
            yes:
                add to 2 lists: for nimb and  dcm2bids classifications
            no:
                notify user to verify the name of the column with ids from the grid file
                remove _id_project from grid
                remove _id_project from f_ids
                add _id_project to missing.json
        if lists for updating:
            run corresponding 4 stages for lists
3:
    there are subjects that need to be processed per app: (self.new_subjects = True)
        send to processing
    else:
        all _ids_bids were processed with all APPs?
            get list _ids_bids have NO stats
            list missing stats not empty:
                 extract stats
            list missing stats empty:
            if 3.stats: user wants to perform STATS?
                yes:
                    do Stats: general description
                grid has variables for GLM? yes:
                    go GLM-based stats
                grid has a group column? yes:
                    do group-based Stats
                    if 3.glm:user wants to perform FreeSurfer GLM
                        and
                        all _ids_bids were processed with FreeSurfer:
                        yes:
                            do GLM-FS for group
                        grid has variables for GLM?
                        yes:
                            do GLM-FS for group for variables
                        environment allows screen export ? yes:
                            extract FS-GLM images
4:
    STEP 1:
        get _ids_src_new that are missing from nimb_classified
        from _ids_src:
            run update nimb classify for list()
    STEP 2:
        get ids_src from nimb_classified, missing from f_ids:
    STEP 3:
        extract ids that are BIDS format and validated
        yes_bids list:
                populate grid col _ids_bids_col
                copy folder to rawdata folder
    STEP 4:
        no_bids list:
            get list(_ids in sourcedata _dir) NOT in nimb_classified file
            for _id in list():
                run dcm2bids (self.classify_with_dcm2bids)
                populate grid with _ids_bids (self.add_ids_source_to_bids_in_grid)
        run 1 A

Definitions:
    _id_bids   : created with DCM2BIDS_helper().make_bids_id
                using dcm2bids app
                includes: bids_prefix-_id_source_session_run;
                e.g: sub-3378_ses-1
                _id_bids is used for stats analysis
    _id_project: ID provided by the user in a grid file.
                MUST correspond to 1 participant
                MUST have ONLY 1 set of data, e.g.: ses-01
                e.g., in PPMI _id_project = 3378_ses-01
                _id_project can be same as _id_bids or _id_source
    _id_source:  ID as defined in a database.
                MUST correspond to 1 participant
                CAN have multiple sets of data, multiple session
                e.g., in PPMI _id_source = 3378 and is a folder with multiple sessions
"""


class ProjectManager:
    '''
        class to Manage a specific project
        missing stages are being initiated with distribution
    Args:
        all_vars
    ALGO:
        - get tsv file to df for project.
            If missing: make default
        - get f_ids.
            If missing: make default
        self.run()
    '''

    def __init__(self, all_vars):

        self.all_vars           = all_vars
        self.local_vars         = all_vars.location_vars['local']
        self.NIMB_tmp           = self.local_vars["NIMB_PATHS"]["NIMB_tmp"]
        self.new_subjects_dir   = self.local_vars["NIMB_PATHS"]["NIMB_NEW_SUBJECTS"]
        self.project            = all_vars.params.project
        self.project_vars       = all_vars.projects[self.project]
        self.materials_dir_pt   = self.project_vars["materials_DIR"][1]
        self.srcdata_dir        = self.project_vars["SOURCE_SUBJECTS_DIR"][1]
        self.BIDS_DIR           = self.project_vars['SOURCE_BIDS_DIR'][1]

        self.f_groups           = self.project_vars['fname_groups']
        self._ids_project_col   = self.project_vars['id_proj_col']
        self._ids_bids_col      = self.project_vars['id_col']
        self.path_stats_dir     = makedir_ifnot_exist(
                                    self.project_vars["STATS_PATHS"]["STATS_HOME"])
        self.f_ids_name         = DEFAULT.f_ids
        self.f_ids_instatsdir   = os.path.join(self.path_stats_dir,
                                                self.f_ids_name)
        self.f_ids_inmatdir     = os.path.join(self.materials_dir_pt,
                                                self.f_ids_name)
        self.new_subjects       = False
        self.test               = all_vars.params.test
        self.nr_for_testing     = 2 # if self.test - this defines nr of subj to run

        self.tab                = Table()
        self.distrib_hlp        = DistributionHelper(self.all_vars)
        self.distrib_ready      = DistributionReady(self.all_vars)
        self.dcm2bids           = DCM2BIDS_helper(self.project_vars,
                                                self.project,
                                                DICOM_DIR = self.srcdata_dir,
                                                tmp_dir = self.NIMB_tmp)
        self.get_df_f_groups()
        self.read_f_ids()
        self.get_ids_nimb_classified()


    def run(self):
        """
            runs project: processing -> stats -> glm
            based projects.json -> project: fname_groups
        Args:
            none
        Return:
            stats
            glm results
        """
        print(f'{LogLVL.lvl1}running pipeline for project: {self.project}')
        do_task = self.all_vars.params.do
        if do_task == 'fs-glm':
            self.glm_fs_do()
        if do_task == 'fs-glm-image':
            self.glm_fs_do(image = True)
        if do_task == 'fs-get-stats':
            self.extract_statistics(app = ["freesurfer",])
        elif do_task == 'fs-get-masks':
            self.get_masks()
        elif do_task == 'check-new':
            self.check_new()
        elif do_task == 'classify':
            self.prep_4dcm2bids_classification()
        elif do_task == 'classify-dcm2bids':
            self.classify_with_dcm2bids()

        self.processing_chk()
        self.ids_project_chk()
        if self.new_subjects:
            print(f'{LogLVL.lvl1}must initiate processing')
            self.send_2processing('process')
        # else:
        #     self.extract_statistics(app = ["freesurfer",])
        #     # self.glm_fs_do()
        #     # self.glm_fs_do(image = True)
        self.check_new()


    def processing_chk(self):
        """
            checks if all ids in self.ids_all were processed
        Args:
            none
        Return:
            bool
        """
        if self._ids_bids:
            not_bids, _, _ = self.verify_ids_are_bids_standard(self._ids_bids, self.BIDS_DIR)
            if not_bids:
                print(f"{LogLVL.lvl2}some subjects are not of bids format: {not_bids}")
                self.mv_ids_bids_in_grid(not_bids)
            apps = list(DEFAULT.app_files.keys())
            for _id_bids in self._ids_bids:
                apps2process = self.processing_get_apps(_id_bids)
                if apps2process:
                    print(f'{LogLVL.lvl1}sending for processing: {_id_bids}, for apps: {apps2process}')
                    self.processing_add_id(_id_bids, apps2process)


    def processing_get_apps(self, _id_bids):
        """
        populate f_ids with corresponding APP processed file names.
        Structure:
            f_ids.json:{
                "_id_bids": {
                    DEFAULT.id_project_key : "ID_in_file_provided_by_user_for_GLM_analysis.tsv",
                    DEFAULT.id_source_key  : "ID_in_source_dir_or_zip_file",
                    "freesurfer"           : "ID_after_freesurfer_processing.zip",
                    "nilearn"              : "ID_after_nilearn_processing.zip",
                    "dipy"                 : "ID_after_dipy_processing.zip"}}
        """
        apps2process = list()
        rawdata_listdir = self.get_listdir(self.BIDS_DIR)

        for app in DEFAULT.app_files:
            self.update_f_ids(_id_bids, app, "")
            if not self._ids_all[_id_bids][app]:                
                key_dir_2processed = DEFAULT.app_files[app]["dir_store_proc"]
                location = self.project_vars[key_dir_2processed][0]
                abspath_2storage = self.project_vars[key_dir_2processed][1]
                if location != "local":
                    print(f"{LogLVL.lvl2}subject {_id_bids} for app: {app} is stored on: {location}")
                else:
                    _id_per_app = [i for i in self.get_listdir(abspath_2storage) if _id_bids in i]
                    if _id_per_app:
                        self.update_f_ids(_id_bids, app, _id_per_app[0])
                    if len(_id_per_app) > 1:
                        print(f"{LogLVL.lvl2}participant: {_id_bids} has multiple ids for app: {app}: {_id_per_app}")
                        print(f"{LogLVL.lvl3}{_id_per_app}")
            if not self._ids_all[_id_bids][app]:
                apps2process.append(app)
        self.save_f_ids()
        return apps2process


    def processing_add_id(self, _id_bids, apps):
        """
        Args:
            _id_bids: id of participant in BIDS format
            apps: list of apps to be processed
        Return:
            bool
        Algo:
            add _id_bids to new_subjects.json for processing
            new_subjects.json = True
            if new_subjects.json:
                if ask OK to initiate processing is True:
                    send for processing
        """
        print("adding new _id_bids to existing new_subjects.json file")
        DEFpaths = DEFAULTpaths(self.NIMB_tmp)
        f_subj2process = DEFpaths.f_subj2process_abspath
        if not os.path.exists(f_subj2process):
            print(f'{LogLVL.lvl1} file with subjects to process is missing; creating empty dictionary')
            self.subs_2process = dict()
        else:
            self.subs_2process = load_json(f_subj2process)

        _, sub_label, ses_label, _ = self.dcm2bids.is_bids_format(_id_bids)
        content = self.processing_get_abspath_rawdata(sub_label, ses_label)
        self.subs_2process[_id_bids] = content
        save_json(self.subs_2process, f_subj2process, print_space = 4)
        self.new_subjects = True


    def processing_get_abspath_rawdata(self, sub_label, ses_label):
        """
            searches for corresponding folders in rawdata
            creates a dict with absolute paths to MRI files
        Args:
            sub_label: label of folder with sub- prefix, as per BIDS standard
            ses_label: label of session sub-folder with ses- prefix, as per BIDS standard
        Return:
            dict(): {
                    "anat":
                        "t1"   :[sub-label_ses-label_T1w.nii.gz],
                        "flair":[sub-label_ses-label_Flair.nii.gz],
                    "func":
                        "bold" :[sub-label_ses-label_bold.nii.gz],
                    "dwi":
                        "dwi"  :[sub-label_ses-label_dwi.nii.gz]}
        """
        print(f'reading dirs: {sub_label} and {ses_label}')
        ses_path = os.path.join(self.BIDS_DIR, sub_label, ses_label)
        content = dict()
        dirs = os.listdir(ses_path)
        for _dir in dirs:
            _dir_content = os.listdir(os.path.join(ses_path, _dir))
            mri_files = [i for i in _dir_content if i.endswith(".nii.gz")]
            if _dir == "dwi":
                content[_dir] = {"dwi":mri_files}
            elif _dir == "func":
                bold_files = [i for i in mri_files if "bold" in i]
                content[_dir] = {"bold":bold_files}
            elif _dir == "anat":
                t1_files = [i for i in mri_files if "T1w" in i]
                content[_dir] = {"t1":t1_files}
                flair_files = [i for i in mri_files if "Flair" in i]
                if flair_files:
                    content[_dir]["flair"] = flair_files
        return content


    def ids_project_chk(self):
        """
            checks if all ids_project in grid were dcm2bids converted
        Args:
            none
        Return:
            bool
        """
        _, yes_bids, _ = self.verify_ids_are_bids_standard(self._ids_project, self.BIDS_DIR)
        if yes_bids:
            print(f"{LogLVL.lvl2}some subjects are of bids format: {yes_bids}")
            self.add_ids_project_to_bids_in_grid(yes_bids)

        ls_2rm_from_grid     = list()
        ls_4dcm2bids_classif = list()
        ls_4nimb_classif     = list()
        for _id_project in self._ids_project:
            if _id_project in self._ids_nimb_classified:
                ls_4dcm2bids_classif.append(_id_project)
            else:
                print(f'{LogLVL.lvl2}id_project: {_id_project} is missing:')
                print(f'{LogLVL.lvl3}from file: {DEFAULT.f_nimb_classified} in: {self.srcdata_dir}')
                if _id_project in self.get_listdir(self.srcdata_dir):
                    print(f'{LogLVL.lvl3}must undergo nimb classification')
                    ls_4nimb_classif.append(_id_project)
                else:
                    print(f'{LogLVL.lvl3}from sourcedata: {self.srcdata_dir}')
                    print(f'{LogLVL.lvl3}removing id: {_id_project} from grid {f_grid}')
                    ls_2rm_from_grid.append(_id_project)

        # removing _id_project from grid and f_ids
        if ls_2rm_from_grid:
            self.rm_id_from_grid(ls_2rm_from_grid)
            missing_file = os.path.join(self.path_stats_dir, "missing.json")
            save_json(ls_2rm_from_grid, missing_file, print_space = 4)
            for _id_project in ls_2rm_from_grid:
                _id_bids_ls = self.f_ids_find_id_bids_4id_project(_id_project)
                for _id_bids in _id_bids_ls:
                    if _id_bids in self._ids_all:
                        self.update_f_ids(_id_bids, DEFAULT.id_project_key, "")
            self.save_f_ids()

        # removing potential _ids that might undergo double classification
        for _id in ls_4nimb_classif[::-1]:
            if _id in ls_4dcm2bids_classif:
                ls_4dcm2bids_classif.remove(_id)
        if ls_4nimb_classif:
            self.run_classify_2nimb(ls_4nimb_classif)
        if ls_4dcm2bids_classif:
            self.run_classify_dcm2bids(ls_4dcm2bids_classif)
        self.processing_chk()


    def f_ids_find_id_bids_4id_project(self, _id_project):
        """
            find the _id_bids from f_ids that corresponds
            to provided _id_project
        Args:
            _id_project
        Return:
            list(of all _id_bids that correspond)
        """
        _id_bids_ls = list()
        key_id_project = DEFAULT.id_project_key
        if _id_project in [self._ids_all[i][key_id_project] for i in self._ids_all]:
            _id_bids_ls = [i for i in self._ids_all if self._ids_all[i][key_id_project] == _id_project]
            if len(_ids_bids_ls) > 1:
                print(f'{LogLVL.lvl1}there are multiple _id_bids: {_id_bids_ls}\
                        that correspond to id {_id_project}')
        return _id_bids_ls


    def update_f_ids(self, _id_bids, key, val_2update):
        if not key and _id_bids in self._ids_all:
            self._ids_all.pop(_id_bids, None)
        elif _id_bids not in self._ids_all:
            self._ids_all[_id_bids] = dict()
        else:
            self._ids_all[_id_bids][key] = val_2update


    def save_f_ids(self):
        """
        f_ids is saved in:
            materials and
            stats_dirs
        """
        save_json(self._ids_all, self.f_ids_inmatdir, print_space = 12)
        save_json(self._ids_all, self.f_ids_instatsdir, print_space = 12)


    def check_new(self):
        """
        DESCRIPTION:
            distributor:
                initiate to get list of unprocessed from nimb_classified.json
                if file is missing:
                    initiate classify 2 nimb_bids
                    get list of unprocessed from nimb_classified.json
        Args:
            none
        Return:
            none
        """
        # STEP 1
        # checking for new subjects
        # extracting subjects missing from the nimb_classified file
        print(f'{LogLVL.lvl1}{"=" * 36}')
        print(f'{LogLVL.lvl1}checking for new subjects in SOURCE_SUBJECTS_DIR:')
        print(f"{LogLVL.lvl2}{self.srcdata_dir}")
        ls_ids_src     = self.get_listdir(self.srcdata_dir)
        archived = [self._ids_nimb_classified[i]["archived"] for i in self._ids_nimb_classified]
        ls_new_ids_src = [i for i in ls_ids_src if i not in self._ids_nimb_classified]
        for file in ls_new_ids_src[::-1]:
            for archive in archived:
                if file in archive:
                    print("file in archive:", archive)
                    ls_new_ids_src.remove(file)
                    break
        if DEFAULT.f_nimb_classified in ls_new_ids_src:
            ls_new_ids_src = ls_new_ids_src.remove(DEFAULT.f_nimb_classified)

        if ls_new_ids_src:
            print(f'{LogLVL.lvl2}there are new subjects that were not classified')
            print(f'{LogLVL.lvl3}initiating nimb classifier, to file: nimb_classified.json')
            is_classified, _ = self.run_classify_2nimb_bids(ls_new_ids_src)
            if is_classified:
                print(f'{LogLVL.lvl3}classification to nimb_classified.json DONE')
            else:
                print(f"{LogLVL.lvl2}ERROR: classification 2nimb-bids had an error")
        else:
            print(f'{LogLVL.lvl3}All data in SOURCE_SUBJECTS_DIR were added to file nimb_classified.json')

        # STEP 2:
        # get ids from nimb_classified missing from f_ids
        self.get_ids_nimb_classified()
        unprocessed_d = self.get_unprocessed_ids_from_nimb_classified()

        # STEP 3:
        # extract potential ids that might have bids structure
        # and could be directly moved to the _ids_bids column in the grid
        print(f'{LogLVL.lvl2}checking BIDS format for folders in:')
        print(f"{LogLVL.lvl3}SOURCE_SUBJECTS_DIR: {self.srcdata_dir}")
        _ids_src_bids_unprocessed = dict()
        for _id_src in unprocessed_d.keys():
            for session in unprocessed_d[_id_src]:
                _ids_src_bids_unprocessed[_id_src] = unprocessed_d[_id_src][session]["id_bids"]
        no_bids, _, yes_bids_d = self.verify_ids_are_bids_standard(
                                                    list(_ids_src_bids_unprocessed.values()),
                                                    self.srcdata_dir)
        if yes_bids_d:
            print(f"{LogLVL.lvl2}some subjects are of BIDS format: {list(yes_bids_d.keys())}")
            self.copy_dir(yes_bids)
            self.add_ids_source_to_bids_in_grid(yes_bids_d)

        # STEP 4:
        # manage the unprocessed ids
        if no_bids:
            _ids_src_unprocessed = list()
            for _id_src in _ids_src_bids_unprocessed.keys():
                if _ids_src_bids_unprocessed[_id_src] in no_bids:
                    _ids_src_unprocessed.append(_id_src)
            print(f'{LogLVL.lvl2}there are {len(_ids_src_unprocessed)} participants')
            print(f'{LogLVL.lvl3}with MRI data to be processed')
            for _id_src in _ids_src_unprocessed:
                _id_bids = self.classify_with_dcm2bids(nimb_classified = self._ids_nimb_classified,
                                                    _id_project = _id_src)
                self.add_ids_source_to_bids_in_grid({_id_src: _id_bids})
            self.processing_chk()
        else:
           print(f'{LogLVL.lvl2}ALL participants with MRI data were processed')



    def get_unprocessed_ids_from_nimb_classified(self):
        """
            get ids_src from nimb_classified that are missing from f_ids.json
        """
        # print(f'{LogLVL.lvl1}nimb_classified is: {self._ids_nimb_classified}')
        unprocessed_d = dict()
        for _id_src in self._ids_nimb_classified:
            unprocessed_d[_id_src] = {}
            ls_sessions = [i for i in  self._ids_nimb_classified[_id_src] if i not in ('archived',)]
            for session in ls_sessions:
                _id_bids, _id_bids_label = self.dcm2bids.make_bids_id(_id_src, session)
                if _id_bids not in self._ids_all:
                    unprocessed_d[_id_src][session] = {"id_bids":_id_bids,
                                                        "id_bids_label": _id_bids_label}
                    if "archived" in self._ids_nimb_classified[_id_src]:
                        archive = self._ids_nimb_classified[_id_src]["archived"]
                        unprocessed_d[_id_src][session]["archived"] = archive
                else:
                    print(f"{LogLVL.lvl2}{_id_bids} registered in file with ids")
        return unprocessed_d



    '''
    CLASSIFICATION related scripts
    '''
    def verify_ids_are_bids_standard(self, ls2chk, _dir2chk):
        """
            verify that all _ids in ls2chk
                have a BIDS structure name
                have a folder in rawdata
                folder is BIDS validated
        Args:
            ls2chk = list() with ids to check
            _dir2chk = str() absolute path to dir with ids to check
        Return:
            no_bids, yes_bids = list() with that do not have or have
                all criteria as True
            yes_bids_d = {_id_src: _id_bids}
        """
        rawdata_listdir = self.get_listdir(_dir2chk)
        no_bids = list()
        yes_bids = list()
        yes_bids_d = dict()

        for _id in ls2chk:
            bids_format, sub_label, ses_label, _ = self.dcm2bids.is_bids_format(_id)
            if not bids_format:
                print(f"{LogLVL.lvl3}subject {_id} name is not of BIDS format")
                no_bids.append(_id)
            elif sub_label not in rawdata_listdir:
                print(f"{LogLVL.lvl3}subject {_id} is missing from: {_dir2chk}")
                no_bids.append(_id)
            else:
                _id_bids, _ = self.dcm2bids.make_bids_id(sub_label, ses_label)
                yes_bids.append(_id)
                yes_bids_d[_id] = _id_bids
            # elif not validate BIDS: !!!!!!!!!!!!!!!!!
            #     print(f"{LogLVL.lvl2}subject {_id} folder in: {_dir2chk} has not been validated for BIDS")
            #     no_bids.append(_id)
        return no_bids, yes_bids, yes_bids_d


    def run_classify_2nimb_bids(self, ls_subjects):
        """initiator for nimb_classifier
        Args:
            ls_subjects: list() if _ids to be classified
        Return:
            is_classified: bool; True = classification was performed correctly
            nimb_classified: dict() of the nimb_classified.json file
        """
        print(f'{LogLVL.lvl2}classifying subjects: {ls_subjects}')
        multi_T1     = self.local_vars['FREESURFER']['multiple_T1_entries']
        add_flair_t2 = self.local_vars['FREESURFER']['flair_t2_add']
        fix_spaces   = self.all_vars.params.fix_spaces
        is_classified, nimb_classified = Classify2_NIMB_BIDS(self.project,
                                                        self.srcdata_dir,
                                                        self.NIMB_tmp,
                                                        ls_subjects = ls_subjects,
                                                        fix_spaces = fix_spaces,
                                                        update = True,
                                                        multiple_T1_entries = multi_T1,
                                                        flair_t2_add = add_flair_t2).run()
        return is_classified, nimb_classified


    def prep_4dcm2bids_classification(self):
        ls_source_dirs = self.get_listdir(self.srcdata_dir)
        if DEFAULT.f_nimb_classified in ls_source_dirs:
            ls_source_dirs = ls_source_dirs.remove(DEFAULT.f_nimb_classified)

        print(f'   there are {len(ls_source_dirs)} files found in {self.srcdata_dir} \
            expected to contain MRI data for project {self.project}')
        if self.test:
            ls_source_dirs = ls_source_dirs[:self.nr_for_testing]

        self.prep_dirs(["SOURCE_BIDS_DIR",
                    "SOURCE_SUBJECTS_DIR"])

        if len(ls_source_dirs) > 0:
            for _dir in ls_source_dirs:
                self.run_classify_2nimb_bids(_dir)
                is_classified, nimb_classified = self.run_classify_2nimb_bids(_dir)
                if is_classified:
                    _id_bids = self.classify_with_dcm2bids(nimb_classified)
        else:
            print(f'    folder with source subjects {self.srcdata_dir} is empty')


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
                save_json(self.all_vars.projects,
                            os.path.join(_get_credentials_home(), 'projects.json'))


    def classify_with_dcm2bids(self, nimb_classified = False, _id_project = False):
        if not nimb_classified:
            try:
                nimb_classified = load_json(os.path.join(
                                                    self.srcdata_dir,
                                                    DEFAULT.f_nimb_classified))
            except Exception as e:
                print(e)
                print('    nimb_classified file cannot be found at: {self.srcdata_dir}')

        if nimb_classified:
            if _id_project:
                ls_ids_2convert_2bids = [_id_project]
            else:
                ls_ids_2convert_2bids = [i for i in nimb_classified]
                if self.test:
                    print(f'        TESTING with {self.nr_for_testing} participants')
                    ls_ids_2convert_2bids = ls_ids_2convert_2bids[:self.nr_for_testing]
            for _id_from_nimb_classified in ls_ids_2convert_2bids:
                ls_sessions = [i for i in nimb_classified[_id_from_nimb_classified] if i not in ('archived',)]
                for ses in ls_sessions:
                    ready_2convert_2bids = self.id_is_bids_converted(_id_from_nimb_classified, ses)
                    if ready_2convert_2bids:
                        print('    ready to convert to BIDS')
                        self.bids_classified, _id_bids = self.convert_with_dcm2bids(_id_from_nimb_classified,
                                                            ses,
                                                            nimb_classified[_id_from_nimb_classified])
                        # print(f'        bids_classified is: {self.bids_classified}')
        if _id_project:
            self.update_f_ids(_id_bids, DEFAULT.id_project_key, _id_project)
            # populate grid with _id_bids
            self.save_f_ids()
        return _id_bids


    def id_is_bids_converted(self, _id_from_nimb_classified, ses):
        bids_dir_location = self.project_vars['SOURCE_BIDS_DIR'][0]
        ready_2convert_2bids = False
        if bids_dir_location == 'local':
            _ids_in_bids_dir = os.listdir(self.BIDS_DIR)
            if _id_from_nimb_classified not in _ids_in_bids_dir:
                ready_2convert_2bids = True
            elif ses not in os.listdir(os.path.join(self.BIDS_DIR, _id_from_nimb_classified)):
                ready_2convert_2bids = True
        else:
            print(f'    bids folder located remotely: {bids_dir_location}')
        return ready_2convert_2bids


    def convert_with_dcm2bids(self, _id_from_nimb_classified, ses, nimb_classified_per_id):
        print(f'    DCM2BIDS STARTING, id: {_id_from_nimb_classified} session: {ses}')
        return self.dcm2bids.run(_id_from_nimb_classified,
                                ses,
                                nimb_classified_per_id)


    def get_listdir(self, path2chk):
        return os.listdir(path2chk)


    '''
    PROCESSING related scripts
    '''
    def get_masks(self):
        if self.distrib_ready.fs_ready():
            print('running mask extraction')
            # self.send_2processing('fs-get-masks')


    def send_2processing(self, task):
        from processing.schedule_helper import Scheduler
        python_run = self.local_vars["PROCESSING"]["python3_run_cmd"]
        NIMB_HOME  = self.local_vars["NIMB_PATHS"]["NIMB_HOME"]
        if task == 'process':
            if not self.test:
                print(f'    sending to scheduler for task {task}')
                self.distrib_hlp.distribute_4_processing(self.unprocessed_d)
            else:
                print(f'    READY to send to scheduler for task {task}. TESTing active')

            # schedule = Scheduler(self.local_vars)
            # cd_cmd   = f'cd {os.path.join(NIMB_HOME, "processing")}'
            # cmd      = f'{python_run} processing_run.py -project {self.project}'
            # process_type = 'nimb_processing'
            # subproc = 'run'
        elif task == 'fs-get-stats':
            self.local_vars['PROCESSING']['processing_env']  = "tmux" #must be checked if works with slurm
            schedule = Scheduler(self.local_vars)
            dir_4stats = self.project_vars['STATS_PATHS']["STATS_HOME"]
            cd_cmd   = f'cd {os.path.join(NIMB_HOME, "processing", "freesurfer")}'
            cmd      = f'{python_run} fs_stats2table.py -project {self.project} -stats_dir {dir_4stats}'
            process_type = 'fs_stats'
            subproc = 'get_stats'
            if not self.test:
                print(f'    sending to scheduler for task {task}')
                schedule.submit_4_processing(cmd, process_type, subproc, cd_cmd)
            else:
                print(f'    READY to send to scheduler for task {task}. TESTing active')
        elif task == 'fs-get-masks':
            cd_cmd   = f'cd {os.path.join(NIMB_HOME, "processing", "freesurfer")}'
            cmd      = f'{python_run} run_masks.py -project {self.project}'
            process_type = 'fs'
            subproc = 'run_masks'
            if not self.test:
                print(f'    sending to scheduler for task {task}')
                schedule.submit_4_processing(cmd, process_type, subproc, cd_cmd)
            else:
                print(f'    READY to send to scheduler for task {task}. TESTing active')


    '''
    EXTRACT STATISTICS related scripts
    '''
    def extract_statistics(self, apps = list()):
        print(f"{LogLVL.lvl1}extracting statistics; script not ready")
        for app in apps:
            if app == "freesurfer":
                if self.distrib_ready.chk_if_ready_for_stats():
                    PROCESSED_FS_DIR = self.distrib_hlp.prep_4fs_stats()
                    if PROCESSED_FS_DIR:
                        print('    ready to extract stats from project helper')
                #         self.send_2processing('fs-get-stats')


    def glm_fs_do(self, image = False):
        """
        ALGO:
            glm vars are present:
                if glm not done:
                    run fs-glm
                    extract fs-glm-image
        """
        print("{LogLVL.lvl1}peforming glm ...; script not ready")
        fs_glm_dir   = self.project_vars['STATS_PATHS']["FS_GLM_dir"]
        if DistributionReady(self.all_vars).chk_if_ready_for_fs_glm():
            GLM_file_path, GLM_dir = DistributionHelper(self.all_vars).prep_4fs_glm(fs_glm_dir,
                                                                        self.f_groups)
            FS_SUBJECTS_DIR = self.vars_local['FREESURFER']['FS_SUBJECTS_DIR']
            DistributionReady(self.all_vars).fs_chk_fsaverage_ready(FS_SUBJECTS_DIR)
            if GLM_file_path:
                print('    GLM file path is:',GLM_file_path)
                self.vars_local['PROCESSING']['processing_env']  = "tmux"
                schedule_fsglm = Scheduler(self.vars_local)
                cd_cmd = 'cd {}'.format(path.join(self.NIMB_HOME, 'processing', 'freesurfer'))
                cmd = f'{self.py_run_cmd} fs_glm_runglm.py -project {self.project} -glm_dir {GLM_dir}'
                schedule_fsglm.submit_4_processing(cmd, 'fs_glm','run_glm', cd_cmd)
        if image:
            if "export_screen" in self.vars_local['FREESURFER'] and \
                self.vars_local['FREESURFER']["export_screen"] == 1:
                if DistributionReady(self.all_vars).fs_ready():
                    print('before running the script, remember to source $FREESURFER_HOME')
                    cmd = '{} fs_glm_extract_images.py -project {}'.format(self.py_run_cmd, self.project)
                    cd_cmd = 'cd '+path.join(self.NIMB_HOME, 'processing', 'freesurfer')
                    self.schedule.submit_4_processing(cmd, 'fs_glm','extract_images', cd_cmd)
                else:
                    print(f"{LogLVL.lvl2}ERR: cannont extract image for GLM analysis: FreeSurfer not ready")
            else:
                print(f"Current environment is not ready to export screen")
                print(f"ERR! check that you can export your screen")
                print(f"Please define a computer where the screen can be used for FreeSurfer Freeview and tksurfer")
                print(f"ERR! Check the variable: export_screen in file credentials_path.py/nimb/local.json")


    '''
    GRID related scripts
    '''
    def get_df_f_groups(self):
        '''reading the user-provided tabular tsv/csv/xlsx file
            with IDs (id_col, id_proj_col) and potential data (variables_for_glm)
            ../nimb/projects.json -> self.f_groups
        Args:
            none
        Return:
            pandas.DataFrame: self.df_grid
            if file is missing:
                return self.make_default_grid()
        '''
        if self.distrib_hlp.get_files_for_stats(self.path_stats_dir,
                                                [self.f_groups,]):
            f_grid = os.path.join(self.path_stats_dir, self.f_groups)
            print(f'    file with groups is present: {f_grid}')
            self.df_grid    = self.tab.get_df(f_grid)
        else:
            self.df_grid    = self.make_default_grid()
        self.get_ids_from_grid()


    def get_ids_from_grid(self):
        """
        Args:
            none
        Return:
            list():           self._ids_project
            list():           self._ids_bids
        """
        if self._ids_bids_col not in self.df_grid.columns:
            print(f'{LogLVL.lvl1}column: {self._ids_bids_col} is missing from grid {self.f_groups}')
            print(f'{LogLVL.lvl2}adding to grid an empty column: {self._ids_bids_col}')
            self.df_grid[self._ids_bids_col] = ''
        if self._ids_project_col not in self.df_grid.columns:
            print(f'{LogLVL.lvl1}column: {self._ids_project_col} is missing from grid {self.f_groups}')
            print(f'{LogLVL.lvl2}adding to grid an empty column: {self._ids_project_col}')
            self.df_grid[self._ids_project_col] = ''

        self._ids_bids    = self.df_grid[self._ids_bids_col].tolist()
        self._ids_project = self.df_grid[self._ids_project_col].tolist()



    def make_default_grid(self):
        '''creates the file default.csv located in:
            ../nimb/projects.json -> materials_DIR -> ['local', 'PATH_2_DIR']
            ../nimb/projects.json -> STATS_PATHS -> STATS_HOME
            script will update file projects.json
        '''
        f_name = DEFAULT.default_tab_name
        df = self.tab.get_clean_df()
        df[self._ids_project_col] = ''
        df[self._ids_bids_col]    = ''
        print(f'    file with groups is absent; creating default grid file:\
                    in: {self.path_stats_dir}\
                    in: {self.materials_dir_pt}')
        self.tab.save_df(df,
            os.path.join(self.path_stats_dir, f_name))
        self.tab.save_df(df,
            os.path.join(self.materials_dir_pt, f_name))
        self.project_vars['fname_groups']    = f_name
        self.f_groups                        = f_name

        # updating self.all_vars and project.json file
        from setup.get_credentials_home import _get_credentials_home
        credentials_home = _get_credentials_home()
        json_projects    = os.path.join(credentials_home, 'projects.json')
        print(f'{LogLVL.lvl1}updating project.json at: {json_projects}')
        self.all_vars.projects[self.project] = self.project_vars
        save_json(self.all_vars.projects, json_projects)
        return df


    def mv_ids_bids_in_grid(self, ls_ids):
        """moving _ids_bids to _ids_project_col
        """
        for _id in ls_ids:
            index = self.tab.get_index_of_val(self.df_grid, self._ids_bids_col, _id)
            self.tab.change_val(self.df_grid,
                                index, self._ids_bids_col,
                                None)
            self._ids_bids.remove(_id)

            # rm from f_ids
            if _id in self._ids_all:
                self.update_f_ids(_id, "", "")
                self.save_f_ids()

            # adding to the _ids_project_col in the grid
            if _id not in self._ids_project:
                self.tab.change_val(self.df_grid, index, self._ids_project_col, _id)
                self._ids_project.append(_id)
            else:
                print(f'{LogLVL.lvl2}id: {_id} is already present in grid  in column: {self._ids_project_col}')
        self.tab.save_df(self.df_grid,
                        os.path.join(self.path_stats_dir, self.f_groups))


    def add_ids_project_to_bids_in_grid(self, ls_ids):
        """moving _id_project to _ids_bids_col
        """
        for _id_project in ls_ids:
            index = self.tab.get_index_of_val(self.df_grid, self._ids_project_col, _id_project)
            if _id_project not in self._ids_bids:
                _id_bids_probab = self.tab.get_value(self.df_grid, index, self._ids_bids_col)
                if not _id_bids_probab:
                    self.tab.change_val(self.df_grid, index, self._ids_bids_col, _id_project)
                    self.tab.change_val(self.df_grid, index, self._ids_project_col, None)
                    self._ids_bids.append(_id_project)
                    self._ids_project.remove(_id_project)
                else:
                    print(f'{LogLVL.lvl2}id: {_id_project} has a corresponding bids: {_id_bids_probab}')
                    print(f'{LogLVL.lvl3}please adjust the names')
            else:
                index_inbids = self.tab.get_index_of_val(self.df_grid, self._ids_bids_col, _id_project)
                if index != index_inbids:
                    print(f'{LogLVL.lvl2}id: {_id_project} is already present in grid  in column: {self._ids_bids_col}')
                    print(f'{LogLVL.lvl3}in the position: {index_inbids}')
                    print(f'{LogLVL.lvl3}ERR: there seem to be 2 participants with the same name and different data!')
                else:
                    self.tab.change_val(self.df_grid, index, self._ids_project_col, None)
                    self._ids_project.remove(_id_project)

        self.tab.save_df(self.df_grid,
                        os.path.join(self.path_stats_dir, self.f_groups))


    def add_ids_source_to_bids_in_grid(self, yes_bids):
        """
            adding a new id from sourcedata dir
            to the bids columns
            in the last position
        Args:
            yes_bids = {_id_src: _id_bids}
        Return:
            populates self._ids_bids
            updates self.df_grid
        """
        # defining variables
        self._ids_bids = self.df_grid[self._ids_bids_col].tolist()

        # loop to work with each _id_src
        for _id_src in yes_bids:
            _id_bids = yes_bids[_id_src]
            self._ids_bids = self._ids_bids + [_id_bids]
            # populating self.f_ids with _id_src
            print("populating f_ids with id_bids:", _id_bids, "for _id_src: ", _id_src)
            self.update_f_ids(_id_bids, DEFAULT.id_source_key, _id_src)
        self.save_f_ids()
        self.populate_df(self._ids_bids, self._ids_bids_col, self.df_grid)


    def populate_df(self, new_vals, col, df):
        """script aims to add new_id to the corresponding column
            in the df, which is a pandas.DataFrame
            it is expected that pandas.DataFrame.index is a range(0, n)
        Args:
            new_vals: list() of vals to be added
            col     : column name in pandas.DataFrame to be populated
        Return:
            saves the updated pandas.DataFrame
        """
        abspath_2save_file = os.path.join(self.path_stats_dir, self.f_groups)
        print("TESTING. self._ids_bids test 2 are:", new_vals)

        # list of _ids_bids
        vals_exist = df[col].tolist()

        # populating the grid, column _ids_bids_col with the new 
        if len(vals_exist) == 0:
            df[col] = new_vals
        else:
            vals2add = [i for i in new_vals if i not in vals_exist]
            ix_all = df.index.tolist()
            ix = len(ix_all) + 1
            for val in vals2add:
                df.loc[ix] = None
                df.at[ix, col] = val
                ix += 1
        print("TESTING. self.df_grid is:", df)
        self.tab.save_df(df, abspath_2save_file)


    def rm_id_from_grid(self, ls_2rm_from_grid):
        """removing _id from grid
        """
        for _id_project in ls_2rm_from_grid:
            index = self.tab.get_index_of_val(self.df_grid, self._ids_project_col, _id)
            self.tab.rm_row(self.df_grid, index)
            self._ids_project.remove(_id_project)
        self.tab.save_df(self.df_grid,
                        os.path.join(self.path_stats_dir, self.f_groups))


    '''
    f_ids related scripts
    '''
    def read_f_ids(self):
        """
        ALGO:
            if f_ids is present in the materials dir:
                ids are loaded
                if f_ids is present in the stats dir:
                    if the two files are are different:
                        save f_ids from materials to stats folder
        """
        self._ids_all = dict()
        if os.path.exists(self.f_ids_inmatdir):
            _ids_in_matdir = load_json(self.f_ids_inmatdir)
            self._ids_all = _ids_in_matdir
            if os.path.exists(self.f_ids_instatsdir):
                _ids_in_stats_dir = load_json(self.f_ids_instatsdir)
                if _ids_in_matdir != _ids_in_stats_dir:
                    print(f'{LogLVL.lvl1} ids in {self.f_ids_instatsdir}')
                    print(f'{LogLVL.lvl1} is DIFFERENT from: {self.f_ids_inmatdir}')
                    print(f'{LogLVL.lvl2}saving {self.f_ids_inmatdir}')
                    print(f'{LogLVL.lvl2}to: {self.path_stats_dir}')
                    save_json(_ids_in_matdir, self.f_ids_instatsdir)
        if not bool(self._ids_all):
            print(f'{LogLVL.lvl2} file with ids is EMPTY')
            self.save_f_ids()
        # print(f'{LogLVL.lvl1} ids all are: {self._ids_all}')


    """
    f_ids_nimb_classified related scripts

    """
    def get_ids_nimb_classified(self):
        _dir_2chk = self.srcdata_dir
        f_abspath = os.path.join(_dir_2chk, DEFAULT.f_nimb_classified)
        self._ids_nimb_classified = dict()

        if os.path.exists(f_abspath):
            self._ids_nimb_classified = load_json(f_abspath)
        else:
            print(f'{LogLVL.lvl1}file {f_abspath} is missing in: {_dir_2chk}')


    def copy_dir(self, yes_bids):
        """some bids folders might require to be copied
            to the rawdata folder
        Args:
            yes_bids = {_id_src: _id_bids}
        """
        ls_copied = list()
        ls_not_copied = list()
        for _id_src in yes_bids:
            _id_bids = yes_bids[_id_src]
            if self.srcdata_dir != self.BIDS_DIR:
                print(f"{LogLVL.lvl2}copying {_id_bids}")
                print(f"{LogLVL.lvl3}from :{self.srcdata_dir}")
                print(f"{LogLVL.lvl3}to   : {self.BIDS_DIR}")
                source_data = os.path.join(self.srcdata_dir, _id_bids)
                target      = os.path.join(self.BIDS_DIR, _id_bids)
                copied      = utilities.copy_rm_dir(source_data, target)
                if copied:
                    ls_copied.append(_id_bids)
                else:
                    ls_not_copied.append(_id_bids)

        # checker to confirm that some _ids_bids were not copied
        if ls_not_copied:
            print(f"{LogLVL.lvl2}some ids could not be copied:")
            print(f"{LogLVL.lvl3}{ls_not_copied}")

        return ls_copied, ls_not_copied


    # def get_id_project_from_nimb_classified(self, sub_label):
    #     """
    #         extracts the corresponding _id_project from
    #         _ids_nimb_classified
    #     Args:
    #         sub_label: sub_id of _id_bids, e.g., sub-ID
    #     Return:
    #         _id_project from _ids_nimb_classified
    #     """
    #     result = ''
    #     for _id_project in self._ids_nimb_classified:
    #         if sub_label in _id_project or \
    #         _id_project in sub_label:
    #             result = _id_project
    #             break
    #     return result
    # def populate_f_ids_from_nimb_classified(self):
    #     """
    #         self._ids_nimb_classified can contain
    #         either _id_source = from the sourdata folder
    #         or can contain _id_project, from the grid file
    #     """
    #     ls_2add_2grid = list()
    #     print(f'{LogLVL.lvl1} ids classified: {self._ids_nimb_classified}')
    #     for _id in self._ids_nimb_classified:
    #         for session in self._ids_nimb_classified[_id]:
    #             _id_bids, _ = self.dcm2bids.make_bids_id(_id, session)
    #             ls_2add_2grid.append(_id_bids)

    #             if _id_bids not in self._ids_all:
    #                 self._ids_all[_id_bids] = dict()
    #             self._ids_all[_id_bids][DEFAULT.id_source_key] = src_id
    #     self.save_f_ids()
    #     if ls_2add_2grid:
    #         self.populate_grid(ls_2add_2grid)


    # def populate_grid(self, ls_2add_2grid):
    #     # get grid
    #     # populate
    #     for _id_bids in ls_2add_2grid:
    #         if _id_bids not in self.df_grid[self._ids_bids_col]:
    #             self.df_grid.loc[-1] = self.df_grid.columns.values
    #             for col in self.df_grid.columns.tolist():
    #                 self.df_grid.at[-1, col] = ''
    #             self.df_grid.at[-1, self._ids_bids_col] = _id_bids
    #             self.df_grid.index = range(len(self.df_grid[self._ids_bids_col]))
    #     # self.tab.save_df(self.df_grid,
    #     #     os.path.join(self.path_stats_dir, self.f_groups))
    #     print('    NIMB ready to initiate processing of data')
    #     self.send_2processing('process')



    # def populate_f_ids_from_remote(self, _ids, _id_bids):
    #     '''
    #     import pandas as pd

    #     fs_processed_col = 'path_freesurfer711'
    #     irm_source_col = 'path_source'
    #     df = pd.read_csv(path.join(self.materials_dir_pt, self.projects[self.proj>
    #     ls_miss = df[irm_source_col].tolist()
    #     remote_loc = self.get_processing_location('freesurfer')
    #     remote_loc = remote_loc[0]
    #     check if self.fs_ready(remote_loc)
    #     host_name = ""
    #     if self.fs_ready():
    #        # 1. install required library and software on the local computer, including freesurfer
    #        self.setting_up_local_computer()
    #        # install freesurfer locally
    #        setup = SETUP_FREESURFER(self.locations)
    #     SSHHelper.upload_multiple_files_to_cluster(remote_loc, ls_miss, self.locations[remote_loc]["NIMB_PATHS"]["NIMB_tmp"]
    #     else:
    #         logger.debug("Setting up the remote server")
    #         # --get the name and the address of remote server
    #         for machine_name, machine_config in self.locations.items():
    #             if machine_name == 'local': # skip
    #                 continue
    #             # a. check the fs_install == 1
    #             if machine_config['FREESURFER']['FreeSurfer_install'] == 1:
    #                 host_name = self.projects['LOCATION'][machine_name]
    #                 self.setting_up_remote_linux_with_freesurfer(host_name=host_name)

    #     # continue working from below
    #     # must set SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR before calling: get from project
    #     # project name get from where?

    #     machine_PROCESSED_FS_DIR, PROCESSED_FS_DIR = self.get_PROCESSED_FS_DIR()
    #     machine_SOURCE_SUBJECTS_DIR, SOURCE_SUBJECTS_DIR = self.get_SOURCE_SUBJECTS_DIR()

    #     self.run_copy_subject_to_cluster(Project)
    #     logger.debug('Cluster analysis started')
    #     logger.debug("Cluster analysing running....")
    #     self.run_processing_on_cluster_2()
    #     '''

    #     # return _ids
    #     pass
