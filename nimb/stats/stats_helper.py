from os import environ, path, chdir, system
import sys
import time

from stats import (db_processing, preprocessing, predict, varia)

class RUN_stats():
    """will run statistical analysis for the provided groups file"""

    def __init__(self, nimb_stats, project_vars):

        self.atlas = ('DK','DS','DKDS')[1]
        self.project_vars = project_vars
        self.stats_paths = nimb_stats['STATS_PATHS']
        self.stats_params = nimb_stats['STATS_PARAMS']
        print('materials located at: {:>40}'.format(project_vars['materials_DIR'][1]))
        print('file for analysis: {:>40}'.format(project_vars['GLM_file_group']))
        print('id column: {:>40}'.format(str(project_vars['id_col'])))
        print('group column: {:>40}'.format(str(project_vars['group_col'])))
        print('variables to analyse: {:>40}'.format(str(project_vars['variables_for_glm'])))
        print('stats will be saved at: {:>40}'.format(self.stats_paths['STATS_HOME']))
        group_param = project_vars['group_param']
        regression_param = project_vars['regression_param']
        other_params = project_vars['other_params']
        f_data_clinical = project_vars['GLM_file_group']

        self.feature_algo = 'PCA' #'RFE'
        self.prediction_vars = self.stats_params["prediction_vars"]
        cor_methods = self.stats_params["cor_methods"]
        cor_level_chosen = self.stats_params["cor_level_chosen"]

        self.get_tables()

        self.STEP_stats_ttest        = False
        self.STEP_Anova              = True
        self.STEP_SimpLinReg         = True # requires Anova to be True
        self.STEP_LinRegModeration   = False
        self.STEP_LogisticRegression = False
        self.STEP_Laterality         = False
        self.STEP_Predict            = False
        self.STEP_Predict_RF_SKF     = False
        self.STEP_Predict_RF_LOO     = False
        self.STEP_get_param_based_db = False

    def run_stats(self):
         for group in ['all',]:#+self.groups: #'all' stands for all groups
            df_X, y_labeled, X_scaled, df_clin_group = self.get_X_data_per_group_all_groups(group)
            df_with_features, features, features_rfe_and_rank_df = self.get_features_df_per_group(group, X_scaled, y_labeled, df_X)

            if group == 'all':
                # STEP run general stats
                if self.STEP_stats_ttest:
                    from stats.stats_stats import ttest_do
                    ttest_res = ttest_do(db_processing.join_dfs(df_clin_group, df_X),
                             self.project_vars['group_col'],
                             self.project_vars['variables_for_glm']+df_X.columns.tolist(),
                             self.groups,
                             varia.get_dir(path.join(self.stats_paths['STATS_HOME'], group)),
                             p_thresh = 0.05).res_ttest

                # STEP run ANOVA and Simple Linear Regression
                if self.STEP_Anova:
                    from stats.stats_models import ANOVA_do
                    print('performing ANOVA')
                    sig_cols = ANOVA_do(db_processing.join_dfs(df_clin_group, df_with_features),
                                       self.project_vars['variables_for_glm'], features,
                                       varia.get_dir(self.stats_paths['anova']),
                                       p_thresh = 0.05, intercept_thresh = 0.05).sig_cols
                    print(sig_cols)
                    if self.STEP_SimpLinReg:
                        print('performing Simple Linear Regression based on ANOVA significant columns')
                        from stats.plotting import Make_Plot_Regression
                        Make_Plot_Regression(db_processing.join_dfs(df_clin_group, df_with_features),
                                             sig_cols, self.project_vars['group_col'],
                                             varia.get_dir(self.stats_paths['simp_lin_reg_dir']))
                        Make_plot_group_difference(db_processing.join_dfs(df_clin_group, df_with_features),
                                                   sig_cols, self.project_vars['group_col'], self.groups,
                                                   varia.get_dir(self.stats_paths['anova']))

#                    from stats.stats_groups_anova import RUN_GroupAnalysis_ANOVA_SimpleLinearRegression
#                    RUN_GroupAnalysis_ANOVA_SimpleLinearRegression(db_processing.join_dfs(df_clin_group, df_with_features),
#                                                            groups,
#                                                            self.project_vars['variables_for_glm'],
#                                                            other_params,
#                                                            varia.get_dir(path.join(self.stats_paths['STATS_HOME'], self.stats_paths['anova']+'_'+group)),
#                                                            self.project_vars['group_col'],
#                                                            features)

                # STEP run ANOVA and Simple Logistic Regression
                if self.STEP_LogisticRegression:
                    from stats import stats_LogisticRegression
                    print('performing Logistic Regression for all groups')
                    stats_LogisticRegression.Logistic_Regression(X_scaled, y_labeled, self.project_vars['group_col'],
                                                        varia.get_dir(path.join(self.stats_paths['STATS_HOME'], self.stats_paths['logistic_regression_dir']+'_'+group)))

                if self.STEP_Predict:
                    # STEP run Prediction RF SKF
                    if self.STEP_Predict_RF_SKF:
                        print('    performing RF SKF Prediction for all groups')
                        df_X_scaled = db_processing.create_df(X_scaled, index_col=range(X_scaled.shape[0]), cols=self.ls_cols_X_atlas)
                        accuracy, best_estimator, average_score_list, _ = predict.SKF_algorithm(
                                features, df_X_scaled[features].values, y_labeled)
                        print("    prediction accuracy computed with RF and SKF based on PCA features is: ",accuracy)
                        # accuracy, best_estimator, average_score_list, _ = predict.SKF_algorithm(
                        #         features_rfe_and_rank_df.feature, df_X_scaled[features_rfe_and_rank_df.feature].values, y_labeled)
                        # print("prediction accuracy computed with RF and SKF based on RFE features is: ",accuracy)

                    # STEP run Prediction RF LOO
                    if self.STEP_Predict_RF_LOO:
                        print('performing RF Leave-One_out Prediction for all groups')
                        df_X_scaled = db_processing.create_df(X_scaled, index_col=range(X_scaled.shape[0]), cols=self.ls_cols_X_atlas)
                        accuracy, best_estimator, average_score_list, _ = predict.LOO_algorithm(
                                features, df_X_scaled[features].values, y_labeled)
                        print("    prediction accuracy computed with RF and SKF based on PCA features is: ",accuracy)
                        accuracy, best_estimator, average_score_list, _ = predict.LOO_algorithm(
                                features_rfe_and_rank_df.feature, df_X_scaled[features_rfe_and_rank_df.feature].values, y_labeled)
                        print("    prediction accuracy computed with RF and SKF based on RFE features is: ",accuracy)

            else:
                # STEP run Linear Regression Moderation
                if self.STEP_LinRegModeration:
                    from stats import stats_models
                    print('performing Linear Regression Moderation analysis')
                    stats_models.linreg_moderation_results(
                            db_processing.join_dfs(df_clin_group, df_with_features),
                            features, group_param, regression_param,
                            varia.get_dir(path.join(self.stats_paths['STATS_HOME'],
                                          self.stats_paths['linreg_moderation_dir'])),
                            group)

                # STEP run Laterality
                if self.STEP_Laterality:
                    from stats import stats_laterality
                    print('performing Laterality analysis')
                    lhrh_feat_d = stats_laterality.RReplace(features).contralateral_features
                    lhrh_features_list = [i for i in lhrh_feat_d.keys()] + [v for v in lhrh_feat_d.values()]
                    df_with_features_lhrh = db_processing.get_df_from_df(df_X, usecols = sorted(lhrh_features_list))
                    stats_laterality.LateralityAnalysis(df_with_features_lhrh, lhrh_feat_d, group,
                                                        varia.get_dir(path.join(self.stats_paths['STATS_HOME'],
                                                                                self.stats_paths['laterality_dir']))).run()



    def get_tables(self):
        f_CoreTIVNaNOut = self.stats_params["file_name_corrected"]
        atlas_sub = 'Subcort'
        atlas_DK = 'DK'
        atlas_DS = 'DS'
        f_subcort    = path.join(self.project_vars['materials_DIR'][1], f_CoreTIVNaNOut+atlas_sub+'.xlsx')
        f_atlas_DK   = path.join(self.project_vars['materials_DIR'][1], f_CoreTIVNaNOut+atlas_DK+'.xlsx')
        f_atlas_DS   = path.join(self.project_vars['materials_DIR'][1], f_CoreTIVNaNOut+atlas_DS+'.xlsx')
        self.df_clin = db_processing.get_df(path.join(self.project_vars['materials_DIR'][1], self.project_vars['GLM_file_group']),
                                    usecols=[self.project_vars['id_col'], self.project_vars['group_col']]+self.project_vars['variables_for_glm'],
                                    index_col = self.project_vars['id_col'])
        self.groups = preprocessing.get_groups(self.df_clin, self.project_vars['group_col'])
        self.df_sub_and_cort, self.ls_cols_X_atlas = preprocessing.get_df(f_subcort, f_atlas_DK, f_atlas_DS,
                                                         self.atlas, self.project_vars['id_col'])
        self.df_clin_atlas = db_processing.join_dfs(self.df_clin, self.df_sub_and_cort, how='outer')

    def get_X_data_per_group_all_groups(self, group):
    # extract X_scaled values for the brain parameters
        if group == 'all':
                df_clin_group = self.df_clin
                df_X = self.df_sub_and_cort
                y_labeled = preprocessing.label_y(self.df_clin, self.prediction_vars['target'])
                X_scaled = preprocessing.scale_X(df_X)
        else:
                df_group      = db_processing.get_df_per_parameter(self.df_clin_atlas, self.project_vars['group_col'], group)
                df_clin_group = db_processing.rm_cols_from_df(df_group, self.ls_cols_X_atlas)
                df_X          = db_processing.rm_cols_from_df(df_group, [i for i in df_group.columns.tolist() if i not in self.ls_cols_X_atlas])
                y_labeled     = preprocessing.label_y(df_group, self.prediction_vars['target'])
                X_scaled      = preprocessing.scale_X(df_X)
        return df_X, y_labeled, X_scaled, df_clin_group

    def log(self):
        stats = predict.get_stats_df(len(ls_cols_X_atlas), atlas,
                                     prediction_vars['nr_threads'], 
                                     definitions.sys.platform,
                                     time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))

    def get_features_df_per_group(self, group, X_scaled, y_labeled, df_X):
        if self.feature_algo == 'PCA':# using PCA
                features = predict.get_features_based_on_pca(varia.get_dir(path.join(self.stats_paths['STATS_HOME'], self.stats_paths['features'])),
                                                    self.prediction_vars['pca_threshold'],
                                                    X_scaled, self.ls_cols_X_atlas,
                                                    group, self.atlas)
                features_rfe_and_rank_df = 'none'
        elif self.feature_algo == 'RFE': # using RFE
                features, features_rfe_and_rank_df = predict.feature_ranking(X_scaled,
                                                                    y_labeled,
                                                                    self.ls_cols_X_atlas)
                print("    number of features extracted by RFE: ",len(features_rfe_and_rank_df.feature))
        df_with_features = db_processing.get_df_from_df(df_X, usecols = features)
        return df_with_features, features, features_rfe_and_rank_df

'''2DO
    zipf's law https://getpocket.com/explore/item/mathematical-model-reveals-the-patterns-of-how-innovations-arise
'''
