class DEFAULT(object):
    """ Default values """

    default_project  = 'project1'
    project_ids      = {'loni_ppmi':{
                            "dcm2bids_config": "dcm2bids_config_ppmi.json",
                            "f_source"       : "Magnetic_Resonance_Imaging.csv",
                            "id_col"         : "PATNO",
                            "dir_from_source": "PPMI",
                            'date_format'    : "%Y-%m-%d_%H_%M_%S.%f",
                                    },
                        'loni_adni':{
                            "dcm2bids_config": "dcm2bids_config_adni.json",
                            "f_source"       : "Magnetic_Resonance_Imaging.csv",
                            "id_col"         : "PATNO",
                            "dir_from_source": "ADNI",
                            'date_format'    : "%Y-%m-%d_%H_%M_%S.%f",
                                   },
                        }

    default_tab_name = 'default.csv'
    BIDS_DIR_name    = 'bids'

    group_col            = "group"
    fname_fs_all_stats   = "fs_all_stats"
    fname_func_all_stats = "func_all_stats"
    fname_other_stats    = "stats_other"

    stats_dirs      = {
                    "FS_GLM_dir"             :'fs_glm',
                    "STATS_HOME"             :'stats',
                    "features"               :'stats/features',
                    "anova"                  :'stats/anova',
                    "simp_lin_reg_dir"       :'stats/simp_lin_reg_dir',
                    "laterality_dir"         :'stats/laterality_dir',
                    "predict_dir"            :'stats/predict_dir',
                    "logistic_regression_dir":'stats/logistic_regression_dir',
                    "linreg_moderation_dir"  :'stats/linreg_moderation_dir',
                        }
    f_nimb_classified = 'nimb_classified.json'
    f_subjects2proc   = 'new_subjects.json'
    f_ids             = 'f_ids.json'
    f_running_fs      = 'running_'
    f_running_process = 'processing_running_'

    process_db_name   = "processing_db.json"
    fs_db_name        = "db.json"



def get_keys_processed(key):
    if key == 'src':
        return 'source'
    elif key == 'fs':
        return 'freesurfer'
    elif key == 'nilearn':
        return 'nilearn'
    elif key == 'dipy':
        return 'dipy'
    else:
        return 'none'
