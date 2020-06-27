#!/usr/bin/env python
# coding: utf-8
# 2020.06.23

from os import getuid, getenv


def _get_username():

    username = ''
    try:
        import pwd
        username = pwd.getpwuid( getuid() ) [0]
        print('username from pwd')
    except ImportError:
        print(e)
    if not username:
        try:
            import getpass
            username = getpass.getuse()
            print('username from getpass')
        except ImportError:
            print('getpass not installed')
    if not username:
        try:
            username = getenv('HOME').split('/')[-1]
            print('username from getenv')
        except Exception as e:
            print(e)
    return username
