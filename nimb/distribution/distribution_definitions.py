class DEFAULT(object):
    """ Default values """
    
    project_ids      = {'loni_ppmi':{},
                           'loni_adni':{},}

    default_tab_name = 'default_table.csv'
    BIDS_DIR_name    = 'bids'


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
