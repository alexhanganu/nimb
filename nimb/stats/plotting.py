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


def mkstatisticsfplots(PATHplots, datagroup, groupsfromf, id_col, group_col):
    #correlations must be made between clinical and structural, only abalon.
    Make_Dirs(PATHplots)
    sns.set()

    tmpdataf = pd.ExcelFile(datagroup)
    sheetnames = (tmpdataf.sheet_names)
    # groupsfromf = pd.read_excel(groupsf, sheet_name='foranalysis')
    groupsfromf.drop(id_col, axis = 1, inplace = True)

    def plotkde(datasheet, sheet):
        print('creating kde plot for sheet '+sheet)
        scatterpd = pd.plotting.scatter_matrix(datasheet, diagonal = 'kde')
        plt.savefig(PATHplots+'kde-'+sheet+'.png')
        plt.cla()

    def correlation_matrix(df, sheet, headers):
        from matplotlib import cm as cm
        print('creating abalone plot for sheet '+sheet)

        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        cmap = cm.get_cmap('jet', 30)
        cax = ax1.imshow(df.corr(), interpolation="nearest", cmap=cmap)
        ax1.grid(True)
        plt.title(sheet+' Abalone Feature Correlation')
        labels=headers
        ax1.set_xticklabels(labels,fontsize=5)
        ax1.set_yticklabels(labels,fontsize=5)
        # Add colorbar, make sure to specify tick locations to match desired ticklabels
        fig.colorbar(cax, ticks=[.75,.8,.85,.90,.95,1])
        plt.savefig(PATHplots+'abalone'+sheet+'.png', dpi = 150)
        plt.cla()

    def plotggplot(datasheet, sheet, group_col):
        plt.style.use('ggplot') #    matplotlib.style.use('ggplot')
        df = pd.concat([datasheet, groupsfromf], axis=1)
        print('creating ggplot for sheet '+sheet)
        print(df.columns.tolist())
        sns_plot = sns.pairplot(df, hue=group_col, height=2.5)
        sns_plot.savefig(PATHplots+"ggplot"+sheet+".png")
    '''
    based on the data.xlsx files create plots-scatter.xls file with statistical results for groups
    '''

    print('Creating the kde scatter plots and the abalone plots with statistical results for groups')
    for sheet in sheetnames[:3]:
        datasheet = pd.read_excel(datagroup, sheet_name=sheet)
        headers = datasheet.columns.values.tolist()
        if sheet == 'Segmentations':
            datasheet.drop(['5th-Ventricle',
                        'Left-WM-hypointensities',
                        'Right-WM-hypointensities',
                        'non-WM-hypointensities',
                        'Left-non-WM-hypointensities',
                        'Right-non-WM-hypointensities'], axis=1, inplace=True)
        plotkde(datasheet, sheet)
        correlation_matrix(datasheet, sheet, headers)
        # plotggplot(datasheet, sheet, group_col)


'''DISTRIBUTIONS AND GROUP DIFFERENCES
Kernel distribution with density estimation and fitting 
parametric distribution to visualize how closely it corresponds to the observed data'''
def Distributions_Compute_Plot(df_clin, group_col, groups, PATH2save_fig, PARAMETER_x_Age, PARAMETERS_INTEREST_y):

    sns_plot_dist_all = sns.distplot(np.array(df_clin[PARAMETER_x_Age]), rug=True, fit=stats.gamma)#fit a parametric distribu>
    plt.savefig(PATH2save_fig+'distribution_histo_all.png')
    plt.close()
    for PARAMETER_y in PARAMETERS_INTEREST_y:
        sns_scatterplot_dist_all = sns.jointplot(x=df_clin[PARAMETER_x_Age], y=df_clin[PARAMETER_y], kind='reg')
        sns_scatterplot_dist_all.savefig(PATH2save_fig+'scatterplot/distribution_scatterplot_all_'+PARAMETER_y+'.png')
        plt.close()
        sns_density_dist_all = sns.jointplot(x=df_clin[PARAMETER_x_Age], y=df_clin[PARAMETER_y], kind='kde')
        sns_density_dist_all.savefig(PATH2save_fig+'density/distribution_density_all_'+PARAMETER_y+'.png')
        plt.close()

    for group in groups:
        sns_plot_dist = sns.distplot(np.array(df_clin[df_clin[group_col] == group][PARAMETER_x_Age]), rug=True, fit=stats.gam>
        plt.savefig(PATH2save_fig+'distribution_histo_'+group+'.png')
        plt.close()
        for PARAMETER_y in PARAMETERS_INTEREST_y:
            sns_scatterplot_dist = sns.jointplot(x=df_clin[df_clin[group_col] == group][PARAMETER_x_Age], y=df_clin[df_clin[g>
            sns_scatterplot_dist.savefig(PATH2save_fig+'scatterplot/distribution_scatterplot_'+group+'_'+PARAMETER_y+'.png')
            plt.close()
            sns_density_dist = sns.jointplot(x=df_clin[df_clin[group_col] == group][PARAMETER_x_Age], y=df_clin[df_clin[group>
            sns_density_dist.savefig(PATH2save_fig+'density/distribution_density_'+group+'_'+PARAMETER_y+'.png')
            plt.close()

