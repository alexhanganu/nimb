#!/bin/python
# 2020.10.20

import os
import shutil
import logging

from processing.freesurfer import fs_definitions
log = logging.getLogger(__name__)


class CHECKER():
    def __init__(self, atlas_definitions):
        self.stats = atlas_definitions.stats_f
        self.atlas = atlas_definitions.atlas_data


    def chk(self, subjid, app, app_vars, stage, rm = False):
        self.app          = app
        self.app_vars     = app_vars
        self.SUBJECTS_DIR = app_vars['SUBJECTS_DIR']
        self.app_ver      = app_vars[f"{app}_version"]
        self.proc_order   = app_vars["process_order"]

        if app == 'freesurfer':
            FSProcs = fs_definitions.FSProcesses(self.app_ver)
            if stage == 'isrunning':
                isrunnings    = FSProcs.IsRunning_files
                path_2scripts = os.path.join(self.SUBJECTS_DIR, subjid, 'scripts')
                return self.IsRunning_chk(subjid, isrunnings, path_2scripts, rm)
            elif stage == 'registration':
                return os.path.exists(os.path.join(self.SUBJECTS_DIR, subjid))
            elif stage in FSProcs.recons:
                files2chk = FSProcs.processes[stage]["files_2chk"]
                return self.fs_chk_recon_files(stage, subjid, files2chk)
            elif stage in FSProcs.atlas_proc:
                atlas2chk = FSProcs.processes[stage]["atlas_2chk"]
                log_file  = os.path.join(self.SUBJECTS_DIR, subjid, FSProcs.log(stage))
                return self.fs_chk_stats_f(subjid, atlas2chk, log_file)
            elif stage == "all_done":
                return self.all_done_chk(subjid)
        elif app == 'nilearn':
            pass
        elif app == 'dipy':
            pass
        else:
            print("ERR in app defining")


    def IsRunning_chk(self, subjid, isrunnings, path_2scripts_dir, rm):
        res = False
        try:
            IsRunning_files = list()
            for file in isrunnings:
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


    def fs_chk_recon_files(self, stage, subjid, files2chk):
        '''
        checks if corresponding FreeSurfer recon files were created
        '''
        files_missing = list()
        for path_f in files2chk:
            if not os.path.exists(os.path.join(self.SUBJECTS_DIR, subjid, path_f)):
                files_missing.append(path_f)
        if stage == 'qcache':
            files_ok = fs_definitions.ChkFSQcache(self.SUBJECTS_DIR, subjid, self.app_vars).miss
            print(f"    files missing after qcache: {files_ok}")

        if files_missing:
            log.info(f'    files are missing for {stage}: {str(files_missing)}')
            return False
        else:
            return True


    def fs_chk_stats_f(self, subjid, atlas2chk, log_file):
        res = True
        if self.fs_chk_log(log_file):
            for atlas in atlas2chk:
                for hemi in self.atlas[atlas]["hemi"]:
                    stats_mridir = self.stats(self.app_ver, atlas, _dir = "mri", hemi=hemi)
                    if os.path.exists(stats_mridir):
                        path_2stats_dir = os.path.join(self.SUBJECTS_DIR, subjid, "stats")
                        self.cp_f(stats_mridir, path_2stats_dir)

                    stats = self.stats(self.app_ver, atlas, _dir = "stats", hemi=hemi)
                    if not os.path.exists(os.path.join(self.SUBJECTS_DIR, subjid, stats)):
                        res = False
                        break
        else:
            res = False
        return res


    def fs_chk_log(self, log_file):
        if os.path.exists(log_file):
            content = open(log_file, 'rt').readlines()
            return any('Everything done' in i for i in content)


    def cp_f(self, src, dst):
        try:
            shutil.copy(src, dst)
            return True
        except Exception as e:
            print(e)
            return False


    def all_done_chk(self, subjid):
        result = True
        if not self.chk(subjid, self.app, self.app_vars, 'isrunning'):
            for process in self.proc_order[1:]:
                if not self.chk(subjid, self.app, self.app_vars, process):
                    log.info('        {} is missing {}'.format(subjid, process))
                    result = False
                    break
        else:
            log.info('            IsRunning file present ')
            result = False
        return result
