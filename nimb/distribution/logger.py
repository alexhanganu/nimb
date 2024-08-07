
# -*- coding: utf-8 -*-

"""Setup logging configuration"""

import platform
import sys
import os
import time

import logging

from setup.version import __version__

os.environ['TZ'] = 'US/Eastern'
if sys.platform == 'win32':
    pass
else:
    time.tzset()


class Log():

    def __init__(self,
                 output_dir):


        self.output_dir = output_dir
        self.logLevel = "INFO"

        # logging setup
        self.set_logger()

        self.logger.info("--- nimb start ---")
        self.logger.info("OS        : {}".format(platform.platform()))
        self.logger.info("python    : {}".format(sys.version.replace("\n", "")))
        self.logger.info("nimb      : {}".format(__version__))


    def set_logger(self):
        """ Set a basic logger"""
        today = time.strftime("%Y%m%d",time.localtime(time.time()))
        logFile = os.path.join(
            self.output_dir,
            "log_{}.log".format(
                          today
                               ),
                              )

        setup_logging(self.logLevel, logFile)
        self.logger = logging.getLogger(__name__)


def setup_logging(logLevel, logFile=None):
    """ Setup logging configuration"""
#    logging.basicConfig(format='%(asctime)s %(module)s %(levelname)s: %(message)s')
    logging.basicConfig(format='{asctime} : {message}')
    logger = logging.getLogger()

    # Check level
    level = getattr(logging, logLevel.upper(), None)
    if not isinstance(level, int):
        raise ValueError("Invalid log level: {}".format(logLevel))
    logger.setLevel(level)

    # Set FileHandler
    if logFile:
        formatter = logging.Formatter("%(asctime)s : %(message)s",
                              "%Y-%m-%d %H:%M:%S")
        handler = logging.FileHandler(logFile)
        handler.setFormatter(formatter)
        handler.setLevel("DEBUG")
        logger.addHandler(handler)


class LogLVL:

    lvl0 = " " * 1
    lvl1 = " " * 4
    lvl2 = " " * 8
    lvl3 = " " * 12
    lvl4 = " " * 15