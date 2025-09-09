# -*- coding: utf-8 -*-
"""
The Scheduler class is a helper utility for submitting
jobs to different processing environments like Slurm or tmux.
"""

from os import path, system
import time
import subprocess
import logging

log = logging.getLogger(__name__)

class Scheduler:
    """
    Handles the creation and submission of job scripts to a scheduler.
    """
    def __init__(self, local_vars):
        self.local_vars = local_vars
        self.processing_config = self.local_vars["PROCESSING"]
        self.fs_config = self.local_vars["FREESURFER"]

        # Paths and commands from config
        self.nimb_tmp = self.local_vars["NIMB_PATHS"]['NIMB_tmp']
        self.submit_enabled = self.processing_config.get("SUBMIT", 1) == 1
        self.processing_env = self.processing_config.get("processing_env", "tmux")
        self.python_load_cmd = self.processing_config.get("python3_load_cmd", "")

    def submit_4_processing(self, cmd, name, task, cd_cmd='', activate_fs=True, python_load=True):
        """
        Main entry point to submit a job.
        Returns the job ID if submission is successful, otherwise None.
        """
        if not self.submit_enabled:
            log.warning("Submission is disabled in local.json (SUBMIT != 1). Job not sent.")
            log.info(f"  -> Intended command: cd {cd_cmd} && {cmd}")
            return None

        if self.processing_env == 'slurm':
            return self._submit_to_slurm(cmd, name, task, cd_cmd, activate_fs, python_load)
        elif self.processing_env == 'tmux':
            return self._submit_to_tmux(cmd, name, cd_cmd, activate_fs, python_load)
        else:
            log.error(f"Unsupported processing environment: '{self.processing_env}'")
            return None

    def _get_submit_file_names(self, name, task):
        """Generates unique names for script and output files."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_name = name.replace(os.sep, "_").replace(" ", "_") # Sanitize name
        files_root = f'{safe_name}_{task}_{timestamp}'
        sh_file = f'{files_root}.sh'
        out_file = f'{files_root}.out'
        return sh_file, out_file

    def _submit_to_slurm(self, cmd, name, task, cd_cmd, activate_fs, python_load):
        """Builds and submits a Slurm script."""
        sh_file, out_file = self.get_submit_file_names(name, task)
        sh_f_abspath = path.join(self.nimb_tmp, sh_file)
        out_file_abspath = path.join(self.nimb_tmp, out_file)

        walltime = self.processing_config.get("batch_walltime", "12:00:00")
        
        script_lines = self.processing_config.get("text4_scheduler", ["#!/bin/sh"])
        script_lines.append(f'{self.processing_config["batch_walltime_cmd"]}{walltime}')
        script_lines.append(f'{self.processing_config["batch_output_cmd"]}{out_file_abspath}')
        
        if activate_fs:
            script_lines.append(self.fs_config["export_FreeSurfer_cmd"])
            script_lines.append(f'export SUBJECTS_DIR={self.fs_config["SUBJECTS_DIR"]}')
            script_lines.append(self.fs_config["source_FreeSurfer_cmd"])
        if python_load and self.python_load_cmd:
            script_lines.append(self.python_load_cmd)
        if cd_cmd:
            script_lines.append(cd_cmd)
        
        script_lines.append(cmd)
        
        with open(sh_f_abspath, 'w') as f:
            f.write('\n'.join(script_lines) + '\n')

        log.info(f"Submitting Slurm job script: {sh_f_abspath}")
        try:
            result = subprocess.run(['sbatch', sh_f_abspath], capture_output=True, text=True, check=True)
            job_id = result.stdout.strip().split(' ')[-1]
            return job_id
        except (subprocess.CalledProcessError, FileNotFoundError, IndexError) as e:
            log.error(f"Failed to submit job to Slurm: {e}")
            if hasattr(e, 'stderr'): log.error(f"Slurm error: {e.stderr}")
            return None

    def _submit_to_tmux(self, cmd, name, cd_cmd, activate_fs, python_load):
        """Submits a command to a new tmux session."""
        timestamp = time.strftime("%Y%m%d_%H%M")
        session_name = f'nimb_{name}_{timestamp}'
        
        log.info(f"Submitting job to tmux session: {session_name}")
        system(f'tmux new -d -s {session_name}')
        
        if activate_fs:
            system(f"tmux send-keys -t '{session_name}' '{self.fs_config['export_FreeSurfer_cmd']}' ENTER")
            system(f"tmux send-keys -t '{session_name}' 'export SUBJECTS_DIR={self.fs_config['SUBJECTS_DIR']}' ENTER")
            system(f"tmux send-keys -t '{session_name}' '{self.fs_config['source_FreeSurfer_cmd']}' ENTER")
        if python_load and self.python_load_cmd:
            system(f"tmux send-keys -t '{session_name}' '{self.python_load_cmd}' ENTER")
        if cd_cmd:
            system(f"tmux send-keys -t '{session_name}' '{cd_cmd}' ENTER")
        
        system(f"tmux send-keys -t '{session_name}' \"{cmd}\" ENTER")
        
        return session_name

