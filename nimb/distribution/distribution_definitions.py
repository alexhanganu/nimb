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
    nimb_tmp_dir     = 'nimb_tmp_dir'
    BIDS_DIR_name    = 'bids'

    group_col            = "group"
    fname_fs_all_stats   = "fs_all_stats"
    fname_func_all_stats = "func_all_stats"
    fname_diff_all_stats = "diff_all_stats"
    fname_other_stats    = "stats_other"
    fname_fs_per_param   = "stats_fs_per_param"
    fname_fs_subcort_vol = "stats_fs_subcortical"
    fname_NaNcor         = "stats_NaNcor"
    fname_eTIVcor        = "stats_eTIVcor"
    fname_Outcor         = "stats_Outcor"
    file_type            = "csv"


    stats_dirs      = {
                    "FS_GLM_dir"             :'fs_glm',
                    "STATS_HOME"             :'stats',
                    "features"               :'stats/features',
                    "anova"                  :'stats/anova',
                    "simp_lin_reg_dir"       :'stats/simp_lin_reg',
                    "laterality_dir"         :'stats/laterality',
                    "predict_dir"            :'stats/prediction',
                    "logistic_regression_dir":'stats/logistic_regression',
                    "linreg_moderation_dir"  :'stats/linreg_moderation',
                        }
    f_nimb_classified = 'nimb_classified.json'
    f_nimb_classified_archive = 'nimb_classified_archive.json'
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
'''
fname_NaNcor: file-name after correcting for NaNs or missing values
fname_eTIVcor: file-name after correcting for eTIV
fname_Outcor: file-name after correcting for outliers

'''