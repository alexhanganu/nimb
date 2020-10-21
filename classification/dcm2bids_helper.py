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

class DCM2BIDS_helper():
    def __init__(self, proj_vars, project, repeat_lim = 1):
        self.proj_vars  = proj_vars
        self.project    = project
        self.repeat_lim = repeat_lim
        self.repeat_updating = 0
        self.DICOM_DIR  = self.get_SUBJ_DIR()
        self.OUTPUT_DIR = self.chk_dir()

    def run(self, subjid = 'none'):
        #run dcm2bids:
        self.config_file = self.get_config_file()
        self.SUBJ_NAME = self.get_sub()
        print(self.SUBJ_NAME)
        system('dcm2bids -d {} -p {} -c {} -o {}'.format(self.DICOM_DIR, self.SUBJ_NAME, self.config_file, self.OUTPUT_DIR))
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
        if [i for i in listdir(path.join(self.OUTPUT_DIR, 'tmp_dcm2bids', 'sub-{}'.format(self.SUBJ_NAME))) if '.nii.gz' in i]:
            self.repeat_updating += 1
            if self.repeat_updating < self.repeat_lim:
                self.get_sidecar()
                print('removing folder tmp_dcm2bids')
                system('rm -r {}'.format(path.join(self.OUTPUT_DIR, 'tmp_dcm2bids')))
                print('re-renning dcm2bids')
                self.run(self.SUBJ_NAME)

    def get_sidecar(self):
        sidecar = [i for i in listdir(path.join(self.OUTPUT_DIR, 'tmp_dcm2bids', 'sub-{}'.format(self.SUBJ_NAME))) if '.json' in i][0]
        content = self.get_json_content(sidecar)
        data_Type, modality = self.classify_mri(content['SeriesDescription'])
        self.update_config(content, data_Type, modality)

    def update_config(self, content, data_Type, modality):
        old_config = self.get_json_content(self.config_file)
        read_key = [k for k in range(0,len(data['descriptions'])) if data['descriptions'][k]['dataType'] == data_Type and data['descriptions'][k]['modalityLabel'] == modality][0]
        criterion = 'SeriesDescription'
        key2populate = old_config['descriptions'][read_key]['criteria'][criterion]
        if content[criterion] not in key2populate:
            if len(key2populate) >1:
                newkey = [key2populate, content[criterion]]
            else:
                newkey = [i for i in key2populate] + [content[criterion]]
            old_config['descriptions'][read_key]['criteria'][criterion] = newkey
        self.save_json(old_config, self.get_config_file())
        self.config_file = old_config


    def run_helper(self):
        helper_dir = path.join(self.OUTPUT_DIR, 'tmp_dcm2bids', 'helper')
        system('dcm2bids_helper -d {} -o {}'.format(self.DICOM_DIR, self.OUTPUT_DIR))
        # read the .json file and add parameters in the config file
        content = open(path.join(helper_dir,
                      [i for i in listdir(path.join()) if '.json' in i][0]), 'r').readlines()
        return sidecar

    def classify_mri(self, param):
        type = 'anat'
        modality = 'T1w'
        return type, modality

    def validate_bids(self):
        # https://github.com/bids-standard/bids-validator
        return True

    def save_json(self, data, file):
        with open(file, 'w') as f:
            json.dump(data, f, indent = 4)
    
    def get_json_content(self, file):
        import json
        with open(file, 'r') as f:
            return json.load(f)

    def get_SUBJ_DIR(self):
        DICOM_DIR = self.proj_vars['SOURCE_SUBJECTS_DIR'][1]
        if path.exists(DICOM_DIR):
            return DICOM_DIR
        else:
            print('    path is invalid: {}'.format(DICOM_DIR))
            return 'PATH_IS_MISSING'

    def chk_dir(self):
        OUTPUT_DIR = self.proj_vars['SOURCE_BIDS_DIR'][1]
        if not path.exists(OUTPUT_DIR):
            makedirs(OUTPUT_DIR)
        return OUTPUT_DIR

