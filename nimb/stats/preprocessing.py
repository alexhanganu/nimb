# !/usr/bin/env python
# coding: utf-8
# last update: 2020-03-27

# script intends to work specifically with sklearn and statistical modules


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



def scale_X(df):
    """
        X_Scaled: normalize x, all features, return as array
        df: x data before transform
        scaler: scaler for x
    """
    '''
    #scales: StandardScaler(), PowerTransformer(), QuantileTransformer(), RobustScaler()
    PowerTransformer is a parametric, monotonic transformation that applies a power transformation to each feature to make the data more Gaussian-like. It finds the optimal scaling factor to stabilize variance and mimimize skewness through maximum likelihood estimation. PowerTransformer uses the Yeo-Johnson transformed, applies zero-mean, unit variance normalization to the transformed output. This is useful for modeling issues related to heteroscedasticity (non-constant variance), or other situations where normality is desired.
    '''
    from sklearn.preprocessing import PowerTransformer #!! there is an issue with using directly sklearn.preprocessing.PowerTransformer
    scaler = PowerTransformer()
    print(scaler.fit(df))
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