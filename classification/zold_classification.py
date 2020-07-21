#!/bin/python
#Alexandru Hanganu, 2019 November 6
'''
temporary file, trying to adjust the registration of participants until the bids version
is ready

'''

from os import listdir, path, system
from var import LONGITUDINAL_DEFINITION
from cdb import get_vars

_, _ , _, _ , _, dir_new_subjects = get_vars()


def get_t1_flair_t2_from_subjects2process(subjid):
        lssubjdir=listdir(dir_new_subjects)
        lsi = {'t1':[],'flair':[],'t2':[]}
        for LONG in LONGITUDINAL_DEFINITION:
            if LONG in subjid:
                longitudinal = True
                longitudinal_name = LONG
                break
            else:
                longitudinal = False
        if longitudinal:
            for DIR in lssubjdir:
                if subjid in DIR and longitudinal_name in DIR:
                        if '_t1' in DIR:
                            lsi['t1'].append(DIR)
                        if '_flair' in DIR or '_t2' in DIR:
                            lsi['flair'].append(DIR)
                        if '_t2' in DIR:
                            lsi['t2'].append(DIR)
        else:
            for DIR in lssubjdir:
                for LONG in LONGITUDINAL_DEFINITION:
                    if LONG in DIR:
                        DIR_not_Long = False
                        break
                    else:
                        DIR_not_Long = True
                if DIR_not_Long:
                    if subjid in DIR:
                        print(DIR)
                        if '_t1' in DIR:
                            lsi['t1'].append(DIR)
                         if '_flair' in DIR:
                            lsi['flair'].append(DIR)
                        if '_t2' in DIR:
                            lsi['t2'].append(DIR)
        T1_PATH_f = ''
        Flair_PATH_f = ''
        T2_PATH_f = ''

        t=0
        while t<len(lsi['t1']):
            x = [lsi['t1'][t]]
            dir2read = dir_new_subjects+x[0]+'/'
            if path.isdir(dir2read):
                file_names=listdir(dir2read)
                if len([f for f in file_names if f.endswith('.dcm')]):
                    if len(file_names) > 15:
                        T1_PATH_f= dir2read+sorted(file_names)[0]
                else:
                    print('ERROR: No dcm files in the folder: ', dir2read)              
            elif any('.nii' or '.nii.gz' in i for i in x):
                T1_PATH_f=(dir_new_subjects+x[0])        
            elif any('.mnc' or '.mnc.gz' in i for i in x):
                from os import system
                system('mnc2nii '+dir_new_subjects+x[0]+' '+dir_new_subjects+subjid+'_t1.nii.gz')
                T1_PATH_f=(dir_new_subjects+subjid+'_t1.nii.gz')        
            t=t+1
        fl=0
        while fl<len(lsi['flair']):
            x = [lsi['flair'][fl]]
            dir2read = dir_new_subjects+x[0]+'/'
            if path.isdir(dir2read):
                file_names=listdir(dir2read)
                if len([f for f in file_names if f.endswith('.dcm')]):
                    if len(file_names) > 15:
                        Flair_PATH_f= dir2read+sorted(file_names)[0]
                else:
                    print('ERROR: No dcm files in the folder: ', dir2read)              
            elif any('.nii' or '.nii.gz' in i for i in x):
                Flair_PATH_f=(dir_new_subjects+x[0])        
            elif any('.mnc' or '.mnc.gz' in i for i in lssubjdir):
                from os import system
                system('mnc2nii '+dir_new_subjects+x[0]+' '+dir_new_subjects+subjid+'_t1.nii.gz')
                Flair_PATH_f=(dir_new_subjects+subjid+'_t1.nii.gz')        
            fl=fl+1
        t2=0
        while t2<len(lsi['flair']):
            x = [lsi['flair'][t2]]
            dir2read = dir_new_subjects+x[0]+'/'
            if path.isdir(dir2read):
                file_names=listdir(dir2read)
                if len([f for f in file_names if f.endswith('.dcm')]):
                    if len(file_names) > 15:
                        Flair_PATH_f= dir2read+sorted(file_names)[0]
                else:
                    print('ERROR: No dcm files in the folder: ', dir2read)              
            elif any('.nii' or '.nii.gz' in i for i in x):
                Flair_PATH_f=(dir_new_subjects+x[0])        
            elif any('.mnc' or '.mnc.gz' in i for i in lssubjdir):
                from os import system
                system('mnc2nii '+dir_new_subjects+x[0]+' '+dir_new_subjects+subjid+'_t1.nii.gz')
                Flair_PATH_f=(dir_new_subjects+subjid+'_t1.nii.gz')        
            t2=t2+1
        return T1_PATH_f, Flair_PATH_f, T2_PATH_f
