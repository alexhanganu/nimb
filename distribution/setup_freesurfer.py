#!/usr/bin/env python
# coding: utf-8
# 2020.08.17


from os import path, chdir, system, remove
import time, shutil

class SETUP_FREESURFER():

    def __init__(self, vars, installers):

        self.NIMB_HOME            = vars['local']['NIMB_PATHS']['NIMB_HOME']
        self.FREESURFER_HOME      = vars['local']['FREESURFER']['FREESURFER_HOME']

        if not path.exists(self.FREESURFER_HOME):
            print("installing freesurfer")
            self.freesurfer_install(vars['local']['FREESURFER']['freesurfer_version'], installers)
            print('FINISHED Installing')
        if not path.exists(path.join(self.FREESURFER_HOME, 'MCRv84')):
            print("installing MATLAB")
            self.matlab_install(vars['local']['FREESURFER']['export_FreeSurfer_cmd'],
                                vars['local']['FREESURFER']['source_FreeSurfer_cmd'])
            print('FINISHED Installing MATLAB')
            print('writing license file')
        self.check_freesurfer_license(vars['local']['FREESURFER']['freesurfer_license'])

    def check_freesurfer_license(self, license):
        print('creating freesurfer license.txt file for FreeSurfer 7.1.1')
        if path.isfile(path.join(self.FREESURFER_HOME, 'license.txt')):
            try:
                shutil.move(path.join(self.FREESURFER_HOME, 'license.txt'),path.join(self.FREESURFER_HOME, 'license_freesurfer.txt'))
            except Exception as e:
                print(e)
                remove(path.join(self.FREESURFER_HOME, 'license.txt'))
        with open(path.join(self.FREESURFER_HOME, 'license.txt'), 'w') as f:
            for line in fs_license:
                f.write(line + '\n')

    def freesurfer_install(self, freesurfer_version, installers):
        if freesurfer_version == 7:
            installer = installers['INSTALLERS']['freesurfer7.1.1_installer']
        else:
            print('freesurfer version not defined')
        chdir(self.NIMB_HOME)
        print('downloading freesurfer')
        installer_f = installer.split("/")[-1]
        try:
            system('wget '+installer)
            while not path.isfile(path.join(self.NIMB_HOME, installer_f)):
                time.sleep(1000)
        except Exception:
            system('curl -o '+installer_f+' '+installer)
            while not path.isfile(path.join(self.NIMB_HOME, installer_f)):
                time.sleep(1000)

        print('extracting freesurfer')
        system('tar -C '+self.FREESURFER_HOME.replace('freesurfer','')+' -xvf '+installer_f)
        system('chmod -R 777 '+path.join(self.FREESURFER_HOME, "subjects"))

        if path.exists(self.FREESURFER_HOME):
            print('removing installer')
            remove(installer_f)
        else:
            print('something wrong, please review')

    def matlab_install(self, export_FreeSurfer_cmd, source_FreeSurfer_cmd):
        chdir(self.FREESURFER_HOME)
        print('installing matlab')
        with open('setup_fs_matlab.sh','w') as f:
            f.write(export_FreeSurfer_cmd+"\n")
            f.write(source_FreeSurfer_cmd+"\n")
            f.write("fs_install_mcr R2014b\n")
        system("chmod +x setup_fs_matlab.sh")
        system("./setup_fs_matlab.sh")

