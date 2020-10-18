#!/bin/python
"""
authors:
Alexandru Hanganu
"""

'''
1) tries to use dcm2bids app to create the bids folder structures
3) tries to create the config files and update the configurations
'''

from os import path, listdir, getenv, walk

# create an example of sidecar:
system('dcm2bids_helper -d {} -o {}'.format(DICOM_DIR, OUTPUT_DIR))

# read the .json file and add parameters in the config file
helper_dir = path.join(OUTPUT_DIR, 'tmp_dcm2bids', 'helper')
content = open(path.join(helper_dir,
               [i for i in listdir(path.join()) if '.json' in i][0]), 'r').readlines()

# e.g., SeriesDescription parameter

#run dcm2bids:
system('dcm2bids -d {} -p {} -c {} -o {}'.format(DICOM_DIR, SUBJ_NAME, config_file, OUTPUT_DIR))
