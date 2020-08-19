from os import path, makedirs
from .get_username import _get_username

def _get_credentials_home():
    credentials_home = str(open("credentials_path").readlines()[0]).replace("~",path.join("/home",_get_username()))
    if not path.exists(credentials_home):
        makedirs(credentials_home)
    return credentials_home
