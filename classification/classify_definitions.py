#!/bin/python

mr_types_2exclude = ['calibration','localizer','loc','moco','perfusion','tse',
                    'survey','scout','hippo','cbf','isotropic','fractional',
                    'pasl','multi_reset','dual_echo','gre','average_dc']

mr_types = {'flair'  :['flair',],
            'dwi'     :['hardi','dti','diffus'],
            'rsfmri'  :['resting_state_fmri','rsfmri'],
            'fieldmap':['field_map','field_mapping','fieldmap'],
            't1'      :['t1','spgr','rage'],
            't2'      :['t2',],}

BIDS_groups = {'anat':['t1','flair','t2'],
               'dwi':['dwi','bval','bvec'],
               'func':['rsfmri','fieldmap',]}
