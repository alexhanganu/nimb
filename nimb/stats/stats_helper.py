from os import environ, path, chdir, system
import sys
import time

class RUN_stats():
    """will run statistical analysis for the provided groups file"""

    def __init__(self, nimb_stats, project_vars):

        self.use_features            = False
        self.feature_algo            = 'PCA' #'RFE'

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

        self.atlas        = ('DK','DS','DKDS')[1]
        self.project_vars = project_vars
        self.stats_paths  = nimb_stats['STATS_PATHS']
        self.stats_params = nimb_stats['STATS_PARAMS']
        group_param       = project_vars['group_param']
        regression_param  = project_vars['regression_param']
        other_params      = project_vars['other_params']
        print('    materials located at: {:<50}'.format(project_vars['materials_DIR'][1]))
        print('    file for analysis: {:<50}'.format(project_vars['fname_groups']))
        print('    id column: {:<50}'.format(str(project_vars['id_col'])))
        print('    group column: {:<50}'.format(str(project_vars['group_col'])))
        print('    variables to analyse: {:<50}'.format(str(project_vars['variables_for_glm'])))

        self.prediction_vars = self.stats_params["prediction_vars"]
        cor_methods          = self.stats_params["cor_methods"]
        cor_level_chosen     = self.stats_params["cor_level_chosen"]

        self.tab = Table()
        self.preproc = preprocessing.Preprocess(utilities)
        self.df_user_stats, self.df_final_grid,\
            self.df_adjusted,\
            self.cols_X,\
            self.groups = MakeGrid(project_vars,
                                nimb_stats).grid()

    def run_stats(self):
         for group in ['all',]:#+self.groups: #'all' stands for all groups
            df_X, y_labeled, X_scaled, df_clin_group = self.get_X_data_per_group_all_groups(group)
            df_with_features, features, features_rfe_and_rank_df = self.get_features_df_per_group(group, X_scaled, y_labeled, df_X)

            if group == 'all':
                # STEP run general stats
                if self.STEP_stats_ttest:
                    from stats.stats_stats import ttest_do
                    ttest_res = ttest_do(self.tab.join_dfs(df_clin_group, df_X),
                             self.project_vars['group_col'],
                             self.project_vars['variables_for_glm']+df_X.columns.tolist(),
                             self.groups,
                             varia.get_dir(path.join(self.stats_paths['STATS_HOME'], group)),
                             p_thresh = 0.05).res_ttest

                # STEP run ANOVA and Simple Linear Regression
                if self.STEP_Anova:
                    from stats.stats_models import ANOVA_do
                    print('performing ANOVA')
                    sig_cols = ANOVA_do(self.df_final_grid,
                                       self.project_vars['variables_for_glm'], features,
                                       varia.get_dir(self.stats_paths['anova']),
                                       p_thresh = 0.05, intercept_thresh = 0.05).sig_cols
                    if self.STEP_SimpLinReg:
                        print('performing Simple Linear Regression based on ANOVA significant columns')
                        from stats.plotting import Make_Plot_Regression, Make_plot_group_difference
                        Make_Plot_Regression(self.df_final_grid,
                                             sig_cols, self.project_vars['group_col'],
                                             varia.get_dir(self.stats_paths['simp_lin_reg_dir']))
                        Make_plot_group_difference(self.df_final_grid,
                                                   sig_cols, self.project_vars['group_col'], self.groups,
                                                   varia.get_dir(self.stats_paths['anova']))

#                    from stats.stats_groups_anova import RUN_GroupAnalysis_ANOVA_SimpleLinearRegression
#                    RUN_GroupAnalysis_ANOVA_SimpleLinearRegression(self.df_final_grid,
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
                        df_X_scaled = self.tab.create_df(X_scaled, index_col=range(X_scaled.shape[0]), cols=self.cols_X)
                        accuracy, best_estimator, average_score_list, _ = predict.SKF_algorithm(
                                features, df_X_scaled[features].values, y_labeled)
                        print("    prediction accuracy computed with RF and SKF based on PCA features is: ",accuracy)
                        # accuracy, best_estimator, average_score_list, _ = predict.SKF_algorithm(
                        #         features_rfe_and_rank_df.feature, df_X_scaled[features_rfe_and_rank_df.feature].values, y_labeled)
                        # print("prediction accuracy computed with RF and SKF based on RFE features is: ",accuracy)

                    # STEP run Prediction RF LOO
                    if self.STEP_Predict_RF_LOO:
                        print('performing RF Leave-One_out Prediction for all groups')
                        df_X_scaled = self.tab.create_df(X_scaled, index_col=range(X_scaled.shape[0]), cols=self.cols_X)
                        accuracy, best_estimator, average_score_list, _ = predict.LOO_algorithm(
                                features, df_X_scaled[features].values, y_labeled)
                        print("    prediction accuracy computed with RF and SKF based on PCA features is: ",accuracy)
                        accuracy, best_estimator, average_score_list, _ = predict.LOO_algorithm(
                                features_rfe_and_rank_df.feature, df_X_scaled[features_rfe_and_rank_df.feature].values, y_labeled)
                        print("    prediction accuracy computed with RF and SKF based on RFE features is: ",accuracy)

            else:
                # STEP run Linear Regression Moderation
                self.run_descriptive_stats(df_clin_group, features,
                                           varia.get_dir(path.join(self.stats_paths['STATS_HOME'],
                                           'description')))
                if self.STEP_LinRegModeration:
                    from stats import stats_models
                    print('performing Linear Regression Moderation analysis')
                    stats_models.linreg_moderation_results(
                            self.df_final_grid,
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
                    df_with_features_lhrh = self.tab.get_df_from_df(df_X, usecols = sorted(lhrh_features_list))
                    stats_laterality.LateralityAnalysis(df_with_features_lhrh, lhrh_feat_d, group,
                                                        varia.get_dir(path.join(self.stats_paths['STATS_HOME'],
                                                                                self.stats_paths['laterality_dir']))).run()



    # def run_descriptive_stats(self, df_clin_group, features,
                               # varia.get_dir(path.join(self.stats_paths['STATS_HOME'],
                               # 'description'))):
        # print('running descriptive statistics')

    def get_X_data_per_group_all_groups(self, group):
    # extract X_scaled values for the brain parameters
        predicted_target = self.project_vars["prediction_target"]
        if not predicted_target:
            predicted_target = self.project_vars["group_col"]
        if group == 'all':
                df_clin_group = self.df_user_stats
                df_X          = self.df_adjusted
                y_labeled     = preprocessing.label_y(self.df_user_stats, predicted_target)
                X_scaled      = preprocessing.scale_X(df_X)
        else:
                df_group      = self.tab.get_df_per_parameter(self.df_final_grid, self.project_vars['group_col'], group)
                df_clin_group = self.tab.rm_cols_from_df(df_group, self.cols_X)
                df_X          = self.tab.rm_cols_from_df(df_group, [i for i in df_group.columns.tolist() if i not in self.cols_X])
                y_labeled     = preprocessing.label_y(df_group, predicted_target)
                X_scaled      = preprocessing.scale_X(df_X)
        return df_X, y_labeled, X_scaled, df_clin_group

    def log(self):
        stats = predict.get_stats_df(len(cols_X), atlas,
                                     prediction_vars['nr_threads'], 
                                     definitions.sys.platform,
                                     time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))

    def get_features_df_per_group(self, group, X_scaled, y_labeled, df_X):
        features_rfe_and_rank_df = 'none'
        if self.use_features:
            if self.feature_algo == 'PCA':# using PCA
                    features = predict.get_features_based_on_pca(varia.get_dir(path.join(self.stats_paths['STATS_HOME'], self.stats_paths['features'])),
                                                        self.prediction_vars['pca_threshold'],
                                                        X_scaled, self.cols_X,
                                                        group, self.atlas)
            elif self.feature_algo == 'RFE': # using RFE
                    features, features_rfe_and_rank_df = predict.feature_ranking(X_scaled,
                                                                        y_labeled,
                                                                        self.cols_X)
                    print("    number of features extracted by RFE: ",len(features_rfe_and_rank_df.feature))
            df_with_features = self.tab.get_df_from_df(df_X, usecols = features)
        else:
            df_with_features = self.tab.get_df_from_df(df_X, usecols = self.cols_X)
            features = self.cols_X
        return df_with_features, features, features_rfe_and_rank_df


def get_parameters(projects):
    """get parameters for nimb"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-project", required=False,
        default=projects[0],
        choices = projects,
        help="names of projects located in credentials_path.py/nimb/projects.json -> PROJECTS",
    )

    params = parser.parse_args()
    return params


if __name__ == "__main__":

    import sys
    from os import system
    import argparse
    try:
        from pathlib import Path
    except ImportError as e:
        print('please install pathlib')
        sys.exit(e)

    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[1]
    sys.path.append(str(top))

    from stats import (db_processing,
                        preprocessing,
                        predict, varia)
    from setup.get_vars import Get_Vars, SetProject
    from stats.make_stats_grid import MakeGrid
    from stats.db_processing import Table
    from distribution import utilities

    all_vars     = Get_Vars()
    projects     = all_vars.projects
    project_ids  = all_vars.project_ids
    params       = get_parameters(project_ids)

    NIMB_tmp     = all_vars.location_vars['local']['NIMB_PATHS']['NIMB_tmp']
    all_vars.stats_vars   = SetProject(NIMB_tmp,
                              all_vars.stats_vars,
                              params.project,
                              projects).stats
    if "STATS_FILES" in all_vars.stats_vars:
        stats_files   = all_vars.stats_vars["STATS_FILES"]
    else:
        stats_files   = {
       "fname_fs_per_param"     : "stats_FreeSurfer_per_param",
       "fname_fs_all_stats"     : "stats_FreeSurfer_all",
       "fname_fs_subcort_vol"   : "stats_FreeSurfer_subcortical",
       "file_type"              : "xlsx"}

    print(f'    Performing statistical analysis in folder: {all_vars.stats_vars["STATS_PATHS"]["STATS_HOME"]}')

    RUN_stats(all_vars.stats_vars,
              projects[params.project]
              ).run_stats()

