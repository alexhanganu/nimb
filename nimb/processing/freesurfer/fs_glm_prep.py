'''
check that all subjects are present in the FS_SUBJECTS_DIR folder
in order to perform the FreeSurfer glm
'''

from os import listdir
import sys

from fs_definitions import GLMVars

try:
    import pandas as pd
    import xlrd
except ImportError as e:
    sys.exit(e)


class CheckIfReady4GLM():

    def __init__(self, proj_vars, vars_fs):
        self.glm_vars = GLMVars(proj_vars)
        self.vars_fs  = vars_fs
        self.id_col   = proj_vars['id_col']

        self.miss = self.chk_if_subjects_ready()

    def get_ids_processed(self):
        f_ids_processed = self.glm_vars.f_ids_processed()
        if path.exists(f_ids_processed):
            content = self.read_json(f_ids_processed)
            return {i:conten[i]['processed'] for i in content}
        else:
            print('getting ids from user-provided GLM file group')
            # df_groups_clin = self.get_df_for_variables(GLM_file_group, variables)
            # self.ids = self.get_ids_ready4glm(df_groups_clin[self.id_col].tolist(), vars_fs)
            # d_init = df_groups_clin.to_dict()
            # self.d_subjid = {}

    def chk_if_subjects_ready(self):
        ids_processed = self.get_ids_processed()
        self.miss = {}
        for sub in ids_processed:
            if subject not in listdir(self.vars_fs['FS_SUBJECTS_DIR']):
                self.miss[sub] = ids_processed[sub]
        return self.miss

    def read_json(f):
        with open(f, 'r') as jf:
            return json.load(jf)

