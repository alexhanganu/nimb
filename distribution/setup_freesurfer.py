#!/usr/bin/env python
# coding: utf-8
# 2020.08.12


from os import path, makedirs, chdir, system, remove
import time

class SETUP_FREESURFER():

    def __init__(self, vars):

        self.NIMB_HOME                = vars['local']['NIMB_PATHS']['NIMB_HOME']
        self.FREESURFER_HOME          = vars['local']['FREESURFER']['FREESURFER_HOME']
        self.freesurfer_download_path = vars['local']['FREESURFER']['freesurfer_download_path']
        self.matlab_download_path     = vars['local']['FREESURFER']['matlab_download_path']


        if not path.exists(self.FREESURFER_HOME):
            print("installing freesurfer")
            self.freesurfer_install()
            print('FINISHED Installing and Setting Up FreeSurfer')
        if not path.exists(path.join(self.FREESURFER_HOME, 'MCRv84')):
            print("installing MATLAB")
            self.matlab_install()
            print('FINISHED Installing MATLAB')
            print('writing license file')
            self.create_license_file(vars['local']['FREESURFER']['freesurfer_license'])


    def freesurfer_install(self):
        chdir(self.NIMB_HOME)
        print('downloading freesurfer')
        installer = self.freesurfer_download_path.split("/")[-1]
        try:
            system('wget '+self.freesurfer_download_path)
            while not path.isfile(path.join(self.NIMB_HOME, installer)):
                time.sleep(1000)
        except Exception:
            system('curl -o '+installer+' '+self.freesurfer_download_path)
            while not path.isfile(path.join(self.NIMB_HOME, installer)):
                time.sleep(1000)

        print('extracting freesurfer')
        system('tar -C '+self.FREESURFER_HOME.replace('freesurfer','')+' -xvf '+installer)

        if path.exists(self.FREESURFER_HOME):
            print('removing installer')
            remove(installer)
        else:
            print('something wrong, please review')


    def matlab_install(self):
        chdir(self.FREESURFER_HOME)
        print('downloading matlab')
        installer = self.matlab_download_path.split("/")[-1]
        system("wget "+self.matlab_download_path)

        print('installing matlab')
        system('unzip '+installer)
        system("./install -mode silent -agreeToLicense yes -destinationFolder " + path.join(self.FREESURFER_HOME, 'MCRv84'))

        print('removing matlab installer')
        remove(installer)


    def create_license_file(self, fs_license):
        print('creating freesurfer license.txt file for FreeSurfer 7.1.1')
        if path.isfile(path.join(self.FREESURFER_HOME, 'license.txt')):
            system("mv "+path.join(self.FREESURFER_HOME, 'license.txt')+" "+path.join(self.FREESURFER_HOME, 'license_freesurfer.txt'))
        with open(path.join(self.FREESURFER_HOME, 'license.txt'), 'w') as f:
            for line in fs_license:
                f.write(line + '\n')






'''
script used for freesurer 7.0 for cedar specifically

        chdir(path.join(FREESURFER_HOME, 'bin'))

        remove('run_SegmentSubject.sh')
        system(
            'curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/BrainstemSS/linux_x86_64/run_SegmentSubject.sh -o run_SegmentSubject.sh')
        system('chmod +x run_SegmentSubject.sh')

        remove('segmentBS.sh')
        system(
            'curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/BrainstemSS/segmentBS.sh -o segmentBS.sh')
        system('chmod +x segmentBS.sh')

        remove('run_SegmentSubfieldsT1Longitudinal.sh')
        system(
            'curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/HippoSF/linux_x86_64/run_SegmentSubfieldsT1Longitudinal.sh -o run_SegmentSubfieldsT1Longitudinal.sh')
        system('chmod +x run_SegmentSubfieldsT1Longitudinal.sh')

        remove('run_segmentSubjectT1T2_autoEstimateAlveusML.sh')
        system(
            'curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/HippoSF/linux_x86_64/run_segmentSubjectT1T2_autoEstimateAlveusML.sh -o run_segmentSubjectT1T2_autoEstimateAlveusML.sh')
        system('chmod +x run_segmentSubjectT1T2_autoEstimateAlveusML.sh')

        remove('run_segmentSubjectT1_autoEstimateAlveusML.sh')
        system(
            'curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/HippoSF/linux_x86_64/run_segmentSubjectT1_autoEstimateAlveusML.sh -o run_segmentSubjectT1_autoEstimateAlveusML.sh')
        system('chmod +x run_segmentSubjectT1_autoEstimateAlveusML.sh')

        remove('run_segmentSubjectT2_autoEstimateAlveusML.sh')
        system(
            'curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/HippoSF/linux_x86_64/run_segmentSubjectT2_autoEstimateAlveusML.sh -o run_segmentSubjectT2_autoEstimateAlveusML.sh')
        system('chmod +x run_segmentSubjectT2_autoEstimateAlveusML.sh')

        remove('segmentHA_T1.sh')
        system(
            'curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/HippoSF/segmentHA_T1.sh -o segmentHA_T1.sh')
        system('chmod +x segmentHA_T1.sh')

        remove('segmentHA_T1_long.sh')
        system(
            'curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/HippoSF/segmentHA_T1_long.sh -o segmentHA_T1_long.sh')
        system('chmod +x segmentHA_T1_long.sh')

        remove('segmentHA_T2.sh')
        system(
            'curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/HippoSF/segmentHA_T2.sh -o segmentHA_T2.sh')
        system('chmod +x segmentHA_T2.sh')

        remove('run_SegmentThalamicNuclei.sh')
        system(
            'curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/ThalamicNuclei/linux_x86_64/run_SegmentThalamicNuclei.sh -o run_SegmentThalamicNuclei.sh')
        system('chmod +x run_SegmentThalamicNuclei.sh')

        remove('segmentThalamicNuclei.sh')
        system(
            'curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/ThalamicNuclei/segmentThalamicNuclei.sh -o segmentThalamicNuclei.sh')
        system('chmod +x segmentThalamicNuclei.sh')

        system(
            'curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/scripts/fs_run_from_mcr -o fs_run_from_mcr')
        system('chmod +x fs_run_from_mcr')
'''
