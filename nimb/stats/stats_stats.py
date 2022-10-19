'''
calculating the T-test for the means of two independent samples of scores (ttest_ind)
kurtosis for the column with Fisher definition, normal ==>0
skew: for normally distributed data, the skewness should be about zero. If >0, means more weight in the right tail of the distribution.
'''

import os
import string
import itertools

import pandas as pd
import numpy as np
from scipy import stats

from stats.db_processing import Table
from distribution import utilities


def get_stats_1sample(data):
    """return the stats for a sample of data
    Args:
        data = list() or tuple() of int() or float()
    """
    mean = stats.tmean(data)
    std = stats.tstd(data)
    kurtosis = stats.kurtosis(data)
    skewness = stats.skew(data)
    return {"mean":mean,
            "std":std,
            "kurtosis":kurtosis,
            "skewness":skewness}


def get_stats_2samples(data1, data2):
    """return the stats between 2 samples of data
    Args:
        data1, data2 = list() or tuple() of int() or float()
    """
    #two-sided test 2 independent samples
    ttest = stats.ttest_ind(data1, data2, equal_var = True), ('t','p')

    welch = stats.ttest_ind(data1, data2, equal_var = False), ('t','p')

    #One way ANOVA, checks the variance
    anova = stats.f_oneway(data1, data2), ('t','p')

    # Bartlett, tests the null hypothesis
    bartlett = stats.bartlett(data1, data2), ('t','p')
    try:
        mannwhitneyu = stats.mannwhitneyu(data1, data2), ('u','p')
    except ValueError:
        mannwhitneyu = (0,0), ('h','p')
    try:
        kruskal = stats.kruskal(data1, data2), ('h','p')
    except ValueError:
        kruskal = (0,0), ('h','p')

    #Calculates a Pearson correlation
    # pearsoncorr, pearsonp = stats.pearsonr(data1,data2)

    #Calculates a Spearman correlation
    # spearmancorr, spearmanp = stats.spearmanr(data1,data2)

    return {"ttest":ttest,
            "welch":welch,
            "anova":anova,
            "bartlett":bartlett,
            "mannwhitneyu":mannwhitneyu,
            "kruskal":kruskal}


def combinations_get(ls, lvl=0):
    """combining values from ls
    Args:
        ls = initial list() with values to be combined (ex : val du gr1 et val du gr 4)
        lvl = int() of number of values to be combined, (
                0 = blank tuple,
                1 = tuple with 1 value,
                2 = tuples of 2 values
    Return:
        combined = final list() that containes tuples() with combinations
                    exemple: [(group1, group2), (group2, group3), (group 1, group3)]
    """
    if lvl == 0:
        return [tuple()]
    elif lvl == 1:
        return [(i,) for i in ls]
    elif lvl == 2:
        result = list()
        combined = list(itertools.product(ls, ls))
        combined_diff = [i for i in combined if i[0] != i[1]]
        for i in combined_diff:
            if i not in result and (i[1], i[0]) not in result:
                result.append(i)
        return result
    else:
        print("    requests for combinations higher than 2\
            cannot be performed because FreeSurfer does not take them")


def get_stats(df_4stats,
                groups,
                group_col,
                path2save,
                sig_thresh = 0.05,
                nr_digits = 6,
                make_with_colors = True,
                filename_stats_json = 'stats',
                filename_stats      = 'stats.csv',
                filename_stats_sig  = 'stats_significant'):
    '''Creates discriptive statistical file,
        based on provided pandas.DataFrame
        Currently works only with 2 groups
    Args:
        df_4stats: pandas.DataFrame
        group: list/ tuple of groups as str/int
        group_col: str() column name in df_4stats that has the group names from group
        path_2save: abspath to save the descrptive files
        sig_thresh: a threshold that will be used to consider as significant the results
        make_with_colors: will create an additional .xlsx file with 
                        colored significant results,
                        provided xlwt is installed
    Return:
        saves results to a .json file
        saves results to a .csv file
        saves results to an .xlsx file where significant results are colored in red
    '''

    tab = Table()
    groups_df = dict()
    stats_dic = dict()
    cols2chk_sig = dict()
    ls_tests = list()
    for group in groups:
        groups_df[group] = tab.get_df_per_parameter(df_4stats, group_col, group)

    vals2chk = df_4stats.columns.tolist()
    if group_col in vals2chk:
        vals2chk.remove(group_col)
    
    for group in groups_df:
        for val in vals2chk:
            results = get_stats_1sample(groups_df[group][val])
            for test in results:
                if test not in ls_tests:
                    ls_tests.append(test)
                key = f'{group}, {test}'
                if key not in stats_dic:
                    stats_dic[key] = dict()
                stats_dic[key][val] = f'{results[test]}'

    for val in vals2chk:
        grpcontrast=(f'{str(groups[0])} vs {str(groups[1])}')
        results = get_stats_2samples(groups_df[groups[0]][val],
                                             groups_df[groups[1]][val])
        for test in results:
            if test not in ls_tests:
                ls_tests.append(test)
            key_test_result = f'{test}, {results[test][1][0]}'
            key_significance = f'{test}, {results[test][1][1]}'
            if key_significance not in cols2chk_sig:
                cols2chk_sig[key_significance] = dict()
            for key in (key_test_result, key_significance):
                if key not in stats_dic:
                    stats_dic[key] = dict()
            val_significance = format(results[test][0][1], f".{nr_digits}f")
            if float(val_significance) < sig_thresh:
                cols2chk_sig[key_significance][val] = val_significance
            stats_dic[key_test_result][val] = f'{results[test][0][0]}'
            stats_dic[key_significance][val] = f'{val_significance}'
    utilities.save_json(stats_dic, os.path.join(path2save,
                                            f'{filename_stats_json}.json'))

    df = tab.create_df_from_dict(stats_dic)
    df = df.astype(float)
    tab.save_df(df,
                os.path.join(path2save, filename_stats),
                sheet_name = 'stats')

    if make_with_colors:
        save_2xlsx_with_colors(df,
                               path2save = path2save,
                               file_name = filename_stats_sig,
                               sig_thresh = sig_thresh,
                               nr_digits = nr_digits,
                               cols2color_sig = cols2chk_sig)

    return stats_dic, cols2chk_sig


def save_2xlsx_with_colors(df,
                           path2save,
                           file_name,
                           sig_thresh,
                           nr_digits,
                           cols2color_sig = dict()):
    if not chk_if_module_ready('xlwt'):
        print('xlwt not installed, cannot continue saving to an xlsx file with colors')
        pass
    else:
        print('creating file xlsx with colors')
        if not file_name:
            file_name = "stats_significant.xlsx"
        else:
            file_name = f"{file_name}.xlsx"

        import xlwt
        w=xlwt.Workbook()
        xlwt.add_palette_colour("custom_colour", 0x21)
        w.set_colour_RGB(0x21, 251, 228, 228)
        style = xlwt.easyxf('pattern: pattern solid, fore_colour custom_colour')
        style_bold = xlwt.easyxf('font: bold on; font: color blue')
        style_significant = xlwt.easyxf('font: bold on; font: color red')
        ws = w.add_sheet('stats', cell_overwrite_ok=True)
        icol = 0
        ls_columns = df.columns.tolist()
        for col in ls_columns:
            ws.write(0, icol+1, col, style_bold)
            if not cols2color_sig:
                if ', p' in col.lower() or col.lower().endswith('p'):
                    cols2color_sig[col] = dict()
            icol += 1
        irow = 0
        while irow < len(df.index):
            ws.write(irow+1, 0, df.index[irow], style_bold)
            for icol in range(0, len(ls_columns)):
                col = ls_columns[icol]
                val = str(df.iloc[irow, icol])[:nr_digits]
                ws.write(irow+1, icol+1, val)
                if col in list(cols2color_sig.keys()) and float(val) < sig_thresh:
                    ws.write(irow+1, icol+1, val, style_significant)                     
            irow += 1
        w.save(os.path.join(path2save, file_name))
    # if make_with_colors:
    #     file = openpyxl.load_workbook(file_xlsx)
    #     sheet = file.worksheets[0]
    #     sheet['O1'].font = Font(color = 'FFFF0000')

    #     nbr_col = len(df.columns)+1
    #     ls_coord = f_coord(nbr_col)
    #     i = 0
    #     icol = ls_coord[0]
    #     ls_sig = []
    #     for col in sheet.iter_cols(values_only=True):
    #         irow = 1
    #         if col[1] == 'p':
    #             for cell in col:
    #                 cell_coord = ''.join((f'{icol}', f'{irow}'))
    #                 value = sheet.cell(irow,i+1).value

    #                 if type(value) is float and value <= sig_thresh:
    #                     ls_sig.append(value)
    #                     sheet[cell_coord].font = Font(color='FFFF0000')

    #                 irow += 1
    #         i+=1
    #         icol = ls_coord[i]
    #     file.save(os.path.join(path2save, filename_wcolors))


def make_table2publish(df,
                       groups,
                       tests,
                       stats_dic,
                       path2save,
                       filename_stats_2publish = 'stats_publishable.csv'):
    """creates a version of a csv table
        with sub-indices, that would be publishable
    author: Emmanuelle Mazur-Lainé 202206
    Args:
        df = pandas.DataFrame()
        tests = list() of tests
        filename_stats_2publish = str() name of the file to save
    Return:
        saves results to a csv file
    """


    ls_tests_dup = []
    ls_param = []
    ls_keys = list(stats_dic.keys())

    mean_gr_done = False

    for test in tests:
        if test in ('mean', 'std'):
            for i in range(0, len(groups)):
                ls_tests_dup.append('mean/std')
            if mean_gr_done == False:
                for i in range (len(groups)) :
                    ls_param.append('gr' + str(i + 1) + ' (val=' + f'{groups[i]}' + ')')
                    ls_param.append('gr' + str(i + 1) + ' (val=' + f'{groups[i]}' + ')')
                    mean_gr_done = True

        elif test in ('kurtosis', 'skewness'):
            for i in range(0, len(groups)) :
                ls_tests_dup.append(test)
                ls_param.append('gr' + str(i+1) + ' (val=' + f'{groups[i]}' + ')')

        elif test in ('TTest', 'Welch',
                'Bartlett', 'MannWhitneyu', 'Kruskal', 'ANOVA') :
            ls_tests_dup.append(test)
            ls_tests_dup.append(test)

    for key in ls_keys[4*(len(groups)):] :
        ls_param.append((str(key))[-1])


    col = [ls_tests_dup, ls_param]
    tuples = list(zip(*col))

    df_new = pd.DataFrame(df.values,
                          index = pd.Index(df.index),
                          columns = pd.MultiIndex.from_tuples(tuples))

    df_new = df_new.round(3)
    tab.save_df(df_new,
        os.path.join(path2save, filename_stats_2publish),
        sheet_name = 'stats')
    color_table2publish(df_new, groups, path2save)
    return df_new


def chk_if_module_ready(module):
    ls_import = list()
    try:
        ls_import.append(__import__(module))
        return True
    except ImportError:
        return False



class ttest_do():
    def __init__(self, df, group_col, ls_cols, groups, path_save_res, p_thresh = 0.05):
        print("function is OBSOLETE. many subfunctions were moved to another module. Please use: get_stats()")
    #     self.df = df
    #     self.group_col = group_col
    #     self.ls_cols = ls_cols
    #     self.groups = groups
    #     self.path_save_res = path_save_res
    #     self.ls_meas = get_names_of_measurements()
    #     self.ls_struct = get_names_of_structures()
    #     self.res_ttest = self.compute_ttest_for_col(p_thresh)
    #     self.tab       = Table()

    # def compute_ttest_for_col(self, p_thresh):
    #     res_4df = {'features':[], 'ttest':[], 'welch':[]}
    #     res = dict()
    #     for col in self.ls_cols:
    #         group1 = self.df[self.df[self.group_col] == self.groups[0]][col]
    #         group2 = self.df[self.df[self.group_col] == self.groups[1]][col]
    #         ttest_eq_pop_var = stats.ttest_ind(group1, group2, equal_var=True)
    #         ttest_welch = stats.ttest_ind(group1, group2, equal_var=False)
    #         if ttest_eq_pop_var[1] < p_thresh:
    #             meas, struct = get_structure_measurement(col, self.ls_meas, self.ls_struct)
    #             #print('{:<15} {}'.format(meas, struct))
    #             res[col] = {'{}, mean'.format(self.groups[0]): stats.tmean(group1),
    #                         '{}, std'.format(self.groups[1]): stats.tstd(group2),
    #                         '{}, mean'.format(self.groups[1]): stats.tmean(group2),
    #                         '{}, std'.format(self.groups[1]): stats.tstd(group2),
    #                         'ttest':ttest_eq_pop_var[1],
    #                         'welch':ttest_welch[1],
    #                         'kurtosis':stats.kurtosis(self.df[self.group_col]),
    #                         'skewness':stats.skew(self.df[self.group_col])}
    #             res_4df['features'].append(struct+' ('+meas+')')
    #             res_4df['ttest'].append(ttest_eq_pop_var[1])
    #             res_4df['welch'].append(ttest_welch[1])
    #     self.save_res(res_4df)
    #     return res

    # def save_res(self, res_4df):
    #     df_result = self.tab.create_df_from_dict(res_4df)
    #     df_result.to_csv(os.path.join(self.path_save_res,'ttest.csv'))