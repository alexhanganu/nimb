NeuroImaging My Brain = NIMB (Pipeline for MRI analysis)

* Module *GUI* :
    * takes the variables and files provided by the user
    * initiates the *DISTRIBUTION* module

* Module *DISTRIBUTION* :
    * takes T1 and Flair and/or T2 MR images and initiates the *CLASSIFIER* module
    * checks for available space on the local or remote computer
    * checks for the volume of data provided for analysis
    * checks if FreeSurfer is installed on the local or remote computer
    * deploys corresponding MR images to the remote computer along with the new_subjects.json file
    * initiates the *PROCESSING* module
    * checks if data is processed
    * moves the processed data to the corresponding storage folder provided by the user

* MOdule *CLASSIFIER* :
    * classifies the raw MR images in the BIDS format, creating the files new_subjects.json

* Module *PROCESSING* :
    * reads the new_subjects.json file and registers the subjects in T1 and/or Flair or T2 to FreeSurfer
    * runs the FreeSurfer steps: recon-all (autorecon1, 2, 3), qcache, brainstem, hippocampus, thalamus
    * extracts the masks for subcortical structures (if requested by the user)

* Module *STATS* :
    * extracts all FreeSurfer-based stats for all participants in the storage folder or based on a csv/excel file provided by the user and creates one excel file with all values (currently >1500 values)
    * checks data/ resuls for inconsistent values, errors, missing values
    -> if the user provides a csv/excel file with the groups:
        * performs t-test between the groups for all parameters and creates another excel/csv file with the results (scipy.stats: ttest_ind, f_oneway, bartlett, mannwhitneyu, kruskal)
        * performs FreeSurfer GLM using mri_glmfit, for all contrasts and for infinite number of variables for correlations
        * saves FDR corrected images
        * saves the MonteCarlo corrected images
        * provides a distribution graph for the groups for the requested variable (seaborn.distplot; seaborn.jointplot)
        * performs correlations between FreeSurfer variables and other variables provided by the user (pandas.DataFrame.corr(pearson, spearman, kendall))
        * performs linear regression for all variables provided by the user and the FreeSurfer variables (seaborn.lmplot)
        * performs logistic regression for all variables provided by the user and the FreeSurfer variables (sklearn.linear_model.LogisticRegression())

* current remote compute is Cedar cluster on Compute Canada