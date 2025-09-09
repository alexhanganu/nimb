# -*- coding: utf-8 -*-
"""
This script is an independent runner for processing a queue of subjects with
FreeSurfer. It's designed to be launched by the main processing daemon.

It manages its own database (`db_fs.json`) to track the `recon-all` progress
for each subject in its queue. It submits and monitors individual `recon-all`
jobs until all subjects are complete.
"""
import os
import sys
import argparse
import logging
import shutil
import time
from os import path

try:
    from pathlib import Path
    top = Path(__file__).resolve().parents[2]
    sys.path.append(str(top))
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from setup.config_manager import ConfigManager
from processing.processing_checker import ProcessingChecker
from processing.schedule_helper import Scheduler
from distribution.utilities import load_json, save_json
from distribution.definitions import DEFAULT
from .fs_utils import FS_Utils

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class FreesurferRunner:
    """
    Manages a queue of subjects for the FreeSurfer pipeline.
    """
    def __init__(self, all_vars):
        self.all_vars = all_vars
        self.project = all_vars.params.project
        self.local_vars = all_vars.location_vars['local']
        self.fs_vars = self.local_vars.get('FREESURFER', {})
        
        # Paths
        self.nimb_tmp = self.local_vars['NIMB_PATHS']['NIMB_tmp']
        self.subjects_dir = self.fs_vars.get('SUBJECTS_DIR')
        self.nimb_processed_dir = self.fs_vars.get('NIMB_PROCESSED')
        self.nimb_error_dir = self.fs_vars.get('NIMB_ERR')
        self.main_db_path = path.join(self.nimb_tmp, "nimb_processing_db.json")
        self.fs_db_path = path.join(self.nimb_tmp, DEFAULT.APP_FILES["freesurfer"]["db"])
        
        # Components
        self.scheduler = Scheduler(self.local_vars)
        self.checker = ProcessingChecker(self.fs_vars, app='freesurfer')
        self.fs_utils = FS_Utils(self.fs_vars.get('FREESURFER_HOME'))
        self.fs_db = self._load_fs_db()

    def run_queue_manager(self):
        """
        Main execution loop. Manages the queue, submits jobs, and checks progress.
        """
        log.info("Freesurfer Runner started.")
        self._add_new_subjects_to_queue()
        
        while self.fs_db['QUEUED'] or self.fs_db['RUNNING']:
            log.info("--- Starting FreeSurfer Runner Cycle ---")
            self._check_running_jobs()
            self._submit_queued_jobs()
            
            log.info(f"Cycle complete. {len(self.fs_db['QUEUED'])} queued, {len(self.fs_db['RUNNING'])} running.")
            log.info("Sleeping for 2 minutes.")
            time.sleep(120)

        log.info("All subjects in the queue have been processed. Exiting runner.")
        # Remove the lock file so the daemon knows it can start a new runner if needed
        runner_lock_file = path.join(self.nimb_tmp, "freesurfer_runner.lock")
        if path.exists(runner_lock_file):
            os.remove(runner_lock_file)

    def _add_new_subjects_to_queue(self):
        """Adds 'queued' subjects from the main DB to this runner's local DB."""
        main_db = load_json(self.main_db_path)
        fs_subjects = main_db.get("PROCESS_fs", {})
        
        for subject_id, info in fs_subjects.items():
            if info['status'] == 'queued' and subject_id not in self.fs_db['ALL_SUBJECTS']:
                self.fs_db['QUEUED'].append(subject_id)
                self.fs_db['ALL_SUBJECTS'][subject_id] = {'status': 'queued'}
                log.info(f"Added {subject_id} to the FreeSurfer processing queue.")
                # Update main DB status to 'processing'
                main_db["PROCESS_fs"][subject_id]['status'] = 'processing'

        self._save_fs_db()
        save_json(main_db, self.main_db_path)

    def _submit_queued_jobs(self):
        """Submits jobs for subjects in the 'QUEUED' list."""
        max_jobs = self.local_vars['PROCESSING'].get('max_nr_running_batches', 5)
        
        while self.fs_db['QUEUED'] and len(self.fs_db['RUNNING']) < max_jobs:
            subject_id = self.fs_db['QUEUED'].pop(0)
            status, stage = self.checker.get_next_stage(subject_id)

            if status == 'run_stage':
                t1_paths = self._get_t1_paths(subject_id)
                command = self.fs_utils.get_command(stage, subject_id, t1_paths)
                
                job_id = self.scheduler.submit_4_processing(
                    command, f"fs_{subject_id}", stage, 
                    cd_cmd=self.subjects_dir, activate_fs=True
                )
                
                if job_id:
                    self.fs_db['RUNNING'][subject_id] = {'stage': stage, 'job_id': job_id}
                    self.fs_db['ALL_SUBJECTS'][subject_id]['status'] = f"running_{stage}"
                    log.info(f"Submitted {stage} for {subject_id} with Job ID: {job_id}")
                else:
                    self.fs_db['QUEUED'].append(subject_id) # Re-queue on submission failure
                    log.error(f"Failed to submit job for {subject_id}.")
                    break # Stop submitting if scheduler fails
        self._save_fs_db()
    
    def _check_running_jobs(self):
        """Checks the status of currently running jobs."""
        # This is a simplified check based on file output. A more robust implementation
        # would query the scheduler (e.g., `squeue`) for job status.
        
        for subject_id in list(self.fs_db['RUNNING'].keys()):
            status, data = self.checker.get_next_stage(subject_id)
            
            if status == 'complete':
                log.info(f"Subject {subject_id} has completed processing.")
                self._handle_completion(subject_id)
            elif status == 'error':
                log.error(f"Subject {subject_id} encountered an error: {data}")
                self._handle_error(subject_id, data)
            elif status == 'run_stage' and data != self.fs_db['RUNNING'][subject_id]['stage']:
                # The job finished the previous stage and is ready for the next one.
                log.info(f"Stage '{self.fs_db['RUNNING'][subject_id]['stage']}' complete for {subject_id}.")
                del self.fs_db['RUNNING'][subject_id]
                self.fs_db['QUEUED'].append(subject_id)
        self._save_fs_db()
    
    def _handle_completion(self, subject_id):
        log.info(f"Archiving results for {subject_id}...")
        subject_path = path.join(self.subjects_dir, subject_id)
        archive_base = path.join(self.nimb_processed_dir, subject_id)
        try:
            shutil.make_archive(archive_base, 'zip', subject_path)
            self.fs_db['COMPLETED'].append(subject_id)
            del self.fs_db['RUNNING'][subject_id]
            self.fs_db['ALL_SUBJECTS'][subject_id]['status'] = 'completed'
            # Optional: shutil.rmtree(subject_path)
        except Exception as e:
            log.error(f"Archiving failed for {subject_id}: {e}")
    
    def _handle_error(self, subject_id, error_tag):
        log.error(f"Moving {subject_id} to error directory...")
        src_path = path.join(self.subjects_dir, subject_id)
        dest_path = path.join(self.nimb_error_dir, f"{subject_id}_{error_tag}")
        try:
            if path.exists(src_path):
                shutil.move(src_path, dest_path)
            self.fs_db['ERRORS'].append(subject_id)
            del self.fs_db['RUNNING'][subject_id]
            self.fs_db['ALL_SUBJECTS'][subject_id]['status'] = f"error_{error_tag}"
        except Exception as e:
            log.error(f"Failed to move error directory for {subject_id}: {e}")

    def _load_fs_db(self):
        if path.isfile(self.fs_db_path):
            return load_json(self.fs_db_path)
        
        log.warning("FreeSurfer DB not found. Creating a new one.")
        return {'QUEUED': [], 'RUNNING': {}, 'COMPLETED': [], 'ERRORS': [], 'ALL_SUBJECTS': {}}

    def _save_fs_db(self):
        save_json(self.fs_db, self.fs_db_path, indent=4)
        
    def _get_t1_paths(self, subject_id):
        """Helper to get T1w paths from the main DB."""
        main_db = load_json(self.main_db_path)
        return main_db.get("PROCESS_fs", {}).get(subject_id, {}).get("paths", {}).get("anat", {}).get("t1")


def main():
    parser = argparse.ArgumentParser(description="NIMB FreeSurfer Queue Runner")
    parser.add_argument("-project", required=True, help="Name of the project.")
    args, _ = parser.parse_known_args()

    try:
        all_vars = ConfigManager(args=args)
        runner = FreesurferRunner(all_vars)
        runner.run_queue_manager()
    except Exception:
        log.error("A fatal error occurred in the FreeSurfer runner.", exc_info=True)
        # Clean up lock file on crash if possible
        runner_lock_file = path.join(all_vars.location_vars['local']['NIMB_PATHS']['NIMB_tmp'], "freesurfer_runner.lock")
        if path.exists(runner_lock_file):
            os.remove(runner_lock_file)
        sys.exit(1)

if __name__ == "__main__":
    main()

