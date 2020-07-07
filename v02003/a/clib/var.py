#!/bin/python

'''following variables are set by the user in the GUI or in this file
current setup is constructed for Compute Canada clusters'''

max_nr_running_batches = 5 #seems to be taking up to 100
process_order = ['registration','autorecon1','autorecon2','autorecon3','qcache','brstem','hip','tha']
supervisor_account = 'def-hanganua'

long_name = 'ses-'
base_name = 'base'
DO_LONG = False
batch_walltime_cmd = '#SBATCH --time='
max_walltime = '99:00:00' # waltime maximal for the remote cluster
batch_walltime = '03:00:00' # walltime maximal for the run.sh batch that runs the pipeline
batch_output_cmd = '#SBATCH --output='
submit_cmd = 'sbatch'
freesurfer_version = 7
archive_processed = False
masks = [] # varibale that includes the ROI names of subcortical regions in order to create the masks.
SUBMIT = True # variable to define if the batches will be submitted to the scheduler. Is used to perform initial verification if files were created correctly





from os import path, makedirs
from cget_username import _get_username

cuser = _get_username()
cusers_list = ['hanganua','hvt','lucaspsy','hiver85']


text4_scheduler = ('#!/bin/sh','#SBATCH --account='+supervisor_account,'#SBATCH --mem=8G',)



'''following variables can be set by the user in the GUI or in this file
or can be left as is and will be created automatically
current setup works for ComputeCanada clusters
It is suggested that freesurfer is installed in the projects folder
since this folder can send batches to the scheduler
the folder that receives the files that are temporary created and do not need to be backup
are saved on the scratch, as per the current Compute Canada setup'''


remote_path_main_dir = path.join('/home',cuser,'projects',supervisor_account)
remote_path_save_temporary_files = path.join('/scratch',cuser)
FREESURFER_HOME = path.join(remote_path_main_dir,'freesurfer')
export_FreeSurfer_cmd = 'export FREESURFER_HOME='+FREESURFER_HOME
source_FreeSurfer_cmd = '$FREESURFER_HOME/SetUpFreeSurfer.sh'

nimb_dir=path.join(remote_path_main_dir,'a/')
dir_new_subjects=path.join(remote_path_main_dir,'subjects/')
# SUBJECTS_DIR = path.join(remote_path_main_dir,'adni/Subjects_GLM') #temporary path for GLM analysis
SUBJECTS_DIR = path.join(remote_path_main_dir,'fs-subjects/')
processed_SUBJECTS_DIR = path.join(remote_path_main_dir,'subjects_processed/')
nimb_scratch_dir=path.join(remote_path_save_temporary_files,'a_tmp/')



'''
following variables are used for the GLM analysis
'''

GLM_file_group = path.join('/home',cuser,'datas_CNvsAD_clinical.csv') # this is the file that contains the: IDs, groups and variables for the FreeSurfer GLM analysis
id_col = 'MRI_subjects' # this is the name of the columns from GLM_file_group where the IDs are defined. The IDs MUST be the same as in SUBJECTS_DIR
group_col = 'Group' # this is the name of the column from GLM_file_group where the groups are defined
variables_for_glm = ['AGE', 'MMSCORE', 'CDMEMORY', 'CDGLOBAL', 'GDMEMORY', 'GDTOTAL', 'FAQTOTAL',
       'PTGENDER', 'PTEDUCAT', 'CLOCKSCOR', 'COPYSCOR', 'AVTOT1', 'AVERR1',
       'AVTOT2', 'AVERR2', 'AVTOT3', 'AVERR3', 'AVTOT4', 'AVERR4', 'AVTOT5',
       'AVERR5', 'AVTOT6', 'AVERR6', 'AVTOTB', 'AVERRB', 'DSPANFOR',
       'DSPANFLTH', 'DSPANBAC', 'DSPANBLTH', 'CATANIMSC', 'CATANPERS',
       'CATANINTR', 'CATVEGESC', 'CATVGPERS', 'CATVGINTR', 'TRAASCOR',
       'TRAAERRCOM', 'TRAAERROM', 'TRABSCOR', 'TRABERRCOM', 'TRABERROM',
       'DIGITSCOR', 'BNTSPONT', 'BNTSTIM', 'BNTCSTIM', 'BNTPHON', 'BNTCPHON',
       'BNTTOTAL', 'AVDEL30MIN', 'AVDELERR1', 'AVDELTOT', 'AVDELERR2',
       'ANARTERR', 'NPIA', 'NPIASEV', 'NPIB', 'NPIBSEV', 'NPIC', 'NPICSEV',
       'NPID', 'NPIDSEV', 'NPIE', 'NPIESEV', 'NPIF', 'NPIFSEV', 'NPIG',
       'NPIGSEV', 'NPIH', 'NPIHSEV', 'NPII', 'NPIISEV', 'NPIJ', 'NPIJSEV',
       'NPIK', 'NPIKSEV', 'NPIL', 'NPILSEV', 'NPISCORE'] # this is the list of variable what will be used to perform the FreeSurfer GLM correlations
GLM_dir = path.join('/scratch',cuser,'adni','glm') # this is the folder whether the glm analysis is made. It is necessary for the file remote_runglm.py
GLM_measurements = ['thickness','area','volume',]#'curv'] # these are the cortical parameters that will be used for GLM analysis
GLM_thresholds = [10,]#5,15,20,25] # these are the threshold levels for smoothing in mm, used for GLM analysis
GLM_MCz_cache = 13 # level of mcz simulation threshold, 13 equals to p=0.05


for remote_path in (nimb_dir, dir_new_subjects, SUBJECTS_DIR, processed_SUBJECTS_DIR, nimb_scratch_dir):
	if not path.isdir(remote_path):
		makedirs(remote_path)



'''these variables were used in the past, but are probably not needed anymore by the cluster.
They are currently not used and can be left uncompleted'''
# cname = 'cedar'
# supervisor_ccri = 'ykc-101-04'
