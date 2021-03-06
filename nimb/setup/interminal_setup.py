#20200915

import os
from os import path
from setup import database

class term_setup():
    def __init__(self, remote):
        self.remote = remote
        self.cluster = database._get_Table_Data('remotes', remote)
        if 'default' in self.cluster:
            self.credentials = self.setupcredentials()
        else:
            self.credentials = self.cluster[self.remote]

    def setupcredentials(self):
        from setup.term_questionnaire import PyInqQuest
        self.change2false()
        self.remote, remote_new = PyInqQuest(self.remote, self.cluster[self.remote]).answered
        database._set_Table_Data('remotes', {self.remote: remote_new}, self.remote)
        return remote_new

    def change2false(self):
        self.cluster[self.remote] = self.cluster['default']
        self.cluster.pop('default', None)
        for key in self.cluster[self.remote]:
            self.cluster[self.remote][key] = False


def get_userdefined_paths(path_name, old_path, add2path, create = False):
        print(f'current {path_name} is located at: {old_path}')
        get_new = False
        if create:
            create_located = "will be created"
        else:
            create_located = "is located"

        if os.path.exists(old_path):
            keep = input('do you want to keep this path ? (y/n)')
            if 'y' in keep:
                return old_path
            else:
                get_new = True
        if get_new or not os.path.exists(old_path):
            ask_1 = f'    please provide an EXISTING path where the {path_name} folder {create_located}: '
            err_miss = f'        path does not exist. \n'
            user_path = input(ask_1)
            while not os.path.exists(user_path):
                user_path = input(f'{err_miss} {ask_1}')
            new_path = os.path.join(user_path, add2path)
            print('new path is: {}'.format(new_path))
            return new_path

def get_yes_no(q):
    if 'y' in input(q):
        return 1
    else:
        return 0

def get_FS_license():
    license = list()
    for q in ['email', "1st license nr", "2nd license space-star-letter code", "3rd license space-letter code"]:
        res = input('    Please provide FreeSurfer license {}: '.format(q))
        license.append(res)
    return license