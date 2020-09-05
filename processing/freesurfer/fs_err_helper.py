#!/bin/python
# 2020.09.24


from os import listdir, path, system, remove
import subprocess
import shutil
import datetime
import time
import logging

log = logging.getLogger(__name__)


def fs_find_error(subjid, SUBJECTS_DIR, NIMB_tmp):
    error = ''
    print('                identifying THE error')
    file_2read = path.join(SUBJECTS_DIR,subjid,'scripts','recon-all.log')
    try:
        if path.exists(file_2read):
            f = open(file_2read,'r').readlines()
            for line in reversed(f):
                if  'ERROR: MultiRegistration::loadMovables: images have different voxel sizes.' in line:
                    log.info('        ERROR: Voxel size is different, Multiregistration is not supported; consider registration with less entries')
                    error = 'voxsizediff'
                    break
                elif  'error: mghRead' in line:
                    log.info('        ERROR: orig bad registration, probably due to multiple -i entries, rerun with less entries')
                    error = 'errorigmgz'
                    break
                elif 'error: MRISreadCurvature:' in line:
                    log.info('                    ERROR: MRISreadCurvature')
                    error = 'errCurvature'
                    break
                if 'ERROR: Talairach failed!' in line or 'error: transforms/talairach.m3z' in line:
                    log.info('        ERROR: Manual Talairach alignment may be necessary, or include the -notal-check flag to skip this test')
                    error = 'talfail'
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
                    error = 'errMRIresample'
                    break
                elif 'Disk quota exceeded' in line:
                    log.info('        ERROR: Disk quota exceeded')
                    error = 'errdiskquota'
                    break
                elif 'ERROR: Invalid FreeSurfer license key' in line:
                    log.info('        ERROR: FreeSurfer license key is missing')
                    error = 'errlicense'
                    break
        else:
            log.info('        ERROR: '+file_2read+' not in '+path.join(SUBJECTS_DIR,subjid,'scripts'))
    except FileNotFoundError as e:
        print(e)
        log.info('    '+subjid+' '+str(e))
    return error



def solve_error(subjid, error, SUBJECTS_DIR, NIMB_tmp):
    file_2read = path.join(SUBJECTS_DIR,subjid,'scripts','recon-all.log')
    f = open(file_2read,'r').readlines()
    if error == "errCurvature":
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
    if error == 'voxsizediff' or error == 'errorigmgz' or error == 'errlicense':
        return 'repeat_reg'

