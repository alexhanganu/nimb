from os import environ, path, chdir, system
import sys
import time
import argparse


class RUN_stats():
    """will run statistical analysis for the provided groups file"""

    def __init__(self, all_vars):
        self.project         = all_vars.params.project
        self.project_vars    = all_vars.projects[self.project]
        self.stats_paths     = self.project_vars['STATS_PATHS']
        self.stats_params    = self.project_vars['STATS_PARAMS']
        self.group_col       = self.project_vars['group_col']
        self.dir_stats_home  = self.stats_paths["STATS_HOME"]
        self.atlas           = ('DK','DS','DKDS')[1]
        self.get_steps(all_vars)

        print(f'    Performing statistical analysis in folder: {self.dir_stats_home}')
        print('    materials located at: {:<50}'.format(self.project_vars['materials_DIR'][1]))
        print('    file for analysis: {:<50}'.format(self.project_vars['fname_groups']))
        print('    id column: {:<50}'.format(str(self.project_vars['id_col'])))
        print('    group column: {:<50}'.format(str(self.project_vars['group_col'])))
        print('    variables to analyse: {:<50}'.format(str(self.project_vars['variables_for_glm'])))

        self.tab = Table()
        self.preproc = preprocessing.Preprocess()
        self.df_user_stats, self.df_final_grid,\
            self.df_adjusted,\
            self.cols_X,\
            self.groups = MakeGrid(self.project_vars).grid()

    def run(self):
        print("running")
        for step in self.steps:
            step2run = self.steps[step]['name']
            if self.steps[step]["run"]:
                print(f"    running step: {step2run}")
                self.run_step(step2run)


    def run_step(self, step2run):
        self.use_features            = False
        self.feature_algo            = 'PCA' #'RFE'

        for group in ['all',]+self.groups: #'all' stands for all groups
            df_X, y_labeled, X_scaled, df_clin_group = self.get_X_data_per_group_all_groups(group)
            df_with_features, features, features_rfe_and_rank_df = self.get_features_df_per_group(group, X_scaled, y_labeled, df_X)

            if group == 'all':
                self.params_y = self.project_vars['variables_for_glm']

                # STEP run general stats
                if step2run == "STEP_stats_ttest":
                    from stats.stats_stats import ttest_do

                    variables = self.params_y+df_X.columns.tolist()
                    dir_2save = varia.get_dir(path.join(self.dir_stats_home, group))
                    ttest_res = ttest_do(self.tab.join_dfs(df_clin_group, df_X),
                                            self.group_col,
                                            variables,
                                            self.groups,
                                            dir_2save,
                                            p_thresh = 0.05).res_ttest

                # STEP run ANOVA and Simple Linear Regression
                if step2run == "STEP_Anova":
                    from stats.stats_models import ANOVA_do
                    print('performing ANOVA')
                    sig_cols = self.run_anova(features, 0.05, 0.05)

                if step2run == "STEP_SimpLinReg":
                    print('performing Simple Linear Regression on all columns')
                    from stats.plotting import Make_Plot_Regression, Make_plot_group_difference
                    dir_2save = varia.get_dir(self.stats_paths['simp_lin_reg_dir'])
                    param_features = self.run_anova(features, 1.0, 1.0)
                    Make_Plot_Regression(self.df_final_grid,
                                         param_features,
                                         self.group_col,
                                         dir_2save)
                    dir_2save = varia.get_dir(self.stats_paths['anova'])
                    Make_plot_group_difference(self.df_final_grid,
                                               param_features,
                                               self.group_col, 
                                               self.groups,
                                               dir_2save)

                    # from stats.stats_groups_anova import RUN_GroupAnalysis_ANOVA_SimpleLinearRegression
                    # dir_2save = varia.get_dir(path.join(self.dir_stats_home,
                    #                                     self.stats_paths['anova']+"_"+group))
                    # RUN_GroupAnalysis_ANOVA_SimpleLinearRegression(self.df_final_grid,
                    #                                         groups,
                    #                                         self.params_y,
                    #                                         self.project_vars['other_params'],
                    #                                         dir_2save,
                    #                                         self.group_col,
                    #                                         features)

                # STEP run ANOVA and Simple Logistic Regression
                if step2run == "STEP_LogisticRegression":
                    from stats import stats_LogisticRegression
                    print('performing Logistic Regression for all groups')
                    dir_2save = varia.get_dir(path.join(self.dir_stats_home,
                                                        self.stats_paths['logistic_regression_dir']+"_"+group))
                    stats_LogisticRegression.Logistic_Regression(X_scaled,
                                                                y_labeled,
                                                                self.group_col,
                                                                dir_2save)

                # STEP run Prediction RF SKF
                if step2run == "STEP_Predict_RF_SKF":
                    print('    performing RF SKF Prediction for all groups')
                    df_X_scaled = self.tab.create_df(X_scaled,
                                                    index_col=range(X_scaled.shape[0]),
                                                    cols=self.cols_X)
                    accuracy, best_estimator, average_score_list, _ = predict.SKF_algorithm(
                                                                                        features,
                                                                                        df_X_scaled[features].values,
                                                                                        y_labeled)
                    print("    prediction accuracy computed with RF and SKF based on PCA features is: ",accuracy)
                    # accuracy, best_estimator, average_score_list, _ = predict.SKF_algorithm(
                    #         features_rfe_and_rank_df.feature, df_X_scaled[features_rfe_and_rank_df.feature].values, y_labeled)
                    # print("prediction accuracy computed with RF and SKF based on RFE features is: ",accuracy)

                # STEP run Prediction RF LOO
                if step2run == "STEP_Predict_RF_LOO":
                    print('performing RF Leave-One_out Prediction for all groups')
                    df_X_scaled = self.tab.create_df(X_scaled,
                                                    index_col=range(X_scaled.shape[0]),
                                                    cols=self.cols_X)
                    accuracy, best_estimator, average_score_list, _ = predict.LOO_algorithm(
                            features, df_X_scaled[features].values, y_labeled)
                    print("    prediction accuracy computed with RF and SKF based on PCA features is: ",accuracy)
                    accuracy, best_estimator, average_score_list, _ = predict.LOO_algorithm(
                            features_rfe_and_rank_df.feature, df_X_scaled[features_rfe_and_rank_df.feature].values, y_labeled)
                    print("    prediction accuracy computed with RF and SKF based on RFE features is: ",accuracy)

            else:
                # run Descriptive Statistics
                dir_2save = varia.get_dir(path.join(self.dir_stats_home,'description'))
                self.run_descriptive_stats(df_clin_group, features,
                                           dir_2save)

                # STEP run Linear Regression Moderation
                if step2run == "STEP_LinRegModeration":
                    from stats import stats_models
                    print('performing Linear Regression Moderation analysis')
                    stats_models.linreg_moderation_results(
                            self.df_final_grid,
                            features, self.project_vars['group_param'],
                            self.project_vars['regression_param'],
                            varia.get_dir(path.join(self.dir_stats_home,
                                          self.stats_paths['linreg_moderation_dir'])),
                            group)

                # STEP run Laterality
                if step2run == "STEP_Laterality":
                    from stats import stats_laterality
                    print('performing Laterality analysis')
                    lhrh_feat_d = stats_laterality.RReplace(features).contralateral_features
                    lhrh_features_list = [i for i in lhrh_feat_d.keys()] + [v for v in lhrh_feat_d.values()]
                    df_with_features_lhrh = self.tab.get_df_from_df(df_X, usecols = sorted(lhrh_features_list))
                    stats_laterality.LateralityAnalysis(df_with_features_lhrh, lhrh_feat_d, group,
                                                        varia.get_dir(path.join(self.dir_stats_home,
                                                                                self.stats_paths['laterality_dir']))).run()


    def run_descriptive_stats(self,
                                df_clin_group,
                                features,
                                dir_2save):
        print('running descriptive statistics')


    def run_anova(self, features, p_thresh, intercept_thresh):
        from stats.stats_models import ANOVA_do
        dir_2save = varia.get_dir(self.stats_paths['anova'])
        return ANOVA_do(self.df_final_grid,
                       self.params_y,
                       features,
                       dir_2save,
                       p_thresh = p_thresh,
                       intercept_thresh = intercept_thresh).sig_cols



    def get_X_data_per_group_all_groups(self, group):
    # extract X_scaled values for the brain parameters
        predicted_target = self.project_vars["prediction_target"]
        print(f"    predicted target column is: {predicted_target}")
        if not predicted_target:
            predicted_target = self.group_col
        if group == 'all':
                df_clin_group = self.df_user_stats
                df_X          = self.df_adjusted
                y_labeled     = preprocessing.label_y(self.df_user_stats, predicted_target)
                X_scaled      = preprocessing.scale_X(df_X)
        else:
                df_group      = self.tab.get_df_per_parameter(self.df_final_grid, self.group_col, group)
                df_clin_group = self.tab.rm_cols_from_df(df_group, self.cols_X)
                df_X          = self.tab.rm_cols_from_df(df_group, [i for i in df_group.columns.tolist() if i not in self.cols_X])
                y_labeled     = preprocessing.label_y(df_group, predicted_target)
                X_scaled      = preprocessing.scale_X(df_X)
        return df_X, y_labeled, X_scaled, df_clin_group


    def log(self):
        stats = predict.get_stats_df(len(cols_X), atlas,
                                     self.stats_params["prediction_vars"]['nr_threads'], 
                                     definitions.sys.platform,
                                     time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))


    def get_features_df_per_group(self, group, X_scaled, y_labeled, df_X):
        features_rfe_and_rank_df = 'none'
        if self.use_features:
            if self.feature_algo == 'PCA':# using PCA
                    dir_2save = varia.get_dir(path.join(self.dir_stats_home, self.stats_paths['features']))
                    pca_threshold = self.stats_params["prediction_vars"]['pca_threshold']
                    features = predict.get_features_based_on_pca(dir_2save,
                                                        pca_threshold,
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


    def get_steps(self, all_vars):
        self.steps = {
            "0": {"name" : "STEP0_make_groups",
                "run" : False},
            "01": {"name" : "STEP_stats_ttest",
                "run" : False},
            "02": {"name" : "STEP_Anova",
                "run" : False},
            "03": {"name" : "STEP_SimpLinReg",
                "run" : False},
            "04": {"name" : "STEP_LogisticRegression",
                "run" : False},
            "05": {"name" : "STEP_Predict_RF_SKF",
                "run" : False},
            "052": {"name" : "STEP_Predict_RF_LOO",
                "run" : False},
            "06": {"name" : "STEP_LinRegModeration",
                "run" : False},
            "07": {"name" : "STEP_Laterality",
                "run" : False},
        }
        if all_vars.params.step == 00:
            for i in ("0", "01", "02", "03", "04", "05", "052"):
                self.steps[i]["run"] = True
        else:
            self.steps[all_vars.params.step]["run"] = True




def get_parameters(projects):
    """get parameters for nimb"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-project", required=True,
        default=projects[0],
        choices = projects,
        help="names of projects located in credentials_path.py/nimb/projects.json -> PROJECTS",
    )

    parser.add_argument(
        "-step", required=True,
        default='00',
        choices = ['00', '0', '01', '02', '03', '04', '05', '052', '06', '07'],
        help="choices for statistical analysis:\
                00 = run all steps; \
                0  = make groups; \
                01 = run ttests demographics; \
                02 = run anova; \
                03 = run simple linear regresison; \
                04 = run logistic regression \
                05 = run prediction with RF SKF \
                052= run prediction with RF LOO \
                06 = run linear regression moderation \
                07 = run laterality analysis ",
    )

    params = parser.parse_args()
    return params




if __name__ == "__main__":


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


    project_ids = Get_Vars().get_projects_ids()
    params      = get_parameters(project_ids)

    # all_vars     = Get_Vars()
    # projects     = all_vars.projects

    params       = get_parameters(project_ids)

    # NIMB_tmp     = all_vars.location_vars['local']['NIMB_PATHS']['NIMB_tmp']
    # all_vars.stats_vars   = SetProject(NIMB_tmp,
    #                           all_vars.stats_vars,
    #                           params.project,
    #                           projects).stats
    all_vars    = Get_Vars(params)
    # if "STATS_FILES" in all_vars.stats_vars:
    #     stats_files   = all_vars.stats_vars["STATS_FILES"]
    # else:
    #     stats_files   = {
    #    "fname_fs_per_param"     : "stats_FreeSurfer_per_param",
    #    "fname_fs_all_stats"     : "stats_FreeSurfer_all",
    #    "fname_fs_subcort_vol"   : "stats_FreeSurfer_subcortical",
    #    "file_type"              : "xlsx"}


    RUN_stats(all_vars).run()

