# %% 2020-03-27
# !/usr/bin/env python
# coding: utf-8

from os import path

from stats import plotting, varia
from stats.db_processing import Table

import time, warnings
warnings.filterwarnings("ignore")

# import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt

from sklearn.preprocessing import LabelEncoder, QuantileTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE
from sklearn.model_selection import LeaveOneOut, StratifiedKFold, RandomizedSearchCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from pprint import pprint


# limit nr of CPUs used:
# try:
# 	import mkl
# 	mkl.set_num_threads(nr_threads)
# except ImportError:
# 	print('mkl is missing')

def get_stats_df(len_df_X,
                atlas,
                nr_threads,
                env_name,
                time_started):
    '''
    script to save the parameters that are used for each specific analysis
    '''

    import sklearn
    import matplotlib

    stats = Table().get_clean_df()
    d = {
        'pandas version':Table().pd_ver,
        'numpy version':np.__version__,
        'matplotlib version':matplotlib.__version__,
        'sklearn version':sklearn.__version__,
        'number of iterations':definitions.prediction_defs['NUM_ITER'],
        'atlas':atlas,
        'nr of features':len_df_X,
        'nr of threads':nr_threads,
        'remote name':env_name,
        'analysis started at':time_started,}
    i = 0
    for key in d:
        stats.at[i,'stats'] = key
        stats.at[i,'values'] = d[key]
        i += 1
    return stats

def split_list(alist, wanted_parts):
    length = len(alist)
    return [ alist[i*length // wanted_parts: (i+1)*length // wanted_parts] 
             for i in range(wanted_parts) ]


params_lang = {
    "FR": {
    'nr_components': 'nombre de composants',
    'expl_cum_var' : 'variance expliquée cumulative'
    },
    "EN": {
    'nr_components': 'number of components',
    'expl_cum_var' : 'explained cumulative variance'
    },

}


def get_pca_features(df, threshold):
    """extract features from df, using PCA, based on provided threshold
        for percentage of explanation
    Args:
        df = pandas.DataFrame with features
        threshold = percentage threshold used for PCA feature selection
    Return:
        expl_variance = list() of explained variance
        components    = componenets_ of the PCA model
    """
    model = PCA(n_components = threshold)
    model.fit_transform(df)
    expl_variance = model.explained_variance_ratio_
    components    = model.components_
    return expl_variance, components


def get_features_from_components(components,
                                expl_variance,
                                features):
    """extract the features per name
        based on the components of the PCA
    Args:
        components = sklearn.decomposition.PCA().fit_transform(df).components_
        expl_variance = sklearn.decomposition.PCA().fit_transform(df).explained_variance_ratio_
        features   = list() of features / columns from the df used for the PCA
    Return:
        dic_feat_comps = {feature_name: explained_variance}
    """
    dic_feat_comps = dict()
    n_components = components.shape[0]
    for i in range(n_components):
            idx = np.abs(components[i]).argmax()
            feat = features[idx]
            if feat not in dic_feat_comps:
                dic_feat_comps[feat] = expl_variance[i]
            else:
                dic_feat_comps[feat] = dic_feat_comps[features[idx]]+expl_variance[i]
    return dic_feat_comps


def get_features_based_on_pca(dir_pca, threshold, X_scaled, features, group, atlas, lang='FR'):

    print('    nr of features to analyze by PCA: {}'.format(len(features)))
    expl_variance, components = get_pca_features(X_scaled, threshold)
    dic_feat_comps = get_features_from_components(components,
                                                expl_variance,
                                                features)
    print('    PCA chose {} components and {} features '.format(len(expl_variance), len(dic_feat_comps.keys())))
    save_features(dic_feat_comps,
                  expl_variance,
                  file2save = path.join(dir_pca, f'features_from_pca_{group}_{atlas}.csv'),
                  img2save = path.join(dir_pca,f'pca_{group}_{atlas}.png'),
                  lang = "EN")
    varia.extract_regions(dic_feat_comps, dir_pca, atlas)

    return list(dic_feat_comps.keys())


def save_features(dic_feat_comps,
                  expl_variance,
                  file2save,
                  img2save,
                  lang = "EN"):
    """features extracted from PCA
        are being saved to a table
        and image
    Args:
        dic_feat_comps = {feature_name: explained_variance}
        expl_variance  = PCA explained_variance_
        file2save      = abspath to the csv file to save the table
        img2save       = abspath to the image png file to save the table
        lang           = language used to describe the results
    """
    df_feat_comps = Table().create_df(dic_feat_comps.values(),
                                      index_col = dic_feat_comps.keys(),
                                      cols = ['explained_variance'])
    df_feat_comps.to_csv(file2save)
    plotting.plot_simple(vals = np.cumsum(expl_variance), 
                    xlabel = params_lang[lang]['nr_components'],
                    ylabel = params_lang[lang]['expl_cum_var'],
                    path_to_save_file = img2save)


def feature_ranking(X_scaled, y_transform, cols_X):
    """
    get the ranking of all features
    :param X_scaled:
    :param y_transform:
    :return: the pandas Dataframe of all ranking feature in a sorted way
    """
    clf = RandomForestClassifier()
    feature_selector = RFE(clf)
    feature_selector.fit(X_scaled, y_transform)

    features_rfe_and_rank_df = Table().create_df(feature_selector.ranking_,
                                        index_col=cols_X, cols=['ranking']).sort_values(['ranking'])

    # features_rfe_and_rank_df = pd.DataFrame(feature_selector.ranking_,
    #                                     index=cols_X, columns=['ranking']).sort_values(['ranking'])
    features_rfe_and_rank_df['feature'] = features_rfe_and_rank_df.index
    return features_rfe_and_rank_df['feature'], features_rfe_and_rank_df


def SKF_algorithm(current_feature_list, X_scaled, y_transform, NUM_ITER):
    """
    Run the Stratified KFold CV algorithm on the data set using current_feature_list
    Params:
        - current_feature_list: the features consider
        - X_scaled: the input features for classification, according to feature list
        - y_transform: the label for classification
    Returns:
        - average accuracy of Stratified KFold CV using RandomForest on the input data set
        - the RandomForest object of the best hyper-parameter
        - average accuracy score list
        - accuracy score list
    """
    cv_algo = StratifiedKFold()
    n_estimators = [1, 2, 4, 8, 16, 32, 64, 100, 200, 400]
    max_features = ['auto', 'sqrt']
    max_depth = [int(x) for x in np.linspace(10, 110, num=11)]
    max_depth.append(None)
    min_samples_split = [2, 5, 10]
    min_samples_leaf = [1, 2, 4]
    bootstrap = [True, False]
    criterion_params = ['gini', 'entropy']
    random_grid = {'n_estimators': n_estimators,
                   'max_features': max_features,
                   'max_depth': max_depth,
                   'min_samples_split': min_samples_split,
                   'min_samples_leaf': min_samples_leaf,
                   'bootstrap': bootstrap,
                   'criterion': criterion_params}
    rf = RandomForestClassifier(random_state=42, verbose=False)
    # print("Start search the best combination")

    rf_random = RandomizedSearchCV(estimator=rf,
                                   param_distributions=random_grid,
                                   n_iter=NUM_ITER, cv=cv_algo, verbose=0, random_state=42, n_jobs=-1)

    rf_random.fit(X_scaled, y_transform)
    best_rf = rf_random.best_estimator_
    print(best_rf)

    score_list = []
    avg_score = []
    # print("Start running LOO algorithm:")

    for train_index, test_index in cv_algo.split(X_scaled, y_transform):
        X_train, X_test = X_scaled[train_index], X_scaled[test_index]
        y_train, y_test = y_transform[train_index], y_transform[test_index]
        best_rf.fit(X_train, y_train)
        y_predict = best_rf.predict(X_test)
        score = accuracy_score(y_test, y_predict)
        score_list.append(score)
        avg_score.append(np.mean(score_list))
    # print("average accuracy is:")
    # print(avg_score[-1])
    return avg_score[-1], best_rf, avg_score, score_list


def LOO_algorithm(current_feature_list, x_transform, y_transform,NUM_ITER):
    """
    Run the LOO algorithm on the data set using current_feature_list
    Params:
        - current_feature_list: the features consider
        - x_transform: the input features for classification, according to feature list
        - y_transform: the label for classification
    Returns:
        - average accuracy of LOO using RandomForest on the input data set
        - the RandomForest object of the best hyper-parameter
        - average accuracy score list
        - accuracy score list
    """
    loo = LeaveOneOut()
    n_estimators = [1, 2, 4, 8, 16, 32, 64, 100, 200, 400]
    max_features = ['auto', 'sqrt']
    max_depth = [int(x) for x in np.linspace(10, 110, num=11)]
    max_depth.append(None)
    min_samples_split = [2, 5, 10]
    min_samples_leaf = [1, 2, 4]
    bootstrap = [True, False]
    criterion_params = ['gini', 'entropy']
    random_grid = {'n_estimators': n_estimators,
                   'max_features': max_features,
                   'max_depth': max_depth,
                   'min_samples_split': min_samples_split,
                   'min_samples_leaf': min_samples_leaf,
                   'bootstrap': bootstrap,
                   'criterion': criterion_params}
    rf = RandomForestClassifier(random_state=42, verbose=False)
    # print("Start search the best combination")

    rf_random = RandomizedSearchCV(estimator=rf,
                                   param_distributions=random_grid,
                                   n_iter=NUM_ITER, cv=loo, verbose=0, random_state=42, n_jobs=-1)

    rf_random.fit(x_transform, y_transform)
    best_rf = rf_random.best_estimator_

    score_list = []
    avg_score = []
    # print("Start running LOO algorithm:")

    for train_index, test_index in loo.split(x_transform):
        X_train, X_test = x_transform[train_index], x_transform[test_index]
        y_train, y_test = y_transform[train_index], y_transform[test_index]
        best_rf.fit(X_train, y_train)
        y_predict = best_rf.predict(X_test)
        score = accuracy_score(y_test, y_predict)
        score_list.append(score)
        avg_score.append(np.mean(score_list))
    # print("average accuracy is:")
    # print(avg_score[-1])
    return avg_score[-1], best_rf, avg_score, score_list


def find_best_feature_set_based_on_ranking(pd_features_and_rank, df_x_transform, y_transform):
    """
    :param pd_features_and_rank:
    :param df_x_transform:
    :param y_transform:
    :return:pd_features_and_rank, df_x_transform, y_transform
    """
    # # running the alogirthm to get the feature set which yields the highest accuracy
    print("Started searching the best feature set based on RFE feature selector")


    current_feature_list = []
    feature_accuracy_dict = {}  # key=list of feature, value = (accuracy)
    best_estimator_accuracy_dict = {}  # key = estimator, value = accuracy
    average_score_list_dict = {}

    index = 0
    for feature in pd_features_and_rank.feature:
        current_feature_list.append(feature)
        index = index + 1
        a = time.time()
        print('\n',time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),"\n  Calculating accuracy for the set :")
        print('  ',current_feature_list)
        accuracy, best_estimator, average_score_list, _ = LOO_algorithm(
            current_feature_list, df_x_transform[current_feature_list].values, y_transform)
        dictionary_key = "@@".join(str(ft) for ft in current_feature_list)
        print('  ',accuracy, dictionary_key)
        feature_accuracy_dict[dictionary_key] = accuracy
        best_estimator_accuracy_dict[dictionary_key] = best_estimator
        average_score_list_dict[dictionary_key] = average_score_list
        b = time.time()
        print('  calculated in ',time.strftime("%H:%M:%S", time.gmtime(b-a)))
    return feature_accuracy_dict, best_estimator_accuracy_dict, average_score_list_dict


def save_to_csv(path, data):
	if type(data) == dict:
		pd.DataFrame(data, index=[0]).T.to_csv(path)
	elif type(data) == list:
		pd.DataFrame(data).to_csv(path)
	else:
		data.to_csv(path)




# PREDICTION

    # # extract features using RFE algorithm and RandomForest
    # _, features_and_rank_rfe = predict.feature_ranking(X_scaled, y_labeled, Table().get_cols(x_df))
    # print('nr of features chosen by RFE: ',len(features_and_rank_rfe))
    # print(type(features_and_rank_rfe))





    # feature_accuracy_dict, best_estimator_accuracy_dict, average_score_list_dict = \
    #     predict.find_best_feature_set_based_on_ranking(
    #         features_and_rank_rfe, df_X_scaled, y_transform)

    # # %%
    # # get the feature sets associated with highest accuracy,
    # max_accuracy_features = max(feature_accuracy_dict,
    #                             key=feature_accuracy_dict.get)
    # final_best_estimator = best_estimator_accuracy_dict[max_accuracy_features]
    # print("Feature combination with highest accuracy:")
    # print(max_accuracy_features.split('@@'))
    # print("Best accuracy is " + str(feature_accuracy_dict[max_accuracy_features]))
    # # print("Best estimator is:", final_best_estimator)

    # predict.save_to_csv(varia.get_dir(definitions.paths['PATH_results'] +"_"+definitions.params['date'])+save_f_name+'max_feature_accuracy.csv', [feature_accuracy_dict[max_accuracy_features]]+max_accuracy_features.split('@@'))
    # predict.save_to_csv(varia.get_dir(definitions.paths['PATH_results'] +"_"+definitions.params['date'])+save_f_name+'best_estimator.csv', final_best_estimator.get_params())

    # avg_score = average_score_list_dict[max_accuracy_features]
    # best_feature_names = max_accuracy_features.split('@@')

    # # %%
    # plt.xlabel('i-th iteration of LOO')
    # plt.ylabel('average accuracy')
    # plt.title('average accuracy')
    # plt.plot(avg_score)
    # plt.savefig(varia.get_dir(definitions.paths['PATH_results'] +"_"+definitions.params['date']) + save_f_name+'avg_score.png')

    # feature_importances = pd.DataFrame(final_best_estimator.feature_importances_,
    #                                    index=data_x[best_feature_names].columns,
    #                                    columns=['importance']).sort_values('importance',
    #                                                                        ascending=False)


    # pd.DataFrame(feature_importances).to_csv(
    #     varia.get_dir(definitions.paths['PATH_results'] +"_"+definitions.params['date']) + save_f_name+'feature_importance.csv')

    # # predict.save_to_csv(varia.get_dir(definitions.paths['PATH_results'] +"_"+definitions.params['date'])+save_f_name+'feature_importance.csv', feature_importances)
    # print("Finished saving important features")

    # start_time = time.time()
    # end_time = time.time()

    # time_end = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    # stats.at[-1,'stats'] = 'analysis end time'
    # stats.at[-1,'values'] = time_end
    # stats.at[-1,'stats'] = 'duration'
    # stats.at[-1,'values'] = time.strftime("%H:%M:%S", time.gmtime(end_time - start_time))

    # predict.save_to_csv(varia.get_dir(definitions.paths['PATH_results'] +"_"+definitions.params['date'])+save_f_name+'stats.csv', stats)


# path_main_dir = [p for p in ('/home_je/hanganua/sSylvie',
# 						'J:/OneDrive - Universite de Montreal/s/s2018-sylvie-reserve',
# 						'J:/Dropbox/2004étSylvie/materials') if os.path.exists(p)][0]
# data_clin = path_main_dir + '/materials/0.data_clinical_'+date+'.xlsx'

# if step == 1:
# 	data_f_X = path_main_dir + '/materials/2.data_FS_eTIVNaNOutcor_'+atlas+'_'+date+'.xlsx'
# elif step == 2:
# 	data_f_X = path_main_dir + '/results/predict_'+date+'/materials/data_sig_feat_'+atlas+'_step'+str(step)+'.xlsx'

# data_f_X = path_main_dir + '/materials/2.data_FS_eTIVNaNOutcor_'+atlas+'_'+date+'.xlsx'

# path_save_results = path_main_dir + '/results/predict_'+date+'/step'+str(step)+'_'+atlas
# save_f_name = '/predict_'+atlas+'_step'+str(part)+'_parts'+str(wanted_parts)+'_'