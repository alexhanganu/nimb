#!/bin/python
"""
authors:
Alexandru Hanganu
"""

"""
1) tries to use dcm2bids app to create the bids folder structures
3) tries to create the config files and update the configurations
"""

from os import path, listdir, getenv, walk

class DCM2BIDS_helper():
    def __init__(self, SUBJ):
        self.SUBJ = SUBJ
        
    def dcm2bids_run(self):
        #run dcm2bids:
        system('dcm2bids -d {} -p {} -c {} -o {}'.format(DICOM_DIR, SUBJ_NAME, config_file, OUTPUT_DIR))

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

if __name__ == '__main__':
    SUBJ = 'test'
    DCM2BIDS_helper(SUBJ).dcm2bids_run()