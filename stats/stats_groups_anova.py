'''
======================================
======================================
GROUP ANALYSIS: ANOVA & SIMPLE LINEAR REGRESSION
======================================
======================================

if cor with education in ALL SUBJECTS:
       if ttest differences between the groups:
           ANOVA education+Age region significant'''

from .stats_definitions import get_structure_measurement, get_names_of_measurements, get_names_of_structures
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.formula.api import ols# For statistics, statsmodels =>5.0
from matplotlib import pyplot as plt
import seaborn as sns
from os import listdir, path, mkdir

def Make_plot_group_difference(data_groups_anova, col, measurement, structure, PATH_plots_groups, group_col, groups):
    # groups = _GET_Groups(data_groups_anova, group_col)
    df = pd.DataFrame({'Groupe':data_groups_anova[group_col],\
                  groups[0]:data_groups_anova[data_groups_anova[group_col] == groups[0]][col],\
                  groups[1]:data_groups_anova[data_groups_anova[group_col] == groups[1]][col]})
    df = df[['Groupe',groups[0],groups[1]]]
    dd=pd.melt(df,id_vars=['Groupe'],value_vars=[groups[0],groups[1]],var_name=col)
    group_plot = sns.boxplot(x='Groupe',y='value',data=dd,hue=col)
    group_plot.figure.savefig(PATH_plots_groups+'/'+structure+'_'+measurement)
    plt.close()

def Make_Plot_Regression(data_groups_anova, col, parameter,model, measurement, structure, PATH_plots_regression, group_col):
    df_plot = pd.DataFrame({
        'Groupe':np.array(data_groups_anova[group_col]),
        parameter:np.array(data_groups_anova[parameter]),
        col:np.array(data_groups_anova[col])})
    sns_plot = sns.lmplot(x=parameter, y=col,hue='Groupe', data=df_plot)#, robust=True
    axes = sns_plot.axes.flatten()
    axes[0].set_title('Groupe diff. p='+str('%.4f'%model.pvalues.x)+'; intercept='+str('%.4f'%model.pvalues.Intercept))
    sns_plot.savefig(PATH_plots_regression+'/'+structure+'_'+measurement+'.png')
    plt.close()


def Compute_ttest_for_col(col):
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
# def _GET_Groups(df, group_col):
    # groups = []
    # for val in df[group_col]:
        # if val not in groups:
            # groups.append(val)
    # return groups

def RUN_GroupAnalysis_ANOVA_SimpleLinearRegression(df, 
                                                    groups, 
                                                    PARAMETERS_y, 
                                                    Other_Params, 
                                                    PATH2save,
                                                    group_col,
                                                    ls_brain_regions):
    '''
    Interpreting the Regression Results
    model.summary()

    Adjusted. R-squared reflects the fit of the model. R-squared values range from 0 to 1, where a higher value generally indicates a better fit, assuming certain conditions are met.
    Y-intercept. means that if both the Interest_Rate and Unemployment_Rate coefficients are zero, then the expected output (i.e., the Y) would be equal to the const coefficient.
    x coefficient represents the change in the output Y due to a change of one unit in the x (everything else held constant)
    std err reflects the level of accuracy of the coefficients. The lower it is, the higher is the level of accuracy
    P >|t| is your p-value. A p-value of less than 0.05 is considered to be statistically significant
    Confidence Interval represents the range in which our coefficients are likely to fall (with a likelihood of 95%)
    '''
    ls_meas = get_names_of_measurements()
    ls_struct = get_names_of_structures()
    columns_main_DK_order = ('VolSeg','VolL_DK', 'VolR_DK', 'ThickL_DK', 'ThickR_DK', 'AreaL_DK', 'AreaR_DK', 'CurvL_DK', 'CurvR_DK', 
                     'NumVertL_DK','NumVertR_DK','FoldIndL_DK','FoldIndR_DK', 'CurvIndL_DK', 'CurvIndR_DK',
                     'CurvGausL_DK','CurvGausR_DK', 'VolSegWM_DK',
                     'ThickStdL_DS',  'ThickStdR_DS', 'eTIV')
    columns_main_DS_order = ('VolL_DS', 'VolR_DS','ThickL_DS', 'ThickR_DS', 'AreaL_DS', 'AreaR_DS', 'CurvL_DS', 'CurvR_DS', 
                     'NumVertL_DS', 'NumVertR_DS', 'FoldIndL_DS','FoldIndR_DS','CurvIndL_DS','CurvIndR_DS',  
                     'CurvGausL_DS','CurvGausR_DS',
                      'ThickStdL_DS',  'ThickStdR_DS',)
    columns_secondary_order = ('VolSegWM_DK','VolSegNVoxels', 'VolSegnormMean', 'VolSegnormStdDev', 'VolSegnormMin',
                     'NumVertL_DS', 'ThickStdL_DS', 'CurvIndL_DS', 'FoldIndL_DS', 'NumVertR_DS', 'ThickStdR_DS',
                     'CurvGausR_DS', 'CurvIndR_DS', 'FoldIndR_DS', 'VolSegWMNVoxels_DK', 'VolSegWMnormMean_DK',
                     'VolSegWMnormStdDev_DK', 'VolSegWMnormMin_DK', 'VolSegWMnormMax_DK', 'VolSegWMnormRange_DK')


    for PARAMETER_y in PARAMETERS_y:
        PATH_plots_regression = PATH2save+'/'+str(PARAMETER_y)+'_regression_pca'
        if not path.exists(PATH_plots_regression):
            mkdir(PATH_plots_regression)
        # PATH_plots_groups = PATH2save+'/'+str(PARAMETER_y)+'_group'
        # if not path.exists(PATH_plots_groups):
        #     mkdir(PATH_plots_groups)
        x = np.array(df[PARAMETER_y])
        df_result = pd.DataFrame(columns=[PARAMETER_y])
        df_result_list = pd.DataFrame(columns=[PARAMETER_y])

        ix = 1
        ixx = 1

        for col in ls_brain_regions[10:]:
            print('    left to analyse:',len(ls_brain_regions[ls_brain_regions.index(col):]),'\n')
            print(col)
            #res_ttest_sig = Compute_ttest_for_col(col)
            y = np.array(df[col])
            data_tmp = pd.DataFrame({'x':x,col:y})
            model = ols(col+" ~ x", data_tmp).fit()
            if model.pvalues.Intercept < 0.05:# and model.pvalues.x < 0.05:
                # print("    ",model.pvalues)
                measurement, structure = get_structure_measurement(col, ls_meas, ls_struct)
                # if structure+'_'+measurement not in listdir(PATH_plots_groups):
                # Make_plot_group_difference(df, col, measurement, structure, PATH_plots_groups, group_col, groups)
                Make_Plot_Regression(df, col,PARAMETER_y,model, measurement, structure, PATH_plots_regression, group_col)
                df_result_list.at[ixx,PARAMETER_y] = structure
                df_result_list.at[ixx,'pvalue'] = '%.4f'%model.pvalues.x
                df_result_list.at[ixx,'measure'] = measurement
                if structure not in df_result[PARAMETER_y].tolist():
                    df_result.at[ix,PARAMETER_y] = structure
                    df_result.at[ix,measurement] = '%.4f'%model.pvalues.x
                    ix += 1
                else:
                    df_result.at[df_result[PARAMETER_y].tolist().index(structure),measurement] = '%.4f'%model.pvalues.x
                ixx += 1
        # sort df_result_list by the pvalue columns
        df_result_list.to_csv(PATH2save+'/linear_regression_results_per_sgnificance_'+PARAMETER_y+'.csv')
        # sort df_results columns as per columns_order
        df_result.to_csv(PATH2save+'/linear_regression_results_per_structure_'+PARAMETER_y+'2.csv')
# in results per structure - the structures are not the same as in the first file.
# probably the renewal of structures is not made










'''
======================================
======================================
IMPORTS
======================================
======================================'''
'''
print('IMPORTING LIBRARIES')
from os import path, sys, remove, listdir, makedirs
import shutil, time, linecache
from .definitions import name_structure, name_measurement
:
import numpy as np
import pandas as pd
import xlsxwriter, xlrd, xlwt

from scipy import stats
from itertools import groupby


import matplotlib 
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import seaborn as sns
                # sns.set(style="white")
sns.set(style="whitegrid", color_codes=True)

from statsmodels.formula.api import ols# For statistics, statsmodels =>5.0

def Make_Dirs(dir):
    if not path.isdir(dir):
        makedirs(dir)
df = pd.read_excel(PATH2save_results+working_file)

'''


'''Moderation Analysis'''

''' formula='QUANTITATIVE_RESPONSE_VARIABLE ~ C(CATEGORICAL_EXPLANATORY_VARIABLE)'
    capital "C" indicates that this is a categorical explanatory variable and the 
    variable name is within parenthesis
    model = ols(formula='WeightLoss ~ C(Diet)', data=df).fit()'''


'''
main_vars = ['Age', 'Gender', 'education']
for var in df.columns[df.columns.tolist().index(group_id)+1:]:
    model = ols(formula='{0} ~ C({1})'.format(var, group_id), data=df).fit()
    if model.f_pvalue < 0.05:
        print('ANOVA significant: ', var)
#print(model.summary())
'''
'''EXPLANATION:
the Dependent variable is MOCA (Dep. Variable) the are 165 observations
F-statistic is 0 and its associated with a non-significant p-value (Prob (F-statistic))
this tells us there is no association between Age and MOCA'''

# sub1= df[['MOCA', 'Age']]
# print('means by MOCA')
# m1 = sub1.groupby('MOCA').mean()
# print(m1)
# print('\nstd for mean MOCA and Age')
# std1 = sub1.groupby('MOCA').std()
# print(std1)

'''

# bivariate bar graph
x = 'education'
y = 'voltoeTIVMask_Segmentations'
for kind in ['swarm', 'violin', 'point', 'boxen', 'box', 'strip', 'bar']:
    seaborn.catplot(x=x, y=y, data=df, kind=kind, ci=None)
    plt.xlabel(x)
    plt.ylabel(y)
'''
'''to test the moderation of a third variable we will do 2 ANOVAs.
we need to create dataframes with only the subsample of interest - 
either one or the other variable separately. 
Then the ANOVA is run for the separate dataframes.'''






		
		
'''ALL SUBJECTS ANALYSIS: ANOVA & SIMPLE LINEAR REGRESSION'''
def Make_Posthoc(model,res,factor,measurement):
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
    

def save_df(res, parameter, PATH2save_anova):
    df_anova = pd.DataFrame.from_dict(res)
    df_transpose = df_anova.transpose()
    df_transpose.sort_index(inplace=True)
    df_transpose.to_csv(PATH2save_anova+'/anova_'+parameter+'.csv')


def RUN_ANOVA_SimpleLinearRegression(data_anova, PARAMETER_x_Age, PARAMETERS_INTEREST_y, ls_struct_cols, PATH2save_anova):

    res_anova_age_struct = {}
    res_anova_parameter_struct = {}
    res_anova_parameter_age_struct = {}


    for col in ls_struct_cols:
        model_age_struct = ols(formula=col+' ~ '+PARAMETER_x_Age, data=data_anova).fit()
        res_age_struct = model_age_struct.pvalues
        if res_age_struct.Intercept<0.05:
            if res_age_struct.Age<0.05:
                measurement, structure = get_structure_measurement(col)
                res_anova_age_struct[structure] = Make_Posthoc(model_age_struct,res_age_struct,[PARAMETER_x_Age],measurement)	
        save_df(res_anova_age_struct, PARAMETER_x_Age, PATH2save_anova)
        print('DONE for all')

    for PARAMETER in PARAMETERS_INTEREST_y:
        for col in ls_struct_cols:
            model_parameter_struct = ols(formula=col+' ~ '+PARAMETER, data=data_anova).fit()
            res_parameter_struct = model_parameter_struct.pvalues
            if res_parameter_struct.Intercept<0.05:
                measurement, structure = get_structure_measurement(col)
                if PARAMETER == 'education':
                    if res_parameter_struct.education<0.05:
                        res_anova_parameter_struct[structure] = Make_Posthoc(model_parameter_struct,res_parameter_struct,[PARAMETER],measurement)
                elif PARAMETER == 'MOCA':
                    if res_parameter_struct.MOCA<0.05:
                        res_anova_parameter_struct[structure] = Make_Posthoc(model_parameter_struct,res_parameter_struct,[PARAMETER],measurement)
                else:
                    print('PARAMETER name is:',PARAMETER,'not testing if <0.05')
                    res_anova_parameter_struct[structure] = Make_Posthoc(model_parameter_struct,res_parameter_struct,[PARAMETER],measurement)
            model_parameter_age_struct = ols(formula=col+' ~ '+PARAMETER+' + '+PARAMETER_x_Age, data=data_anova).fit()
            res_parameter_age_struct = model_parameter_age_struct.pvalues
            if res_parameter_age_struct.Intercept<0.05:
                measurement, structure = get_structure_measurement(col)
                if PARAMETER == 'education':
                    if res_parameter_struct.education<0.05:
                        res_anova_parameter_age_struct[structure] = Make_Posthoc(model_parameter_age_struct,res_parameter_age_struct,[PARAMETER,PARAMETER_x_Age],measurement)
                elif PARAMETER == 'MOCA':
                    if res_parameter_struct.MOCA<0.05:
                        res_anova_parameter_struct[structure] = Make_Posthoc(model_parameter_struct,res_parameter_struct,[PARAMETER],measurement)
                else:
                    print('PARAMETER name is:',PARAMETER,'not testing if <0.05')
                    res_anova_parameter_age_struct[structure] = Make_Posthoc(model_parameter_age_struct,res_parameter_age_struct,[PARAMETER,PARAMETER_x_Age],measurement)

        save_df(res_anova_parameter_struct, PARAMETER, PATH2save_anova)
        save_df(res_anova_parameter_age_struct, PARAMETER+'_'+PARAMETER_x_Age, PATH2save_anova)
        print('DONE for ',PARAMETER)

#    for col in ls_struct_cols:
#        model_age_struct = ols(formula=col+' ~ Age', data=data_anova).fit()
#        res_age_struct = model_age_struct.pvalues
#        if res_age_struct.Intercept<0.05:
#            res_anova_age_struct[col] = Make_Posthoc(model_age_struct,res_age_struct,['Age',])
#        model_edu_struct = ols(formula=col+' ~ education', data=data_anova).fit()
#        res_edu_struct = model_edu_struct.pvalues
#        if res_edu_struct.Intercept<0.05:
#            res_anova_edu_struct[col] = Make_Posthoc(model_edu_struct,res_edu_struct,['education',])
#        model_edu_age_struct = ols(formula=col+' ~ education + Age', data=data_anova).fit()
#        res_edu_age_struct = model_edu_age_struct.pvalues
#        if res_edu_age_struct.Intercept<0.05:
#            res_anova_edu_age_struct[col] = Make_Posthoc(model_edu_age_struct,res_edu_age_struct,['education','Age',])

#    save_df(res_anova_age_struct,'anova_age_struct')
#    save_df(res_anova_edu_struct,'anova_edu_struct')
#    save_df(res_anova_edu_age_struct,'anova_edu_age_struct')

