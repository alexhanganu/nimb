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

    def __init__(self, proj_vars, local_vars, f_GLM_group=False):
        self.proj_vars         = proj_vars
        self.FS_SUBJECTS_DIR   = local_vars['FREESURFER']['FS_SUBJECTS_DIR']
        self.NIMB_PROCESSED_FS = local_vars["NIMB_PATHS"]["NIMB_PROCESSED_FS"]
        self.vars_fs           = local_vars['FREESURFER']
        self.f_GLM_group       = f_GLM_group

    def get_ids_processed(self):
        if self.proj_vars['materials_DIR'][0] == 'local':
            from .fs_definitions import GLMVars
            f_ids_processed = GLMVars(proj_vars).f_ids_processed()    
            if path.exists(f_ids_processed):
                content = self.read_json(f_ids_processed)
                return {i:content[i]['processed'] for i in content}
        elif self.f_GLM_group:
            print('getting ids from user-provided GLM file group')
            df = self.get_df()
            return {i: 'none' for i in df[self.proj_vars['id_col']].tolist()}
        else:
            print('ERROR: cannot find a source for subjects IDs')

    def chk_if_subjects_ready(self):
        self.miss = {}
        self.ids = self.get_ids_processed()
        for _id in self.ids:
            if self.ids[_id] != 'none':
                self.chk_path(self.ids[_id], _id)
            else:
                self.add_path(_id)
        if self.miss.keys():
            print('some subjects or files are missing: {}'.format(self.miss))
        return {i:self.ids[i] for i in self.ids if i not in self.miss.keys()}, list(self.miss.keys())

    def chk_path(self, path2chk, _id):
        if path.exists(path.join(path2chk, 'surf')) and path.exists(path.join(path2chk, 'label')):
            for hemi in ['lh','rh']:
                for meas in self.vars_fs["GLM_measurements"]:
                    for thresh in self.vars_fs["GLM_thresholds"]:
                        file = '{}.{}.fwhm{}.fsaverage.mgh'.format(hemi, meas, str(thresh))
                        if not path.exists(path.join(path2chk, 'surf', file)):
                            self.add_to_miss(_id, file)
        else:
            self.add_to_miss(_id, 'none')

    def add_path(self, _id):
        for path_subjs in [self.FS_SUBJECTS_DIR, self.NIMB_PROCESSED_FS]:
            path2chk = path.join(path_subjs, _id)
            self.chk_path(path2chk, _id)
            if _id not in self.miss:
                self.ids[_id] = path2chk

    def add_to_miss(self, _id, file):
        if _id not in self.miss:
            self.miss[_id] = list()
        self.miss[_id].append(file)

    def read_json(self, f):
        with open(f, 'r') as jf:
            return json.load(jf)

    def get_df(self):
        if '.csv' in self.f_GLM_group:
            return pd.read_csv(self.f_GLM_group)
        elif '.xlsx' in self.f_GLM_group or '.xls' in self.f_GLM_group:
            return pd.read_excel(self.f_GLM_group)
