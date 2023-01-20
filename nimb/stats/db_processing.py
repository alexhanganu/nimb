# !/usr/bin/env python
# coding: utf-8
# last update: 2020-08-21
# script intends to work specifically with pandas on xlx, xlsx and csv files
# https://pandas.pydata.org/docs/user_guide/index.html

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

import logging
log = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s:%(asctime)s| %(message)s')
log.setLevel(logging.INFO)

class Table:
    def __init__(self):
        self.pd_ver = pd.__version__


    def get_df(self,
               path2file,
               sheetname = 0,
               cols = None,
               index = None,
               rename = False,
               remove_Unnamed = False):
        """returns a pandas.DataFrame
        path2file: absolute path to file to read
        sheetname = name of a sheet to read
        cols = list of columns to read
        index = if provided, the index will be changed to the one provided
        rename: if True, the name of the file will be changed
        remove_Unnamed: if True, the default created columns Unnamed will be removed
        """
        log.info(f"        reading file: {path2file}\n    sheet: {sheetname}")
        df = self.read_df(path2file, sheetname, cols)
        if index:
            df = df.set_index(index)
        if rename:
            df.rename(columns = rename, inplace=True)
        if remove_Unnamed:
            df = self.rm_cols_from_df(df, ["Unnamed: 0",])
        return df


    def change_index(self, df, index):
        '''to set the index, based on column
        Args:
            index = str(column name)
        '''
        return df.set_index(index)


    def read_df(self, path2file, sheetname, cols):
        '''reads a csv, xls or an xlsx file
        '''
        df = self.get_clean_df()
        if path2file.endswith('.csv'):
            log.info(f"        this a csv file")
            try:
                df = pd.read_csv(path2file, sep = '\s+', usecols = cols)
                if len(df.columns) == 1:
                    try:
                        df = pd.read_csv(path2file, usecols = cols)
                    except Exception as e:
                        log.info(e)
            except ValueError as e:
                try:
                    df = pd.read_csv(path2file, delim_whitespace=True, usecols = cols)
                except Exception as e:
                    log.info(e)
                    try:
                        df = pd.read_csv(path2file, sep = ",", usecols = cols)
                    except Exception as e:
                        log.info(e)
        if path2file.endswith('.xls'):
            log.info(f"        this a xls file")
            df =  pd.read_excel(path2file, sheet_name = sheetname, usecols = cols)
        if path2file.endswith('.xlsx'):
            log.info(f"        this a xlsx file")
            df =  pd.read_excel(path2file, engine='openpyxl', sheet_name = sheetname, usecols = cols)
        return df


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


    def get_clean_df(self):
        return pd.DataFrame()


    def create_df(self, vals, index_col, cols):
        return pd.DataFrame(vals, index = index_col, columns=cols)


    def create_df_from_dict(self, d):
        return pd.DataFrame(d)


    def rm_cols_from_df(self, df, cols):
        return df.drop(columns=cols)


    def save_df(self, df, f_path_to_save, sheet_name = 'nimb_created'):
        if f_path_to_save.endswith('.csv'):
            df.to_csv(f_path_to_save)
        elif f_path_to_save.endswith('.xls') or f_path_to_save.endswith('.xlsx'):
            df.to_excel(f_path_to_save, engine='openpyxl', sheet_name=sheet_name)
        elif f_path_to_save.endswith('.tsv'):
            df.to_csv(f_path_to_save, index=True, sep="\t", header=True)


    def save_df_tocsv(self, df, f_path_to_save):#must be avoides in order to rm
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

    def get_dict_with_tables_per_param(self,
                                       df,
                                       variables,
                                       var_col):
        """extracting data per parameter
        Args:
            df = pandas.DataFrame with variables to be extracted
            variables = list() of variables in str() format, for example groups
            var_col = str() name of the pandas.DataFrame column that has the variables
        Return:
            df_per_vars = {"var1":pandas.DataFrame of var1,
                            "var2":pandas.DataFrame of var2,}
        """
        df_per_vars = {}
        for var in variables:
            df_per_vars[var] = dict()
            df_per_vars[var] = df[df[var_col] == var]
        return df_per_vars


    def get_df_with_mean_of_feats_combined(self,
                                           df,
                                           feats_combined):
        """in the pandas.DataFrames
            will create a column with the means of the
            features from feats_combined
        Args:
            df = pandas.DataFrame
            feats_combined = {feat_name_combined: [feature_1,feature_2,feature_n]}
        Return:
            pandas.DataFrame with feats per feat_name_combined
        """
        cols_2rm = list()
        for feature_main in feats_combined:
            cols = feats_combined[feature_main]
            cols_2rm = cols_2rm + cols
            df[feature_main] = df[cols].mean(axis = 1)
        df = self.rm_cols_from_df(df, cols_2rm)
        return df


    def val_is_nan(self, val):
        return pd.isna(val)


    def get_feats_per_lobe(self,
                            ls_features_2combine,
                            ls_features_all):
        """creates a dict() with features per ls_features_2combine
        Args:
            ls_features_2combine = list() of features to be searched for and based on them combine other features
            ls_features_all = list() of all features
        Return:
            {feature_common: [features,]}
        """
        feats_per_common = dict()
        for feat in ls_features_all:
            feat_ok = False
            for feat_combined in ls_features_2combine:
                if feat_combined not in feats_per_common:
                    feats_per_common[feat_combined] = list()
                if feat_combined in feat:
                    feats_per_common[feat_combined].append(feat)
                    feat_ok = True
                    break
                else:
                    feat_ok = False
            if not feat_ok:
                print("not feat: ", feat_hemi)
        return feats_per_common


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


    def check_str_columns(self, df):
        """verifies columns for str()
        """
        for col in df.columns:
            for value in df[col].tolist():
                if value.__str__().isalpha():
                    print("value: ", value, " is string")


    def concat_dfs(self, frames, ax=1, sort = True):
        '''
            frames: tuple of DataFrames to concatenate
            default ax = 1 concatenates based on the index
        '''
        return pd.concat(frames, axis=ax, sort=sort)


    def get_rows_with_nans(self, df):
        return list(df.loc[pd.isnull(df).any(1), :].index.values)


    def get_index_of_val(self, df, col, val):
        """
            get the index of the value
            if multiple indices are present:
                only the first is provided
        """
        try:
            return list(df[df[col] == val].index.values)[0]
        except IndexError:
            return None


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


    def get_value(df, index, col):
        return df.at[index, col]


    def change_val(self,df, index, col, new_val):
        """
            change to new_val the value located in position: index: col
        """
        df.at[index, col] = new_val
        return df


    def rm_row(self,df, index):
        df.drop(index, axis = 0, inplace = True)
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
