#!/bin/python
# 2020.06.12

from os import path, system, mkdir
from sys import argv

import var, cdb
_, _, _, SUBJECTS_DIR, _, _, _, _ = var.get_vars()



def run_make_masks(subjid):

    print('subject id is: '+subjid)
    subj_dir = path.join(SUBJECTS_DIR,subjid)

    open(path.join(subj_dir,'scripts','IsRunning.lh+rh')).close()


    mask_dir = path.join(subj_dir,'masks')
    if not path.isdir(mask_dir):
        mkdir(mask_dir)

    for structure in var.masks:
        aseg_mgz = path.join(subj_dir,'mri','aseg.mgz')
        orig001_mgz = path.join(subj_dir,'mri','orig','001.mgz')
        mask_mgz = path.join(mask_dir,structure+'.mgz')
        mask_nii = path.join(mask_dir,structure+'.nii')
        system('mri_binarize --match '+str(cdb.get_mask_codes(structure))+' --i '+aseg_mgz+' --o '+mask_mgz)
        system('mri_convert -rl '+orig001_mgz+' -rt nearest '+mask_mgz+' '+mask_nii)
    system('rm '+path.join(subj_dir,'scripts','IsRunning.lh+rh'))

if __name__ == '__main__':
    run_make_masks(argv[1])