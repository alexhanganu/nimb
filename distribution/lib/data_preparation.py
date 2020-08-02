#!/bin/python


try:
    from os import lchmod
except ImportError:
    pass
from os import makedirs, path, listdir
from datetime import datetime
from sys import platform
from . import database

MainFolder = database._get_folder('Main')
DIRs_INCOMING = database._get_folder('MRI')

dirrawdata = MainFolder+'raw_t1/'

def data_preparation(Project):
    id_col = 'id'
    group_col = 'group'

    Project_Data = database._get_Project_Data_d(Project)
    print("Project_Data_d[project]['file_groups'] is not defined")
    file_groups = Project_Data_d[project]['file_groups'] # not available yet

    if len(file_groups)>0:
        print('file groups present, starting making fsgd files')
        try:
            from a.lib import makestats_groups
            status.set('Creating FSGD files for GLM analysis')
            GLM_dir = Project_Data[Project][2]+Project+'/'+str(datetime.now().year)+str(datetime.now().month)+str(datetime.now().day)+'/'
            if not path.isdir(GLM_dir):
                makedirs(GLM_dir)
            makestats_groups.MakeStatsForGroups(GLM_dir, file_groups, id_col, group_col, Project_Data[Project][1])
        except ImportError:
            print('error importing the makestats_groups from a.lib')
            pass
    if platform == 'darwin' or platform == 'linux' or platform == 'linux2':
        if len(listdir(Project_Data[Project][2]))>0 and len(database._get_folder('LocalProcessing'))>0:
            print('GLM dir not empty, local processing present, performing glm')
            try:
                from a.lib import makeglm
                status.set('Performing GLM')
                GLM_dir = Project_Data[Project][2]+Project+'/'
                for folder in listdir(GLM_dir):
                    if 'results' not in listdir(GLM_dir+folder):
                        PATH_4glm = GLM_dir+folder+'/'
                        makeglm.PerformGLM(PATH_4glm, database._get_folder('LocalProcessing'))
                    else:
                        print('results created')
            except ImportError:
                print('ERROR importing makeglm module')
                pass	

def define_SUBJID(DIR, id):
    name=('PDMCI','PD-MCI','PD_MCI', 'pdmci')
    SESSION_names = ['B','C']
    LONGITUDINAL_DEFINITION = ['T2','T3']

    if DIR == 'INCOMING':
                for n in name:
                    if any(n in i for i in id):
                        id=id[0]
                        pos_mci_in_id=[i for i, s in enumerate(id) if 'I' in s]
                        SUBJECT_NR=id[pos_mci_in_id[0]+1:]
                        SUBJECT_NR = SUBJECT_NR.replace('-','').replace('_','')
                        if SUBJECT_NR[0] =='0':
                            SUBJECT_NR = SUBJECT_NR[1:]
                session_ = ''
                for session in SESSION_names:
                    if session in SUBJECT_NR:
                        position = [i for i, s in enumerate(SUBJECT_NR) if session in s]
                        SUBJECT_NR = SUBJECT_NR.replace(SUBJECT_NR[position[0]], '')
                        session_ = session
                for LONG in LONGITUDINAL_DEFINITION:
                            if LONG in SUBJECT_NR:
                                longitudinal = True
                                longitudinal_name = LONG
                                break
                            else:
                                longitudinal = False
                if longitudinal:
                    SUBJECT_NR = SUBJECT_NR.replace(longitudinal_name, '')
                    SUBJECT_ID = 'pdmci'+SUBJECT_NR+longitudinal_name
                    FILE_name = SUBJECT_ID+session_
                else:
                    SUBJECT_ID = 'pdmci'+SUBJECT_NR
                    FILE_name = SUBJECT_ID+session_
    else:
                SUBJECT_ID = id[0].replace(' ','_')
                FILE_name = SUBJECT_ID

    database.update_ls_subj2fs(SUBJECT_ID)

    return(FILE_name)