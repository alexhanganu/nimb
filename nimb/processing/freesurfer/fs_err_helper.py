#!/bin/python
# 2020.09.24


from os import listdir, path, system, remove
import subprocess
import shutil
import datetime
import time
import logging

log = logging.getLogger(__name__)


import fs_checker
class ErrorCheck():
    def __init__(self, vars_freesurfer):
        self.vars_freesurfer = vars_freesurfer

    def check_error(self, db, scheduler_jobs, process):
        log.info('ERROR checking')

        if db['PROCESSED']['error_'+process]:
            lserr = db['PROCESSED']['error_'+process].copy()
            for subjid in lserr:
                log.info('    '+subjid)
                if subjid not in db["ERROR_QUEUE"] and path.exists(path.join(SUBJECTS_DIR, subjid)): #path.exists was added due to moving the subjects too early; requires adjustment
                    fs_checker.IsRunning_rm(SUBJECTS_DIR, subjid)
                    log.info('        checking the recon-all-status.log for error for: '+process)
                    fs_checker.chkreconf_if_without_error(NIMB_tmp, subjid, SUBJECTS_DIR)
                    log.info('        checking if all files were created for: '+process)
                    if not fs_checker.checks_from_runfs(SUBJECTS_DIR, process, subjid, vars_local["FREESURFER"]["freesurfer_version"], vars_local["FREESURFER"]["masks"]):
                            log.info('            some files were not created and recon-all-status has errors.')
                            fs_error = fs_err_helper.fs_find_error(subjid, SUBJECTS_DIR, NIMB_tmp, process)
                            solved = False
                            if fs_error:
                                solve = fs_err_helper.solve_error(subjid, fs_error, SUBJECTS_DIR, NIMB_tmp)
                                if solve == 'continue':
                                    solved = True
                                    db['PROCESSED']['error_'+process].remove(subjid)
                                    db['DO'][process].append(subjid)
                                    log.info('        moving from error_'+process+' to DO '+process)
                                elif solve == 'repeat_reg':
                                    if subjid in db['REGISTRATION']:
                                        solved = True
                                        db['REGISTRATION'][subjid]['anat']['t1'] = db['REGISTRATION'][subjid]['anat']['t1'][:1]
                                        if 'flair' in db['REGISTRATION'][subjid]['anat']:
                                                db['REGISTRATION'][subjid]['anat'].pop('flair', None)
                                        if 't2' in db['REGISTRATION'][subjid]['anat']:
                                                db['REGISTRATION'][subjid]['anat'].pop('t2', None)
                                        db['PROCESSED']['error_'+process].remove(subjid)
                                        db['DO']["registration"].append(subjid)
                                        log.info('              removing '+subjid+' from '+SUBJECTS_DIR)
                                        system('rm -r '+path.join(SUBJECTS_DIR, subjid))
                                        log.info('        moving from error_'+process+' to RUNNING registration')
                                    else:
                                        new_name = 'error_noreg_'+subjid
                                        log.info('            solved: '+solve+' but subjid is missing from db[REGISTRATION]')
                                else:
                                    new_name = 'error_'+fs_error+'_'+subjid
                                    log.info('            not solved')
                            else:
                                new_name = 'error_'+process+'_'+subjid
                            if not solved:
                                log.info('            Excluding '+subjid+' from pipeline')
                                _id, _ = cdb.get_id_long(subjid, db['LONG_DIRS'], vars_local["FREESURFER"]["base_name"], vars_local["FREESURFER"]["long_name"])
                                if _id != 'none':
                                    try:
                                        db['LONG_DIRS'][_id].remove(subjid)
                                        db['LONG_TPS'][_id].remove(subjid.replace(_id+'_',''))
                                        if len(db['LONG_DIRS'][_id])==0:
                                            db['LONG_DIRS'].pop(_id, None)
                                            db['LONG_TPS'].pop(_id, None)
                                        if subjid in db['REGISTRATION']:
                                            db['REGISTRATION'].pop(subjid, None)
                                        else:
                                            log.info('        missing from db[REGISTRATION]')
                                    except Exception as e:
                                        log.info('        ERROR, id not found in LONG_DIRS; '+str(e))
                                else:
                                    log.info('        ERROR, '+subjid+' is absent from LONG_DIRS')
                                move_processed_subjects(subjid, 'error_'+process, new_name)
                    else:
                            log.info('            all files were created for process: '+process)
                            db['PROCESSED']['error_'+process].remove(subjid)
                            db['RUNNING'][process].append(subjid)
                            log.info('        moving from error_'+process+' to RUNNING '+process)
                else:
                    if subjid in db["ERROR_QUEUE"]:
                        db = self.error_queue_check(db, subjid, scheduler_jobs)
                    elif not fs_checker.chkIsRunning(SUBJECTS_DIR, subjid) or db['ERROR_QUEUE'][subjid] < str(format(datetime.now(), "%Y%m%d_%H%M")):
                            log.info('    removing from ERROR_QUEUE')
                            db['ERROR_QUEUE'].pop(subjid, None)
                    else:
                        log.info('    not in SUBJECTS_DIR')
                        db['PROCESSED']['error_'+process].remove(subjid)
                db['PROCESSED']['error_'+process].sort()
                cdb.Update_DB(db, NIMB_tmp)
    def error_queue_check(self, db, subjid, scheduler_jobs):
        db['RUNNING_JOBS'], status = Get_status_for_subjid_in_queue(db['RUNNING_JOBS'], subjid, scheduler_jobs)
        log.info('     waiting until: '+db['ERROR_QUEUE'][subjid])
        if status != 'none' and subjid in db['RUNNING_JOBS']:
            log.info('     status is: {}, should be moving back to RUNNING_JOBS'.format(status))
            db['ERROR_QUEUE'].pop(subjid, None)
            db['PROCESSED']['error_'+process].remove(subjid)
            db['RUNNING'][process].append(subjid)
        return db




def fs_find_error(subjid, SUBJECTS_DIR, NIMB_tmp, process, log_file):
    error = ''
    print('                identifying THE error')
    try:
        if path.exists(log_file):
            f = open(log_file,'r').readlines()
            for line in reversed(f):
                if  'ERROR: MultiRegistration::loadMovables: images have different voxel sizes.' in line:
                    log.info('        ERROR: Voxel size is different, Multiregistration is not supported; consider registration with less entries')
                    error = 'voxsizediff'
                    break
                elif  'error: mghRead' in line:
                    log.info('        ERROR: orig bad registration, probably due to multiple -i entries, rerun with less entries')
                    error = 'origmgz'
                    break
                elif 'error: ERROR: MRISread: file ../surf/lh.white has many more faces than vertices!' in line:
                    log.info('        ERROR: MRISread: file surf/lh.white has many more faces than vertices')
                    error = 'MRISread'
                    break
                elif 'error: MRISreadCurvature:' in line:
                    log.info('                    ERROR: MRISreadCurvature')
                    error = 'Curvature'
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
                elif 'ERROR: input(s) cannot have multiple frames!' in line:
                    log.info('        ERROR: orig.mgz file has multiple frames. Cannot continue')
                    error = 'regframes'
                    break
                elif 'ERROR: cannot find' in line:
                    log.info('        ERROR: cannot find files')
                    error = 'cannotfind'
                    break
                elif 'error: MRIresample():' in line:
                    log.info('        ERROR: MRIresample error')
                    error = 'MRIresample'
                    break
                elif 'Disk quota exceeded' in line:
                    log.info('        ERROR: Disk quota exceeded')
                    error = 'diskquota'
                    break
                elif 'ERROR: Invalid FreeSurfer license key' in line:
                    log.info('        ERROR: FreeSurfer license key is missing')
                    error = 'license'
                    break
                elif 'freesurfer/bin/segmentSubject: error while loading shared libraries:' in line:
                    log.info('        ERROR: MATLAB: shared libraries cannot be opened. Try to reinstall Matlab or search for this error on freesurfer mailing list: https://www.mail-archive.com/freesurfer@nmr.mgh.harvard.edu/')
                    error = 'matlab'
                    break
        else:
            log.info('        ERROR: {} not in {}'.format(log_file, path.join(SUBJECTS_DIR, subjid, 'scripts')))
    except FileNotFoundError as e:
        print(e)
        log.info('    {}: {}'.format(subjid, str(e)))
    return error



def solve_error(subjid, error, SUBJECTS_DIR, NIMB_tmp):
    log_file = path.join(SUBJECTS_DIR, subjid, files.log_f('recon'))
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
    if error == 'voxsizediff' or error == 'origmgz' or error == 'license':
        return 'repeat_reg'



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
