# -*- coding: utf-8 -*-

from os import path, makedirs, listdir


class Management():

    def __init__(self, task, vars):

        print(task)

        self.vars = vars
        self.NIMB_tmp = self.vars["local"]["NIMB_PATHS"]["NIMB_tmp"]
        print('start distribution')
        self.verify_paths()

    def verify_paths(self):
        # to verify paths and if not present - create them or return error
        if path.exists(self.vars['local']['NIMB_PATHS']['NIMB_HOME']):
            for p in (     self.NIMB_tmp,
                 path.join(self.NIMB_tmp, 'mriparams'),
                 path.join(self.NIMB_tmp, 'usedpbs'),
                           self.vars['local']['NIMB_PATHS']['NIMB_NEW_SUBJECTS'],
                           self.vars['local']['NIMB_PATHS']['NIMB_PROCESSED_FS'],
                           self.vars['local']['NIMB_PATHS']['NIMB_PROCESSED_FS_error'],
                           self.vars['local']['FREESURFER']['FS_SUBJECTS_DIR']):
                if not path.exists(p):
                    makedirs(p)

    def freesurfer(self):
        if self.vars['local']['FREESURFER']['FreeSurfer_install'] == 1:
            self.check_freesurfer_ready()
            print('start freesurfer processing')
            return True
            

    def fs_stats(self):
        """will check if the STATS folder is present and will create if absent
           will return the folder with unzipped stats folder for each subject"""

        if not path.exists(self.vars["local"]["STATS_PATHS"]["STATS_HOME"]):
            makedirs(p)

        PROCESSED_FS_DIR = self.vars["local"]["MRDATA_PATHS"]["PROCESSED_FS_DIR"]
        
        if any('.zip' in i for i in listdir(PROCESSED_FS_DIR)):
            from .manage_archive import ZipArchiveManagement
            zipmanager = ZipArchiveManagement()
            tmp_dir = path.join(self.NIMB_tmp, 'tmp_subject_stats')
            if not path.exists(tmp_dir):
                makedirs(tmp_dir)
            zipmanager.extract_archive(PROCESSED_FS_DIR, ['stats',], tmp_dir)
            return tmp_dir
        else:
            return PROCESSED_FS_DIR
        print('perform statistical analysis')


     def fs_glm(self):

        print('start freesurfer GLM')


    def check_freesurfer_ready(self):
        if not path.exists(path.join(self.vars['local']['FREESURFER']['FREESURFER_HOME'], ".license")):
            self.freesurfer_setup()
        else:
            return True


    def freesurfer_setup(self):
        from .setup_freesurfer import SETUP_FREESURFER
        SETUP_FREESURFER(self.vars)
