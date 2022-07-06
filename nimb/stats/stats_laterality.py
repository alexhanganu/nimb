import os
import argparse

from stats import db_processing
from matplotlib import pyplot as plt
import numpy as np


def LateralityAnalysis(df,
                lhrh_feat_d,
                file_name,
                PATH_save_results):
    '''creates a pandas.DataFrame with laterality analysis using the formula:
        laterality = ( feature_left - feature_right ) / ( feature_left + feature_right )
    Args:
        df = pandas.DataFrame to be used for columns
        lhrh_feat_d = {'feature':('feature_left', 'feature_right')}
        file_name - name of the file.csv
        PATH_save_results = abspath to save the file.csv
    Return:
        pandas.DataFrame csv file with results
        positive values means feature_left > feature_right
        positive values means feature_right > feature_left
    '''

    df_lat = db_processing.Table().get_clean_df()
    for feature in lhrh_feat_d:
        feat_left = lhrh_feat_d[feature][0]
        feat_right = lhrh_feat_d[feature][1]
        df_lat[feature] = (df[feat_left]-df[feat_right]) / (df[feat_left] + df[feat_right])
    df_lat.to_csv(os.path.join(PATH_save_results, f'{file_name}.csv'))
    return df_lat


def plot_laterality_per_group(X,
                              means,
                              path_2save_img,
                              y_axis_label = 'Laterality Index, right < 0 > left',
                              x_axis_label = 'Regions',
                              plot_title = 'Laterality Index by region, by group',
                              dpi = 150,
                              show = False):
    """creates a plot for laterality analysis
        author: 1st version by Andréanne Bernatchez 202205
    Args:
        X = list() of pandas.DataFrame.columns
        means = {"group_name": numpy.array(values_to_be_plotted)}
        path_2save_img = absolute path to save the image
        y_axis_label = label for the y axis
        plot_title = title of the plot
        dpi = resolution, default is 150
        show = if True will print the image
    Return:
        saves plot
    """
    groups = list(means.keys())
    X_axis = np.arange(len(X))

    for group in means:
        ax_distance = 0.1 * groups.index(group)+0.1
        X_axis = X_axis + ax_distance
        plt.bar(X_axis, means[group], 0.2, label = group)
      
    plt.xticks(X_axis, X, rotation='vertical')
    plt.xlabel(x_axis_label)
    plt.ylabel(y_axis_label)
    plt.title(plot_title)
    plt.grid(True, color = "grey", linewidth = "0.3", linestyle = "-")
    plt.legend()
    plt.savefig(path_2save_img, bbox_inches='tight', dpi=dpi)


def get_lateralized_feats(feats,
                         lat_param_left,
                         lat_param_right,
                         print_check = False):
    '''create dict() with lateralized data
        it is expected that ROIs have the same name before the hemi_param_left
        e.g.: <roi>_<hemi_param_left> = <roi>_<hemi_param_right>
    Args:
        feats = list() of all features
        lat_param_left = str() for left part laterality parameter, e.g., lh or rh
        lat_param_right = str() for right part laterality parameter, e.g., lh or rh
        print_check = if True will print the results of lateralized features
    Return:
        {atlas: {measure: {roi: (left_roi, right_roi)}}}
    '''

    def laterality_roi_get(feat, lat_param_left):
        """will search if lat_param_left in feat
        Args:
            feat = str()
            lat_param_left = str()
        Return:
            lat_feat_left: str() of feat[:lat_param_left]
                    or: ""
        """
        if lat_param_left in feat:
            lat_feat_left = feat[:feat.find(lat_param_left)]
        else:
            print("lat param: ", lat_param_left, " not in feature: ", feat)
            lat_feat_left = ""
        return lat_feat_left

    def laterality_find_contra(feats, lat_feat_left):
        """searches for a potential contralateral feature
            in the list of all features
        Args:
            feats = list() of all feats
            lat_feat_left = str() of a part of one feature that might be present in feats
        Return:
            bool, roi_contra
        """
        contra_feat = ""
        for feat in feats:
            if lat_feat_left in feat:
                contra_feat = feat
        return contra_feat

    lhrh_feat_d = {}
    contra_feats = list()
    for feat in feats:
        if feat not in contra_feats:
            lat_feat_left = laterality_roi_get(feat, lat_param_left)
            if lat_feat_left:
                lat_feat_right = laterality_find_contra(feats, lat_feat_left)
                if lat_feat_right:
                    lhrh_feat_d[lat_feat_left] = (feat, lat_feat_right)
                    contra_feats.append(lat_feat_right)
            else:
                print("lat param2: ", lat_feat_left, " not in feature: ", feat)
    if print_check:
        print("CHECKING laterality:")
        for key in lhrh_feat_d:
            print(key,":", lhrh_feat_d[key])
    return lhrh_feat_d


def laterality_per_groups(dict_dfs_per_groups,
                          feats,
                          lat_param_left,
                          lat_param_right,
                          path2save,
                          plot_title = 'Laterality Index by region, by group',
                          dpi = 150,
                          file_name = f'Laterality_results_',
                          print_check = False,
                          show_img = False):
    """calculates laterality per multiple groups
        saves the results as csv files
        saves a plot for laterality results
        it is expected that ROIs have the same name before the hemi_param_left
        e.g.: <roi>_<hemi_param_left> = <roi>_<hemi_param_right>
    Args:
        dict_dfs_per_groups = {str(group_name): pandas.DataFrame with group data}
        feats = list() of all features
        lat_param_left = str() for left part laterality parameter, e.g., lh or rh
        lat_param_right = str() for right part laterality parameter, e.g., lh or rh
        path2save = absolute path to save the file file_name
        dpi = resolution, default is 150
        file_name = the name of the file to use for laterality data
        print_check = if True will print the results of lateralized_lhrh features
        show_img = if True will show the image
    Return:
        plot image
        saves csv files with laterality analysis
    """
    lateralized_lhrh = get_lateralized_feats(feats,
                                        lat_param_left,
                                        lat_param_right, 
                                        print_check = False)
    laterality_calculated = {"means":dict()}
    for group in dict_dfs_per_groups:
        file = f'{file_name}{group}'
        df = dict_dfs_per_groups[group]
        laterality_results = LateralityAnalysis(df, 
                                                lateralized_lhrh,
                                                file,
                                                path2save)
        laterality_calculated[group] = laterality_results
        laterality_calculated["means"][group] = laterality_calculated[group].mean().to_numpy()

    groups = list(dict_dfs_per_groups.keys())
    X = laterality_calculated[groups[0]].columns.tolist()
    X_axis = np.arange(len(X))
    path_2save_img = os.path.join(path2save, f"laterality_{'_'.join(groups)}.png")
    plot_laterality_per_group(X,
                              laterality_calculated["means"],
                              path_2save_img,
                              plot_title = plot_title,
                              dpi = dpi,
                              show = show_img)
