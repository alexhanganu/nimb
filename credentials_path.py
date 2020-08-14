'''
currently the main database with passwords and setup files
are located in:
/home/user/nimb (for linux and mac)
C:/Users/User/nimb (for windows)
'''
from os import path, makedirs

#CHANGE THIS LINE TO DEFINE ANOTHER LOCATION FOR THE DATABASE
credentials_home = path.join(path.expanduser("~"), 'nimb')



if not path.exists(credentials_home):
    makedirs(credentials_home)