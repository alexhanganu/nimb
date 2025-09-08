# -*- coding: utf-8 -*-

"""
This module provides a robust logging utility for the NIMB application.
It sets up a logger that outputs to both the console and a log file.
"""

import platform
import sys
import os
import time
import logging

try:
    from setup.version import __version__
except ImportError:
    __version__ = "unknown"

# Set time zone for consistent logging
if sys.platform != 'win32':
    os.environ['TZ'] = 'US/Eastern'
    time.tzset()


class Log:
    """
    A class to set up and manage the application's logging.
    """
    def __init__(self, output_dir, logLevel="INFO"):
        self.output_dir = output_dir
        self.logLevel = logLevel
        self.logger = self._setup_logger()

        self.logger.info("--- NIMB Logger Initialized ---")
        self.logger.info(f"OS        : {platform.platform()}")
        self.logger.info(f"Python    : {sys.version.splitlines()[0]}")
        self.logger.info(f"NIMB      : {__version__}")

    def _setup_logger(self):
        """Configures and returns a logger instance."""
        logger = logging.getLogger("NIMB")
        
        # Prevent duplicate handlers if already configured
        if logger.handlers:
            return logger
            
        level = getattr(logging, self.logLevel.upper(), logging.INFO)
        logger.setLevel(level)
        
        # Console handler
        console_formatter = logging.Formatter('%(levelname)-8s: %(message)s')
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler
        makedir_if_not_exist(self.output_dir)
        today = time.strftime("%Y%m%d")
        log_file = os.path.join(self.output_dir, f"nimb_log_{today}.log")
        
        file_formatter = logging.Formatter("%(asctime)s [%(levelname)-8s]: %(message)s", "%Y-%m-%d %H:%M:%S")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        return logger


def makedir_if_not_exist(path_list):
    """Helper to create a directory if it doesn't exist."""
    if not isinstance(path_list, list):
        path_list = [path_list]
    for p in path_list:
        if not os.path.exists(p):
            try:
                os.makedirs(p)
            except OSError as e:
                print(f"Error creating directory {p}: {e}")
                return False
    return True
