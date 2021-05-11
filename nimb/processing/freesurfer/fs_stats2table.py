#!/bin/python
'''
Extract the stats data for all subjects located in a folder, to 2/3 excel files

Args:
    PATHstats = path of the folder where the final excel files will be saved
    NIMB_PROCESSED_FS = path to the folder where the FreeSurfer processed subjects are located. These can be 
                        raw folders, or zip archived folders (with .zip as ending)
    data_only_volumes = True or False, is user wants an additional file to constructed that will include only subcortical volumes
Return:
    an excel file with all subjects and all parameters, per sheets
    one big excel file with all parameters on one sheet
'''

from os import path, listdir, sep
import pandas as pd
import numpy as np
import xlsxwriter, xlrd
import json
from fs_definitions import (BS_Hip_Tha_stats_f, brstem_hip_header,
                             segmentation_parameters,
                             segmentations_header, parc_parameters,
                             parc_DK_f2rd, parc_DK_header,
                             parc_DS_f2rd, parc_DS_header)

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def chk_if_all_stats_present(_SUBJECT, stats_dir_path, miss = dict()):
    ''' check if subject has all stats files
    Args:
        _SUBJECT: sub to check, str
        stats_dir_path: path to _SUBJECT + _SUBJECTS
        miss : dictionary with missing data, to be populated
    Return:
        ready: _SUBJECT has all required files and is ready to undergo stats extraction
        miss: newly populated dictionary with missing _SUBJECT or missing files
    '''
    def add_2dict(d, key, val):
        if key not in d:
            d[key] = list()
        if val:
            d[key].append(val)
        return d

    ready = True
    for sheet in BS_Hip_Tha_stats_f:
        try:
            file_with_stats = [i for i in BS_Hip_Tha_stats_f[sheet] if path.exists(path.join(stats_dir_path.replace('/stats',''),i))][0]
            if not file_with_stats:
                logger.info('missing: {}'.format(sheet))
                ready = False
                miss = add_2dict(miss, _SUBJECT, sheet)
        except Exception as e:
            logger.info(e)
            ready = False
            miss = add_2dict(miss, _SUBJECT, sheet)
    if not path.exists(path.join(stats_dir_path, 'aseg.stats')):
            logger.info('missing: aseg.stats')
            ready = False
            miss = add_2dict(miss, _SUBJECT, 'VolSeg')
    for hemisphere in parc_DK_f2rd:
        file_with_stats = parc_DK_f2rd[hemisphere]
        if not path.isfile(path.join(stats_dir_path,file_with_stats)):
            logger.info('missing: {}'.format(file_with_stats))
            ready = False
            miss = add_2dict(miss, _SUBJECT, file_with_stats)
    for hemisphere in parc_DS_f2rd:
        file_with_stats = parc_DS_f2rd[hemisphere]
        if not path.isfile(path.join(stats_dir_path,file_with_stats)):
            logger.info('missing: {}'.format(file_with_stats))
            ready = False
            miss = add_2dict(miss, _SUBJECT, file_with_stats)
    file_with_stats = 'wmparc.stats'
    if not path.isfile(path.join(stats_dir_path,file_with_stats)):
            ready = False
            miss = add_2dict(miss, _SUBJECT, file_with_stats)
            logger.info('missing: {}'.format(file_with_stats))
    return ready, miss

import time
date = str(time.strftime('%Y%m%d', time.localtime()))

class FSStats2Table:
    '''extract stats of subjects to table
    Args:
        ls_subjects: list of subjects
        PATH2subjects: it is expected that all subjects are located in the same folder PATH2subjects
        stats_DIR: path to DIR where stats will be saved
        big_file : True, will create one file with all FS stats on one sheet
        data_only_volumes: True: will create one file with one sheet with only subcortical volumes
    Return:
        fname_fs_per_param: one file with multiple sheets. Sheet per parameter per hemisphere, per atlas
    '''
    def __init__(self, ls_subjects,
                    stats_DIR,
                    project_vars,
                    stats_files,
                    big_file = True,
                    data_only_volumes=False,
                    new_date = True):
        self.ls_subjects       = ls_subjects
        self.stats_DIR         = stats_DIR
        self.PATH2subjects     = project_vars["PROCESSED_FS_DIR"][1]
        self.stats_files       = stats_files
        fname_fs_per_param     = stats_files["fname_fs_per_param"]
        self.big_file          = big_file
        self.data_only_volumes = data_only_volumes
        if new_date:
            file_name          = f"{fname_fs_per_param}_{date}.xlsx"
        else:
            file_name          = f"{fname_fs_per_param}.xlsx"
        self.dataf             = self.get_path(self.stats_DIR, file_name)
        self.dir_stats         = 'stats'
        if not ls_subjects:
            self.ls_subjects = sorted(listdir(self.PATH2subjects))
            logger.info(f'    Extracting stats for subjects located in folder: {PATH2subjects}')

        self.miss = dict()
        self.run()

    def run(self):
        '''
        runs the pipeline to extract FreeSurfer stats to excel file
        '''
        self.writer=pd.ExcelWriter(self.dataf, engine='xlsxwriter')
        self.sheetnames = list()
        self.row=1

        for sub in self.ls_subjects:
            subs_left = len(self.ls_subjects[self.ls_subjects.index(sub):])
            logger.info(f'reading: {sub}; left: {subs_left}')
            path_2sub        = self.get_path(self.PATH2subjects, sub)
            stats_dir_path   = self.get_path(path_2sub, self.dir_stats)
            ready, self.miss = chk_if_all_stats_present(sub, stats_dir_path, self.miss)
            if ready:
                logger.info('    extracting stats for {}'.format(sub))
                self.get_bs_hip_amy_tha(stats_dir_path, sub)
                self.get_segmentations(stats_dir_path, sub)
                self.get_parcelations(stats_dir_path, sub)
                self.get_parcelations_destrieux(stats_dir_path, sub)
                self.get_parcelations_desikan_wm(stats_dir_path, sub)
                self.row += 1
        self.writer.save()
        self.save_missing()
        self.make_one_sheet()

    def get_bs_hip_amy_tha(self, stats_dir_path, _SUBJECT):
        '''Extracting Brainstem,  Hippocampus, Amygdala, Thalamus'''
        print('    Brainstem,  Hippocampus, Amygdala, Thalamus running')
        for sheet in BS_Hip_Tha_stats_f:
            file_with_stats = [i for i in BS_Hip_Tha_stats_f[sheet] if path.exists(path.join(stats_dir_path.replace('/stats',''),i))][0]
            if file_with_stats:
                if '.v12' in file_with_stats or '.v21' in file_with_stats:
                    df = self.read_BS_HIP_AMY_THA_v12_v21(path.join(stats_dir_path.replace('/stats',''),file_with_stats),_SUBJECT)
                else:
                    df = self.read_BS_HIP_v10(path.join(stats_dir_path.replace('/stats',''),file_with_stats),_SUBJECT)
            else:
                print('    ERROR, '+sheet+' stats file is missing\n')
                index_df = brstem_hip_header[sheet]
                df=pd.DataFrame(np.repeat('nan',len(index_df)), columns=[_SUBJECT], index=index_df)
                df=df.T
            if sheet in self.sheetnames:
                df.to_excel(self.writer,sheet_name=sheet,startcol=0, startrow=self.row, header=False, index=True)
            else:
                df.rename(columns=lambda ROI: brstem_hip_header['all'][ROI], inplace=True)
                df.to_excel(self.writer,sheet_name=sheet,startcol=0, startrow=0, header=True, index=True)
                self.sheetnames.append(sheet)

    def get_segmentations(self, stats_dir_path, _SUBJECT):
        '''Extracting SEGMENTATIONS'''
        print('    Segmentations ')
        sheet = 'VolSeg'
        file = 'aseg.stats'
        file_with_stats = path.join(stats_dir_path, file)
        if file_with_stats:
            lines = list(open(file_with_stats,'r'))
            dict_vol_general = {x.split()[3].strip(','):x.split()[-2].strip(',') for x in lines if 'Measure' in x}
            # volumes_general_structures = [x.split()[3].strip(',') for x in lines if 'Measure' in x]
            # volumes_general_values = [x.split()[-2].strip(',') for x in lines if 'Measure' in x]
            segmentations = lines[lines.index([x for x in lines if 'ColHeaders' in x][0]):]
            seg_measurements = [segmentations[0].split()[4:]]
            for line in segmentations[1:]:
                seg_measurements.append(line.split()[2:])
            df = pd.DataFrame(seg_measurements[1:], columns=seg_measurements[0])

            for parameter in segmentation_parameters:
                sheetName = 'VolSeg'+parameter.replace('Volume_mm3','')
                df2 = pd.DataFrame()
                df2[_SUBJECT] = df[parameter]
                df2.index = df['StructName']
                df2 = df2.transpose()
                if parameter == 'Volume_mm3':
                    for ROI in dict_vol_general:
                        df2[ROI] = dict_vol_general[ROI]
                    # for ROI in volumes_general_structures:
                    #     df2[ROI] = volumes_general_values[volumes_general_structures.index(ROI)]
                if sheetName in self.sheetnames:
                    df2.to_excel(self.writer,sheet_name=sheetName,startcol=0, startrow=self.row, header=False, index=True)
                else:
                    df2.rename(columns=lambda ROI: segmentations_header[ROI], inplace=True)
                    df2.to_excel(self.writer,sheet_name=sheetName,startcol=0, startrow=0, header=True, index=True)
                    self.sheetnames.append(sheetName)
        else:
            logger.info('    ERROR {} is missing\n'.format(file_with_stats))

    def get_parcelations(self, stats_dir_path, _SUBJECT):
        '''Extracting PARCELLATIONS Desikan'''
        logger.info('    Cortical Parcellations:\n        Desikan')
        atlas = '_DK'
        for hemisphere in parc_DK_f2rd:
            file_with_stats = parc_DK_f2rd[hemisphere]
            f_exists = False
            if path.isfile(path.join(stats_dir_path, file_with_stats)):
                file = path.join(stats_dir_path, file_with_stats)
                f_exists = True
            else:
                logger.info('    ERROR {} is missing\n'.format(file_with_stats))
            if f_exists:
                lines = list(open(file,'r'))
                dict_vol_general = {x.split()[2].strip(',')+'_'+x.split()[3].strip(','):x.split()[-2].strip(',') for x in lines if 'Measure' in x}
                # volumes_general_structures = [x.split()[2].strip(',')+'_'+x.split()[3].strip(',') for x in lines if 'Measure' in x and 'Cortex' in x]
                # volumes_general_values = [x.split()[-2].strip(',') for x in lines if 'Measure' in x and 'Cortex' in x]
                segmentations = lines[lines.index([x for x in lines if 'ColHeaders' in x][0]):]
                seg_measurements = [segmentations[0].split()[2:]]
                for line in segmentations[1:]:
                    seg_measurements.append(line.split())
                df = pd.DataFrame(seg_measurements[1:], columns=seg_measurements[0])

                for parameter in parc_parameters:
                    sheetName = parc_parameters[parameter]+hemisphere+atlas
                    df2 = pd.DataFrame()
                    df2[_SUBJECT] = df[parameter]
                    df2.index = df['StructName']
                    df2 = df2.transpose()
                    if parameter == 'SurfArea':
                        df2['Cortex_WhiteSurfArea'] = dict_vol_general['Cortex_WhiteSurfArea']
                        # df2['Cortex_WhiteSurfArea'] = volumes_general_values[volumes_general_structures.index('Cortex_WhiteSurfArea')]
                    elif parameter == 'ThickAvg':
                        df2['Cortex_MeanThickness'] = dict_vol_general['Cortex_MeanThickness']
                        # df2['Cortex_MeanThickness'] = volumes_general_values[volumes_general_structures.index('Cortex_MeanThickness')]
                    elif parameter == 'GrayVol':
                        if 'Cortex_CortexVol' in dict_vol_general:
                            df2['Cortex_CortexVol'] = dict_vol_general['Cortex_CortexVol']
                            # df2['Cortex_CortexVol'] = volumes_general_values[volumes_general_structures.index('Cortex_CortexVol')]
                        else:
                            df2['Cortex_CortexVol'] = 'nan'
                    elif parameter == 'NumVert':
                        df2['Cortex_NumVert'] = dict_vol_general['Cortex_NumVert']
                        # df2['Cortex_NumVert'] = volumes_general_values[volumes_general_structures.index('Cortex_NumVert')]
                    if sheetName in self.sheetnames:
                        df2.to_excel(self.writer,sheet_name=sheetName,startcol=0, startrow=self.row, header=False, index=True)
                    else:
                        df2.rename(columns=lambda ROI: parc_DK_header[ROI], inplace=True)
                        df2.to_excel(self.writer,sheet_name=sheetName,startcol=0, startrow=0, header=True, index=True)
                        self.sheetnames.append(sheetName)

    def get_parcelations_destrieux(self, stats_dir_path, _SUBJECT):
        '''Extracting PARCELLATIONS Destrieux'''
        logger.info('        Destrieux')
        atlas = '_DS'
        for hemisphere in parc_DS_f2rd:
            file_with_stats = parc_DS_f2rd[hemisphere]
            f_exists = False
            if path.isfile(path.join(stats_dir_path, file_with_stats)):
                file = path.join(stats_dir_path, file_with_stats)
                f_exists = True
            else:
                print('    ERROR '+file_with_stats+' file is missing\n')
            if f_exists:
                lines = list(open(file,'r'))
                segmentations = lines[lines.index([x for x in lines if 'ColHeaders' in x][0]):]
                seg_measurements = [segmentations[0].split()[2:]]
                for line in segmentations[1:]:
                    seg_measurements.append(line.split())
                df = pd.DataFrame(seg_measurements[1:], columns=seg_measurements[0])

                for parameter in parc_parameters:
                    sheetName = parc_parameters[parameter]+hemisphere+atlas
                    df2 = pd.DataFrame()
                    df2[_SUBJECT] = df[parameter]
                    df2.index = df['StructName']
                    df2 = df2.transpose()
                    if sheetName in self.sheetnames:
                        df2.to_excel(self.writer,sheet_name=sheetName,startcol=0, startrow=self.row, header=False, index=True)
                    else:
                        df2.rename(columns=lambda ROI: parc_DS_header[ROI], inplace=True)
                        df2.to_excel(self.writer,sheet_name=sheetName,startcol=0, startrow=0, header=True, index=True)
                        self.sheetnames.append(sheetName)

    def get_parcelations_desikan_wm(self, stats_dir_path, _SUBJECT):
        '''Extracting PARCELLATIONS Desikan WhiteMatter'''
        logger.info('        WhiteMatter')
        atlas = '_DK'
        file_with_stats = 'wmparc.stats'
        f_exists = False
        if path.isfile(path.join(stats_dir_path, file_with_stats)):
            file = path.join(stats_dir_path, file_with_stats)
            f_exists = True
        else:
            print('    ERROR '+file_with_stats+' file is missing\n')
        if f_exists:
                lines = list(open(file,'r'))
                segmentations = lines[lines.index([x for x in lines if 'ColHeaders' in x][0]):]
                seg_measurements = [segmentations[0].split()[4:]]
                for line in segmentations[1:]:
                    seg_measurements.append(line.split()[2:])
                df = pd.DataFrame(seg_measurements[1:], columns=seg_measurements[0])

                for parameter in segmentation_parameters:
                    sheetName = 'VolSegWM'+parameter.replace('Volume_mm3','')+atlas
                    df2 = pd.DataFrame()
                    df2[_SUBJECT] = df[parameter]
                    df2.index = df['StructName']
                    df2 = df2.transpose()

                    if sheetName in self.sheetnames:
                        df2.to_excel(self.writer,sheet_name=sheetName,startcol=0, startrow=self.row, header=False, index=True)
                    else:
                        df2.rename(columns=lambda ROI: parc_DK_header[ROI.replace('wm-lh-','').replace('wm-rh-','').replace('Left-','').replace('Right-','')]+self.get_ending_dswm(ROI[:5]), inplace=True)
                        df2.to_excel(self.writer,sheet_name=sheetName,startcol=0, startrow=0, header=True, index=True)
                        self.sheetnames.append(sheetName)

    def read_BS_HIP_AMY_THA_v12_v21(self, file, _SUBJECT):
        logger.info(file)
        content=open(file,'r').readlines()
        if 'amygdalar-nuclei' in file or 'thalamic-nuclei' in file:
            d_data = {i.split(' ')[-1].strip('\n'):i.split(' ')[-2] for i in content[1:]}
        else:
            d_data = {i.split(' ')[-2]:i.split(' ')[-1].strip('\n') for i in content}
        return pd.DataFrame(d_data, index=[_SUBJECT])

    def read_BS_HIP_v10(self, file, _SUBJECT):
        df=pd.read_table(file)
        df.loc[-1]=df.columns.values
        df.index=df.index+1
        df=df.sort_index()
        df.columns=['col']
        df['col'],df[_SUBJECT]=df['col'].str.split(' ',1).str
        df.index=df['col']
        del df['col']
        return df.transpose()

    def get_ending_dswm(self, str):
        if str == 'wm-lh':
            ending = 'L'
        elif str == 'wm-rh':
            ending = 'R'
        elif str == 'Left-':
            ending = 'L'
        elif str == 'Right':
            ending = 'R'
        return ending

    def save_missing(self):
        if self.miss:
            f_miss = self.get_path(self.stats_DIR, 'subjects_with_missing_files.json')
            logger.info('ERROR: some subjects are missing the required files. Check file: {}'.format(f_miss))
            self.save_json(self.miss, f_miss)

    def make_one_sheet(self):
        if self.big_file:
            from fs_stats_utils import FSStatsUtils
            fs_utils = FSStatsUtils(self.dataf, self.stats_DIR, _id_col, self.sheetnames)
            file_type = self.stats_files["file_type"]
            file_name = self.stats_files["fname_fs_all_stats"]
            fs_utils.create_BIG_data_file(file_name, file_type)
            if self.data_only_volumes:
                file_name = self.stats_files["fname_fs_subcort_vol"]
                fs_utils.create_file_with_only_subcort_volumes(file_name, file_type)

    def get_path(self, link1, link2):
        return path.join(link1, link2).replace(sep, '/')

    def save_json(self, d, f):
        with open(f, 'w') as jf:
            json.dump(d, jf, indent=4)


def get_parameters(projects, default_stats_dir):
    """get parameters for nimb"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-project", required=False,
        default=projects[0],
        choices = projects,
        help="names of projects located in credentials_path.py/nimb/projects.json -> PROJECTS",
    )

    parser.add_argument(
        "-stats_dir", required=False,
        default=default_stats_dir,
        help="path to GLM folder",
    )

    params = parser.parse_args()
    return params


if __name__ == "__main__":

    import sys
    from os import system
    import argparse
    try:
        from pathlib import Path
    except ImportError as e:
        print('please install pathlib')
        sys.exit(e)

    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[2]
    sys.path.append(str(top))

    from setup.get_vars import Get_Vars
    getvars           = Get_Vars()
    vars_stats        = getvars.stats_vars
    default_stats_dir = vars_stats["STATS_PATHS"]["STATS_HOME"]
    if "STATS_FILES" in vars_stats:
        stats_files   = vars_stats["STATS_FILES"]
    else:
        stats_files   = {
       "fname_fs_per_param"     : "stats_FreeSurfer_per_param",
       "fname_fs_all_stats"     : "stats_FreeSurfer_all",
       "fname_fs_subcort_vol"   : "stats_FreeSurfer_subcortical",
       "file_type"              : "xlsx"}

    projects      = getvars.projects
    all_projects  = [i for i in projects.keys() if 'EXPLANATION' not in i and 'LOCATION' not in i]
    params        = get_parameters(all_projects, default_stats_dir)
    project_vars  = projects[params.project]
    ls_subjects   = []
    stats_DIR     = params.stats_dir

    FSStats2Table(ls_subjects,
                    stats_DIR,
                    project_vars,
                    stats_files,
                    big_file = True,
                    data_only_volumes=False,
                    new_date = True)

