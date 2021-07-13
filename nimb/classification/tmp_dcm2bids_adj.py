#!/bin/python
import os, shutil, json, time, sys, logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(module)s %(levelname)s: %(message)s')
logger.setLevel(logging.INFO)

from classification.classify_definitions import BIDS_types, mr_modalities
from distribution.utilities import makedir_ifnot_exist, load_json, save_json
from distribution.distribution_definitions import DEFAULT

class DCM2BIDS_helper():

    def __init__(self, params,
                repeat_lim = 10):

        self.run_stt         = 0
        self.repeat_lim      = repeat_lim
        self.repeat_updating = 0
        self.OUTPUT_DIR      = params.p
        self.ses             = 'ses-01'
        self.bids_id         = params.id
        self.project         = 'loni_ppmi'

    def run(self, bids_id = 'none', ses = 'none'):
#        self.run_dcm2bids(abs_path2mr)
        self.sub_SUBJDIR = os.path.join(self.OUTPUT_DIR, 'tmp_dcm2bids', 'sub-{}'.format(self.bids_id))
        self.chk_if_processed()


    def get_sidecar(self, f_name): # not correct - need to modify
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

        self.config = self.get_json_content(self.config_file)
        list_criteria = set()
        for des in self.config['descriptions']:
            criterion = list(des['criteria'].keys())[0]
            modality = des["modalityLabel"]
            type = des['dataType']
            list_criteria.add((type, modality, criterion))

        # return type, modality, criterion
        return list_criteria


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
            print('return value is: ',return_value)
#            return_value = int(bin(return_value).replace("0b", "").rjust(16, '0')[:8], 2)
#            if return_value != 0:# failed
#                os.system('dcm2bids -d {} -p {} -s {} -c {} -o {}'.format(abs_path2mr, self.bids_id, self.ses, self.config_file,
#                                                                 self.OUTPUT_DIR))
#            self.sub_SUBJDIR = os.path.join(self.OUTPUT_DIR, 'tmp_dcm2bids', 'sub-{}'.format(self.bids_id))
            print("        subject located in:", self.sub_SUBJDIR)
            self.chk_if_processed()
            print("/"*40)


    def chk_if_processed(self):
        print("*********Convert remaining folder",self.sub_SUBJDIR)
        ls_niigz_files = [i for i in os.listdir(self.sub_SUBJDIR) if '.nii.gz' in i]
        if ls_niigz_files:
            print("        remaining nii in ", self.sub_SUBJDIR)
            if self.repeat_updating < self.repeat_lim:
                for niigz_f in ls_niigz_files:
                    f_name = niigz_f.replace('.nii.gz','')
                    self.get_sidecar(f_name)
                print('        removing folder tmp_dcm2bids/sub')
                # self.rm_dir(self.sub_SUBJDIR)
                self.repeat_updating += 1
                print('    re-renning dcm2bids')
#                self.run(self.SUBJ_NAME)
        else:
            print("        case2")
#            self.rm_dir(self.sub_SUBJDIR)

    def rm_dir(self, DIR):
        os.system('rm -r {}'.format(DIR))


    def get_config_file(self):
        config_file = os.path.join(self.OUTPUT_DIR,
                             'dcm2bids_config_{}.json'.format(self.project))
        if os.path.exists(config_file):
            return config_file
        else:
            print('config file is missing')



def get_parameters():
    """get parameters for nimb"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""text {}""".format(
            __version__
        ),
        epilog="""
            Documentation at https://github.com/alexhanganu/nimb
            """,
    )

    parser.add_argument(
        "-p", required=False,
    )

    parser.add_argument(
        "-id", required=False,
    )

    params = parser.parse_args()
    return params


if __name__ == "__main__":
    params      = get_parameters()
    DCM2BIDS_helper(params, repeat_lim = 10)



