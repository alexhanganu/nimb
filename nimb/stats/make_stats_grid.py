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
        self.stats_HOME    = self.stats_vars["STATS_PATHS"]["STATS_HOME"]
        self.id_col        = project_vars['id_col']
        self.group_col     = project_vars['group_col']
        self.vars_4stats   = project_vars['variables_for_glm']
        self.miss_val_file = path.join(self.stats_HOME, "missing_values.json")
        self.tab           = Table()
        self.preproc       = Preprocess()
        self.cp2materials  = []

    def grid(self):
        self.get_main_stats()
        file_with_adjusted = self.get_base_file()
        if file_with_adjusted:
            df_final_grid = self.tab.get_df(file_with_adjusted,
                                          index = self.id_col)
            cols_grid = self.tab.get_cols_tolist(df_final_grid)
            cols_X    = [i for i in cols_grid if i not in self.df_stats.columns]
            df_adjusted = df_final_grid[cols_X]
        else:
            file_other_stats = self.get_files_other_stats()
            if file_other_stats:
                df_adjusted, cols_X = self.get_df_other_stats(file_other_stats)
                df_final_grid = self.tab.concat_dfs((self.df_stats, df_adjusted))
            else:
                df_adjusted = []
                cols_X = []
                df_final_grid = self.df_stats
            df_final_grid = self.check_nans(df_final_grid)
            path2save = path.join(self.stats_HOME, "grid.csv")
            self.tab.save_df(df_final_grid, path2save, "grid")
            self.cp2materials.append(path2save)
            self.copy_2materials()
        return self.df_stats, df_final_grid, df_adjusted, cols_X, self.groups

    def check_nans(self, df):
        rows_nan = self.tab.get_rows_with_nans(df)
        if rows_nan:
            print(f'There are missing values. These are first 10 rows with mssing values: {rows_nan[:10]}')
            return self.populate_missing_data(df)
        else:
            return df

    def populate_missing_data(self, df):
        """Some values are missing. If number of missing values is lower then 5%,
            missing values are changed to group mean
            else: columns is excluded
        """
        df_groups = dict()
        _, cols_with_nans = self.tab.check_nan(df, self.miss_val_file)
        self.cp2materials.append(self.miss_val_file)
        for group in self.groups:
            df_group = self.tab.get_df_per_parameter(df, self.group_col, group)
            df_group = self.preproc.populate_missing_vals_2mean(df_group, cols_with_nans)
            df_groups[group] = df_group
        frames = (df_groups[i] for i in df_groups)
        df_meaned_vals = self.tab.concat_dfs(frames, ax=0, sort=True)
        # df_meaned_vals = pd.concat_dfs(frames, axis=0, sort=True)
        for col in cols_with_nans:
            df[col] = df_meaned_vals[col]
        df.index.name = self.id_col
        file_name = f'{self.file_names["fname_NaNcor"]}.{self.file_names["file_type"]}'
        path2save = path.join(self.stats_HOME, file_name)
        print(f'Missing values were corrected to group mean. File saved at: {path2save}')
        self.tab.save_df(df, path2save, "grid")
        self.cp2materials.append(path2save)
        return df


    def get_df_other_stats(self, ls_files):
        all_dfs = []
        for file_name in ls_files:
            path_2file = path.join(self.stats_HOME, file_name)
            df_tmp = self.tab.get_df(path_2file,
                                    index = self.id_col)
            all_dfs.append(df_tmp)
        df_adjusted = self.tab.concat_dfs(all_dfs)
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
                path_2chk = path.join(self.stats_HOME, file_name)
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
        self.groups = self.preproc.get_groups(list(self.df_stats[self.group_col]))

    def get_base_file(self):
        file_with_adjusted = None
        for file in ["fname_Outcor", "fname_eTIVcor", "fname_NaNcor"]:
            file_name = f'{self.file_names[file]}.{self.file_names["file_type"]}'
            path_2chk = path.join(self.stats_HOME, file_name)
            if path.exists(path_2chk):
                file_with_adjusted = path_2chk
                break
        return file_with_adjusted

    def copy_2materials(self):
        if self.cp2materials:
            print(f'must copy to materials: {self.cp2materials}')