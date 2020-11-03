# -*- coding: utf-8 -*-

from os import path, system, sep, makedirs
import shutil
import json
from .get_username import _get_username
from .get_credentials_home import _get_credentials_home
from .interminal_setup import get_userdefined_paths, get_yes_no

class SetProject():

    def __init__(self, NIMB_tmp, stats, project):
        self.stats = self.set_project(NIMB_tmp, stats, project)

    def set_project(self, NIMB_tmp, stats, project):
        for key in stats['STATS_PATHS']:
            if project not in stats['STATS_PATHS'][key]:
                    if key != "STATS_HOME":
                        new_ending = '/'.join(stats['STATS_PATHS'][key].replace(sep, '/').split('/')[-2:])
                    else:
                        new_ending = '/'.join(stats['STATS_PATHS'][key].replace(sep, '/').split('/')[-1:])
                    stats['STATS_PATHS'][key] = path.join(NIMB_tmp, project, new_ending).replace(sep, '/')
        return stats

class Get_Vars():

    def __init__(self):

        self.credentials_home = _get_credentials_home()
        print("credentials are located at: {}".format(self.credentials_home))
        if path.exists(path.join(self.credentials_home, 'projects.json')):
            self.projects   = self.read_file(path.join(self.credentials_home, 'projects.json'))
            self.location_vars = self.get_vars(self.projects, self.credentials_home)
            self.stats_vars = self.read_file(path.join(self.credentials_home, 'stats.json'))
        else:
            self.define_credentials()
            shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'projects.json'), path.join(self.credentials_home, 'projects.json'))
            shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'local.json'), path.join(self.credentials_home, 'local.json'))
            shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'remote1.json'), path.join(self.credentials_home, 'remote1.json'))
            shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'stats.json'), path.join(self.credentials_home, 'stats.json'))
            self.projects = self.read_file(path.join(self.credentials_home, 'projects.json'))
            self.location_vars = self.get_default_vars(self.projects)
            self.stats_vars = self.read_file(path.join(self.credentials_home, 'stats.json'))
        print('local user is: '+self.location_vars['local']['USER']['user'])
        self.installers = self.read_file(path.join(path.dirname(path.abspath(__file__)), 'installers.json'))


    def define_credentials(self):
        self.credentials_home = get_userdefined_paths('credentials', self.credentials_home, "nimb")
        with open(path.join(path.dirname(path.abspath(__file__)), 'credentials_path.py'), 'w') as f:
            f.write('credentials_home=\"'+self.credentials_home+'\"')
        with open(path.join(path.dirname(path.abspath(__file__)), 'credentials_path'), 'w') as f:
            json.dump(self.credentials_home, f)
    
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
        d_all_vars['local'] = self.setup_default_local_nimb(d_all_vars['local'])
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

    def setup_default_local_nimb(self, data):
        NIMB_HOME = path.abspath(path.join(path.dirname(__file__), '..'))
        print('NIMB_HOME is: ', NIMB_HOME)
        data['NIMB_PATHS']['NIMB_HOME']               = NIMB_HOME
        new_NIMB_tmp = get_userdefined_paths('NIMB temporary folder nimb_tmp', path.join(NIMB_HOME, '../..', 'nimb_tmp'), 'nimb_tmp')
        if not path.exists(new_NIMB_tmp):
            makedirs(new_NIMB_tmp)
        data['NIMB_PATHS']['NIMB_tmp']                = new_NIMB_tmp
        data['NIMB_PATHS']['NIMB_NEW_SUBJECTS']       = path.join(new_NIMB_tmp, 'nimb_new_subjects')
        data['NIMB_PATHS']['NIMB_PROCESSED_FS']       = path.join(new_NIMB_tmp, 'nimb_processed_fs')
        data['NIMB_PATHS']['NIMB_PROCESSED_FS_error'] = path.join(new_NIMB_tmp, 'nimb_processed_fs_error')
        new_miniconda_path = get_userdefined_paths('miniconda3 folder', path.join(NIMB_HOME, '../..', 'miniconda3'), 'miniconda3')
        data['NIMB_PATHS']['miniconda_home']          = new_miniconda_path
        data['NIMB_PATHS']['miniconda_python_run']    = path.join(new_miniconda_path,'bin','python3.7').replace(path.expanduser("~"),"~")
        new_freesurfer_path = get_userdefined_paths('FreeSurfer folder', path.join(NIMB_HOME, '../..', 'freesurfer'), 'freesurfer')
        FreeSurfer_install = get_yes_no('do you want to install FreeSurfer at the provided location {}? (y/n)'.format(new_freesurfer_path))
        data['FREESURFER']['FreeSurfer_install']      = FreeSurfer_install
        data['FREESURFER']['FREESURFER_HOME']         = new_freesurfer_path
        data['FREESURFER']['FS_SUBJECTS_DIR']         = path.join(new_freesurfer_path, 'subjects')
        data['FREESURFER']['export_FreeSurfer_cmd']   = "export FREESURFER_HOME="+new_freesurfer_path
        return data

class SetLocation():

    def __init__(self, data_requested, location):
        self.credentials_home = _get_credentials_home()
        self.username = data_requested[location]['username']
        print(self.username)
        self.set_project(location)

    def set_project(self, location):
        if path.exists(path.join(self.credentials_home, 'projects.json')):
            projects = self.read_file(path.join(self.credentials_home, 'projects.json'))
            projects['LOCATION'].append(location)
            self.save_json('projects.json', projects, self.credentials_home)
            new_loc = self.read_file(path.join(self.credentials_home, 'remote1.json'))
            new_loc['USER']['user']= self.username
            self.save_json(location+'.json', new_loc, self.credentials_home)

    def read_file(self, file):
        with open(file) as jf:
            return json.load(jf)

    def save_json(self, file, data, dst):
        with open(path.join(dst, file), 'w') as jf:
            json.dump(data, jf, indent=4)