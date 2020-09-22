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


def RUN_GroupAnalysis_ANOVA_SimpleLinearRegression(df,
                                                    groups,
                                                    PARAMETERS_y,
                                                    Other_Params,
                                                    PATH2save,
                                                    group_col,
                                                    ls_brain_regions):
    ls_meas = get_names_of_measurements()
    ls_struct = get_names_of_structures()
    for PARAMETER_y in PARAMETERS_y:
        PATH_plots_regression = PATH2save+'/'+str(PARAMETER_y)+'_regression_pca'
        if not path.exists(PATH_plots_regression):
            mkdir(PATH_plots_regression)
        x = np.array(df[PARAMETER_y])
        df_result = pd.DataFrame(columns=[PARAMETER_y])
        df_result_list = pd.DataFrame(columns=[PARAMETER_y])
        ix = 1
        ixx = 1
        for col in ls_brain_regions[10:]:
            print('    left to analyse:',len(ls_brain_regions[ls_brain_regions.index(col):]),'\n')
            print(col)
            y = np.array(df[col])
            data_tmp = pd.DataFrame({'x':x,col:y})
            model = ols(col+" ~ x", data_tmp).fit()
            if model.pvalues.Intercept < 0.05:# and model.pvalues.x < 0.05:
                measurement, structure = get_structure_measurement(col, ls_meas, ls_struct)
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
