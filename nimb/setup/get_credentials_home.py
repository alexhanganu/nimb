from os import path, makedirs, environ
from sys import platform

def _get_credentials_home():
    if platform == 'win32':
        home = environ['USERPROFILE']
    else:
        home = environ['HOME']
    try:
        from setup.credentials_path import credentials_home
        credentials_home = credentials_home.replace("~", home)
    except Exception as e:
        credentials_home = str(open("setup/credentials_path").readlines()[0]).replace("~",home)
    if not path.exists(credentials_home):
        makedirs(credentials_home)
    return credentials_home


