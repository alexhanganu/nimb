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


def plot_laterality_per_group(ls_of_features,
                              data_2plot_per_group,
                              path_2save_img,
                              on_axis = "X",
                              y_axis_label = 'Laterality Index, right < 0 > left',
                              x_axis_label = 'Regions',
                              plot_title = 'Laterality Index by region, by group',
                              plot_figure_size = (20, 3),
                              dpi = 150,
                              show = False):
    """creates a plot for laterality analysis
        author: 1st version by Andréanne Bernatchez 202205
                adjusted by Emmanuelle Mazur-Lainé 202207, Alexandru Hanganu
    Args:
        ls_of_features = list() of pandas.DataFrame.columns
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
    plt.rcParams["figure.figsize"] = plot_figure_size
    groups = list(data_2plot_per_group.keys())
    axis_vals = np.arange(len(ls_of_features))

    for group in data_2plot_per_group:
        ax_distance = 0.1 * groups.index(group)+0.1
        axis_vals = axis_vals + ax_distance
        if on_axis == "X":
            plt.bar(axis_vals, data_2plot_per_group[group], 0.2, label = group)
        else:
            plt.barh(axis_vals, data_2plot_per_group[group], 0.2, label = group)

    if on_axis == "X":
        plt.xticks(axis_vals, ls_of_features, rotation='vertical')
        plt.xlabel(x_axis_label)
        plt.ylabel(y_axis_label)
    else:
        plt.yticks(axis_vals, ls_of_features)
        plt.ylabel(x_axis_label)
        plt.xlabel(y_axis_label)

    plt.title(plot_title)
    plt.grid(True, color = "grey", linewidth = "0.3", linestyle = "-")
    plt.legend()
    plt.savefig(path_2save_img, bbox_inches='tight', dpi=dpi)
    plt.close()


def get_lateralized_feats(feats_2lateralize,
                         lat_param,
                         contra_lat_param,
                         print_check = False):
    '''creates dict() with lateralized data
        it is expected that ROIs have the same name before the hemi_parameter
        e.g.: <roi>_<hemi_param_left> = <roi>_<hemi_param_right>
    Args:
        feats_2lateralize = list() of all features
        lat_param = str() the laterality parameter to be searched for, e.g., lh or rh
        contra_lat_param = str() the contralateral laterality parameter, e.g., lh or rh
        print_check = if True will print the results of lateralized features
    Return:
        {feature: (left_feature, right_feature)}
    '''
    def get_laterality_subfeat(feat, lat_param):
        """script tries to avoid the situation when lat_param is in position 0
        """
        lat_subfeat = feat[:feat.find(lat_param)]
        if not lat_subfeat:
            subfeat_2chk = feat[1:]
            lat_subfeat = feat[0] + subfeat_2chk[:subfeat_2chk.find(lat_param)]
        return lat_subfeat

    if print_check:
        print(feats)

    # combine two feats based on laterality
    lhrh_feat_d = {}
    contra_feats = list()
    for feat in feats_2lateralize:
        if feat not in contra_feats and lat_param in feat:
            lat_subfeat = get_laterality_subfeat(feat, lat_param)
            if lat_subfeat:
                contra_feat = ""
                feats_left2search = feats_2lateralize[feats_2lateralize.index(feat)+1:]
                ls_feats_correspond = [i for i in feats_left2search if lat_subfeat in i]
                for feat_found in ls_feats_correspond:
                    contra_subfeat = feat_found[:feat_found.find(contra_lat_param)]
                    if contra_subfeat == lat_subfeat \
                        and len(feat) == len(feat_found):
                        contra_feat = feat_found
                        break
                    elif contra_subfeat in feat:
                        contra_feat = feat_found
                        lat_subfeat = contra_subfeat
                        break
                if contra_feat:
                        contra_feats.append(contra_feat)
                        lhrh_feat_d[lat_subfeat] = (feat, contra_feat)
                else:
                    print("cannot find contralateral feature for: ", feat)
            else:
                print("lat param: ", lat_param, " not in feature: ", feat)

    if print_check:
        print("\n\nCHECKING laterality:")
        print("    iterated features: ", int(len(feats_2lateralize) / 2))
        print("    combined features: ", len(lhrh_feat_d.keys()))
        for key in lhrh_feat_d:
            print("     ",key,":", lhrh_feat_d[key])
    return lhrh_feat_d


def get_all_combined_feats_per_param(feats_per_param,
                                     laterality_param):
    """combines all features in a list of features
        based on the laterality_param provided
    Args:
        feats_per_param = dict() {"feature_per_param_a": (feature_lateral_hemi_a1, feature_lateral_hemi_a2),
                                  "feature_per_param_b": (feature_lateral_hemi_b1, feature_lateral_hemi_b2)}
        laterality_param = list() [laterality_param_hemi1, laterality_param_hemi2]
    Return:
    ombined_feats_per_param = dict() {feature_per_param_laterality_param_hemi1: [feature_lateral_hemi_a1, feature_lateral_hemi_b1],
                                      feature_per_param_laterality_param_hemi2: [feature_lateral_hemi_a2, feature_lateral_hemi_b2]}
    """
    combined_feats_per_param = dict()
    for param in feats_per_param:
        feats = feats_per_param[param]
        lateralized_lhrh = get_lateralized_feats(feats,
                                                 laterality_param[0],
                                                 laterality_param[1])
        for hemi in laterality_param:
            pos = laterality_param.index(hemi)
            param_hemi = f"{param}_{hemi}"
            if param_hemi not in combined_feats_per_param:
                combined_feats_per_param[param_hemi] = list()
            for feat_main in lateralized_lhrh:
                feat_hemi = lateralized_lhrh[feat_main][pos]
                combined_feats_per_param[param_hemi].append(feat_hemi)
    return combined_feats_per_param


def laterality_per_groups(dict_dfs_per_groups,
                          feats,
                          lat_param_left,
                          lat_param_right,
                          path2save,
                          ls_of_features_2plot = list(),
                          on_axis = "X",
                          plot_title = 'Laterality Index by region, by group',
                          plot_figure_size = (20, 3),
                          dpi = 150,
                          file_name = f'Laterality',
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
        ls_of_features_2plot = list() of features to use for plotting
        dpi = resolution, default is 150
        file_name = the name of the file to use for laterality data
        print_check = if True will print the results of lateralized_lhrh features
        show_img = if True will show the image
    Return:
        plot image
        saves csv files with laterality analysis
    """
    groups = list(dict_dfs_per_groups.keys())
    lateralized_lhrh = get_lateralized_feats(feats,
                                        lat_param_left,
                                        lat_param_right, 
                                        print_check = print_check)
    laterality_calculated = {"means":dict()}
    for group in dict_dfs_per_groups:
        file = f'{file_name}_results_{group}'
        df = dict_dfs_per_groups[group]
        laterality_results = LateralityAnalysis(df, 
                                                lateralized_lhrh,
                                                file,
                                                path2save)
        laterality_calculated[group] = laterality_results
        laterality_calculated["means"][group] = laterality_calculated[group].mean().to_numpy()


    if not ls_of_features_2plot:
        ls_of_features_2plot = laterality_calculated[groups[0]].columns.tolist()
    path_2save_img = os.path.join(path2save, f"{file_name}_{'_'.join(groups)}.png")
    plot_laterality_per_group(ls_of_features_2plot,
                              laterality_calculated["means"],
                              path_2save_img,
                              on_axis = on_axis,
                              plot_title = plot_title,
                              plot_figure_size = plot_figure_size,
                              dpi = dpi,
                              show = show_img)
