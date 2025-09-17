# !/usr/bin/env python
# coding: utf-8
# last update: 2022-03-27

# script intends to work specifically with sklearn and statistical modules

import os

import sklearn
import numpy as np
from distribution import utilities

class Preprocess:
    def __init__(self):
        self.sklearn_ver = sklearn.__version__
        self.save_json   = utilities.save_json


    def populate_missing_vals_2mean(self, df, cols):
        for col in cols:
            col_mean = df[col].mean()
            df[col]  = df[col].fillna(col_mean)
        return df


    def get_groups(self, groups_list):
        '''
        Args:
            groups_list = list with all group variables
        Return:
            list with only one group variable, no repetition
        '''
        groups = []
        for val in groups_list:
            if val not in groups:
                groups.append(val)
        return groups


    def outliers_get(self, df, file2save=None, change_to_nan=True):
        '''script check outliers on each column in a pandas.DataFrame
            Outlier is defined as a value bigger than 10% from column mean
            Outliers are changed to NaN
        Args:
            df: pandas.DataFrame to be checked
            id_col: name of the column to be used as id, to be added to the json file
            file2save: path to file with the json file with outliers will be saved
            change_to_nan: True - Outliers will be changed to nan
        Return:
            df: with Outliers to nan values or without changes
            outliers: dict{'index of outlier: column of outlier'}
        '''
        outliers = dict()
        for col in df:
            dataIn = df[col].to_numpy()
            outliers_index = self.outliers_find_with_iqr(dataIn)
            if outliers_index:
                for ix in outliers_index:
                    index_df_src = df.index.tolist()[ix]
                    outliers = self.populate_outliers(outliers, index_df_src, col, outliers_index[ix])
        if change_to_nan:
            df = self.outliers_change_to_nan(df, outliers)
        # if file2save:
        #     self.save_json(outliers, file2save)
        return df


    def outliers_find_with_iqr(self, dataIn, factor=15):
        '''code by K.Foe and Alex S, 20121009 (https://stackoverflow.com/questions/11686720/is-there-a-numpy-builtin-to-reject-outliers-from-a-list)
            find outliers based on InterQuartile Percentile, ONLY if data follows Gaussian distribution
        Args:
            dataIn: data to be checked, numpy.array
            factor: n*sigma range, default = 15; !!grid must be checked visually
        Return:
            outliers_index: dict() {index of value: value}
        '''
        outliers_index = dict()
        quant3, quant1 = np.percentile(dataIn, [75 ,25])
        iqr            = quant3 - quant1
        iqrSigma       = iqr/1.34896
        medData        = np.median(dataIn)
        for i in range(len(dataIn)):
            x = dataIn[i]
            if not ( (x > medData - factor* iqrSigma)
                    and (x < medData + factor* iqrSigma) ):
                outliers_index[i] = x
        return outliers_index


    def populate_outliers(self, d, index, col, val):
        if index not in d:
            d[index] = dict()
        if col not in d[index]:
            d[index][col] = val
        return d


    def outliers_change_to_nan(self, df, outliers):
        for ix in list(outliers.keys()):
            for col in outliers[ix]:
                df.loc[ix, col] = np.nan
        return df


    def nan_rm_cols_if_more(self, df, cols, threshold = 0.05):
        '''if NaN number is more than threshold:
                column is removed
        Args:
            df: pandas.DataFrame
            cols: columns with NaNs
            threshold: level to be considered to columns deletion; 0.05 = 5%
        Return:
            df: new pandas.DataFrame with removed columns
        '''
        cols2rm = list()
        for col in cols:
            nan_sum = df[col].isna().sum()
            if nan_sum > len(df[col])*threshold:
                print(f'    removing column: {col}, {nan_sum}, {len(df[col])}')
                cols2rm.append(col)
        if cols2rm:
            df.drop(columns = cols2rm, inplace=True)
        for col in cols2rm:
            cols.remove(col)
        return df, cols


def rm_feats_with_zeros(df,
                        remove = False,
                        path2log = None):
    '''script searches for columns that have at least 1 zero
        for ANOVA and PCA zeros must be removed
    Args:
        df = pandas.DataFrame
    Return:
        cols_with_zeros = list() of columns that have zeros
   '''
    cols_with_zeros = list()
    for col in df:
        n = df[col].isin([0]).sum()
        if n>0:
            cols_with_zeros.append(col)

    # alternative code:
    # show number of value of zeros per column:
    #(df == 0).astype(int).sum(axis=0)
    # show number of value of zeros per row:
    #(df == 0).sum(axis=1)
    
    # removing features with zeros
    if remove:
        df.drop(columns = cols_with_zeros, inplace = True)

    # saving columns with zeros to a log file
    if path2log == None:
        path2log = os.path.join(os.getcwd(), "features_with_zeros.txt")
    with open(path2log, 'w') as f:
        f.write("INFO: features with zeros are:\n\n")
        if remove:
            f.write("INFO: features were removed from the grid\n\n")
        for feat in cols_with_zeros:
            f.write(feat+"\n")

    return df, cols_with_zeros


def get_missing_nan_values(df, 
                        features,
                        id_col = "default",
                        remove = False,
                        path2log = None):
    '''
        script iterates through ids to extract columns / features with NaN/None
        populates dictionary with missing values
    Args:
        df = pandas.DataFrame
        features = list(pandas.DataFrame.columns)
        id_col = feature name (column) with ids, but can be ommited
    Return:
        d_nan = {id: [column, column]}
        ls_cols = list(columns with NaN)
    '''
    d_nan = dict()
    ls_cols_with_nan = list()
    for col in features:
        if df[col].isnull().values.any():
            ls_cols_with_nan.append(col)

    for col in ls_cols_with_nan:
        ls_nan_trues = df[col].isnull().tolist()
        for ix in df.index:
            if id_col != "default":
                _id = df.at[ix, id_col]
            value = df.at[ix, col]
            if ls_nan_trues[ix]:
                if id_col != "default":
                    if _id not in d_nan:
                        d_nan[_id] = list()
                    d_nan[_id].append(col)
                else:
                    if ix not in d_nan:
                        d_nan[ix] = list()
                    d_nan[ix].append(col)

    # removing features with NaN/None
    if remove:
        df.drop(columns = ls_cols_with_nan, inplace = True)

    # saving columns with NaN/None to a log file
    if path2log == None:
        path2log = os.path.join(os.getcwd(), "features_with_nan.txt")
    with open(path2log, 'w') as f:
        f.write("INFO: features with NaN/None are:\n\n")
        if remove:
            f.write("INFO: features were removed from the grid\n\n")
        for feat in ls_cols_with_nan:
            f.write(feat+"\n")

    return df, d_nan, ls_cols_with_nan


def scale_X(df, algo = 'power'):
    """
        X_Scaled: normalize x, all features, return as array
        df: x data before transform
        scaler: scaler for x
    """
    '''
    #scales: StandardScaler(),
            PowerTransformer(),
            QuantileTransformer(),
            RobustScaler()
    PowerTransformer is a parametric, monotonic transformation that applies a power transformation to each feature to make the data more Gaussian-like. It finds the optimal scaling factor to stabilize variance and mimimize skewness through maximum likelihood estimation. PowerTransformer uses the Yeo-Johnson transformed, applies zero-mean, unit variance normalization to the transformed output. This is useful for modeling issues related to heteroscedasticity (non-constant variance), or other situations where normality is desired.
    '''
    if algo == "power":
        from sklearn.preprocessing import PowerTransformer #!! there is an issue with using directly sklearn.preprocessing.PowerTransformer
        scaler = PowerTransformer()
    elif algo == "quantile":
        from sklearn.preprocessing import QuantileTransformer
        scaler = QuantileTransformer()
    print(f'    scaler: {scaler.fit(df)}')
    X_Scaled = scaler.transform(df)
    return X_Scaled


def label_y(df, target):
    """
        y_labeled: y after encoded to 1 and zero using label encoder
        le: label encoder for y
    """
    le = sklearn.preprocessing.LabelEncoder()
    le.fit(df[target])
    y_labeled = le.transform(df[target])

    return y_labeled


def preprocessing_data(data, target):
    """
    preprocessing
    :param data: read from excel
    :return:
        X_scaled: normalize x, all features
        y_labeled: y after encoded to 1 and zero using label encoder
        data_x: x data before transform
        x_scaler: minmax scaler for x
    """
    y_labeled = label_y(data, target)

    # create the X data
    data_x = data.drop(labels=[target], axis=1)
    X_scaled = scale_X(data_x, algo = 'quantile')

    return X_scaled, y_labeled, data_x


def Z_Scores_create():
    #Alternatively use the scikit feature to create z-values
    #http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html
    #sklearn.preprocessing.StandardScaler.fit_transform
    #dfz_sk = pd.read_excel(path+'tmp.xlsx', sheetname='Sheet1')
    #from sklearn import preprocessing

    #scaler= preprocessing.StandardScaler()

    #dfz_prep = pd.DataFrame(scaler.fit_transform(dfz_sk.T), columns=dfz_sk.columns, index=dfz_sk.index)
    dfzvalues = df_all_data.copy(deep=True) #code from Jonathan Eunice, stockoverflow
    columns_2_drop = ['subject','Age','group','Duration_of_Disease','Edu_years_completed']
    df_with_nonchanged_data = dfzvalues[columns_2_drop]
    dfzvalues.drop(columns=columns_2_drop, inplace=True)
    writer = pd.ExcelWriter(PATH_to_save_results+'materials_all_data_zvalues.xlsx', engine='xlsxwriter')

    for col in dfzvalues.select_dtypes([np.number]):
        col_mean = dfzvalues[col].mean()
        col_std = dfzvalues[col].std()
        dfzvalues[col] = dfzvalues[col].apply(lambda x: (x-col_mean) / col_std)

    frame_final = (df_with_nonchanged_data, dfzvalues)
    dfzvalues = pd.concat(frame_final,axis=1)
    dfzvalues.to_excel(writer)
    writer.save()

def get_features_clean(df, ls_feats_2rm, ls_params_2rm):
    ls_of_features_2plot = list()
    for feat in df.columns.tolist():
        feat_ok = True
        for feat2rm in ls_feats_2rm:
            if feat == feat2rm:
                feat_ok = False
                break
        if feat_ok:
            for var2rm in ls_params_2rm:
                feat = feat.replace(var2rm,"")
            if feat not in ls_of_features_2plot:
                ls_of_features_2plot.append(feat)
    return ls_of_features_2plot