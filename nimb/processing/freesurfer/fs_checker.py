#!/bin/python
# 2020.10.20

import os
import shutil
import logging
import fs_definitions

log = logging.getLogger(__name__)


class FreeSurferChecker():
    def __init__(self, vars_fs, atlas_definitions, process_order):
        self.vars_fs       = vars_fs
        self.SUBJECTS_DIR  = vars_fs['FS_SUBJECTS_DIR']
        self.fsver         = vars_fs['freesurfer_version']
        self.process_order = process_order
        self.masks         = vars_fs['masks']
        self.meas          = vars_fs["GLM_measurements"]
        self.thresh        = vars_fs["GLM_thresholds"]
        self.Procs         = fs_definitions.FSProcesses(self.fsver)
        self.stats         = atlas_definitions.stats_f
        self.atlas         = atlas_definitions.atlas_data


    def IsRunning_chk(self, subjid, rm = False):
        path_2scripts_dir = os.path.join(self.SUBJECTS_DIR, subjid, 'scripts')
        res = False
        try:
            IsRunning_files = list()
            for file in self.Procs.IsRunning_files:
                file_abspath = os.path.join(path_2scripts_dir, file)
                if os.path.exists(file_abspath):
                    IsRunning_files.append(file)
                    if rm:
                        os.remove(file_abspath)
            if IsRunning_files:
                res = True
        except Exception as e:
            print(e)
            res = True
        return res


    def checks_from_runfs(self, process, subjid):
        if process == 'registration':
            return self.chksubjidinfs(subjid)
        elif process in self.Procs.recons:
            return self.chk_recon_files(process, subjid)
        elif process in self.Procs.atlas_proc:
                return self.chk_stats_f(process, subjid)
        elif process == 'masks':
            return self.chk_masks(subjid)
        # elif process == 'recon-all':
        #     return self.chk_if_recon_done(subjid)


    def chksubjidinfs(self, subjid):
        if subjid in os.listdir(self.SUBJECTS_DIR):
            return True
        else:
            return False


    def chk_recon_files(self, process, subjid):
        files_missing = list()
        for path_f in self.Procs.processes[process]["files_2chk"]:
            if not os.path.exists(os.path.join(self.SUBJECTS_DIR, subjid, path_f)):
                files_missing.append(path_f)
        if process == 'qcache':
            files_ok = fs_definitions.ChkFSQcache(self.SUBJECTS_DIR, subjid, self.vars_fs).miss
            print(f"    files missing after qcache: {files_ok}")
        if files_missing:
            log.info(f'    files are missing for {process}: {str(files_missing)}')
            return False
        else:
            return True



    def chk_stats_f(self, process, subjid):
        res = True
        if self.log_chk(process, subjid):
            for atlas in self.Procs.processes[process]["atlas_2chk"]:
                for hemi in self.atlas[atlas]["hemi"]:
                    stats_mridir = self.stats(self.fsver, atlas, _dir = "mri", hemi=hemi)
                    path_2stats_dir = os.path.join(self.SUBJECTS_DIR, subjid, "stats")
                    self.stats_f_cp_from_mri(stats_mridir, path_2stats_dir)

                    stats = self.stats(self.fsver, atlas, _dir = "stats", hemi=hemi)
                    if not os.path.exists(os.path.join(self.SUBJECTS_DIR, subjid, stats)):
                        res = False
                        break
        else:
            res = False
        return res


    def log_chk(self, process, subjid):
        log_file = os.path.join(self.SUBJECTS_DIR, subjid, self.Procs.log(process))
        if os.path.exists(log_file) and any('Everything done' in i for i in open(log_file, 'rt').readlines()):
            return True
        else:
            return False


    def chk_masks(self, subjid):
        if os.path.isdir(os.path.join(self.SUBJECTS_DIR, subjid, 'masks')):
            for structure in self.masks:
                if not os.path.exists(os.path.join(self.SUBJECTS_DIR, subjid, 
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


    def stats_f_cp_from_mri(self, src, dst):
        if os.path.exists(src):
            try:
                shutil.copy(src, dst)
                return True
            except Exception as e:
                print(e)
                return False
        else:
            return False



    # def IsRunning_rm(self, subjid):
    #     path_2scripts_dir = os.path.join(self.SUBJECTS_DIR, subjid, 'scripts')
    #     try:
    #         IsRunning_f = [i for i in self.Procs.IsRunning_files if os.path.exists(os.path.join(path_2scripts_dir, i))][0]
    #         os.remove(os.path.join(path_2scripts_dir, IsRunning_f))
    #     except Exception as e:
    #         print(e)


    # def chk_if_recon_done(self, subjid):
    #     if os.path.exists(os.path.join(self.SUBJECTS_DIR,subjid, 'mri', 'wmparc.mgz')):
    #         return True
    #     else:
    #         return False