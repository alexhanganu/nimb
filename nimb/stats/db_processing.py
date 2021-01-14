# !/usr/bin/env python
# coding: utf-8
# last update: 2020-08-21
# script intends to work specifically with pandas on xlx, xlsx and csv files

import sys
try:
    import pandas as pd
    import xlrd
    import openpyxl
    from pathlib import Path
except ImportError as e:
    print('could not import modules: pandas or xlrd or openpyxl.\
        try to install them using pip, or use the miniconda run with the command located \
        in credentials_path.py/local.json -> miniconda_python_run')
    sys.exit(e)
from distribution.utilities import save_json

class Table:
    def __init__(self):
        self.pd_ver = pd.__version__

    def get_df(self, path2file, sheetname = 0, cols = None, index = None, rename=False):
        print(f"    reading file: {path2file},\n        sheet: {sheetname}")
        df = self.read_df(path2file, sheetname, cols)
        if index:
            df = self.change_index(df, index)
        if rename:
            df.rename(columns = rename, inplace=True)
        return df

    def read_df(self, path2file, sheetname, cols):
        '''reads a csv, xls or an xlsx file
        '''
        if path2file.endswith('.csv'):
            return pd.read_csv(path2file, sheet_name = sheetname, usecols = cols)
        if path2file.endswith('.xls'):
            return pd.read_excel(path2file, sheet_name = sheetname, usecols = cols)
        if path2file.endswith('.xlsx'):
            return pd.read_excel(path2file, engine='openpyxl', sheet_name = sheetname, usecols = cols)

    def change_index(self, df, index):
        '''to set the index, based on column with str name
        '''
        return df.set_index(index)

    def get_df_index(self, file, index_col='default'):
        if index_col=='default':
            df = pd.read_excel(file)
        elif index_col != 'default':
            df = pd.read_excel(file, index_col = index_col)
        return df

    def get_df_from_df(self, df, usecols):
        return df[usecols]

    def join_dfs(self, df1, df2, how='outer'):
        return df1.join(df2, how=how)

    def get_cols(self, df):
        return df.columns

    def get_cols_tolist(self, df):
        return df.columns.tolist()

    def get_clean_df():
        return pd.DataFrame()

    def create_df(self, vals, index_col, cols):
        return pd.DataFrame(vals, index = index_col, columns=cols)

    def create_df_from_dict(self, d):
        return pd.DataFrame(d)

    def rm_cols_from_df(self, df, cols):
        return df.drop(columns=cols)

    def save_df(self, df, f_path_to_save, sheet_name):
        if f_path_to_save.endswith('.csv'):
            df.to_csv(f_path_to_save)
        elif f_path_to_save.endswith('.xls') or f_path_to_save.endswith('.xlsx'):
            df.to_excel(f_path_to_save, engine='openpyxl', sheet_name=sheet_name)

    def save_df_tocsv(self, df, f_path_to_save):
        df.to_csv(f_path_to_save)

    def get_df_per_parameter(self, df, param_col, param):
        return df[df[param_col] == param]

    def get_df_with_columns(self, path2file, columns_only):
        df = self.get_df(path2file)
        cols2drop = list()
        for col in df.columns.tolist():
            if col not in columns_only:
                cols2drop.append(col)
        if cols2drop:
            df.drop(columns=cols2drop, inplace=True)
        return df

    def check_nan(self, df, err_file_abspath):
        d_err = dict()
        cols_with_nans = list()
        for col in df.columns:
            if df[col].isnull().values.any():
                ls = df[col].isnull().tolist()
                for val in ls:
                    if val:
                        ix = df.index[ls.index(val)]
                        if ix not in d_err:
                            d_err[ix] = list()
                        if col not in d_err[ix]:
                            d_err[ix].append(col)
                        if col not in cols_with_nans:
                            cols_with_nans.append(col)
        save_json(d_err, err_file_abspath)
        return d_err, cols_with_nans

    def concat_dfs(self, frames, ax=1, sort = True):
        '''
            frames: tuple of DataFrames to concatenate
            default ax = 1 concatenates based on the index
        '''
        return pd.concat(frames, axis=ax, sort=sort)

    def get_rows_with_nans(self, df):
        return list(df.loc[pd.isnull(df).any(1), :].index.values)

    def get_nan_from_col(self, df, col):
        return df[col].isnull().tolist()

    def rm_rows_with_nan(self, df, col2chk=None, reset_index = False):
        if col2chk:
            vals_nan = self.get_nan_from_col(df, col2chk)
            idxs_2rm = [i for i in df.index if vals_nan[df.index.tolist().index(i)]]
        else:
            idxs_2rm = self.get_rows_with_nans(df)
        if idxs_2rm:
            print('    removing rows with NAN')
            df.drop(idxs_2rm, axis = 0, inplace = True)
            if reset_index:
                df.reset_index(drop = True, inplace = True)
        return df


def get_df_with_params(df, params):

    ls_cols_2get = list()
    for val in df.columns:
        for param in params:
            if param in val:
                ls_cols_2get.append(val)
    print(ls_cols_2get)

    return df_subcort_atlas, ls_cols_X_atlas
    
def get_df_for_fs_atlas(f_subcort, f_atlas_DK, f_atlas_DS, atlas, id_col):
    cols_DK = [id_col,'cortex_thickness_ThickL_DK', 'cortex_vol_VolR_DK', 'cortex_area_AreaL_DK']
    df_subcort = db_processing.get_df(f_subcort,
                                        usecols=False,
                                        index_col = id_col)
    if 'DK' in atlas:
        df_atlas = db_processing.get_df(f_atlas_DK,
                                    usecols=False,
                                    index_col = id_col)
        if 'DS' in atlas:
            df_atlas_DS = db_processing.get_df(f_atlas_DS,
                                    usecols=False,
                                    index_col = id_col)
            df_atlas = db_processing.join_dfs(df_atlas, df_atlas_DS)
    if atlas == 'DS':
        df_atlas = db_processing.get_df(f_atlas_DS,
                                    usecols=False,
                                    index_col = id_col)
    df_sub_and_cort = db_processing.join_dfs(df_subcort, df_atlas)
    ls_cols_X = db_processing.get_cols_tolist(df_sub_and_cort)
    return df_sub_and_cort, ls_cols_X