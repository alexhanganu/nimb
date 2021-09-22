from os import path, sep
import pandas as pd
import numpy as np
import xlsxwriter, xlrd
import json

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
from fs_definitions import all_data, cols_per_measure_per_atlas


class FSStatsUtils:
    def __init__(self,
                dataf,
                stats_DIR,
                _id_col,
                sheetnames,
                sheet_subcort,
                Table):
        self.dataf      = dataf
        self.sheetnames = sheetnames
        self.stats_DIR  = stats_DIR
        self._id        = _id_col
        self.subcort    = sheet_subcort
        self.tab        = Table()
        self.f_errors   = self.get_path(stats_DIR, 'subjects_with_missing_values.json')

    def create_file_with_only_subcort_volumes(self, file_name, file_type):
        '''CREATING ONE BIG STATS FILE'''
        logger.info('CREATING file with Subcortical Volumes')

        df_concat = pd.read_excel(self.dataf, engine = 'openpyxl', sheet_name=self.sheetnames[0])
        df_concat = self.change_column_name(df_concat, self.sheetnames[0])

        for sheet in self.sheetnames[1:5]:
            df2 = pd.read_excel(self.dataf, engine = 'openpyxl', sheet_name=sheet)
            df2 = self.change_column_name(df2, sheet)
            frames = (df_concat, df2)
            df_concat = pd.concat(frames, axis=1, sort=True)

        df_segmentations = pd.read_excel(self.dataf, engine = 'openpyxl', sheet_name=self.subcort)
        frame_final = (df_concat, df_segmentations['eTIV'])
        df_concat = pd.concat(frame_final,axis=1, sort=True)
        df_concat.index.name = self._id

        self.f_subcort  = self.get_path(self.stats_DIR, f"{file_name}.{file_type}")
        writer = pd.ExcelWriter(self.f_subcort, engine='xlsxwriter')
        df_concat.to_excel(writer, 'stats')
        writer.save()
        logger.info('FINISHED creating file with Subcortical Volumes')

    def create_file_with_only_subcort_volumes_V2(self, file_name, file_type):
        '''CREATING ONE BIG STATS FILE'''
        logger.info('CREATING file with Subcortical Volumes - VERSION 2, must be checked')

        all_df = dict()
        df_segmentations = pd.read_excel(self.dataf, engine = 'openpyxl', sheet_name=self.subcort)

        for sheet in self.sheetnames[0:5]:
            df = pd.read_excel(self.dataf, engine = 'openpyxl', sheet_name=sheet)
            all_df[sheet] = self.change_column_name(df, sheet)
        frames = [all_df[i] for i in all_df]+[df_segmentations['eTIV']]
        df_concat = pd.concat(frames, axis=1, sort=True)
        df_concat.index.name = self._id

        self.f_subcort  = self.get_path(self.stats_DIR, f"{file_name}.{file_type}")
        writer = pd.ExcelWriter(self.f_subcort, engine='xlsxwriter')
        df_concat.to_excel(writer, 'stats')
        writer.save()
        logger.info('FINISHED creating file with Subcortical Volumes')

    def create_BIG_data_file(self, file_name, file_type):

        logger.info('CREATING One file for all subjects')
        df_concat = pd.read_excel(self.dataf, engine = 'openpyxl', sheet_name=self.sheetnames[0], index_col = 0)
        df_concat = self.change_column_name(df_concat, self.sheetnames[0])

        for sheet in self.sheetnames[1:]:
            df2 = pd.read_excel(self.dataf, engine = 'openpyxl', sheet_name=sheet, index_col = 0)
            df2 = self.change_column_name(df2, sheet)
            frames = (df_concat, df2)
            df_concat = pd.concat(frames, axis=1, sort=True)

        df_segmentations = pd.read_excel(self.dataf, engine = 'openpyxl', sheet_name=self.subcort, index_col = 0)
        frame_final = (df_concat, df_segmentations['eTIV'])
        df_concat = pd.concat(frame_final, axis=1, sort=True)
        df_concat.index.name = self._id

        path_2filename   = self.get_path(self.stats_DIR, f"{file_name}.{file_type}")
        print(path_2filename)
        self.tab.save_df(df_concat, path_2filename, sheet_name = 'stats')
        logger.info('FINISHED creating One file for all subjects')
        self.check_nan(df_concat)

    def create_HIP_to_cortex_ratio(self, df_data_big, HIP_to_cortex_ratio_DK, HIP_to_cortex_ratio_DS):

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

    def create_SurfArea_to_Vol_ratio(self, df_data_big, f_SA_to_Vol_ratio_DK, f_SA_to_Vol_ratio_DS):
        """
        this parameter is also an indirect method to add curvature int he analysis.
        Surface are corrected for Volume is NOT the same as raw Surface Area.
        The first outlining also the curvature.
        """

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


    def create_Vol_2FoldingIndex_ratio(self):
        """ create VOlume to Folding index ratio
        this parameter might correlate with raw Surface Area
        """
        print('CREATING file Volume to Folding Index ratio')


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
        self.save_json(d_err, self.f_errors)

    def change_column_name(self, df, sheet):
        columns_2_remove = ['eTIV'] #removing because there are multiple entries
        ls = df.columns.tolist()
        columns_2_drop = []
        for col in columns_2_remove:
            if col in ls:
                columns_2_drop.append(col)
                ls.remove(col)
        if len(columns_2_drop)>0:
            df.drop(columns=columns_2_drop, inplace=True)
        for col in ls:
            ls[ls.index(col)] = f'{col}_{sheet}'
        df.columns = ls
        return df

    def save_json(self, d, f):
        with open(f, 'w') as jf:
            json.dump(d, jf, indent=4)

    def get_path(self, link1, link2):
        return path.join(link1, link2).replace(sep, '/')

