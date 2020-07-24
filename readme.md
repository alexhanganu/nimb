NeuroImaging My Brain = NIMB (Pipeline for Structural MRI analysis wih FreeSurfer)

* Module *GUI* (exe.py) or file 'variables.py':
    * takes the variables and files provided by the user
    * sends the variables to sqlite database; 
    * initiates the *DISTRIBUTION* module (in the GUI or the terminal command: "nimb process")
    * if a file is provided that has the groups and the names of the subjects:
        ** initiates the *STATS* module

* Module *DISTRIBUTION* : (works on the local computer as GUI or terminal or on the remote computer in the terminal) (folder "$NIMB_HOME/distribution")
    * checks that all folders and variables are defined
    * checks if with the processing app is installed on the local or remote computer
        ** if not -> installs with the processing app and miniconda3 with pandas, paramiko, numpy, xlrd
    * if there are subjects in the SOURCE_SUBJECTS_DIR folder (archived zip or .gz):
        ** verifies if all subjects have the processed data, located in the $PROCESSED_FS_DIR
            ** if not:
                *** makes the list of subjects to be processed
                *** checks for available space on the computer that has the processing app
                *** defines the volume of subjects that will be sent for processing depending on the available space
                *** checks the volume available on $NIMB_HOME/new_subjects folder
                * if content of the SOURCE_SUBJECTS_DIR folder is archived:
                    ** unzips each subject and puts it in $NIMB_HOME/new_subjects, populating the folder up to the defined available space
                *** if processing is performed on a remote computer:
                    **** deploys all MR data from $NIMB_HOME/new_subjects to the remote computer in the $NIMB_RHOME/new_subjects folder
                *** initiates the *CLASSIFIER* module on the computer with the processing app
                *** once the $NIMB_RHOME/tmp/new_subjects.json file is created:
                    **** initiates the *PROCESSING* module for the processing app
                *** checks if data is processed in all folders in the PROCESSED_NIMB folder
                *** if there is data in any of the folders:
                    **** moves the subjects to the local or remote $PROCESSED_FS_DIR folder
                    **** if SOURCE_BIDS_DIR is provided:
                        **** moves the processed subjects to corresponding SOURCE_BIDS_DIR/subject/session/processed_fs folder


* Module *CLASSIFIER* : (works on the computer that has the processing app installed)(folder "$NIMB_HOME/classifier")
    * takes the content of the $NIMB_HOME/new_subjects or $NIMB_RHOME/new_subjects folder
    * verifies the voxel parameters of all T1 and:
        ** classifies the T1 images based on sessions
        ** keeps in the same session only the T1 with the same voxel parameters
    * if there are T1 images:
        ** searches for Flair images and if present and if Flair images have the same voxel parameters as T1, adds them for the analysis
        ** if there are no Flair images:
            *** searches for T2 images; if present and T2 have the same voxel parameters as T1, adds them for the analysis
        ** searches for DWI images and if present adds them for the analysis
        ** searches for rsfMRI images and if present adds them for the analysis
    * if the user defined a SOURCE_BIDS_DIR folder:
        ** uses the dcm2bids app to convert the subjects from the SOURCE_SUBexJECTS_DIR folder into .nii.gz format
        ** classifies the MR files into BIDS format
    * saves the dictionary as $NIMB_HOME/tmp/new_subjects.json or $NIMB_RHOME/tmp/new_subjects.json file


* Module *PROCESSING* : (works on the computer that has the processing app installed) (folder "$NIMB_HOME/processing")
    * reads the $NIMB_HOME/tmp/new_subjects.json file, registers the subjects and the paths to their corresponding MR files
    sub-MODULE "environement":
        * if analysis is performed with the slurm or moab scheduler:
            ** creates the corresponding batches
            ** sends the batches to the scheduler
            ** verifies that the analysis is done by the scheduler
        * if analysis is performed in the tmux environement:
            ** sends the processing commands to the tmux environement
            ** verifies that the analysis is done in tmux
    sub-MODULE 'freesurfer-processing':
        * registers all subjects with at least 1 T1, 1 T1 and at least 1 Flair, 1 T1 and at leat 1 T2 in the FS_SUBJECTS_DIR
        * runs the FreeSurfer steps: autorecon1, autorecon2, autorecon3, qcache, brainstem, hippocampus, thalamus
        * if user requested extraction of masks:
            ** extracts the masks for the corresponding subcortical structures and puts them in the processed_folder/masks
        * once the processing is done, moves the processed subjects to the $PROCESSED_NIMB/processed_fs folder
    * if user wants the data archived:
        ** archives with zip the each subject in the $PROCESSED_NIMB/processed_fs folder


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



=== USER-defined variables:
SOURCE_SUBJECTS_DIR = 'path' folder that has the raw MRIs of the subjects in archived or non-archived format
PROCESSED_FS_DIR = 'path' # to local or remote folder that has the data processed with FreeSurfer
NIMB_HOME = 'path' where the local nimb folder was downloaded
archive_processed = True # if True the processed subjects must be archived with zip; if False subjects are NOT archived
masks = [] # list of masks for which the user wants FreeSurfer to create masks
flair_t2_add = False # defines if Flair or T2 images should be used for the FreeSurfer processing


* REMOTE COMPUTER specific variables: (tested on cedar.computecanada.ca with slurm and on local with tmux)
raddress       = 'cedar.computecanada.ca' # address to access the remote computer, can be an IP
ruser          = 'username' # username to access the remote computer. Password will be asked by nimb and stored in sqlite
NIMB_RHOME     = 'path' on the remote computer where nimb will be downloaded
processing_env = 'slurm' or 'tmux' or 'moab' # is the environment used for processing data

python3_load_cmd = '' # command if python is used as module, can be: 'module load python/3.8.2'
cusers_list      = [] # if the number of users on the remote computer are more than 1, can be: ['user1','user2',]


* COMPUTE CANADA specific variables:
supervisor_account = 'def-supervisor' # variable used on compute canada clusters to create the batches


=== USER-defined STATISTICAL ANALYSIS variables:
GLM_file_group = "PATH to the file.csv or file.xlsx" that has the subjects, groups and variables for statistical analyis
id_col = "name" of the column in the file.csv that includes the names of the subjects similar to the names in PROCESSED_FS_DIR
group_col = "name" of the column in the file.csv that includes the groups
variables_for_glm = ['variable1','variable2',] # a list of variables from the columns in file.csv file for statistical analysis
GLM_dir = 'pat' # to the folder were the glm analysis will be made.
GLM_measurements = ['thickness','area','volume',]#'curv'] # cortical parameters that will be used for FreeSurfer GLM analysis
GLM_thresholds = [10,]#5,15,20,25] # threshold levels for smoothing in mm, used for FreeSurfer GLM analysis
GLM_MCz_cache = 13 # level of FreeSurfer GLM MCZ simulation threshold 13 equals to p=0.05



=== DEFAULT variables that can be changed:
* PATHs:
SOURCE_BIDS_DIR = '' # path to a folder that, if NOT blank, pipeline will convert SOURCE_SUBJECTS_DIR to BIDS format
PROCESSED_NIMB = $NIMB_HOME/processed_nimb # path to folder where the processed subjects will be stored temporarily

* Processing variables:
SUBMIT = True                   # or False, defines if the scheduler batches are submitted to the scheduler. Is used to verify the batches
max_nr_running_batches = 100    # number of batches that can be sent to the scheduler at the same time.
max_walltime = '99:00:00'       # waltime maximal for the scheduler
batch_walltime_cmd = '#SBATCH --time=' #this command differs between schedulers
batch_output_cmd = '#SBATCH --output=' # command used in the batch to define the path of the output file
submit_cmd = 'sbatch'           # command used to submit the batched to the scheduler
batch_walltime = '03:00:00'     # walltime maximal for the pipeline to reinitate itself; 3 hours is the duration that is used by the scheduler to quickly deploy the script

* LONGITUDINAL analysis:
DO_LONG = False # True or False, if longitudinal analysis needs to be made
base_name = 'base' # the name of the base subject that will be created during the longitudinal analysis with FreeSurfer
python3_run_cmd = 'python3' # is the command used on the local or remote computer that is used to initiate python 3

* FREESURFER specific variables
FREESURFER_HOME = '$NIMB_RHOME/freesurfer' # path to the freesurfer folder. If OS is Linux/Mac by default freesurfer is installed in $NIMB_HOME. If OS is Windows, pipeline will ask the credentials for a remote Linux/Mac.
FS_SUBJECTS_DIR = '$NIMB_HOME/freesurfer/subjects' # path to the folder where the subjects are being processed by FreeSurfer.
long_name = 'ses-' # abbreviation used to define the longitudinal time points for subjects
export_FreeSurfer_cmd = 'export FREESURFER_HOME='+FREESURFER_HOME # in some cases this command has to be adjusted
source_FreeSurfer_cmd = '$FREESURFER_HOME/SetUpFreeSurfer.sh' # command might be different if FreeSurfer is used as module
freesurfer_version = '7' # default is 7 (for 7.1.0) but pipeline should also work with versions 6 and 5
process_order = ['registration','autorecon1','autorecon2','autorecon3','qcache','brstem','hip','tha'] #list of processing steps in FreeSurfer. For FreeSurfer version lower thatn 7, "tha" must be remove; Instead of autorecon1, autorecon2 and autorecon3, the commmand "recon" can be used (which will use the command 'recon-all' for freesurfer processing), but it will take more time for processing and this can be limited by the scheduler


