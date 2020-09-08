from os import environ, path, chdir, system
import sys
import time

from setup.get_vars import SetProject
from stats import (db_processing, preprocessing, predict, varia, linear_regression_moderation, stats_LogisticRegression, stats_laterality)
from stats.stats_groups_anova import RUN_GroupAnalysis_ANOVA_SimpleLinearRegression

class RUN_stats():
    """will run statistical analysis for the provided groups file"""

    def __init__(self, vars_local, projects, project):


        All_Steps               = False
        STEP1_Make_Files        = False
        STEP_LinRegModeration   = False
        STEP_Anova_SimpLinReg   = False
        STEP_LogisticRegression = False
        STEP_Laterality         = True
        STEP_Predict_RF_SKF     = False
        STEP_Predict_RF_LOO     = False
        STEP_get_param_based_db = False

        paths = projects[project]
        nimb_stats = SetProject(vars_local['NIMB_PATHS']['NIMB_tmp'], vars_local['STATS_PATHS'], project).STATS_PATHS
        print(nimb_stats)



        params = {'group_param': 'education',
                'regression_param': 'age',
                'cog_param':'moca',
                'y':['education','moca',],
                'other_params':['Code Labo','SCANNER','NB de cannaux','Code_SCAN','Année_SCAN',],}
        f_source = path.join("source", "0.data_main_from_samira_20180614.xlsx")
        f_data_clinical = paths['GLM_file_group']#"0.data_clinical_"+date+".xlsx"
        f_CoreTIVNaNOut = "2.data_FS_eTIVNaNOutcor_"
        atlas = ('DK','DS','DKDS')[1]
        atlas_sub = 'Subcort'
        atlas_DK = 'DK'
        atlas_DS = 'DS'
        f_subcort    = path.join(paths['materials_DIR'][1], f_CoreTIVNaNOut+atlas_sub+'_'+date+'.xlsx')
        f_atlas_DK   = path.join(paths['materials_DIR'][1], f_CoreTIVNaNOut+atlas_DK+'_'+date+'.xlsx')
        f_atlas_DS   = path.join(paths['materials_DIR'][1], f_CoreTIVNaNOut+atlas_DS+'_'+date+'.xlsx')
        groups_all = ['high_school', 'bac']
        # sex 1=male, 2=female
        feature_algo = 'PCA' #'RFE'
        prediction_vars = {"target" : paths['group_col'], 'pca_threshold':0.5, 'skf_NUM_ITER': 150, 'NUM_ITER': 10, "nr_threads" : 15}
        cor_methods = ('pearson','spearman','kendall',)
        cor_level_chosen = ['STRONG','MODERATE','WEAK']
        # VARIABLES end ===============================================

    def run_stats(self):
        # TABLES get for stats start ===============================================
        df_clin = db_processing.get_df(path.join(paths['materials_DIR'][1], paths['GLM_file_group']),
                                    usecols=[paths['id_col'], paths['group_col'], 'education', 'age', 'moca'],
                                    index_col = paths['id_col'])
        groups = preprocessing.get_groups(df_clin, paths['group_col'], groups_all)
        df_sub_and_cort, ls_cols_X_atlas = preprocessing.get_df(f_subcort, f_atlas_DK, f_atlas_DS,
                                                         atlas, paths['id_col'])
        df_clin_atlas = db_processing.join_dfs(df_clin, df_sub_and_cort, how='outer')
        # TABLES get for stats  end ===============================================


        # stats = predict.get_stats_df(len(ls_cols_X_atlas), atlas,
        #                             prediction_vars['nr_threads'], 
        #                             definitions.sys.platform,
        #                             time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))

    # analyses per GROUP and for ALL participants
        for group in groups + ['all',]: #'all' stands for all participants
            df_X, y_labeled, X_scaled, df_clin_group = get_X_data_per_group_all_groups(group)
            if feature_algo == 'PCA':# using PCA
                features = predict.get_features_based_on_pca(varia.get_dir(path.join(nimb_stats['STATS_HOME'], nimb_stats['features'])),
                                                    prediction_vars['pca_threshold'],
                                                    X_scaled, ls_cols_X_atlas,
                                                    group, atlas)
            elif feature_algo == 'RFE': # using RFE
                features, features_rfe_and_rank_df = predict.feature_ranking(X_scaled,
                                                                    y_labeled,
                                                                    ls_cols_X_atlas)
                print("number of features extracted by RFE: ",len(features_rfe_and_rank_df.feature))
            # print(features)
            df_with_features = db_processing.get_df_from_df(df_X, usecols = features)
            df_with_features_lhrh = db_processing.get_df_from_df(df_X, usecols = sorted(stats_laterality.RReplace(features).lhrh_list))

            # STEP run Linear Regression Moderation
            if STEP_LinRegModeration:
                linear_regression_moderation.linreg_moderation_results(db_processing.join_dfs(df_clin_group, df_with_features),
                        features, params['group_param'], params['regression_param'],
                        varia.get_dir(path.join(nimb_stats['STATS_HOME'], nimb_stats['linreg_moderation_dir'])),
                        atlas, group)
            if STEP_Laterality:
                stats_laterality.run_laterality(db_processing.join_dfs(df_clin_group, df_with_features_lhrh), paths["group_col"],
                        varia.get_dir(path.join(nimb_stats['STATS_HOME'], nimb_stats['laterality_dir']+'_'+group)))
            if group == 'all':
            # STEP run ANOVA and Simple Linear Regression
                if STEP_Anova_SimpLinReg:
                    RUN_GroupAnalysis_ANOVA_SimpleLinearRegression(db_processing.join_dfs(df_clin_group, df_with_features),
                                                            groups,
                                                            params['y'],
                                                            params['other_params'],
                                                            varia.get_dir(path.join(nimb_stats['STATS_HOME'], nimb_stats['anova']+'_'+group)),
                                                            paths['group_col'],
                                                            features)
            # STEP run ANOVA and Simple Logistic Regression
                if STEP_LogisticRegression:
                    stats_LogisticRegression.Logistic_Regression(X_scaled, y_labeled, paths['group_col'],
                                                        varia.get_dir(path.join(nimb_stats['STATS_HOME'], nimb_stats['logistic_regression_dir']+'_'+group)))



    def get_X_data_per_group_all_groups(self, group):
    # extract X_scaled values for the brain parameters for and use them to extract PCA-based features
    # print('group is: ',group)
        if group == 'all':
                df_clin_group = df_clin
                df_X = df_sub_and_cort
                y_labeled = preprocessing.label_y(df_clin, prediction_vars['target'])
                X_scaled = preprocessing.scale_X(df_X)
            else:
                df_group      = db_processing.get_df_per_parameter(df_clin_atlas, paths['group_col'], group)
                df_clin_group = db_processing.rm_cols_from_df(df_group, ls_cols_X_atlas)
                df_X          = db_processing.rm_cols_from_df(df_group, [i for i in df_group.columns.tolist() if i not in ls_cols_X_atlas])
                y_labeled     = preprocessing.label_y(df_group, prediction_vars['target'])
                X_scaled      = preprocessing.scale_X(df_X)
            return df_X, y_labeled, X_scaled, df_clin_group


