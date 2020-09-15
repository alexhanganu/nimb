#!/bin/python
q_confirm ={
        'type': 'confirm',
        'name': 'path',
        'message': 'Is this path correct?',
        'default': False}
q_input ={
        'type': 'input',
        'name': 'entry',
        'message': 'Please provide a path:'}

try:
    from PyInquirer import prompt
except ImportError:
    import argparse
    print('please install PyInquirer: pip3 install PyInquirer')

class PyInqQuest():

    def __init__(self, path_2confirm):

        q_confirm['name'] = path_2confirm
        resp =  self.ask_q()
        if not resp[path_2confirm]:
            resp = self.ask_input()
            print(resp)

    def ask_q(self):
        print('path is: {}'.format(q_confirm['name']))
        return prompt(q_confirm)

    def ask_input(self):
        return prompt(q_input)



