#!/bin/python

'''following variables are set by the user in the GUI or in this file
current setup is constructed for Compute Canada clusters'''

max_nr_running_batches = 5 #seems to be taking up to 100
process_order = ['registration','autorecon1','autorecon2','autorecon3','qcache','brstem','hip','tha']
supervisor_account = 'def-hanganua'

long_name = 'ses-1'
base_name = 'base'
DO_LONG = False
batch_walltime_cmd = '#SBATCH --time='
max_walltime = '99:00:00'
batch_walltime = '03:00:00'
batch_output_cmd = '#SBATCH --output='
submit_cmd = 'sbatch'
freesurfer_version = 7
archive_processed = False
masks = []





from os import path
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
export_FreeSurfer_cmd = 'export FREESURFER_HOME='+path.join(remote_path_main_dir,'freesurfer')
source_FreeSurfer_cmd = '$FREESURFER_HOME/SetUpFreeSurfer.sh'

nimb_dir=path.join(remote_path_main_dir,'a/')
dir_new_subjects=path.join(remote_path_main_dir,'subjects/')
SUBJECTS_DIR = path.join(remote_path_main_dir,'fs-subjects/')
processed_SUBJECTS_DIR = path.join(remote_path_main_dir,'subjects_processed/')
nimb_scratch_dir=path.join(remote_path_save_temporary_files,'a_tmp/')

for remote_path in (nimb_dir, dir_new_subjects, SUBJECTS_DIR, processed_SUBJECTS_DIR, nimb_scratch_dir):
	if not path.isdir(remote_path):
		makedirs(remote_path)



'''these variables were used in the past, but are probably not needed anymore by the cluster.
They are currently not used and can be left uncompleted'''
# cname = 'cedar'
# supervisor_ccri = 'ykc-101-04'
