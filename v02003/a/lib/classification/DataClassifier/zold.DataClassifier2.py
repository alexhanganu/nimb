import os
import glob
import pandas
import math
import csv
# import json

'''
predefined:
address of the DCM_folder (where dcm files are present)
address of the folder with results
Main_File = address of the main file with data (may have the with extension “_tp1”)
Longitudinal-TP-names = user defined (e.g., ‘tp’+INT)	
'''

'''
2do:
change name 'baseline' to 'tp0'

'''

DCM_path = 'C:/Users/Jessica/Documents/s2019-NPS-db/freesurfer_nacc/raw/'
Data_path = 'Data'
Long_tp = 'tp'
Main_tp_file = 'tp1_mri_files_classified.csv'

batch_file_header = ('#!/bin/sh', '#SBATCH --time=150:00:00', '#SBATCH --account=def-hanganua')


class DataClassifier:
    # def __init__(self, DCM_path, Data_path, Main_file, Long_tp):
    def __init__(self):
        self.Classification_dict = {}
        self.DCM_path = DCM_path
        self.Data_path = Data_path
        self.Main_File = Main_tp_file
        self.Long_tp = Long_tp

    def run(self):
        count = 1
        subjects_id = {}

        os.chdir(self.Data_path)

        # access the Main_File
        main_data = pandas.read_csv(self.Main_File, index_col=0)

        # extract column 'id'
        main_indexs = main_data.index[:5]

        # extract each id from the main file
        for _id in main_indexs:
            # extract name of t1/flair/t2 for _id in MAIN_FILE
            main_idx_value = main_data.loc[_id]

            # create structure for baseline
            sub_id = _id
            subjects_id[_id] = sub_id
            count += 1
            self.Classification_dict[sub_id] = {'anat': {'tp0': {}}}

            self.send_to_dictionnary(sub_id, 'tp0', main_idx_value)

        # check if there are additional tp files
        additional_tps = sorted([f for f in glob.glob(self.Long_tp + '*', recursive=True) if f != self.Main_File])
        if len(additional_tps):
            for tp in additional_tps:

                data = pandas.read_csv(tp, index_col=0)
                data_indexs = data.index

                for _id in main_indexs:

                    # if main_id in list of id’s for the tp file
                    if _id in data_indexs:

                        # extract the name of t1/flair/t2 for _id in that specific tp
                        tp_idx_value = data.loc[_id]

                        tp_label = 'tp' + str(len(self.Classification_dict[subjects_id[_id]]['anat']))

                        self.Classification_dict[subjects_id[_id]]['anat'][tp_label] = {}

                        self.send_to_dictionnary(subjects_id[_id], tp_label, tp_idx_value)

        # with open('Classification_dict.json', 'w') as f:  # writing JSON object
        #     json.dump(self.Classification_dict, f, indent=4)

        for _id, value in self.Classification_dict.items():
            if len(value['anat']) > 1:
                for tp_id, tp in value['anat'].items():
                    subj_id = _id + '_' + tp_id
                    stage = 'cross_analysis'
                    method = 'long'
                    if tp['flair']:
                        cmd = 'recon-all -i ' + tp['t1'] + ' -FLAIR' + tp['flair'] + ' -subjid ' + subj_id
                    else:
                        cmd = 'recon-all -i ' + tp['t1'] + ' -subjid ' + subj_id

                    # self.make_batch_file(cmd)
                    self.send_to_running_log(_id, subj_id, stage, method)

            else:
                tp = value['anat']['tp0']
                subj_id = _id + '_tp0'
                stage = 'cross_analysis'
                method = 'cross'

                if tp['flair']:
                    cmd = 'recon-all -i ' + tp['t1'] + ' -FLAIR' + tp['flair'] + ' -subjid ' + _id + '_tp0'
                else:
                    cmd = 'recon-all -i ' + tp['t1'] + ' -subjid ' + _id + '_tp0'

                # self.make_batch_file(cmd)
                self.send_to_running_log(_id, subj_id, stage, method)

    @staticmethod
    def make_batch_file(cmd):
        with open('batchfile.sh', 'w') as f:
            for line in batch_file_header:
                f.write(line + '\n')
            f.write('cd some folder' + '\n')
            f.write(cmd)
    #   save file to folder (batches)

    @staticmethod
    def send_to_running_log(_id, subj_id, stage, method):
        # file format: id / subjid / stage / method
        if not os.path.exists('logs.csv'):
            first_line = ["id", "subj_id", 'stage', "method"]
            with open('logs.csv', 'w', newline='') as f:
                wr = csv.writer(f, quoting=csv.QUOTE_ALL)
                wr.writerow(first_line)

        new_line = [_id, subj_id, stage, method]

        with open('logs.csv', 'a') as f:
            wr = csv.writer(f, quoting=csv.QUOTE_ALL)
            wr.writerow(new_line)

    def send_to_dictionnary(self, _id, tp_label, obj):

        tp_obj = {'t1': '', 'flair': '', 't2': ''}

        for attr, value in tp_obj.items():
            # for each file(t1 / flair / t2):
            if hasattr(obj, attr):
                if type(obj[attr]).__name__ != 'float' or not math.isnan(obj[attr]):
                    # check_if_file_is_present
                    path_file = check_if_file_is_present(obj[attr], DCM_path)
                    tp_obj[attr] = path_file

        self.Classification_dict[_id]['anat'][tp_label] = tp_obj


def check_if_file_is_present(_dir, path):
    if os.path.isdir(path+_dir):
        file_names = os.listdir(path + _dir)
        if len([f for f in file_names if f.endswith('.dcm')]):
            if len(file_names) > 15:
                return path + _dir + '/' + sorted(file_names)[0]
        else:
            print('ERROR: No dcm files in the folder: ', _dir)
    elif os.path.isfile(path+_dir):
        if _dir.endswith('.nii'):
            return path + _dir
    return ''
