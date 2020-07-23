# -*- coding: utf-8 -*-



class Management():

    def __init__(self, task, vars):

        print(task)

        self.vars = vars
        print('start distribution')


    def freesurfer(self):
        if self.vars['local']['FREESURFER']['FreeSurfer_install'] == 1:
            print('start freesurfer processing')
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
