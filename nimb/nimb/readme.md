NeuroImaging My Brain = NIMB

Pipeline for MRI analysis:
* deploys T1, Flair, DWI for pre-processing on Compute Canada cluster/ clusters;
* extracts stats for individual participants
* checks data/ resuls
* moves data from the cluster to the local database
* performs GLM
  => FreeSurfer GLM
    * saves FDR corrected images
    * save MonteCarlo corrected images
  => python stats on data
    * distribution (seaborn.distplot; seaborn.jointplot)
    * group descriptions (scipy.stats: ttest_ind, f_oneway, bartlett, mannwhitneyu, kruskal)
    * correlations (pandas.DataFrame.corr(pearson, spearman, kendall))
    * anova (statsmodels.formula.api.ols)
    * linear regression (seaborn.lmplot)
    * logistic regression (sklearn.linear_model.LogisticRegression())
