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

def Make_plot_group_difference(data_groups_anova, col, measurement, structure, PATH_plots_groups, group_col, groups):
    df = pd.DataFrame({'Groupe':data_groups_anova[group_col],\
                  groups[0]:data_groups_anova[data_groups_anova[group_col] == groups[0]][col],\
                  groups[1]:data_groups_anova[data_groups_anova[group_col] == groups[1]][col]})
    df = df[['Groupe',groups[0],groups[1]]]
    dd=pd.melt(df,id_vars=['Groupe'],value_vars=[groups[0],groups[1]],var_name=col)
    group_plot = sns.boxplot(x='Groupe',y='value',data=dd,hue=col)
    group_plot.figure.savefig(PATH_plots_groups+'/'+structure+'_'+measurement)
    plt.close()

def Make_Plot_Regression(data_groups_anova, col, parameter,model, measurement, structure, PATH_plots_regression, group_col):
    df_plot = pd.DataFrame({
        'Groupe':np.array(data_groups_anova[group_col]),
        parameter:np.array(data_groups_anova[parameter]),
        col:np.array(data_groups_anova[col])})
    sns_plot = sns.lmplot(x=parameter, y=col,hue='Groupe', data=df_plot)#, robust=True
    axes = sns_plot.axes.flatten()
    axes[0].set_title('Groupe diff. p='+str('%.4f'%model.pvalues.x)+'; intercept='+str('%.4f'%model.pvalues.Intercept))
    sns_plot.savefig(PATH_plots_regression+'/'+structure+'_'+measurement+'.png')
    plt.close()
