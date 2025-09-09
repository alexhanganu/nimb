# -*- coding: utf-8 -*-
"""
This module contains the ProjectManager class, which is responsible for
project-specific tasks like finding new data and adding it to the
processing queue.
"""

import os
import logging

from ..stats.db_processing import Table
from ..distribution.distribution_manager import DistributionManager
from ..processing.processing_manager import ProcessingManager # Import new manager
from ..distribution.utilities import load_json, save_json, makedir_ifnot_exist
from ..distribution.definitions import DEFAULT

log = logging.getLogger(__name__)

class ProjectManager:
    """
    Manages a specific project's lifecycle, from checking for new data
    to initiating processing and statistical analysis.
    """
    def __init__(self, all_vars, distribution_manager, processing_manager):
        self.all_vars = all_vars
        self.params = all_vars.params
        self.project = self.params.project
        self.project_vars = all_vars.projects[self.project]
        self.logger = all_vars.logger

        # Use the passed-in manager instances
        self.dist_manager = distribution_manager
        self.processing_manager = processing_manager

        # Key directories
        self.srcdata_dir = self.project_vars["SOURCE_SUBJECTS_DIR"][1]
        self.bids_dir = self.project_vars['SOURCE_BIDS_DIR'][1]
        
        self.logger.info(f"ProjectManager for '{self.project}' initialized.")

    def run(self):
        """
        Runs the main project pipeline based on the '-do' parameter.
        """
        do_task = self.params.do
        self.logger.info(f"Executing task: '{do_task}' for project '{self.project}'")

        if do_task == 'all':
            self.check_new_and_queue()
            # The actual processing is started with a separate command
            self.logger.info("Checked for new subjects and updated queue. "
                             "Run 'nimb -process process' to start the processing loop.")
        elif do_task == 'check-new':
            self.check_new_and_queue()
        else:
            self.logger.warning(f"Task '{do_task}' is not fully implemented in ProjectManager yet.")
            
    def check_new_and_queue(self):
        """
        Checks for new subjects in the source directory and adds them to the
        processing queue via the ProcessingManager.
        """
        self.logger.info(f"Checking for new subjects in {self.srcdata_dir}...")
        
        unprocessed_subjects = []
        try:
            # A simple comparison logic: list items in source vs. BIDS derivatives
            # This can be made more robust by checking against the processing DB.
            if not os.path.exists(self.srcdata_dir):
                self.logger.error(f"Source directory not found: {self.srcdata_dir}")
                return

            source_subjects = {d for d in os.listdir(self.srcdata_dir) 
                               if os.path.isdir(os.path.join(self.srcdata_dir, d))}
            
            bids_subjects = set()
            if os.path.exists(self.bids_dir):
                bids_subjects = {d for d in os.listdir(self.bids_dir) 
                                 if d.startswith('sub-')}
            
            # This logic assumes BIDS subjects are named 'sub-<source_subject_id>'
            processed_bids_names = {s.replace('sub-', '') for s in bids_subjects}
            
            unprocessed_subjects = list(source_subjects - processed_bids_names)
            
            if unprocessed_subjects:
                self.logger.info(f"Found {len(unprocessed_subjects)} new subjects to queue.")
                # Add these subjects to the processing queue
                self.processing_manager.add_subjects_to_queue(unprocessed_subjects)
            else:
                self.logger.info("No new subjects found.")

        except FileNotFoundError as e:
            self.logger.error(f"Directory not found while checking for new subjects: {e}")

