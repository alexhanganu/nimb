# -*- coding: utf-8 -*-

import os
from os import path, system, sep, makedirs
import shutil
import json
from .get_username import _get_username
from .get_credentials_home import _get_credentials_home
from .interminal_setup import get_userdefined_paths, get_yes_no, get_FS_license
from distribution.utilities import load_json, save_json
from distribution.distribution_definitions import DEFAULT



class Get_Vars():
    '''retrieving main variables, based on the json files located in credentials_home/
        if variables are missing - they are being defined through a questionnaire
    Args:
        none
    Return:
        projects - dict with all projects from the credentials_home/projects.json file
        location_vars - dict with all varibale from the credentials_home/local.json and all remote.json files
        stats_vars - dict with all vars from the credentials_home/stats.json file
    '''

    def __init__(self, params = list()):

        self.credentials_home = _get_credentials_home()
        self.params           = params

        self.set_projects()
        self.get_all_locations_vars()
        if self.params:
            self.project   = self.params.project
            self.populate_default_project()
            self.chk_location_vars()
            self.chk_project_vars()
            self.chk_stats()


    def get_projects_ids(self):
        """retrieve projects_ids"""
        default_projects = list(DEFAULT.project_ids.keys())
        all_projects = [i for i in self.projects.keys() if i not in ('EXPLANATION', 'LOCATION')]
        return all_projects + default_projects


    def set_projects(self):
        """retrieve projects_ids"""
        file = os.path.join(self.credentials_home, 'projects.json')
        default = False
        if not self.chk_if_defined('projects'):
            self.define_credentials()
            default = True
            shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'projects.json'), file)
            shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stats.json'),
                        os.path.join(self.credentials_home, 'stats.json'))
            print(f'    CHECK PROJECTS AND VARIABLES in: {self.credentials_home}')
        self.projects    = self.load_file('projects', default = default)
        self.stats_vars  = load_json(path.join(self.credentials_home, 'stats.json'))
        self.project_ids = self.get_projects_ids()


    def load_file(self, file, default = False):
        if default:
            return load_json(os.path.join(os.path.dirname(os.path.abspath(__file__)), f'{file}.json'))
        else:
            return load_json(os.path.join(self.credentials_home, f'{file}.json'))


    def chk_if_defined(self, file):
        return os.path.exists(os.path.join(self.credentials_home, f'{file}.json'))


    def get_all_locations_vars(self):
        if not self.chk_if_defined('local'):
            self.setup_default_local_nimb()
        self.location_vars    = dict()
        for location in self.projects['LOCATION']:
            try:
                self.location_vars[location] = self.load_file(location)
            except Exception as e:
                print(e)
        self.change_username()


    def change_username(self):
        local_vars = self.location_vars['local']
        user = local_vars['USER']['user']
        user_local = _get_username()
        if user_local != user:
            print('    changing username')
            local_vars['USER']['user'] = user_local
            NIMB_PATHS = local_vars['NIMB_PATHS']
            FS_PATHS   = local_vars['FREESURFER']
            for var in NIMB_PATHS:
                NIMB_PATHS[var] = NIMB_PATHS[var].replace(user, user_local)
            for var in ("FREESURFER_HOME", "FS_SUBJECTS_DIR", "export_FreeSurfer_cmd"):
                FS_PATHS[var] = FS_PATHS[var].replace(user, user_local)
            local_vars['NIMB_PATHS'] = NIMB_PATHS
            local_vars['FREESURFER'] = FS_PATHS
        self.location_vars['local'] = local_vars


    def populate_default_project(self):
        default_project = self.load_file('projects', default = True)
        for project in DEFAULT.project_ids:
            if project not in self.projects:
                self.projects[project] = dict()
        if self.params and self.project in DEFAULT.project_ids:
            if not self.projects[self.project]:
                print('    this is default name of a project used by NIMB. It has pre-defined classification files\
                    and uses files downloaded from source website')
                self.projects[self.project] = default_project[DEFAULT.default_project]
                for key in DEFAULT.project_ids[self.project]:
                    self.projects[self.project][key] = DEFAULT.project_ids[self.project][key]


    def set_stats(self):
        '''sets the stats folders for the chosedn project
        '''
        update = False
        default_stats = self.load_file('stats', default = True)

        print('    setting stats')
        NIMB_tmp     = self.location_vars['local']['NIMB_PATHS']['NIMB_tmp']
        try:
            fname_groups = self.projects[self.project]['fname_groups']
        except KeyError:
            fname_groups = DEFAULT.default_tab_name
        fname_dir    = path.splitext(fname_groups)[0].replace('(','').replace(')','')

        for key in [i for i in default_stats.keys() if i not in ('EXPLANATION',)]:
            if key not in self.projects[self.project]:
                self.projects[self.project][key] = {}#default_stats[key]
                update = True
            for subkey in default_stats[key]:
                if subkey not in self.projects[self.project][key]:
                    self.projects[self.project][key][subkey] = default_stats[key][subkey]
                    self.projects['EXPLANATION'][subkey] = default_stats['EXPLANATION'][subkey]
                    update = True
                if isinstance(subkey, list):
                    if not isinstance(self.projects[self.project][key][subkey], list):
                        print('    types are different {}'.format(subkey))

        for _dir in DEFAULT.stats_dirs:
            new_key = path.join(NIMB_tmp, 'projects', self.project, fname_dir,
                                    DEFAULT.stats_dirs[_dir]).replace(sep, '/')
            self.projects[self.project]['STATS_PATHS'][_dir] = new_key
            update = True
        return update


    def chk_project_vars(self):
        """
        check if variables are defined in json
        :param config_file: path to configuration json file
        :return: new version, populated with missing values
        """
        update = False
        if self.params:
            update = self.set_stats()

        default_project = self.load_file('projects', default = True)
        for subkey in default_project[DEFAULT.default_project]:
            if subkey not in self.projects[self.project]:
                print('adding missing subkey {} to project: {}'.format(subkey, self.project))
                self.projects[self.project][subkey] = default_project[DEFAULT.default_project][subkey]
                self.projects['EXPLANATION'][subkey] = default_project['EXPLANATION'][subkey]
                update = True
            if isinstance(subkey, list):
                if not isinstance(self.projects[self.project][subkey], list):
                    print('types are different {}'.format(subkey))
        if update:
            save_json(self.projects, path.join(self.credentials_home, 'projects.json'))

        for project in DEFAULT.project_ids:
            if project not in self.projects:
                self.projects[project] = default_project[DEFAULT.default_project]


    def chk_stats(self):
        """
        check if variables are defined in json
        :param config_file: path to configuration json file
        :return: new version, populated with missing values
        """
        default_stats = self.load_file('stats', default = True)

        update_stats = False
        for key in [i for i in default_stats.keys() if 'EXPLANATION' not in i]:
            if key not in self.stats_vars:
                print('adding missing key {} to stats'.format(key))
                self.stats_vars[key] = default_stats[key]
                update_stats = True
            for subkey in default_stats[key]:
                if subkey not in self.stats_vars[key]:
                    print('adding missing subkey {} to stats group: {}'.format(subkey, key))
                    self.stats_vars[key][subkey] = default_stats[key][subkey]
                    self.stats_vars['EXPLANATION'][subkey] = default_stats['EXPLANATION'][subkey]
                    update_stats = True
                if isinstance(subkey, list):
                    if not isinstance(self.stats_vars[key][subkey], list):
                        print('    types are different {}'.format(subkey))
        if update_stats:
            save_json(self.stats_vars, path.join(self.credentials_home, 'stats.json'))


    def chk_location_vars(self):
        default_local = self.load_file('local', default = True)

        update = False
        for location in self.location_vars:
            for Key in default_local:
                if Key not in self.location_vars[location]:
                    print('adding missing key {} to location: {}'.format(Key, location))
                    self.location_vars[location][Key] = default_local[Key]
                    update = True
                for subkey in default_local[Key]:
                    if subkey not in self.location_vars[location][Key]:
                        print('adding missing subkey {} to location: {}, key: {}'.format(subkey, location, Key))
                        self.location_vars[location][Key][subkey] = default_local[Key][subkey]
                        update = True
            if location == 'local':
                self.chk_paths(self.location_vars[location])
            if update:
                self.location_vars[location]['EXPLANATION'] = default_local['EXPLANATION']
                print('must update location: {}'.format(location))
                save_json(self.location_vars[location], path.join(self.credentials_home, location+'.json'))


    def chk_paths(self, local_vars):
        # to verify paths and if not present - create them or return error
        NIMB_HOME = local_vars['NIMB_PATHS']['NIMB_HOME']
        if path.exists(NIMB_HOME):
            NIMB_tmp = local_vars['NIMB_PATHS']['NIMB_tmp']
            for p in (NIMB_tmp,
                 path.join(NIMB_tmp, 'mriparams'),
                 path.join(NIMB_tmp, 'usedpbs'),
                           local_vars['NIMB_PATHS']['NIMB_NEW_SUBJECTS'],
                           local_vars['NIMB_PATHS']['NIMB_PROCESSED_FS'],
                           local_vars['NIMB_PATHS']['NIMB_PROCESSED_FS_error']):
                if not path.exists(p):
                    print('creating path ',p)
                    makedirs(p)
        else:
            print(f"path NIMB_HOME is missing at: {NIMB_HOME}")


    def define_credentials(self):
        self.new_credentials_home = get_userdefined_paths('credentials', self.credentials_home, "nimb")
        if self.new_credentials_home != self.credentials_home:
            self.credentials_home = self.new_credentials_home
            try:
                with open(path.join(path.dirname(path.abspath(__file__)), 'credentials_path.py'), 'w') as f:
                    f.write('credentials_home=\"'+self.credentials_home+'\"')
            except Exception as e:
                print(e)


    def setup_default_local_nimb(self):
        shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'local.json'),
                    os.path.join(self.credentials_home, 'remote1.json'))

        local_vars = self.load_file('local', default = True)
        local_vars['USER']['user'] = _get_username()

        '''setting NIMB paths'''
        NIMB_PATHS = local_vars['NIMB_PATHS']
        NIMB_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        print('NIMB_HOME is: ', NIMB_HOME)
        NIMB_PATHS['NIMB_HOME']               = NIMB_HOME
        new_NIMB_tmp = get_userdefined_paths('NIMB temporary folder nimb_tmp',
                                            os.path.join(NIMB_HOME.replace('/nimb/nimb', ''), 'nimb_tmp'),
                                            'nimb_tmp')
        if not path.exists(new_NIMB_tmp):
            makedirs(new_NIMB_tmp)
        NIMB_PATHS['NIMB_tmp']                = new_NIMB_tmp
        NIMB_PATHS['NIMB_NEW_SUBJECTS']       = os.path.join(new_NIMB_tmp, 'nimb_new_subjects')
        NIMB_PATHS['NIMB_PROCESSED_FS']       = os.path.join(new_NIMB_tmp, 'nimb_processed_fs')
        NIMB_PATHS['NIMB_PROCESSED_NILEARN']  = os.path.join(new_NIMB_tmp, 'nimb_processed_nilearn')
        NIMB_PATHS['NIMB_PROCESSED_DIPY']     = os.path.join(new_NIMB_tmp, 'nimb_processed_dipy')
        NIMB_PATHS['NIMB_PROCESSED_FS_error'] = os.path.join(new_NIMB_tmp, 'nimb_processed_fs_error')


        '''setting FREESURFER paths'''
        new_freesurfer_path = get_userdefined_paths('FreeSurfer folder',
                                                    os.path.join(NIMB_HOME.replace('/nimb/nimb', ''),'freesurfer'),
                                                    'freesurfer')

        new_conda_path = new_freesurfer_path.replace("freesurfer", "conda3")
        NIMB_PATHS['conda_home']              = new_conda_path
        NIMB_PATHS['miniconda_python_run']    = os.path.join(new_conda_path,
                                                            'bin',
                                                            'python3.7').replace(os.path.expanduser("~"),"~")
        local_vars['NIMB_PATHS'] = NIMB_PATHS

        FS_PATHS   = local_vars['FREESURFER']
        FS_PATHS['FREESURFER_HOME']       = new_freesurfer_path
        FS_PATHS['FS_SUBJECTS_DIR']       = os.path.join(new_freesurfer_path, 'subjects')
        FS_PATHS['export_FreeSurfer_cmd'] = "export FREESURFER_HOME="+new_freesurfer_path
        if not os.path.exists(new_freesurfer_path):
            FreeSurfer_install = get_yes_no(f'do you want to install FreeSurfer at the provided location {new_freesurfer_path}? (y/n)')
            FS_PATHS['FreeSurfer_install']     = FreeSurfer_install
            if FreeSurfer_install == 1:
                freesurfer_license = get_FS_license()
                FS_PATHS['freesurfer_license'] = freesurfer_license
        else:
            FS_PATHS['FreeSurfer_install']     = 1
        local_vars['FREESURFER'] = FS_PATHS

        '''setting PROCESSING paths'''
        environ = get_yes_no("Will this account use slurm or tmux for processing ? (y/n; y=slurm/ n=tmux)")
        if environ == 1:
            local_vars['PROCESSING']['processing_env']      = 'slurm'
            supervisor = input("For some slurm environments a supervisor account is required. Please type supervisor account name or leave blank:")
            if supervisor:
                print('supervisor account name is: {}'.format(supervisor))
                local_vars['USER']['supervisor_account']       = str(supervisor)
                local_vars['PROCESSING']['supervisor_account'] = str(supervisor)
                local_vars['PROCESSING']['text4_scheduler'][1] = local_vars['PROCESSING']['text4_scheduler'][1].replace('def-supervisor',supervisor)
            else:
                print('supervisor account not provided')
                local_vars['USER']['supervisor_account']       = ''
                local_vars['PROCESSING']['supervisor_account'] = ''
                local_vars['PROCESSING']['text4_scheduler'].remove(local_vars['PROCESSING']['text4_scheduler'][1])
        else:
            print('environment for processing is: {}'.format(environ))
            local_vars['PROCESSING']['processing_env']      = 'tmux'
        save_json(local_vars, os.path.join(self.credentials_home, 'local.json'))
        self.get_all_locations_vars()




class SetLocation():


    def __init__(self, data_requested, location):
        self.credentials_home = _get_credentials_home()
        self.username = data_requested[location]['username']
        print(self.username)
        self.set_project(location)


    def set_project(self, location):
        if path.exists(path.join(self.credentials_home, 'projects.json')):
            projects = load_json(path.join(self.credentials_home, 'projects.json'))
            projects['LOCATION'].append(location)
            save_json(projects, path.join(self.credentials_home, 'projects.json'))
            # self.save_json('projects.json', projects, self.credentials_home)
            new_loc = load_json(path.join(self.credentials_home, 'remote1.json'))
            new_loc['USER']['user']= self.username
            save_json(new_loc, path.join(self.credentials_home, location+'.json'))



class SetProject():
    '''
    stats defined in credentials_path-> stats.json are general. This one defines stats folder for each project
    Args:
        NIMB_tmp folder, current stats folder names, project name
    Return:
        new dict stats with the project name as folder inside the nimb_tmp folder
    '''


    def __init__(self, NIMB_tmp, stats, project, projects):
        self.projects = projects
        fname_groups = self.projects[project]['fname_groups']
        self.stats = self.set_project(NIMB_tmp, stats, project, fname_groups)


    def set_project(self, NIMB_tmp, stats, project, fname_groups):
        fname_dir = path.splitext(fname_groups)[0].replace('(','').replace(')','')
        for _dir in DEFAULT.stats_dirs:
            if 'default' in stats['STATS_PATHS'][_dir]:
                new_key = path.join(NIMB_tmp, 'projects', project, fname_dir,
                    DEFAULT.stats_dirs[_dir]).replace(sep, '/')
                stats['STATS_PATHS'][_dir] = new_key

        '''old version'''
        # for key in stats['STATS_PATHS']:
        #     if 'nimb_tmp' in stats['STATS_PATHS'][key]:
        #         if key == "FS_GLM_dir":
        #             stats['STATS_PATHS'][key] = path.join(NIMB_tmp, 'projects', project, fname_dir, 'fs_glm').replace(sep, '/')
        #         elif key == "STATS_HOME":
        #             stats['STATS_PATHS'][key] = path.join(NIMB_tmp, 'projects', project, fname_dir, 'stats').replace(sep, '/')
        #         else:
        #             new_ending = stats['STATS_PATHS'][key].replace(sep, '/').split('/')[-1]
        #             stats['STATS_PATHS'][key] = path.join(NIMB_tmp, 'projects', project, fname_dir, 'stats', new_ending).replace(sep, '/')
        return stats