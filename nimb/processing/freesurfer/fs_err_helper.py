#!/bin/python
# 2020.09.24


from os import listdir, path, system, remove
import subprocess
import shutil
import datetime
import time
import logging

log = logging.getLogger(__name__)


def fs_find_error(log_file):
    error = ''
    print('                identifying THE error')
    try:
        if path.exists(log_file):
            f = open(log_file,'r').readlines()
            for line in reversed(f):
                if 'error: MRISreadCurvature:' in line:
                    log.info('                    ERROR: MRISreadCurvature')
                    error = 'Curvature'
                    break
                elif  'ERROR: MultiRegistration::loadMovables: images have different voxel sizes.' in line:
                    log.info('        ERROR: Voxel size is different, Multiregistration is not supported; consider registration with less entries')
                    error = 'voxsizediff'
                    break
                elif 'ERROR: input(s) cannot have multiple frames!' in line:
                    log.info('        ERROR: orig.mgz file has multiple frames. Cannot continue')
                    error = 'regframes'
                    break
                elif  'error: mghRead' in line:
                    log.info('        ERROR: orig bad registration, probably due to multiple -i entries, rerun with less entries')
                    error = 'origmgz'
                    break
                elif 'ERROR: Invalid FreeSurfer license key' in line:
                    log.info('        ERROR: FreeSurfer license key is missing')
                    error = 'license'
                    break
                elif 'error: ERROR: MRISread: file ../surf/lh.white has many more faces than vertices!' in line:
                    log.info('        ERROR: MRISread: file surf/lh.white has many more faces than vertices')
                    error = 'MRISread'
                    break
                elif 'ERROR: Talairach failed!' in line or 'error: transforms/talairach.m3z' in line:
                    log.info('        ERROR: Manual Talairach alignment may be necessary, or include the -notal-check flag to skip this test')
                    error = 'talfail'
                    for line in reversed(f):
                        if 'ERROR: cannot find or read transforms/talairach.m3z' in line:
                            log.info('        ERROR: cannot find or read transforms/talairach.m3z')
                            error = 'tal_m3z_miss'
                            break
                    break
                elif 'error: Numerical result out of range' in line:
                    log.info('        ERROR: umerical result out of range')
                    error = 'numrange'
                    break
                elif 'ERROR: no run data found' in line:
                    log.info('        ERROR: file has no registration')
                    error = 'noreg'
                    break
                elif 'ERROR: inputs have mismatched dimensions!' in line:
                    log.info('        ERROR: files have mismatched dimension, repeat registration will be performed')
                    error = 'regdim'
                    break
                elif 'ERROR: cannot find' in line:
                    log.info('        ERROR: cannot find files')
                    error = 'cannotfind'
                    break
                elif 'error: MRIresample():' in line:
                    log.info('        ERROR: MRIresample error')
                    error = 'MRIresample'
                    break
                elif 'error: niiRead(): unsupported datatype 128' in line:
                    log.info('        ERROR: Datatype 128. Freesurfer doesn’t support yet RGB datatype (128)')
                    error = 'niiRead128'
                    break
                elif 'Disk quota exceeded' in line:
                    log.info('        ERROR: Disk quota exceeded')
                    error = 'diskquota'
                    break
                elif 'freesurfer/bin/segmentSubject: error while loading shared libraries:' in line:
                    log.info('        ERROR: MATLAB: shared libraries cannot be opened. Try to reinstall Matlab or search for this error on freesurfer mailing list: https://www.mail-archive.com/freesurfer@nmr.mgh.harvard.edu/')
                    error = 'matlab'
                    break
                elif 'Segmentation fault (core dumped)' in line:
                    log.info('                    ERROR: Segmentation fault (core dumped)')
                    error = 'SegFault'
                    break
        else:
            log.info(f'        ERROR: {log_file} is absent')
    except FileNotFoundError as e:
        print(e)
        log.info('    {}: {}'.format(str(e)))
    return error



def solve_error(log_file, error):
    f = open(log_file,'r').readlines()
    if error == "Curvature":
        for line in reversed(f):
            if 'error: MRISreadCurvature:' in line:
                line_nr = f.index(line)
                break
        if line_nr:
            if [i for i in f[line_nr:line_nr+20] if 'Skipping this (and any remaining) curvature files' in i]:
                log.info('                        MRISreadCurvature error, but is skipped')
                return 'continue'
        else:
            return 'unsolved'
    if error == 'origmgz' or error == 'license':
        return 'repeat_reg'
    if error == 'regframes': #based on answer from: https://www.mail-archive.com/freesurfer@nmr.mgh.harvard.edu/msg69007.html
        return 'run_mri_concat_pass_orig_to_recon_all'
    if error == 'voxsizediff':
        return "rm_multi_origmgz"
    if error == 'tal_m3z_miss':
        return 'add_careg'



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
