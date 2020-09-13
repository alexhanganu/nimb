'''
Analysis of Variance models containing anova_lm for ANOVA analysis with a linear OLSModel,
and AnovaRM for repeated measures ANOVA, within ANOVA for balanced data.

    Interpreting statsmodels summary: model.summary()
    Adjusted. R-squared reflects the fit of the model. R-squared values range from 0 to 1, where a higher value generally indicates a better fit, assuming certain conditions are met.
    Y-intercept. means that if both the Interest_Rate and Unemployment_Rate coefficients are zero, then the expected output (i.e., the Y) would be equal to the const coefficient.
    x coefficient represents the change in the output Y due to a change of one unit in the x (everything else held constant)
    std err reflects the level of accuracy of the coefficients. The lower it is, the higher is the level of accuracy
    P >|t| is your p-value. A p-value of less than 0.05 is considered to be statistically significant
    Confidence Interval represents the range in which our coefficients are likely to fall (with a likelihood of 95%)

code source: https://www.statsmodels.org/stable/anova.html
code exmpl:
In [1]: import statsmodels.api as sm
In [2]: from statsmodels.formula.api import ols

In [3]: moore = sm.datasets.get_rdataset("Moore", "carData", cache=True) # load data
In [4]: data = moore.data
In [5]: data = data.rename(columns={"partner.status": "partner_status"}) # make name pythonic

In [6]: moore_lm = ols('conformity ~ C(fcategory, Sum)*C(partner_status, Sum)', data=data).fit()
In [7]: table = sm.stats.anova_lm(moore_lm, typ=2) # Type 2 ANOVA DataFrame
In [8]: print(table)

https://www.statsmodels.org/stable/generated/statsmodels.stats.anova.AnovaRM.html#statsmodels.stats.anova.AnovaRM
Repeated measures Anova using least squares regression
The full model regression residual sum of squares is used to compare with the reduced model for calculating the within-subject effect sum of squares [1].
Currently, only fully balanced within-subject designs are supported. Calculation of between-subject effects and corrections for violation of sphericity are not yet implemented.
'''

from .stats_definitions import get_structure_measurement, get_names_of_measurements, get_names_of_structures
import pandas as pd
import numpy as np
from statsmodels.formula.api import ols# For statistics, statsmodels =>5.0
from os import path


class ANOVA_do():
    def __init__(self, df, params_y, ls_cols4anova, path2save, p_thresh = 0.05, intercept_thresh = 0.05):
        self.ls_meas = get_names_of_measurements()
        self.ls_struct = get_names_of_structures()
        self.df = df
        self.params_y = params_y
        self.ls_cols4anova = ls_cols4anova
        self.sig_cols = dict()

    def run_anova(self):
        for param_y in self.params_y:
            self.sig_cols[param_y] = dict()
            x = np.array(self.df[param_y])
            df_result = self.get_new_df(param_y)
            df_result_list = self.get_new_df(param_y)
            ix = 1
            ixx = 1
            for col in self.ls_cols4anova:
                print(col, '    left to analyse:',len(self.ls_cols4anova[self.ls_cols4anova.index(col):]),'\n')
                y = np.array(df[col])
                data_tmp = pd.DataFrame({'x':x,col:y})
                model = ols(col+" ~ x", data_tmp).fit()
                if model.pvalues.Intercept < p_thresh and model.pvalues.x < intercept_thresh:
                    measurement, structure = get_structure_measurement(col, self.ls_meas, self.ls_struct)
                    self.sig_cols[param_y][col] = model
                    df_result_list = self.populate_df(df_result_list, ixx, {param_y: structure, 'measure': measurement, 'pvalue': '%.4f'%model.pvalues.x})
                    if structure not in df_result[param_y].tolist():
                        df_result = self.populate_df(df_result, ix, {param_y: structure, measurement: '%.4f'%model.pvalues.x})
                        ix += 1
                    else:
                        df_result = self.populate_df(df_result, df_result[param_y].tolist().index(structure), {measurement: '%.4f'%model.pvalues.x})
                    ixx += 1
        self.save_df(self, df_result_list, path.join(self.path2save, 'anova_per_significance_'+param_y+'.csv'))
        self.save_df(self, df_result, path.join(self.path2save, 'anova_per_structure_'+param_y+'.csv'))

    def populate_df(self, df, idx, cols_vals):
        for col in cols_vals:
            df.at[idx, col] = cols_vals[col]
        return df

    def save_results(self, df, path2save):
        df.to_csv(path2save)

    #res_ttest_sig = self.compute_ttest_for_col(col)

    def compute_ttest_for_col(self, col):
        from scipy import stats
        sig = False
        res_ttest_sig = {}
        group1 = data_groups_anova[data_groups_anova['Groupe'] == group1][col]
        group2 = data_groups_anova[data_groups_anova['Groupe'] == group2][col]
        ttest_eq_pop_var = stats.ttest_ind(group1, group2, equal_var=True)
        #ttest_welch = stats.ttest_ind(group1, group2, equal_var=False)
        if ttest_eq_pop_var[1] < 0.05:
            #res_ttest_sig[col] = []
            #res_ttest_sig[col].append(ttest_eq_pop_var[1])
            #res_ttest_sig[col].append(ttest_welch[1])
            sig = True
        return sig
