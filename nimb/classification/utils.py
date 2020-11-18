#!/bin/python
# -*- coding: utf-8 -*-

from os import makedirs, path, sep, system
import json
from collections import OrderedDict

def load_json_ordered(file_abspath):
    """ Load a JSON file as ordered dict
    Args:
        file_abspath (str): Path of a JSON file
    Return:
        Dictionnary of the JSON file
    """
    with open(file_abspath, 'r') as f:
        return json.load(f, object_pairs_hook=OrderedDict)

def load_json(file_abspath):
    """ Load a JSON file as UNordered dict
    Args:
        file_abspath (str): Path of a JSON file
    Return:
        Dictionnary of the JSON file
    """
    with open(file_abspath, 'r') as f:
        return json.load(f)


def save_json(data, file_abspath):
    with open(file_abspath, 'w') as f:
        json.dump(data, f, indent=4)
    system('chmod 777 {}'.format(file_abspath))


def write_txt(file_abspath, lines, write_type = 'w'):
    with open(file_abspath, write_type) as f:
        for val in lines:
            f.write('{}\n'.format(val))

def chk_if_exists(dir):
        if not path.exists(dir):
            makedirs(dir)
        return dir

def get_path(link1, link2):
        return path.join(link1, link2).replace(sep, '/')
