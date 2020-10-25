#!/bin/python
# 2020.10.20

from os import listdir, path, system, remove
import shutil
import logging
import fs_definitions

log = logging.getLogger(__name__)

class FreeSurferChecker():
    def __init__(self, vars_fs):
        self.SUBJECTS_DIR       = vars_fs['FS_SUBJECTS_DIR']
        self.freesurfer_version = vars_fs['freesurfer_version']
        self.process_order      = vars_fs['process_order']
        self.masks              = vars_fs['masks']
        self.meas               = vars_fs["GLM_measurements"]
        self.thresh             = vars_fs["GLM_thresholds"]
        self.file               = fs_definitions.FilePerFSVersion(vars_fs['freesurfer_version'])

    def IsRunning_chk(self, subjid):
        try:
            for file in fs_definitions.IsRunning_files:
                if path.exists(path.join(self.SUBJECTS_DIR, subjid, 'scripts', file)):
                    return True
            else:
                return False
        except Exception as e:
            print(e)
            return True

    def IsRunning_rm(self, subjid):
        try:
            IsRunning_f = [i for i in fs_definitions.IsRunning_files if path.exists(path.join(self.SUBJECTS_DIR, subjid, 'scripts', i))][0]
            remove(path.join(self.SUBJECTS_DIR, subjid, 'scripts', IsRunning_f))
        except Exception as e:
            print(e)

    def checks_from_runfs(self, process, subjid):
        if process == 'registration':
            return self.chksubjidinfs(subjid)
        if process == 'recon-all':
            return self.chk_if_recon_done(subjid)
        if process == 'autorecon1':
            return self.chk_if_autorecon_done(1, subjid)
        if process == 'autorecon2':
            return self.chk_if_autorecon_done(2, subjid)
        if process == 'autorecon3':
            return self.chk_if_autorecon_done(3, subjid)
        if process == 'qcache':
            return self.chk_if_qcache_done(subjid)
        if process == 'brstem':
            return self.chkbrstemf(subjid)
        if process == 'hip':
            return self.chkhipf(subjid,)
        if process == 'tha':
            return self.chkthaf(subjid)
        if process == 'masks':
            return self.chk_masks(subjid)

    def chksubjidinfs(self, subjid):
        if subjid in listdir(self.SUBJECTS_DIR):
            return True
        else:
            return False

    def chk_process_files(self, process):
        files_missing = list()
        for path_f in fs_definitions.files_created[process]:
            if not path.exists(path.join(self.SUBJECTS_DIR, subjid, path_f)):
                files_missing.append(path_f)
        if files_missing:
            log.info('    files are missing for {}: {}'.format(process, str(files_missing)))
            return False
        else:
            return True

    def chk_if_recon_done(self, subjid): # move to chk_process_files
        if path.exists(path.join(self.SUBJECTS_DIR,subjid, 'mri', 'wmparc.mgz')):
            return True
        else:
            return False
    def chk_if_autorecon_done(self, lvl, subjid): # move to chk_process_files
        for path_f in fs_definitions.f_autorecon[lvl]:
                if not path.exists(path.join(self.SUBJECTS_DIR, subjid, path_f)):
                    return False
                    break
                else:
                    return True
    def chk_if_qcache_done(self, subjid): # move to chk_process_files
        if 'rh.w-g.pct.mgh.fsaverage.mgh' and 'lh.thickness.fwhm10.fsaverage.mgh' in listdir(path.join(self.SUBJECTS_DIR, subjid, 'surf')):
            self.check_qcache_files(subjid)
            return True
        else:
            return False
    def check_qcache_files(self, subjid):
            miss = list()
            for hemi in fs_definitions.hemi:
                for meas in self.meas:
                    for thresh in self.thresh:
                        file = hemi+'.'+meas+'.fwhm'+str(thresh)+'.fsaverage.mgh'
                        if not path.exists(path.join(self.SUBJECTS_DIR, subjid, 'surf', file)):
                            miss.append(file)
            if not miss:
                return True
            else:
                log.info('    files are missing: {}'.format(str(miss)))
                return False

    def log_chk(self, process, subjid):
        log_file = path.join(self.SUBJECTS_DIR, subjid, 'scripts', fs_definitions.log_files[process][self.freesurfer_version])
        if path.exists(log_file) and any('Everything done' in i for i in open(log_file, 'rt').readlines()):
            return True
        else:
            return False

    def stats_f_cp_from_mri(self, src, dst):
        if path.exists(src):
            try:
                shutil.copy(src,dst)
                return True
            except Exception as e:
                print(e)
                return False
        else:
            return False

    def chkbrstemf(self, subjid):
        if self.log_chk('bs', subjid):
            self.stats_f_cp_from_mri(path.join(self.SUBJECTS_DIR, subjid, self.file.stats_f('bs', 'mri')), path.join(self.SUBJECTS_DIR, subjid, self.file.stats_f('bs', 'stats')))
            if path.join(self.SUBJECTS_DIR, subjid, self.file.stats_f('bs', 'stats')):
                return True
            else:
                return False
        else:
            return False

    def chkhipf(self, subjid):
        res = True
        if self.log_chk('hip', subjid):
            for hemi in fs_definitions.hemi:
                for process in ['hip','amy']:
                    stats_f_inmri = path.join(self.SUBJECTS_DIR, subjid, self.file.stats_f(process, 'mri', hemi))
                    stats_f_instats = path.join(self.SUBJECTS_DIR, subjid, self.file.stats_f(process, 'stats', hemi))
                    self.stats_f_cp_from_mri(stats_f_inmri, stats_f_instats)
            for hemi in fs_definitions.hemi:
                for process in ['hip','amy']:
                    if not path.exists(self.SUBJECTS_DIR, subjid, self.file.stats_f(process, 'stats', hemi))
                        res = False
                        break
        else:
            res = False
        return res

    def chkthaf(self, subjid):
        if self.log_chk('tha', subjid):
            self.stats_f_cp_from_mri(path.join(self.SUBJECTS_DIR, subjid, self.file.stats_f('tha', 'mri')), path.join(self.SUBJECTS_DIR, subjid, self.file.stats_f('tha', 'stats')))            
            if path.join(self.SUBJECTS_DIR, subjid, self.file.stats_f('tha', 'stats')):
                return True
            else:
                return False
        else:
            return False

    def chk_masks(self, subjid):
        if path.isdir(path.join(self.SUBJECTS_DIR, subjid, 'masks')):
            for structure in self.masks:
                if not path.exists(path.join(self.SUBJECTS_DIR, subjid, 
                                            'masks', '{}.nii'.format(structure))):
                    return False
                else:
                    return True
        else:
            return False

    def chk_if_all_done(self, subjid):
            result = True
            if not self.IsRunning_chk(subjid):
                for process in self.process_order[1:]:
                    if not self.checks_from_runfs(process, subjid):
                        log.info('        {} is missing {}'.format(subjid, process))
                        result = False
                        break
            else:
                log.info('            IsRunning file present ')
                result = False
            return result



"""
2RM
def chkIsRunning(SUBJECTS_DIR, subjid):
    try:
        for file in fs_definitions.IsRunning_files:
            if path.exists(path.join(SUBJECTS_DIR,subjid,'scripts',file)):
                return True
        else:
            return False
    except Exception as e:
        print(e)
        return True


def IsRunning_rm(SUBJECTS_DIR, subjid):
    try:
        remove(path.join(SUBJECTS_DIR, subjid, 'scripts', [i for i in fs_definitions.IsRunning_files if path.exists(path.join(SUBJECTS_DIR, subjid, 'scripts', i))][0]))
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

def chksubjidinfs(SUBJECTS_DIR, subjid):

    lsallsubjid=listdir(SUBJECTS_DIR)

    if subjid in lsallsubjid:
        return True

    else:
        return False


# == move to chk_process_files
def chk_if_autorecon_done(SUBJECTS_DIR, lvl, subjid):
    for path_f in fs_definitions.f_autorecon[lvl]:
            if not path.exists(path.join(SUBJECTS_DIR, subjid, path_f)):
                return False
                break
            else:
                return True
def chk_if_recon_done(SUBJECTS_DIR, subjid):

    if path.exists(path.join(SUBJECTS_DIR,subjid, 'mri', 'wmparc.mgz')):
        return True
    else:
        return False
def chk_if_qcache_done(SUBJECTS_DIR, subjid):

    if 'rh.w-g.pct.mgh.fsaverage.mgh' and 'lh.thickness.fwhm10.fsaverage.mgh' in listdir(path.join(SUBJECTS_DIR, subjid, 'surf')):
        return True
    else:
        return False
# == up to here

def check_qcache_files(SUBJECTS_DIR, subjid, vars_fs):

        res = True
        miss = list()
        for hemi in ['lh','rh']:
            for meas in vars_fs["GLM_measurements"]:
                for thresh in vars_fs["GLM_thresholds"]:
                    file = hemi+'.'+meas+'.fwhm'+str(thresh)+'.fsaverage.mgh'
                    if not path.exists(path.join(SUBJECTS_DIR, subjid, 'surf', file)):
                        miss.append(file)
        if miss:
            print('some subjects or files are missing: {}'.format(str(miss)))
            res = False
        return res


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
"""