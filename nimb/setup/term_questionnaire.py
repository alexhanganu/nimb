#!/bin/python
q_confirm ={
        'type': 'confirm',
        'name': 'path',
        'message': 'Is this correct?',
        'default': False}
q_input ={
        'type': 'input',
        'name': 'entry',
        'message': 'Please provide:'}

import sys
try:
    from PyInquirer import prompt
except ImportError:
    import argparse
    print('please install PyInquirer: pip3 install PyInquirer')
    sys.exit(0)

# type = 'inputs' for adding string to dictionary keys
# type = 'paths' for adding paths to dictionary keys

class PyInqQuest():

    def __init__(self, qa = {"q":False}, type = 'inputs'):
        self.qa = qa
        self.type = type
        if self.add():
            new_name = self.define_key()
            self.populate_qa()
            self.answered = (new_name, self.qa)

    def add(self):
        answer = True
        print('location is not defined or credentials are missing, please provide credentials for {}:'.format(self.qa))
        return answer

    def define_key(self):
        q_input['name'] = 'name'
        q_input['message'] = 'Please provide {}'.format('name')
        return self.ask_input()['name']

    def populate_qa(self):
        for key in self.qa:
            if not self.qa[key]:
                q_input['name'] = key
                q_input['message'] = 'Please provide {}'.format(key)
                self.populate(key)

    def populate(self, key):
        resp = self.ask_input()
        if self.type == 'paths':
            if not self.check_path(resp):
                self.populate()
        self.qa[key] = resp[key]

    def check_path(self, path2chk):
        if not path.exists(path2chk):
            print('path does not exist')
            return False
        else:
            return True

    def ask_input(self):
        return prompt(q_input)

    def confirm_qa(self):
        q_confirm['name'] = path_2confirm
        resp =  self.ask_confirm()
        if not resp[path_2confirm]:
            print(resp)

    def ask_confirm(self):
        print('path is: {}'.format(q_confirm['name']))
        return prompt(q_confirm)
