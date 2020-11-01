#!/bin/python
# 2020.09.04

from os import path, system, mkdir
from sys import argv
from fs_definitions import fs_structure_codes


def run_make_masks(subjid):

    print('subject id is: '+subjid)
    subj_dir = path.join(SUBJECTS_DIR, subjid)

    open(path.join(subj_dir, 'scripts', 'IsRunning.lh+rh')).close()


    mask_dir = path.join(subj_dir,'masks')
    if not path.isdir(mask_dir):
        mkdir(mask_dir)

    for structure in masks:
        aseg_mgz = path.join(subj_dir, 'mri', 'aseg.mgz')
        orig001_mgz = path.join(subj_dir, 'mri', 'orig', '001.mgz')
        mask_mgz = path.join(mask_dir, structure+'.mgz')
        mask_nii = path.join(mask_dir, structure+'.nii')
        system('mri_binarize --match {0} --i {1} --o {2}'.format(str(fs_structure_codes(structure)), aseg_mgz, mask_mgz))
        system('mri_convert -rl {0} -rt nearest{1} {2}'.format(orig001_mgz, mask_mgz, mask_nii))
    system('rm {}'.format(path.join(subj_dir,'scripts', 'IsRunning.lh+rh')))

if __name__ == '__main__':
    run_make_masks(argv[1])
