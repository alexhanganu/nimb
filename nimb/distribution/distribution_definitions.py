# -*- coding: utf-8 -*-

"""
This module defines all static, default values and constants used throughout
the NIMB distribution and setup processes.
"""

class DEFAULT(object):
    """
    A class to hold default values for the application.
    """

    # Application and Version Information
    FREESURFER_VERSION = "7.3.2"
    CENTOS_VERSION = '7'
    NIMB_TIME_FORMAT = "%Y%m%d_%H%M"

    # Processing and Scheduling Defaults
    BATCH_WALLTIME = "12:00:00"
    CLUSTER_TIME_FORMAT = "%H:%M:%S"

    # Naming and Key Conventions
    ID_SOURCE_KEY = "id_source"
    ID_PROJECT_KEY = "id_project"
    APPS_PER_TYPE = {
        "anat": "freesurfer",
        "func": "nilearn",
        "dwi": "dipy"
    }
    
    # Files and Directories
    APP_FILES = {
        "freesurfer": {
            "new_subjects": "new_subjects_fs.json",
            "db": "db_fs.json",
            "run_file": "freesurfer_runner.py",
            "dir_store_proc": "PROCESSED_FS_DIR",
            "name_abbrev": "fs"
        },
        "nilearn": {
            "new_subjects": "new_subjects_nl.json",
            "db": "db_nl.json",
            "run_file": "nilearn_runner.py",
            "dir_store_proc": "PROCESSED_NILEARN_DIR",
            "name_abbrev": "nl"
        },
        "dipy": {
            "new_subjects": "new_subjects_dp.json",
            "db": "db_dp.json",
            "run_file": "dipy_runner.py",
            "dir_store_proc": "PROCESSED_DIPY_DIR",
            "name_abbrev": "dp"
        }
    }
    
    STATS_DIRS = {
        "STATS_HOME": "stats",
        "FS_GLM_dir": "fs_glm"
    }
    
    # Statistical and GLM Defaults
    GLM_MEASUREMENTS = "thickness,area,volume,curv"
    GLM_THRESHOLDS = "5,10,15,20,25"
    GLM_MCZ_CACHE = "13"

