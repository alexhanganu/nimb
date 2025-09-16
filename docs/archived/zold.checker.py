# -*- coding: utf-8 -*-
"""
This module provides the ProcessingChecker class, responsible for verifying
the status and completion of various processing stages, particularly for FreeSurfer.
"""
import os
import logging
from .freesurfer import fs_definitions

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
        self.proc_order = self.app_vars.get("process_order", [])

        if self.app == 'freesurfer':
            fs_home = self.app_vars.get(f"{app.upper()}_HOME")
            self.fs_defs = fs_definitions.FSProcesses(fs_home)
        else:
            self.fs_defs = None # Placeholder for other apps like nilearn/dipy

    def get_next_stage(self, subject_id):
        """
        Determines the next required processing stage for a subject.

        Args:
            subject_id (str): The ID of the subject to check.

        Returns:
            str: The name of the next stage to run, or 'complete' if all
                 stages are finished, or 'error' if a check fails.
        """
        if self.app != 'freesurfer':
            log.warning(f"Checker not fully implemented for app: {self.app}")
            return 'error'

        # 1. Check if the subject directory exists (first step: registration)
        subject_path = os.path.join(self.subjects_dir, subject_id)
        if not os.path.exists(subject_path):
            return 'registration'

        # 2. Check if any 'IsRunning' files exist, which indicates a stuck process
        if self._is_running_flag_present(subject_id, remove_stale_flags=True):
            log.warning(f"Stale 'IsRunning' file found for {subject_id}. Process may have crashed.")
            # Depending on policy, you might return 'error' or attempt to rerun the last stage.
            # For now, we'll proceed assuming the user wants to continue.
            pass

        # 3. Iterate through defined processing stages to find the first incomplete one
        for stage in self.proc_order:
            is_complete = self._check_freesurfer_stage(subject_id, stage)
            if not is_complete:
                log.info(f"Stage '{stage}' is not complete for subject '{subject_id}'.")
                return stage
        
        log.info(f"All stages appear complete for subject '{subject_id}'.")
        return 'complete'

    def _check_freesurfer_stage(self, subject_id, stage):
        """
        Checks the completion of a specific FreeSurfer stage by looking for
        its expected output files.

        Returns:
            bool: True if the stage appears complete, False otherwise.
        """
        if not self.fs_defs or stage not in self.fs_defs.processes:
            log.error(f"Unknown FreeSurfer stage: {stage}")
            return False

        files_to_check = self.fs_defs.processes[stage].get("files_2chk", [])
        if not files_to_check:
            # If no files are defined, we can check the log file for success
            log_file_path = os.path.join(self.subjects_dir, subject_id, 'scripts', self.fs_defs.log(stage))
            return self._was_log_successful(log_file_path)

        for file_path in files_to_check:
            full_path = os.path.join(self.subjects_dir, subject_id, file_path)
            if not os.path.exists(full_path):
                log.debug(f"Missing file for stage '{stage}': {full_path}")
                return False
        
        return True

    def _is_running_flag_present(self, subject_id, remove_stale_flags=False):
        """
        Checks for the presence of 'IsRunning' files in the subject's script directory.
        """
        scripts_dir = os.path.join(self.subjects_dir, subject_id, 'scripts')
        if not os.path.isdir(scripts_dir):
            return False

        is_running_files = self.fs_defs.IsRunning_files if self.fs_defs else []
        for flag_file in is_running_files:
            file_path = os.path.join(scripts_dir, flag_file)
            if os.path.exists(file_path):
                if remove_stale_flags:
                    log.warning(f"Removing stale lock file: {file_path}")
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        log.error(f"Could not remove stale lock file {file_path}: {e}")
                        return True # Return True to indicate it's still "running"
                else:
                    return True
        return False

    def _was_log_successful(self, log_file_path):
        """Checks a log file for a success message."""
        if not os.path.exists(log_file_path):
            return False
        try:
            with open(log_file_path, 'r') as f:
                content = f.read()
            # This is a common success message in recon-all logs
            return "finished without error" in content
        except Exception as e:
            log.error(f"Could not read log file {log_file_path}: {e}")
            return False
