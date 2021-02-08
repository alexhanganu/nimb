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
# check that "results per structure" have the same structures as in the "results" file
#http://hamelg.blogspot.com/2015/11/python-for-data-analysis-part-16_23.html

# last update: 2020-09-14
# linear regression on 2 variables (moderation analysis): Lynn Valeyry Verty, Alex Hanganu

from os import path
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import ols
from sklearn.linear_model import LinearRegression
from distribution.utilities import save_json
from stats.db_processing import Table
from processing.freesurfer.fs_definitions import GetFSStructureMeasurement


class ANOVA_do():
    def __init__(self, df, params_y, ls_cols4anova, path2save,
                p_thresh = 0.05, intercept_thresh = 0.05,
                print_not_FS = False):
        self.df            = df
        self.params_y      = params_y
        self.ls_cols4anova = ls_cols4anova
        self.sig_cols      = dict()
        self.tab           = Table()
        self.fs_struc_meas = GetFSStructureMeasurement()
        self.run_anova(p_thresh, intercept_thresh, path2save)

    def run_anova(self, p_thresh, intercept_thresh, path2save):
        ls_err = list()
        for param_y in self.params_y:
            x = np.array(self.df[param_y])
            df_result = self.tab.get_clean_df()
            df_result_list = df_result.copy()
            df_result[param_y] = ''
            df_result_list[param_y] = ''
            ix = 1
            ixx = 1
            # print(f'    analysing {len(self.ls_cols4anova)} features for parameter: {param_y}')
            for col in self.ls_cols4anova:
                y = np.array(self.df[col])
                data_tmp = pd.DataFrame({'x':x,col:y})
                model = ols(col+" ~ x", data_tmp).fit()
                if model.pvalues.Intercept < p_thresh and model.pvalues.x < intercept_thresh:
                    measurement, structure, ls_err = self.fs_struc_meas.get(col, ls_err)
                    if param_y not in self.sig_cols:
                        self.sig_cols[param_y] = dict()
                    self.sig_cols[param_y][col] = {'pvalues':model.pvalues.x, 'intercept': model.pvalues.Intercept, 'meas': measurement, 'struct': structure}
                    df_result_list = self.populate_df(df_result_list, ixx, {param_y: structure, 'measure': measurement, 'pvalue': '%.4f'%model.pvalues.x})
                    if structure not in df_result[param_y].tolist():
                        df_result = self.populate_df(df_result, ix, {param_y: structure, measurement: '%.4f'%model.pvalues.x})
                        ix += 1
                    else:
                        df_result = self.populate_df(df_result, df_result[param_y].tolist().index(structure), {measurement: '%.4f'%model.pvalues.x})
                    ixx += 1
            self.tab.save_df_tocsv(df_result_list, path.join(path2save, f'anova_per_significance_{param_y}.csv'))
            self.tab.save_df_tocsv(df_result, path.join(path2save, f'anova_per_structure_{param_y}.csv'))
        save_json(self.sig_cols, path.join(path2save, f'anova_significant_features.json'))
        if print_not_FS:
            print('NOT freesurfer structures: ', ls_err)

    def populate_df(self, df, idx, cols_vals):
        for col in cols_vals:
            df.at[idx, col] = cols_vals[col]
        return df


def get_main_dict(group_param, regression_param):
    d = {}
    for i in ('R2_adjusted'+'_'+group_param+'_'+regression_param,
              'p_'+group_param,'p_'+regression_param,
              'B_'+group_param,'B_'+regression_param,
              'Intercept'):
        d[i] =[]
    return d

def compute_linreg_data(df, ls_cols_X, group_param, regression_param):
    d1 = get_main_dict(group_param, regression_param)
    d1['Region'] = ls_cols_X
    X = df[[group_param, regression_param]]
    X = sm.add_constant(X.to_numpy())

    for region in ls_cols_X:
        y = df[[region]]
        model = sm.OLS(y, X).fit()
        reg = LinearRegression().fit(X, y)
        #predictions = model.predict(X)
        #d1['R-deux'].append(model.rsquared)
        d1['R2_adjusted'+'_'+group_param+'_'+regression_param].append(model.rsquared_adj)
        d1['p_'+group_param].append(model.pvalues.x1)
        d1['p_'+regression_param].append(model.pvalues.x2)
        d1['B_'+group_param].append((reg.coef_[0])[1])
        d1['B_'+regression_param].append((reg.coef_[0])[2])
        d1['Intercept'].append(reg.intercept_[0])
    return d1

def linreg_moderation_results(df_X_linreg, ls_cols_X_atlas, group_param, regression_param,
                              path_dir_save_results, group):
    d_result = compute_linreg_data(df_X_linreg,
                                   ls_cols_X_atlas,
                                   group_param,
                                   regression_param)
    df_result = db_processing.create_df_from_dict(d_result)
    db_processing.save_df(df_result, path.join(path_dir_save_results,'linreg_moderation_'+group+'.csv'))


def posthoc_run(model,res,factor,measurement):
    d = {}
    d[measurement] = measurement
    d['Intercept'] = '%.4f'%res.Intercept
    if len(factor)==2:
        d[factor[0]] = '%.4f'%res[0]
        d[factor[1]] = '%.4f'%res[1]
    else:
        d[factor[0]] = '%.4f'%res[1]

    '''Posthoc'''
    if len(factor)==2:
        posthoc10min1 = model.f_test([1,0,-1])
        posthoc1min10 = model.f_test([1,-1,0])
        d['posthoc'] = {}
        d['posthoc']['col_vs_age'] = str('%.4f'%posthoc10min1.pvalue)
        d['posthoc']['col_vs_edu'] = str('%.4f'%posthoc1min10.pvalue)
    else:
        posthoc1min1 = model.f_test([1,-1])
        d['posthoc'] = str('%.4f'%posthoc1min1.pvalue)
    return d



# def RUN_ANOVA_SimpleLinearRegression(data_anova, PARAMETER_x_Age, PARAMETERS_INTEREST_y, ls_struct_cols, PATH2save_anova):
#     Make_Dirs(PATH2save_anova)

#     res_anova_age_struct = {}
#     res_anova_parameter_struct = {}
#     res_anova_parameter_age_struct = {}


#     for col in ls_struct_cols:
#         model_age_struct = ols(formula=col+' ~ '+PARAMETER_x_Age, data=data_anova).fit()
#         res_age_struct = model_age_struct.pvalues
#         if res_age_struct.Intercept<0.05:
#             if res_age_struct.Age<0.05:
#                 measurement, structure = get_structure_measurement(col)
#                 res_anova_age_struct[structure] = Make_Posthoc(model_age_struct,res_age_struct,[PARAMETER_x_Age],measurement) 
#         save_df(res_anova_age_struct, PARAMETER_x_Age, PATH2save_anova)
#         print('DONE for all')

#     for PARAMETER in PARAMETERS_INTEREST_y:
#         for col in ls_struct_cols:
#             model_parameter_struct = ols(formula=col+' ~ '+PARAMETER, data=data_anova).fit()
#             res_parameter_struct = model_parameter_struct.pvalues
#             if res_parameter_struct.Intercept<0.05:
#                 measurement, structure = get_structure_measurement(col)
#                 if PARAMETER == 'education':
#                     if res_parameter_struct.education<0.05:
#                         res_anova_parameter_struct[structure] = Make_Posthoc(model_parameter_struct,res_parameter_struct,[PAR>
#                 elif PARAMETER == 'MOCA':
#                     if res_parameter_struct.MOCA<0.05:
#                         res_anova_parameter_struct[structure] = Make_Posthoc(model_parameter_struct,res_parameter_struct,[PAR>
#                 else:
#                     print('PARAMETER name is:',PARAMETER,'not testing if <0.05')
#                     res_anova_parameter_struct[structure] = Make_Posthoc(model_parameter_struct,res_parameter_struct,[PARAMET>
#             model_parameter_age_struct = ols(formula=col+' ~ '+PARAMETER+' + '+PARAMETER_x_Age, data=data_anova).fit()
#             res_parameter_age_struct = model_parameter_age_struct.pvalues
#             if res_parameter_age_struct.Intercept<0.05:
#                 measurement, structure = get_structure_measurement(col)
#                 if PARAMETER == 'education':
#                     if res_parameter_struct.education<0.05:
#                         res_anova_parameter_age_struct[structure] = Make_Posthoc(model_parameter_age_struct,res_parameter_age>
#                 elif PARAMETER == 'MOCA':
#                     if res_parameter_struct.MOCA<0.05:
#                         res_anova_parameter_struct[structure] = Make_Posthoc(model_parameter_struct,res_parameter_struct,[PAR>
#                 else:
#                     print('PARAMETER name is:',PARAMETER,'not testing if <0.05')
#                     res_anova_parameter_age_struct[structure] = Make_Posthoc(model_parameter_age_struct,res_parameter_age_str>

#         save_df(res_anova_parameter_struct, PARAMETER, PATH2save_anova)
#         save_df(res_anova_parameter_age_struct, PARAMETER+'_'+PARAMETER_x_Age, PATH2save_anova)
#         print('DONE for ',PARAMETER)

