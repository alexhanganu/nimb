# -*- coding: utf-8 -*-

from os import path
import json

def get_vars():

	with open(path.join(path.dirname(path.abspath(__file__)), 'local.json')) as jf:
		vars = json.load(jf)

	print(vars)#.remote_environment)

# # ==================================
# # script to use the correct username if multiple users are using the same pipeline
# if len(users_list)>1:
#        try:
#               from cget_username import _get_username
#        except ImportError:
#               from a.clib.cget_username import _get_username
#        user = _get_username()
# from os import path
# ==================================



'''
variables that must be changed in all scripts and must be removed
'''
# from os import makedirs
# for remote_path in (NIMB_RHOME, dir_new_subjects, FS_SUBJECTS_DIR, processed_SUBJECTS_DIR, nimb_scratch_dir):
# 	if not path.isdir(remote_path):
# 		makedirs(remote_path)

# cusers_list = users_list
# cuser = user
# nimb_dir = NIMB_HOME
# SUBJECTS_DIR = FS_SUBJECTS_DIR
# processed_SUBJECTS_DIR = path.join('/home',user,'projects',supervisor_account,'processed_subjects') #must be changed to NIMB_HOME/processed_nimb/processed_fs
# dir_new_subjects=path.join('/home',user,'projects',supervisor_account,'new_subjects')  #must be changed to NIMB_RHOME/new_subjects
