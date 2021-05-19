class DEFAULT(object):
    """ Default values """

    default_project  = 'project1'
    project_ids      = {'loni_ppmi':{
                            "dcm2bids_config":'dcm2bids_config_ppmi.json',
                            "f_source"       : "Magnetic_Resonance_Imaging.csv",
                            "id_col"         : "PATNO"
                                    }#,
                           # 'loni_adni':{
                           #         },
                        }

    default_tab_name = 'default.csv'
    BIDS_DIR_name    = 'bids'

    group_col            = "group"
    fname_fs_all_stats   = "fs_all_stats"
    fname_func_all_stats = "func_all_stats"
    fname_other_stats    = "stats_other"


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
