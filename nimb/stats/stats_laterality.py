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


def get_lateralized_feats_for_freesurfer():
    '''create dict() with lateralized data for freesurfer atlases
    Return: {atlas: {measure: {roi: (left_roi, right_roi)}}}
    '''
    lateralized = dict()
    for atlas in atlases_hemi:
        lateralized[atlas] = dict()
        for meas in measures[atlas]:
            lateralized[atlas][meas] = dict()

    for roi_atlas in cols_X:
        for atlas in atlases_hemi:
            atlas_hemi = atlases_hemi[atlas]
            if atlas_hemi in roi_atlas:
                roi = roi_atlas.replace(f'_{atlas_hemi}','')
                contralat_atlas_hemi = atlas_hemi.replace("L", 'R')
                if atlas in subcort_atlases:
                    meas = measures[atlas][0]
                    lateralized[atlas][meas][roi] = (roi_atlas, roi_atlas.replace(atlas_hemi, contralat_atlas_hemi))
                elif atlas_hemi == 'L_VolSeg':
                    if roi_atlas.endswith(atlas_hemi):
                        meas = measures[atlas][0]
                        lateralized[atlas][meas][roi] = (roi_atlas, roi_atlas.replace(atlas_hemi, contralat_atlas_hemi))
                else:
                    for meas in measures[atlas]:
                        if f'{meas}{atlas_hemi}' in roi_atlas:
                            lateralized[atlas][meas][roi] = (roi_atlas, roi_atlas.replace(atlas_hemi, contralat_atlas_hemi))
    return lateralized

# def get_parameters(projects):
#     """get parameters for nimb"""
#     parser = argparse.ArgumentParser(
#         formatter_class=argparse.RawDescriptionHelpFormatter,
#     )


#     parser.add_argument(
#         "-lhrh", required=False,
#         default="lh",
#         help="provide name to search for left and right hemispheres, devide by comma; example: lh,rh",
#     )

#     parser.add_argument(
#         "-test", required=False,
#         action='store_true',
#         help="when used, script will run only 2 participants",
#     )


#     params = parser.parse_args()
#     return params


# def main():
#     """
#         params  : from parameters defined by user, process, project
#         projects: parameters of all projects from credentials_path/projects.json
#     """
#     #check if python2
#     print('Please use python3.5 and up')
#     if sys.version_info <= (3,5):
#         sys.stdout.write("Please use python 3.5")
#         sys.exit(1)

#     project_ids = Get_Vars().get_projects_ids()
#     params      = get_parameters(project_ids)
#     project     = params.project
#     print(f'    project is: {project}')

#     all_vars    = Get_Vars(params)

#     app = NIMB(all_vars)
#     return app.run()


#     # Means_table_Thick = pd.DataFrame()
#     # Means_table_Thick = pd.concat([Mean_Group1.tail(1), Mean_Group2.tail(1), Mean_Group3.tail(1)], axis=0)
#     # Means_table_Thick = Means_table_Thick.iloc[: , 1:]

#     # X = Means_table_Thick.columns.tolist()
#     # Group1_Thick = Means_table_Thick.values[0]
#     # Group2_Thick = Means_table_Thick.values[1]
#     # Group3_Thick = Means_table_Thick.values[2]


# if __name__ == "__main__":
#     main()


# class LateralityAnalysis():
#     '''creates a pandas.DataFrame with laterality analysis using the formula:
#         laterality = ( feature - contralateral_feature ) / ( feature + contralateral_feature )
#     Args:
#         df: pandas.DataFrame to be used for columns
#         lhrh_feat_d: {'common_feature_name':('feature', 'contralateral_feature')}
#         file_name: name of the file.csv
#         PATH_save_results: abspath to save the file.csv
#     Return:
#         pandas.DataFrame csv file with results
#     '''

#     def __init__(self,
#                 df,
#                 lhrh_feat_d,
#                 file_name,
#                 PATH_save_results):

#         self.df          = df
#         self.lhrh_feat_d = lhrh_feat_d
#         self.file_name   = file_name
#         self.PATH_save   = PATH_save_results
#         self.run()

#     def run(self):

#         # df_lat = pd.DataFrame()

#         df_lat = db_processing.Table().get_clean_df()
#         for common_feature_name in self.lhrh_feat_d:
#             feat = self.lhrh_feat_d[common_feature_name][0]
#             contra_feat = self.lhrh_feat_d[common_feature_name][1]
#             df_lat[common_feature_name] = (self.df[feat]-self.df[contra_feat]) / (self.df[feat] + self.df[contra_feat])
#         df_lat.to_csv(os.path.join(self.PATH_save, f'{self.file_name}.csv'))