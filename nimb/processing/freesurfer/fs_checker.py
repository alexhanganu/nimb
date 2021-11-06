#!/bin/python
# 2020.10.20

from os import listdir, path, system, remove
import shutil
import logging
import fs_definitions
# from fs_glm_prep import ChkFSQcache

log = logging.getLogger(__name__)

class FreeSurferChecker():
    def __init__(self, vars_fs, atlas_definitions):
        self.SUBJECTS_DIR  = vars_fs['FS_SUBJECTS_DIR']
        self.fsver         = vars_fs['freesurfer_version']
        self.process_order = vars_fs['process_order']
        self.masks         = vars_fs['masks']
        self.meas          = vars_fs["GLM_measurements"]
        self.thresh        = vars_fs["GLM_thresholds"]
        self.Procs         = fs_definitions.FSProcesses(self.fsver)
        self.stats         = atlas_definitions.stats_f
        self.atlas         = atlas_definitions.atlas_data
        self.file          = fs_definitions.FilePerFSVersion(self.fsver)

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
        if process == 'masks':
            return self.chk_masks(subjid)
        if process == "brstem" or process == "hip" or process == "tha" or process == "hypotha":
            for atlas in self.Procs.processes[process]["atlas_2chk"]:
                return self.chk_stats_f(atlas, subjid)

        # if process == 'brstem':
        #     return self.chkbrstemf(subjid)
        # if process == 'hip':
        #     return self.chkhipf(subjid,)
        # if process == 'tha':
        #     return self.chkthaf(subjid)

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
            # files_ok = ChkFSQcache(self.SUBJECTS_DIR, subjid, vars_fs).miss
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
        if miss:
            log.info('    files are missing: {}'.format(str(miss)))

    def log_chk(self, process, subjid):
        # log_file = path.join(self.SUBJECTS_DIR, subjid, self.Procs.log(process))
        log_file = path.join(self.SUBJECTS_DIR, subjid, self.file.log_f(process))
        if path.exists(log_file) and any('Everything done' in i for i in open(log_file, 'rt').readlines()):
            return True
        else:
            return False

    def stats_f_cp_from_mri(self, src, dst):
        if path.exists(src):
            try:
                shutil.copy(src, dst)
                return True
            except Exception as e:
                print(e)
                return False
        else:
            return False


    def chk_stats_f(self, atlas, subjid):
        res = True
        if self.log_chk(atlas, subjid):
            for hemi in self.atlas[atlas]["hemi"]:
                stats_mridir = self.stats(self.fsver, atlas, _dir = "mri", hemi=hemi)
                path_2stats_dir = os.path.join(self.SUBJECTS_DIR, subjid, "stats")
                self.stats_f_cp_from_mri(stats_mridir, path_2stats_dir)
            for hemi in self.atlas[atlas]["hemi"]:
                stats = self.stats(self.fsver, atlas, _dir = "stats", hemi=hemi)
                if not os.path.exists(os.path.join(self.SUBJECTS_DIR, subjid, stats)):
                    res = False
                    break
        else:
            res = False
        return res


    def chkbrstemf(self, subjid):        
        if self.log_chk('brstem', subjid):
            file_in_mri_dir   = path.join(self.SUBJECTS_DIR, subjid, self.file.stats_f('brstem', 'mri'))
            path_2stats_dir = os.path.join(self.SUBJECTS_DIR, subjid, "stats")
            self.stats_f_cp_from_mri(file_in_mri_dir, path_2stats_dir)
            file_in_stats_dir = path.join(self.SUBJECTS_DIR, subjid, self.file.stats_f('brstem', 'stats'))
            if path.join(file_in_stats_dir):
                return True
            else:
                return False
        else:
            return False


    def chkthaf(self, subjid):
        if self.log_chk('tha', subjid):
            path_2stats_dir = os.path.join(self.SUBJECTS_DIR, subjid, "stats")
            stats_f_inmri = path.join(self.SUBJECTS_DIR, subjid, self.file.stats_f('tha', 'mri'))
            self.stats_f_cp_from_mri(stats_f_inmri, path_2stats_dir)

            stats_f_instats = self.SUBJECTS_DIR, subjid, self.file.stats_f('tha', 'stats')
            if path.join(stats_f_instats):
                return True
            else:
                return False
        else:
            return False


    def chkhipf(self, subjid):
        res = True
        if self.log_chk('hip', subjid):
            for hemi in fs_definitions.hemi:
                for process in ['hip', 'amy']:
                    stats_f_inmri = path.join(self.SUBJECTS_DIR, subjid, self.file.stats_f(process, 'mri', hemi))
                    path_2stats_dir = os.path.join(self.SUBJECTS_DIR, subjid, "stats")
                    self.stats_f_cp_from_mri(stats_f_inmri, path_2stats_dir)

            for hemi in fs_definitions.hemi:
                for process in ['hip','amy']:
                    stats_f_instats = path.join(self.SUBJECTS_DIR, subjid, self.file.stats_f(process, 'stats', hemi))
                    if not path.exists(stats_f_instats):
                        res = False
                        break
        else:
            res = False
        return res


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
