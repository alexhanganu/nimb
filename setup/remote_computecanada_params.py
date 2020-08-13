
def Commands_cluster_scheduler(cluster, cuser, supervisor_ccri):

    # CEDAR-SimonFraser cedar.computecanada.ca
    if cluster == 'cedar':
        # install freesurfer 6.0 with epub and use module load freesurfer/6.0.0, https://docs.computecanada.ca/wiki/FreeSurfer
        # use 'diskusage_report' to get the available space for the user
        # check priority with: sshare -l -A def-prof1_cpu -u prof1,grad2,postdoc3
        remote_type = 'slurm'

        FreeSurfer_Install = True
        from setup.setup import freesurfer71_centos7_download_address
        FreeSurfer_Source = freesurfer71_centos7_download_address
        freesurfer_version = 7

        batch_file_header = (
            '#!/bin/sh',
            '#SBATCH --account=def-hanganua',
            '#SBATCH --mem=8G',)
        cusers_list = ['hanganua','hvt','lucaspsy',]
        chome_dir = '/home'
        cprojects_dir = 'projects/def-hanganua'
        cscratch_dir = '/scratch'
        batch_walltime_cmd = '#SBATCH --time='
        max_walltime='99:00:00' # up to 600, 28 days
        batch_output_cmd = '#SBATCH --output='
        export_FreeSurfer_cmd = 'export FREESURFER_HOME='+chome_dir+'/'+cuser+'/'+cprojects_dir+'/freesurfer'
        source_FreeSurfer_cmd = '$FREESURFER_HOME/SetUpFreeSurfer.sh'
        nimb_dir=chome_dir+'/'+cuser+'/'+cprojects_dir+'/a/'
        dir_new_subjects=chome_dir+'/'+cuser+'/'+cprojects_dir+'/subjects/'
        nimb_scratch_dir=cscratch_dir+'/'+cuser+'/a_tmp/'
        SUBJECTS_DIR = chome_dir+'/'+cuser+'/'+cprojects_dir+'/fs-subjects/'
        processed_SUBJECTS_DIR = cscratch_dir+'/'+cuser+'/subjects_processed/'
        avail_processes = ['registration','autorecon1','autorecon2','autorecon3','qcache','brstem','hip']
        max_nr_running_batches=10
        submit_cmd = 'sbatch'

    # BELUGA-McGill beluga.calculquebec.ca
    if cluster == 'beluga':
        # install freesurfer 6.0 with epub and use module load freesurfer/6.0.0
        # use 'diskusage_report' to get the available space for the user
        remote_type = 'slurm'

        FreeSurfer_Install = False
        FreeSurfer_Source = ''
        freesurfer_version = 6

        batch_file_header = (
            '#!/bin/sh',
            '#SBATCH --account=def-hanganua',
            '#SBATCH --mem=8G',)
        cusers_list = ['hanganua','hvt','lucaspsy',]
        chome_dir = '/home'
        cprojects_dir = 'projects/def-hanganua'
        cscratch_dir = '/scratch'
        batch_walltime_cmd = '#SBATCH --time='
        max_walltime='99:00:00' # up to 168, 7 days
        batch_output_cmd = '#SBATCH --output='
        export_FreeSurfer_cmd = 'module load freesurfer/6.0.0'
        source_FreeSurfer_cmd = '$EBROOTFREESURFER/FreeSurferEnv.sh'
        nimb_dir=chome_dir+'/'+cuser+'/'+cprojects_dir+'/a/'
        dir_new_subjects=chome_dir+'/'+cuser+'/'+cprojects_dir+'/subjects/'
        nimb_scratch_dir=cscratch_dir+'/'+cuser+'/a_tmp/'
        SUBJECTS_DIR = chome_dir+'/'+cuser+'/'+cprojects_dir+'/fs-subjects/'
        processed_SUBJECTS_DIR = cscratch_dir+'/'+cuser+'/subjects_processed/'
        avail_processes = ['registration','autorecon1','autorecon2','autorecon3','qcache','brstem','hip']
        max_nr_running_batches=45#allows only up to 15 batches to run simultaneously
        submit_cmd = 'sbatch'


    # HELIOS-Laval helios.calculquebec.ca
    elif cluster == 'helios':
        # install freesurfer 6.0 by downloading
        remote_type = 'slurm'

        batch_file_header = (
            '#!/bin/sh',
            '#SBATCH --account=def-hanganua',
            '#SBATCH --mem=8G',)
        cusers_list = ['hanganua','hvt','lucaspsy',]
        chome_dir = '/home'
        cprojects_dir = 'projects/def-hanganua'
        cscratch_dir = '/scratch'
        batch_walltime_cmd = '#SBATCH --time='
        max_walltime='99:00:00'
        batch_output_cmd = '#SBATCH --output='
        export_FreeSurfer_cmd = 'export FREESURFER_HOME='+chome_dir+'/'+cuser+'/'+cprojects_dir+'/freesurfer'
        source_FreeSurfer_cmd = '$FREESURFER_HOME/SetUpFreeSurfer.sh'
        nimb_dir=chome_dir+'/'+cuser+'/'+cprojects_dir+'/a/'
        dir_new_subjects=chome_dir+'/'+cuser+'/'+cprojects_dir+'/subjects/'
        nimb_scratch_dir=cscratch_dir+'/'+cuser+'/a_tmp/'
        SUBJECTS_DIR = chome_dir+'/'+cuser+'/'+cprojects_dir+'/fs-subjects/'
        processed_SUBJECTS_DIR = cscratch_dir+'/'+cuser+'/subjects_processed/'
        avail_processes = ['registration','autorecon1','autorecon2','autorecon3','qcache','brstem','hip']
        max_nr_running_batches=10
        submit_cmd = 'sbatch'

    # NIAGARA-Toronto niagara.scinet.utoronto.ca
    elif cluster == 'niagara':
        # use module load freesurfer
        # use 'scinet niagara priority' to get the priority for the user
        #memory requests are of no use, 202GB are always given; there are 40 cores per node
        remote_type = 'slurm'
        chk_priority = 'scinet niagara priority'
		
        batch_file_header = (
            '#!/bin/bash',
            '#SBATCH --nodes=1',
            '#SBATCH --cpus-per-task=40',
            '#SBATCH --mail-type=FAIL',)
        batch_walltime_cmd = '#SBATCH --time='
        max_walltime='24:00:00'
        batch_output_cmd = '#SBATCH --output='
        pbs_file_FS_setup = (
            'module load freesurfer')
        avail_processes = ['registration','autorecon1','autorecon2','autorecon3','qcache','brstem','hip']
        max_nr_running_batches=10
        submit_cmd = 'sbatch'
		
    # GRAHAM-UWaterloo graham.calculcanada.ca
    elif cluster == 'graham':
        # install freesurfer 6.0 with epub and use module load freesurfer/6.0.0
        remote_type = 'slurm'

        batch_file_header = (
            '#!/bin/sh',
            '#SBATCH --account=def-hanganua',
            '#SBATCH --mem=8G',)
        batch_walltime_cmd = '#SBATCH --time='
        max_walltime='99:00:00' # up to 600, 28 days
        batch_output_cmd = '#SBATCH --output='
        pbs_file_FS_setup = (
            'module load freesurfer/6.0.0',
            'source $EBROOTFREESURFER/FreeSurferEnv.sh',)
        avail_processes = ['registration','autorecon1','autorecon2','autorecon3','qcache','brstem','hip']
        max_nr_running_batches=10
        submit_cmd = 'sbatch'

    # ELM-criugm.qc.ca
    if cluster == 'elm':
        # module load freesurfer/6.0.1
        remote_type = 'tmux'

        batch_file_header = ()
        batch_walltime_cmd = 'none'
        max_walltime='none'
        batch_output_cmd = 'screen -S minecraft -p 0 -X stuff "stop^M" '
        pbs_file_FS_setup = ('module load freesurfer/6.0.1') #https://unix.stackexchange.com/questions/409861/its-possible-to-send-input-to-a-tmux-session-without-connecting-to-it
        avail_processes = ['registration','autorecon1','autorecon2','autorecon3','qcache','brstem','hip']
        max_nr_running_batches=5
        submit_cmd = 'tmux'

    return batch_file_header, batch_walltime_cmd, max_walltime, batch_output_cmd, pbs_file_FS_setup, avail_processes, max_nr_running_batches, submit_cmd

