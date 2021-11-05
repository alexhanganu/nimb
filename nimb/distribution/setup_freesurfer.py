# coding: utf-8
# 2020.09.02

import os
import time
import shutil
import json

class SETUP_FREESURFER():

    def __init__(self, vars, default):

        self.NIMB_HOME            = vars['local']['NIMB_PATHS']['NIMB_HOME']
        self.FS_vars              = vars['local']['FREESURFER'] 
        self.FREESURFER_HOME      = self.FS_vars['FREESURFER_HOME']
        self.centos_version       = default.centos_version #'7'
        self.freesurfer_version   = default.freesurfer_version
        # freesurfer_version        = self.FS_vars['freesurfer_version']

        if not os.path.exists(self.FREESURFER_HOME):
            print("freesurfer requires to be installed")
            self.freesurfer_install()
            print('FINISHED Installing')
        self.check_freesurfer_license(self.FS_vars['freesurfer_license'])
        self.check_matlab_installation('install')
        self.check_matlab_installation('none')

    def check_matlab_installation(self, action):
        if not os.path.exists(os.path.join(self.FREESURFER_HOME, 'MCRv84')):
            print('Matlab is required to perform processing of brainstem, hippocampus, amygdala and thalamus')
            if action == 'install':
                print("trying to install MATLAB...")
                self.matlab_install(self.FS_vars['export_FreeSurfer_cmd'],
                                    self.FS_vars['source_FreeSurfer_cmd'])
            else:
                print(f'sorry, something whent wrong, cannot install MATLAB. Try the commands: \n\
                cd {self.FREESURFER_HOME}\n\
                ./setup_fs_matlab.sh')
        else:
            print('FINISHED Installing MATLAB')

    def check_freesurfer_license(self, license):
        print('creating freesurfer license.txt file for FreeSurfer 7.1.1')
        if os.path.isfile(os.path.join(self.FREESURFER_HOME, 'license.txt')):
            try:
                shutil.move(os.path.join(self.FREESURFER_HOME, 'license.txt'),
                            os.path.join(self.FREESURFER_HOME, 'license_freesurfer.txt'))
            except Exception as e:
                print(e)
                os.remove(os.path.join(self.FREESURFER_HOME, 'license.txt'))
        with open(os.path.join(self.FREESURFER_HOME, 'license.txt'), 'w') as f:
            for line in license:
                f.write(line + '\n')

    def freesurfer_install(self):
        installer = self.fs_download_path()
        os.chdir(self.NIMB_HOME)
        print('downloading freesurfer')
        installer_f = installer.split("/")[-1]
        try:
            os.system('wget '+installer)
            while not os.path.isfile(os.path.join(self.NIMB_HOME, installer_f)):
                time.sleep(1000)
        except Exception:
            os.system('curl -o '+installer_f+' '+installer)
            while not os.path.isfile(os.path.join(self.NIMB_HOME, installer_f)):
                time.sleep(1000)

        print('extracting freesurfer')
        os.system(f"tar -C {self.FREESURFER_HOME.replace('freesurfer','')} -xvf {installer_f}")
        os.system(f"chmod -R 777 {os.path.join(self.FREESURFER_HOME, 'subjects')}")

        if os.path.exists(self.FREESURFER_HOME):
            print('removing installer')
            os.remove(installer_f)
        else:
            print('something wrong, please review')

    def fs_download_path(self):
        # path2fs = "https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/{}/freesurfer-linux-centos{}_x86_64-{}.tar.gz".format(
        #             self.freesurfer_version, self.centos_version, self.freesurfer_version)
        with open("nimb/distribution/installers.json", "r") as f:
            installers = json.load(f)
        return installers[f"install_fs{self.freesurfer_version}_centos{self.centos_version}"]

    def matlab_install(self, export_FreeSurfer_cmd, source_FreeSurfer_cmd):
        os.chdir(self.FREESURFER_HOME)
        print('installing matlab')
        with open('setup_fs_matlab.sh','w') as f:
            f.write(export_FreeSurfer_cmd+"\n")
            f.write(source_FreeSurfer_cmd+"\n")
            f.write("fs_install_mcr R2014b\n")
        os.system("chmod +x setup_fs_matlab.sh")
        os.system("./setup_fs_matlab.sh")

