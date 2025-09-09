# -*- coding: utf-8 -*-
"""
This script is an independent runner for processing a single subject with Nilearn.
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
from . import nl_helper

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class NilearnRunner:
    """
    Encapsulates the logic for running the Nilearn pipeline on a single subject.
    """
    def __init__(self, all_vars, subject_id):
        self.all_vars = all_vars
        self.subject_id = subject_id
        self.local_vars = all_vars.location_vars['local']
        self.nl_vars = self.local_vars.get('NILEARN', {})

        # Paths
        self.nimb_tmp = self.local_vars['NIMB_PATHS']['NIMB_tmp']
        self.subjects_dir = self.nl_vars.get('SUBJECTS_DIR')
        self.main_db_path = path.join(self.nimb_tmp, "nimb_processing_db.json")

    def run_analysis(self):
        """
        Executes the full Nilearn connectivity analysis for the subject.
        """
        log.info(f"Starting Nilearn analysis for subject: {self.subject_id}")

        bold_path = self._get_bold_path()
        if not bold_path:
            self._handle_error("missing_bold_file")
            return

        # Create a temporary directory inside SUBJECTS_DIR for this subject's output
        subject_output_dir = path.join(self.subjects_dir, self.subject_id)
        os.makedirs(subject_output_dir, exist_ok=True)

        try:
            # --- Harvard Oxford Atlas Analysis ---
            log.info("Running connectivity analysis with Harvard-Oxford atlas.")
            harvard_atlas = nl_helper.HarvardAtlas()
            labels, rois_ts = harvard_atlas.extract_label_rois(bold_path)
            connectivity_matrix = harvard_atlas.extract_connectivity(rois_ts)
            
            # Save results
            csv_path = path.join(subject_output_dir, f"{self.subject_id}_connectivity_harvard.csv")
            png_path = path.join(subject_output_dir, f"{self.subject_id}_corr_harvard.png")
            harvard_atlas.save_results(connectivity_matrix, labels, csv_path, png_path)
            
            # --- Add other atlases here if needed, e.g., Destrieux ---
            
            self._handle_completion(subject_output_dir)

        except Exception as e:
            log.error(f"An error occurred during Nilearn processing for {self.subject_id}.", exc_info=True)
            self._handle_error(f"analysis_failed_{e}")

    def _get_bold_path(self):
        """Retrieves the path to the BOLD nifty file from the main processing DB."""
        db = load_json(self.main_db_path)
        subject_info = db.get("PROCESS_nl", {}).get(self.subject_id, {})
        bold_paths = subject_info.get("paths", {}).get("func", {}).get("bold", [])
        
        if bold_paths and path.exists(bold_paths[0]):
            return bold_paths[0]
        
        log.error(f"Could not find a valid BOLD file path for {self.subject_id}")
        return None

    def _handle_completion(self, subject_output_dir):
        """Archives the results into a zip file in the NILEARN SUBJECTS_DIR."""
        archive_base_path = path.join(self.subjects_dir, self.subject_id)
        log.info(f"Archiving results for {self.subject_id} to {archive_base_path}.zip")
        
        try:
            shutil.make_archive(archive_base_path, 'zip', subject_output_dir)
            log.info("Archiving successful.")
            # Clean up the temporary subject directory after archiving
            shutil.rmtree(subject_output_dir)
        except Exception as e:
            log.error(f"Failed to archive results for {self.subject_id}: {e}")
            self._handle_error("archiving_failed")

    def _handle_error(self, error_tag):
        """Handles errors, potentially by creating an error flag file."""
        log.error(f"Handling error '{error_tag}' for {self.subject_id}.")
        error_dir = self.nl_vars.get("NIMB_ERR")
        if error_dir:
            if not os.path.exists(error_dir):
                os.makedirs(error_dir)
            # Create a flag file to indicate the error
            with open(path.join(error_dir, f"{self.subject_id}_{error_tag}.err"), 'w') as f:
                f.write(f"Nilearn processing failed for subject {self.subject_id} with error: {error_tag}")

def main():
    parser = argparse.ArgumentParser(description="NIMB Nilearn Single-Subject Runner")
    parser.add_argument("-project", required=True, help="Name of the project.")
    parser.add_argument("-subject", required=True, help="ID of the subject to process.")
    args, _ = parser.parse_known_args()

    try:
        all_vars = ConfigManager(args=args)
        runner = NilearnRunner(all_vars, args.subject)
        runner.run_analysis()
    except Exception:
        log.error("A fatal error occurred in the Nilearn runner.", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
