ids_processed = ('src', 'fs', 'freesurfer', 'nilearn', 'dipy')

def get_ids_processed(key):
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
