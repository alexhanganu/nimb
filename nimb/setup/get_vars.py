# -*- coding: utf-8 -*-

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

        # if not path.exists(path.join(self.credentials_home, 'projects.json')):
        #     self.define_credentials()
        # self.set_projects()
        # self.location_vars = self.get_all_locations_vars(self.projects['LOCATION'], self.credentials_home)
        # self.chk_location_vars()
        # self.chk_project_vars()
        # self.stats_vars    = load_json(path.join(self.credentials_home, 'stats.json'))
        # self.chk_stats()


        if path.exists(path.join(self.credentials_home, 'projects.json')):
            self.projects      = load_json(path.join(self.credentials_home, 'projects.json'))
            self.project_ids   = self.get_projects_ids()
            self.location_vars = self.get_all_locations_vars(self.projects['LOCATION'], self.credentials_home)
            self.stats_vars    = load_json(path.join(self.credentials_home, 'stats.json'))
            if params:
                self.project   = self.params.project
                self.chk_location_vars()
                self.chk_project_vars()
                self.chk_stats()
        else:
            self.define_credentials()
            shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'remote1.json'), path.join(self.credentials_home, 'remote1.json'))
            shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'projects.json'), path.join(self.credentials_home, 'projects.json'))
            self.projects      = load_json(path.join(self.credentials_home, 'projects.json'))
            self.project_ids   = self.get_projects_ids()
            shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'local.json'), path.join(self.credentials_home, 'local.json'))
            shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'stats.json'), path.join(self.credentials_home, 'stats.json'))
            self.location_vars = self.get_default_vars(self.projects)
            self.stats_vars    = load_json(path.join(self.credentials_home, 'stats.json'))


    def get_projects_ids(self):
        """retrieve projects_ids"""
        default_projects = list(DEFAULT.project_ids.keys())
        all_projects = [i for i in self.projects.keys() if i not in ('EXPLANATION', 'LOCATION')]
        return all_projects + default_projects


    def set_projects(self):
        """retrieve projects_ids"""
        self.projects   = load_json(path.join(self.credentials_home, 'projects.json'))
        self.populate_default_project()
        self.project_ids = [i for i in self.projects.keys() if i not in ('EXPLANATION', 'LOCATION')]


    def get_all_locations_vars(self, all_locations, path_files):
        d_all_vars = dict()
        for location in all_locations:
            try:
                d_all_vars[location] = load_json(path.join(path_files, location+'.json'))
            except Exception as e:
                print(e)
        d_all_vars = self.change_username(d_all_vars)
        return d_all_vars


    def change_username(self, data):
        user = data['local']['USER']['user']
        user_local = _get_username()
        if user_local != user:
            print('    changing username')
            data['local']['USER']['user'] = user_local
            for variable in data['local']['NIMB_PATHS']:
                data['local']['NIMB_PATHS'][variable] = data['local']['NIMB_PATHS'][variable].replace(user, user_local)
            data['local']['FREESURFER']["FREESURFER_HOME"] = data['local']['FREESURFER']["FREESURFER_HOME"].replace(user, user_local)
            data['local']['FREESURFER']["FS_SUBJECTS_DIR"] = data['local']['FREESURFER']["FS_SUBJECTS_DIR"].replace(user, user_local)
            data['local']['FREESURFER']["export_FreeSurfer_cmd"] = data['local']['FREESURFER']["export_FreeSurfer_cmd"].replace(user, user_local)
        return data


    def populate_default_project(self):
        default_project = load_json(path.join(path.dirname(path.abspath(__file__)), 'projects.json'))
        for project in DEFAULT.project_ids:
            if project not in self.projects:
                self.projects[project] = dict()
        if self.params and self.project in DEFAULT.project_ids:
            print('this is default name of a project used by NIMB. It has pre-defined classification files\
                and uses files downloaded from source website')
            self.projects[self.project] = default_project[DEFAULT.default_project]
            for key in DEFAULT.project_ids[self.project]:
                self.projects[self.project][key] = DEFAULT.project_ids[self.project][key]


    def set_stats(self):
        '''sets the stats folders for the chosedn project
        '''
        update = False
        default_stats   = load_json(path.join(path.dirname(path.abspath(__file__)), 'stats.json'))

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

        if 'nimb_tmp' in self.projects[self.project]['STATS_PATHS']["FS_GLM_dir"]:
            new_key = path.join(NIMB_tmp, 'projects', self.project, fname_dir, 'fs_glm').replace(sep, '/')
            self.projects[self.project]['STATS_PATHS']["FS_GLM_dir"] = new_key
            update = True
        if 'nimb_tmp' in self.projects[self.project]['STATS_PATHS']["STATS_HOME"]:
            new_key = path.join(NIMB_tmp, 'projects', self.project, fname_dir, 'stats').replace(sep, '/')
            self.projects[self.project]['STATS_PATHS'][key] = new_key
            update = True
        for key in [i for i in self.projects[self.project]['STATS_PATHS'] if i not in ("FS_GLM_dir", "STATS_HOME")]:
            if 'nimb_tmp' in self.projects[self.project]['STATS_PATHS'][key]:
                new_ending = self.projects[self.project]['STATS_PATHS'][key].replace(sep, '/').split('/')[-1]
                new_key = path.join(NIMB_tmp, 'projects', self.project, fname_dir, 'stats', new_ending).replace(sep, '/')
                self.projects[self.project]['STATS_PATHS'][key] = new_key
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
            self.populate_default_project()
            update = self.set_stats()

        default_project = load_json(path.join(path.dirname(path.abspath(__file__)), 'projects.json'))
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
        default_stats = load_json(path.join(path.dirname(path.abspath(__file__)), 'stats.json'))

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
        default_local = load_json(path.join(path.dirname(path.abspath(__file__)), 'local.json'))

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
            try:
                with open(path.join(path.dirname(path.abspath(__file__)), 'credentials_path.py'), 'w') as f:
                    f.write('credentials_home=\"'+self.credentials_home+'\"')
            except Exception as e:
                print(e)

        # shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'stats.json'), path.join(self.new_credentials_home, 'stats.json'))
        shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'remote1.json'), path.join(self.new_credentials_home, 'remote1.json'))
        shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'projects.json'), path.join(self.new_credentials_home, 'projects.json'))
        self.projects      = load_json(path.join(self.new_credentials_home, 'projects.json'))

        d_all_vars = self.get_all_locations_vars(self.projects['LOCATION'], path.dirname(path.abspath(__file__)))
        d_all_vars['local'] = self.setup_default_local_nimb(d_all_vars['local'])
        save_json(d_all_vars['local'], path.join(self.new_credentials_home, 'local.json'))
        print('PROJECTS AND VARIABLES ARE NOT DEFINED. check: '+self.credentials_home)


    def get_default_vars(self, projects): #2 be removed
        d_all_vars = self.get_all_locations_vars(projects['LOCATION'], path.dirname(path.abspath(__file__)))
        d_all_vars['local'] = self.setup_default_local_nimb(d_all_vars['local'])
        save_json(d_all_vars['local'], path.join(self.credentials_home, 'local.json'))
        print('PROJECTS AND VARIABLES ARE NOT DEFINED. check: '+self.credentials_home)
        return d_all_vars


    def setup_default_local_nimb(self, data):
        NIMB_HOME = path.abspath(path.join(path.dirname(__file__), '..'))
        print('NIMB_HOME is: ', NIMB_HOME)
        data['NIMB_PATHS']['NIMB_HOME']               = NIMB_HOME
        new_NIMB_tmp = get_userdefined_paths('NIMB temporary folder nimb_tmp', path.join(NIMB_HOME.replace('/nimb/nimb', ''), 'nimb_tmp'), 'nimb_tmp')
        if not path.exists(new_NIMB_tmp):
            makedirs(new_NIMB_tmp)
        data['NIMB_PATHS']['NIMB_tmp']                = new_NIMB_tmp
        data['NIMB_PATHS']['NIMB_NEW_SUBJECTS']       = path.join(new_NIMB_tmp, 'nimb_new_subjects')
        data['NIMB_PATHS']['NIMB_PROCESSED_FS']       = path.join(new_NIMB_tmp, 'nimb_processed_fs')
        data['NIMB_PATHS']['NIMB_PROCESSED_FS_error'] = path.join(new_NIMB_tmp, 'nimb_processed_fs_error')
        new_miniconda_path = get_userdefined_paths('miniconda3 folder', path.join(NIMB_HOME.replace('/nimb/nimb', ''), 'miniconda3'), 'miniconda3')
        data['NIMB_PATHS']['miniconda_home']          = new_miniconda_path
        data['NIMB_PATHS']['miniconda_python_run']    = path.join(new_miniconda_path,'bin','python3.7').replace(path.expanduser("~"),"~")
        new_freesurfer_path = get_userdefined_paths('FreeSurfer folder', path.join(NIMB_HOME.replace('/nimb/nimb', ''), 'freesurfer'), 'freesurfer')
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
            supervisor = input("For some slurm environments a supervisor account is required. Please type supervisor account name or leave blank:")
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
        for key in stats['STATS_PATHS']:
            if 'nimb_tmp' in stats['STATS_PATHS'][key]:
                if key == "FS_GLM_dir":
                    stats['STATS_PATHS'][key] = path.join(NIMB_tmp, 'projects', project, fname_dir, 'fs_glm').replace(sep, '/')
                elif key == "STATS_HOME":
                    stats['STATS_PATHS'][key] = path.join(NIMB_tmp, 'projects', project, fname_dir, 'stats').replace(sep, '/')
                else:
                    new_ending = stats['STATS_PATHS'][key].replace(sep, '/').split('/')[-1]
                    stats['STATS_PATHS'][key] = path.join(NIMB_tmp, 'projects', project, fname_dir, 'stats', new_ending).replace(sep, '/')
        return stats