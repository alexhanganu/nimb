# -*- coding: utf-8 -*-
"""
This module provides a unified manager for all data classification and
BIDS conversion tasks within the NIMB application. It consolidates the logic
for scanning source directories, identifying MRI modalities, and converting
data to the BIDS format using dcm2bids.
"""

import os
import shutil
import json
import logging
import subprocess
import datetime as dt
from collections import defaultdict

# Assumed project structure allows these imports
from ..distribution.utilities import save_json, load_json, makedir_ifnot_exist
from ..distribution.manage_archive import is_archive, ZipArchiveManagement
from ..distribution.distribution_definitions import DEFAULT

log = logging.getLogger(__name__)

# --- Constants formerly in classify_definitions.py ---

# Keywords to exclude when scanning for relevant MR sequences
MR_TYPES_TO_EXCLUDE = [
    'calibration', 'localizer', 'loc', 'cbf', 'isotropic', 'fractional',
    'average_dc', 'perfusion', 'tse', 'survey', 'scout', 'hippo', 'pasl',
    'multi_reset', 'dual_echo', 'gre'
]

# Keywords to identify different MR modalities
MR_MODALITIES = {
    'flair': ['flair'],
    'dwi': ['hardi', 'dti', 'diffus'],
    'bold': ['resting_state_fmri', 'rsfmri', 'mocoseries', 'rest'],
    'fmap': ['field_map', 'field_mapping', 'fieldmap'],
    't1': ['t1', 'spgr', 'rage', '3d_sag'],
    't2': ['t2'],
    'pd': ['pd'],
    'swi': ['swi']
}

# Mapping of NIMB's internal modality labels to BIDS data types
BIDS_TYPES = {
    'anat': ['t1', 'flair', 't2', 'swi', 'pd'],
    'dwi': ['dwi'],
    'func': ['bold'],
    'fmap': ['fmap']
}

# Mapping of NIMB modality labels to dcm2bids modality labels
NIMB_TO_DCM2BIDS_MODALITY = {
    "t1": "T1w",
    "t2": "T2w",
    "flair": "FLAIR",
    "dwi": "dwi",
    "bold": "bold",
}


class ClassificationManager:
    """
    Orchestrates the classification of source MRI data and its conversion
    to the BIDS format.
    """
    def __init__(self, all_vars):
        self.params = all_vars.params
        self.project_vars = all_vars.projects[self.params.project]
        self.local_vars = all_vars.location_vars['local']
        
        self.project_name = self.params.project
        self.source_dir = self.project_vars["SOURCE_SUBJECTS_DIR"][1]
        self.bids_dir = self.project_vars["SOURCE_BIDS_DIR"][1]
        self.tmp_dir = self.local_vars["NIMB_PATHS"]["NIMB_tmp"]
        
        self.fix_spaces = self.params.fix_spaces
        self.scan_report_path = os.path.join(self.source_dir, DEFAULT.F_NIMB_CLASSIFIED)

    # =========================================================================
    # PUBLIC METHODS (Entry Points)
    # =========================================================================

    def generate_scan_report(self, subjects_to_scan=None, update=True):
        """
        Scans source directories to identify and categorize MR data,
        saving the results to a 'nimb_classified.json' report.
        This is the first step before BIDS conversion.
        """
        log.info("Starting source data scan to generate classification report...")
        
        if subjects_to_scan is None:
            subjects_to_scan = os.listdir(self.source_dir)

        scan_report = self._load_existing_report() if update else {}

        for subject_id in subjects_to_scan:
            subject_path = os.path.join(self.source_dir, subject_id)
            if not os.path.isdir(subject_path) and not is_archive(subject_path)[0]:
                continue
            
            log.info(f"Scanning subject/archive: {subject_id}")
            scan_data = self._scan_subject(subject_path)
            if scan_data:
                scan_report.update(scan_data)
        
        log.info(f"Scan complete. Saving report to: {self.scan_report_path}")
        save_json(scan_report, self.scan_report_path)
        return True, scan_report

    def convert_to_bids(self):
        """
        Uses the generated scan report ('nimb_classified.json') to convert
        the source data into a BIDS-compliant structure using dcm2bids.
        """
        log.info("Starting BIDS conversion process...")
        if not os.path.exists(self.scan_report_path):
            log.error(f"Scan report not found: {self.scan_report_path}. Please run '-process classify' first.")
            return

        scan_report = load_json(self.scan_report_path)
        config_file = self._get_dcm2bids_config()

        for subject_id, subject_data in scan_report.items():
            sessions = [s for s in subject_data if s.startswith('ses-')]
            for session in sessions:
                log.info(f"Converting subject '{subject_id}', session '{session}' to BIDS.")
                self._run_dcm2bids_for_session(subject_id, session, subject_data, config_file)

    # =========================================================================
    # PRIVATE METHODS - SCANNING (formerly classify_2nimb_bids.py)
    # =========================================================================

    def _load_existing_report(self):
        """Loads the existing scan report if it exists."""
        if os.path.exists(self.scan_report_path):
            log.info(f"Updating existing scan report: {self.scan_report_path}")
            return load_json(self.scan_report_path)
        return {}
        
    def _scan_subject(self, subject_path):
        """Scans a single subject directory or archive and returns its structure."""
        is_archived, _ = is_archive(subject_path)
        
        if is_archived:
            with ZipArchiveManagement(subject_path) as archive:
                content_list = archive.get_content_list()
            # This logic needs to be more robust for complex archives
            subject_id = os.path.basename(subject_path).split('.')[0] 
            classified_data = self._classify_paths(content_list)
            classified_data['archived'] = subject_path
            return {subject_id: classified_data}
        
        elif os.path.isdir(subject_path):
            subject_id = os.path.basename(subject_path)
            paths = [root for root, _, files in os.walk(subject_path) if any(f.endswith(('.dcm', '.nii', '.nii.gz')) for f in files)]
            classified_data = self._classify_paths(paths)
            classified_data['archived'] = ''
            return {subject_id: classified_data}
        
        return None

    def _classify_paths(self, path_list):
        """Classifies a list of file paths into sessions and modalities."""
        # This is a simplified combination of the original logic.
        # It assumes a relatively simple structure. A more complex project
        # might need the original date-based session detection.
        
        session_data = defaultdict(lambda: defaultdict(list))
        
        # 1. Filter and group paths by modality
        for path in path_list:
            if any(ex in path.lower() for ex in MR_TYPES_TO_EXCLUDE):
                continue
            
            modality = self._get_modality_from_path(path)
            if modality:
                # Simple session detection (e.g., looks for "ses-01")
                session_label = "ses-01" # Default if no session is found
                for part in path.split(os.sep):
                    if part.startswith("ses-"):
                        session_label = part
                        break
                session_data[session_label][modality].append(path)
        
        # 2. Structure into BIDS datatypes
        bids_structure = {}
        for session, modalities in session_data.items():
            bids_structure[session] = defaultdict(dict)
            for modality, paths in modalities.items():
                for dtype, allowed_modalities in BIDS_TYPES.items():
                    if modality in allowed_modalities:
                        bids_structure[session][dtype][modality] = paths
                        break
        return dict(bids_structure)
        
    def _get_modality_from_path(self, path):
        """Identifies the MR modality from a given path string."""
        path_lower = path.lower()
        for modality, keywords in MR_MODALITIES.items():
            if any(key in path_lower for key in keywords):
                return modality
        return None

    # =========================================================================
    # PRIVATE METHODS - BIDS CONVERSION (formerly dcm2bids_helper.py)
    # =========================================================================
    
    def _get_dcm2bids_config(self):
        """
        Ensures a project-specific dcm2bids config exists, copying the
        default if necessary.
        """
        project_config_name = f'dcm2bids_config_{self.project_name}.json'
        project_config_path = os.path.join(self.bids_dir, project_config_name)

        if not os.path.exists(project_config_path):
            log.info(f"Project config not found. Copying default to {project_config_path}")
            default_config_path = os.path.join(
                os.path.dirname(__file__), 'dcm2bids', 'dcm2bids_config_default.json'
            )
            if os.path.exists(default_config_path):
                shutil.copy(default_config_path, project_config_path)
            else:
                log.error("Default dcm2bids config is missing. Cannot proceed.")
                return None
        return project_config_path

    def _run_dcm2bids_for_session(self, subject_id, session, subject_data, config_file):
        """
        Executes the dcm2bids command for a single session's data.
        This is a simplified implementation. The original had complex logic for
        retries and auto-updating the config, which could be re-integrated if needed.
        """
        # dcm2bids needs a single input directory. We might need to stage files.
        # This is a major simplification. The original extracted from archives.
        # For now, we assume the source_dir contains unarchived DICOMs.
        dicom_dir = os.path.join(self.source_dir, subject_id)
        if not os.path.isdir(dicom_dir):
            log.warning(f"Skipping BIDS conversion for {subject_id}: Source is not a directory (archived data not yet fully supported in this version).")
            return

        command = [
            'dcm2bids',
            '-d', dicom_dir,
            '-p', subject_id,
            '-s', session,
            '-c', config_file,
            '-o', self.bids_dir,
            '--forceDcm2niix', # Often useful
            '--clobber' # Overwrite existing
        ]
        
        log.debug(f"Executing command: {' '.join(command)}")
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            log.info(f"dcm2bids output for {subject_id}/{session}:\n{result.stdout}")
            if result.stderr:
                log.warning(f"dcm2bids warnings:\n{result.stderr}")
        except FileNotFoundError:
            log.error("`dcm2bids` command not found. Is it installed and in your PATH?")
        except subprocess.CalledProcessError as e:
            log.error(f"dcm2bids failed for {subject_id}/{session} with exit code {e.returncode}.")
            log.error(f"STDOUT: {e.stdout}")
            log.error(f"STDERR: {e.stderr}")
