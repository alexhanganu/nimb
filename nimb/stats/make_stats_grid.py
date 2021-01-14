'''
script creates the final grid file for statistical analysis
'''

from os import path
import preprocessing
from db_processing import Table
from stats.preprocessing import Preprocess

class MakeGrid:
    def __init__(self, project_vars, stats_vars):
        self.project_vars  = project_vars
        self.stats_vars    = stats_vars
        self.file_names    = stats_vars["STATS_FILES"]
        self.materials_DIR = project_vars['materials_DIR'][1]
        self.stats_HOME    = self.stats_vars["STATS_PATHS"]["STATS_HOME"]
        self.id_col        = project_vars['id_col']
        self.group_col     = project_vars['group_col']
        self.vars_4stats   = project_vars['variables_for_glm']
        self.tab           = Table()
        self.grid()

    def grid(self):
        self.get_main_stats()
        file_with_adjusted = self.get_base_file()
        if file_with_adjusted:
            df_adjusted = self.tab.get_df(file_with_adjusted,
                                          index = self.id_col)
            cols_X = self.tab.get_cols_tolist(df_adjusted)
        else:
            file_other_stats = self.get_files_other_stats()
            if file_other_stats:
                df_adjusted, cols_X = self.get_df_other_stats(file_other_stats)
            else:
                df_adjusted = []
                cols_X = []
        df_final_grid = self.tab.concat_dfs((self.df_stats, df_adjusted))
        self.tab.save_df(df_final_grid, path.join(self.stats_HOME, "grid.csv"), "grid")
        return self.df_stats, df_final_grid, df_adjusted, cols_X, self.groups

    def get_df_other_stats(self, ls_files):
        all_dfs = []
        for file_name in ls_files:
            path_2file = path.join(self.materials_DIR, file_name)
            df_tmp = self.tab.get_df(path_2file,
                                    index = self.id_col)
            all_dfs.append(df_tmp)
        df_adjusted = db_processing.concat_dfs(all_dfs)
        cols_X = self.tab.get_cols_tolist(df_adjusted)
        return df_adjusted, cols_X

    def get_files_other_stats(self):
        file_other_stats = []
        for file in ["fname_fs_all_stats", "fname_func_all_stats", "fname_other_stats"]:
            file_name = self.project_vars[file]
            if file_name:
                if file_name == "default":
                    file_name = self.file_names[file]
                file_name = f'{file_name}.{self.file_names["file_type"]}'
                path_2chk = path.join(self.materials_DIR, file_name)
                if path.exists(path_2chk):
                    file_other_stats.append(path_2chk)
        return file_other_stats

    def get_main_stats(self):
        grid_src = path.join(
                    self.stats_HOME,
                    self.project_vars["fname_groups"])
        self.df_stats = self.tab.get_df(grid_src,
                                   cols=[self.id_col, self.group_col]+self.vars_4stats,
                                   index = self.id_col)
        self.groups = Preprocess().get_groups(list(self.df_stats[self.group_col]))

    def get_base_file(self):
        file_with_adjusted = None
        for file in ["fname_Outcor", "fname_eTIVcor", "fname_NaNOcor"]:
            file_name = f'{self.file_names[file]}.{self.file_names["file_type"]}'
            path_2chk = path.join(self.materials_DIR, file_name)
            if path.exists(path_2chk):
                file_with_adjusted = path_2chk
                break
        return file_with_adjusted

    # def get_tables(self):
        # f_CoreTIVNaNOut = self.stats_params["file_name_corrected"]
        # atlas_sub = 'Subcort'
        # atlas_DK = 'DK'
        # atlas_DS = 'DS'
        # f_subcort    = path.join(self.project_vars['materials_DIR'][1], f_CoreTIVNaNOut+atlas_sub+'.xlsx')
        # f_atlas_DK   = path.join(self.project_vars['materials_DIR'][1], f_CoreTIVNaNOut+atlas_DK+'.xlsx')
        # f_atlas_DS   = path.join(self.project_vars['materials_DIR'][1], f_CoreTIVNaNOut+atlas_DS+'.xlsx')
        # self.df_stats = self.tab.get_df(path.join(self.project_vars['materials_DIR'][1], self.project_vars['GLM_file_group']),
                                    # usecols=[self.project_vars['id_col'], self.project_vars['group_col']]+self.project_vars['variables_for_glm'],
                                    # index_col = self.project_vars['id_col'])
        # self.df_adjusted, self.cols_X = Preprocess.get_df(f_subcort, f_atlas_DK, f_atlas_DS,
                                                         # self.atlas, self.project_vars['id_col'])
        # self.df_final_grid = self.tab.join_dfs(self.df_stats, self.df_adjusted, how='outer')
