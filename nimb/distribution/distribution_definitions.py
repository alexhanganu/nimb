import os

class DEFAULT(object):
    """ Default values """

    freesurfer_version = "7.3.2"
    centos_version     = '7'
    batch_walltime     = "12:00:00"
    cluster_time_format= "%H:%M:%S"
    nimb_time_format   = "%Y%m%d_%H%M"

    apps_per_type    = {"anat":"freesurfer",
                        "func":"nilearn",
                        "dwi" :"dipy"}

    id_source_key    = "id_source"
    id_project_key   = "id_project"
    apps_keys        = {id_source_key :"source",
                        "freesurfer"  :"freesurfer",
                        "nilearn"     :"nilearn",
                        "dipy"        :"dipy",}
    freesurfer_key   = "freesurfer"

    app_files        = {"freesurfer":{"new_subjects"  :"new_subjects_fs.json",
                                      "running"       :"IsRunningFS_",
                                      "db"            :"db_fs.json",
                                      "install_param" :"FreeSurfer_install",
                                      "run_file"      :"crun.py",
                                      "dir_nimb_proc" :"NIMB_PROCESSED_FS",
                                      "dir_store_proc":"PROCESSED_FS_DIR",
                                      "fname_stats"   :"fs_stats",
                                      "fname_st_param":"fs_stats_per_param"},
                        "nilearn"   :{"new_subjects"  :"new_subjects_nl.json",
                                      "running"       :"IsRunningNL_",
                                      "db"            :"db_nl.json",
                                      "install_param" :"nilearn_install",
                                      "run_file"      :"nl_run.py",
                                      "dir_nimb_proc" :"NIMB_PROCESSED_NILEARN",
                                      "dir_store_proc":"PROCESSED_NILEARN_DIR",
                                      "fname_stats"   :"func_stats",
                                      "fname_st_param":"func_stats_per_param"},
                        "dipy"      :{"new_subjects"  :"new_subjects_dp.json",
                                      "running"       :"IsRunningDP_",
                                      "db"            :"db_dp.json",
                                      "install_param" :"dipy_install",
                                      "run_file"      :"dp_run.py",
                                      "dir_nimb_proc" :"NIMB_PROCESSED_DIPY",
                                      "dir_store_proc":"PROCESSED_DIPY_DIR",
                                      "fname_stats"   :"diff_stats",
                                      "fname_st_param":"diff_stats_per_param"}}
    f_nimb_classified = 'nimb_classified.json'
    f_ids             = 'f_ids.json'
    f_subjects2proc   = 'new_subjects.json'
    f_running_process = 'IsRunningProcessing_'
    process_db_name   = "processing_db.json"

    default_project  = 'project1'
    project_ids      = {'loni_ppmi':{
                            "dcm2bids_config": "dcm2bids_config_loni_ppmi.json",
                            "f_source"       : "Magnetic_Resonance_Imaging.csv",
                            "proj_id_col"    : "PATNO",
                            "dir_from_source": "PPMI",
                            'date_format'    : "%Y-%m-%d_%H_%M_%S.%f",
                            'link'           : "",},
                        'loni_adni':{
                            "dcm2bids_config": "dcm2bids_config_loni_adni.json",
                            "f_source"       : "FILE_NAME.csv",
                            "proj_id_col"    : "RID",
                            "dir_from_source": "ADNI",
                            'date_format'    : "%Y-%m-%d_%H_%M_%S.%f",
                            "demographics"   : {"file" :"DXSUM_PDXCONV_ADNIALL.csv",
                                                "file_name":"Diagnostic Summary [ADNI1,GO,2,3]",
                                                "sheet":"DXSUM_PDXCONV_ADNIALL"},
                            "diagnosis"      : {"file" :"ADSXLIST.csv",
                                                "file_name":"Diagnosis and Symptoms Checklist [ADNI1,GO,2]",
                                                "sheet":"ADSXLIST"},
                            "baseline_diagnosis": {"file" :"BLCHANGE.csv",
                                                "file_name":"Diagnostic Summary - Baseline Changes [ADNI1,GO,2,3]",
                                                "sheet":"BLCHANGE"},
                            'link'           : "ida.loni.usc.edu",},
                        'nacc_ad':{
                            "dcm2bids_config": "dcm2bids_config_nacc_ad.json",
                            "f_source"       : "FILE_NAME.csv",
                            "proj_id_col"    : "NACCID",
                            "dir_from_source": "",
                            'date_format'    : "%Y-%m-%d_%H_%M_%S.%f",
                            'link'           : "https://naccdata.org/",},
                        'nacc_park':{
                            "dcm2bids_config": "dcm2bids_config_nacc_park.json",
                            "f_source"       : "FILE_NAME.csv",
                            "proj_id_col"    : "NACCID",
                            "dir_from_source": "",
                            'date_format'    : "%Y-%m-%d_%H_%M_%S.%f",
                            'link'           : "https://naccdata.org/",},
                        'cimaq':{
                            "dcm2bids_config": "dcm2bids_config_cimaq.json",
                            "f_source"       : "FILE_NAME.csv",
                            "proj_id_col"    : "ID",
                            "dir_from_source": "",
                            'date_format'    : "%Y-%m-%d_%H_%M_%S.%f",
                            'link'           : "",},
                        'radc':{
                            "dcm2bids_config": "dcm2bids_config_radc.json",
                            "f_source"       : "FILE_NAME.csv",
                            "proj_id_col"    : "ID",
                            "dir_from_source": "",
                            'date_format'    : "%Y-%m-%d_%H_%M_%S.%f",
                            'link'           : "https://www.radc.rush.edu/",},
                        'adcs':{
                            "dcm2bids_config": "dcm2bids_config_adcs.json",
                            "f_source"       : "FILE_NAME.csv",
                            "proj_id_col"    : "ID",
                            "dir_from_source": "",
                            'date_format'    : "%Y-%m-%d_%H_%M_%S.%f",
                            'link'           : "https://www.adcs.org/data-sharing/",}}

    default_tab_name = 'default.csv'
    nimb_tmp_dir     = 'nimb_tmp_dir'
    BIDS_DIR_name    = 'rawdata'

    id_col               = "id"
    proj_id_col          = "id_proj"
    group_col            = "group"
    fname_other_stats    = "stats_other"
    fname_NaNcor         = "stats_NaNcor"
    fname_eTIVcor        = "stats_eTIVcor"
    fname_Outcor         = "stats_Outcor"
    file_type            = "csv"
    fname_fs_subcort_vol = "stats_fs_subcortical"

    stats_dirs      = {
                    "FS_GLM_dir"             :'fs_glm',
                    "STATS_HOME"             :'stats',
                    "features"               :'stats/features',
                    "anova"                  :'stats/anova',
                    "simp_lin_reg_dir"       :'stats/simp_lin_reg',
                    "laterality_dir"         :'stats/laterality',
                    "predict_dir"            :'stats/prediction',
                    "logistic_regression_dir":'stats/logistic_regression',
                    "linreg_moderation_dir"  :'stats/linreg_moderation',}

    gaain_link        =  "http://www.gaain.org/"

    # below must be adjusted for app_files and removed
    fname_fs_all_stats   = "fs_all_stats"
    fname_func_all_stats = "func_all_stats"
    fname_diff_all_stats = "diff_all_stats"
    fname_fs_per_param   = "stats_fs_per_param"

    apps_all          = ('freesurfer', 'nilearn', 'dipy')
    f_new_subjects_fs = 'new_subjects_fs.json'
    f_new_subjects_nl = 'new_subjects_nl.json'
    f_new_subjects_dp = 'new_subjects_dp.json'
    f_running_fs      = 'IsRunningFS_'
    f_running_nl      = 'IsRunningNL_'
    f_running_dp      = 'IsRunningDP_'
    apps_instal_param= {"freesurfer":"FreeSurfer_install",
                        "nilearn"   :"nilearn_install",
                        "dipy"      :"dipy_install",}

class DEFAULTpaths:

    def __init__(self, NIMB_tmp):
        self.f_subj2process_abspath = os.path.join(NIMB_tmp, DEFAULT.f_subjects2proc)



def get_keys_processed(key):
    keys_all = DEFAULT.apps_keys
    print(keys_all)
    if key == 'src':
        return DEFAULT.id_source_key
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