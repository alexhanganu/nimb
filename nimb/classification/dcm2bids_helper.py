#!/bin/python
"""
authors:
Alexandru Hanganu
"""

"""
1) tries to use dcm2bids app to create the bids folder structures
3) tries to create the config files and update the configurations
"""

from os import path, system, makedirs, listdir
import shutil
import json

from classify_definitions import BIDS_types, mr_modalities

class DCM2BIDS_helper():
    """
    goal: use UNFMontreal/dcm2bids to convert .dcm files to BIDS .nii.gz
    args: DIR with the subjects with .dcm files that need to be converted; currently must be unacrhived
    args: OUTPUT_DIR - DIR where the BIDS structure will be created
    algo: (1) convert (run()), (2) check if any unconverted (chk_if_processed()),
          (3) if not converted, try to create the config file (get_sidecar(), update_config())
          (4) redo run() up to repeat_lim
    """

    def __init__(self, proj_vars, project, repeat_lim = 1):
        self.proj_vars  = proj_vars
        self.project    = project
        self.run        = 1
        self.repeat_lim = repeat_lim
        self.repeat_updating = 0
        self.DICOM_DIR  = self.get_SUBJ_DIR()
        self.OUTPUT_DIR = self.chk_dir()

    def run(self, subjid = 'none'):
        #run dcm2bids:
        if self.run == '1':
            self.config_file = self.get_config_file()
            self.SUBJ_NAME = self.get_sub()
            print(self.SUBJ_NAME)
            system('dcm2bids -d {} -p {} -c {} -o {}'.format(self.DICOM_DIR, self.SUBJ_NAME, self.config_file, self.OUTPUT_DIR))
            self.sub_SUBJDIR = path.join(self.OUTPUT_DIR, 'tmp_dcm2bids', 'sub-{}'.format(self.SUBJ_NAME))
            self.chk_if_processed()

    def get_sub(self):
        return listdir(self.DICOM_DIR)[0]

    def get_config_file(self):
        config_file = path.join(self.OUTPUT_DIR,
                             'dcm2bids_config_{}.json'.format(self.project))
        if path.exists(config_file):
            return config_file
        else:
            shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'dcm2bids','dcm2bids_config_default.json'),
                        config_file)
            return config_file

    def chk_if_processed(self):
        if [i for i in listdir(self.sub_SUBJDIR) if '.nii.gz' in i]:
            if self.repeat_updating < self.repeat_lim:
                self.get_sidecar()
                print('removing folder tmp_dcm2bids/sub')
                self.rm_dir(self.sub_SUBJDIR)
                self.repeat_updating += 1
                print('re-renning dcm2bids')
                self.run(self.SUBJ_NAME)
        else:
            self.rm_dir(self.sub_SUBJDIR)

    def get_sidecar(self):
        sidecar = [i for i in listdir(self.sub_SUBJDIR) if '.json' in i][0]
        self.sidecar_content = self.get_json_content(path.join(self.sub_SUBJDIR, sidecar))
        data_Type, modality, criterion = self.classify_mri()
        self.update_config(data_Type, modality, criterion)

    def update_config(self, data_Type, modality, criterion):
        self.config = self.get_json_content(self.config_file)
        if self.chk_if_in_config(data_Type, modality, criterion):
            new_des = {
               ['dataType' : data_Type, 'modalityLabel' : modality,
               'criteria':{criterion: self.sidecar_content[criterion]}}
            self.config['descriptions'].append(new_des)
            self.save_json(self.config, self.config_file)
        else:
           print('criterion {} present in config file'.format(criterion))

    def chk_if_in_config(self, data_Type, modality, criterion):
        for des in self.config['descriptions']:
            if data_Type in self.config['descriptions'][des]['data_Type'] and
                modality in self.config['descriptions'][des]['modalityLabel'] and 
                self.sidecar_content[criterion] in self.config['descriptions'][des]['criteria'][criterion]:
                return True
            else:
                self.run == '0'
                return False

    def run_helper(self):
        helper_dir = path.join(self.OUTPUT_DIR, 'tmp_dcm2bids', 'helper')
        system('dcm2bids_helper -d {} -o {}'.format(self.DICOM_DIR, self.OUTPUT_DIR))
        # read the .json file and add parameters in the config file
        self.sidecar_content = open(path.join(helper_dir,
                      [i for i in listdir(path.join()) if '.json' in i][0]), 'r').readlines()
        return sidecar

    def classify_mri(self):
        # BIDS_types
        criterion = 'SeriesDescription'
        type = 'anat'
        modality = 'T1w'
        return type, modality, criterion

    def validate_bids(self):
        # https://github.com/bids-standard/bids-validator
        return True

    def save_json(self, data, file):
        with open(file, 'w') as f:
            json.dump(data, f, indent = 4)
    
    def get_json_content(self, file):
        with open(file, 'r') as f:
            return json.load(f)

    def get_SUBJ_DIR(self):
        DICOM_DIR = self.proj_vars['SOURCE_SUBJECTS_DIR'][1]
        if path.exists(DICOM_DIR):
            return DICOM_DIR
        else:
            print('    path is invalid: {}'.format(DICOM_DIR))
            return 'PATH_IS_MISSING'

    def rm_dir(self, DIR):
        system('rm -r {}'.format(DIR))

    def chk_dir(self):
        OUTPUT_DIR = self.proj_vars['SOURCE_BIDS_DIR'][1]
        if not path.exists(OUTPUT_DIR):
            makedirs(OUTPUT_DIR)
        return OUTPUT_DIR

