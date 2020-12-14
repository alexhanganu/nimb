'''
check that all subjects are present in the FS_SUBJECTS_DIR folder
in order to perform the FreeSurfer glm
'''

from os import listdir, path
import sys
import json

try:
    import pandas as pd
    import xlrd
except ImportError as e:
    sys.exit(e)


class CheckIfReady4GLM():

    def __init__(self, nimb_vars, fs_vars, proj_vars, f_ids_processed, f_GLM_group):
        self.proj_vars         = proj_vars
        self.vars_fs           = fs_vars
        self.FS_SUBJECTS_DIR   = fs_vars['FS_SUBJECTS_DIR']
        self.NIMB_PROCESSED_FS = nimb_vars["NIMB_PROCESSED_FS"]
        self.f_ids_processed   = f_ids_processed
        self.f_GLM_group       = f_GLM_group

    def chk_if_subjects_ready(self):
        self.miss = {}
        self.ids = self.get_ids_processed()
        for _id in self.ids:
            self.define_subjects_path(_id)
        if self.miss.keys():
            ids_ok = {i:self.ids[i] for i in self.ids if i not in self.miss.keys()}
            print('{} subjects are missing and {} are present in the processing folder'.format(len(self.miss.keys()), len(ids_ok.keys())))
            return list(self.miss.keys())
        else:
            return list()

    def chk_path(self, path2chk, _id):
        '''FS GLM requires two folders: surf and label
            scripts checks that both folders are present
            checks that all GLM files are present
        Args:
            path2chk: path to the folder with the subject
            _id: ID of the subject to chk
        Return:
            populates list of missing subjects
        '''
        if path.exists(path.join(path2chk, 'surf')) and path.exists(path.join(path2chk, 'label')):
            for hemi in ['lh','rh']:
                for meas in self.vars_fs["GLM_measurements"]:
                    for thresh in self.vars_fs["GLM_thresholds"]:
                        file = '{}.{}.fwhm{}.fsaverage.mgh'.format(hemi, meas, str(thresh))
                        if not path.exists(path.join(path2chk, 'surf', file)):
                            print('    id {} misses file {}'.format(_id, file))
                            self.add_to_miss(_id, file)
        else:
            self.add_to_miss(_id, 'surf label missing')
        if _id not in self.miss:
            return True
        else:
            return False

    def define_subjects_path(self, _id):
        '''it is expected that the BIDS IDs after processing are located in one of the two folders
            script defines the the folder for analysis
            checks if subjects are present
        Args:
            _id: ID of the subject to chk
        Return:
            populates list of missing subjects
            populates dict with ids
            Folder with Subjects for GLM analysis
        '''
        self.defined_path = list()
        path_id_processed = ''
        for path_subjs in [self.FS_SUBJECTS_DIR, self.NIMB_PROCESSED_FS]:
            path2chk = path.join(path_subjs, _id)
            if path.exists(path2chk):
                path_id_processed = path2chk
                break
        if path_id_processed:
            if self.chk_path(path_id_processed, _id):
                self.defined_path.append(path_id_processed)
                self.ids[_id] = path_id_processed
        else:
            print('id is missing {}'.format(_id))
            self.add_to_miss(_id, 'id_missing')
        path2use = max(self.defined_path, key = self.defined_path.count)
        self.create_glm_df([i for i in self.ids if path2use in self.ids[i]])

    def create_glm_df(ls_ids):
        ls_ix_2rm = list()
        self.df['fs_id'] = ''
        for ix in self.df.index:
            src_id = self.df.at[ix, self.proj_vars['id_col']]
            bids_id = [i for i in self.ids_all if self.ids_all[i]['source'] == src_id][0]
            self.df.at[ix, 'fs_id'] = bids_id
            if bids_id not in ls_ids:
                ls_ix_2rm.append(ix)
        self.df_new = self.df.drop(ls_ix_2rm)
        self.df_new.drop(columns=[self.proj_vars['id_col']], inplace=True)
        self.df.rename(columns={'fs_id': self.proj_vars['id_col']}, inplace=True)
        self.df_new.to_excel(self.f_GLM_group)

    def get_ids_processed(self):
        '''retrieves the bids names of the IDs provided in the GLM file.
            It is expected that each project had a group of subjects that are present in the dataset
            the f_ids.json has the BIDS names of the subjects, the source names and the freesurfer/nilearn/dipy names
            see nimb/example/f_ids.json
        '''
        self.ids_all = self.read_json(self.f_ids_processed)
        self.df = self.get_df()
        ids_glm_file = self.df[self.proj_vars['id_col']].tolist()
        return {i: 'path' for i in self.ids_all if self.ids_all[i]['source'] in ids_glm_file}


    def add_to_miss(self, _id, file):
        '''add to the list of missing subjects
        '''
        if _id not in self.miss:
            self.miss[_id] = list()
        self.miss[_id].append(file)

    def read_json(self, f):
        '''read a json file
        '''
        with open(f, 'r') as jf:
            return json.load(jf)

    def get_df(self):
        '''reads a csv or an xlsx file
        '''
        if '.csv' in self.f_GLM_group:
            return pd.read_csv(self.f_GLM_group)
        elif '.xlsx' in self.f_GLM_group or '.xls' in self.f_GLM_group:
            return pd.read_excel(self.f_GLM_group)
