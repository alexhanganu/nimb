#!/usr/bin/env python
# coding: utf-8
# 2020.06.23


def _get_username():

    username = ''
    try:
        from os import getuid
        import pwd
        username = pwd.getpwuid( getuid() ) [0]
        print('username from pwd')
    except ImportError as e:
        print(e)
    if not username:
        try:
            import getpass
            try:
                username = getpass.getuser()
            except Exception as e:
                print(e)
            print('username from getpass')
        except ImportError:
            print('getpass not installed')
    if not username:
        try:
            from os import getenv
            username = getenv('HOME').split('/')[-1]
            print('username from getenv')
        except Exception as e:
            print(e)
    return username
