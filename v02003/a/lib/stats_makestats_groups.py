#!/bin/python
'''2DO
    ppt: https://medium.com/@d.timothy.freeman/using-python-pptx-to-programmatically-create-powerpoint-slides-b7a8581fb184
group descriptions: mkstatisticsf
    descriptions - significant differences put in red
    correlations must be done per GROUP on the same file, saved in another file in /results/
	+ correlations 07, 08 must be done per GROUP on the same file, saved in separate sheets and outlined in red the sig
	significant diff between groups in volumes and clinical, if sig -> make plot.

	
logistic regression:
    https://scikit-learn.org/stable/auto_examples/linear_model/plot_sgd_comparison.html
	https://scikit-learn.org/stable/auto_examples/linear_model/plot_iris_logistic.html
	https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html

STATS methods:
    (1) creating 2 columns of a report showing statistically sig baseline diff M vs. W.
	(2) comparison of the estimate of effect by sex can be achieved by using the raw data to construct two separate 2 x 2 tables, then calculating measures of association between the exposure and outcome for men and women separately
	(3) stratification example (another): building a structural equation model with the data and testing the goodness of fit, or diff in specific paths in the model, separately for each sex
	(4) mediation modelling allow to understand the mechanisms that produce the m/f diff in the health outcome - they show what the contribution of individual sex- and gender- related factors have on m/f diff in the outcome. this approach allow to estimate what m/f diff would remain if these factors were equal between m and w. 
    controlling or adjusting for sex in multivariable regression or modelling analysis is not the same as stratification. Controlling for sex eliminates the ability to explore data separately for men and women. If the relationship between the variable of interest and the outcome differes for men and women, adjustment for sex will provide an estimate of the average relationship between the variable and the outcome, if sex was held constant.
	A commong error is toreport baseline sex differences in Table 1 of a paper then only present adjusted analysis in the rest of the results section. Stratified analysis should always be presented when there is evidence that the effect of exposure differts (or there is reason to believe it might differ) for men and owmen.
	(5) testing sex as a modifying variable using interaction terms: y=b0+b1X1+b2X2+B3X1*X2; creating an interaction term with sex then testing for sig using regression anal. is equiv to stratifying by sex and comparing if estimated for m and w diff.; if the interaction term is sig, data points can be introduced into equation to calcualte estimates of effect separately for m and w; creating an interaction term is commonly used to determine whether sex modifies the relationship between a given exposure and outcome; when analysis are presented separately by sex, this provides the clearest picture of where exposure might differ for m and w. the diff in estimated between m and w should always be formally tested, but oftern it is quite difficult to calculate and interpret diff using coef from multiple interaction.
	(6) 4 common strategies are used to analyze gender: account for gender by using sex-related associations; look for a gender story by applying second-level disaggregation by sex; look for a gender story by using gender-related variables; create a composite gender index/gender score to analyze gender independently of sex.
	=> to create a gender index/score: (1) sum up diff vars to create a score; (2) regress vars to predict m/f; (3) factor analysis to capture underlying gender-based constructs; (4) create a ranking based on the m/f distribution to a single var (e.g.: vars -> PCA -> LogisticRegression-> predictive vars retained[Pelletier R, Ditto B, Pilote L, 2015]{predictive vars: info who is the primary earner in the household; personal income, nr of hrs of housework, responsibility for housework, lvl of stress at home, measures of masculinity, measures of femininity Bem Sex Role Inventory})
	
	zipf's law https://getpocket.com/explore/item/mathematical-model-reveals-the-patterns-of-how-innovations-arise
'''



'''
======================================
======================================
IMPORTS
======================================
======================================'''
print('IMPORTING LIBRARIES')
from os import path, sys, remove, listdir, makedirs
import shutil, time, linecache
from .definitions import name_structure, name_measurement

try:
            import pandas as pd
            try:
                import xlsxwriter, xlrd, xlwt
            except ImportError:
                print('Install xlsxwriter, xlrd and xlwt  modules (pip3 install xlsxwriter, xlrd)')
except ImportError:
                print('Install pandas module. Type in the terminal: pip3 install pandas')

try:
            from scipy import stats
            from itertools import groupby
except ImportError:
            from sys import platform as _platform
            if _platform == 'linux' or _platform == 'linux2':
                sys.exit('Install scipy module. Type in the terminal: sudo apt-get install python-scipy')
            elif _platform == 'darwin':
                sys.exit('Install scipy module. Type in the terminal: pip3 install scipy')
            elif _platform == 'win32':
                print('Download the numpy mkl from here: http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy\n')
                print('Download the win32 version of scipy: http://www.lfd.uci.edu/~gohlke/pythonlibs/#scipy\n')
                print('In the cmd.exe use the command: pip install package.whl')

try:
            import matplotlib 
            matplotlib.use('Agg')
            from matplotlib import pyplot as plt
            try:
                import seaborn as sns
                # sns.set(style="white")
                # sns.set(style="whitegrid", color_codes=True)
            except ImportError:
                sys.exit('Install seaborn module (pip3 install seaborn)')
except ImportError:
            sys.exit('Install matplotlib (pip3 install matplotlib')
try:
    import numpy as np
    from statsmodels.formula.api import ols# For statistics, statsmodels =>5.0
except ImportError:
    sys.exit('Install numpy and statsmodels')




def Make_Dirs(dir):
    if not path.isdir(dir):
        makedirs(dir)

		
		
'''
======================================
======================================
Initiate Analysis per for groups
======================================
======================================'''
class MakeStatsForGroups():
    '''
    based on the groups.xlsx file and the data from the data.xlsx files
    will create new 
	datapergroup.xlsx
	group_statistics.xls files that will have the statistical results for groups
	and perform GLM analysis
    '''

    def __init__(self, GLM_dir, file_groups, id_col, group_col, freesurfer):
        self.Make_Dirs(GLM_dir)
        print('reading groups')
        PARAMETER_x_Age = 'Age'
        PARAMETERS_INTEREST_y = list()
        self.df_clin = pd.read_excel(file_groups, sheet_name='data')
        for i in self.df_clin.columns.tolist():
            if i not in [id_col,group_col,PARAMETER_x_Age]:
                PARAMETERS_INTEREST_y.append(i)

        dataf = GLM_dir+'data.xlsx'
        self.data_subcortical_volumes = GLM_dir+'group_data_subcortical_volumes.xlsx'
        if path.isfile(GLM_dir+'group_data_subcortical_volumes_etiv_corr.xlsx'):#group_clin_brain_volumes_eTIVcor
            self.data_subcortical_volumes = GLM_dir+'group_data_subcortical_volumes_etiv_corr.xlsx'
        self.data_big = GLM_dir+'group_data_big.xlsx'
        self.id_col = id_col
        self.group_col = group_col
        self.GLM_dir = GLM_dir

        groups, subjects_per_group = self._GET_Groups(self.df_clin, group_col, self.id_col)
        # print('\nSTEP 1 of 7: making file with subjects')
        # self.make_py_f_subjects(GLM_dir, subjects_per_group)

        # print('\nSTEP 2 of 7: making files for GLM')
        # PrepareForGLM(GLM_dir, file_groups, self.id_col, group_col)

        # print('\nSTEP 3 of 7: making file with structural data')
		from . import database, stats_stats2table

        stats_stats2table.stats2table(database._get_folder_freesurfer(), database._get_subjects_dir(), data_only_volumes=False)
        # xtrctdata2xlsx(freesurfer+'stats/', self.df_clin, self.id_col, GLM_dir, dataf, self.data_big, self.data_subcortical_volumes)

        # print('\nSTEP 4 of 7: making file with statistics')
        # make_descriptions_per_groups(groups, self.concatenate_dataframes('data_for_groups_clin_and_all_structural').copy(),
                                       # group_col, GLM_dir)

        # print('\nSTEP 5 of 7: making file with statistics')
        # mkstatisticsf(self.concatenate_dataframes('data_groups_clin_brain_volumes').copy(), group_col, GLM_dir)

        # print('\nSTEP 6 of 7: distributions')
        # Distributions_Compute_Plot(self.df_clin, group_col, groups, GLM_dir+'results/distributions/', PARAMETER_x_Age, PARAMETERS_INTEREST_y)

        # print('\nSTEP 7 of 7: Correlations for all columns, results/correlations/')
        # for group in groups:
            # df= self.concatenate_dataframes('data_groups_clin_brain_volumes').copy()
            # df= df.drop(df[df[group_col] != group].index)
            # make_correlations_per_group(df, 'data_groups_clin_brain_volumes', group, PARAMETERS_INTEREST_y[-1], GLM_dir+'results/correlations/',
                                        # cor_methods = ('pearson','spearman','kendall',), cor_level_chosen = ['STRONG','MODERATE',])

        # print('\nSTEP 8 of 10: Group Analysis ANOVA and Simple Linear Regression in anova folder')
        # RUN_GroupAnalysis_ANOVA_SimpleLinearRegression(self.concatenate_dataframes('data_groups_clin_brain_volumes').copy(),
                                    # PARAMETERS_INTEREST_y, PARAMETER_x_Age, GLM_dir+'results/anova_linear_regression/plots/',
                                    # GLM_dir+'results/anova_linear_regression/', group_col, id_col)

        # print('\nSTEP 9 of 10: Group Analysis Logistic Regression')
        # from .stats.LogisticRegression import Logistic_Regression
        # Logistic_Regression(self.concatenate_dataframes('data_for_groups_clin_and_all_structural').copy(), group_col,
                            # GLM_dir+'results/logistic_regression/results_clin_all_struct.txt',
                            # GLM_dir+'results/logistic_regression/LogROC_clin_all_struct')
        # Logistic_Regression(self.concatenate_dataframes('data_groups_clin_brain_volumes').copy(), group_col,
                            # GLM_dir+'results/logistic_regression/results_clin_brain_vol.txt',
                            # GLM_dir+'results/logistic_regression/LogROC_clin_brain_vol')
	
        # print('\nSTEP 10 of 10: Group Analysis ICA, PCA classification')
        # from .stats.ICA_PCA import ICA_PCA
        # ICA_PCA(self.concatenate_dataframes('data_for_groups_clin_and_all_structural').copy(), group_col,
                            # GLM_dir+'results/logistic_regression/results_clin_all_struct.txt',
                            # GLM_dir+'results/logistic_regression/LogROC_clin_all_struct')
        # ICA_PCA(self.concatenate_dataframes('data_groups_clin_brain_volumes').copy(), group_col,
                            # GLM_dir+'results/logistic_regression/results_clin_brain_vol.txt',
                            # GLM_dir+'results/logistic_regression/LogROC_clin_brain_vol')

        # print('\nSTEP 11 of 10: Anova and Simple Linear Regression in anova_v2')
        # RUN_ANOVA_SimpleLinearRegression(self.concatenate_dataframes('data_groups_clin_brain_volumes'),
                                    # PARAMETER_x_Age, PARAMETERS_INTEREST_y, df_brain_vol.columns.tolist(),
                                    # GLM_dir+'results/anova_v2/')
        # print('\nSTEP 12 of 10: making plots')
        # RUN_CORRELATIONS_with_stats_stats_pearsonr(study)
        # Z_Scores_create(study)

        # RUN_ANOVA_LinearRegression_Noemie('Oury-Noemie') #Noemie's analysis col 18 is read as text
        print('DONE!')

    def concatenate_dataframes(self, file):
        ls_files = {'data_for_groups_clin_and_all_structural':{'address':self.GLM_dir+'group_clin_all_structural.xlsx',
                                    'concat_with':self.data_big},
                    'data_groups_clin_brain_volumes':{'address':self.GLM_dir+'group_clin_brain_volumes.xlsx',
                                    'concat_with':self.data_subcortical_volumes},}

        df_struct = pd.read_excel(ls_files[file]['concat_with'], sheet_name='stats')
        if not path.isfile(ls_files[file]['address']):
            df_clin_tmp = self.df_clin.copy()
            df_clin_tmp.index = df_clin_tmp[self.id_col]
            df_clin_tmp = df_clin_tmp.drop(columns=[self.id_col])
            frame_clin_struct = (df_clin_tmp, df_struct)
            df_final = pd.concat(frame_clin_struct,axis=1, sort=True)
            print('writing ',ls_files[file]['address'])
            df_final.to_excel(ls_files[file]['address'], sheet_name='data')
        df_final = pd.read_excel(ls_files[file]['address'], sheet_name='data')
        print('df_final from self concatenate: ',df_final.columns.tolist()[:5])
        return df_final

    def Make_Dirs(self, GLM_dir):
        for dir in ['results/','results/distributions/','results/distributions/density/',
                    'results/distributions/scatterplot/','results/correlations/',
                    'results/anova_linear_regression/','results/anova_linear_regression/plots/',
                     'results/logistic_regression/',]:
            if not path.isdir(GLM_dir+dir):
                makedirs(GLM_dir+dir)

    def _GET_Groups(self, df, group_col, id_col):
        groups = []
        subjects_per_group = {}
        for val in df[group_col]:
            if val not in groups:
                groups.append(val)
        for group in groups:
            subjects_per_group[group] = []
            for row in df.index.tolist():
                if df.at[row, group_col] == group:
                        subjects_per_group[group].append(df.at[row, id_col])
        return groups, subjects_per_group

    def make_py_f_subjects(self, GLM_dir, subjects_per_group):
        file = 'subjects_per_group.py'
        open(GLM_dir+file, 'w').close()
        with open(GLM_dir+file, 'a') as f:
            f.write('#!/bin/python/\nsubjects_per_group = {')
            for group in subjects_per_group:
                f.write('\''+group+'\':[')
                for subject in subjects_per_group[group]:
                    f.write('\''+subject+'\',')
                f.write('],')
            f.write('}')

		
# def xtrctdata2xlsx(dirstats, df_clin, id_col, GLM_dir, dataf, data_big, data_subcortical_volumes):
    # '''
    # extracts the data from the data files of each subject and creates the data.xlsx file
    # '''
    # #writing Headers for all sheets
    # print('Writing the Headers for all sheets')
    # from .definitions import (header_brstem, sbrstem, header_hip, 
                                # ship, header_seg, header_mris, 
                                # header_parc2009, svolcurv, sthick, sarea, 
                                # svolcurv2009, sthick2009, sarea2009, smris, 
                                # BrStem_Hip_f2rd, MRIS_columns2extract,
                                # MRIS_sheet_names, MRIS_f2cp, SegParc_f2cp)

    # headerbrstem=pd.DataFrame(header_brstem)
    # headerhip=pd.DataFrame(header_hip)
    # headerseg=pd.DataFrame(header_seg)																		
    # headermris=pd.DataFrame(header_mris)
    # headerparc2009=pd.DataFrame(header_parc2009)
    # headerparc2=pd.DataFrame({'35':['volBrainSegNotVent'],'36':['eTIV']})
    # headerparc3=pd.DataFrame({'35':['meanThickness'],'36':['volBrainSegNotVent'],'37':['eTIV']}) 
    # headerparc4=pd.DataFrame({'35':['whiteSurfArea'],'36':['volBrainSegNotVent'],'37':['eTIV']})
    # headerparc5=pd.DataFrame({'75':['volBrainSegNotVent'],'76':['eTIV']})
    # headerparc6=pd.DataFrame({'75':['meanThickness'],'76':['volBrainSegNotVent'],'77':['eTIV']}) 
    # headerparc7=pd.DataFrame({'75':['whiteSurfArea'],'76':['volBrainSegNotVent'],'77':['eTIV']}) 

    # headervolcurv=pd.merge(headermris,headerparc2, right_index=True, left_index=True)
    # headerthick=pd.merge(headermris,headerparc3, right_index=True, left_index=True)
    # headerarea=pd.merge(headermris, headerparc4, right_index=True, left_index=True)
    # headervolcurv2009=pd.merge(headerparc2009,headerparc5, right_index=True, left_index=True)
    # headerthick2009=pd.merge(headerparc2009,headerparc6, right_index=True, left_index=True)
    # headerarea2009=pd.merge(headerparc2009,headerparc7, right_index=True, left_index=True)

    # writer=pd.ExcelWriter(dataf, engine='xlsxwriter')
    # row=0
    # headerbrstem.to_excel(writer,sheet_name=sbrstem,startcol=1, startrow=row, header=False, index=False) 
    # for sh in ship:
        # headerhip.to_excel(writer,sheet_name=sh,startcol=1, startrow=row, header=False, index=False)
    # headerseg.to_excel(writer,sheet_name='Segmentations',startcol=1, startrow=row, header=False, index=False)
    # for sv in svolcurv:
        # headervolcurv.to_excel(writer,sheet_name=sv,startcol=1, startrow=row, header=False, index=False)
    # for st in sthick:
        # headerthick.to_excel(writer,sheet_name=st,startcol=1, startrow=row, header=False, index=False)
    # for sa in sarea:
        # headerarea.to_excel(writer,sheet_name=sa,startcol=1, startrow=row, header=False, index=False)
    # for sv2009 in svolcurv2009:
        # headervolcurv2009.to_excel(writer,sheet_name=sv2009,startcol=1, startrow=row, header=False, index=False)
    # for st2009 in sthick2009:
        # headerthick2009.to_excel(writer,sheet_name=st2009,startcol=1, startrow=row, header=False, index=False)
    # for sa2009 in sarea2009:
        # headerarea2009.to_excel(writer,sheet_name=sa2009,startcol=1, startrow=row, header=False, index=False)
    # for sm in smris:
        # headermris.to_excel(writer,sheet_name=sm,startcol=1, startrow=row, header=False, index=False)
    # col=0
    # row=1
    # ls_f_stats = listdir(dirstats)
    # print('Writing stats for subjects')
    # for _SUBJECT in df_clin[id_col].tolist():
        # for sheet in BrStem_Hip_f2rd:
            # f_name = _SUBJECT+"_"+BrStem_Hip_f2rd[sheet]
            # if path.isfile(dirstats+f_name):
                # file = dirstats+f_name
            # else:
                # for val in ls_f_stats:
                    # if _SUBJECT in val and BrStem_Hip_f2rd[sheet] in val:
                        # file = dirstats+val
            # if path.exists(file):
                # df=pd.read_table(file)
                # df.loc[-1]=df.columns.values
                # df.index=df.index+1
                # df=df.sort_index()
                # df.columns=['col']
                # df['col'],df[_SUBJECT]=df['col'].str.split(' ',1).str
                # del df['col']
                # df=df.transpose()
                # df.to_excel(writer,sheet_name=sheet, startcol=col, startrow=row, header=False, index=True)
            # else:
                # print('ERROR BrstemHip!!! file '+file+' is missing\n')

        # for sheet in SegParc_f2cp:
            # f_name = _SUBJECT+"_"+SegParc_f2cp[sheet]
            # if path.isfile(dirstats+f_name):
                # file = dirstats+f_name
            # else:
                # for val in ls_f_stats:
                    # if _SUBJECT in val and SegParc_f2cp[sheet] in val:
                        # file = dirstats+val
            # if path.exists(file):
                # f=pd.read_table(file)
                # f.to_excel(writer,sheet_name=sheet,startcol=col, startrow=row, header=False, index=False)
            # else:
                # print('ERROR SerParc!!! file '+file+' is missing\n')

        # for hemisphere in MRIS_f2cp:
            # f_name = _SUBJECT+MRIS_f2cp[hemisphere]
            # if path.isfile(dirstats+f_name):
                # file = dirstats+f_name
            # else:
                # for val in ls_f_stats:
                    # if _SUBJECT in val and MRIS_f2cp[hemisphere] in val:
                        # file = dirstats+val
            # if path.exists(file):
                # line2read = 60
                # line2finish_reading = 94
                # line_with_columns=(linecache.getline(file, line2read-1))
                # while line2read<line2finish_reading:
                    # line=(linecache.getline(file, line2read))
                    # split_line=' '.join(line.split())
                    # with open(dirstats+_SUBJECT+'tmp.txt','a') as f:
                        # f.write(split_line+'\n')
                    # line2read += 1
                # table=pd.read_csv(dirstats+_SUBJECT+'tmp.txt', sep=' ', header=None)
                # table.dropna(axis=1, how='all')
                # table.columns=line_with_columns.split()[2:]
                # table = table[MRIS_columns2extract]
                # for name in MRIS_columns2extract[1:]:
                    # table2=table[[name]]
                    # table2.columns=[_SUBJECT]
                    # table2=table2.transpose()
                    # table2.to_excel(writer,sheet_name=MRIS_sheet_names[name][hemisphere],startcol=col, startrow=row, header=False, index=True)
                # remove(dirstats+_SUBJECT+'tmp.txt')
            # else:
                # print('ERROR MRIS!!! file '+file+' is missing\n')
        # row += 1
    # writer.save()

    # '''CREATING file with Subcortical Volumes and ONE BIG STATS FILE'''
    # print('CREATING file with Subcortical Volumes')
    # columns_2_remove = ['ventricle_5th','wm_hypointensities_L',
                        # 'wm_hypointensities_R','non_wm_hypointensities',
                        # 'non_wm_hypointensities_L','non_wm_hypointensities_R',
                        # 'eTIV']
    
    # def change_column_name(df, sheet):
        # ls = df.columns.tolist()
        # columns_2_drop = []
        # for col in columns_2_remove:
            # if col in ls:
                # columns_2_drop.append(col)
                # ls.remove(col)
            # if sheet != 'Segmentations':
                # if 'volBrainSegNotVent' in ls:
                    # columns_2_drop.append('volBrainSegNotVent')
                    # ls.remove('volBrainSegNotVent')             
        # if len(columns_2_drop)>0:
            # df.drop(columns=columns_2_drop, inplace=True)
        # for col in ls:
            # ls[ls.index(col)] = col+'_'+sheet
        # df.columns = ls
        # return df

    # sheetnames = pd.ExcelFile(dataf).sheet_names

    # df_segmentations = pd.read_excel(dataf, sheet_name='Segmentations')
    # df_final = df_segmentations['eTIV']

    # df_concat = pd.read_excel(dataf, sheet_name=sheetnames[0])
    # df_concat = change_column_name(df_concat, sheetnames[0])

    # for sheet in sheetnames[1:4]:
        # df2 = pd.read_excel(dataf, sheet_name=sheet)
        # df2 = change_column_name(df2, sheet)
        # frames = (df_concat, df2)
        # df_concat = pd.concat(frames, axis=1, sort=True)

    # frame_final = (df_concat, df_final)
    # df_concat = pd.concat(frame_final,axis=1)
	
    # writer = pd.ExcelWriter(data_subcortical_volumes, engine='xlsxwriter')
    # df_concat.to_excel(writer, 'stats')
    # writer.save()
    # print('FINISHED creating file with Subcortical Volumes')
    # print('CREATING One file with all statistics')

    # df_concat = pd.read_excel(dataf, sheet_name=sheetnames[0])
    # df_concat = change_column_name(df_concat, sheetnames[0])

    # for sheet in sheetnames[1:]:
        # df2 = pd.read_excel(dataf, sheet_name=sheet)
        # df2 = change_column_name(df2, sheet)
        # frames = (df_concat, df2)
        # df_concat = pd.concat(frames, axis=1)

    # frame_final = (df_concat, df_final)
    # df_concat = pd.concat(frame_final,axis=1)
	
    # writer = pd.ExcelWriter(data_big, engine='xlsxwriter')
    # df_concat.to_excel(writer, 'stats')
    # writer.save()
    # print('FINISHED creating One file with all statistics')



                
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
                        ttestt, ttestp = stats.ttest_ind(group2compare1,group2compare2) #two-sided test 2 independent samples identical average values
                        anovat, anovap = stats.f_oneway(group2compare1,group2compare2) #One way Anova checks if the variance between the groups is greater then the variance within groups, and computes the probability of observing this variance ratio using F-distribution
                        bartt, bartp = stats.bartlett(group2compare1,group2compare2) #Bartlett’s test tests the null hypothesis that all input samples are from populations with equal variances.
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
                       #pearsoncorr, pearsonp = stats.pearsonr(group2compare1,group2compare2) #Calculates a Pearson correlation coefficient and the p-value for testing non-correlation
                       #spearmancorr, spearmanp = stats.spearmanr(group2compare1,group2compare2) #Calculates a Spearman rank-order correlation coefficient and the p-value to test for non-correlation
                    
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


'''DISTRIBUTIONS AND GROUP DIFFERENCES
Kernel distribution with density estimation and fitting 
parametric distribution to visualize how closely it corresponds to the observed data'''
def Distributions_Compute_Plot(df_clin, group_col, groups, PATH2save_fig, PARAMETER_x_Age, PARAMETERS_INTEREST_y):

    sns_plot_dist_all = sns.distplot(np.array(df_clin[PARAMETER_x_Age]), rug=True, fit=stats.gamma)#fit a parametric distribution
    plt.savefig(PATH2save_fig+'distribution_histo_all.png')
    plt.close()
    for PARAMETER_y in PARAMETERS_INTEREST_y:
        sns_scatterplot_dist_all = sns.jointplot(x=df_clin[PARAMETER_x_Age], y=df_clin[PARAMETER_y], kind='reg')
        sns_scatterplot_dist_all.savefig(PATH2save_fig+'scatterplot/distribution_scatterplot_all_'+PARAMETER_y+'.png')
        plt.close()
        sns_density_dist_all = sns.jointplot(x=df_clin[PARAMETER_x_Age], y=df_clin[PARAMETER_y], kind='kde')
        sns_density_dist_all.savefig(PATH2save_fig+'density/distribution_density_all_'+PARAMETER_y+'.png')
        plt.close()

    for group in groups:
        sns_plot_dist = sns.distplot(np.array(df_clin[df_clin[group_col] == group][PARAMETER_x_Age]), rug=True, fit=stats.gamma)#fit a parametric distribution
        plt.savefig(PATH2save_fig+'distribution_histo_'+group+'.png')
        plt.close()
        for PARAMETER_y in PARAMETERS_INTEREST_y:
            sns_scatterplot_dist = sns.jointplot(x=df_clin[df_clin[group_col] == group][PARAMETER_x_Age], y=df_clin[df_clin[group_col] == group][PARAMETER_y], kind='reg')
            sns_scatterplot_dist.savefig(PATH2save_fig+'scatterplot/distribution_scatterplot_'+group+'_'+PARAMETER_y+'.png')
            plt.close()
            sns_density_dist = sns.jointplot(x=df_clin[df_clin[group_col] == group][PARAMETER_x_Age], y=df_clin[df_clin[group_col] == group][PARAMETER_y], kind='kde')
            sns_density_dist.savefig(PATH2save_fig+'density/distribution_density_'+group+'_'+PARAMETER_y+'.png')
            plt.close()


	
		
'''
======================================
======================================
Correlations
======================================
======================================'''

'''I. CORRELATION for each group'''

def make_correlations_per_group(df, file, group, last_value_2_correlate, PATH2save_res, cor_methods, cor_level_chosen):
    '''creating files with descriptions and correlations of each sheet (groups, df, group_col, GLM_dir)'''

    print('writing correlation sheet, group: ',group)
    cor_levels_and_thresholds = {'STRONG': {'minim':0.7,'maxim':1}, 'MODERATE': {'minim':0.5,'maxim':0.7}, 'WEAK': {'minim':0.3,'maxim':0.5}}
    cor_methods_2_analyse = []
    frame = [{'Correlation':'0', 'Region1':'0', 'Region2':'0', 'Value':'0'}]
    results_df = pd.DataFrame(frame)
    for cor_method_chosen in cor_methods:
        cor_methods_2_analyse.append(cor_method_chosen)


    for cor in cor_methods_2_analyse:
        writer = pd.ExcelWriter(PATH2save_res+'cor_'+file+'_'+group+'_'+cor+'.xlsx', engine='xlsxwriter')
        df_cor = df.corr(method=cor)
        df_cor.to_excel(writer, 'correlation')
        df_cor05 = df.corr(method=cor)>0.5
        df_cor05.to_excel(writer, 'correlation_r07')
        df_cor07 = df.corr(method=cor)>0.7
        df_cor07.to_excel(writer, 'correlation_r08')
        writer.save()
        # df_cor.to_csv(PATH2save_res+'cor_'+file+'_'+group+'_'+cor+'.csv', encoding='utf-8', index=True)
        nr_row_2_start = 0
        df_row = 0
        for cor_level in cor_level_chosen:
            cor_thresholds = cor_levels_and_thresholds[cor_level]
            for nr_col in range(0, df_cor.columns.tolist().index(last_value_2_correlate)+1):
                for nr_row in range(nr_row_2_start, len(df_cor.iloc[nr_col])):
                    if df_cor.iloc[nr_col, nr_row] > cor_thresholds['minim'] and df_cor.iloc[nr_col, nr_row]< cor_thresholds['maxim']:
                        cor_type = cor_level+' POSITIVE'
                    elif df_cor.iloc[nr_col, nr_row] < -cor_thresholds['minim'] and df_cor.iloc[nr_col, nr_row]> -cor_thresholds['maxim']:
                        cor_type = cor_level+' NEGATIVE '
                    else:
                        cor_type = 0
                    if cor_type != 0:
                        results_df.at[df_row, 'Correlation'] = cor_type
                        results_df.at[df_row, 'Region1'] = df_cor.columns[nr_col]
                        results_df.at[df_row, 'Region2'] = df_cor.index[nr_row]
                        results_df.at[df_row, 'Value'] = str(df_cor.iloc[nr_col, nr_row])
                        df_row += 1
                nr_row_2_start += 1
            results_df = results_df.sort_values(by=['Region1'])#or 'Correlation'
            print('saving: ','cor_res_'+file+'_'+group+'_'+cor+'_'+cor_level+'.csv')
            results_df.to_csv(PATH2save_res+'cor_res_'+file+'_'+group+'_'+cor+'_'+cor_level+'.csv', encoding='utf-8', index=False)
    print('FINISHED creating correlation file for group:', group)
    # mkstatisticsfplots(GLM_dir+'results/plots_correlations_subcort_vol/', groups_dataf, df_clin, self.id_col, group_col)
    



#http://hamelg.blogspot.com/2015/11/python-for-data-analysis-part-16_23.html
'''
======================================
======================================
GROUP ANALYSIS: ANOVA & SIMPLE LINEAR REGRESSION
======================================
======================================

if cor with education in ALL SUBJECTS:
       if ttest differences between the groups:
           ANOVA education+Age region significant'''
def get_structure_measurement(col_y):
    print(col_y)
    for meas in name_measurement:
        if meas in col_y:
            measurement = meas
            break
        elif 'eTIV' in col_y:
            measurement = 'eTIV'
    for struct in name_structure:
        if struct in col_y:
            structure = struct
            break
        elif 'eTIV' in col_y:
            structure = 'eTIV'
    print('results: ',measurement, structure)
    return measurement, structure

def Make_plot_group_difference(data_groups_anova, col, measurement, structure, PATH2save_plots, name_img_bars_diff, group_col):
    groups = _GET_Groups(data_groups_anova, group_col)
    df = pd.DataFrame({'Groupe':data_groups_anova[group_col],\
                  groups[0]:data_groups_anova[data_groups_anova[group_col] == groups[0]][col],\
                  groups[1]:data_groups_anova[data_groups_anova[group_col] == groups[1]][col]})
    df = df[['Groupe',groups[0],groups[1]]]
    dd=pd.melt(df,id_vars=['Groupe'],value_vars=[groups[0],groups[1]],var_name=col)
    group_plot = sns.boxplot(x='Groupe',y='value',data=dd,hue=col)
    group_plot.figure.savefig(PATH2save_plots+structure+'_'+measurement+name_img_bars_diff)
    plt.close()
def Make_Plot_Regression(data_groups_anova, col, parameter,model, measurement, structure, PATH2save_plots, group_col):
    df_plot = pd.DataFrame({
        'Groupe':np.array(data_groups_anova[group_col]),
        parameter:np.array(data_groups_anova[parameter]),
        col:np.array(data_groups_anova[col])})
    sns_plot = sns.lmplot(x=parameter, y=col,hue='Groupe', data=df_plot)#, robust=True
    axes = sns_plot.axes.flatten()
    axes[0].set_title('Groupe diff. p='+str('%.4f'%model.pvalues.x)+'; intercept='+str('%.4f'%model.pvalues.Intercept))
    sns_plot.savefig(PATH2save_plots+structure+'_'+measurement+'_'+parameter+'regression.png')
    plt.close()   
def Make_csv_results(model,parameter,measurement):
    d = {}
    res = model.pvalues
    posthoc1min1 = model.f_test([1,-1])
    d[measurement] = measurement
    d['Intercept'] = '%.4f'%res.Intercept
    d[parameter] = '%.4f'%res.x
    d['vs_'+parameter] = str('%.4f'%posthoc1min1.pvalue)
    return d
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
def _GET_Groups(df, group_col):
    groups = []
    for val in df[group_col]:
        if val not in groups:
            groups.append(val)
    return groups

def RUN_GroupAnalysis_ANOVA_SimpleLinearRegression(df_main, PARAMETERS_INTEREST_y, PARAMETER_x_Age, PATH2save_plots, PATH2save_anova, group_col, id_col):
    ls_brain_regions = df_main.columns.tolist()
    for param in PARAMETERS_INTEREST_y+[group_col, id_col, PARAMETER_x_Age]:
        if param in ls_brain_regions:
            ls_brain_regions.remove(param)
    name_img_bars_diff = '_grp.png'

    result_csv = {}
    for PARAMETER in PARAMETERS_INTEREST_y:
        x = np.array(df_main[PARAMETER])
        for col in ls_brain_regions:
            #res_ttest_sig = Compute_ttest_for_col(col)
            y = np.array(df_main[col])
            data_tmp = pd.DataFrame({'x':x,col:y})
            model = ols(col+" ~ x", data_tmp).fit()
            if model.pvalues.Intercept < 0.05 and model.pvalues.x < 0.05:
                measurement, structure = get_structure_measurement(col)
                if structure+'_'+measurement+name_img_bars_diff not in listdir(PATH2save_anova):
                    Make_plot_group_difference(df_main, col, measurement, structure, PATH2save_plots, name_img_bars_diff, group_col)
                Make_Plot_Regression(df_main, col,PARAMETER,model, measurement, structure, PATH2save_plots, group_col)
                result_csv[structure] = Make_csv_results(model,PARAMETER,measurement)
            # print(len(ls_brain_regions[ls_brain_regions.index(col):]),'structures left to analyse')    
        df_anova = pd.DataFrame.from_dict(result_csv)
        df_transpose = df_anova.transpose()
        df_transpose.to_csv(PATH2save_anova+'anova_groups_'+PARAMETER+'.csv')
		
		
	
		
		
		
		
		
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
    df_transpose.to_csv(PATH2save_anova+'anova_'+parameter+'.csv')

	
def RUN_ANOVA_SimpleLinearRegression(data_anova, PARAMETER_x_Age, PARAMETERS_INTEREST_y, ls_struct_cols, PATH2save_anova):
    Make_Dirs(PATH2save_anova)

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








































































'''Standardizing DATA, transforming in z-score (z-value=(x-mean)/sd)
clinical values are z scores, structural are raw scores'''
def Z_Scores_create():
    #Alternatively use the scikit feature to create z-values
    #http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html
    #sklearn.preprocessing.StandardScaler.fit_transform
    #dfz_sk = pd.read_excel(path+'tmp.xlsx', sheetname='Sheet1')
    #from sklearn import preprocessing

    #scaler= preprocessing.StandardScaler()

    #dfz_prep = pd.DataFrame(scaler.fit_transform(dfz_sk.T), columns=dfz_sk.columns, index=dfz_sk.index)
    dfzvalues = df_all_data.copy(deep=True) #code from Jonathan Eunice, stockoverflow
    columns_2_drop = ['subject','Age','group','Duration_of_Disease','Edu_years_completed']
    df_with_nonchanged_data = dfzvalues[columns_2_drop]
    dfzvalues.drop(columns=columns_2_drop, inplace=True)
    writer = pd.ExcelWriter(PATH_to_save_results+'materials_all_data_zvalues.xlsx', engine='xlsxwriter')

    for col in dfzvalues.select_dtypes([np.number]):
        col_mean = dfzvalues[col].mean()
        col_std = dfzvalues[col].std()
        dfzvalues[col] = dfzvalues[col].apply(lambda x: (x-col_mean) / col_std)

    frame_final = (df_with_nonchanged_data, dfzvalues)
    dfzvalues = pd.concat(frame_final,axis=1)
    dfzvalues.to_excel(writer)
    writer.save()









'''II: CORRELATIONS: ASSESS THE PRESENCE OF CORRELATION between COL and PARAMETER'''
def RUN_Correlate(x,y):
    res = {}
    cor = stats.stats.pearsonr(x,y)
    if cor[1] <0.05:
        if cor[0] > 0:
            cor_type = 'pos'
        else:
            cor_type = 'neg'
        res['correlation'] = cor_type
    res['r'] = cor[0]
    res['p'] = cor[1]
    return res



def update_dataframe(df,res_correlate,col_x,measurement, structure):
    ls = df['structure'].tolist()
    if structure in ls:
        df_row = ls.index(structure)
        #df.at[df_row, measurement] = measurement
        #df.at[df_row, 'cor_'+measurement] = res_correlate['correlation']
        #df.at[df_row, 'r_'+measurement] = str(res_correlate['r'])
        df.at[df_row, measurement+'_p'] = str(res_correlate['p'])
    else:
        if len(df.iloc[0]['Clinical_Variable']) == 1:
            df_row = 0
        else:
            df_row = len(ls)+1
        df.at[df_row, 'Clinical_Variable'] = col_x
        df.at[df_row, 'structure'] = structure
        #df.at[df_row, measurement] = measurement
        #df.at[df_row, 'cor_'+measurement] = res_correlate['correlation']
        #df.at[df_row, 'r_'+measurement] = str(res_correlate['r'])
        df.at[df_row, measurement+'_p'] = str(res_correlate['p'])
    return df

def RUN_CORRELATIONS_with_stats_stats_pearsonr():
    groups = _GET_Groups(study)
    ls_cols, first_clin_col_index, last_clin_col_index, first_struct_col_index, last_struct_col_index = _GET_df_Parameters(study)	
    df_main =_GET_df(study)
    group_col = _get_definitions(study, 'group_col')
    data_cor =df_main.copy()
    name_file_all = 'v1res_cor_all_'
    name_file_group = 'v1res_cor_'

    frame = [{'Clinical_Variable':'0', 'structure':'0',}]
    results_df = pd.DataFrame(frame)
    results_df_all = results_df

    f_per_group = {}
    for group in groups:
        f_per_group[group] = []
    f_per_group['all'] = []

    for col_x in ls_cols[first_clin_col_index+1:last_clin_col_index+1]:
        d_groups_2_analyze = {}
        for group in groups:
                x = np.array(df_main[df_main[group_col] == group][col_x])
                for val in x:
                    if val != 0:
                        d_groups_2_analyze[group] = True
                        break
                    else:
                        d_groups_2_analyze[group] = False
        d_groups_2_analyze['all'] = True
        for group in d_groups_2_analyze:
            if d_groups_2_analyze[group] == False:
                d_groups_2_analyze['all'] = False
                break
        if d_groups_2_analyze['all'] == True:
            x = np.array(data_cor[col_x])
            df_row = 0
            for col_y in ls_cols[first_struct_col_index:last_struct_col_index+1]:
                y = np.array(data_cor[col_y])
                res_correlate = RUN_Correlate(x,y)
                if res_correlate['p'] <0.05:
                    #measurement, structure = get_structure_measurement(col_y)
                    #results_df_all = update_dataframe(results_df_all,res_correlate,col_x,measurement, structure)
                    #results_df_all.at[df_row, 'Correlation'] = res_correlate['Correlation']
                    results_df_all.at[df_row, 'Clinical_Variable'] = col_x
                    results_df_all.at[df_row, 'structure'] = col_y
                    results_df_all.at[df_row, 'r'] = str(res_correlate['r'])
                    results_df_all.at[df_row, 'p'] = str(res_correlate['p'])
                    df_row += 1        
            results_df_all = results_df_all.sort_values(by=['Clinical_Variable'])
            results_df_all.to_csv(PATH2save_fig+name_file_all+col_x.replace('/','-')+'.csv', encoding='utf-8', index=False)
            f_per_group['all'].append(PATH2save_fig+name_file_all+col_x.replace('/','-')+'.csv')
        else:
            pass

        for group in groups:
            if d_groups_2_analyze[group] == True:
                results_df_group = results_df.copy(deep=True)
                x = np.array(data_cor[data_cor[group_col] == group][col_x])
                df_row = 0
                for col_y in ls_cols[first_struct_col_index:last_struct_col_index+1]:
                    y = np.array(data_cor[data_cor[group_col] == group][col_y])
                    res_correlate = RUN_Correlate(x,y)
                    if res_correlate['p'] <0.05:
                        #measurement, structure = get_structure_measurement(col_y)
                        #results_df_group = update_dataframe(results_df_group,res_correlate,col_x,measurement, structure)
                        #results_df_group.at[df_row, 'Correlation'] = res_correlate['Correlation']
                        results_df_group.at[df_row, 'Clinical_Variable'] = col_x
                        results_df_group.at[df_row, 'structure'] = col_y
                        results_df_group.at[df_row, 'r'] = str(res_correlate['r'])
                        results_df_group.at[df_row, 'p'] = str(res_correlate['p'])
                        df_row += 1            
                if len(results_df_group.iloc[0]['Clinical_Variable']) > 1:
                    results_df_group = results_df_group.sort_values(by=['Clinical_Variable'])
                    results_df_group = results_df_group.sort_values(by=['structure'])
                    results_df_group.to_csv(PATH2save_fig+name_file_group+group+'_'+col_x.replace('/','-')+'.csv', encoding='utf-8', index=False)
                    f_per_group[group].append(PATH2save_fig+name_file_group+group+'_'+col_x.replace('/','-')+'.csv')


    for group in f_per_group:
        if len(f_per_group[group])>0:
            writer = pd.ExcelWriter(PATH2save_fig+'res_'+group+'.xlsx', engine='xlsxwriter')
            df_concat = pd.read_csv(f_per_group[group][0])   
            for file in f_per_group[group][1:]:
                df2 = pd.read_csv(file)
                frames = (df_concat, df2)
                df_concat = pd.concat(frames, axis=0)
        
            df_concat = df_concat.sort_values(by=['Clinical_Variable','structure'])
            #for file in f_per_group[group]:
            #    remove(file)

        df_concat.to_excel(writer, 'correlations')
        writer.save()
    print('DONE')

'''TO DO
in df sometimes the z-scores are 'text' and cannot be read in np.array -> maybe when creating the data_for_analysis.xlsx, to check if values are int
correction eTIV
groups sans CEGEP

cor avec education
effet age par edu (age x edu)

quand il y a un effet, on fait un split dans 2 groups.

interaction entre age + edu

quelle est la raison de faire deux groups ?

not group but age

concentrate on x=age, y=total gray vol
Age effect ANOVA ?

- cor age/structurelle

http://www.statsmodels.org/devel/examples/notebooks/generated/regression_plots.html#Partial-Regression-Plots
https://stackoverflow.com/questions/30948997/evaluate-slope-and-error-for-specific-category-for-statsmodels-ols-fit
https://www.dummies.com/programming/big-data/data-science/data-science-how-to-create-interactions-between-variables-with-python/
https://blog.datarobot.com/multiple-regression-using-statsmodels
https://blog.datarobot.com/ordinary-least-squares-in-python
https://stackoverflow.com/questions/22054964/ols-regression-scikit-vs-statsmodels
https://stackoverflow.com/questions/34276686/prediction-plots-for-statsmodels-ols-fit-taking-out-categorical-effects
'''

# X = np.linspace(-5.0, 5.0, 100)
# plt.title('Normal distribution')
# histd1 = np.histogram(d1, bins =100)
# hist_distd1 = stats.rv_histogram(histd1)
# plt.hist(d1, normed = True, bins = 100)
# #plt.plot(X, hist_distd1.pdf(X), label = 'PDF')
# #plt.plot(X, hist_distd1.cdf(X), label = 'CDF')
# plt.show()



# X = np.linspace(-5.0, 5.0, 100)
# plt.title("PDF from Template")
# data = scipy.stats.norm.rvs(size=100000, loc=0, scale=1.5, random_state=123)
# histdata = np.histogram(data, bins=100)
# hist_distdata = scipy.stats.rv_histogram(histdata)
# plt.hist(data, normed=True, bins=100)
# plt.plot(X, hist_distdata.pdf(X), label='PDF')
# plt.plot(X, hist_distdata.cdf(X), label='CDF')
# plt.show()






class PrepareForGLM():

    #https://surfer.nmr.mgh.harvard.edu/fswiki/FsgdExamples
    def __init__(self, path_save_fsgd, file_clinical_data, id_col, group_col):
        self.PATH = path_save_fsgd
        self.PATHfsgd = self.PATH+'fsgd/'
        self.PATHmtx = self.PATH+'contrasts/'
        Make_Dirs(self.PATHfsgd)
        Make_Dirs(self.PATHmtx)
        print(self.PATHfsgd)
        shutil.copy(file_clinical_data, self.PATH+file_clinical_data[file_clinical_data.rfind('/')+1:])
        self.group_col = group_col
        d_init = pd.read_excel(file_clinical_data, sheet_name = 'data').to_dict()
        self.d_subjid = {}
        ls_all_vars = [key for key in d_init if key != id_col]
        self.ls_groups = []
        for rownr in d_init[id_col]:
            id = d_init[id_col][rownr]
            self.d_subjid[id] = {}
            for key in ls_all_vars:
                self.d_subjid[id][key] = d_init[key][rownr]
        for id in self.d_subjid:
            if self.d_subjid[id][group_col] not in self.ls_groups:
                self.ls_groups.append(self.d_subjid[id][group_col])
        self.ls_vars_stats = ls_all_vars
        self.ls_vars_stats.remove(group_col)

        self.contrasts = {'g1v1':{'slope.mtx':['0 1','t-test with the slope>0 being positive; is the slope equal to 0? does the correlation between thickness and variable differ from zero ?',],},
            'g2v0':{'group.diff.mtx':['1 -1','t-test with Group1>Group2 being positive; is there a difference between the group intercepts? Is there a difference between groups?',],},
            'g2v1':{'group.diff.mtx':['1 -1 0 0','t-test with Group1>Group2 being positive; is there a difference between the group intercepts? Is there a difference between groups regressing out the effect of age?',],'group-x-var.mtx':['0 0 1 -1','t-test with Group1>Group2 being positive; is there a difference between the group age slopes? Note: this is an interaction between group and age. Note: not possible to test with DOSS',],
                    'g1g2.var.mtx':['0 0 0.5 0.5','This is a t-test with (Group1+Group2)/2 > 0 being positive (red/yellow). If the mean is < 0, then it will be displayed in blue/cyan; does mean of group age slope differ from 0? Is there an average affect of age regressing out the effect of group?',],}}
        # contrasts_not_used = 
                # {'g1v0':{'intercept.mtx':['1','t-test with the intercept>0 being positive; is the intercept/mean equal to 0?',],},
                # 'g1v1':{'intercept.mtx':['1 0','t-test with the intercept>0 being positive; is the intercept equal to 0? Does the average thickness differ from zero ?',],},
                # 'g1v2':{'main.mtx':['1 0 0','t-test with offset>0 being positive; the intercept/offset is different than 0 after regressing out the effects of var1 and var2',],'var1.mtx':['0 1 0','t-test with var1 slope>0 being positive',],'var2.mtx':['0 0 1','t-test with var2 slope>0 being positive',],},
                # 'g2v0':{'group1.mtx':['1 0','t-test with Group1>0 being positive; is there a main effect of Group1? Does the mean of Group1 equal 0?',],'group2.mtx':['0 1','t-test with Group2>0 being positive; is there a main effect of Group2? Does the mean of Group2 equal 0?',],'g1g2.intercept.mtx':['0.5 0.5','t-test with (Group1+Group2)/2 > 0 being positive (red/yellow). If the mean is < 0, then it will be displayed in blue/cyan; does mean of the group means differ from 0?',],}
                # 'g2v1':{'g1g2.intercept.mtx':['0.5 0.5 0 0','t-test with (Group1+Group2)/2 > 0 being positive (red/yellow). If the mean is < 0, then it will be displayed in blue/cyan; does mean of group intercepts differ from 0? Is there an average main effect regressing out age?',]},}
        gd2 = {'g1v1':['dods',],'g2v0':['doss','dods',],'g2v1':['dods',],}#gd2_not_used = {'g1v0':['dods',],'g1v2':['dods',],}
        self.files_glm = {}
        for contrast_type in self.contrasts:
            self.files_glm[contrast_type]={}
            self.files_glm[contrast_type]['fsgd'] = []
            self.files_glm[contrast_type]['mtx'] = []
            self.files_glm[contrast_type]['mtx_explanation'] = []
            self.files_glm[contrast_type]['gd2mtx'] = gd2[contrast_type]

        print('creating fsgd for g1g2v0')
        self.make_fsgd_g1g2v0()
        print('creating fsgd for g1v1')
        self.make_fsgd_g1v1()
        print('creating fsgd for g1v2')
        # self.make_fsgd_g1v2()
        # print('creating fsgd for g2v1')
        self.make_fsgd_g2v1()
        print('creating contrasts')
        self.make_contrasts()
        print('creating py file with all data')
        self.make_py_f()
        print('creating qdec fsgd files')
        self.make_qdec_fsgd_g2()

    def make_fsgd_g1g2v0(self):
        file = 'g2v0'+'_'+self.ls_groups[0]+'_'+self.ls_groups[1]+'.fsgd'
        open(self.PATHfsgd+file, 'w').close()
        with open(self.PATHfsgd+file, 'a') as f:
            f.write('GroupDescriptorFile 1\nClass '+self.ls_groups[0]+' plus blue\nClass '+self.ls_groups[1]+' circle green\n')
            for subjid in self.d_subjid:
                f.write('Input '+subjid+' '+self.d_subjid[subjid][self.group_col]+'\n')
        self.files_glm['g2v0']['fsgd'].append(file)
        # for group in self.ls_groups:
            # file = 'g1v0'+'_'+group+'.fsgd'
            # open(self.PATHfsgd+file, 'w').close()
            # with open(self.PATHfsgd+file, 'a') as f:
                # f.write('GroupDescriptorFile 1\nClass Main\n')
                # for subjid in self.d_subjid:
                    # if self.d_subjid[subjid][self.group_col] == group:
                        # f.write('Input '+subjid+' Main\n')
            # self.files_glm['g1v0']['fsgd'].append(file)

    def check_var_zero(self, var, group):
        ls = []
        for subjid in self.d_subjid:
            if self.d_subjid[subjid][self.group_col] == group:
                ls.append(self.d_subjid[subjid][var])
        return all(v == 0 for v in ls)
            
    def make_fsgd_g1v1(self):
        for group in self.ls_groups:
            for variable in self.ls_vars_stats:
                if not self.check_var_zero(variable, group):
                    file = 'g1v1'+'_'+group+'_'+variable+'.fsgd'
                    open(self.PATHfsgd+file, 'w').close()
                    with open(self.PATHfsgd+file, 'a') as f:
                        f.write('GroupDescriptorFile 1\nClass Main\nVariables '+variable+'\n')
                        for subjid in self.d_subjid:
                            if self.d_subjid[subjid][self.group_col] == group:
                                f.write('Input '+subjid+' Main '+str(self.d_subjid[subjid][variable])+'\n')
                    self.files_glm['g1v1']['fsgd'].append(file)


    def make_fsgd_g1v2(self):
        for group in self.ls_groups:
            for variable in self.ls_vars_stats[:-1]:
                if not self.check_var_zero(variable, group):
                    for variable2 in self.ls_vars_stats[self.ls_vars_stats.index(variable)+1:]:
                        if not self.check_var_zero(variable2, group):
                            file = 'g1v2'+'_'+group+'_'+variable+'_'+variable2+'.fsgd'
                            open(self.PATHfsgd+file, 'w').close()
                            with open(self.PATHfsgd+file, 'a') as f:
                                f.write('GroupDescriptorFile 1\nClass Main\nVariables '+variable+' '+variable2+'\n')
                                for subjid in self.d_subjid:
                                    if self.d_subjid[subjid][self.group_col] == group:
                                        f.write('Input '+subjid+' Main '+str(self.d_subjid[subjid][variable])+' '+str(self.d_subjid[subjid][variable2])+'\n')
                            self.files_glm['g1v2']['fsgd'].append(file)

    def make_fsgd_g2v1(self):
        for variable in self.ls_vars_stats:
            if not self.check_var_zero(variable, self.ls_groups[0]) and not self.check_var_zero(variable, self.ls_groups[1]):
                file = 'g2v1'+'_'+self.ls_groups[0]+'_'+self.ls_groups[1]+'_'+variable+'.fsgd'
                open(self.PATHfsgd+file, 'w').close()
                with open(self.PATHfsgd+file, 'a') as f:
                    f.write('GroupDescriptorFile 1\nClass '+self.ls_groups[0]+' plus blue\nClass '+self.ls_groups[1]+' circle green\nVariables ')
                    f.write(variable+'\n')
                    for subjid in self.d_subjid:
                        f.write('Input '+subjid+' '+self.d_subjid[subjid][self.group_col]+' '+str(self.d_subjid[subjid][variable])+'\n')
                self.files_glm['g2v1']['fsgd'].append(file)

    def make_qdec_fsgd_g2(self):
        file = 'qdec_g2.fsgd'
        open(self.PATH+file, 'w').close()
        with open(self.PATH+file, 'a') as f:
            f.write('fsid group ')
            for variable in self.ls_vars_stats:
                if not self.check_var_zero(variable, self.ls_groups[0]) and not self.check_var_zero(variable, self.ls_groups[1]):
                    f.write(variable+' ')
            f.write('\n')
            for id in self.d_subjid:
                f.write(id+' '+self.d_subjid[id][self.group_col]+' ')
                for variable in self.ls_vars_stats:
                    f.write(self.d_subjid[id][variable]+' ')
                f.write('\n')

    def make_contrasts(self):
        for contrast_type in self.contrasts:
            for contrast_name in self.contrasts[contrast_type]:
                file = contrast_type+'_'+contrast_name
                open(self.PATHmtx+file, 'w').close()
                with open(self.PATHmtx+file, 'a') as f:
                    f.write(self.contrasts[contrast_type][contrast_name][0])
                self.files_glm[contrast_type]['mtx'].append(file)
                self.files_glm[contrast_type]['mtx_explanation'].append(self.contrasts[contrast_type][contrast_name][1])



    def make_py_f(self):
        file = 'files_for_glm.py'
        open(self.PATH+file, 'w').close()
        with open(self.PATH+file, 'a') as f:
            f.write('#!/bin/python/\nfiles_for_glm = {')
            for contrast_type in self.files_glm:
                f.write('\''+contrast_type+'\':{')
                for group in self.files_glm[contrast_type]:
                    f.write('\''+group+'\':[')
                    for value in self.files_glm[contrast_type][group]:
                        f.write('\''+value+'\',')
                    f.write('],')
                f.write('},')
            f.write('}')

			
			
			
			
			
			
'''
==============================================================
PROBABLY NOT NEEDED OR NEED ADJUSTMENTS
==============================================================
==============================================================
'''



def mkstatisticsfplots(PATHplots, datagroup, groupsfromf, id_col, group_col):
    #correlations must be made between clinical and structural, only abalon.
    Make_Dirs(PATHplots)
    sns.set()

    tmpdataf = pd.ExcelFile(datagroup)
    sheetnames = (tmpdataf.sheet_names)
    # groupsfromf = pd.read_excel(groupsf, sheet_name='foranalysis')
    groupsfromf.drop(id_col, axis = 1, inplace = True)

    def plotkde(datasheet, sheet):
        print('creating kde plot for sheet '+sheet)
        scatterpd = pd.plotting.scatter_matrix(datasheet, diagonal = 'kde')
        plt.savefig(PATHplots+'kde-'+sheet+'.png')
        plt.cla()

    def correlation_matrix(df, sheet, headers):
        from matplotlib import cm as cm
        print('creating abalone plot for sheet '+sheet)

        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        cmap = cm.get_cmap('jet', 30)
        cax = ax1.imshow(df.corr(), interpolation="nearest", cmap=cmap)
        ax1.grid(True)
        plt.title(sheet+' Abalone Feature Correlation')
        labels=headers
        ax1.set_xticklabels(labels,fontsize=5)
        ax1.set_yticklabels(labels,fontsize=5)
        # Add colorbar, make sure to specify tick locations to match desired ticklabels
        fig.colorbar(cax, ticks=[.75,.8,.85,.90,.95,1])
        plt.savefig(PATHplots+'abalone'+sheet+'.png', dpi = 150)
        plt.cla()

    def plotggplot(datasheet, sheet, group_col):
        plt.style.use('ggplot') #    matplotlib.style.use('ggplot')
        df = pd.concat([datasheet, groupsfromf], axis=1)
        print('creating ggplot for sheet '+sheet)
        print(df.columns.tolist())
        sns_plot = sns.pairplot(df, hue=group_col, height=2.5)
        sns_plot.savefig(PATHplots+"ggplot"+sheet+".png")
		
    '''
    based on the data.xlsx files create plots-scatter.xls file with statistical results for groups
    '''

    print('Creating the kde scatter plots and the abalone plots with statistical results for groups')
	
    for sheet in sheetnames[:3]:
        datasheet = pd.read_excel(datagroup, sheet_name=sheet)
        headers = datasheet.columns.values.tolist()
        if sheet == 'Segmentations':
            datasheet.drop(['5th-Ventricle',
			'Left-WM-hypointensities',
			'Right-WM-hypointensities',
			'non-WM-hypointensities',
			'Left-non-WM-hypointensities',
			'Right-non-WM-hypointensities'], axis=1, inplace=True)
        plotkde(datasheet, sheet)
        correlation_matrix(datasheet, sheet, headers)
        # plotggplot(datasheet, sheet, group_col)
