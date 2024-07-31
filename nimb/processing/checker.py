#!/bin/python
# 2020.10.20

import os
import shutil
import logging

from processing.freesurfer import fs_definitions
log = logging.getLogger(__name__)


class CHECKER():
    def __init__(self,
                 app_vars = dict(),
                 app = 'freesurfer',
                 atlas_definitions = dict()):
        self.stats    = atlas_definitions.stats_f
        self.atlas    = atlas_definitions.atlas_data
        self.app_vars = app_vars
        self.app      = app
        app_home      = self.app_vars[f"{app.upper()}_HOME"]
        if app == "freesurfer":
            self.FSProcs  = fs_definitions.FSProcesses(app_home)
        self.SUBJECTS_DIR = self.app_vars['SUBJECTS_DIR']
        self.proc_order   = self.app_vars["process_order"]
        self.app_ver  = self.app_vars["version"]

    def chk(self, subjid, stage, rm = False):
        if self.app == 'freesurfer':
            if stage == 'isrunning':
                isrunnings    = self.FSProcs.IsRunning_files
                path_2scripts = os.path.join(self.SUBJECTS_DIR, subjid, 'scripts')
                return self.IsRunning_chk(subjid, isrunnings, path_2scripts, rm)
            elif stage == 'registration':
                return os.path.exists(os.path.join(self.SUBJECTS_DIR, subjid))
            elif stage in self.FSProcs.recons:
                files2chk = self.FSProcs.processes[stage]["files_2chk"]
                return self.fs_chk_recon_files(stage, subjid, files2chk)
            elif stage in self.FSProcs.atlas_proc:
                atlas2chk = self.FSProcs.processes[stage]["atlas_2chk"]
                log_file  = os.path.join(self.SUBJECTS_DIR, subjid, self.FSProcs.log(stage))
                return self.fs_chk_stats_f(subjid, atlas2chk, log_file)
            elif stage == "all_done":
                return self.all_done_chk(subjid)
        elif self.app == 'nilearn':
            pass
        elif self.app == 'dipy':
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
        if not self.chk(subjid, 'isrunning'):
            for process in self.proc_order[1:]:
                if not self.chk(subjid, self.app, self.app_vars, process):
                    log.info('        {} is missing {}'.format(subjid, process))
                    result = False
                    break
        else:
            log.info('            IsRunning file present ')
            result = False
        return result
