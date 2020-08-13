#!/usr/bin/env python
# coding: utf-8
# 2020.08.12
freesurfer_download_path = "https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.1.1/freesurfer-linux-centos7_x86_64-7.1.1.tar.gz"
freesurfer_install_file = "freesurfer-linux-centos7_x86_64-7.1.1.tar.gz"
matlab_download_path = "https://ssd.mathworks.com/supportfiles/downloads/R2014b/deployment_files/R2014b/installers/glnxa64/MCR_R2014b_glnxa64_installer.zip"
matlab_installer = "MCR_R2014b_glnxa64_installer.zip"

from os import path, makedirs, chdir, system, remove
import time

class SETUP_FREESURFER():

    def __init__(self, FREESURFER_HOME, NIMB_HOME, fs_license):
        self.FREESURFER_HOME = FREESURFER_HOME
        self.NIMB_HOME = NIMB_HOME

        if not path.exists(self.FREESURFER_HOME):
            print("installing freeaurfer")
            self.freesurfer_install()
            self.matlab_install()
            print('FINISHED Installing and Setting Up FreeSurfer')
        elif not path.exists(path.join(FREESURFER_HOME, 'MCRv84')):
            self.matlab_install()
            print('FINISHED Installing MATLAB')
        else:
            print('writing license file')
            self.create_license_file(fs_license)
            return True


    def freesurfer_install(self):
        chdir(self.NIMB_HOME)
        print('downloading freesurfer')
        try:
            system('wget '+freesurfer_download_path)
            while not path.isfile(path.join(self.NIMB_HOME, freesurfer_install_file)):
                time.sleep(1000)
        except Exception:
            system('curl -o '+freesurfer_install_file+' '+freesurfer_download_path)
            while not path.isfile(path.join(self.NIMB_HOME, freesurfer_install_file)):
                time.sleep(1000)

        print('extracting freesurfer')
        system('tar -C '+self.FREESURFER_HOME.replace('freesurfer','')+' -xvf '+freesurfer_install_file)

        if path.exists(self.FREESURFER_HOME):
            print('removing installer')
            remove(freesurfer_install_file)
        else:
            print('something wrong, please review')


    def matlab_install(self):
        chdir(self.FREESURFER_HOME)
        print('downloading matlab')
        system("wget "+matlab_download_path)

        print('installing matlab')
        system('unzip '+matlab_installer)
        system("./install -mode silent -agreeToLicense yes -destinationFolder " + path.join(self.FREESURFER_HOME, 'MCRv84'))

        print('removing matlab installer')
        remove(matlab_installer)


    def create_license_file(self, fs_license):
        print('creating freesurfer .license file')
        with open(path.join(self.FREESURFER_HOME, '.license'), 'w') as f:
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
