#20200915

from setup import database
from os import path, makedirs

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
        self.remote, remote_new = PyInqQuest(self.cluster[self.remote]).answered
        database._set_Table_Data('remotes', {self.remote: remote_new}, self.remote)
        return remote_new

    def change2false(self):
        self.cluster[self.remote] = self.cluster['default']
        self.cluster.pop('default', None)
        for key in self.cluster[self.remote]:
            self.cluster[self.remote][key] = False


def get_userdefined_paths(path_name, old_path, add2path):
        new_path = old_path
        print('current {} is located at: {}'.format(path_name, old_path))
        if 'n' in input('do you want to keep this path for the {}? (y/n)'.format(path_name)):
            user_path = input('please provide a new path where the {}  will be installed: '.format(path_name))
            while not path.exists(user_path):
                user_path = input('path does not exist. Please provide a new path where {} will be installed: '.format(path_name))
            new_path = path.join(user_path, add2path)
            if not path.exists(new_path):
                makedirs(new_path)
        print('new path is: {}'.format(new_path))
        return new_path

def get_yes_no(q):
    if 'y' in input(q):
        return 1
    else:
        return 0