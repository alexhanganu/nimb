# !/usr/bin/env python
# coding: utf-8
# last update: 2020-03-27

# script intends to work specifically with sklearn and statistical modules


'''
PowerTransformer is a parametric, monotonic transformation that applies a power transformation to each feature to make the data more Gaussian-like.
The power transform finds the optimal scaling factor to stabilize variance and mimimize skewness through maximum likelihood estimation.
PowerTransformer uses the Yeo-Johnson transformed, applies zero-mean, unit variance normalization to the transformed output.
This is useful for modeling issues related to heteroscedasticity (non-constant variance), or other situations where normality is desired.
'''
import sklearn
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import PowerTransformer as scale #StandardScaler, PowerTransformer QuantileTransformer, RobustScaler 

from stats import db_processing#, varia

def get_df(f_subcort, f_atlas_DK, f_atlas_DS, atlas, id_col):
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


def get_df_with_params(df, params):

    ls_cols_2get = list()
    for val in df.columns:
        for param in params:
            if param in val:
                ls_cols_2get.append(val)
    print(ls_cols_2get)

    return df_subcort_atlas, ls_cols_X_atlas

def scale_X(df):
    """
        X_Scaled: normalize x, all features, return as array
        df: x data before transform
        scaler: scaler for x
    """
    scaler = scale()
    print(scaler.fit(df))
    X_Scaled = scaler.transform(df)
    return X_Scaled

def label_y(df, target):
    """
        y_labeled: y after encoded to 1 and zero using label encoder
        le: label encoder for y
    """
    le = LabelEncoder()
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

class Preprocess:
    def __init__(self):
        self.sklearn_ver = sklearn.__version__

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