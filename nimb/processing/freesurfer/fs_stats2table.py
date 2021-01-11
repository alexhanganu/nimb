#!/bin/python
'''
Extract the stats data for all subjects located in a folder, to 2/3 excel files

Args:
    PATHstats = path of the folder where the final excel files will be saved
    NIMB_PROCESSED_FS = path to the folder where the FreeSurfer processed subjects are located. These can be 
                        raw folders, or zip archived folders (with .zip as ending)
    NIMB_tmp = folder where temporary files will be saved and folder where the 
                "stats" folder of the subjects will be extracted if subjects are archived with .zip
    data_only_volumes = True or False, is user wants an additional file to constructed that will include only subcortical volumes
Return:
    an excel file with all subjects and all parameters, per sheets
    one big excel file with all parameters on one sheet
'''
import time
date = str(time.strftime('%Y%m%d', time.localtime()))

#Names of the final files with statistical data:
file_with_all_sheets = 'data_FreeSurfer_'+date+'.xlsx'
file_with_only_subcortical_volumes = 'data_FreeSurfer_subcortical_volumes_'+date+'.xlsx'
file_with_all_data_one_sheet = 'data_FreeSurfer_one_sheet_'+date+'.xlsx'

from os import path, listdir, sep
import pandas as pd
import numpy as np
import xlsxwriter, xlrd
import json
import logging
from fs_definitions import (BS_Hip_Tha_stats_f, brstem_hip_header,
                             segmentation_parameters,
                             segmentations_header, parc_parameters,
                             parc_DK_f2rd, parc_DK_header,
                             parc_DS_f2rd, parc_DS_header)
columns_2_remove = ['ventricle_5th','wm_hypointensities_L',
                    'wm_hypointensities_R','non_wm_hypointensities',
                    'non_wm_hypointensities_L','non_wm_hypointensities_R',
                    'eTIV', 'volBrainSegNotVent'] #removing because they are zeros and this gives errors in stats

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class FSStats2Table:
    def __init__(self, PATHstats, NIMB_PROCESSED_FS, NIMB_tmp, data_only_volumes=False):
        self.stats_DIR         = PATHstats
        self.NIMB_PROCESSED_FS = NIMB_PROCESSED_FS
        self.NIMB_tmp          = NIMB_tmp
        self.data_only_volumes = data_only_volumes
        self.dir_stats         = 'stats'

        self.miss = dict()
        self.dataf                    = self.get_path(self.stats_DIR, file_with_all_sheets)
        self.data_subcortical_volumes = self.get_path(self.stats_DIR, file_with_only_subcortical_volumes)
        self.data_big                 = self.get_path(self.stats_DIR, file_with_all_data_one_sheet)
        self.f_subj_with_errors       = self.get_path(self.stats_DIR, 'subjects_with_errors.json')
        self.run()

    def run(self):
        '''
        will run the pipeline of extracting FreeSurfer stats to excel file
        '''
        logger.info(self.NIMB_PROCESSED_FS)
        ls_all_sub = sorted(listdir(self.NIMB_PROCESSED_FS))
        self.writer=pd.ExcelWriter(self.dataf, engine='xlsxwriter')
        self.sheetnames = list()
        self.row=1

        for sub in ls_all_sub:
            logger.info('reading: {}; left: {}'.format(sub, len(ls_all_sub[ls_all_sub.index(sub):])))
            stats_dir_path, sub = self.get_stats_dir(sub)
            stats_dir_path = self.get_path(stats_dir_path, self.dir_stats)
            if self.stats_ready(sub, stats_dir_path):
                logger.info('    extracting stats for {}'.format(sub))
                self.get_bs_hip_amy_tha(stats_dir_path, sub)
                self.get_segmentations(stats_dir_path, sub)
                self.get_parcelations(stats_dir_path, sub)
                self.get_parcelations_destrieux(stats_dir_path, sub)
                self.get_parcelations_desikan_wm(stats_dir_path, sub)
                self.row += 1
        self.writer.save()

        if self.miss:
            f_miss = self.get_path(self.NIMB_PROCESSED_FS, 'nimb_subjects_missing.json')
            logger.info('ERROR: some subjects are missing the required files. Check file: {}'.format(f_miss))
            self.save_json(self.miss, f_miss)

        self.create_BIG_data_file()
        if self.data_only_volumes:
            self.create_file_with_only_subcort_volumes()

    def get_stats_dir(self, sub):
        '''
        checks if subject is archived
        using only the "zip" methods currently
        extracts the "stats" folder of the subject
        '''
        sub_path = self.get_path(self.NIMB_PROCESSED_FS, sub)
        if not path.isdir(sub_path):
            if sub.endswith('zip'):
                logger.info('Must extract folder {} for each subject to destination {}'.format('stats', sub_path))
                ZipArchiveManagement(sub_path, 
                                    path2xtrct = self.NIMB_tmp, path_err = False,
                                    dirs2xtrct = [self.dir_stats,], log=True)
                time.sleep(1)
                sub = sub.replace('.zip','')
                return self.get_path(self.NIMB_tmp, sub), sub
        else:
            return sub_path, sub

    def stats_ready(self, _SUBJECT, stats_dir_path):
        '''
        checks if subject has all stats files
        '''
        ready = True
        for sheet in BS_Hip_Tha_stats_f:
            try:
                file_with_stats = [i for i in BS_Hip_Tha_stats_f[sheet] if path.exists(path.join(stats_dir_path.replace('/stats',''),i))][0]
                if not file_with_stats:
                    logger.info('missing: {}'.format(sheet))
                    ready = False
                    self.miss = self.add_2dict(self.miss, _SUBJECT, sheet)
            except Exception as e:
                logger.info(e)
                ready = False
                self.miss = self.add_2dict(self.miss, _SUBJECT, sheet)
        if not path.exists(path.join(stats_dir_path, 'aseg.stats')):
                logger.info('missing: aseg.stats')
                ready = False
                self.miss = self.add_2dict(self.miss, _SUBJECT, 'VolSeg')
        for hemisphere in parc_DK_f2rd:
            file_with_stats = parc_DK_f2rd[hemisphere]
            if not path.isfile(path.join(stats_dir_path,file_with_stats)):
                logger.info('missing: {}'.format(file_with_stats))
                ready = False
                self.miss = self.add_2dict(self.miss, _SUBJECT, file_with_stats)
        for hemisphere in parc_DS_f2rd:
            file_with_stats = parc_DS_f2rd[hemisphere]
            if not path.isfile(path.join(stats_dir_path,file_with_stats)):
                logger.info('missing: {}'.format(file_with_stats))
                ready = False
                self.miss = self.add_2dict(self.miss, _SUBJECT, file_with_stats)
        file_with_stats = 'wmparc.stats'
        if not path.isfile(path.join(stats_dir_path,file_with_stats)):
                ready = False
                self.miss = self.add_2dict(self.miss, _SUBJECT, file_with_stats)
                logger.info('missing: {}'.format(file_with_stats))
        return ready

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

    def create_file_with_only_subcort_volumes(self):
        '''CREATING ONE BIG STATS FILE'''
        logger.info('CREATING file with Subcortical Volumes')

        df_concat = pd.read_excel(self.dataf, engine = 'openpyxl', sheet_name=self.sheetnames[0])
        df_concat = self.change_column_name(df_concat, self.sheetnames[0])

        for sheet in self.sheetnames[1:5]:
            df2 = pd.read_excel(self.dataf, engine = 'openpyxl', sheet_name=sheet)
            df2 = self.change_column_name(df2, sheet)
            frames = (df_concat, df2)
            df_concat = pd.concat(frames, axis=1, sort=True)

        df_segmentations = pd.read_excel(self.dataf, engine = 'openpyxl', sheet_name='VolSeg')
        frame_final = (df_concat, df_segmentations['eTIV'])
        df_concat = pd.concat(frame_final,axis=1, sort=True)

        writer = pd.ExcelWriter(self.data_subcortical_volumes, engine='xlsxwriter')
        df_concat.to_excel(writer, 'stats')
        writer.save()
        logger.info('FINISHED creating file with Subcortical Volumes')

    def create_file_with_only_subcort_volumes_V2(self):
        '''CREATING ONE BIG STATS FILE'''
        logger.info('CREATING file with Subcortical Volumes - VERSION 2, must be checked')

        all_df = dict()
        df_segmentations = pd.read_excel(self.dataf, engine = 'openpyxl', sheet_name='VolSeg')

        for sheet in self.sheetnames[0:5]:
            df = pd.read_excel(self.dataf, engine = 'openpyxl', sheet_name=sheet)
            all_df[sheet] = self.change_column_name(df, sheet)
        frames = [all_df[i] for i in all_df]+[df_segmentations['eTIV']]
        df_concat = pd.concat(frames, axis=1, sort=True)

        writer = pd.ExcelWriter(self.data_subcortical_volumes, engine='xlsxwriter')
        df_concat.to_excel(writer, 'stats')
        writer.save()
        logger.info('FINISHED creating file with Subcortical Volumes')

    def create_BIG_data_file(self):

        logger.info('CREATING One file for all subjects')
        df_concat = pd.read_excel(self.dataf, engine = 'openpyxl', sheet_name=self.sheetnames[0], index_col = 0)
        df_concat = self.change_column_name(df_concat, self.sheetnames[0])

        for sheet in self.sheetnames[1:]:
            df2 = pd.read_excel(self.dataf, engine = 'openpyxl', sheet_name=sheet, index_col = 0)
            df2 = self.change_column_name(df2, sheet)
            frames = (df_concat, df2)
            df_concat = pd.concat(frames, axis=1, sort=True)

        df_segmentations = pd.read_excel(self.dataf, engine = 'openpyxl', sheet_name='VolSeg', index_col = 0)
        frame_final = (df_concat, df_segmentations['eTIV'])
        df_concat = pd.concat(frame_final, axis=1, sort=True)

        writer = pd.ExcelWriter(self.data_big, engine='xlsxwriter')
        df_concat.to_excel(writer, 'stats')
        writer.save()
        logger.info('FINISHED creating One file for all subjects')
        self.check_nan(df_concat)

    def check_nan(self, df):
        '''
        df.index must be the ids, as str() not int()
        Args:
            df to be checked
        Return:
            json file with a dictionary {id: [columns with nan]}
        '''
        d_err = dict()
        for col in df.columns:
            if df[col].isnull().values.any():
                ls = df[col].isnull().tolist()
                for val in ls:
                    if val:
                        _id = df.index[ls.index(val)]
                        if _id not in d_err:
                            d_err[_id] = list()
                        if col not in d_err[_id]:
                            d_err[_id].append(col)
        self.save_json(d_err, self.f_subj_with_errors)

    def change_column_name(self, df, sheet):
        ls = df.columns.tolist()
        columns_2_drop = []
        for col in columns_2_remove:
            if col in ls:
                columns_2_drop.append(col)
                ls.remove(col)
        if len(columns_2_drop)>0:
            df.drop(columns=columns_2_drop, inplace=True)
        for col in ls:
            ls[ls.index(col)] = '{}_{}'.format(col, sheet)
        df.columns = ls
        return df

    def add_2dict(self, d, key, val):
            if key not in d:
                d[key] = list()
            if val:
                d[key].append(val)
            return d

    def get_path(self, link1, link2):
        return path.join(link1, link2).replace(sep, '/')

    def save_json(self, d, f):
        with open(f, 'w') as jf:
            json.dump(d, jf, indent=4)




'''
below are previous versions of multiple scripts
that were assembled in the FSStats2Table class
'''
def chk_if_subjects_ready(PATHstats, SUBJECTS_DIR):
    ''' this checks if all subjects have all stats files'''

    miss = dict()

    def add_to_miss(miss, _SUBJECT, sheet):
        if _SUBJECT not in miss:
            miss[_SUBJECT] = list()
        if sheet:
            miss[_SUBJECT].append(sheet)
        return miss

    subjects = sorted(listdir(SUBJECTS_DIR))
    for _SUBJECT in subjects:
        print('reading: ', _SUBJECT, '; left: ', len(subjects[subjects.index(_SUBJECT):]))
        for sheet in BS_Hip_Tha_stats_f:
            try:
                file_with_stats = [i for i in BS_Hip_Tha_stats_f[sheet] if path.exists(path.join(SUBJECTS_DIR,_SUBJECT,i))][0]
                if not file_with_stats:
                    print('missing: ', sheet)
                    miss = add_to_miss(miss, _SUBJECT, sheet)
            except Exception as e:
                print(e)
                miss = add_to_miss(miss, _SUBJECT, sheet)                
        if not path.exists(path.join(SUBJECTS_DIR,_SUBJECT, 'stats', 'aseg.stats')):
                print('missing: ', 'aseg.stats')
                miss = add_to_miss(miss, _SUBJECT, 'VolSeg')
        for hemisphere in parc_DK_f2rd:
            file_with_stats = parc_DK_f2rd[hemisphere]
            if not path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)):
                print('missing: ', file_with_stats)
                miss = add_to_miss(miss, _SUBJECT, file_with_stats)
        for hemisphere in parc_DS_f2rd:
            file_with_stats = parc_DS_f2rd[hemisphere]
            if not path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)):
                print('missing: ', file_with_stats)
                miss = add_to_miss(miss, _SUBJECT, file_with_stats)
        file_with_stats = 'wmparc.stats'
        if not path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)):
                miss = add_to_miss(miss, _SUBJECT, file_with_stats)
                print('missing: ', file_with_stats)

    if miss:
        print('ERROR: some subjects are missing the required files')
        with open(path.join(PATHstats, 'subjects_missing.json'), 'w') as j:
            json.dump(miss, j, indent=4)




# works on stats of FreeSurfer 7.1, needs to be confirmed on stats from FreeSurfer <7
def stats2table_v7(PATHstats, SUBJECTS_DIR, data_only_volumes=True):

    dataf = path.join(PATHstats,file_with_all_sheets)
    data_subcortical_volumes = path.join(PATHstats,file_with_only_subcortical_volumes)
    data_big = path.join(PATHstats,file_with_all_data_one_sheet)

    '''
    extracts the data from the data files of each subject and creates the dataf file
    '''
    #writing Headers for all sheets
    print('Writing Headers for all sheets')

    def read_BS_HIP_AMY_THA_v12_v21(file, _SUBJECT):
        content=open(file,'r').readlines()
        if 'hipposubfields' in file:
            dict1 = {i.split(' ')[-2]:i.split(' ')[-1].strip('\n') for i in content}
        else:
            dict1 = {i.split(' ')[-1].strip('\n'):i.split(' ')[-2] for i in content[1:]}
        return pd.DataFrame(dict1, index=[_SUBJECT])

    def read_BS_HIP_v10(file, _SUBJECT):
        df=pd.read_table(file)
        df.loc[-1]=df.columns.values
        df.index=df.index+1
        df=df.sort_index()
        df.columns=['col']
        df['col'],df[_SUBJECT]=df['col'].str.split(' ',1).str
        df.index=df['col']
        del df['col']
        return df.transpose()

    def get_ending(str):
        if str == 'wm-lh':
            ending = 'L'
        elif str == 'wm-rh':
            ending = 'R'
        elif str == 'Left-':
            ending = 'L'
        elif str == 'Right':
            ending = 'R'

        return ending


    writer=pd.ExcelWriter(dataf, engine='xlsxwriter')
    sheetnames = list()
    row=1
    print('Writing stats for subjects')

    for _SUBJECT in listdir(SUBJECTS_DIR):
        print(_SUBJECT)
        '''Extracting Brainstem,  Hippocampus, Amygdala, Thalamus'''
        print('    Brainstem,  Hippocampus, Amygdala, Thalamus running')
        for sheet in BS_Hip_Tha_stats_f:
            file_with_stats = [i for i in BS_Hip_Tha_stats_f[sheet] if path.exists(path.join(SUBJECTS_DIR,_SUBJECT,i))][0]
            if file_with_stats:
                if '.v12' in file_with_stats or '.v21' in file_with_stats:
                    df = read_BS_HIP_AMY_THA_v12_v21(path.join(SUBJECTS_DIR,_SUBJECT,file_with_stats),_SUBJECT)
                else:
                    df = read_BS_HIP_v10(path.join(SUBJECTS_DIR,_SUBJECT,file_with_stats),_SUBJECT)
            else:
                print('    ERROR, '+sheet+' stats file is missing\n')
                index_df = brstem_hip_header[sheet]
                df=pd.DataFrame(np.repeat('nan',len(index_df)), columns=[_SUBJECT], index=index_df)
                df=df.T
            if sheet in sheetnames:
                df.to_excel(writer,sheet_name=sheet,startcol=0, startrow=row, header=False, index=True)
            else:
                df.rename(columns=lambda ROI: brstem_hip_header['all'][ROI], inplace=True)
                df.to_excel(writer,sheet_name=sheet,startcol=0, startrow=0, header=True, index=True)
                sheetnames.append(sheet)


        '''Extracting SEGMENTATIONS'''
        print('    Segmentations ')
        sheet = 'VolSeg'
        file = 'aseg.stats'
        file_with_stats = path.join(SUBJECTS_DIR,_SUBJECT,'stats',file)
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
                if sheetName in sheetnames:
                    df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=row, header=False, index=True)
                else:
                    df2.rename(columns=lambda ROI: segmentations_header[ROI], inplace=True)
                    df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=0, header=True, index=True)
                    sheetnames.append(sheetName)
        else:
            print('    ERROR '+file_with_stats+' is missing\n')



        '''Extracting PARCELLATIONS Desikan'''
        print('    Cortical Parcellations:\n        Desikan')
        atlas = '_DK'
        for hemisphere in parc_DK_f2rd:
            file_with_stats = parc_DK_f2rd[hemisphere]
            f_exists = False
            if path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)):
                file = path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)
                f_exists = True
            else:
                print('    ERROR '+file_with_stats+' file is missing\n')
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
                    if sheetName in sheetnames:
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=row, header=False, index=True)
                    else:
                        df2.rename(columns=lambda ROI: parc_DK_header[ROI], inplace=True)
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=0, header=True, index=True)
                        sheetnames.append(sheetName)


        '''Extracting PARCELLATIONS Destrieux'''
        print('        Destrieux')
        atlas = '_DS'
        for hemisphere in parc_DS_f2rd:
            file_with_stats = parc_DS_f2rd[hemisphere]
            f_exists = False
            if path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)):
                file = path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)
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
                    if sheetName in sheetnames:
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=row, header=False, index=True)
                    else:
                        df2.rename(columns=lambda ROI: parc_DS_header[ROI], inplace=True)
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=0, header=True, index=True)
                        sheetnames.append(sheetName)



        '''Extracting PARCELLATIONS Desikan WhiteMatter'''
        print('        WhiteMatter')
        atlas = '_DK'
        file_with_stats = 'wmparc.stats'
        f_exists = False
        if path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)):
            file = path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)
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

                    if sheetName in sheetnames:
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=row, header=False, index=True)
                    else:
                        df2.rename(columns=lambda ROI: parc_DK_header[ROI.replace('wm-lh-','').replace('wm-rh-','').replace('Left-','').replace('Right-','')]+get_ending(ROI[:5]), inplace=True)
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=0, header=True, index=True)
                        sheetnames.append(sheetName)

        row += 1
    writer.save()



    '''CREATING file with Subcortical Volumes and ONE BIG STATS FILE'''
    print('CREATING file with Subcortical Volumes')
    columns_2_remove = ['ventricle_5th','wm_hypointensities_L',
                        'wm_hypointensities_R','non_wm_hypointensities',
                        'non_wm_hypointensities_L','non_wm_hypointensities_R',
                        'eTIV', 'volBrainSegNotVent']

    def change_column_name(df, sheet):
        ls = df.columns.tolist()
        columns_2_drop = []
        for col in columns_2_remove:
            if col in ls:
                columns_2_drop.append(col)
                ls.remove(col)

        if len(columns_2_drop)>0:
            df.drop(columns=columns_2_drop, inplace=True)
        for col in ls:
            ls[ls.index(col)] = col+'_'+sheet
        df.columns = ls
        return df


    df_segmentations = pd.read_excel(dataf, sheet_name='VolSeg')
    df_final = df_segmentations['eTIV']

    df_concat = pd.read_excel(dataf, sheet_name=sheetnames[0])
    df_concat = change_column_name(df_concat, sheetnames[0])

    for sheet in sheetnames[1:5]:
        df2 = pd.read_excel(dataf, sheet_name=sheet)
        df2 = change_column_name(df2, sheet)
        frames = (df_concat, df2)
        df_concat = pd.concat(frames, axis=1, sort=True)

    frame_final = (df_concat, df_final)
    df_concat = pd.concat(frame_final,axis=1, sort=True)

    if data_only_volumes:
        writer = pd.ExcelWriter(data_subcortical_volumes, engine='xlsxwriter')
        df_concat.to_excel(writer, 'stats')
        writer.save()
    print('FINISHED creating file with Subcortical Volumes')


    print('CREATING One file with all statistics')

    df_concat = pd.read_excel(dataf, sheet_name=sheetnames[0])
    df_concat = change_column_name(df_concat, sheetnames[0])

    for sheet in sheetnames[1:]:
        df2 = pd.read_excel(dataf, sheet_name=sheet)
        df2 = change_column_name(df2, sheet)
        frames = (df_concat, df2)
        df_concat = pd.concat(frames, axis=1, sort=True)

    frame_final = (df_concat, df_final)
    df_concat = pd.concat(frame_final,axis=1, sort=True)

    writer = pd.ExcelWriter(data_big, engine='xlsxwriter')
    df_concat.to_excel(writer, 'stats')
    writer.save()
    print('FINISHED creating One file with all statistics')


'''
def create_HIP_to_cortex_ratio(df_data_big, HIP_to_cortex_ratio_DK, HIP_to_cortex_ratio_DS):

	print('CREATING file Hippocampus to Cortex ratio')
	from a.lib.stats_definitions import all_data, cols_per_measure_per_atlas
	cols2meas2atlas = cols_per_measure_per_atlas(df_data_big)
	cols_to_meas = cols2meas2atlas.cols_to_meas_to_atlas

	ls_columns = df_data_big.columns
	ls_atlases_laterality = list()
	for atlas in all_data['atlases']:
		if all_data[atlas]['two_hemi']:
			ls_atlases_laterality.append(atlas)

	ls_HIP = []
	for index in cols_to_meas['HIP']['HIPL']:
		ls_HIP.append(ls_columns[index])
	for index in cols_to_meas['HIP']['HIPR']:
		ls_HIP.append(ls_columns[index])
	df_HIP = df_data_big[ls_HIP]

	ls_Vol_CORTEX_DK = []
	for index in cols_to_meas['ParcDK']['GrayVol']:
		ls_Vol_CORTEX_DK.append(ls_columns[index])
	df_Vol_CORTEX_DK = df_data_big[ls_Vol_CORTEX_DK]

	ls_Vol_CORTEX_DS = []
	for index in cols_to_meas['ParcDS']['GrayVol']:
		ls_Vol_CORTEX_DS.append(ls_columns[index])
	df_Vol_CORTEX_DS = df_data_big[ls_Vol_CORTEX_DS]

	df_HIP_to_CORTEX_DK_ratio = pd.DataFrame()
	for col_HIP in df_HIP:
		for col_COR in df_Vol_CORTEX_DK:
			df_HIP_to_CORTEX_DK_ratio[col_HIP.replace('_HIP','')+col_COR] = df_HIP[col_HIP]*100/df_Vol_CORTEX_DK[col_COR]
	df_HIP_to_CORTEX_DK_ratio.to_csv(HIP_to_cortex_ratio_DK)

	df_HIP_to_CORTEX_DS_ratio = pd.DataFrame()
	for col_HIP in df_HIP:
		for col_COR in df_Vol_CORTEX_DS:
			df_HIP_to_CORTEX_DS_ratio[col_HIP.replace('_HIP','')+col_COR] = df_HIP[col_HIP]*100/df_Vol_CORTEX_DS[col_COR]
	df_HIP_to_CORTEX_DS_ratio.to_csv(HIP_to_cortex_ratio_DS)
	print('FINISHED creating file Hippocampus to Cortex ratio')



def create_SurfArea_to_Vol_ratio(df_data_big, f_SA_to_Vol_ratio_DK, f_SA_to_Vol_ratio_DS):

	print('CREATING file Surface Area to Volume ratio')
	from a.lib.stats_definitions import all_data, cols_per_measure_per_atlas
	cols2meas2atlas = cols_per_measure_per_atlas(df_data_big)
	cols_to_meas = cols2meas2atlas.cols_to_meas_to_atlas

	ls_columns = df_data_big.columns
	ls_atlases_laterality = list()
	for atlas in all_data['atlases']:
		if all_data[atlas]['two_hemi']:
			ls_atlases_laterality.append(atlas)

	ls_Surf_DK = []
	for index in cols_to_meas['ParcDK']['SurfArea']:
		ls_Surf_DK.append(ls_columns[index])
	df_Surf_DK = df_data_big[ls_Surf_DK]

	ls_Surf_DS = []
	for index in cols_to_meas['ParcDS']['SurfArea']:
		ls_Surf_DS.append(ls_columns[index])
	df_Surf_DS = df_data_big[ls_Surf_DS]

	ls_Vol_CORTEX_DK = []
	for index in cols_to_meas['ParcDK']['GrayVol']:
		ls_Vol_CORTEX_DK.append(ls_columns[index])
	df_Vol_CORTEX_DK = df_data_big[ls_Vol_CORTEX_DK]

	ls_Vol_CORTEX_DS = []
	for index in cols_to_meas['ParcDS']['GrayVol']:
		ls_Vol_CORTEX_DS.append(ls_columns[index])
	df_Vol_CORTEX_DS = df_data_big[ls_Vol_CORTEX_DS]


	SurfArea_to_Vol_ratio_DK = pd.DataFrame()
	for col_SA_DK in df_Surf_DK:
		for col_Vol_DK in df_Vol_CORTEX_DK:
			SurfArea_to_Vol_ratio_DK[col_SA_DK+col_Vol_DK] = df_Surf_DK[col_SA_DK]*100/df_Vol_CORTEX_DK[col_Vol_DK]
	SurfArea_to_Vol_ratio_DK.to_csv(f_SA_to_Vol_ratio_DK)

	SurfArea_to_Vol_ratio_DS = pd.DataFrame()
	for col_SA_DS in df_Surf_DS:
		for col_Vol_DS in df_Vol_CORTEX_DS:
			SurfArea_to_Vol_ratio_DS[col_SA_DS+col_Vol_DS] = df_Surf_DS[col_SA_DS]*100/df_Vol_CORTEX_DS[col_Vol_DS]
	SurfArea_to_Vol_ratio_DS.to_csv(f_SA_to_Vol_ratio_DS)
	print('FINISHED creating file Surface Area to Volume ratio')


'''

def get_parameters(projects):
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

    params = parser.parse_args()
    return params


def initiate_fs_from_sh(vars_local):
    """
    FreeSurfer needs to be initiated with source and export
    this functions tries to automate this
    """
    sh_file = path.join(vars_local["NIMB_PATHS"]["NIMB_tmp"], 'source_fs.sh')
    with open(sh_file, 'w') as f:
        f.write(vars_local["FREESURFER"]["export_FreeSurfer_cmd"]+'\n')
        f.write("export SUBJECTS_DIR="+vars_local["FREESURFER"]["FS_SUBJECTS_DIR"]+'\n')
        f.write(vars_local["FREESURFER"]["source_FreeSurfer_cmd"]+'\n')
    system("chmod +x {}".format(sh_file))
    return ("source {}".format(sh_file))


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

    import subprocess
    from distribution.logger import Log
    from distribution.manage_archive import ZipArchiveManagement
    from setup.get_vars import Get_Vars, SetProject
    getvars      = Get_Vars()
    dir_4stats   = getvars.stats_vars["STATS_PATHS"]["STATS_HOME"]
    vars_local   = getvars.location_vars['local']
    NIMB_tmp     = vars_local['NIMB_PATHS']['NIMB_tmp']
    fs_start_cmd = initiate_fs_from_sh(vars_local)
    try:
        subprocess.run(['mri_info'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    except Exception as e:
        print(e)
        print('please initiate freesurfer using the command: \n    {}'.format(fs_start_cmd))

    projects     = getvars.projects
    all_projects = [i for i in projects.keys() if 'EXPLANATION' not in i and 'LOCATION' not in i]
    params       = get_parameters(all_projects)
    PROCESSED_FS_DIR = projects[params.project]["PROCESSED_FS_DIR"][1]

    FSStats2Table(dir_4stats, PROCESSED_FS_DIR, NIMB_tmp,
                    data_only_volumes=False)
