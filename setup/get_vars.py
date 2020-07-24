# -*- coding: utf-8 -*-

from os import path
import json

class Get_Vars():

	def __init__(self):

		f_vars_local = path.join(path.dirname(path.abspath(__file__)), 'local.json')
		self.d_all_vars = dict()
		self.d_all_vars['local'] = self.get_vars(f_vars_local)
		self.change_username()
		for remote_name in self.d_all_vars['local']['REMOTE']:
			self.d_all_vars[remote_name] = self.get_vars(path.join(path.dirname(path.abspath(__file__)), remote_name+'.json'))

	def get_vars(self, file):
		with open(file) as jf:
			return json.load(jf)

	def verify_local_user(self):
		from get_username import _get_username
		user = self.d_all_vars['local']['USER']['user']
		user_local = _get_username()
		if user_local != user:
			return True, user, user_local

	def change_username(self):
		if len(self.d_all_vars['local']['USER']["users_list"])>1:
			change, user, user_local = self.verify_local_user()
			if change:
				print('changing username')
				self.d_all_vars['local']['USER']['user'] = user_local
				for variable in self.d_all_vars['local']['NIMB_PATHS']:
					self.d_all_vars['local']['NIMB_PATHS'][variable] = self.d_all_vars['local']['NIMB_PATHS'][variable].replace(user, user_local)
				for variable in self.d_all_vars['local']['FREESURFER']:
					self.d_all_vars['local']['FREESURFER'][variable] = self.d_all_vars['local']['FREESURFER'][variable].replace(user, user_local)
