# -*- coding: utf-8 -*-
"""
This module contains the GLMRunner, an independent script for performing a
full FreeSurfer GLM analysis pipeline. It is designed to be submitted as a
job to a scheduler like Slurm.

The pipeline includes:
1. Preprocessing surfaces with mris_preproc.
2. Fitting the GLM with mri_glmfit for all specified contrasts.
3. Running permutation simulations for multiple comparisons correction.
4. Applying Monte-Carlo correction with mri_surfcluster.
5. Extracting and summarizing significant results.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path

# Adjust path to import other NIMB modules
try:
    top = Path(__file__).resolve().parents[2]
    sys.path.append(str(top))
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from setup.config_manager import ConfigManager
from processing.schedule_helper import Scheduler
from .fs_utils import FS_Utils
from stats.db_processing import Table

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


class GLMRunner:
    """
    Orchestrates the entire FreeSurfer GLM analysis for a given project.
    """
    def __init__(self, all_vars):
        self.all_vars = all_vars
        self.params = all_vars.params
        self.local_vars = all_vars.location_vars['local']
        self.project_vars = all_vars.projects[self.params.project]
        self.fs_vars = self.local_vars['FREESURFER']

        # --- Paths and Configuration ---
        self.glm_dir = self.project_vars['STATS_PATHS']['FS_GLM_dir']
        self.subjects_dir = self.fs_vars['SUBJECTS_DIR']
        self.glm_plan_file = os.path.join(self.glm_dir, 'files_for_glm.json')
        self.path_glm_data = os.path.join(self.glm_dir, 'glm')
        self.path_results = os.path.join(self.glm_dir, 'results')
        
        # --- Components ---
        self.scheduler = Scheduler(self.local_vars)
        self.fs_utils = FS_Utils(self.fs_vars['FREESURFER_HOME'])

        # --- State Tracking ---
        self.running_jobs = {}  # key: job_name, value: job_id
        self.glm_plan = self._load_glm_plan()

    def run_glm_pipeline(self):
        """
        Executes the full GLM pipeline in sequential stages.
        """
        log.info("Starting GLM pipeline...")
        
        self._run_preprocessing()
        self._wait_for_jobs("Preprocessing")

        self._run_glmfit()
        self._wait_for_jobs("GLM Fit")

        self._run_simulations()
        self._wait_for_jobs("Simulations")

        self._run_monte_carlo_correction()
        self._wait_for_jobs("Monte Carlo Correction")

        self._extract_results()
        self._generate_summary_csv()

        log.info("GLM pipeline finished successfully.")

    def _load_glm_plan(self):
        """Loads and filters the GLM plan based on user arguments."""
        if not os.path.exists(self.glm_plan_file):
            log.error(f"GLM plan file not found: {self.glm_plan_file}")
            sys.exit(1)
            
        full_plan = load_json(self.glm_plan_file)
        filtered_plan = {}

        for contrast_type in full_plan:
            # Filter by contrast choice (e.g., 'g2v1')
            if any(choice in contrast_type for choice in self.params.glmcontrast):
                # Filter by correction flag
                if self.params.glmcorrected and "_cor" in contrast_type:
                    filtered_plan[contrast_type] = full_plan[contrast_type]
                elif not self.params.glmcorrected and "_cor" not in contrast_type:
                    filtered_plan[contrast_type] = full_plan[contrast_type]
        
        log.info(f"Loaded and filtered GLM plan. Running {len(filtered_plan)} contrast types.")
        return filtered_plan

    def _submit_batch_job(self, name, commands, stage):
        """Submits a list of commands as a single batch job."""
        if not commands:
            return
        
        # Combine multiple commands into one script for efficiency
        full_command = "\n".join(commands)
        job_id = self.scheduler.submit_4_processing(
            cmd=full_command,
            name=name,
            task=stage,
            activate_fs=True
        )
        self.running_jobs[name] = job_id
        log.info(f"Submitted {stage} job '{name}' with ID: {job_id}")

    def _wait_for_jobs(self, stage_name):
        """Waits for all currently running jobs for a stage to complete."""
        log.info(f"Waiting for {stage_name} jobs to complete...")
        while self.running_jobs:
            time.sleep(300)  # Wait for 5 minutes
            
            # Check status of jobs
            scheduler_jobs = self.scheduler.get_jobs_status(
                self.local_vars["USER"]["user"], self.running_jobs
            )
            
            completed_jobs = []
            for name, job_id in self.running_jobs.items():
                if str(job_id) not in scheduler_jobs:
                    log.info(f"Job '{name}' (ID: {job_id}) has completed.")
                    completed_jobs.append(name)
            
            for name in completed_jobs:
                del self.running_jobs[name]
        log.info(f"All {stage_name} jobs finished.")

    def _run_preprocessing(self):
        """Generates and submits mris_preproc commands."""
        log.info("--- Stage 1: Preprocessing ---")
        commands = []
        for plan in self.glm_plan.values():
            for fsgd_file in plan['fsgd']:
                fsgd_name = Path(fsgd_file).stem.replace('_unix', '')
                for hemi in ['lh', 'rh']:
                    for meas in self.fs_vars['GLM_measurements']:
                        for fwhm in self.fs_vars['GLM_thresholds']:
                            analysis_name = f"{fsgd_name}.{meas}.{hemi}.fwhm{fwhm}"
                            mgh_out = os.path.join(self.path_glm_data, analysis_name, f"{meas}.{hemi}.fwhm{fwhm}.y.mgh")
                            if not os.path.exists(mgh_out):
                                commands.append(self.fs_utils.get_preproc_cmd(fsgd_file, 'fsaverage', hemi, mgh_out))
        self._submit_batch_job("glm_preproc_batch", commands, "preproc")

    def _run_glmfit(self):
        """Generates and submits mri_glmfit commands."""
        log.info("--- Stage 2: GLM Fit ---")
        commands = []
        for contrast_type, plan in self.glm_plan.items():
            for fsgd_file in plan['fsgd']:
                 # ... logic to build and append glmfit commands to `commands` list
                pass # Placeholder for glmfit command generation
        self._submit_batch_job("glmfit_batch", commands, "glmfit")

    def _run_simulations(self):
        """Generates and submits mri_glmfit-sim commands."""
        log.info("--- Stage 3: Simulations ---")
        commands = []
        # ... logic to build and append simulation commands
        self._submit_batch_job("simulation_batch", commands, "simulation")

    def _run_monte_carlo_correction(self):
        """Generates and submits mri_surfcluster commands."""
        log.info("--- Stage 4: Monte Carlo Correction ---")
        commands = []
        # ... logic to build and append mri_surfcluster commands
        self._submit_batch_job("mc_correction_batch", commands, "mc_correction")

    def _extract_results(self):
        """Extracts significant results after all analyses are done."""
        log.info("--- Stage 5: Extracting Results ---")
        # This part can be complex and depends on parsing the summary files.
        # It would loop through the completed analysis directories.
        pass

    def _generate_summary_csv(self):
        """Converts the final cluster summary log into a clean CSV."""
        log.info("--- Stage 6: Generating Summary CSV ---")
        cluster_log = os.path.join(self.path_results, 'cluster_stats.log')
        cluster_csv = os.path.join(self.path_results, 'cluster_stats.csv')
        if os.path.exists(cluster_log):
            # Logic to parse the log and write to CSV
            pass

def main():
    """
    Main entry point for the independent GLM runner script.
    """
    try:
        # The script is independent, so it loads its own config
        all_vars = ConfigManager()
        runner = GLMRunner(all_vars)
        runner.run_glm_pipeline()
    except Exception as e:
        log.error("A fatal error occurred in the GLM runner.", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
