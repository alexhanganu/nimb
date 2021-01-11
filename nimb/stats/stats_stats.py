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
        df_result.to_csv(path.join(self.path_save_res,'ttest.csv'))

def make_descriptions_per_groups(groups, df, group_col, GLM_dir):
    '''creating files with descriptions and correlations of each sheet'''

    for group in groups:
            print('CREATING the file with general descriptions for group: ', group)
            df_descr= df.drop(df[df[group_col] != group].index)
            print('writing file with clinical and structural data for group: ',group)
            df_descr.to_excel(GLM_dir+'results/group_clin_struct_'+group+'.xlsx', sheet_name='data')
            writer = pd.ExcelWriter(GLM_dir+'results/group_descriptions_'+group+'_.xlsx', engine='xlsxwriter')
            print('writing description sheet, group: ',group)
            dfdescription = df_descr.describe()
            dfdescription.to_excel(writer, 'description')
            writer.save()

    print('FINISHED creating General Descriptions file')



def mkstatisticsf(df, group_col, GLM_dir):

    print('Creating the group_statistics.xls file with statistical results for groups')
    print(df.columns.tolist()[:5])
    '''creating lists with the row limits for each group and the number of cotrasts'''
    lsgroups = df[group_col]
    groups = []
    for x in lsgroups:
            if x not in groups:
                groups.append(x)
    lengroups = []
    for i in range(0,len(groups)):
        lengroups.append(0)
    for x in lsgroups:
        for group in groups:
            if x == group:
                lengroups[groups.index(group)] += 1
    # lengroups = [len(list(group)) for key, group in groupby(lsgroups)] #not working, don't know why
    rownr = [0]
    k = 0
    v = 0
    while k<len(lengroups):
            v = lengroups[k]+v
            rownr.append(v)
            k+=1

    NrOfGroupContrasts = 0
    l = 0
    while l<len(groups)-1:
        t = l+1
        while t<len(groups):
            NrOfGroupContrasts += 1
            t += 1
        l += 1
    #lists
    lsstatsres = ('ttest t','ttest p','anova t','anova p','Bartlett t','Bartlett p',
                  'MannWhitneyu u','MannWhitneyu p', 'Kruskal H','Kruskal p') #list of statistical results to be presented

    '''creating the file with statistical results'''

    w=xlwt.Workbook()
    xlwt.add_palette_colour("custom_colour", 0x21)
    w.set_colour_RGB(0x21, 251, 228, 228)
    style = xlwt.easyxf('pattern: pattern solid, fore_colour custom_colour')
    style_bold = xlwt.easyxf('font: bold on; font: color blue')
    style_significant = xlwt.easyxf('font: bold on; font: color red')

    ws = w.add_sheet('stats')
    df.drop(['id',group_col], axis=1, inplace=True)
    colnamesdata = df.columns.values.tolist()
    
    base = 0

    '''writing the first column with the names of the statistical tests'''
    n = 0
    row = base+2
    col = base    
    while n<NrOfGroupContrasts:
            n1 = 0
            while n1<len(lsstatsres):
                res = lsstatsres[n1]
                ws.write(row, col, res)
                n1 += 1
                row += 1
            n += 1
            row += 2
    
    '''writing the results for each data column and each group contrast'''
    colname = 0
    while colname<len(colnamesdata):
            row = base
            col = colname + 1
            ws.write(row, col, colnamesdata[colname])
        
            row = base +1
            l = 0
            while l<len(groups)-1:
                    t=l+1
                    group2compare1 = df[colnamesdata[colname]][rownr[l]:rownr[t]]
                                        #mk a list with the means and std of each groups

                    '''writing the results for each data column and each group contrast'''
                    while t<len(rownr)-1:
                        grpcontrast=(groups[l]+'vs'+groups[t])
                        group2compare2 = df[colnamesdata[colname]][rownr[t]:rownr[t+1]]
                        tls = []
                        pls = []
                        ttestt, ttestp = stats.ttest_ind(group2compare1,group2compare2) #two-sided test 2 independent samples>
                        anovat, anovap = stats.f_oneway(group2compare1,group2compare2) #One way Anova checks if the variance >
                        bartt, bartp = stats.bartlett(group2compare1,group2compare2) #Bartlett’s test tests the null hypothes>
                        try:
                            manu, manp = stats.mannwhitneyu(group2compare1,group2compare2) #
                        except ValueError:
                            manu, manp = (0, 0)
                        try:
                            kruskh, kruskp = stats.kruskal(group2compare1,group2compare2) #
                        except ValueError:
                            kruskh, kruskp = (0, 0)
                        tls = (ttestt, anovat, bartt, manu, kruskh)
                        pls = (ttestp, anovap, bartp, manp, kruskp)
                       #pearsoncorr, pearsonp = stats.pearsonr(group2compare1,group2compare2) #Calculates a Pearson correlati>
                       #spearmancorr, spearmanp = stats.spearmanr(group2compare1,group2compare2) #Calculates a Spearman rank->
                    
                        ws.write(row, col, grpcontrast, style_bold)
                    
                        reslsnr = 0
                        row += 1
                        while reslsnr<len(tls):
                            ws.write(row, col, tls[reslsnr])
                            if pls[reslsnr]<0.05:
                                ws.write(row+1, col, pls[reslsnr], style_significant)
                            else:
                                ws.write(row+1, col, pls[reslsnr])
                            reslsnr += 1
                            row += 2

                        t=t+1
                        row += 1
                    
                    l=l+1

            '''creating the plots for all groups for each column/value'''
            #make a plot with means and std for all groups for each value
            colname += 1

    w.save(GLM_dir+'results/group_statistics.xls')
    print('FINISHED creating General Statistics files')
