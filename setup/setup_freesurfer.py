#!/usr/bin/env python
# coding: utf-8
# 2020.08.09

def setup_freesurfer(FREESURFER_HOME, NIMB_HOME, fs_license):
    from os import path, makedirs, chdir, system, remove
    import time


    if not path.exists(FREESURFER_HOME):
        chdir(NIMB_HOME)
        system(
            'curl "https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.1.0/freesurfer-linux-centos7_x86_64-7.1.0.tar.gz" -o "freesurfer_installation.tar.gz" ')
        while not path.isfile(path.join(NIMB_HOME, 'freesurfer_installation.tar.gz')):
            time.sleep(1000)
        system('tar xvf freesurfer_installation.tar.gz -'+FREESURFER_HOME.strip('/freesurfer'))
        remove('freesurfer_installation.tar.gz')

        with open(path.join(FREESURFER_HOME, '.license'), 'w') as f:
            for line in fs_license:
                f.write(line + '\n')

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

    if not path.exists(path.join(FREESURFER_HOME, 'MCRv84')):
        chdir(FREESURFER_HOME)
        system(
            "curl https://ssd.mathworks.com/supportfiles/downloads/R2014b/deployment_files/R2014b/installers/glnxa64/MCR_R2014b_glnxa64_installer.zip -o installer.zip")
        system('unzip installer.zip')
        system("./install -mode silent -agreeToLicense yes -destinationFolder " + path.join(FREESURFER_HOME,
                                                                                            'MCRv84'))
        print('removing installer')
        remove('installer.zip')

    if not path.exists(path.join(NIMB_HOME, 'miniconda3')):
        chdir(NIMB_HOME)
        system('curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda3.sh')
        system('chmod +x miniconda3.sh')
        system('./miniconda3.sh -b -p ' + path.join(NIMB_HOME, 'miniconda3'))
        remove('miniconda3.sh')
        cmd = 'export PATH=~..' + path.join(NIMB_HOME, 'miniconda3') + '/bin:$PATH >> $HOME/.bashrc'
        system('echo "' + cmd + '"')
        system('/miniconda3/bin/conda init')
        system('./miniconda3/bin/conda config --set report_errors false')
        system('./miniconda3/bin/conda install -y dcm2niix')
        system('./miniconda3/bin/conda install -y dcm2bids')
        system('./miniconda3/bin/conda install -y -c conda-forge dipy')
        system('./miniconda3/bin/conda install -y pandas')
        system('./miniconda3/bin/conda install -y numpy')
        system('./miniconda3/bin/conda install -y xlrd')
        system('./miniconda3/bin/conda install -y paramiko')
        system('./miniconda3/bin/conda install -y xlsxwriter')
    print(
        'FINISHED Setting Up FreeSurfer and miniconda3 with dcm2niix, dcm2bids, pandas, numpy, xlrd, paramiko and dipy')
