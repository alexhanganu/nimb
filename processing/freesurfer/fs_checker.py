#!/bin/python
# 2020.09.04


from os import listdir, path, system, remove
import shutil
import logging
import fs_definitions

log = logging.getLogger(__name__)


def chkIsRunning(SUBJECTS_DIR, subjid):

    IsRunning_files = ['IsRunning.lh+rh', 'IsRunningBSsubst', 'IsRunningHPsubT1.lh+rh', 'IsRunningThalamicNuclei_mainFreeSurferT1']
    try:
        for file in IsRunning_files:
            if path.exists(path.join(SUBJECTS_DIR,subjid,'scripts',file)):
                return True
        else:
            return False
    except Exception as e:
        print(e)
        return True


def IsRunning_rm(SUBJECTS_DIR, subjid):
    IsRunning_files = ['IsRunning.lh+rh', 'IsRunningBSsubst', 'IsRunningHPsubT1.lh+rh', 'IsRunningThalamicNuclei_mainFreeSurferT1']
    try:
        remove(path.join(SUBJECTS_DIR, subjid, 'scripts', [i for i in IsRunning_files if path.exists(path.join(SUBJECTS_DIR, subjid, 'scripts', i))][0]))
    except Exception as e:
        print(e)



def checks_from_runfs(SUBJECTS_DIR, process, subjid, freesurfer_version, masks):

    if process == 'registration':
        result = chksubjidinfs(SUBJECTS_DIR, subjid)

    if process == 'autorecon1':
        result = chk_if_autorecon_done(SUBJECTS_DIR, 1, subjid)

    if process == 'autorecon2':
        result = chk_if_autorecon_done(SUBJECTS_DIR, 2, subjid)

    if process == 'autorecon3':
        result = chk_if_autorecon_done(SUBJECTS_DIR, 3, subjid)

    if process == 'recon-all':
        result = chk_if_recon_done(SUBJECTS_DIR, subjid)

    if process == 'qcache':
        result = chk_if_qcache_done(SUBJECTS_DIR, subjid)

    if process == 'brstem':
        result = chkbrstemf(SUBJECTS_DIR, subjid, freesurfer_version)

    if process == 'hip':
        result = chkhipf(SUBJECTS_DIR, subjid, freesurfer_version)

    if process == 'tha':
        result = chkthaf(SUBJECTS_DIR, subjid, freesurfer_version)

    if process == 'masks':
        result = chk_masks(SUBJECTS_DIR, subjid, masks)

    return result



def chk_if_all_done(SUBJECTS_DIR, subjid, process_order, NIMB_tmp, freesurfer_version, masks):
        result = True
        if not chkIsRunning(SUBJECTS_DIR, subjid):
            for process in process_order[1:]:
                if not checks_from_runfs(SUBJECTS_DIR, process, subjid, freesurfer_version, masks):
                    log.info('        '+subjid+' is missing '+process)
                    result = False
                    break
        else:
            log.info('            IsRunning file present ')
            result = False
        return result



def chksubjidinfs(SUBJECTS_DIR, subjid):

    lsallsubjid=listdir(SUBJECTS_DIR)

    if subjid in lsallsubjid:
        return True

    else:
        return False




def chk_if_autorecon_done(SUBJECTS_DIR, lvl, subjid):
    f_autorecon = {1:['mri/nu.mgz','mri/orig.mgz','mri/brainmask.mgz',],
                2:['stats/lh.curv.stats','stats/rh.curv.stats',],
                3:['stats/aseg.stats','stats/wmparc.stats',]}
    for path_f in f_autorecon[lvl]:
            if not path.exists(path.join(SUBJECTS_DIR, subjid, path_f)):
                return False
                break
            else:
                return True


def chk_if_recon_done(SUBJECTS_DIR, subjid):

    '''must check for all files: https://surfer.nmr.mgh.harvard.edu/fswiki/ReconAllDevTable
    '''
    if path.exists(path.join(SUBJECTS_DIR,subjid, 'mri', 'wmparc.mgz')):
        return True
    else:
        return False


def chk_if_qcache_done(SUBJECTS_DIR, subjid):

    if 'rh.w-g.pct.mgh.fsaverage.mgh' and 'lh.thickness.fwhm10.fsaverage.mgh' in listdir(path.join(SUBJECTS_DIR, subjid, 'surf')):
        return True
    else:
        return False


def bs_hip_tha_chk_log_if_done(process, SUBJECTS_DIR, subjid, freesurfer_version):
    log_file = path.join(SUBJECTS_DIR, subjid, 'scripts', fs_definitions.log_files[process][freesurfer_version])
    if path.exists(log_file) and any('Everything done' in i for i in open(log_file, 'rt').readlines()):
        return True
    else:
        return False


def bs_hip_tha_get_stats_file(process, SUBJECTS_DIR, subjid, freesurfer_version):
    lsmri = listdir(path.join(SUBJECTS_DIR, subjid, 'mri'))
    file_stats = path.join(SUBJECTS_DIR, subjid, 'mri', fs_definitions.bs_hip_tha_stats_file_inmri[process][freesurfer_version])
    if path.exists(file_stats):
        try:
            shutil.copy(path.join(SUBJECTS_DIR, subjid, 'mri', file_stats),
                        path.join(SUBJECTS_DIR, subjid, 'stats', fs_definitions.bs_hip_tha_stats_file_instats[process][freesurfer_version]))
        except Exception as e:
            print(e)
        return file_stats
    else:
        return ''


def chkbrstemf(SUBJECTS_DIR, subjid, freesurfer_version):
    if bs_hip_tha_chk_log_if_done('bs', SUBJECTS_DIR, subjid, freesurfer_version):
        file_stats = bs_hip_tha_get_stats_file('bs', SUBJECTS_DIR, subjid, freesurfer_version)
        if file_stats:
            return True
        else:
            return False
    else:
        return False


def chkhipf(SUBJECTS_DIR, subjid, freesurfer_version):
    if bs_hip_tha_chk_log_if_done('hip', SUBJECTS_DIR, subjid, freesurfer_version):
        if path.exists(path.join(SUBJECTS_DIR, subjid, 'mri', fs_definitions.bs_hip_tha_stats_file_inmri['hipR'][freesurfer_version])):
            for file in ['hipL', 'hipR', 'amyL', 'amyR']:
                file_stats = bs_hip_tha_get_stats_file(file, SUBJECTS_DIR, subjid, freesurfer_version)
            return True
        else:
            return False
    else:
        return False


def chkthaf(SUBJECTS_DIR, subjid, freesurfer_version):
    if bs_hip_tha_chk_log_if_done('tha', SUBJECTS_DIR, subjid, freesurfer_version):
        file_stats = bs_hip_tha_get_stats_file('tha', SUBJECTS_DIR, subjid, freesurfer_version)
        if file_stats:
            return True
        else:
            return False
    else:
        return False


def chk_masks(SUBJECTS_DIR, subjid, masks):

    if path.isdir(path.join(SUBJECTS_DIR,subjid,'masks')):
        for structure in masks:
            if structure+'.nii' not in listdir(path.join(SUBJECTS_DIR,subjid,'masks')):
                return False
            else:
                return True
    else:
        return False


def chkreconf_if_without_error(NIMB_tmp, subjid, SUBJECTS_DIR):

    file_2read = 'recon-all-status.log'
    try:
        if file_2read in listdir(path.join(SUBJECTS_DIR,subjid,'scripts')):
            f = open(path.join(SUBJECTS_DIR,subjid,'scripts',file_2read),'r').readlines()

            for line in reversed(f):
                if 'finished without error' in line:
                    return True
                    break
                elif 'exited with ERRORS' in line:
                    log.info('        exited with ERRORS')
                    return False
                    break
                elif 'recon-all -s' in line:
                    return False
                    break
                else:
                    log.info('        not clear if finished with or without ERROR')
                    return False
                    break
        else:
            return False
    except FileNotFoundError as e:
        print(e)
        log.info('    '+subjid+' '+str(e))
