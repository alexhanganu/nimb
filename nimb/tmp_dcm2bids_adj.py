#!/bin/python
"""
authors:
Alexandru Hanganu
Kim Phuong Pham

1) uses nimb_classified.json
2) for each subject, each session: runs unfmontreal/dcm2bids
3) creates new BIDS folder in the DIR provided per project in proj_vars
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
    """

    def __init__(self,
		        proj_vars,
                project,
                nimb_classified_per_id = dict(),
                DICOM_DIR    = 'default',
                tmp_dir      = 'none',
                repeat_lim = 10):

        self.proj_vars       = proj_vars
        self.project         = project
        self.id_classified   = nimb_classified_per_id
        self.run_stt         = 0
        self.repeat_lim      = repeat_lim
        self.repeat_updating = 0
        self.DICOM_DIR       = DICOM_DIR
        if DICOM_DIR == 'default':
            self.DICOM_DIR   = self.get_SUBJ_DIR()
        self.tmp_dir         = tmp_dir
        self.OUTPUT_DIR      = self.chk_dir(self.proj_vars['SOURCE_BIDS_DIR'][1])
        self.archived        = False


    def run(self, bids_id = 'none', ses = 'none'):
        #run dcm2bids:
        '''
            if nimb_classified.json[bids_id][archived]:
                extract from archive specific subject_session
                start dcm2bids for subject_session
        '''
        print(f'        folder with subjects is: {self.DICOM_DIR}')
        self.bids_id = bids_id
        self.ses     = ses
        if self.id_classified:
            self.start_stepwise_choice()
        else:
            self.nimb_classified = dict()
            try:
                self.nimb_classified = load_json(os.path.join(self.DICOM_DIR, DEFAULT.f_nimb_classified))
            except Exception as e:
                print(f'        could not load the nimb_classified file at: {self.DICOM_DIR}')
                sys.exit(0)
        if self.nimb_classified:
            self.bids_ids = list(self.nimb_classified.keys())
            for self.bids_id in self.bids_ids[:1]: # !!!!!!!!!!!!!this is for testing
                self.id_classified = self.nimb_classified[self.bids_id]
                for self.ses in [i for i in self.id_classified if i not in ('archived',)]:
                    self.start_stepwise_choice()


    def start_stepwise_choice(self):
        print(f'        classifying for id: {self.bids_id} for session: {self.ses}')
#        print(f'        nimb_classified data are: {self.id_classified}')
        if self.id_classified['archived']:
            self.archived = True
        for BIDS_type in BIDS_types:
            if BIDS_type in self.id_classified[self.ses] and BIDS_type == 'anat':  # !!!!!!!!!!!!!!anat is used to adjust the script
                for mr_modality in BIDS_types[BIDS_type]:
                    if mr_modality in self.id_classified[self.ses][BIDS_type]:
                       paths_2mr_data = self.id_classified[self.ses][BIDS_type][mr_modality]
                       for path2mr_ in paths_2mr_data:
                            print(f'        converting mr type: {BIDS_type}')
#                            print(f'            dcm files located in: {path2mr}')
                            abs_path2mr = self.get_path_2mr(path2mr_)
                            self.run_dcm2bids(abs_path2mr)
                            self.sub_SUBJDIR = os.path.join(self.OUTPUT_DIR, 'tmp_dcm2bids', f'sub-{self.bids_id}_{self.ses}')
                            print("        subject located in:", self.sub_SUBJDIR)
                            self.chk_if_processed()


    def run_dcm2bids(self, abs_path2mr):
        if self.run_stt == 0:
            self.config_file = self.get_config_file()
            print("*"*50)
            print("        config_file is: ", self.config_file)
            print("        bids id:", self.bids_id)
            print("*" * 50)
            return_value = os.system('dcm2bids -d {} -p {} -s {} -c {} -o {}'.format(
                                                                                    abs_path2mr,
                                                                                    self.bids_id,
                                                                                    self.ses,
                                                                                    self.config_file,
                                                                                    self.OUTPUT_DIR))
            # with each subject create temporary directory for Dcm2niix
            # self.chk_dir(self.sub_SUBJDIR)
            # Run the dcm2bids aself.SUBJ_NAMEpp
            # print(self.DICOM_DIR, subj_name,self.OUTPUT_DIR)
            # --clobber: Overwrite output if it exists
            # ----forceDcm2niix: Overwrite previous temporary dcm2niix output if it exists
#            sub_dir = os.path.join(self.DICOM_DIR, self.bids_id)
            # the tempo subj dir contains remaining unconvert files
            # Calculate the return value code
            print('return value is: ',return_value)
            return_value = int(bin(return_value).replace("0b", "").rjust(16, '0')[:8], 2)
            if return_value != 0: # failed
                os.system('dcm2bids -d {} -p {} -s {} -c {} -o {}'.format(abs_path2mr, self.bids_id, self.ses, self.config_file,
                                                                 self.OUTPUT_DIR))
            print("/"*40)


    def get_path_2mr(self, path2mr_):
        if self.archived:
            path_2archive = self.id_classified['archived']
            print(f'        archive located at: {path_2archive}')
            if is_archive(path_2archive):
                print('        is archive')
                return self.extract_from_archive(path_2archive,
                                                 path2mr_)
            else:
                print(f'        file: {path_2archive} does not seem to be an archive')
                return ''
        else:
            return path2mr_


    def extract_from_archive(self, archive_abspath, path2mr_):
        if self.tmp_dir == 'none':
            self.tmp_dir = os.path.dirname(archive_abspath)
        tmp_dir_xtract = os.path.join(self.tmp_dir, 'tmp_for_classification')
        tmp_dir_err    = os.path.join(self.tmp_dir, 'tmp_for_classification_err')
#        print(f'            extracting data: {path2mr_}')
        makedir_ifnot_exist(tmp_dir_xtract)
        makedir_ifnot_exist(tmp_dir_err)
        ZipArchiveManagement(
            archive_abspath,
            path2xtrct = tmp_dir_xtract,
            path_err   = tmp_dir_err,
            dirs2xtrct = [path2mr_,])
        if len(os.listdir(tmp_dir_err)) == 0:
            shutil.rmtree(tmp_dir_err, ignore_errors=True)
        return tmp_dir_xtract


    def get_config_file(self):
        """Get the dcm2bids_config_{project_name}.json.
           If not exist, get dcm2bids_config_default.json
        """
        config_file = os.path.join(self.OUTPUT_DIR,
                             'dcm2bids_config_{}.json'.format(self.project))
        if os.path.exists(config_file):
            return config_file
        else:
            shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dcm2bids','dcm2bids_config_default.json'),
                        config_file)
            return config_file


    def chk_if_processed(self):
        """Check if any unconverted,
          - if not converted, try to create the config file (get_sidecar(), update_config())
          - redo run() up to repeat_lim
        """
        # self.chk_dir(self.sub_SUBJDIR)
        # Read all .nii in subjdir and move to appropriate folder
        print("*********Convert remaining folder",self.sub_SUBJDIR)
        if [i for i in os.listdir(self.sub_SUBJDIR) if '.nii.gz' in i]:
            print("        remaining nii in ", self.sub_SUBJDIR)
            if self.repeat_updating < self.repeat_lim:
                self.get_sidecar()
                print('        removing folder tmp_dcm2bids/sub')
                # self.rm_dir(self.sub_SUBJDIR)
                self.repeat_updating += 1
                print('    re-renning dcm2bids')
                self.run(self.SUBJ_NAME)
        else:
            print("        case2")
            self.rm_dir(self.sub_SUBJDIR)


    def get_sidecar(self): # not correct - need to modify
        """...."""
        print("    getting sidecar") # list of sidecar
        list_sidecar = [i for i in os.listdir(self.sub_SUBJDIR) if '.json' in i]
        sidecar = list_sidecar[0]
        print("    sidecar: ", list_sidecar, sidecar)
        print(">>>>"*20)
        # for sidecar in list_sidecar:
        print(os.path.join(self.sub_SUBJDIR, sidecar))
        print(">>>>" * 20)
        self.sidecar_content = load_json(os.path.join(self.sub_SUBJDIR, sidecar))
        # data_Type, modality, criterion = self.classify_mri()
        list_critera = self.classify_mri()
        print(list_critera)
        print("##################################")
        # get all types and etc
        # loop to update config for each of them
        # todo: here

        print("*" * 50)

        # print(data_Type, modality, criterion)
        print("*" * 50)
        for criteron in list_critera:
            data_Type, modality, criterion1 = criteron
            self.update_config(data_Type, modality, criterion1)
            break
            # break


    def update_config(self, data_Type, modality, criterion): # to modify
        """....."""
        print("Config file:",self.config_file)
        # if criterion in sidecar not = criterion in config -> add new des
        if  not self.chk_if_in_config(data_Type, modality, criterion):
            new_des = {
               'dataType': data_Type,
               'modalityLabel' : modality,
               'criteria':{criterion:  self.sidecar_content[criterion]}}
            print("==="*30)
            print(new_des)
            print("===" * 30)
            self.config['descriptions'].append(new_des)
            self.save_json(self.config, self.config_file)
            print("<<<<<<<<>>>> chet tiet .." + self.config_file)
        else:
           print('criterion {} present in config file'.format(criterion))


    def chk_if_in_config(self, data_Type, modality, criterion):
        """
        true: in config
        false: not in config
        """
        """..If sidecar criterion exist in config.."""
        print ("chk_if_in_config")
        self.config = load_json(self.config_file)
        print(self.sidecar_content.keys())
        print("++" * 20)
        # print(self.config['descriptions'])
        print("++" * 20)
        for des in self.config['descriptions']:
            if not (criterion in self.sidecar_content):
                continue
            # kiem tra key co trong des khong
            if not criterion in des['criteria'].keys():
                continue
            if not ( data_Type in des['dataType'] and modality in des['modalityLabel'] ):
                continue
            # kiem tra value of key co trong des khong
            if  (self.sidecar_content[criterion] == des['criteria'][criterion]):
                return True

            # if not self.sidecar_content[criterion] in des['criteria'].keys():
            #     continue
            #     #############
            # if data_Type in des['dataType'] and \
            #    modality in des['modalityLabel'] and \
            #    self.sidecar_content[criterion] == des['criteria'][criterion]: # gia tri giong nhau thi false
            #     print ("*"*30 + "chk_if_in_config" +"#"*30)
            #     # move .nii + classify theo bids
            #     return False
            # ################
            # if data_Type in des['dataType'] and \
            #    modality in des['modalityLabel'] and \
            #    self.sidecar_content[criterion] in des['criteria'][criterion]: # if paired
            #     print ("*"*30 + "chk_if_in_config" +"#"*30)
            #     # move .nii + classify theo bids
            #     return True
            # else: # no pairing -> chinh file config lai
            #     self.run_stt = 0# coi lai
                # return False
            # todo: here
        #self.run_stt = 0
        return False

    def run_helper(self):
        """...."""
        helper_dir = os.path.join(self.OUTPUT_DIR, 'tmp_dcm2bids', 'helper')
        os.system('dcm2bids_helper -d {} -o {}'.format(self.DICOM_DIR, self.OUTPUT_DIR))
        # read the .json file and add parameters in the config file
        self.sidecar_content = open(os.path.join(helper_dir,
                      [i for i in os.listdir(os.path.join()) if '.json' in i][0]), 'r').readlines()
        return self.sidecar_content


    def classify_mri(self):
        """...."""
        # BIDS_types
        criterion = 'SeriesDescription'
        type = 'anat'
        modality = 'T1w'

        self.config = load_json(self.config_file)
        list_criteria = set()
        for des in self.config['descriptions']:
            criterion = list(des['criteria'].keys())[0]
            modality = des["modalityLabel"]
            type = des['dataType']
            list_criteria.add((type, modality, criterion))

        # return type, modality, criterion
        return list_criteria

    def validate_bids(self):
        print("test validate_bids")
        # https://github.com/bids-standard/bids-validator
        return True


    def save_json(self, data, file):
        with open(file, 'w') as f:
            json.dump(data, f, indent = 4)


#    def get_json_content(self, file):
#        with open(file, 'r') as f:
#            return json.load(f)

    def get_SUBJ_DIR(self):
        """Get the path of DICOM_DIR"""
        DICOM_DIR = self.proj_vars['SOURCE_SUBJECTS_DIR'][1]
        if os.path.exists(DICOM_DIR):
            return DICOM_DIR
        else:
            print('    path is invalid: {}'.format(DICOM_DIR))
            return 'PATH_IS_MISSING'


    def rm_dir(self, DIR):
        os.system('rm -r {}'.format(DIR))


    def chk_dir(self, location):
        """Check if a directory exists. If not, create a directory"""
        print(location)
        if not os.path.exists(location):
            os.makedirs(location)
        return location

