# !/usr/bin/env python
# coding: utf-8
# last update: 2020-03-27

# script intends to do all the plots


import matplotlib.pyplot as plt
import seaborn as sns


def plot_simple(vals, xlabel, ylabel, path_to_save_file):
    plt.plot(vals)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.savefig(path_to_save_file)

def plot_features(df): #written by Lynn Valeyry Verty, adapted by Alex Hanganu
    plt.figure(figsize=(20, 10))
    plt.pcolor(df, cmap = 'bwr')
    plt.yticks(np.arange(0.5, len(df.index), 1), df.index)
    plt.xticks(rotation=90)
    plt.xticks(np.arange(0.5, len(df.columns), 1), sorted(df.columns))
    plt.title('All Parameters', loc='center')
    plt.show()

def Make_plot_group_difference(df, param_feat, group_col, groups, PATH_plots_groups):
    for param_y in param_features:
        for feat in param_features[param_y]:
            df_group = pd.DataFrame({'group':df[group_col],\
                  groups[0]:df[df[group_col] == groups[0]][feat],\
                  groups[1]:df[df[group_col] == groups[1]][feat]})
            df_2 = df_group[['group', groups[0], groups[1]]]
            dd=pd.melt(df_2, id_vars=['group'], value_vars=[groups[0], groups[1]], var_name=feat)
            group_plot = sns.boxplot(x='group', y='value', data=dd, hue=feat)
            group_plot.figure.savefig(path.join(PATH_plots_groups,'{}_{}.png'.format(param_features[param_y][feat]['struct'], param_features[param_y][feat]['meas'])))
            plt.close()

def Make_Plot_Regression(df, param_features, group_col,
                         PATH_plots_regression):

    for param_y in param_features:
        for feat in param_features[param_y]:
            df_plot = pd.DataFrame({
                'group':np.array(df[group_col]),
                parameter:np.array(df[param_y]),
                col:np.array(df[col])})
            sns_plot = sns.lmplot(x=parameter, y=col, hue='group', data=df_plot)#, robust=True
            axes = sns_plot.axes.flatten()
            axes[0].set_title('Group diff. p='+str('%.4f'%param_features[param_y][feat]['pvalues'])+'; intercept='+str('%.4f'%param_features[param_y][feat]['intercept']))
        #    axes[0].set_title('Group diff. p='+str('%.4f'%model.pvalues.x)+'; intercept='+str('%.4f'%model.pvalues.Intercept))
            sns_plot.savefig(path.join(PATH_plots_regression, '{}_{}_{}.png'.format(param_y,param_features[param_y][feat]['struct'], param_features[param_y][feat]['meas'])))
            plt.close()
