'''
calculating the T-test for the means of two independent samples of scores (ttest_ind)
kurtosis for the column with Fisher definition, normal ==>0
skew: for normally distributed data, the skewness should be about zero. If >0, means more weight in the right tail of the distribution.
'''

from stats import db_processing
from processing.freesurfer.fs_definitions import get_structure_measurement, get_names_of_measurements, get_names_of_structures
import pandas as pd
import numpy as np
from scipy import stats
import os
from stats.db_processing import Table
from distribution import utils


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
                res[col] = {'{}, mean'.format(self.groups[0]): stats.tmean(group1),
                            '{}, std'.format(self.groups[1]): stats.tstd(group2),
                            '{}, mean'.format(self.groups[1]): stats.tmean(group2),
                            '{}, std'.format(self.groups[1]): stats.tstd(group2),
                            'ttest':ttest_eq_pop_var[1],
                            'welch':ttest_welch[1],
                            'kurtosis':stats.kurtosis(self.df[self.group_col]),
                            'skewness':stats.skew(self.df[self.group_col])}
                res_4df['features'].append(struct+' ('+meas+')')
                res_4df['ttest'].append(ttest_eq_pop_var[1])
                res_4df['welch'].append(ttest_welch[1])
        self.save_res(res_4df)
        return res

    def save_res(self, res_4df):
        df_result = db_processing.create_df_from_dict(res_4df)
        df_result.to_csv(os.path.join(self.path_save_res,'ttest.csv'))


def get_stats(stats_type, data1, data2):
    '''
    Args: type of stats, data
    Return: float
    '''
    if stats_type == 'mean':
        return (stats.tmean(data1), stats.tmean(data2)), ('mean', 'mean')
    if stats_type == 'std':
        return (stats.tstd(data1), stats.tstd(data2)), ('std', 'std')
    elif stats_type == 'kurtosis':
        return (stats.kurtosis(data1), stats.kurtosis(data2)), ('kurtosis', 'kurtosis')
    elif stats_type == 'skewness':
        return (stats.skew(data1), stats.skew(data2)), ('skewness', 'skewness')
    elif stats_type == 'TTest':
        return stats.ttest_ind(data1, data2, equal_var = True), ('t','p')
    elif stats_type == 'Welch':
        return stats.ttest_ind(data1, data2, equal_var = False), ('t','p')
    elif stats_type == 'ANOVA':
        return stats.f_oneway(data1, data2), ('t','p') #One way ANOVA, checks the variance
    elif stats_type == 'Bartlett':
        return stats.bartlett(data1, data2), ('t','p') # Bartlett, tests the null hypothesis
    elif stats_type == 'MannWhitneyu':
        try:
            return stats.mannwhitneyu(data1, data2), ('u','p')
        except ValueError:
            return (0,0), ('h','p')
    elif stats_type == 'Kruskal':
        try:
            return stats.kruskal(data1, data2), ('h','p')
        except ValueError:
            return (0,0), ('h','p')


def mkstatisticsf(df_4stats,
                groups,
                group_col,
                path2save,
                make_with_colors = True):
    '''Creates discriptive statistical file for publication,
        based on provided pandas.DataFrame
        Works only on 2 groups
    Args: df_4stats: pandas.DataFrame
        group: list/ tuple of groups as str/int
        group_col: column name in df_4stats that has the group names from group
        path_2save: abspath to save the descrptive files
        make_with_colors: will create an additional .xlsx file with 
                        colored significant results,
                        provided xlwt is installed
    Return:
        json file with results
        .csv file with results
        .xlsx file with results with red colored significant ones
    '''

    tab = Table()
    ls_tests = ('mean', 'std',
                'kurtosis', 'skewness',
                'TTest', 'Welch', 'ANOVA', 
                'Bartlett', 'MannWhitneyu', 'Kruskal')

    groups_df = dict()
    for group in groups:
        groups_df[group] = tab.get_df_per_parameter(df_4stats, group_col, group)

    stats_dic = dict()
    vals2chk = df_4stats.columns.tolist()
    if group_col in vals2chk:
        vals2chk.remove(group_col)

    cols2color_sig = list()
    groups = list(groups_df.keys())
    group1 = groups_df[groups[0]]
    group2 = groups_df[groups[1]]
    for test in ls_tests:
        for val in vals2chk:
            results, params = get_stats(test, group1[val], group2[val])       
            if test in ('mean', 'std', 'kurtosis', 'skewness'):
                key1 = f'{groups[0]}, {params[0]}'
                key2 = f'{groups[1]}, {params[0]}'
            else:
                key1 = f'{test}, {params[0]}'
                key2 = f'{test}, {params[1]}'
                cols2color_sig.append(key2)
            for key in (key1, key2):
                if key not in stats_dic:
                    stats_dic[key] = dict()
            stats_dic[key1][val] = f'{results[0]}'
            stats_dic[key2][val] = f'{results[1]}'

    df = tab.create_df_from_dict(stats_dic)
    tab.save_df(df, os.path.join(path2save, 'stats_general.csv'), sheet_name = 'stats')
    utils.save_json(stats_dic, os.path.join(path2save,'stats_general.json'))
    if make_with_colors:
        save_2xlsx_with_colors(df, path2save = path2save,
                           cols2color_sig = cols2color_sig)


def chk_if_module_ready(module):
    ls_import = list()
    try:
        ls_import.append(__import__(module))
        return True
    except ImportError:
        return False

def save_2xlsx_with_colors(df, path2save,
                           file_name = 'stats_general.xlsx',
                           cols2color_sig = [],
                           sig_thresh = 0.05,
                           nr_digits = 6):
    if not chk_if_module_ready('xlwt'):
        print('xlwt not installed, cannot continue saving to an xlsx file with colors')
        pass
    else:
        print('creating file xlsx with colors')
        import xlwt
        w=xlwt.Workbook()
        xlwt.add_palette_colour("custom_colour", 0x21)
        w.set_colour_RGB(0x21, 251, 228, 228)
        style = xlwt.easyxf('pattern: pattern solid, fore_colour custom_colour')
        style_bold = xlwt.easyxf('font: bold on; font: color blue')
        style_significant = xlwt.easyxf('font: bold on; font: color red')
        ws = w.add_sheet('stats_general', cell_overwrite_ok=True)
        icol = 0
        for col in df.columns.tolist():
            ws.write(0, icol+1, col, style_bold)
            if not cols2color_sig:
                if ', p' in col.lower() or col.lower().endswith('p'):
                    cols2color_sig.append(col)
            icol += 1
        irow = 0
        while irow < len(df.index):
            ws.write(irow+1, 0, df.index[irow], style_bold)
            for icol in range(0, len(df.columns.tolist())):
                col = df.columns.tolist()[icol]
                val = str(df.iloc[irow, icol])[:nr_digits]
                ws.write(irow+1, icol+1, val)
                if col in cols2color_sig and float(val) < sig_thresh:
                    ws.write(irow+1, icol+1, val, style_significant)                     
            irow += 1
        w.save(os.path.join(path2save, file_name))

# def mkstatisticsf(df, group_col, GLM_dir):

#     print('Creating the group_statistics.xls file with statistical results for groups')
#     print(df.columns.tolist()[:5])
#     '''creating lists with the row limits for each group and the number of cotrasts'''
#     lsgroups = df[group_col]
#     groups = []
#     for x in lsgroups:
#             if x not in groups:
#                 groups.append(x)
#     lengroups = []
#     for i in range(0,len(groups)):
#         lengroups.append(0)
#     for x in lsgroups:
#         for group in groups:
#             if x == group:
#                 lengroups[groups.index(group)] += 1
#     # lengroups = [len(list(group)) for key, group in groupby(lsgroups)] #not working, don't know why
#     rownr = [0]
#     k = 0
#     v = 0
#     while k<len(lengroups):
#             v = lengroups[k]+v
#             rownr.append(v)
#             k+=1

#     NrOfGroupContrasts = 0
#     l = 0
#     while l<len(groups)-1:
#         t = l+1
#         while t<len(groups):
#             NrOfGroupContrasts += 1
#             t += 1
#         l += 1
#     #lists
#     lsstatsres = ('ttest t','ttest p','anova t','anova p','Bartlett t','Bartlett p',
#                   'MannWhitneyu u','MannWhitneyu p', 'Kruskal H','Kruskal p') #list of statistical results to be presented

#     '''creating the file with statistical results'''

#     w=xlwt.Workbook()
#     xlwt.add_palette_colour("custom_colour", 0x21)
#     w.set_colour_RGB(0x21, 251, 228, 228)
#     style = xlwt.easyxf('pattern: pattern solid, fore_colour custom_colour')
#     style_bold = xlwt.easyxf('font: bold on; font: color blue')
#     style_significant = xlwt.easyxf('font: bold on; font: color red')

#     ws = w.add_sheet('stats')
#     df.drop(['id',group_col], axis=1, inplace=True)
#     colnamesdata = df.columns.values.tolist()
    
#     base = 0

#     '''writing the first column with the names of the statistical tests'''
#     n = 0
#     row = base+2
#     col = base    
#     while n<NrOfGroupContrasts:
#             n1 = 0
#             while n1<len(lsstatsres):
#                 res = lsstatsres[n1]
#                 ws.write(row, col, res)
#                 n1 += 1
#                 row += 1
#             n += 1
#             row += 2
    
#     '''writing the results for each data column and each group contrast'''
#     colname = 0
#     while colname<len(colnamesdata):
#             row = base
#             col = colname + 1
#             ws.write(row, col, colnamesdata[colname])
        
#             row = base +1
#             l = 0
#             while l<len(groups)-1:
#                     t=l+1
#                     group2compare1 = df[colnamesdata[colname]][rownr[l]:rownr[t]]
#                                         #mk a list with the means and std of each groups

#                     '''writing the results for each data column and each group contrast'''
#                     while t<len(rownr)-1:
#                         grpcontrast=(groups[l]+'vs'+groups[t])
#                         group2compare2 = df[colnamesdata[colname]][rownr[t]:rownr[t+1]]
#                         tls = []
#                         pls = []
#                         ttestt, ttestp = stats.ttest_ind(group2compare1,group2compare2) #two-sided test 2 independent samples>
#                         anovat, anovap = stats.f_oneway(group2compare1,group2compare2) #One way Anova checks if the variance >
#                         bartt, bartp = stats.bartlett(group2compare1,group2compare2) #Bartlett’s test tests the null hypothes>
#                         try:
#                             manu, manp = stats.mannwhitneyu(group2compare1,group2compare2) #
#                         except ValueError:
#                             manu, manp = (0, 0)
#                         try:
#                             kruskh, kruskp = stats.kruskal(group2compare1,group2compare2) #
#                         except ValueError:
#                             kruskh, kruskp = (0, 0)
#                         tls = (ttestt, anovat, bartt, manu, kruskh)
#                         pls = (ttestp, anovap, bartp, manp, kruskp)
#                        #pearsoncorr, pearsonp = stats.pearsonr(group2compare1,group2compare2) #Calculates a Pearson correlati>
#                        #spearmancorr, spearmanp = stats.spearmanr(group2compare1,group2compare2) #Calculates a Spearman rank->
                    
#                         ws.write(row, col, grpcontrast, style_bold)
                    
#                         reslsnr = 0
#                         row += 1
#                         while reslsnr<len(tls):
#                             ws.write(row, col, tls[reslsnr])
#                             if pls[reslsnr]<0.05:
#                                 ws.write(row+1, col, pls[reslsnr], style_significant)
#                             else:
#                                 ws.write(row+1, col, pls[reslsnr])
#                             reslsnr += 1
#                             row += 2

#                         t=t+1
#                         row += 1
                    
#                     l=l+1

#             '''creating the plots for all groups for each column/value'''
#             #make a plot with means and std for all groups for each value
#             colname += 1

#     w.save(GLM_dir+'results/group_statistics.xls')
#     print('FINISHED creating General Statistics files')
