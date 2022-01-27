# coding: utf-8
# 2020.09.02

import os
import sys

import time
import shutil
import json

from setup.interminal_setup import get_yes_no 
from distribution.utilities import chk_dir_is_writable, makedir_ifnot_exist


class SETUP_FREESURFER():

    def __init__(self, vars, default):

        self.NIMB_tmp            = vars['local']['NIMB_PATHS']['NIMB_tmp']
        self.FS_vars              = vars['local']['FREESURFER'] 
        self.FREESURFER_HOME      = self.FS_vars['FREESURFER_HOME']
        self.centos_version       = default.centos_version #'7'
        self.freesurfer_version   = default.freesurfer_version
        # freesurfer_version        = self.FS_vars['freesurfer_version']

        if not os.path.exists(self.FREESURFER_HOME):
            print("freesurfer requires to be installed")
            if get_yes_no('    do you want to install FreeSurfer? (y/n)') == 1:
                if chk_dir_is_writable(self.FREESURFER_HOME.replace('freesurfer','')):
                        self.freesurfer_install()
                        self.check_freesurfer_license(self.FS_vars['freesurfer_license'])
                        self.check_matlab_installation('install')
                        self.check_matlab_installation('none')
                        print('FINISHED Installing')
                else:
                    print(f"    installation folder is not writable: {self.FREESURFER_HOME.replace('freesurfer','')}. Sorry!")
                    print(f"    please change the permissions with the command:")
                    print(f"        sudo chmod 757 -R {self.FREESURFER_HOME.replace('freesurfer','')}")
                    print(f"        rerun nimb to install FreeSurfer")
                    print(f"        for SECURITY measures, change back permissions to the main folder:")
                    print(f"        sudo chmod 755 -R {self.FREESURFER_HOME.replace('freesurfer','')}")
                    print(f"        change permissions to the FREESURFER_HOME folder to allow files to be written by FreeSurfer:")
                    print(f"        sudo chmod 757 -R {self.FREESURFER_HOME}")
                    print("THANK YOU for using nimb !")
                    sys.exit()
            else:
                print("THANK YOU for using nimb !")
                sys.exit()
        else:
            print(f"    freesurfer folder exists: {self.FREESURFER_HOME}")
            self.check_freesurfer_license(self.FS_vars['freesurfer_license'])
            self.check_matlab_installation('install')
            self.check_matlab_installation('none')


    def check_matlab_installation(self, action):
        if not os.path.exists(os.path.join(self.FREESURFER_HOME, 'MCRv84')):
            print('    Matlab is required to perform processing of brainstem, hippocampus, amygdala and thalamus')
            if action == 'install':
                self.matlab_install(self.FS_vars['export_FreeSurfer_cmd'],
                                    self.FS_vars['source_FreeSurfer_cmd'])
            else:
                print(f'    sorry, something is wrong, cannot install MATLAB')
        else:
            print('FINISHED Installing MATLAB')


    def check_freesurfer_license(self, license):
        file_abspath = os.path.join(self.FREESURFER_HOME, 'license.txt')
        if os.path.isfile(file_abspath):
            print('    creating freesurfer license.txt file for FreeSurfer 7.2')
            try:
                shutil.move(file_abspath,
                            os.path.join(self.FREESURFER_HOME, 'license_freesurfer.txt'))
            except Exception as e:
                print(e)
                os.remove(file_abspath)
        with open(file_abspath, 'w') as f:
            for line in license:
                f.write(line + '\n')


    def freesurfer_install(self):
        """
            extract from archive the downloaded FreeSurfer file
        """
        downloaded, installer_abs_path = self.freesurfer_download()
        if downloaded:
            print('extracting freesurfer')
            os.system(f"tar -C {self.FREESURFER_HOME.replace('freesurfer','')} -xvf {installer_f}")
            os.system(f"chmod -R 777 {os.path.join(self.FREESURFER_HOME, 'subjects')}")

            if self.freesurfer_installed():
                print(f'    installer can be removed at: {installer_abs_path}')
                # os.remove(installer_f)
            else:
                print('    ERROR! something wrong, please review')
        else:
            print('    ERROR! FreeSurfer install file could not be downloaded')


    def freesurfer_download(self):
        """
            downloads the corresponding FreeSurfer file
        """
        with open("nimb/distribution/installers.json", "r") as f:
            installers = json.load(f)
        installer = installers[f"install_fs{self.freesurfer_version}_centos{self.centos_version}"]
        installer_f = installer.split("/")[-1]
        installer_abs_path = os.path.join(self.NIMB_tmp, installer_f)

        if not os.path.exists(installer_abs_path):
            print('downloading freesurfer')
            os.chdir(self.NIMB_tmp)
            try:
                os.system(f'wget {installer}')
                while not os.path.isfile(installer_abs_path):
                    time.sleep(1000)
            except Exception:
                os.system(f'curl -o {installer_f} {installer}')
                while not os.path.isfile(installer_abs_path):
                    time.sleep(1000)
        return True, installer_abs_path


    def freesurfer_installed():
        """
            checks if FreeSurfer has the corresponding files
            implying that the standard version was correctly unarchived
            NOTE: it does not check for Matlab installation
        """
        file = os.path.join(self.FREESURFER_HOME, "FreeSurferEnv.sh")
        if not os.path.isfile(file):
            return False
        return True


    def matlab_install(self,
                        export_FreeSurfer_cmd,
                        source_FreeSurfer_cmd):
        print("        trying to install MATLAB...")
        print(f'        changing location to folder: {self.FREESURFER_HOME}')
        os.chdir(self.FREESURFER_HOME)

        try:
            with open('setup_fs_matlab.sh','w') as f:
                f.write(export_FreeSurfer_cmd+"\n")
                f.write(source_FreeSurfer_cmd+"\n")
                f.write("fs_install_mcr R2014b\n")
            os.system("chmod +x setup_fs_matlab.sh")
            os.system(f"bash /{self.FREESURFER_HOME}/setup_fs_matlab.sh")
        except Exception as e:
            print(e)

        if not os.path.exists(os.path.join(self.FREESURFER_HOME, 'MCRv84')):
            try:
                print("        trying 2nd method:")
                os.system("export_FreeSurfer_cmd")
                os.system("source_FreeSurfer_cmd")
                os.system("fs_install_mcr R2014b")
            except Exception as e:
                print(e)

        if not os.path.exists(os.path.join(self.FREESURFER_HOME, 'MCRv84')):
            print(f'sorry, something whent wrong')
            print(f'    cannot install MATLAB. Try the commands:')
            print(f'    cd {self.FREESURFER_HOME}')
            print(f'    ./setup_fs_matlab.sh')
            print(f'    ALTERNATIVELY, please try:')
            print(f'        cd {self.FREESURFER_HOME}')
            print(f'        {export_FreeSurfer_cmd}')
            print(f'        {source_FreeSurfer_cmd}')
            print(f'        fs_install_mcr R2014b')

