#!/bin/python
import os, shutil, json, time, sys, logging, argparse
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(module)s %(levelname)s: %(message)s')
logger.setLevel(logging.INFO)



class DCM2BIDS_tester():
    """
    tester for dcm2bids_helper.py
    goal: use UNFMontreal/dcm2bids to convert .dcm files to BIDS .nii.gz
    args: DICOM_DIR with the subjects with .dcm files that need to be converted
    args: OUTPUT_DIR - DIR where the BIDS structure will be created
    algo: (1) convert (run()), (2) check if any unconverted (chk_if_processed()),
          (3) if not converted, try to create the config file (update_config())
          (4) redo run() up to repeat_lim
    """
    def __init__(self, params,
                repeat_lim = 2):

        self.proj_vars       = dict()
        self.project         = params.project
        self.id_classified   = dict()
        self.run_stt         = 0
        self.repeat_lim      = int(repeat_lim)
        self.repeat_updating = 0
        self.DICOM_DIR       = params.src
        self.tmp_dir         = 'none'
        self.OUTPUT_DIR      = makedir_ifnot_exist(params.o)
        self.archived        = False

    def run(self, nimb_id = 'none', ses = 'none'):
        #run dcm2bids:
        '''
            if nimb_classified.json[nimb_id][archived]:
                extract from archive specific subject_session
                start dcm2bids for subject_session
        '''
        print(f'        folder with subjects is: {self.DICOM_DIR}')
        self.nimb_id = nimb_id
        self.ses     = ses
        self.bids_id = f'sub-{self.nimb_id}_{self.ses}'
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
            self.nimb_ids = list(self.nimb_classified.keys())
            for self.nimb_id in self.nimb_ids:
                self.id_classified = self.nimb_classified[self.nimb_id]
                for self.ses in [i for i in self.id_classified if i not in ('archived',)]:
                    self.start_stepwise_choice()
        if nimb_id != 'none':
            return self.bids_id
        else:
            return 'none'


    def start_stepwise_choice(self):
        print(f'\n\n        classifying for id: {self.bids_id}')
        if self.id_classified['archived']:
            self.archived = True
        for self.data_Type in BIDS_types:
            if self.data_Type in self.id_classified[self.ses]:
                for modalityLabel in BIDS_types[self.data_Type]:
                    if modalityLabel in self.id_classified[self.ses][self.data_Type]:
                        paths_2mr_data = self.id_classified[self.ses][self.data_Type][modalityLabel]
                        self.modalityLabel = mr_modality_nimb_2_dcm2bids[modalityLabel] # changing to dcm2bids type modality_label
                        if len(paths_2mr_data) > 1:
                            print(f'    NOTE: there are more than 1 MRI of type: {self.modalityLabel} in the source folder.')
                            print(f'        dcm2bids CANNOT save multiple versions of the same MR type in the same session.')
                            print(f'        ONLY the first MR version will be used')
                        path2mr_ = paths_2mr_data[0]
                        print(f'        converting mr type: {self.data_Type}')
                        self.abs_path2mr = self.get_path_2mr(path2mr_)
                        self.sub_SUBJDIR = os.path.join(self.OUTPUT_DIR, 'tmp_dcm2bids', self.bids_id)
                        self.run_dcm2bids()
                        if os.path.exists(self.sub_SUBJDIR) and \
                            len(os.listdir(self.sub_SUBJDIR)) > 0:
                            print('    conversion did not find corresponding values in the configuration file')
                            print("        temporary converted subject located in:", self.sub_SUBJDIR)
                            self.chk_if_processed()
                        else:
                            print('    dcm2bids conversion DONE')


    def run_dcm2bids(self):
        if self.run_stt == 0:
            self.config_file = self.get_config_file()
            return_value = os.system('dcm2bids -d {} -p {} -s {} -c {} -o {}'.format(
                                                                                    self.abs_path2mr,
                                                                                    self.nimb_id,
                                                                                    self.ses,
                                                                                    self.config_file,
                                                                                    self.OUTPUT_DIR))
            # Calculate the return value code
            return_value = int(bin(return_value).replace("0b", "").rjust(16, '0')[:8], 2)
            print('return value is: ',return_value)
            if return_value != 0: # failed
                os.system('dcm2bids -d {} -p {} -s {} -c {} -o {}'.format(self.abs_path2mr,
                                                                        self.nimb_id,
                                                                        self.ses,
                                                                        self.config_file,
                                                                        self.OUTPUT_DIR))
            print("/"*40)


    def chk_if_processed(self):
        """Check if any unconverted,
          - if not converted, update config file based on sidecar params (update_config())
          - redo run() up to repeat_lim
        """
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
                    print('        removing folder: ', self.sub_SUBJDIR)
                    self.repeat_updating += 1
                    self.rm_dir(self.sub_SUBJDIR)
                    print('    re-renning dcm2bids')
                    self.run_dcm2bids()
                    print('    looping to another chk_if_processed')
                    self.chk_if_processed()
        else:
            print('    dcm2bids conversion DONE')
            if os.path.exists(self.sub_SUBJDIR):
                self.rm_dir(self.sub_SUBJDIR)


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
            print('    there is at least one configuration with dataType: ', self.data_Type)
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
        if len(list_criteria) == 0:
            print ("        updating config with value: ", sidecar_crit1)
            new_des = {
               'dataType': self.data_Type,
               'modalityLabel' : self.modalityLabel,
               'criteria':{criterion1:  sidecar_crit1}}
            self.config['descriptions'].append(new_des)
            self.update = True

        if self.update:
            self.run_stt = 0
            save_json(self.config, self.config_file)
        else:
           print('criterion {} present in config file'.format(criterion1))


    def get_config_file(self):
        """Get the dcm2bids_config_{project_name}.json.
           If not exist, get dcm2bids_config_default.json
        """
        config_file = os.path.join(self.OUTPUT_DIR,
                             f'dcm2bids_config_{self.project}.json')
        if os.path.exists(config_file):
            print("*"*50)
            print("        config_file is: ", config_file)
            print("*" * 50)
            return config_file
        else:
            shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dcm2bids','dcm2bids_config_default.json'),
                        config_file)
            return config_file


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


    def rm_dir(self, DIR):
        os.system('rm -r {}'.format(DIR))


    def get_SUBJ_DIR(self):
        """Get the path of DICOM_DIR"""
        DICOM_DIR = self.proj_vars['SOURCE_SUBJECTS_DIR'][1]
        if os.path.exists(DICOM_DIR):
            return DICOM_DIR
        else:
            print('    path is invalid: {}'.format(DICOM_DIR))
            return 'PATH_IS_MISSING'


#    def run_helper(self):
#        """SCRIPT is probably not required"""
#        helper_dir = os.path.join(self.OUTPUT_DIR, 'tmp_dcm2bids', 'helper')
#        os.system('dcm2bids_helper -d {} -o {}'.format(self.DICOM_DIR, self.OUTPUT_DIR))
#        # read the .json file and add parameters in the config file
#        self.sidecar_content = open(os.path.join(helper_dir,
#                      [i for i in os.listdir(os.path.join()) if '.json' in i][0]), 'r').readlines()
#        return self.sidecar_content


    # def validate_bids(self):
    #     print("test validate_bids")
    #     # https://github.com/bids-standard/bids-validator
    #     return True


def get_parameters():
    """get parameters for nimb"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Documentation at https://github.com/alexhanganu/nimb
            """,
    )

    parser.add_argument(
        "-src", required=True,
        help="absolute path to MR data to be classified",
    )

    parser.add_argument(
        "-o", required=True,
        help="output folder of bids classified files",
    )

    parser.add_argument(
        "-project", required=True,
    )

    parser.add_argument(
        "-rep", required=False,
        default=5,
        help="number of repetitions to use to retry the dcm2bids classification, default is 5",
    )

    params = parser.parse_args()
    return params


if __name__ == "__main__":
    from pathlib import Path
    top = Path(__file__).resolve().parents[1]
    sys.path.append(str(top))
    from classification.classify_definitions import BIDS_types, mr_modalities, mr_modality_nimb_2_dcm2bids
    from distribution.manage_archive import is_archive, ZipArchiveManagement
    from distribution.utilities import makedir_ifnot_exist, load_json, save_json
    from distribution.distribution_definitions import DEFAULT

    params      = get_parameters()
    DCM2BIDS_tester(params, repeat_lim = params.rep).run()



