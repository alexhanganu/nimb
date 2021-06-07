#!/bin/python

mr_types_2exclude = ['calibration','localizer','loc',
                     'cbf','isotropic','fractional','average_dc',
                     'perfusion','tse','survey','scout','hippo',
                     'pasl','multi_reset','dual_echo','gre',]

mr_modalities = {'flair' :['flair',],
                 'dwi'   :['hardi','dti','diffus'],
                 'bold'  :['resting_state_fmri','rsfmri','mocoseries', 'rest'],
                 'fmap'  :['field_map','field_mapping','fieldmap'],
                 't1'    :['t1','spgr','rage'],
                 't2'    :['t2',],
                 'pd'    :['pd',],
                 'swi'   :['swi',]
                }

BIDS_types = {'anat':['t1','flair','t2', 'swi', 'pd'],
              'dwi' :['dwi','bval','bvec'],
              'func':['bold','rsfmri'],
              'fmap':['fmap',]
                }
