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
import time

from classification.classify_definitions import BIDS_types, mr_modalities

class DCM2BIDS_helper():
    """
    goal: use UNFMontreal/dcm2bids to convert .dcm files to BIDS .nii.gz
    args: DIR with the subjects with .dcm files that need to be converted; currently must be unacrhived
    args: OUTPUT_DIR - DIR where the BIDS structure will be created
    algo: (1) convert (run()), (2) check if any unconverted (chk_if_processed()),
          (3) if not converted, try to create the config file (get_sidecar(), update_config())
          (4) redo run() up to repeat_lim
    """

    def __init__(self, proj_vars, project, repeat_lim = 10):
        self.proj_vars  = proj_vars
        self.project    = project    #project item in projects.json
        self.run_stt        = 1
        self.repeat_lim = repeat_lim
        self.repeat_updating = 0
        self.DICOM_DIR  = self.get_SUBJ_DIR()
        self.OUTPUT_DIR = self.chk_dir(self.proj_vars['SOURCE_BIDS_DIR'][1])


    def run(self, subjid = 'none'):
        #run dcm2bids:
        if self.run_stt == 1:
            self.config_file = self.get_config_file()
            print("config_file", self.config_file)
            list_subj = self.get_sub()
            print("kp_list_subj:", list_subj)
            if list_subj != None:
                for subj_name in list_subj:
                    # self.SUBJ_NAME = self.get_sub()
                    self.SUBJ_NAME = subj_name
                    print("kptest_subjectdir:", self.SUBJ_NAME)
                    # with each subject create temporary directory for Dcm2niix
                    # self.chk_dir(self.sub_SUBJDIR)
                    # Run the dcm2bids aself.SUBJ_NAMEpp
                    try:
                        # print(self.DICOM_DIR, subj_name,self.OUTPUT_DIR)
                        # --clobber: Overwrite output if it exists
                        # ----forceDcm2niix: Overwrite previous temporary dcm2niix output if it exists
                        sub_dir = path.join(self.DICOM_DIR, self.SUBJ_NAME)
                        return_value = system('dcm2bids -d {} -p {} -c {} -o {}'.format(sub_dir, self.SUBJ_NAME, self.config_file, self.OUTPUT_DIR))
                        # the tempo subj dir contains remaining unconvert files
                        # Calculate the return value code
                        return_value = int(bin(return_value).replace("0b", "").rjust(16, '0')[:8], 2)
                        if return_value != 0:# failed
                            system('dcm2bids -d {} -p {} -c {} -o {}'.format(sub_dir, self.SUBJ_NAME, self.config_file,
                                                                             self.OUTPUT_DIR))
                        self.sub_SUBJDIR = path.join(self.OUTPUT_DIR, 'tmp_dcm2bids', 'sub-{}'.format(self.SUBJ_NAME))
                        print("kptest_sub_dir:", self.sub_SUBJDIR)
                        self.chk_if_processed()
                    except Exception as e: # run second time
                        system('dcm2bids -d {} -p {} -c {} -o {}'.format(self.DICOM_DIR, self.SUBJ_NAME, self.config_file, self.OUTPUT_DIR))
                    finally:
                        print("/"*40)
            else:
                return



    def get_sub(self):
        """Get list of all file names in the input dir """
        try:
            list_files = listdir(self.DICOM_DIR)
            return list_files
        except Exception as e:
            print(e)
            return


    def get_config_file(self):
        """Get the dcm2bids_config_{project_name}.json.
           If not exist, get dcm2bids_config_default.json
        """
        config_file = path.join(self.OUTPUT_DIR,
                             'dcm2bids_config_{}.json'.format(self.project))
        if path.exists(config_file):
            return config_file
        else:
            shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'dcm2bids','dcm2bids_config_default.json'),
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
        if [i for i in listdir(self.sub_SUBJDIR) if '.nii.gz' in i]:
            print("case1")
            if self.repeat_updating < self.repeat_lim:
                self.get_sidecar()
                print('removing folder tmp_dcm2bids/sub')
                self.rm_dir(self.sub_SUBJDIR)
                self.repeat_updating += 1
                print('re-renning dcm2bids')
                self.run(self.SUBJ_NAME)
        else:
            print("case2")
            self.rm_dir(self.sub_SUBJDIR)


    def get_sidecar(self): # not correct - need to modify
        """...."""
        print("get_sidecar")
        sidecar = [i for i in listdir(self.sub_SUBJDIR) if '.json' in i][0]
        print("sidecar:", sidecar)
        self.sidecar_content = self.get_json_content(path.join(self.sub_SUBJDIR, sidecar))
        #print("kp_sidecar:", self.sidecar_content)
        data_Type, modality, criterion = self.classify_mri()
        self.update_config(data_Type, modality, criterion)


    def update_config(self, data_Type, modality, criterion): # to modify
        """....."""
        print("Config file:",self.config_file)
        self.config = self.get_json_content(self.config_file)
        if self.chk_if_in_config(data_Type, modality, criterion):
            new_des = {
               'dataType': data_Type,
               'modalityLabel' : modality,
               'criteria':{criterion: self.sidecar_content[criterion]}}
            self.config['descriptions'].append(new_des)
            self.save_json(self.config, self.config_file)
        else:
           print('criterion {} present in config file'.format(criterion))


    def chk_if_in_config(self, data_Type, modality, criterion):
        """...."""
        print ("chk_if_in_config")
        for des in self.config['descriptions']:
            # print("json:", des['data_Type'])
            # print("json2:", des['modalityLabel'])
            if data_Type in des['dataType'] and \
               modality in des['modalityLabel'] and \
               self.sidecar_content[criterion] in des['criteria'][criterion]:
                    print("kp_criterion_found:", self.sidecar_content[criterion])
                    return True
            else:
                self.run_stt == 0
                return False


    def run_helper(self):
        """...."""
        helper_dir = path.join(self.OUTPUT_DIR, 'tmp_dcm2bids', 'helper')
        system('dcm2bids_helper -d {} -o {}'.format(self.DICOM_DIR, self.OUTPUT_DIR))
        # read the .json file and add parameters in the config file
        self.sidecar_content = open(path.join(helper_dir,
                      [i for i in listdir(path.join()) if '.json' in i][0]), 'r').readlines()
        return self.sidecar_content


    def classify_mri(self):
        """...."""
        # BIDS_types
        criterion = 'SeriesDescription'
        type = 'anat'
        modality = 'T1w'
        return type, modality, criterion


    def validate_bids(self):
        print("test validate_bids")
        # https://github.com/bids-standard/bids-validator
        return True


    def save_json(self, data, file):
        with open(file, 'w') as f:
            json.dump(data, f, indent = 4)


    def get_json_content(self, file):
        with open(file, 'r') as f:
            return json.load(f)

    def get_SUBJ_DIR(self):
        """Get the path of DICOM_DIR"""
        DICOM_DIR = self.proj_vars['SOURCE_SUBJECTS_DIR'][1]
        if path.exists(DICOM_DIR):
            return DICOM_DIR
        else:
            print('    path is invalid: {}'.format(DICOM_DIR))
            return 'PATH_IS_MISSING'


    def rm_dir(self, DIR):
        system('rm -r {}'.format(DIR))


    def chk_dir(self, location):
        """Check if a directory exists. If not, create a directory"""
        print(location)
        if not path.exists(location):
            makedirs(location)
        return location

