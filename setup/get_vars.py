# -*- coding: utf-8 -*-

from os import path, system
import shutil
import json
from credentials_path import credentials_home

class Get_Vars():

	def __init__(self):

		if path.exists(path.join(credentials_home, 'projects.json')):
			f_projects = path.join(credentials_home, 'projects.json')
		else:
			f_projects = path.join(path.dirname(path.abspath(__file__)), 'projects.json')
			print('PROJECTS AND VARIABLES ARE NOT DEFINED. this can be done in the files located at: '+credentials_home)
			for file in ['local.json', 'projects.json', 'remote1.json']:
				shutil.copy(path.join(path.dirname(path.abspath(__file__)), file), path.join(credentials_home, file))
		self.projects = self.get_vars(f_projects)
		self.d_all_vars = dict()
		for location in self.projects['LOCATION']:
			try:
				self.d_all_vars[location] = self.get_vars(path.join(path.dirname(path.abspath(__file__)), location+'.json'))
			except Exception as e:
				print(e)
		if 'local' in self.d_all_vars and len(self.d_all_vars['local']['USER']["users_list"]) > 1:
				self.change_username()

	def get_vars(self, file):
		with open(file) as jf:
			return json.load(jf)

	def verify_local_user(self):
		from .get_username import _get_username
		user = self.d_all_vars['local']['USER']['user']
		user_local = _get_username()
		if user_local != user:
			return True, user, user_local

	def change_username(self):
		change, user, user_local = self.verify_local_user()
		if change:
			print('changing username')
			self.d_all_vars['local']['USER']['user'] = user_local
			for variable in self.d_all_vars['local']['NIMB_PATHS']:
				self.d_all_vars['local']['NIMB_PATHS'][variable] = self.d_all_vars['local']['NIMB_PATHS'][variable].replace(user, user_local)
			self.d_all_vars['local']['FREESURFER']["FREESURFER_HOME"] = self.d_all_vars['local']['FREESURFER']["FREESURFER_HOME"].replace(user, user_local)
			self.d_all_vars['local']['FREESURFER']["FS_SUBJECTS_DIR"] = self.d_all_vars['local']['FREESURFER']["FS_SUBJECTS_DIR"].replace(user, user_local)
			self.d_all_vars['local']['FREESURFER']["export_FreeSurfer_cmd"] = self.d_all_vars['local']['FREESURFER']["export_FreeSurfer_cmd"].replace(user, user_local)

