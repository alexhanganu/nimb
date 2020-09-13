'''
ttest analysis
'''

from .stats_definitions import get_structure_measurement, get_names_of_measurements, get_names_of_structures
import pandas as pd
import numpy as np
from scipy import stats
from os import path


class ttest_do():
    def __init__(self, df, group_col, ls_cols, p_thresh = 0.05)
        self.df = df
        self.group_col = group_col
        self.ls_cols = ls_cols
        res_ttest = self.compute_ttest_for_col()

    def compute_ttest_for_col(self):
        res_ttest = {}
        for col in self.ls_cols:
            group1 = df[df[self.group_col] == group1][col]
            group2 = df[df[self.group_col] == group2][col]
            ttest_eq_pop_var = stats.ttest_ind(group1, group2, equal_var=True)
            ttest_welch = stats.ttest_ind(group1, group2, equal_var=False)
            if ttest_eq_pop_var[1] < p_thresh:
                res_ttest[col] = []
                res_ttest[col].append(ttest_eq_pop_var[1])
                res_ttest[col].append(ttest_welch[1])
        return res_ttest
