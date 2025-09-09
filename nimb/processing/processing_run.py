# -*- coding: utf-8 -*-
"""
This script is the main processing daemon for NIMB. It is designed to be
submitted to a cluster scheduler and run independently.

It finds new subjects, launches application-specific runners (like freesurfer_runner.py),
and handles the final archiving and moving of completed data.
"""
import os
import sys
import time
import json
import argparse
import shutil
from os import path

try:
    from pathlib import Path
    top = Path(__file__).resolve().parents[1]
    sys.path.append(str(top))
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from setup.config_manager import ConfigManager
from processing.schedule_helper import Scheduler
from distribution.utilities import load_json, save_json
from distribution.definitions import DEFAULT
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class ProcessingDaemon:
    """
    Manages the high-level processing lifecycle as a long-running, independent job.
    """
    def __init__(self, all_vars):
        self.all_vars = all_vars
        self.params = all_vars.params
        self.project = self.params.project
        self.local_vars = all_vars.location_vars['local']
        self.project_vars = all_vars.projects[self.project]
        
        # Paths
        self.nimb_home = self.local_vars['NIMB_PATHS']['NIMB_HOME']
        self.nimb_tmp = self.local_vars['NIMB_PATHS']['NIMB_tmp']
        self.db_path = path.join(self.nimb_tmp, "nimb_processing_db.json")
        self.py_run_cmd = self.local_vars["PROCESSING"]["python3_run_cmd"]

        # Components
        self.scheduler = Scheduler(self.local_vars)
        self.db = self._load_db()

    def run_loop(self):
        """
        The main daemon loop that continuously manages the processing queue.
        """
        log.info("Processing daemon started.")
        
        walltime_str = self.local_vars["PROCESSING"].get("batch_walltime", "12:00:00")
        h, m, s = map(int, walltime_str.split(':'))
        max_runtime_seconds = (h * 3600 + m * 60 + s) - 600
        start_time = time.time()
        
        while (time.time() - start_time) < max_runtime_seconds:
            log.info("--- Starting Daemon Cycle ---")
            self._find_and_queue_new_subjects()
            self._launch_app_runners()
            self._archive_completed_subjects()
            
            log.info("Daemon cycle complete. Sleeping for 2 minutes.")
            time.sleep(120)

        self._resubmit_daemon()

    def _find_and_queue_new_subjects(self):
        """
        Scans for `new_subjects_*.json` files and adds subjects to the main DB.
        """
        log.info("Checking for new subjects to queue...")
        for app, app_data in DEFAULT.APP_FILES.items():
            app_key = f"PROCESS_{app_data['name_abbrev']}"
            new_subjects_file = path.join(self.nimb_tmp, app_data["new_subjects"])
            
            if path.exists(new_subjects_file) and os.path.getsize(new_subjects_file) > 2:
                new_subjects = load_json(new_subjects_file)
                for subject_id, data_paths in new_subjects.items():
                    if subject_id not in self.db[app_key]:
                        self.db[app_key][subject_id] = {"status": "queued", "paths": data_paths}
                        log.info(f"Queued subject '{subject_id}' for '{app}'.")
                
                self._save_db()
                save_json({}, new_subjects_file) # Clear file after processing

    def _launch_app_runners(self):
        """
        Checks if an application runner is already active. If not, and if there
        are queued subjects, it launches the runner.
        """
        log.info("Checking status of application runners...")
        for app, app_data in DEFAULT.APP_FILES.items():
            runner_lock_file = path.join(self.nimb_tmp, f"{app}_runner.lock")
            
            # Simple lock file check to see if a runner job is already submitted
            if path.exists(runner_lock_file):
                log.info(f"'{app}' runner is already active.")
                continue

            app_key = f"PROCESS_{app_data['name_abbrev']}"
            has_queued_subjects = any(v['status'] == 'queued' for v in self.db[app_key].values())

            if has_queued_subjects:
                log.info(f"Found queued subjects for '{app}'. Launching runner.")
                
                runner_script = app_data["run_file"] # e.g., 'freesurfer_runner.py'
                cmd = f'{self.py_run_cmd} {runner_script} -project {self.project}'
                cd_cmd = path.join(self.nimb_home, 'processing', app)
                
                job_id = self.scheduler.submit_4_processing(
                    cmd, f"nimb_{app}_runner", 'run', cd_cmd, 
                    activate_fs=(app == 'freesurfer'), python_load=True
                )
                
                if job_id:
                    with open(runner_lock_file, 'w') as f:
                        f.write(job_id)
                    log.info(f"'{app}' runner submitted with Job ID: {job_id}")
                else:
                    log.error(f"Failed to submit '{app}' runner.")

    def _archive_completed_subjects(self):
        """
        Checks for processed output, moves them to final storage, and updates DB.
        """
        log.info("Checking for completed subjects to archive...")
        for app, app_data in DEFAULT.APP_FILES.items():
            nimb_processed_dir = self.local_vars[app.upper()]["NIMB_PROCESSED"]
            final_storage_dir = self.project_vars[app_data["dir_store_proc"]][1]
            
            if not path.isdir(nimb_processed_dir): continue

            for filename in os.listdir(nimb_processed_dir):
                if filename.endswith(".zip"):
                    subject_id = filename.replace(".zip", "")
                    src_path = path.join(nimb_processed_dir, filename)
                    dest_path = path.join(final_storage_dir, filename)

                    try:
                        log.info(f"Archiving completed subject '{subject_id}': {src_path} -> {dest_path}")
                        shutil.move(src_path, dest_path)
                        
                        # Update status in the main DB
                        app_key = f"PROCESS_{app_data['name_abbrev']}"
                        if subject_id in self.db[app_key]:
                            self.db[app_key][subject_id]["status"] = "completed_archived"
                            
                    except Exception as e:
                        log.error(f"Failed to archive '{subject_id}': {e}")
        self._save_db()

    def _resubmit_daemon(self):
        """Resubmits this script to the scheduler."""
        log.warning("Walltime approaching. Re-submitting daemon.")
        cd_cmd = path.join(self.nimb_home, 'processing')
        cmd = f'{self.py_run_cmd} processing_run.py -project {self.project}'
        self.scheduler.submit_4_processing(cmd, 'nimb_daemon', 'run', cd_cmd)

    def _load_db(self):
        """Loads or creates the main processing database."""
        if path.isfile(self.db_path):
            return load_json(self.db_path)
        
        log.warning("Main processing DB not found. Creating a new one.")
        db = {"PROJECTS": {self.project: []}, "PROCESSED": {}}
        for app, data in DEFAULT.APP_FILES.items():
            db[f"PROCESS_{data['name_abbrev']}"] = {}
        return db

    def _save_db(self):
        """Saves the state of the main processing database."""
        save_json(self.db, self.db_path, indent=4)


def main():
    parser = argparse.ArgumentParser(description="NIMB Processing Daemon")
    parser.add_argument("-project", required=True, help="Name of the project.")
    args = parser.parse_args()

    try:
        all_vars = ConfigManager(args=args)
        daemon = ProcessingDaemon(all_vars)
        daemon.run_loop()
    except Exception:
        log.error("A fatal error occurred in the processing daemon.", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

