#!/bin/python
"""
authors:
Alexandru Hanganu
Kim Phuong Pham

1) uses nimb_classified.json
2) for each subject, each session: runs unfmontreal/dcm2bids
3) creates new BIDS folder in the DIR provided per project in proj_vars
validateBIDS: https://github.com/bids-standard/bids-validator
"""

import os
import shutil
import json
import time
import sys

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(module)s %(levelname)s: %(message)s')
logger.setLevel(logging.INFO)

from classification.classify_definitions import BIDS_types, mr_modalities, mr_modality_nimb_2_dcm2bids
from distribution.manage_archive import is_archive, ZipArchiveManagement
from distribution.utilities import makedir_ifnot_exist, load_json, save_json
from distribution.distribution_definitions import DEFAULT


class DCM2BIDS_helper():
    """
    goal: use UNFMontreal/dcm2bids to convert .dcm files to BIDS .nii.gz
    args: DICOM_DIR with the subjects with .dcm files that need to be converted
    args: OUTPUT_DIR - DIR where the BIDS structure will be created
    algo: (1) convert (run()), (2) check if any unconverted (chk_if_processed()),
          (3) if not converted, try to create the config file (update_config())
          (4) redo run() up to repeat_lim

    ID description:
    nimb_id   : ID based on provided MR data, 
                nimb_id name does NOT include the session; 
                e.g. ID1 (in PPMI nimb_id = 3378)
    bids_id   : ID after using the dcm2bids conversion;
                it includes the session;
                e.g.: sub-ID1_ses-1 (in PPMI nimb_id = 3378_ses-1)
    """

    def __init__(self,
		        proj_vars,
                project,
                DICOM_DIR    = 'default',
                tmp_dir      = 'none',
                repeat_lim = 10):

        self.proj_vars       = proj_vars
        self.project         = project
        self.run_stt         = 0
        self.repeat_lim      = repeat_lim
        self.repeat_updating = 0
        self.DICOM_DIR       = DICOM_DIR
        if DICOM_DIR == 'default':
            self.DICOM_DIR   = self.get_SUBJ_DIR()
        self.OUTPUT_DIR      = makedir_ifnot_exist(self.proj_vars['SOURCE_BIDS_DIR'][1])
        self.tmp_dir         = tmp_dir
        if self.tmp_dir == 'none':
            self.tmp_dir = os.path.dirname(self.OUTPUT_DIR)
        self.archived        = False


    def run(self,
        nimb_id = 'none',
        ses = 'none',
        nimb_classified_per_id = dict()):
        #run dcm2bids:
        '''
            if nimb_classified.json[nimb_id][archived]:
                extract from archive specific subject_session
                start dcm2bids for subject_session
        Return:
            self.bids_classified = 
            {'bids_id':
                {'anat':
                    {'t1': ['local',
                            'PATH_TO_rawdata/bids_id_label/bids_id_session/modality/bids_label_ses-xx_run-xx_T1w.nii.gz']},
                    },
                {'dwi':
                    {'dwi': ['local',
                            'PATH_TO_rawdata/bids_id_label/bids_id_session/modality/bids_label_ses-xx_run-xx_dwi.nii.gz'],
                    'bval': ['local',
                            'PATH_TO_rawdata/bids_id_label/bids_id_session/modality/bids_label_ses-xx_run-xx_dwi.bval'],
                    'bvec': ['local',
                            'PATH_TO_rawdata/bids_id_label/bids_id_session/modality/bids_label_ses-xx_run-xx_dwi.bvec']}
                    }
            }
        '''
        self.id_classified   = nimb_classified_per_id
        self.bids_classified = dict()
        print(f'{" " *8}folder with subjects is: {self.DICOM_DIR}')
        if self.id_classified:
            self.nimb_id = nimb_id
            self.ses     = ses
            self.bids_id, self.bids_id_dir = self.make_bids_id(self.nimb_id, self.ses)
            self.start_stepwise_choice()
        else:
            self.nimb_classified = dict()
            try:
                self.nimb_classified = load_json(os.path.join(self.DICOM_DIR, DEFAULT.f_nimb_classified))
            except Exception as e:
                print(f'{" " *12}  could not load the nimb_classified file at: {self.DICOM_DIR}')
                sys.exit(0)
            if self.nimb_classified:
                self.nimb_ids = list(self.nimb_classified.keys())
                for self.nimb_id in self.nimb_ids:
                    self.id_classified = self.nimb_classified[self.nimb_id]
                    for self.ses in [i for i in self.id_classified if i not in ('archived',)]:
                        self.bids_id, self.bids_id_dir = self.make_bids_id(self.nimb_id, self.ses)
                        self.start_stepwise_choice()
        return self.bids_classified, self.bids_id


    def start_stepwise_choice(self):
        print(f'{" " *8}classifying for id: {self.bids_id}')
        if self.id_classified['archived']:
            self.archived = True
        self.sub_SUBJDIR_tmp = os.path.join(self.OUTPUT_DIR, 'tmp_dcm2bids', self.bids_id)

        for self.data_Type in BIDS_types:
            if self.data_Type in self.id_classified[self.ses]:
                for self.modalityLabel_nimb in BIDS_types[self.data_Type]:
                    if self.modalityLabel_nimb in self.id_classified[self.ses][self.data_Type]:
                        self.modalityLabel = mr_modality_nimb_2_dcm2bids[self.modalityLabel_nimb] # changing to dcm2bids type modality_label
                        print(f'{" " *8}DCM2BIDS CONVERTING: type: {self.data_Type}; label: {self.modalityLabel}')
                        paths_2mr_data = self.id_classified[self.ses][self.data_Type][self.modalityLabel_nimb]
                        abs_path2mr_all = self.get_path_2mr(paths_2mr_data)
                        abs_path2mr  = abs_path2mr_all[0]
                        self.run_dcm2bids(abs_path2mr)
                        if os.path.exists(self.sub_SUBJDIR_tmp) and \
                            len(os.listdir(self.sub_SUBJDIR_tmp)) > 0:
                            print(f'{" " *12}> conversion did not find corresponding values in the configuration file')
                            print(f'{" " *12}> temporary converted: {self.sub_SUBJDIR_tmp}')
                            self.chk_if_processed(abs_path2mr)
                        else:
                            self.populate_bids_classifed()
                            self.cleaning_after_conversion(abs_path2mr)


    def populate_bids_classifed(self):
        """
        MUST ADJUST:
        dwi is inside anat, but must be new key
        {'sub-4085_ses-01':
            {'anat': 
                {'t1': ['local', 'path2.nii.gz']},
                'dwi': {'dwi': ['local', 'path2.nii.gz'],
                        'bval': ['local', 'path2.bval'],
                        'bvec': ['local', 'path2.bvec']}}}

        """
        if self.bids_id not in self.bids_classified:
            self.bids_classified[self.bids_id] = dict()
        if self.data_Type not in self.bids_classified[self.bids_id]:
            self.bids_classified[self.bids_id][self.data_Type] = dict()
        if self.modalityLabel_nimb not in self.bids_classified[self.bids_id][self.data_Type]:
            modality_content = self.modality_content_populate()
            self.bids_classified[self.bids_id][self.data_Type] = modality_content
        else:
            print(f'{" " * 12} ERR: modality {self.modalityLabel_nimb} is already present.')


    def modality_content_populate(self):
        abspath_2dir_data_type = os.path.join(self.OUTPUT_DIR, self.bids_id_dir, self.ses, self.data_Type)

        # populating nii.gz files
        abspath_nii_files      = list()
        ls_nii_files           = [i for i in os.listdir(abspath_2dir_data_type) if i.endswith('.nii.gz')]
        for file in ls_nii_files:
            abspath_nii_files.append(os.path.join(
                                        abspath_2dir_data_type, file))

        # populating dwi bval and bvec files
        modalityLabel_content = {self.modalityLabel_nimb: ['local', abspath_nii_files]}
        if self.modalityLabel_nimb == 'dwi':
            abspath_bval_files = list()
            bval_files = [i for i in os.listdir(abspath_2dir_data_type) if i.endswith('.bval')]
            for file in bval_files:
                abspath_bval_files.append(os.path.join(
                                        abspath_2dir_data_type, file))

            abspath_bvec_files = list()
            bvec_files = [i for i in os.listdir(abspath_2dir_data_type) if i.endswith('.bvec')]
            for file in bvec_files:
                abspath_bvec_files.append(os.path.join(
                                        abspath_2dir_data_type, file))

            modalityLabel_content = {'dwi' : ['local', abspath_nii_files],
                                     'bval': ['local', abspath_bval_files],
                                     'bvec': ['local', abspath_bvec_files]}
        return modalityLabel_content


    def run_dcm2bids(self, abs_path2mr):
        print("====RUNNING DCM2BIDS====" * 3)
        if self.run_stt == 0:
            print(">" * 80)
            self.config_file = self.get_config_file()
            print(f'{" " * 12}config file is: {self.config_file}')
            print(f'{" " * 15}folder with data located at: {abs_path2mr}')
            return_value = os.system('dcm2bids -d {} -p {} -s {} -c {} -o {}'.format(
                                                                                    abs_path2mr,
                                                                                    self.nimb_id,
                                                                                    self.ses,
                                                                                    self.config_file,
                                                                                    self.OUTPUT_DIR))
            # Calculate the return value code
            return_value = int(bin(return_value).replace("0b", "").rjust(16, '0')[:8], 2)
            if return_value != 0: # failed
                print(f'{" " *12}conversion finished with error')
                os.system('dcm2bids -d {} -p {} -s {} -c {} -o {}'.format(abs_path2mr,
                                                                        self.nimb_id,
                                                                        self.ses,
                                                                        self.config_file,
                                                                        self.OUTPUT_DIR))
            print("^" * 80)


    def chk_if_processed(self, abs_path2mr):
        """Check if any unconverted,
          - if not converted, update config file based on sidecar params (update_config())
          - redo run() up to repeat_lim
        """
        ls_niigz_files = [i for i in os.listdir(self.sub_SUBJDIR_tmp) if '.nii.gz' in i]
        if ls_niigz_files:
            print(f'{" " *12}> remaining nii in {self.sub_SUBJDIR_tmp}')
            if self.repeat_updating < self.repeat_lim:
                self.update = False
                for niigz_f in ls_niigz_files:
                    f_name = niigz_f.replace('.nii.gz','')
                    sidecar = f'{f_name}.json'
                    self.sidecar_content = load_json(os.path.join(self.sub_SUBJDIR_tmp, sidecar))
                    self.update_config()
                if self.update:
                    print(f'{" " *12}removing folder: {self.sub_SUBJDIR_tmp}')
                    self.repeat_updating += 1
                    self.rm_dir(self.sub_SUBJDIR_tmp)
                    print(f'{" " *12}re-renning dcm2bids')
                    self.run_dcm2bids(abs_path2mr)
                    print(f'{" " *12}looping to another chk_if_processed')
                    self.chk_if_processed(abs_path2mr)
        else:
            self.populate_bids_classifed()
            self.cleaning_after_conversion(abs_path2mr)


    def cleaning_after_conversion(self, abs_path2mr):
        print(f'{" " *15}>>>>DCM2BIDS conversion DONE')
        if os.path.exists(self.sub_SUBJDIR_tmp):
            print(f'{" " *15}removing folder: {self.sub_SUBJDIR_tmp}')
            self.rm_dir(self.sub_SUBJDIR_tmp)
        if os.path.exists(abs_path2mr):
            print(f'{" " *15}removing folder: {abs_path2mr}')
            self.rm_dir(abs_path2mr)
        print('\n')


    def update_config(self):
        """....."""
        self.add_criterion = False
        self.config   = load_json(self.config_file)
        criterion1    = 'SeriesDescription'
        sidecar_crit1 = self.sidecar_content[criterion1]

        list_criteria = list()
        for des in self.config['descriptions']:
            if des['dataType'] == self.data_Type and \
                des["modalityLabel"] == self.modalityLabel:
                list_criteria.append(des)
        if len(list_criteria) > 0:
            print(f'{" " *12}> there is at least one configuration with dataType: {self.data_Type}')
            for des in list_criteria[::-1]:
                if criterion1 in des['criteria']:
                    if des['criteria'][criterion1] == sidecar_crit1:
                        print(f'{" " *12} sidecar is present in the config file. Add another sidecar criterion in the dcm2bids_helper.py script')
                        self.add_criterion = True
                        sys.exit(0)
                    else:
                        list_criteria.remove(des)
        if len(list_criteria) > 0:
            print(f'{" " *12}> cannot find a correct sidecar location. Please add more parameters.')
        if len(list_criteria) == 0:
            print (f'{" " *12}> updating config with value: {sidecar_crit1}')
            new_des = {
               'dataType': self.data_Type,
               'modalityLabel' : self.modalityLabel,
               'criteria':{criterion1:  sidecar_crit1}}
            self.config['descriptions'].append(new_des)
            self.update = True

        if self.update:
            self.run_stt = 0
            save_json(self.config, self.config_file, print_space = 12)
        else:
           print(f'{" " *12}criterion {criterion1} present in config file')


    def get_config_file(self):
        """Get the dcm2bids_config_{project_name}.json.
           If not exist, get dcm2bids_config_default.json
        """
        config_file = os.path.join(self.OUTPUT_DIR,
                             f'dcm2bids_config_{self.project}.json')
        if os.path.exists(config_file):
            return config_file
        else:
            shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dcm2bids','dcm2bids_config_default.json'),
                        config_file)
            return config_file


    def get_path_2rawdata(self,
                        sub_label,
                        ses_label,
                        BIDS_type,
                        mr_modality):
        sub_rawdata_dir = os.path.join(self.OUTPUT_DIR, sub_label)
        path_2rawdata = ""
        if os.path.exists(sub_rawdata_dir):
            # verify if BIDS classificaiton OK
            sub_ses_bidstype_dir = os.path.join(sub_rawdata_dir, ses_label, BIDS_type)
            if os.path.exists(sub_ses_bidstype_dir):
                lsdir = os.listdir(sub_ses_bidstype_dir)
                # print("searching modality:", mr_modality)
                # print(os.listdir(sub_ses_bidstype_dir))
                bids_mr_modality = mr_modality_nimb_2_dcm2bids[mr_modality]
                niigz_f = [i for i in lsdir if '.nii.gz' in i and bids_mr_modality in i]
                if niigz_f:
                    path_2rawdata = os.path.join(sub_ses_bidstype_dir, niigz_f[0])
            else:
                print("something is missing:")
                print(os.listdir(os.path.join(sub_rawdata_dir, ses_label)))
                print(os.listdir(sub_ses_bidstype_dir))
        return path_2rawdata


    def make_bids_id(self, _id, session, run = False):
        '''
        https://github.com/bids-standard/bids-specification/blob/master/src/02-common-principles.md
        the _id_bids MUST have the structure: sub-<label>_ses-<label>_run-<label>
        the "sub-<label>" corresponds to the "subject" because of the "sub-" key.

        if there are multiple runs of the same session, the key "run" is used:
        "run" is an uninterrupted repetition of data acquisition
            that has the same acquisition parameters and task
            (however events can change from run to run
            due to different subject response or randomized nature of the stimuli).
            Run is a synonym of a data acquisition.
            if a subject leaves the scanner, the acquisition must be restarted.

        nimb is using DCM2BIDS and DCM2NIIx to create the corresponding BIDS files and structures
        this script intends to define one _id_bids that will be used throughout nimb
        '''
        _id_bids_label = _id
        ses_bids_label = session
        if "sub-" not in _id:
            _id_bids_label = f'sub-{_id}'
        if "ses-" not in session:
            ses_bids_label = f'ses-{session}'
        _id_bids = f'{_id_bids_label}_{ses_bids_label}'
        if run:
            run_bids_label = run
            if "run-" not in run:
                run_bids_label = f'run-{run}'
            _id_bids = f'{_id_bids_label}_{ses_bids_label}_{run_bids_label}'
        return _id_bids, _id_bids_label


    def is_bids_format(self, _id):
        """
        check if _id has a BIDS format
        if True:
            return True, expected bids folder, session name, run name
        """
        is_bids_format = False
        ses_exist = False
        run_label   = ""
        ses_label   = ""
        run_loc = _id.find('run-')
        ses_loc = _id.find('ses-')
        if '_run-' in _id:
            run_label = _id[run_loc:]
        if 'ses-' in _id:
            ses_exist = True
            if run_label:
                ses_label = _id[ses_loc:run_loc]
            else:
                ses_label = _id[ses_loc:]
        sub_label = _id[:ses_loc]

        if ses_label:
            if "_" in ses_label[-1]:
                ses_label = ses_label[:-1]
        if "_" in sub_label[-1]:
            sub_label = sub_label[:-1]

        if ses_exist and _id.startswith('sub-'):
            is_bids_format = True
        return is_bids_format, sub_label, ses_label, run_label


    # must adapt this and next defs to the ones from distribution_helper
    def get_path_2mr(self, paths_2mr_data):
        """
        Args:
            paths_2mr_data = list() of paths to MR data
        Return:
            paths_2mrdata = list() with all abspaths to MR data
        """
        paths_2mrdata = list()
        for path2mr_ in paths_2mr_data:
            if self.archived:
                path_2archive = self.id_classified['archived']
                if is_archive(path_2archive):
                    print(f'{" " *12}archive located at: {path_2archive}')
                    path_extracted = self.extract_from_archive(path_2archive,
                                                                path2mr_)
                    paths_2mrdata.append(path_extracted)
                else:
                    print(f'{" " *12} ile: {path_2archive} does not seem to be an archive')
                    paths_2mrdata.append('')
            else:
                paths_2mrdata.append(path2mr_)
        return paths_2mrdata


    def extract_from_archive(self, archive_abspath, path2mr_):
        self.tmp_dir_xtract = os.path.join(self.tmp_dir, 'tmp_for_classification')
        self.tmp_dir_err    = os.path.join(self.tmp_dir, 'tmp_for_classification_err')
#        print(f'            extracting data: {path2mr_}')
        makedir_ifnot_exist(self.tmp_dir_xtract)
        makedir_ifnot_exist(self.tmp_dir_err)
        ZipArchiveManagement(
            archive_abspath,
            path2xtrct = self.tmp_dir_xtract,
            path_err   = self.tmp_dir_err,
            dirs2xtrct = [path2mr_,])
        if len(os.listdir(self.tmp_dir_err)) == 0:
            shutil.rmtree(self.tmp_dir_err, ignore_errors=True)
        return self.tmp_dir_xtract


    def rm_dir(self, DIR):
        os.system('rm -r {}'.format(DIR))


    def get_SUBJ_DIR(self):
        """Get the path of DICOM_DIR"""
        DICOM_DIR = self.proj_vars['SOURCE_SUBJECTS_DIR'][1]
        if os.path.exists(DICOM_DIR):
            return DICOM_DIR
        else:
            print(f'{" " *12} path is invalid: {DICOM_DIR}')
            return 'PATH_IS_MISSING'


def make_bids_id(proj_id, session, run = False):
    '''
    https://github.com/bids-standard/bids-specification/blob/master/src/02-common-principles.md
    the _id_bids MUST have the structure: sub_<label>_ses-<label>
    the "sub-<label>" corresponds to the "subject" because of the "sub-" key.

    if there are multiple runs of the same session, the key "run" is used:
    "run" is an uninterrupted repetition of data acquisition
        that has the same acquisition parameters and task
        (however events can change from run to run
        due to different subject response or randomized nature of the stimuli).
        Run is a synonym of a data acquisition.
        if a subject leaves the scanner, the acquisition must be restarted.

    nimb is using DCM2BIDS and DCM2NIIx to create the corresponding BIDS files and structures
    this script intends to define one _id_bids that will be used throughout nimb
    '''
    _id_bids_dir = f'sub-{proj_id}'
    _id_bids = f'{_id_bids_dir}_{session}'
    '''must adjust run in the name
    '''
    if run:
        _id_bids = f'{_id_bids_dir}_{session}_{run}'
    return _id_bids, _id_bids_dir


def is_bids_format(_id):
    """
        check if _id has a BIDS format
        this def is read by AddDBManage and is missing the projects
    if True:
        return True, expected bids folder, session name, run name
    """
    is_bids_format = False
    ses_exist = False
    run_label   = ""
    ses_label   = ""
    run_loc = _id.find('run-')
    ses_loc = _id.find('ses-')
    if '_run-' in _id:
        run_label = _id[run_loc:]
    if 'ses-' in _id:
        ses_exist = True
        if run_label:
            ses_label = _id[ses_loc:run_loc]
        else:
            ses_label = _id[ses_loc:]
    sub_label = _id[:ses_loc]

    if ses_label:
        if "_" in ses_label[-1]:
            ses_label = ses_label[:-1]
    if "_" in sub_label[-1]:
        sub_label = sub_label[:-1]

    if ses_exist and _id.startswith('sub-'):
        is_bids_format = True
    return is_bids_format, sub_label, ses_label, run_label
