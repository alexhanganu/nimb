# -*- coding: utf-8 -*-

import os
import sys
import logging

from stats.db_processing import Table
from .distribution_manager import DistributionManager
from .utilities import load_json, save_json, makedir_ifnot_exist
from .definitions import DEFAULT
from classification.classify_2nimb_bids import Classify2_NIMB_BIDS
from classification.dcm2bids_helper import DCM2BIDS_helper
# from setup.interminal_setup import get_userdefined_paths, get_yes_no

log = logging.getLogger(__name__)

class ProjectManager:
    """
    Manages a specific project's lifecycle, from checking for new data
    to initiating processing and statistical analysis.
    """
    def __init__(self, all_vars, distribution_manager):
        self.all_vars = all_vars
        self.params = all_vars.params
        self.local_vars = all_vars.location_vars['local']
        self.project = all_vars.params.project
        self.project_vars = all_vars.projects[self.project]
        self.logger = all_vars.logger

        # Use the passed-in DistributionManager instance
        self.dist_manager = distribution_manager

        self.NIMB_tmp = self.local_vars["NIMB_PATHS"]["NIMB_tmp"]
        self.srcdata_dir = self.project_vars["SOURCE_SUBJECTS_DIR"][1]
        self.BIDS_DIR = self.project_vars['SOURCE_BIDS_DIR'][1]
        
        self.f_groups = self.project_vars['fname_groups']
        self._ids_project_col = self.project_vars['id_proj_col']
        self._ids_bids_col = self.project_vars['id_col']
        self.path_stats_dir = self.project_vars["STATS_PATHS"]["STATS_HOME"]
        
        self.new_subjects = False  # Flag to indicate if new subjects are found
        self.test = all_vars.params.test

        self.logger.info(f"ProjectManager for '{self.project}' initialized.")
        # Initial setup calls would go here, e.g., loading project-specific files
        # self.read_f_ids()
        # self.get_df_f_groups()
        # self.processing_chk()

    def run(self):
        """
        Runs the main project pipeline based on the '-do' parameter.
        """
        do_task = self.params.do
        self.logger.info(f"Executing task: '{do_task}' for project '{self.project}'")

        if do_task == 'all':
            self.check_new()
            self.classify_new()
            self.process_new()
            self.run_stats()
        elif do_task == 'check-new':
            self.check_new()
        elif do_task == 'classify':
            self.classify_new()
        elif do_task == 'process':
            self.process_new()
        elif do_task == 'fs-get-stats':
            # This logic is better handled directly in nimb.py's handler
            self.logger.warning("'-do fs-get-stats' should be run via '-process fs-get-stats'")
        else:
            self.logger.warning(f"Task '{do_task}' is not fully implemented in ProjectManager yet.")

    def check_new(self):
        """
        Checks for new subjects in the source directory that haven't been processed.
        """
        self.logger.info(f"Checking for new subjects in {self.srcdata_dir}...")
        
        # This is a placeholder for your logic to find new subjects.
        # It might involve listing source directories and comparing against a
        # database or log file of processed subjects.
        
        # Example logic:
        try:
            source_subjects = set(os.listdir(self.srcdata_dir))
            # Assuming derivatives dir holds processed subjects named the same way
            processed_subjects = set(os.listdir(self.project_vars['PROCESSED_FS_DIR'][1]))
            
            unprocessed = list(source_subjects - processed_subjects)
            
            if unprocessed:
                self.logger.info(f"Found {len(unprocessed)} new subjects: {unprocessed}")
                self.new_subjects = True
            else:
                self.logger.info("No new subjects found.")
                self.new_subjects = False
        except FileNotFoundError as e:
            self.logger.error(f"Directory not found while checking for new subjects: {e}")
            self.new_subjects = False

    def classify_new(self):
        """
        Initiates classification for any new subjects found.
        """
        if not self.new_subjects:
            self.logger.info("No new subjects to classify. Checking again first.")
            self.check_new()
        
        if self.new_subjects:
            self.logger.info("Initiating classification process...")
            # This would call the classification logic, similar to _handle_classify in nimb.py
            # For example:
            # nimb_main_instance._handle_classify()
            pass # Logic is in nimb.py for now
        else:
            self.logger.info("Skipping classification as no new subjects were found.")
            
    def process_new(self):
        """
        Sends new subjects to the processing pipeline.
        """
        if not self.new_subjects:
            self.logger.info("No new subjects to process. Checking again first.")
            self.check_new()
            
        if self.new_subjects:
            self.logger.info("Sending new subjects to the processing pipeline...")
            # Here you would implement logic to prepare and submit jobs
            # to your scheduler (e.g., Slurm, tmux).
            # self.dist_manager.distribute_4_processing(...)
            pass
        else:
            self.logger.info("Skipping processing as no new subjects were found.")
            
    def run_stats(self):
        """
        Initiates the statistical analysis pipeline.
        """
        self.logger.info("Initiating statistical analysis...")
        # This would call the stats logic, similar to _handle_run_stats in nimb.py
        pass
