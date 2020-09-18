'''
ttest analysis
'''

from stats import db_processing
from .stats_definitions import get_structure_measurement, get_names_of_measurements, get_names_of_structures
import pandas as pd
import numpy as np
from scipy import stats
from os import path


class ttest_do():
    def __init__(self, df, group_col, ls_cols, groups, path_save_res, p_thresh = 0.05):
        self.df = df
        self.group_col = group_col
        self.ls_cols = ls_cols
        self.groups = groups
        self.path_save_res = path_save_res
        self.ls_meas = get_names_of_measurements()
        self.ls_struct = get_names_of_structures()
        self.res_ttest = self.compute_ttest_for_col(p_thresh)

    def compute_ttest_for_col(self, p_thresh):
        res_4df = {'features':[], 'ttest':[], 'welch':[]}
        res = dict()
        for col in self.ls_cols:
            group1 = self.df[self.df[self.group_col] == self.groups[0]][col]
            group2 = self.df[self.df[self.group_col] == self.groups[1]][col]
            ttest_eq_pop_var = stats.ttest_ind(group1, group2, equal_var=True)
            ttest_welch = stats.ttest_ind(group1, group2, equal_var=False)
            if ttest_eq_pop_var[1] < p_thresh:
                meas, struct = get_structure_measurement(col, self.ls_meas, self.ls_struct)
                #print('{:<15} {}'.format(meas, struct))
                res[col] = {'ttest':ttest_eq_pop_var[1],'welch':ttest_welch[1]}
                res_4df['features'].append(struct+' ('+meas+')')
                res_4df['ttest'].append(ttest_eq_pop_var[1])
                res_4df['welch'].append(ttest_welch[1])
        self.save_res(res_4df)
        return res

    def save_res(self, res_4df):
        df_result = db_processing.create_df_from_dict(res_4df)
        df_result.to_csv(path.join(self.path_save_res,'ttest.csv'))
