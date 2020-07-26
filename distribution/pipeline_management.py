# -*- coding: utf-8 -*-

from os import path, makedirs


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

    def stats(self):

        print('perform statistical analysis')

    def fsglm(self):

        print('start freesurfer GLM')



'''
variables that must be changed in all scripts and must be removed
'''
# from os import makedirs
# for remote_path in (NIMB_RHOME, dir_new_subjects, FS_SUBJECTS_DIR, processed_SUBJECTS_DIR, nimb_scratch_dir):
#   if not path.isdir(remote_path):
#       makedirs(remote_path)
