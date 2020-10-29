#!/usr/bin/env python
# coding: utf-8
# 2020.09.02


from os import path, chdir, system, remove
import time, shutil

class SETUP_FREESURFER():

    def __init__(self, vars, installers):

        self.NIMB_HOME            = vars['local']['NIMB_PATHS']['NIMB_HOME']
        self.FS_vars              = vars['local']['FREESURFER'] 
        self.FREESURFER_HOME      = self.FS_vars['FREESURFER_HOME']

        if not path.exists(self.FREESURFER_HOME):
            print("freesurfer requires to be installed")
            self.freesurfer_install(self.FS_vars['freesurfer_version'], installers)
            print('FINISHED Installing')
        self.check_freesurfer_license(self.FS_vars['freesurfer_license'])
        self.check_matlab_installation('install')
        self.check_matlab_installation('none')

    def check_matlab_installation(self, action):
        if not path.exists(path.join(self.FREESURFER_HOME, 'MCRv84')):
            print('Matlab is required to perform processing of brainstem, hippocampus, amygdala and thalamus')
            if action == 'install':
                print("trying to install MATLAB...")
                self.matlab_install(self.FS_vars['export_FreeSurfer_cmd'],
                                    self.FS_vars['source_FreeSurfer_cmd'])
            else:
                print('sorry, something whent wrong, cannot install MATLAB. Try to source freesurfer and run setup_fs_matlab.sh')
        else:
            print('FINISHED Installing MATLAB')

    def check_freesurfer_license(self, license):
        print('creating freesurfer license.txt file for FreeSurfer 7.1.1')
        if path.isfile(path.join(self.FREESURFER_HOME, 'license.txt')):
            try:
                shutil.move(path.join(self.FREESURFER_HOME, 'license.txt'),path.join(self.FREESURFER_HOME, 'license_freesurfer.txt'))
            except Exception as e:
                print(e)
                remove(path.join(self.FREESURFER_HOME, 'license.txt'))
        with open(path.join(self.FREESURFER_HOME, 'license.txt'), 'w') as f:
            for line in license:
                f.write(line + '\n')

    def freesurfer_install(self, freesurfer_version, installers):
        if freesurfer_version == 7:
            installer = installers['freesurfer7.1.1_installer']
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

