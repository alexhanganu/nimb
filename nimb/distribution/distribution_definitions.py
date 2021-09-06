import os

class DEFAULT(object):
    """ Default values """

    default_project  = 'project1'
    project_ids      = {'loni_ppmi':{
                            "dcm2bids_config": "dcm2bids_config_loni_ppmi.json",
                            "f_source"       : "Magnetic_Resonance_Imaging.csv",
                            "proj_id_col"    : "PATNO",
                            "dir_from_source": "PPMI",
                            'date_format'    : "%Y-%m-%d_%H_%M_%S.%f",
                            'link'           : "",
                                    },
                        'loni_adni':{
                            "dcm2bids_config": "dcm2bids_config_loni_adni.json",
                            "f_source"       : "Magnetic_Resonance_Imaging.csv",
                            "proj_id_col"    : "PATNO",
                            "dir_from_source": "ADNI",
                            'date_format'    : "%Y-%m-%d_%H_%M_%S.%f",
                            'link'           : "",
                                   },
                        'nacc_ad':{
                            "dcm2bids_config": "dcm2bids_config_nacc_ad.json",
                            "f_source"       : "Magnetic_Resonance_Imaging.csv",
                            "proj_id_col"    : "NACCID",
                            "dir_from_source": "",
                            'date_format'    : "%Y-%m-%d_%H_%M_%S.%f",
                            'link'           : "https://naccdata.org/",
                                   },
                        'nacc_park':{
                            "dcm2bids_config": "dcm2bids_config_nacc_park.json",
                            "f_source"       : "Magnetic_Resonance_Imaging.csv",
                            "proj_id_col"    : "NACCID",
                            "dir_from_source": "",
                            'date_format'    : "%Y-%m-%d_%H_%M_%S.%f",
                            'link'           : "https://naccdata.org/",
                                   },
                        'cimaq':{
                            "dcm2bids_config": "dcm2bids_config_cimaq.json",
                            "f_source"       : "Magnetic_Resonance_Imaging.csv",
                            "proj_id_col"    : "ID",
                            "dir_from_source": "",
                            'date_format'    : "%Y-%m-%d_%H_%M_%S.%f",
                            'link'           : "",
                                   },
                        'radc':{
                            "dcm2bids_config": "dcm2bids_config_radc.json",
                            "f_source"       : "Magnetic_Resonance_Imaging.csv",
                            "proj_id_col"    : "ID",
                            "dir_from_source": "",
                            'date_format'    : "%Y-%m-%d_%H_%M_%S.%f",
                            'link'           : "https://www.radc.rush.edu/",
                                   },
                        'adcs':{
                            "dcm2bids_config": "dcm2bids_config_adcs.json",
                            "f_source"       : "Magnetic_Resonance_Imaging.csv",
                            "proj_id_col"    : "ID",
                            "dir_from_source": "",
                            'date_format'    : "%Y-%m-%d_%H_%M_%S.%f",
                            'link'           : "https://www.adcs.org/data-sharing/",
                                   },
                        }

    default_tab_name = 'default.csv'
    nimb_tmp_dir     = 'nimb_tmp_dir'
    BIDS_DIR_name    = 'bids'

    id_col               = "id"
    proj_id_col          = "id_proj"
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
    f_subjects2proc   = 'new_subjects.json'
    f_ids             = 'f_ids.json'
    f_running_fs      = 'running_'
    f_running_process = 'processing_running_'

    process_db_name   = "processing_db.json"
    fs_db_name        = "db.json"
    gaain_link        =  "http://www.gaain.org/"


class DEFAULTpaths:

    def __init__(self, NIMB_tmp):
        self.f_subj2process_abspath = os.path.join(NIMB_tmp, DEFAULT.f_subjects2proc)



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

def publishing_texts():

    gaain = "Data used in preparation of this article were obtained from the Global Alzheimer’s Association Interactive Network (GAAIN), funded by the Alzheimer’s Association at the Mark and Mary Stevens Neuroimaging and Informatics Institute at Keck School of Medicine of USC. The primary goal of GAAIN is to advance research into the causes and preventions and treatment of Alzheimer’s and other neurodegenerative diseases. For up-to-date information, refer to gaain.org."
    gaain_note = 'use gaain logo'