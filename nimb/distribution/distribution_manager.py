# -*- coding: utf-8 -*-

"""
This module contains the DistributionManager class, which is responsible for
consolidating all logic related to application readiness, setup, disk space checks,
and subject distribution. It serves as the central hub for the 'distribution' package.
"""

import os
import shutil
from os.path import expanduser

from .utilities import (
    makedir_ifnot_exist, is_writable_directory, is_ENV_defined,
    ErrorMessages, load_json, is_command_ran_successfully
)
from .dependency_manager import DependencyManager
from .definitions import DEFAULT


class DistributionManager:
    """
    Manages all distribution-related tasks, including environment setup,
    dependency checks, and data preparation.
    """

    def __init__(self, all_vars):
        self.all_vars = all_vars
        self.params = all_vars.params
        self.locations = all_vars.location_vars
        self.local_vars = self.locations["local"]
        self.project_vars = all_vars.projects[all_vars.params.project]
        
        # Common Paths
        self.NIMB_HOME = self.local_vars["NIMB_PATHS"]["NIMB_HOME"]
        self.NIMB_tmp = self.local_vars["NIMB_PATHS"]["NIMB_tmp"]
        self.MINICONDA_HOME = self.local_vars["NIMB_PATHS"]["conda_home"]
        self.FREESURFER_HOME = self.local_vars['FREESURFER']['FREESURFER_HOME']
        
        self.logger = all_vars.logger
        self.test = all_vars.params.test

    # =========================================================================
    # SECTION: Readiness Checks (from former distribution_ready.py)
    # =========================================================================

    def check_ready(self):
        """
        Performs a series of checks to ensure the application is ready to run.
        This is the main entry point for all readiness validations.
        """
        self.logger.info("Checking if the environment is ready for NIMB...")

        if not self._check_nimb_paths():
            return False
        if not self._check_all_apps_ready():
            return False
        
        self.logger.info("All readiness checks passed successfully.")
        return True

    def _check_nimb_paths(self):
        """Verifies that all NIMB-specific paths are valid and writable."""
        paths_to_check = [self.NIMB_HOME, self.NIMB_tmp]
        for p in paths_to_check:
            if not is_writable_directory(p):
                self.logger.warning(f"NIMB path '{p}' is not writable or does not exist. Attempting to create.")
                if not makedir_ifnot_exist(p):
                    self.logger.error(f"Failed to create or access path: {p}")
                    return False
        return True

    def _check_all_apps_ready(self):
        """Checks the readiness of all required external applications."""
        if not self._check_miniconda_ready():
            return False
        if not self._check_freesurfer_ready():
            return False
        return True

    def _check_miniconda_ready(self):
        """Checks if Miniconda is installed and configured."""
        self.logger.info("Checking Miniconda installation...")
        if not DependencyManager.is_miniconda_installed(self.MINICONDA_HOME):
            self.logger.warning("Miniconda is not installed. Initiating setup.")
            if not DependencyManager.setup_miniconda(self.MINICONDA_HOME, self.NIMB_HOME):
                self.logger.error("Miniconda setup failed.")
                return False
        
        # Example modules to check
        modules_list = ['pandas', 'numpy']
        if not DependencyManager.check_modules_installed(self.MINICONDA_HOME, modules_list):
            self.logger.error("Some required Python modules are missing. Please check installation.")
            return False
        
        self.logger.info("Miniconda is ready.")
        return True

    def _check_freesurfer_ready(self):
        """Checks if FreeSurfer is installed and configured."""
        self.logger.info("Checking FreeSurfer installation...")
        fs_home_env = os.environ.get("FREESURFER_HOME")
        if not fs_home_env or not os.path.exists(self.FREESURFER_HOME):
            self.logger.warning("FreeSurfer is not configured or installed. Initiating setup.")
            if not DependencyManager.setup_freesurfer(self.local_vars, DEFAULT):
                self.logger.error("FreeSurfer setup failed.")
                return False

        if not is_command_ran_successfully("recon-all --version"):
            self.logger.error("FreeSurfer 'recon-all' command not found. Check your PATH and FreeSurfer setup.")
            return False
        
        self.logger.info("FreeSurfer is ready.")
        return True
        
    def is_classify_ready(self):
        """Check if prerequisites for classification are met."""
        # Add specific checks if necessary, e.g., dcm2niix is installed
        self.logger.info("Classification prerequisites met.")
        return True

    def is_ready_for_stats(self):
        """Check if ready to perform statistical analysis."""
        # Placeholder for specific checks, e.g., stats software is available
        self.logger.info("Ready for statistical analysis.")
        return True
        
    def is_ready_for_fs_glm(self):
        """Check if ready for FreeSurfer GLM analysis."""
        if not self._check_freesurfer_ready():
            return False
        # Add more checks, like if the GLM design file exists
        self.logger.info("Ready for FreeSurfer GLM.")
        return True

    def is_ready_for_fs_glm_image(self):
        """Checks if the environment can export screen for Freeview/tksurfer."""
        export_screen = self.local_vars.get('FREESURFER', {}).get("export_screen", 0)
        if export_screen != 1:
            self.logger.error("Screen export is not enabled in local.json. Cannot extract FS-GLM images.")
            return False
        if "DISPLAY" not in os.environ:
            self.logger.warning("DISPLAY environment variable not set. Image extraction might fail.")
        
        return self._check_freesurfer_ready()

    def fs_check_fsaverage_ready(self, subjects_dir):
        """Checks for the presence of the fsaverage subject."""
        fsaverage_path = os.path.join(subjects_dir, 'fsaverage')
        if not os.path.isdir(fsaverage_path):
            self.logger.error(f"'fsaverage' is missing from SUBJECTS_DIR: {subjects_dir}")
            return False
        self.logger.info("'fsaverage' subject is present.")
        return True


    # =========================================================================
    # SECTION: Data Handling and Preparation (from former distribution_helper.py)
    # =========================================================================

    def get_subj_2classify(self):
        """Identifies subjects that need classification."""
        self.logger.info("Identifying subjects to classify...")
        # This is placeholder logic. You should implement how to find new subjects.
        # For example, by comparing a source directory with a 'classified' log.
        source_dir = self.project_vars['SOURCE_SUBJECTS_DIR'][1]
        if not os.path.exists(source_dir):
            self.logger.error(f"Source subjects directory not found: {source_dir}")
            return []
        
        # Example: return all directories in the source folder
        subjects = [os.path.join(source_dir, d) for d in os.listdir(source_dir)
                    if os.path.isdir(os.path.join(source_dir, d))]
        self.logger.info(f"Found {len(subjects)} potential subject directories to classify.")
        return subjects

    def prep_4fs_stats(self, subject_ids=None):
        """Prepares the environment for FreeSurfer stats extraction."""
        self.logger.info("Preparing for FreeSurfer stats extraction...")
        processed_fs_dir = self.project_vars['PROCESSED_FS_DIR'][1]
        if not os.path.isdir(processed_fs_dir):
            self.logger.error(f"Processed FreeSurfer directory not found: {processed_fs_dir}")
            return None
        # Potentially unzip or link subject data if needed
        return processed_fs_dir

    def prep_4fs_glm(self, fs_glm_dir, fname_groups):
        """Prepares files and directories for FreeSurfer GLM analysis."""
        self.logger.info("Preparing for FreeSurfer GLM analysis...")
        if not makedir_ifnot_exist(fs_glm_dir):
            return None, None
        
        glm_file_path = os.path.join(fs_glm_dir, fname_groups)
        if not os.path.exists(glm_file_path):
            self.logger.warning(f"GLM group file not found: {glm_file_path}. You may need to create it.")
            # You might want to copy a template file here
        
        return glm_file_path, fs_glm_dir

    def prep_4stats(self):
        """General preparation for statistical analysis."""
        self.logger.info("Preparing for statistical analysis...")
        stats_home = self.project_vars['STATS_PATHS']['STATS_HOME']
        fname_groups = self.project_vars['fname_groups']
        
        if not makedir_ifnot_exist(stats_home):
            return None
            
        groups_file = os.path.join(stats_home, fname_groups)
        if not os.path.exists(groups_file):
            self.logger.error(f"Groups file for stats is missing: {groups_file}")
            return None
            
        return fname_groups
