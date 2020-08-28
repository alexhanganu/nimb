
# -*- coding: utf-8 -*-

"""Setup logging configuration"""

import platform
import sys
import os
import time

import logging

os.environ['TZ'] = 'US/Eastern'
time.tzset()


class Log():

    def __init__(self,
                 output_dir):


        self.output_dir = output_dir
        self.logLevel = "INFO"

        # logging setup
        self.set_logger()

        self.logger.info("--- nimb start ---")
        self.logger.info("OS:version: %s", platform.platform())
        self.logger.info("python:version: %s", sys.version.replace("\n", ""))
#        self.logger.info("nimb:version: %s", __version__)
#        self.logger.info("freesurfer:version: %s", freesurfer_version)


    def set_logger(self):
        """ Set a basic logger"""
        logFile = os.path.join(
            self.output_dir,
            "log_{}.log".format(
                          time.strftime("%Y%m%d_%H%M",time.localtime(time.time()))
                               ),
                              )

        setup_logging(self.logLevel, logFile)
        self.logger = logging.getLogger(__name__)



def setup_logging(logLevel, logFile=None):
    """ Setup logging configuration"""
    logging.basicConfig()
    logger = logging.getLogger()

    # Check level
    level = getattr(logging, logLevel.upper(), None)
    if not isinstance(level, int):
        raise ValueError("Invalid log level: {}".format(logLevel))
    logger.setLevel(level)

    # Set FileHandler
    if logFile:
        formatter = logging.Formatter(logging.BASIC_FORMAT)
        handler = logging.FileHandler(logFile)
        handler.setFormatter(formatter)
        handler.setLevel("DEBUG")
        logger.addHandler(handler)
