# -*- coding: utf-8 -*-
"""
This script is an independent runner for processing a single subject with DIPY.
It is designed to be submitted as a job to a scheduler by the main processing daemon.
"""

import os
import sys
import argparse
import logging
import shutil
from os import path

# Adjust path to import other NIMB modules
try:
    from pathlib import Path
    top = Path(__file__).resolve().parents[2]
    sys.path.append(str(top))
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from setup.config_manager import ConfigManager
from distribution.utilities import load_json
from . import dipy_helper

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


class DipyRunner:
    """
    Encapsulates the logic for running the DIPY pipeline on a single subject.
    """
    def __init__(self, all_vars, subject_id):
        self.all_vars = all_vars
        self.subject_id = subject_id
        self.local_vars = all_vars.location_vars['local']
        self.dp_vars = self.local_vars.get('DIPY', {})

        # Paths
        self.nimb_tmp = self.local_vars['NIMB_PATHS']['NIMB_tmp']
        self.subjects_dir = self.dp_vars.get('SUBJECTS_DIR')
        self.main_db_path = path.join(self.nimb_tmp, "nimb_processing_db.json")

    def run_analysis(self):
        """
        Executes the full DIPY processing pipeline for the subject.
        """
        log.info(f"Starting DIPY analysis for subject: {self.subject_id}")

        dwi_path, bval_path, bvec_path = self._get_dwi_paths()
        if not all([dwi_path, bval_path, bvec_path]):
            self._handle_error("missing_dwi_files")
            return

        # Create a temporary directory inside SUBJECTS_DIR for this subject's output
        subject_output_dir = path.join(self.subjects_dir, self.subject_id)
        os.makedirs(subject_output_dir, exist_ok=True)

        try:
            helper = dipy_helper.DipyHelper(dwi_path, bval_path, bvec_path, subject_output_dir, self.subject_id)
            
            log.info("Step 1: Denoising...")
            helper.run_denoising()

            log.info("Step 2: DTI Fitting...")
            helper.run_dti_fitting()

            log.info("Step 3: Streamline Extraction...")
            helper.run_streamline_extraction()
            
            log.info("Step 4: Connectivity Matrix...")
            helper.run_connectivity_matrix()

            self._handle_completion(subject_output_dir)

        except Exception:
            log.error(f"An error occurred during DIPY processing for {self.subject_id}.", exc_info=True)
            self._handle_error("analysis_failed")

    def _get_dwi_paths(self):
        """Retrieves DWI, bval, and bvec file paths from the main processing DB."""
        db = load_json(self.main_db_path)
        subject_info = db.get("PROCESS_dp", {}).get(self.subject_id, {})
        dwi_data = subject_info.get("paths", {}).get("dwi", {})
        
        dwi_path = dwi_data.get("dwi", [None])[0]
        bval_path = dwi_data.get("bval", [None])[0]
        bvec_path = dwi_data.get("bvec", [None])[0]
        
        if dwi_path and bval_path and bvec_path:
            return dwi_path, bval_path, bvec_path
        
        log.error(f"Could not find valid DWI/bval/bvec file paths for {self.subject_id}")
        return None, None, None

    def _handle_completion(self, subject_output_dir):
        """Archives the results into a zip file in the DIPY SUBJECTS_DIR."""
        archive_base_path = path.join(self.subjects_dir, self.subject_id)
        log.info(f"Archiving results for {self.subject_id} to {archive_base_path}.zip")
        
        try:
            shutil.make_archive(archive_base_path, 'zip', subject_output_dir)
            log.info("Archiving successful.")
            shutil.rmtree(subject_output_dir)
        except Exception as e:
            log.error(f"Failed to archive results for {self.subject_id}: {e}")
            self._handle_error("archiving_failed")

    def _handle_error(self, error_tag):
        """Handles errors by creating a flag file."""
        error_dir = self.dp_vars.get("NIMB_ERR")
        if error_dir:
            os.makedirs(error_dir, exist_ok=True)
            with open(path.join(error_dir, f"{self.subject_id}_{error_tag}.err"), 'w') as f:
                f.write(f"DIPY processing failed for subject {self.subject_id} with error: {error_tag}")

def main():
    parser = argparse.ArgumentParser(description="NIMB DIPY Single-Subject Runner")
    parser.add_argument("-project", required=True, help="Name of the project.")
    parser.add_argument("-subject", required=True, help="ID of the subject to process.")
    args, _ = parser.parse_known_args()

    try:
        all_vars = ConfigManager(args=args)
        runner = DipyRunner(all_vars, args.subject)
        runner.run_analysis()
    except Exception:
        log.error("A fatal error occurred in the DIPY runner.", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
