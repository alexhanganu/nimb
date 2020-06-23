#!/usr/bin/env python
# coding: utf-8
# 2020.06.23

"""
files that must be copied to the cluster:
crun.py, crunfs.py, cdb.py, cwalltime.py, run_masks.py, mri_info

For the license: USER provides the license details in the GUI and they are 
added in this script.
"""

fs_license = ("hanganu.alexandru@gmail.com",
"11009",
"*C1QZcOiGGrPE",
"FSUt0BPqKfdQc",)

from os import path, makedirs, chdir, system, remove
import os, shutil, time

cmaindir = "/home/mellahs/projects/def-bellevil/"
cscratch_dir = "/scratch"

pbs_file_header = (
            '#!/bin/sh',
            '#SBATCH --account=def-bellevil',
            '#SBATCH --mem=8G',
            '#SBATCH --time=03:00:00',
            '#SBATCH --output=/scratch/mellahs/a_tmp/running_output.out')
python_cmd = 'module load python/3.8.2'
export_FreeSurfer_cmd = 'export FREESURFER_HOME='+path.join(cmaindir,'freesurfer')
source_FreeSurfer_cmd = '$FREESURFER_HOME/SetUpFreeSurfer.sh'

pbs_files_and_content = {'run.sh':('cd '+path.join(cmaindir,'a'),python_cmd,'python crun.py')}

for subDIR in (path.join(cmaindir,'subjects'),
                path.join(cmaindir,'a'),
                path.join(cscratch_dir,'a_tmp'),
                path.join(cmaindir,'fs-subjects'),
                path.join(cmaindir,'subjects_processed')):
    if not path.exists(subDIR):
        makedirs(subDIR)
for file in ('crun.py','crunfs.py','cdb.py','cwalltime.py','run_masks.py','mri_info'):
    if path.exists(path.join(cmaindir,file)):
        shutil.move(path.join(cmaindir,file), path.join(cmaindir,'a',file))

if not path.exists(path.join(cmaindir,'a','__init__.py')):
    open(path.join(cmaindir,'a','__init__.py'),'w').close()
with open(path.join(cmaindir,'a','var.py'),'w') as f:
    f.write('#!/bin/python\n')
    f.write('cname="cedar"\n')
    f.write('cusers_list=["mellahs",]\n')
    f.write('supervisor_ccri="yyc"\n')
    f.write('max_nr_running_batches = 100\n')
    f.write('cmaindir = "'+cmaindir+'"\n')
    f.write('cscratch_dir = "'+cscratch_dir+'"\n')
    f.write("process_order = ['registration','autorecon1','autorecon2','autorecon3','qcache','brstem','hip','tha',]\n")
    f.write('long_name = "ses-1"\n')
    f.write('base_name = "base"\n')
    f.write('DO_LONG = False\n')
    f.write("text4_scheduler = ('#!/bin/sh','#SBATCH --account=def-bellevil','#SBATCH --mem=8G',)\n")
    f.write('batch_walltime_cmd = "#SBATCH --time="\n')
    f.write('max_walltime = "99:00:00"\n')
    f.write('batch_walltime = "03:00:00"\n')
    f.write('batch_output_cmd = "#SBATCH --output="\n')
    f.write('submit_cmd = "sbatch"\n')
    f.write('freesurfer_version = 7\n')
    f.write('archive_processed = False\n')
    f.write('masks = []\n')

    f.write('\n')
    f.write('from os import path, getuid, getenv\n')
    f.write('\n')
    f.write('def get_vars():\n')
    f.write('\n')
    f.write('    cuser = ''\n')
    f.write('    try:\n')
    f.write('        import pwd\n')
    f.write('        user = pwd.getpwuid( getuid() ) [0]\n')
    f.write('    except ImportError:\n')
    f.write('        print(e)\n')
    f.write('    if not cuser:\n')
    f.write('        for user in cusers_list:\n')
    f.write("            if user in getenv('HOME'):\n")
    f.write('                cuser = user\n')
    f.write('                break\n')
    f.write('    else:\n')
    f.write("        print('ERROR - user not defined')\n")
    f.write('\n')
    f.write("    nimb_dir=path.join(cmaindir,'a/')\n")
    f.write("    dir_new_subjects=path.join(cmaindir,'subjects/')\n")
    f.write("    nimb_scratch_dir=path.join(cscratch_dir,cuser,'a_tmp/')\n")
    f.write("    SUBJECTS_DIR = path.join(cmaindir,'fs-subjects/')\n")
    f.write("    processed_SUBJECTS_DIR = path.join(cmaindir,'subjects_processed/')\n")
    f.write("    export_FreeSurfer_cmd = 'export FREESURFER_HOME='+path.join(cmaindir,'freesurfer')\n")
    f.write("    source_FreeSurfer_cmd = '$FREESURFER_HOME/SetUpFreeSurfer.sh'\n")

    f.write("    return cuser, nimb_dir, nimb_scratch_dir, SUBJECTS_DIR, processed_SUBJECTS_DIR, dir_new_subjects, export_FreeSurfer_cmd, source_FreeSurfer_c$\n")

with open(path.join(cmaindir,'freesurfer','.license'),'w') as f:
    for line in fs_license:
        f.write(line+'\n')



    for file in pbs_files_and_content:
        with open(path.join(cmaindir,'a',file),'w') as f:
            for line in pbs_file_header:
                f.write(line+'\n')
            f.write('\n')
            for line in pbs_files_and_content[file]:
                f.write(line+'\n')

if not path.exists(path.join(cmaindir,'freesurfer')):
    chdir(cmaindir)
    system('curl "https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.1.0/freesurfer-linux-centos7_x86_64-7.1.0.tar.gz" -o "freesurfer_installation.tar.gz" ')
    while not path.isfile(path.join(cmaindir,'freesurfer_installation.tar.gz')):
        time.sleep(1000)
    system('tar xvf freesurfer_installation.tar.gz')
    remove('freesurfer_installation.tar.gz')
    chdir(path.join(cmaindir,'freesurfer','bin'))

    remove('run_SegmentSubject.sh')
    system('curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/BrainstemSS/linux_x86_64/run_SegmentSubject.sh -o run_SegmentSubject.sh')
    system('chmod +x run_SegmentSubject.sh')

    remove('segmentBS.sh')
    system('curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/BrainstemSS/segmentBS.sh -o segmentBS.sh')
    system('chmod +x segmentBS.sh')

    remove('run_SegmentSubfieldsT1Longitudinal.sh')
    system('curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/HippoSF/linux_x86_64/run_SegmentSubfieldsT1Longitudinal.sh -o run_SegmentSubfieldsT1Longitudinal.sh')
    system('chmod +x run_SegmentSubfieldsT1Longitudinal.sh')

    remove('run_segmentSubjectT1T2_autoEstimateAlveusML.sh')
    system('curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/HippoSF/linux_x86_64/run_segmentSubjectT1T2_autoEstimateAlveusML.sh -o run_segmentSubjectT1T2_autoEstimateAlveusML.sh')
    system('chmod +x run_segmentSubjectT1T2_autoEstimateAlveusML.sh')

    remove('run_segmentSubjectT1_autoEstimateAlveusML.sh')
    system('curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/HippoSF/linux_x86_64/run_segmentSubjectT1_autoEstimateAlveusML.sh -o run_segmentSubjectT1_autoEstimateAlveusML.sh')
    system('chmod +x run_segmentSubjectT1_autoEstimateAlveusML.sh')

    remove('run_segmentSubjectT2_autoEstimateAlveusML.sh')
    system('curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/HippoSF/linux_x86_64/run_segmentSubjectT2_autoEstimateAlveusML.sh -o run_segmentSubjectT2_autoEstimateAlveusML.sh')
    system('chmod +x run_segmentSubjectT2_autoEstimateAlveusML.sh')

    remove('segmentHA_T1.sh')
    system('curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/HippoSF/segmentHA_T1.sh -o segmentHA_T1.sh')
    system('chmod +x segmentHA_T1.sh')

    remove('segmentHA_T1_long.sh')
    system('curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/HippoSF/segmentHA_T1_long.sh -o segmentHA_T1_long.sh')
    system('chmod +x segmentHA_T1_long.sh')

    remove('segmentHA_T2.sh')
    system('curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/HippoSF/segmentHA_T2.sh -o segmentHA_T2.sh')
    system('chmod +x segmentHA_T2.sh')

    remove('run_SegmentThalamicNuclei.sh')
    system('curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/ThalamicNuclei/linux_x86_64/run_SegmentThalamicNuclei.sh -o run_SegmentThalamicNuclei.sh')
    system('chmod +x run_SegmentThalamicNuclei.sh')

    remove('segmentThalamicNuclei.sh')
    system('curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/ThalamicNuclei/segmentThalamicNuclei.sh -o segmentThalamicNuclei.sh')
    system('chmod +x segmentThalamicNuclei.sh')

    system('curl https://raw.githubusercontent.com/freesurfer/freesurfer/dev/scripts/fs_run_from_mcr -o fs_run_from_mcr')
    system('chmod +x fs_run_from_mcr')

shutil.move(path.join(cmaindir,'.license'), path.join(cmaindir,'freesurfer','.license'))
if not path.exists(path.join(cmaindir,'freesurfer','MCRv84')):
    chdir(cmaindir)
    system("curl https://ssd.mathworks.com/supportfiles/downloads/R2014b/deployment_files/R2014b/installers/glnxa64/MCR_R2014b_glnxa64_installer.zip -o installer.zip")
    system('unzip installer.zip')
    system("./install -mode silent -agreeToLicense yes -destinationFolder "+path.join(cmaindir,'freesurfer','MCRv84'))
    print('removing installer')
    remove('installer.zip')

if not path.exists(path.join(cmaindir,'miniconda3')):
    chdir(cmaindir)
    system('curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda3.sh')
    system('chmod +x miniconda3.sh')
    system('./miniconda3.sh -b -p '+path.join(cmaindir, 'miniconda3'))
    remove('miniconda3.sh')
    cmd = 'export PATH=~..'+path.join(cmaindir,'miniconda3')+'/bin:$PATH >> $HOME/.bashrc'
    system('echo "'+cmd+'"')
    system('/miniconda3/bin/conda init')
    system('./miniconda3/bin/conda config --set report_errors false')
    system('./miniconda3/bin/conda install -y dcm2niix')
    system('./miniconda3/bin/conda install -y dcm2bids')
    system('./miniconda3/bin/conda install -y paramiko')
print('SETUP FINISHED')
