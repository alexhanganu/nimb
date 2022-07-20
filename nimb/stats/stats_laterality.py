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


def plot_laterality_per_group(ls_of_columns,
                              data_2plot_per_group,
                              path_2save_img,
                              on_axis = "X",
                              y_axis_label = 'Laterality Index, right < 0 > left',
                              x_axis_label = 'Regions',
                              plot_title = 'Laterality Index by region, by group',
                              dpi = 150,
                              show = False):
    """creates a plot for laterality analysis
        author: 1st version by Andréanne Bernatchez 202205
                adjusted by Emmanuelle Mazur-Lainé 202207, Alexandru Hanganu
    Args:
        ls_of_columns = list() of pandas.DataFrame.columns
        data_2plot_per_group = {"group_name": numpy.array(values_to_be_plotted)}
        on_axis = axis chosen to plot the data; default is "X", alternative is "Y"
        path_2save_img = absolute path to save the image
        y_axis_label = label for the y axis
        plot_title = title of the plot
        dpi = resolution, default is 150
        show = if True will print the image
    Return:
        saves plot
    """
    groups = list(data_2plot_per_group.keys())
    axis_vals = np.arange(len(ls_of_columns))

    for group in data_2plot_per_group:
        ax_distance = 0.1 * groups.index(group)+0.1
        axis_vals = axis_vals + ax_distance
        if on_axis == "X":
            plt.bar(axis_vals, data_2plot_per_group[group], 0.2, label = group)
        else:
            plt.barh(axis_vals, data_2plot_per_group[group], 0.2, label = group)

    if on_axis == "X":
        plt.xticks(axis_vals, ls_of_columns, rotation='vertical')
        plt.xlabel(x_axis_label)
        plt.ylabel(y_axis_label)
    else:
        plt.yticks(axis_vals, ls_of_columns)#, rotation='vertical')
        plt.ylabel(x_axis_label)
        plt.xlabel(y_axis_label)

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
        {roi: (left_roi, right_roi)}
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


def get_feats_lateralized_per_lobe(hemis,
                                   lobes,
                                   lateralized_lhrh):
    """aims to create a lateralized dict with features classified per lobe
    Args:
        hemis = list(hemisphere_abbreviation_left, hemisphere_abbreviation_left)
                similar to nimb/processing/atlases/atlas_definitions.hemis
        lobes = list(of all lobes)
                similar to nimb/processing/atlases/atlas_definitions.lobes.keys()
        lateralized_lhrh = dict() from get_lateralized_feats()
    Return:
        {lobe_hemi: [features,]}
    """
    feats_per_lobe = dict()
    for hemi in hemis:
        pos = hemis.index(hemi)
        for feat in lateralized_lhrh:
            feat_hemi = lateralized_lhrh[feat][pos]
            feat_ok = False
            for lobe in lobes:
                lobe_hemi = f"{lobe}_{hemi}"
                if lobe_hemi not in feats_per_lobe:
                    feats_per_lobe[lobe_hemi] = list()
                if lobe in feat:
                    feats_per_lobe[lobe_hemi].append(feat_hemi)
                    feat_ok = True
                    break
                else:
                    feat_ok = False
            if not feat_ok:
                print("not feat: ", feat_hemi)
    return feats_per_lobe


def get_df_data_per_lobe_per_group(dict_dfs_per_groups,
                                    feats_per_lobe):
    """will take the pandas.DataFrames per group
        extract the corresponding features per lobes
        as per features classified with get_feats_lateralized_per_lobe()
    Args:
        dict_dfs_per_groups = {group1: pandas.DataFrame,
                               group2: pandas.DataFrame}
        feats_per_lobe = dict() received from get_feats_lateralized_per_lobe()
    Return:
        dict_dfs_per_groups = {group1: pandas.DataFrame with feats per lobes,
                               group2: pandas.DataFrame with feats per lobes}
    """
    d_dfs_per_group_per_lobe = dict()
    for group in dict_dfs_per_groups:
        df = dict_dfs_per_groups[group]
        for lobe_hemi in feats_per_lobe:
            cols = feats_per_lobe[lobe_hemi]
            df[lobe_hemi] = df[cols].mean(axis = 1)
        d_dfs_per_group_per_lobe[group] = df[list(feats_per_lobe.keys())]
    return d_dfs_per_group_per_lobe


def laterality_per_groups(dict_dfs_per_groups,
                          feats,
                          lat_param_left,
                          lat_param_right,
                          path2save,
                          on_axis = "X",
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
                              on_axis = on_axis,
                              plot_title = plot_title,
                              dpi = dpi,
                              show = show_img)
