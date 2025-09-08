# -*- coding: utf-8 -*-

"""
This module defines all static, default values and constants used throughout
the NIMB distribution and setup processes.
"""

import os


class DEFAULT(object):
    """
    A class to hold default values for the application.
    """

    # Application and Version Information
    FREESURFER_VERSION = "7.3.2"
    CENTOS_VERSION = '7'
    NIMB_TIME_FORMAT = "%Y%m%d_%H%M"

    # Naming and Key Conventions
    ID_SOURCE_KEY = "id_source"
    ID_PROJECT_KEY = "id_project"
    ID_COL = "participant_id" # BIDS compliant default
    F_IDS = "nimb_ids.json"
    F_NIMB_CLASSIFIED = "nimb_classified.json"
    DEFAULT_TAB_NAME = "participants.tsv"
    
    # Application specifics
    APPS_PER_TYPE = {
        "anat": ["freesurfer"],
        "func": ["nilearn"],
        "dwi": ["dipy"]
    }

    APP_FILES = {
        "freesurfer": {
            "new_subjects": "new_subjects_fs.json",
            "running": "IsRunningFS_",
            "db": "db_fs.json",
            "dir_store_proc": "PROCESSED_FS_DIR",
            "fname_stats": "fs_stats",
            "name_abbrev": "fs"
        }
        # TODO: Add nilearn and dipy specific files here.
    }
    
    STATS_DIRS = {
        "STATS_HOME": "stats",
        "FS_GLM_dir": "fs_glm"
    }
    
    # Statistical and GLM Defaults
    GLM_MEASUREMENTS = "thickness,area,volume,curv"
    GLM_THRESHOLDS = "5,10,15,20,25"
    GLM_MCZ_CACHE = "13"
