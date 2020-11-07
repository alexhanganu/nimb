#!/bin/python
# 2020.09.04

from os import path, system, mkdir
from sys import argv
import sys
from pathlib import Path
import argparse

class GetMasks:
    '''
    extract the masks for defined regions
    args: SUBJECTS_DIR (where the subject is located)
          MASKS region codes to be extracted, as per FreeSurferColorLUT.txt
    return: $SUBJECTS_DIR/SUBJECT/masks/mask.nii
    '''

    def __init__(self, vars_fs, masks = 'all'):
        self.SUBJECTS_DIR = vars_fs['FS_SUBJECTS_DIR']
        self.masks        = masks
        self.all_codes    = self.read_FreeSurferColorLUT()
        self.codes        = self.get_codes()

    def run_make_masks(self,subjid):

        print('subject id is: '+subjid)
        subj_dir = path.join(self.SUBJECTS_DIR, subjid)

        open(path.join(subj_dir, 'scripts', 'IsRunning.lh+rh')).close()


        mask_dir = path.join(subj_dir,'masks')
        if not path.isdir(mask_dir):
            mkdir(mask_dir)

        for structure in self.codes():
            aseg_mgz = path.join(subj_dir, 'mri', 'aseg.mgz')
            orig001_mgz = path.join(subj_dir, 'mri', 'orig', '001.mgz')
            mask_mgz = path.join(mask_dir, structure+'.mgz')
            mask_nii = path.join(mask_dir, structure+'.nii')
            system('mri_binarize --match {0} --i {1} --o {2}'.format(str(self.codes(structure)), aseg_mgz, mask_mgz))
            system('mri_convert -rl {0} -rt nearest{1} {2}'.format(orig001_mgz, mask_mgz, mask_nii))
        system('rm {}'.format(path.join(subj_dir,'scripts', 'IsRunning.lh+rh')))

    def get_codes(self):
        if self.masks == 'subcortical':
            return self.all_codes.valus().tolist()
        if self.masks == 'cortical':
            return self.all_codes.valus().tolist()
        if self.masks == 'cerebralWM':
            return [2, 41, 77, 251, 252, 253, 254, 255]
        if self.masks == 'allWM':
            return [2, 41, 77, 251, 252, 253, 254, 255, 7, 46]

    def read_FreeSurferColorLUT(self):
        codes = dict()
        file = '/media/g/freesurfer/FreeSurferColorLUT.txt'
        for line in open(file,'r').readlines():#[3:89]:
            if len(line) > 1:
                aslist = [i for i in line.split(' ') if str(i) != '']
                if '#' not in aslist[0]:
                    codes[aslist[1]] = aslist[0]
        return codes


def get_parameters(projects):
    """get parameters for nimb"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-project", required=False,
        default=projects[:1][0],
        choices = projects,
        help="names of projects located in credentials_path.py/nimb/projects.json -> PROJECTS",
    )

    parser.add_argument(
        "-masks", required=False,
        default='all',
        choices = ['all'],
        help="names of masks to be extracted, currently only all subcortical are extracted,"
    )

    params = parser.parse_args()
    return params


# THIS IS a list of subcortical codes, present in read_FreeSurferColorLUT()
# {'left_hippocampus':17,'right_hippocampus':53,
#                     'left_thalamus':10,'right_thalamus':49,'left_caudate':11,'right_caudate':50,
#                     'left_putamen':12,'right_putamen':51,'left_pallidum':13,'right_pallidum':52,
#                     'left_amygdala':18,'right_amygdala':54,'left_accumbens':26,'right_accumbens':58,
#                     'left_hippocampus_CA2':550,'right_hippocampus_CA2':500,
#                     'left_hippocampus_CA1':552,'right_hippocampus_CA1':502,
#                     'left_hippocampus_CA4':556,'right_hippocampus_CA4':506,
#                     'left_hippocampus_fissure':555,'right_hippocampus_fissure':505,
#                     'left_amygdala_subiculum':557,'right_amygdala_subiculum':507,
#                     'left_amygdala_presubiculum':554,'right_amygdala_presubiculum':504,
#                     }

def initiate_fs_from_sh(vars_local):
    """
    FreeSurfer needs to be initiated with source and export
    this functions tries to automate it
    """
    sh_file = path.join(vars_local["NIMB_PATHS"]["NIMB_tmp"], 'source_fs.sh')
    with open(sh_file, 'w') as f:
        f.write(vars_local["FREESURFER"]["export_FreeSurfer_cmd"]+'\n')
        f.write("export SUBJECTS_DIR="+vars_local["FREESURFER"]["FS_SUBJECTS_DIR"]+'\n')
        f.write(vars_local["FREESURFER"]["source_FreeSurfer_cmd"]+'\n')
    system("chmod +x {}".format(sh_file))
    return ("source {}".format(sh_file))




if __name__ == '__main__':


    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[2]
    sys.path.append(str(top))

    import subprocess
    # from distribution.logger import Log
    from setup.get_vars import Get_Vars, SetProject
    getvars      = Get_Vars()
    vars_local   = getvars.location_vars['local']
    fs_start_cmd = initiate_fs_from_sh(vars_local)

    print('please initiate freesurfer using the command: \n    {}'.format(fs_start_cmd))
    try:
        subprocess.run(['mri_info'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    except Exception as e:
        print(e)
        print('please initiate freesurfer using the command: \n    {}'.format(fs_start_cmd))

    print('extracting masks')
    GetMasks(vars_local["FREESURFER"]).run_make_masks(argv[1])
