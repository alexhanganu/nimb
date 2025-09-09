# -*- coding: utf-8 -*-
"""
This module provides a centralized utility class, FS_Utils, for managing all
FreeSurfer-specific definitions, including pipeline stages, required files,
command generation, and common error diagnostics.
"""

import os
import logging
from os import path

log = logging.getLogger(__name__)

class FS_Utils:
    """
    A utility class containing definitions and helpers for the FreeSurfer pipeline.
    """
    def __init__(self, fs_home):
        self.fs_home = fs_home
        self.version, _, _, _ = self._get_fs_version()
        
        # Defines the entire FreeSurfer processing pipeline
        self.processes = {
            "autorecon1": {
                "directive": "autorecon1",
                "files_2chk": ['mri/nu.mgz', 'mri/orig.mgz', 'mri/brainmask.mgz'],
                "isrun_f": "IsRunning.lh+rh"
            },
            "autorecon2": {
                "directive": "autorecon2",
                "files_2chk": ['surf/lh.white', 'surf/rh.white'],
                 "isrun_f": "IsRunning.lh+rh"
            },
            "autorecon3": {
                "directive": "autorecon3",
                "files_2chk": ['stats/aseg.stats', 'stats/wmparc.stats'],
                 "isrun_f": "IsRunning.lh+rh"
            },
            "qcache": {
                "directive": "qcache",
                "files_2chk": ['surf/rh.w-g.pct.mgh', 'surf/lh.thickness.fwhm10.fsaverage.mgh'],
                 "isrun_f": "IsRunning.lh+rh"
            }
        }
        # Files that indicate a process is stuck
        self.IsRunning_files = {p["isrun_f"] for p in self.processes.values()}

    def get_command(self, stage, subject_id, t1_paths=None):
        """Generates the recon-all command for a given stage."""
        if stage == 'registration':
            if not t1_paths:
                log.error("Registration stage requires T1w image paths.")
                return None
            t1_flags = " ".join([f"-i {p}" for p in t1_paths])
            # The initial run uses -all to perform all steps
            return f"recon-all -subjid {subject_id} {t1_flags} -all"
        
        elif stage in self.processes:
            directive = self.processes[stage].get("directive")
            if directive:
                # Subsequent runs use specific directives to continue the pipeline
                return f"recon-all -subjid {subject_id} -{directive}"
        
        log.error(f"No command directive found for stage: {stage}")
        return None

    def get_error_solution(self, log_file_path):
        """
        Analyzes a recon-all log file to find a known error and suggest a command
        to fix it.
        """
        if not path.exists(log_file_path):
            return None, None

        with open(log_file_path, 'r') as f:
            log_content = f.read()

        # Add more error patterns and their solutions here
        if "ERROR: Talairach failed!" in log_content:
            log.warning("Talairach failed. Suggesting rerun with -notal-check flag.")
            return "talairach_failed", "-notal-check"
        if "cannot find or read transforms/talairach.m3z" in log_content:
            log.warning("Talairach transform missing. Suggesting rerun with -careg.")
            return "tal_m3z_missing", "-careg"
        
        return None, None

    def _get_fs_version(self):
        """Reads the FreeSurfer version from the build-stamp.txt file."""
        build_file = os.path.join(self.fs_home, "build-stamp.txt")
        if not os.path.exists(build_file):
            log.warning(f"FreeSurfer build-stamp not found at: {build_file}. Using default.")
            return "7.0.0", "unknown", "70", False
        
        with open(build_file, "r") as f:
            content = f.readline().strip().split("-")
        
        opsys, version = content[2], content[3]
        version_2numbers = version.replace(".", "")[:2]
        return version, opsys, version_2numbers, True
