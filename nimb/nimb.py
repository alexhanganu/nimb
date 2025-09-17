# -*- coding: utf-8 -*-
"""
NIMB Main Module
This is the main entry point for the NIMB application. It initializes the
configuration and dispatches tasks based on user input.
"""

import sys
import os
from setup.config_manager import ConfigManager
from distribution.distribution_manager import DistributionManager
from processing.schedule_helper import Scheduler
from classification.classifier import ClassificationManager

class NIMB:
    """Main object to orchestrate the NIMB pipeline."""
    def __init__(self, all_vars):
        self.all_vars = all_vars
        self.params = all_vars.params
        self.project_vars = all_vars.projects[self.params.project]
        self.local_vars = all_vars.location_vars['local']
        self.nimb_home = self.local_vars['NIMB_PATHS']['NIMB_HOME']
        self.logger = all_vars.logger
        self.scheduler = Scheduler(self.local_vars)
        self.py_run_cmd = self.local_vars['PROCESSING']["python3_run_cmd"]

        self.dist_manager = DistributionManager(all_vars)
        
        # A dictionary to map command-line arguments to handler methods
        self.process_handlers = {
            'ready': self._handle_ready,
            'classify-bids': self._handle_classify_bids,
            'process': self._handle_process,
            'fs-stats-get': self._handle_fs_stats_get,
            'fs-glm-prep': self._handle_fs_glm_prep,
            'fs-glm-run': self._handle_fs_glm_run,
            'fs-glm-images': self._handle_fs_glm_images,
            'run-stats': self._handle_run_stats
        }

    def run(self):
        """Dispatches the appropriate process based on user parameters."""
        handler = self.process_handlers.get(self.params.process)
        if handler:
            self.logger.info(f"Running process: {self.params.process}")
            handler()
        else:
            self.logger.error(f"Unknown process: '{self.params.process}'. Please check the command.")
            sys.exit(1)

    def _handle_ready(self):
        """Checks if the environment is ready."""
        self.dist_manager.check_ready()

    def _handle_classify_bids(self):
        """Handles the two-stage BIDS classification process."""
        self.logger.info("Initiating BIDS classification workflow...")
        classifier = ClassificationManager(self.all_vars)
        
        # Stage 1: Scan and create report
        success, _ = classifier.generate_scan_report(update=True)
        if not success:
            self.logger.error("Stage 1 (scan) failed. Aborting.")
            return

        # Stage 2: Convert using the report
        classifier.convert_to_bids()
        self.logger.info("BIDS classification workflow complete.")

    def _handle_process(self):
        """Submits the main processing daemon to the scheduler."""
        self.logger.info("Submitting the main processing daemon to the scheduler...")
        script_path = os.path.join(self.nimb_home, 'processing', 'processing_run.py')
        cmd = f"{self.py_run_cmd} {script_path} -project {self.params.project}"
        
        # No need for cd_cmd if using absolute paths
        self.scheduler.submit_4_processing(cmd, 'nimb_daemon', 'main_loop', activate_fs=False)
        self.logger.info("Processing daemon has been submitted.")

    def _handle_fs_stats_get(self):
        """Submits the FreeSurfer stats extraction runner to the scheduler."""
        self.logger.info("Submitting FreeSurfer stats extraction job...")
        stats_dir = self.project_vars["STATS_PATHS"]["STATS_HOME"]
        processed_dir = self.project_vars["PROCESSED_FS_DIR"][1]
        
        script_path = os.path.join(self.nimb_home, 'processing', 'freesurfer', 'fs_stats_runner.py')
        cmd = (f"{self.py_run_cmd} {script_path} "
               f"-project {self.params.project} "
               f"-stats_dir {stats_dir} "
               f"-dir_fs_processed {processed_dir}")
               
        self.scheduler.submit_4_processing(cmd, 'fs_stats_get', 'extraction', activate_fs=False)
        self.logger.info("Stats extraction job submitted.")
        
    def _handle_fs_glm_prep(self):
        """Runs the GLM preparation script locally."""
        self.logger.info("Preparing files for FreeSurfer GLM analysis...")
        # This process is typically fast and run locally, not scheduled
        from processing.freesurfer.fs_glm_prep import GLMManager
        glm_manager = GLMManager(self.all_vars)
        glm_manager.prepare_glm_files()
        self.logger.info("GLM preparation complete.")

    def _handle_fs_glm_run(self):
        """Submits the FreeSurfer GLM runner to the scheduler."""
        self.logger.info("Submitting FreeSurfer GLM analysis job...")
        glm_dir = self.project_vars["STATS_PATHS"]["FS_GLM_dir"]
        
        script_path = os.path.join(self.nimb_home, 'processing', 'freesurfer', 'fs_glm_runglm.py')
        cmd = (f"{self.py_run_cmd} {script_path} "
               f"-project {self.params.project} "
               f"-glm_dir {glm_dir} "
               f"-contrast {' '.join(self.params.glmcontrast)} "
               f"-permutations {self.params.glmpermutations}"
               f"{' -corrected' if self.params.glmcorrected else ''}")

        self.scheduler.submit_4_processing(cmd, 'fs_glm_run', 'analysis', activate_fs=True)
        self.logger.info("GLM analysis job submitted.")

    def _handle_fs_glm_images(self):
        """Submits the GLM image extraction runner to the scheduler."""
        self.logger.info("Submitting GLM image extraction job...")
        glm_dir = self.project_vars["STATS_PATHS"]["FS_GLM_dir"]
        
        script_path = os.path.join(self.nimb_home, 'processing', 'freesurfer', 'freesurfer_get_glm_images_runner.py')
        cmd = (f"{self.py_run_cmd} {script_path} "
               f"-project {self.params.project} "
               f"-glm_dir {glm_dir}")

        self.scheduler.submit_4_processing(cmd, 'fs_glm_images', 'extraction', activate_fs=True)
        self.logger.info("GLM image extraction job submitted.")

    def _handle_run_stats(self):
        """Submits the main statistical analysis runner to the scheduler."""
        self.logger.info("Submitting statistical analysis job...")
        script_path = os.path.join(self.nimb_home, 'stats', 'stats_runner.py')
        cmd = (f"{self.py_run_cmd} {script_path} "
               f"-project {self.params.project} "
               f"-step {self.params.step}")
               
        self.scheduler.submit_4_processing(cmd, 'nimb_stats', 'run', activate_fs=False)
        self.logger.info("Statistical analysis job submitted.")

def main():
    """Main function to run the NIMB application."""
    if sys.version_info < (3, 6):
        sys.stdout.write("NIMB requires Python 3.6 or higher.\n")
        sys.exit(1)
    
    try:
        all_vars = ConfigManager()
        app = NIMB(all_vars)
        app.run()
    except Exception:
        log.error("A fatal error occurred in the main application.", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

