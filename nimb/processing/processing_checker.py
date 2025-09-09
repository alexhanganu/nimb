# -*- coding: utf-8 -*-
"""
This module provides the ProcessingChecker class, responsible for verifying
the status and completion of various processing stages, particularly for FreeSurfer.
"""
import os
import logging
from .freesurfer import fs_utils

log = logging.getLogger(__name__)

class ProcessingChecker:
    """
    Checks the output files of a processing pipeline to determine the status
    of a subject's analysis.
    """
    def __init__(self, app_vars, app='freesurfer'):
        self.app_vars = app_vars
        self.app = app
        self.subjects_dir = self.app_vars['SUBJECTS_DIR']
        
        if self.app == 'freesurfer':
            fs_home = self.app_vars.get(f"{app.upper()}_HOME")
            self.fs_utils = fs_utils.FS_Utils(fs_home)
            # The order of processing is critical
            self.proc_order = ["registration", "autorecon1", "autorecon2", "autorecon3", "qcache"]
        else:
            self.fs_utils = None
            self.proc_order = []

    def get_next_stage(self, subject_id):
        """
        Determines the next required processing stage for a subject.

        Returns:
            A tuple (status, data):
            - ('run_stage', 'stage_name')
            - ('complete', None)
            - ('error', 'error_description')
        """
        subject_path = os.path.join(self.subjects_dir, subject_id)

        # 1. Initial stage: If the subject directory doesn't exist, we start with registration.
        if not os.path.exists(subject_path):
            return 'run_stage', 'registration'

        # 2. Check for stale 'IsRunning' files which indicate a crashed process.
        if self._is_running_flag_present(subject_id, remove_stale_flags=True):
            log.warning(f"Stale 'IsRunning' file found for {subject_id}. Process likely crashed.")
            # We'll continue checking from the last known state.
        
        # 3. Check the main recon-all log for errors first.
        log_file_path = os.path.join(subject_path, 'scripts', 'recon-all.log')
        if "exited with ERRORS" in self._read_log_file(log_file_path):
            log.error(f"recon-all log for {subject_id} indicates an error.")
            error_type, solution_flag = self.fs_utils.get_error_solution(log_file_path)
            if solution_flag:
                return 'error_with_solution', (error_type, solution_flag)
            return 'error', 'unknown_log_error'

        # 4. Iterate through defined stages to find the first incomplete one.
        for stage in self.proc_order:
            if not self._is_stage_complete(subject_id, stage):
                log.info(f"Next stage for '{subject_id}': {stage}")
                return 'run_stage', stage
        
        log.info(f"All stages appear complete for '{subject_id}'.")
        return 'complete', None

    def _is_stage_complete(self, subject_id, stage):
        """Checks if a specific stage is complete by verifying its output files."""
        if stage == 'registration':
            # The 'registration' stage is complete if the subject directory exists
            # and contains the mri/orig folder.
            return os.path.isdir(os.path.join(self.subjects_dir, subject_id, 'mri', 'orig'))

        stage_info = self.fs_utils.processes.get(stage, {})
        files_to_check = stage_info.get("files_2chk", [])

        if not files_to_check:
            log.warning(f"No files defined to check completion for stage '{stage}'. Assuming complete.")
            return True

        for file_path in files_to_check:
            full_path = os.path.join(self.subjects_dir, subject_id, file_path)
            if not os.path.exists(full_path):
                return False
        return True

    def _is_running_flag_present(self, subject_id, remove_stale_flags=False):
        """Checks for 'IsRunning' flag files."""
        scripts_dir = os.path.join(self.subjects_dir, subject_id, 'scripts')
        if not os.path.isdir(scripts_dir):
            return False

        for flag_file in self.fs_utils.IsRunning_files:
            file_path = os.path.join(scripts_dir, flag_file)
            if os.path.exists(file_path):
                if remove_stale_flags:
                    log.warning(f"Removing stale lock file: {file_path}")
                    try: os.remove(file_path)
                    except OSError: pass # Ignore if it fails
                return True
        return False

    def _read_log_file(self, log_file_path):
        """Safely reads the content of a log file."""
        if not os.path.exists(log_file_path):
            return ""
        try:
            with open(log_file_path, 'r') as f:
                return f.read()
        except Exception:
            return ""

