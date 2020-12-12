# -*- coding: utf-8 -*-

from os import path, system, sep, makedirs
import shutil
import json
from .get_username import _get_username
from .get_credentials_home import _get_credentials_home
from .interminal_setup import get_userdefined_paths, get_yes_no, get_FS_license

class SetProject():
    '''
    stats defined in credentials_path-> stats.json are general. This one defines stats folder for each project
    Args:
        NIMB_tmp folder, current stats folder names, project name
    Return:
        new dict stats with the project name as folder inside the nimb_tmp folder
    '''

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


    def define_credentials(self):
        self.new_credentials_home = get_userdefined_paths('credentials', self.credentials_home, "nimb")
        if self.new_credentials_home != self.credentials_home:
            try:
                with open(path.join(path.dirname(path.abspath(__file__)), 'credentials_path.py'), 'w') as f:
                    f.write('credentials_home=\"'+self.credentials_home+'\"')
                with open(path.join(path.dirname(path.abspath(__file__)), 'credentials_path'), 'w') as f:
                    json.dump(self.credentials_home, f)
            except Exception as e:
                print(e)

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
        if not path.exists(new_freesurfer_path):
            FreeSurfer_install = get_yes_no('do you want to install FreeSurfer at the provided location {}? (y/n)'.format(new_freesurfer_path))
            data['FREESURFER']['FreeSurfer_install']      = FreeSurfer_install
            if FreeSurfer_install == 1:
                freesurfer_license = get_FS_license()
                data['FREESURFER']['freesurfer_license']  = freesurfer_license
        else:
            data['FREESURFER']['FreeSurfer_install']      = 1
        data['FREESURFER']['FREESURFER_HOME']         = new_freesurfer_path
        data['FREESURFER']['FS_SUBJECTS_DIR']         = path.join(new_freesurfer_path, 'subjects')
        data['FREESURFER']['export_FreeSurfer_cmd']   = "export FREESURFER_HOME="+new_freesurfer_path
        environ = get_yes_no("Will this account use slurm or tmux for processing ? (y/n; y=slurm/ n=tmux)")
        if environ == 1:
            data['PROCESSING']['processing_env']      = 'slurm'
            supervisor = input("For some slurm environments a supervisor account is required. Please type superviros account name or leave blank:")
            if supervisor:
                print('supervisor account name is: {}'.format(supervisor))
                data['USER']['supervisor_account']       = str(supervisor)
                data['PROCESSING']['text4_scheduler'][1] = data['PROCESSING']['text4_scheduler'][1].replace('def-supervisor',supervisor)
            else:
                print('supervisor account not provided')
                data['USER']['supervisor_account']       = ''
                data['PROCESSING']['text4_scheduler'].remove(data['PROCESSING']['text4_scheduler'][1])
        else:
            print('environment for processing is: {}'.format(environ))
            data['PROCESSING']['processing_env']      = 'tmux'


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
