NeuroImaging My Brain = NIMB (Pipeline for Structural MRI analysis wih FreeSurfer)

* Module *GUI* (exe.py) or file 'variables.py':
    * takes the variables and files provided by the user; sends them to the sqlite database; alternatively, passwords for accesing remote computers are being saved in file located in '/home/$USER' or '/Users' (though this method should be avoided due to security reasons)
    * initiates the *DISTRIBUTION* module (in the GUI or the terminal command: "nimb process")
    * if a file is provided that has the groups and the names of the subjects:
        ** initiates the *STATS* module


* Module *DISTRIBUTION* : (works on the local computer as GUI or terminal or on the remote computer in the terminal) (folder "$NIMB_HOME/distribution")
    * checks that all folders and variables are defined
    * checks if with the processing app is installed on the local or remote computer
        ** if not -> installs with the processing app and miniconda3 with pandas, paramiko, numpy, xlrd
    * if there are subjects in the DATABASE/SOURCE/MRI folder (archived zip or .gz):
        ** verifies if all subjects have the processed data, located in the PROCESSED_FS
            ** if not:
                *** makes the list of subjects to be processed
                *** checks for available space on the computer that has the processing app
                *** defines the volume of subjects that will be sent for processing depending on the available space
                *** check the volume of the DATABASE/SOURCE/MRI_UNZIPPED folder
                * if content of the DATABASE/SOURCE/MRI folder is archived:
                    ** unzips each subjects and puts it in DATABASE/SOURCE/MRI_UNZIPPED, populating the folder until the defined available space is fille
                *** if processing app is on a remote computer:
                    **** deploys all MR data from DATABASE/SOURCE/MRI_UNZIPPED to the remote computer in the NEW_SUBJECTS folder
                *** initiates the *CLASSIFIER* module on the computer with the processing app
                *** once the $NIMB_HOME/tmp/new_subjects.json file is created:
                    **** initiates the *PROCESSING* module for the processing app
                *** checks if data is processed in all folders in the PROCESSED_NIMB folder
                *** if there is data is any of the folders:
                    **** moves the subjects to the DATABASE/PROCESSED_FS folder
                    **** if the user defined a DATABASE/BIDS folder:
                        **** moves the processed subjects to each corresponding subject and corresponding session in the DATABASE/BIDS/SUBJECT/SESSION/PROCESSED_FS folder



* Module *CLASSIFIER* : (works on the computer that has the processing app installed)(folder "$NIMB_HOME/classifier")
    * takes the content of the NEW_SUBJECTS folder (on the remote) or the DATABASE/SOURCE/MRI_UNZIPPED (on the local computer)
    * verifies the voxel parameters of all T1 and:
        ** classifies the T1 images based on sessions
        ** keeps in the same session only the T1 with the same voxel parameters
    * if there are T1 images:
        ** searches for Flair images and if present and if Flair images have the same voxel parameters as T1, adds them for the analysis
        ** if there are no Flair images:
            *** searches for T2 images; if present and T2 have the same voxel parameters as T1, adds them for the analysis
        ** searches for DWI images and if present adds them for the analysis
        ** searches for rsfMRI images and if present adds them for the analysis
    * if the user defined a DATABASE/BIDS folder:
        ** uses the DCM2BIDS app to convert the subjects from the MRI_UNZIPPED folder into .nii.gz format
        ** classifies the MR files into BIDS format
    * saves the dictionary as $NIMB_HOME/tmp/new_subjects.json file


* Module *PROCESSING* : (works on the computer that has the processing app installed) (folder "$NIMB_HOME/processing")
    * reads the $NIMB_HOME/tmp/new_subjects.json file, registers the subjects and the paths to their corresponding MR files
    sub-MODULE "environement":
        * if analysis is performed with the slurm or moab scheduler:
            ** creates the corresponding batches
            ** send the batches to the slurm scheduler
            ** verifies that the analysis is done by the scheduler
        * if analysis is performed in the tmux environement:
            ** sends the processing commands to the tmux environement
            ** verifies that the analysis is done in tmux
    sub-MODULE 'freesurfer-processing':
        * registers all subjects with at least 1 T1, 1 T1 + at least 1 Flair, 1 T1 with at leat 1 T2 in the SUBJECTS_DIR
        * runs the FreeSurfer steps: autorecon1, autorecon2, autorecon3, qcache, brainstem, hippocampus, thalamus
        * if user requested extraction of masks:
            ** extracts the masks for the corresponding subcortical structures and puts them in the processed_folder/masks
        * once the processing is done, moves the processed subjects to the PROCESSED_NIMB/PROCESSED_FS folder
    * if user wants the data archived:
        ** archives with zip the subjects in the PROCESSED_NIMB/PROCESSED_FS folder


* Module *STATS* : (works on the local computer as GUI or terminal or on the remote computer in the terminal) (folder "$NIMB_HOME/stats") (cmd: nimb stats)
    * extracts all FreeSurfer-based stats for all participants in the storage folder or based on a csv/excel file provided by the user and creates one excel file with all values (currently >1500 values)
    * checks data/ resuls for inconsistent values, errors, missing values
    -> if the user provides a csv/excel file with the groups:
        * performs t-test between the groups for all parameters and creates another excel/csv file with the results (scipy.stats: ttest_ind, f_oneway, bartlett, mannwhitneyu, kruskal)
        * performs FreeSurfer GLM using mri_glmfit, for all contrasts and for infinite number of variables for correlations (cmd: nimb glm)
        * if analysis is performed on the local computer:
            ** saves FDR corrected images + MonteCarlo corrected images (cmd nimb glm images)
        * provides a distribution graph for the groups for the requested variable (seaborn.distplot; seaborn.jointplot)
        * performs correlations between FreeSurfer variables and other variables provided by the user (pandas.DataFrame.corr(pearson, spearman, kendall))
        * performs linear regression for all variables provided by the user and the FreeSurfer variables (seaborn.lmplot)
        * performs logistic regression for all variables provided by the user and the FreeSurfer variables (sklearn.linear_model.LogisticRegression())

* current remote compute is Cedar cluster on Compute Canada
* processing is sent to the slurm scheduler (#SBATCH)
* the processing app is FreeSurfer 7.1.0

=== variables defined by the user:
DATABASE/SOURCE/MRI - folder that has the raw MRIs of the subjects in an archived or non-archived format
DATABASE/PROCESSED_FS - folder that has the data processed with FreeSurfer
NIMB_HOME = 'path' to the nimb folder
BIDS definitions; for blank, '' can be used
base_name = 'base' # the name of the base subject that will be created during the longitudinal analysis with FreeSurfer
archive_processed = False or True # True is the user want the processed subjects to be archived with zip
masks = [] # the list of masks for which the user wants FreeSurfer to create masks, that will be located in the processed_subjects_folder/masks
python3_run_cmd = 'python3' # is the command used on the local or remote computer that is used to initiate python 3
flair_t2_add = False # parameters defines if the user wants to use Flair or T2 images for the FreeSurfer processing, if images are provided
freesurfer_version = '7' #default is 7, but other versions are considered to be added. Previous versions should be working as well, but the variable has to be changed, because brainstem, hippocampus and thalamus processing have other commands.

=== FREESURFER specific variables
FREESURFER_HOME = 'path' to the freesurfer folder, if it is installed or where the freesurfer will be installed. If blank and analysis is made in a Linux or Mac environement, freesurfer will be installed in the NIMB_HOME folder. If is made in Windows, pipeline will return an error and ask for a path.
long_name = 'ses-' # the abbreviation that will be used to define the longitudinal abbreviations for subjects; ses- is in line with 
export_FreeSurfer_cmd = 'export FREESURFER_HOME='+FREESURFER_HOME # in some cases, when FreeSurer is used as module, this command is different
source_FreeSurfer_cmd = '$FREESURFER_HOME/SetUpFreeSurfer.sh' #this command might be different if FreeSurfer is used as module


=== REMOTE COMPUTER specific variables:
python3_load_cmd = 'module load python/3.8.2' # this commands is used if the processing is performed on a remote computer where python3 can be used only from module load
processing_env = 'slurm' or 'tmux' #defines which environment is used for the processing of data
cusers_list = [] # if the number of users on the remote computer are more than 1.

=== COMPUTE CANADA specific variables:
supervisor_account = 'def-supervisor' # variable used on compute canada clusters to create the batches

=== STATISTICAL ANALYSIS variables:
GLM_file_group = "PATH to the file.csv or file.xlsx" that has the subjects, groups and variables for statistical analyis
id_col = "name" of the column in the file.csv that includes the names of the subjects. Names MUST be the same as the names in DATABASE/PROCESSED_FS
group_col = "name" of the column in the file.csv that includes the groups
variables_for_glm = ['variable1','variable2',] # a list or variables from the file.csv file that has the corresponding variables for statistical analysis
GLM_dir = path.join('/scratch',cuser,'adni','glm') # this is the folder whether the glm analysis is made.
GLM_measurements = ['thickness','area','volume',]#'curv'] # these are the cortical parameters that will be used for FreeSurfer GLM analysis
GLM_thresholds = [10,]#5,15,20,25] # these are the threshold levels for smoothing in mm, used for FreeSurfer GLM analysis
GLM_MCz_cache = 13 # level of FreeSurfer GLM MCS simulation threshold, 13 equals to p=0.05
