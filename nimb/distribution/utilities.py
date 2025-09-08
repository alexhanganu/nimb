# -*- coding: utf-8 -*-

"""
A collection of reusable utility functions for file system operations,
JSON handling, and error messages.
"""

import os
import json
import shutil
import sys
from os.path import expanduser
import subprocess


def load_json(filepath):
    """Loads and returns a JSON file as a dictionary."""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {filepath}: {e}")
            return {}
    return {}


def save_json(data, filepath, print_space=4):
    """Saves a dictionary as a JSON file."""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=print_space)
        return True
    except Exception as e:
        print(f"Error saving JSON to {filepath}: {e}")
        return False


def get_path(path_var, root_dir=''):
    """
    Converts a path variable to an absolute path, expanding the home directory.
    If a root directory is provided, it joins the path with the root.
    """
    if not path_var:
        return ''
    full_path = expanduser(path_var)
    if root_dir:
        full_path = os.path.join(root_dir, full_path)
    return os.path.abspath(full_path)


def makedir_ifnot_exist(path_list):
    """
    Creates a directory or a list of directories if they don't exist.
    """
    if not isinstance(path_list, list):
        path_list = [path_list]
    for p in path_list:
        if p and not os.path.exists(p):
            try:
                os.makedirs(p, exist_ok=True)
            except OSError as e:
                print(f"Error creating directory {p}: {e}")
                return False
    return True


def is_writable_directory(dir_path):
    """
    Checks if a directory exists and is writable.
    """
    return dir_path and os.path.isdir(dir_path) and os.access(dir_path, os.W_OK)


def is_ENV_defined(env_name):
    """
    Checks if an environment variable is defined in the shell environment.
    """
    return env_name in os.environ and os.environ[env_name]


def is_command_ran_successfully(command):
    """
    Executes a shell command and checks if it ran successfully.
    Returns True if successful, False otherwise.
    """
    try:
        subprocess.run(command, shell=True, check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


class ErrorMessages:
    """
    A class to store and retrieve formatted error messages.
    """
    @staticmethod
    def error_unknown_process(process_name):
        print(f"ERROR: Unknown process '{process_name}'. Check your -process argument.")

    @staticmethod
    def error_classify():
        print("ERROR: Classification pre-requisites not met. Please run with '-process ready' to diagnose.")
