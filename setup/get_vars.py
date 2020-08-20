# -*- coding: utf-8 -*-

from os import path, system, makedirs
import shutil
import json
from .get_username import _get_username
from .get_credentials_home import _get_credentials_home

class Get_Vars():

    def __init__(self):

        self.credentials_home = _get_credentials_home()
        print("credentials are located at: "+self.credentials_home)        
        if path.exists(path.join(self.credentials_home, 'projects.json')):
            self.projects   = self.read_file(path.join(self.credentials_home, 'projects.json'))
            self.location_vars = self.get_vars(self.projects, self.credentials_home)
        else:
            shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'projects.json'), path.join(self.credentials_home, 'projects.json'))
            shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'remote1.json'), path.join(self.credentials_home, 'remote1.json'))
            self.projects = self.read_file(path.join(path.dirname(path.abspath(__file__)), 'projects.json'))
            self.location_vars = self.get_default_vars(self.projects)
        print('local user is: '+self.location_vars['local']['USER']['user'])
        self.installers = self.read_file(path.join(path.dirname(path.abspath(__file__)), 'installers.json'))


    def read_file(self, file):
        with open(file) as jf:
            return json.load(jf)


    def get_vars(self, projects, path_files):
        d_all_vars = dict()
        for location in projects['LOCATION']:
            try:
                d_all_vars[location] = self.read_file(path.join(path_files, location+'.json'))
            except Exception as e:
                print(e)
        d_all_vars = self.change_username(d_all_vars)
        return d_all_vars

    def get_default_vars(self, projects):
        d_all_vars = self.get_vars(projects, path.dirname(path.abspath(__file__)))
        d_all_vars['local'] = self.set_local_nimb(d_all_vars['local'], projects['PROJECTS'][0])
        self.save_json('local.json', d_all_vars['local'], self.credentials_home)
        print('PROJECTS AND VARIABLES ARE NOT DEFINED. check: '+self.credentials_home)
        return d_all_vars

    def verify_local_user(self, user):
        user_local = _get_username()
        return user_local

    def change_username(self, data):
        user = data['local']['USER']['user']
        user_local = self.verify_local_user(user)
        if user_local != user:
            print('changing username')
            data['local']['USER']['user'] = user_local
            for variable in data['local']['NIMB_PATHS']:
                data['local']['NIMB_PATHS'][variable] = data['local']['NIMB_PATHS'][variable].replace(user, user_local)
            data['local']['FREESURFER']["FREESURFER_HOME"] = data['local']['FREESURFER']["FREESURFER_HOME"].replace(user, user_local)
            data['local']['FREESURFER']["FS_SUBJECTS_DIR"] = data['local']['FREESURFER']["FS_SUBJECTS_DIR"].replace(user, user_local)
            data['local']['FREESURFER']["export_FreeSurfer_cmd"] = data['local']['FREESURFER']["export_FreeSurfer_cmd"].replace(user, user_local)
        return data

    def save_json(self, file, data, dst):
        with open(path.join(dst, file), 'w') as jf:
            json.dump(data, jf, indent=4)

    def set_local_nimb(self, data, project):
        NIMB_HOME = path.abspath(path.join(path.dirname(__file__), '..'))
        print('NIMB_HOME is: ',NIMB_HOME)
        data['NIMB_PATHS']['NIMB_HOME']               = NIMB_HOME
        data['NIMB_PATHS']['NIMB_tmp']                = path.join(NIMB_HOME, '..', 'nimb_tmp')
        data['NIMB_PATHS']['NIMB_NEW_SUBJECTS']       = path.join(NIMB_HOME, '..', 'nimb_tmp', 'nimb_new_subjects')
        data['NIMB_PATHS']['NIMB_PROCESSED_FS']       = path.join(NIMB_HOME, '..', 'nimb_tmp', 'nimb_processed_fs')
        data['NIMB_PATHS']['NIMB_PROCESSED_FS_error'] = path.join(NIMB_HOME, '..', 'nimb_tmp', 'nimb_processed_fs_error')
        data['NIMB_PATHS']['miniconda_home']          = path.join(NIMB_HOME, '..', 'miniconda3')
        data['NIMB_PATHS']['miniconda_python_run']    = path.join(NIMB_HOME, '..', 'miniconda3','bin','python3.7').replace(path.expanduser("~"),"~")
        data['FREESURFER']['FREESURFER_HOME']         = path.join(NIMB_HOME,'..', 'freesurfer')
        data['FREESURFER']['FS_SUBJECTS_DIR']         = path.join(NIMB_HOME, '..', 'freesurfer', 'subjects')
        data['FREESURFER']['export_FreeSurfer_cmd']   = "export FREESURFER_HOME="+path.join(NIMB_HOME, '..', 'freesurfer')
        data['FREESURFER']['GLM_dir']                 = path.join(NIMB_HOME, '..', 'nimb_tmp', project, 'glm')
        data['STATS_PATHS']['STATS_HOME']             = path.join(NIMB_HOME, '..', 'nimb_tmp', project, 'stats')
        return data
