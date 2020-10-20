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
    def __init__(self, proj_vars, project):
        self.proj_vars = proj_vars
        self.project   = project
        self.chk_dir()

    def run(self, subjid = 'none'):
        #run dcm2bids:
        config_file = self.get_config_file()
        print(config_file)
        sub = self.get_sub()
        print(sub)
#        system('dcm2bids -d {} -p {} -c {} -o {}'.format(DICOM_DIR, SUBJ_NAME, config_file, OUTPUT_DIR))
        return True

    def get_sub(self):
        return listdir(self.proj_vars['SOURCE_SUBJECTS_DIR'])[0]

    def get_config_file(self):
        config_file = path.join(self.proj_vars['SOURCE_BIDS_DIR'],
                             'dcm2bids_config_{}.json'.format(self.project))
        if path.exists(config_file):
            return config_file
        else:
            shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'dcm2bids_config_default.json'),
                        config_file)
            return config_file

    def chk_if_processed(self):
        return True

    def get_sidecar(self):
        sidecar = '.json'
        helper_dir = path.join(OUTPUT_DIR, 'tmp_dcm2bids', 'helper')
        system('dcm2bids_helper -d {} -o {}'.format(DICOM_DIR, OUTPUT_DIR))
        # read the .json file and add parameters in the config file
        content = open(path.join(helper_dir,
                       [i for i in listdir(path.join()) if '.json' in i][0]), 'r').readlines()        
        return sidecar

    def create_config(self):
        # create an example of sidecar:
        # e.g., SeriesDescription parameter
        config_file = 'config_file'
        return config_file

    def validate_bids(self):
        # https://github.com/bids-standard/bids-validator
        return True

    def chk_dir(self):
        if not path.exists(self.proj_vars['SOURCE_BIDS_DIR']):
            makedirs(self.proj_vars['SOURCE_BIDS_DIR'])

