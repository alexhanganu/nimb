# !/usr/bin/env python
# coding: utf-8
# last update: 2020-08-21
# script intends to work specifically with pandas on the excel and csv files


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

class Table:
    def __init__(self):
        self.pd_ver = pd.__version__

    def get_df(self, path2file):
        '''reads a csv, xls or an xlsx file
        '''
        if '.csv' in path2file:
            return pd.read_csv(path2file)
        if path2file.endswith('.xls'):
            return pd.read_excel(path2file)
        if path2file.endswith('.xlsx'):
            return pd.read_excel(path2file, engine='openpyxl')


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
        df.to_excel(f_path_to_save, sheet_name=sheet_name)

    def save_df_tocsv(self, df, f_path_to_save):
        df.to_csv(f_path_to_save)


    def get_df_per_parameter(self, df, param_col, param):
        return df[df[param_col] == param]

    def get_df_with_columns(self, path2file, columns_only):
        df = get_df(path2file)
        cols2drop = list()
        for col in df.columns.tolist():
            if col not in columns_only:
                cols2drop.append(col)
        if cols2drop:
            df.drop(columns=cols2drop, inplace=True)
        return df