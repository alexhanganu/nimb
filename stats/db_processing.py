# !/usr/bin/env python
# coding: utf-8
# last update: 2020-08-21
# script intends to work specifically with pandas on the excel and csv files


import pandas as pd

def get_pandas_version():
	return pd.__version__

def get_df(file, usecols = False, index_col='default'):
	if not usecols and index_col=='default':
		df = pd.read_excel(file)
	elif not usecols and index_col != 'default':
		df = pd.read_excel(file, index_col = index_col)
	else:
		df = pd.read_excel(file, index_col = index_col, usecols=usecols)
	return df

def get_df_from_df(df, usecols):
	return df[usecols]

def join_dfs(df1, df2, how='outer'):
	return df1.join(df2, how=how)

def get_cols(df):
	return df.columns

def get_cols_tolist(df):
	return df.columns.tolist()

def get_clean_df():
	return pd.DataFrame()

def create_df(vals, index_col, cols):
	return pd.DataFrame(vals, index = index_col, columns=cols)

def create_df_from_dict(d):
	return pd.DataFrame(d)

def rm_cols_from_df(df, cols):
	return df.drop(columns=cols,inplace=True)

def save_df(df, f_path_to_save, sheet_name):
	df.to_excel(f_path_to_save, sheet_name=sheet_name)

def save_df_tocsv(df, f_path_to_save):
	df.to_csv(f_path_to_save)