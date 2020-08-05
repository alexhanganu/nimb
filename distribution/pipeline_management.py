# -*- coding: utf-8 -*-

from os import path, makedirs, listdir


class Management():

    def __init__(self, task, vars):

        print(task)

        self.vars = vars
        print('start distribution')
        self.verify_paths()

    def verify_paths(self):
        # to verify paths and if not present - create them or return error
        if path.exists(self.vars['local']['NIMB_PATHS']['NIMB_HOME']):
            for p in (
                       self.vars['local']['NIMB_PATHS']['NIMB_tmp'],
             path.join(self.vars['local']['NIMB_PATHS']['NIMB_tmp'],'mriparams'),
             path.join(self.vars['local']['NIMB_PATHS']['NIMB_tmp'],'usedpbs'),
                       self.vars['local']['NIMB_PATHS']['NIMB_NEW_SUBJECTS'],
                       self.vars['local']['NIMB_PATHS']['NIMB_PROCESSED_FS'],
                       self.vars['local']['NIMB_PATHS']['NIMB_PROCESSED_FS_error'],
                       self.vars['local']['FREESURFER']['FS_SUBJECTS_DIR']):
                if not path.exists(p):
                    makedirs(p)

    def freesurfer(self):
        if self.vars['local']['FREESURFER']['FreeSurfer_install'] == 1:
            print('start freesurfer processing')

            # todo: write the processing thing here
            return True

    def fs_stats(self):
        """will check if the STATS folder is present and will create if absent
           will return the folder with unzipped stats folder for each subject"""

        for p in [self.vars["local"]["STATS_PATHS"]["STATS_HOME"],]:
            if not path.exists(p):
                makedirs(p)

        PROCESSED_FS_DIR = self.vars["local"]["MRDATA_PATHS"]["PROCESSED_FS_DIR"]
        
        if any('.zip' in i for i in listdir(PROCESSED_FS_DIR)):
            tmp_dir = path.join(PROCESSED_FS_DIR, 'tmp_subject_stats')
            if not path.exists(tmp_dir):
                makedirs(tmp_dir)
                extract_archive(PROCESSED_FS_DIR, ['stats',], tmp_dir)
            return tmp_dir
        else:
            return PROCESSED_FS_DIR


        print('perform statistical analysis')

    def fs_glm(self):

        print('start freesurfer GLM')



'''
variables that must be changed in all scripts and must be removed
'''
# from os import makedirs
# for remote_path in (NIMB_RHOME, dir_new_subjects, FS_SUBJECTS_DIR, processed_SUBJECTS_DIR, nimb_scratch_dir):
#   if not path.isdir(remote_path):
#       makedirs(remote_path)
