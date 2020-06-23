#!/bin/python
max_nr_running_batches = 100 #seems to be taking up to 100
cname = 'cedar'
cusers_list = ['hanganua','hvt','lucaspsy','hiver85']
chome_dir = '/home'
cprojects_dir = 'projects/def-hanganua'
cscratch_dir = '/scratch'
process_order = ['registration','autorecon1','autorecon2','autorecon3','qcache','brstem','hip','tha']
long_name = 'ses-1'
base_name = 'base'
DO_LONG = False
supervisor_ccri = 'ykc-101-04'
text4_scheduler = ('#!/bin/sh','#SBATCH --account=def-hanganua','#SBATCH --mem=8G',)
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

def get_vars():

    cuser = _get_username()

    nimb_dir=path.join(chome_dir,cuser,cprojects_dir,'a/')
    dir_new_subjects=path.join(chome_dir,cuser,cprojects_dir,'subjects/')
    nimb_scratch_dir=path.join(cscratch_dir,cuser,'a_tmp/')
    SUBJECTS_DIR = path.join(chome_dir,cuser,cprojects_dir,'fs-subjects/')
    processed_SUBJECTS_DIR = path.join(chome_dir,cuser,cprojects_dir,'subjects_processed/')
    export_FreeSurfer_cmd = 'export FREESURFER_HOME='+path.join(chome_dir,cuser,cprojects_dir,'freesurfer')
    source_FreeSurfer_cmd = '$FREESURFER_HOME/SetUpFreeSurfer.sh'
 
    return cuser, nimb_dir, nimb_scratch_dir, SUBJECTS_DIR, processed_SUBJECTS_DIR, dir_new_subjects, export_FreeSurfer_cmd, source_FreeSurfer_cmd
