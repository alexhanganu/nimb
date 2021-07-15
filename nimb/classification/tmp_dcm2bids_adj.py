#!/bin/python
import os, shutil, json, time, sys, logging, argparse
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(module)s %(levelname)s: %(message)s')
logger.setLevel(logging.INFO)



class DCM2BIDS_helper():

    def __init__(self, params,
                repeat_lim = 2):

        self.run_stt         = 0
        self.repeat_lim      = repeat_lim
        self.repeat_updating = 0
        self.OUTPUT_DIR      = params.dir
        self.ses             = 'ses-01'
        self.bids_id         = params.id
        self.project         = params.project
        self.abs_path2mr     = params.abspathmr
        self.config_file     = self.get_config_file()

    def run(self, bids_id = 'none', ses = 'none'):
        self.sub_SUBJDIR = os.path.join(self.OUTPUT_DIR, 'tmp_dcm2bids', f'sub-{self.bids_id}_{self.ses}')
        self.BIDS_type = "anat"
        self.mr_modality = "t1"
#        self.run_dcm2bids(self.abs_path2mr)
        self.chk_if_processed()


    def update_config(self):
        """....."""
        self.add_criterion = False
        self.config   = load_json(self.config_file)
        data_Type     = self.BIDS_type
        modality      = mr_modality_nimb_2_dcm2bids[self.mr_modality]
        criterion1    = 'SeriesDescription'
        sidecar_crit1 = self.sidecar_content[criterion1]

        self.config = load_json(self.config_file)
        list_criteria = list()
        for des in self.config['descriptions']:
            if des['dataType'] == data_Type and \
                des["modalityLabel"] == modality:
                list_criteria.append(des)
        if len(list_criteria) > 0:
            print('    there is at least one configuration with dataType: ', data_Type)
            for des in list_criteria[::-1]:
                if criterion1 in des['criteria']:
                    if des['criteria'][criterion1] == sidecar_crit1:
                        print('        sidecar is present in the config file. Add another sidecar criterion in the dcm2bids_helper.py script')
                        self.add_criterion = True
                        sys.exit(0)
                    else:
                        list_criteria.remove(des)
        if len(list_criteria) > 0:
            print('    cannot find a correct sidecar location. Please add more parameters.')
        if len(list_criteria) == 0 and 'MPRAGE' in sidecar_crit1: # !!!!!!!!!!!!!!!!!!!to rm MPRAGE condition
            print ("    updating config with value: ", sidecar_crit1)
            new_des = {
               'dataType': data_Type,
               'modalityLabel' : modality,
               'criteria':{criterion1:  sidecar_crit1}}
            self.config['descriptions'].append(new_des)
            self.update = True

        if self.update:
            self.run_stt = 0
            save_json(self.config, self.config_file)
        else:
           print('criterion {} present in config file'.format(criterion1))


    def chk_if_processed(self):
        print("*********Convert remaining folder",self.sub_SUBJDIR)
        ls_niigz_files = [i for i in os.listdir(self.sub_SUBJDIR) if '.nii.gz' in i]
        if ls_niigz_files:
            print("        remaining nii in ", self.sub_SUBJDIR)
            if self.repeat_updating < self.repeat_lim:
                self.update = False
                for niigz_f in ls_niigz_files:
                    f_name = niigz_f.replace('.nii.gz','')
                    sidecar = f'{f_name}.json'
                    self.sidecar_content = load_json(os.path.join(self.sub_SUBJDIR, sidecar))
                    self.update_config()
                if self.update:
                    print('        removing folder tmp_dcm2bids/sub')
                    self.repeat_updating += 1
                    self.rm_dir(self.sub_SUBJDIR)
                    print('    re-renning dcm2bids')
                    self.run_dcm2bids(self.abs_path2mr)
                    #self.run(self.SUBJ_NAME)
        else:
            print("        case2")
#            self.rm_dir(self.sub_SUBJDIR)


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


    def rm_dir(self, DIR):
        os.system('rm -r {}'.format(DIR))


    def get_config_file(self):
        config_file = os.path.join(self.OUTPUT_DIR,
                             'dcm2bids_config_{}.json'.format(self.project))
        if os.path.exists(config_file):
            print("        Config file: ",config_file)
            return config_file
        else:
            print('config file is missing')

#    def run_helper(self):
#        """SCRIPT is probably not required"""
#        helper_dir = os.path.join(self.OUTPUT_DIR, 'tmp_dcm2bids', 'helper')
#        os.system('dcm2bids_helper -d {} -o {}'.format(self.DICOM_DIR, self.OUTPUT_DIR))
#        # read the .json file and add parameters in the config file
#        self.sidecar_content = open(os.path.join(helper_dir,
#                      [i for i in os.listdir(os.path.join()) if '.json' in i][0]), 'r').readlines()
#        return self.sidecar_content



def get_parameters():
    """get parameters for nimb"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Documentation at https://github.com/alexhanganu/nimb
            """,
    )

    parser.add_argument(
        "-dir", required=False,
    )

    parser.add_argument(
        "-id", required=False,
    )

    parser.add_argument(
        "-project", required=False,
    )

    parser.add_argument(
        "-abspathmr", required=False,
    )

    params = parser.parse_args()
    return params


if __name__ == "__main__":
    from pathlib import Path
    top = Path(__file__).resolve().parents[1]
    sys.path.append(str(top))
    from classification.classify_definitions import BIDS_types, mr_modalities, mr_modality_nimb_2_dcm2bids
    from distribution.utilities import makedir_ifnot_exist, load_json, save_json
    from distribution.distribution_definitions import DEFAULT

    params      = get_parameters()
    DCM2BIDS_helper(params, repeat_lim = 10).run()



