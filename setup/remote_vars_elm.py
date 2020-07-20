#!/bin/python
from os import path

'''
USER-defined variables for the REMOTE processing environment
beluga.computecanada.ca
'''
raddress           = 'elm.criugm.qc.ca' # address to access the remote computer, can be an IP
supervisor_account = '' # variable used on compute canada clusters to create the batches
ruser              = 'hanganua' # username to access the remote computer. Password will be asked by nimb and stored in sqlite
rusers_list        = [] # if the number of users on the remote computer are more than 1, can be: ['user1','user2',]


# ==================================
# DO NOT CHANGE: script to use the correct username if multiple users are using the same pipeline
if len(rusers_list)>1:
       try:
              from cget_username import _get_username
       except ImportError:
              from a.clib.cget_username import _get_username
       ruser = _get_username()
from os import path
# ==================================


# PATHS
NIMB_RHOME = path.join('/home_je',ruser,'nimb') # where the local/remote nimb folder is downloaded
nimb_scratch_dir=path.join(NIMB_RHOME,'tmp') # Default is NIMB_RHOME/tmp path to a temporary folder where all temporary files will be saved. This folder needs to be put in a place that allows quick reading and writing and to delete the files; This folder can get very big. On compute canada it should be put on scratch
SOURCE_SUBJECTS_DIR = path.join('home_je',ruser, 'database','loni_ppmi','source','mri') # folder that has the raw MRIs of the subjects in archived or non-archived format
SOURCE_BIDS_DIR = '' # path to a folder that, if NOT blank, pipeline will convert SOURCE_SUBJECTS_DIR to BIDS format
PROCESSED_FS_DIR = path.join('/home_je',ruser, 'database','loni_ppmi','processed_fs') # path to local or remote folder that has the data processed with FreeSurfer


# Processing variables:
PROCESSED_NIMB         = path.join(NIMB_RHOME, 'processed_nimb') # path to folder where the processed subjects will be stored temporarily
SUBMIT                 = True                   # or False, defines if the scheduler batches are submitted to the scheduler. Is used to verify the batches
processing_env         = 'tmux' # or 'tmux' or 'moab' # is the environment used for processing data
max_nr_running_batches = 10    # number of batches that can be sent to the scheduler at the same time.
text4_scheduler        = ()
batch_walltime_cmd     = '' #this command differs between schedulers
batch_output_cmd       = '' # command used in the batch to define the path of the output file
submit_cmd             = 'tmux'           # command used to submit the batched to the scheduler
max_walltime           = '50:00:00'       # waltime maximal for the scheduler
batch_walltime         = '03:00:00'     # walltime maximal for the pipeline to reinitate itself; 3 hours is the duration that is used by the scheduler to quickly deploy the script
python3_load_cmd       = 'module load python/3.8.2' # command if python is used as module, can be: 'module load python/3.8.2'
python3_run_cmd        = 'python3' # is the command used on the local or remote computer that is used to initiate python 3



# FreeSurfer variables
FreeSurfer_install = True # to define if the local/remote compute will be used to perform FreeSurfer analysis
freesurfer_version = 7 # default is 7 (for 7.1.0) but pipeline should also work with versions 6 and 5
FREESURFER_HOME = () # path to the freesurfer folder. Default is $NIMB_HOME/freesurfer. If OS is Windows, pipeline will ask the credentials for a remote Linux/Mac.
FS_SUBJECTS_DIR = path.join(NIMB_RHOME,'fs_subjects') # Default is 'FREESURFER_HOME/subjects', path to the folder where the subjects are being processed by FreeSurfer.
export_FreeSurfer_cmd = 'module load freesurfer/7.1.0' # in some cases this command has to be adjusted
source_FreeSurfer_cmd = '' # command might be different if FreeSurfer is used as module
process_order = ['registration','autorecon1','autorecon2','autorecon3','qcache'] #list of processing steps in FreeSurfer. For FreeSurfer version lower thatn 7, "tha" must be remove; Instead of autorecon1, autorecon2 and autorecon3, the commmand "recon" can be used (which will use the command 'recon-all' for freesurfer processing), but it will take more time for processing and this can be limited by the scheduler
archive_processed = True # if True the processed subjects must be archived with zip; if False subjects are NOT archived
masks = [] # list of masks names of subcortical regions for which the user wants FreeSurfer to create masks
flair_t2_add = False # defines if Flair or T2 images should be used for the FreeSurfer processing
DO_LONG = False # True or False, if longitudinal analysis needs to be made
base_name = 'base' # the name of the base subject that will be created during the longitudinal analysis with FreeSurfer
long_name = 'ses-' # abbreviation used to define the longitudinal time points for subjects




'''
USER-defined STATISTICAL ANALYSIS variables:
If freesurfer_install is True, the environment can be used to perform FreeSurfer GLM analysis.
But GLM can be done ONLY if the environment is ready to perform brainste/ hippocampus and thalamus processing.
If not - the GLM can be done only in a screen, and will not work if sent to the scheduler.
'''

GLM_file_group = '' # "PATH to the file.csv or file.xlsx" that has the subjects, groups and variables for statistical analyis
id_col = '' # name of the column in the file.csv that includes the names of the subjects similar to the names in PROCESSED_FS_DIR
group_col = '' # name of the column in the file.csv that includes the groups
variables_for_glm = [] # list of variables from the columns in file.csv file for statistical analysis, FreeSurfer GLM and correlations
GLM_dir = '' # path to the folder were the glm analysis will be made.
GLM_measurements = ['thickness','area','volume',]#'curv'] # cortical parameters that will be used for FreeSurfer GLM analysis
GLM_thresholds = [10,]#5,15,20,25] # threshold levels for smoothing in mm, used for FreeSurfer GLM analysis
GLM_MCz_cache = 13 # level of FreeSurfer GLM MCZ simulation threshold 13 equals to p=0.05







'''
variables that must be changed in all scripts and must be removed
'''
from os import makedirs
for remote_path in (NIMB_RHOME, dir_new_subjects, FS_SUBJECTS_DIR, processed_SUBJECTS_DIR, nimb_scratch_dir):
	if not path.isdir(remote_path):
		makedirs(remote_path)

cusers_list = rusers_list
cuser = ruser
nimb_dir = NIMB_RHOME
SUBJECTS_DIR = FS_SUBJECTS_DIR
processed_SUBJECTS_DIR = path.join(PROCESSED_NIMB,'processed_fs') #must be changed to NIMB_HOME/processed_nimb/processed_fs
dir_new_subjects= NIMB_RHOME/new_subjects #must be changed to NIMB_RHOME/new_subjects
remote_path_main_dir = path.join('/home',ruser)
remote_path_save_temporary_files = remote_path_main_dir
