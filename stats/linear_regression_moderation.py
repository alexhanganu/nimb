# !/usr/bin/env python
# coding: utf-8
# last update: 2020-04-06

# logistic regression on 2 variables
# also called moderation analysis

# Lynn Valeyry Verty, Alex Hanganu.

from sklearn.linear_model import LinearRegression
import statsmodels.api as sm


def get_main_dict(group_param, regression_param):
    d = {}
    for i in ('R2_adjusted'+'_'+group_param+'_'+regression_param,
              'p_'+group_param,'p_'+regression_param,
              'B_'+group_param,'B_'+regression_param,
              'Intercept'):
        d[i] =[]
    return d

def compute_linreg_data(df, ls_cols_X, group_param, regression_param):
    d1 = get_main_dict(group_param, regression_param)
    d1['Region'] = ls_cols_X
    X = df[[group_param, regression_param]]
    X = sm.add_constant(X.to_numpy())
    
    for region in ls_cols_X:
        y = df[[region]]
        model = sm.OLS(y, X).fit()
        reg = LinearRegression().fit(X, y)
        #predictions = model.predict(X)        
        #d1['R-deux'].append(model.rsquared)
        d1['R2_adjusted'+'_'+group_param+'_'+regression_param].append(model.rsquared_adj)
        d1['p_'+group_param].append(model.pvalues.x1)
        d1['p_'+regression_param].append(model.pvalues.x2)
        d1['B_'+group_param].append((reg.coef_[0])[1])
        d1['B_'+regression_param].append((reg.coef_[0])[2])
        d1['Intercept'].append(reg.intercept_[0])
    return d1