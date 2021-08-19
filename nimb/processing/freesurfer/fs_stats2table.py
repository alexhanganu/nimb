#!/bin/python
'''
Extract the stats data for all subjects located in a folder, to 2/3 excel files

Args:
    PATHstats = path of the folder where the final excel files will be saved
    NIMB_PROCESSED_FS = path to the folder where the FreeSurfer processed subjects are located.
                        These must be un-archived folders, if script is run directly, 
                        or can be zip archived folders (with .zip as ending) if script is run through nimb.py
    data_only_volumes = True or False, is user wants an additional file to constructed that will include only subcortical volumes
Return:
    an excel file with all subjects and all parameters, per sheets
    one big excel file with all parameters on one sheet
'''
from os import path, listdir, sep, system
import sys
import argparse

import pandas as pd
import numpy as np
import xlsxwriter, xlrd
import json
import time

from fs_definitions import (all_data, aparc_file_extra_measures,
                            BS_Hip_Tha_stats_f,
                            parc_DK_f2rd, parc_DS_f2rd,
                            FilePerFSVersion)

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

archive_types = ('.zip', '.gz', '.tar.gz')

def is_archive(file):
    archived = False
    archive_type = 'none'
    for ending in archive_types:
        if file.endswith(ending):
            archived = True
            archive_type = ending
            break
    return archived, archive_type


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

    archived, _ = is_archive(_SUBJECT)
    if archived:
        logger.info(f'subject: {_SUBJECT} is archived. Please run through nimb.py -process fs-get-stats')
        ready = False
    else:
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
                    big_file = True,
                    use_params_nimb = True,
                    data_only_volumes=False,
                    new_date = True):
        self.ls_subjects       = ls_subjects
        self.stats_DIR         = stats_DIR
        self.project_vars      = project_vars
        self.PATH2subjects     = self.project_vars["PROCESSED_FS_DIR"][1]
        self.big_file          = big_file
        self.data_only_volumes = data_only_volumes
        self.use_params_nimb   = use_params_nimb
        self.dir_stats         = 'stats'
        self.miss = dict()
        freesurfer_version     = '7.1.1'
        self.get_file               = FilePerFSVersion(freesurfer_version)

        self.define_file_names(new_date)
        self.run()


    def define_file_names(self, new_date):
        self.file_type = self.project_vars["STATS_FILES"]["file_type"]
        if self.file_type == 'default':
            self.file_type = DEFAULT.file_type
        self.fname_fs_all_stats = self.project_vars["STATS_FILES"]["fname_fs_all_stats"]
        if self.fname_fs_all_stats == 'default':
            self.fname_fs_all_stats = DEFAULT.fname_fs_all_stats
        self.fname_fs_subcort_vol = self.project_vars["STATS_FILES"]["fname_fs_subcort_vol"]
        if self.fname_fs_subcort_vol == 'default':
            self.fname_fs_subcort_vol = DEFAULT.fname_fs_subcort_vol
        fname_fs_per_param         = self.project_vars["STATS_FILES"]["fname_fs_per_param"]
        if fname_fs_per_param == 'default':
            fname_fs_per_param = DEFAULT.fname_fs_per_param

        if new_date:
            date = str(time.strftime('%Y%m%d', time.localtime()))
            file_name_nimb_vars = f"{fname_fs_per_param}_{date}.xlsx"
            file_name_fs_vars   = f'stats_fs_with_fs_var_names_{date}.xlsx'
        else:
            file_name_nimb_vars = f"{fname_fs_per_param}.xlsx"
            file_name_fs_vars   = 'stats_fs_with_fs_var_names.xlsx'

        self.dataf_fs          = self.get_path(self.stats_DIR, file_name_fs_vars)
        self.dataf_nimb        = self.get_path(self.stats_DIR, file_name_nimb_vars)
        self.f_miss            = self.get_path(self.stats_DIR,
                                            'subjects_with_missing_files.json')


    def run(self):
        '''
        runs the pipeline to extract FreeSurfer stats to excel file
        '''
        if not self.ls_subjects:
            self.ls_subjects = sorted(listdir(self.PATH2subjects))
            logger.info(f'Extracting stats for subjects located in folder: {self.PATH2subjects}')

        self.writer_fs   = pd.ExcelWriter(self.dataf_fs,   engine = 'xlsxwriter')
        self.writer_nimb = pd.ExcelWriter(self.dataf_nimb, engine = 'xlsxwriter')
        self.sheetnames_fs    = list()
        self.sheetnames_nimb  = list()
        self.row = 1



        for sub in self.ls_subjects:
            subs_left = len(self.ls_subjects[self.ls_subjects.index(sub):])
            logger.info(f'    reading: {sub}; left: {subs_left}')
            path_2sub        = self.get_path(self.PATH2subjects, sub)
            stats_dir_path   = self.get_path(path_2sub, self.dir_stats)
            ready, self.miss = chk_if_all_stats_present(sub, stats_dir_path, self.miss)
            if ready:
                logger.info('    extracting stats for {}'.format(sub))
                self.get_fs_stats_2table(path_2sub, sub)
                self.row += 1
        self.writer_fs.save()
        self.writer_nimb.save()
        self.save_missing()
        self.make_one_sheet()


    def get_fs_stats_2table(self, path_2sub, sub):
        '''Extracting SEGMENTATIONS and PARCELLATIONS'''
        atlases = ('bs', 'hip', 'amy','tha', 'Subcort', 'DK', 'DKT', 'DS', 'WMDK')
        for atlas  in atlases:
            name = all_data["atlas_params"][atlas]['atlas_name']
            logger.info(f'    Atlas: {name}')
            stats_param = all_data["atlas_params"][atlas]['atlas_param']
            parameters = all_data[stats_param]['parameters']
            for hemisphere in all_data[stats_param]['hemi']:
                file = self.get_file.stats_f(atlas, 'stats', hemisphere)
                f_stats_abspath = path.join(path_2sub, file)
                if not self.f_exists(f_stats_abspath, file):
                    file = self.get_file.stats_f(atlas, 'stats_old', hemisphere)
                    f_stats_abspath = path.join(path_2sub, file)
                    logger.info(f'        using old version of {file}')
                if self.f_exists(f_stats_abspath, file):
                    content = list(open(f_stats_abspath,'r'))
                    df, extra_measures = self.get_values(atlas, content, file, stats_param, sub)
                    if len(all_data[stats_param]['parameters']) > 1:
                        for fs_param in parameters:
                            param = self.define_parameter_for_sheet(parameters, fs_param)
                            sheetName = f'{atlas}_{param}_{hemisphere}'
                            if atlas == 'Subcort' and fs_param == 'Volume_mm3':
                                self.sheet_subcort = sheetName
                            df2 = pd.DataFrame()
                            df2[sub] = df[fs_param]
                            df2.index = df['StructName']
                            df2 = df2.transpose()
                            df2 = self.populate_extra_measures(df2, content, fs_param, extra_measures, atlas)
                            self.add_sheet_2df(df2, sheetName, all_data["header_fs2nimb"], atlas)
                    else:
                        param = list(parameters.keys())[0]
                        sheetName = f'{atlas}_{param}_{hemisphere}'
                        self.add_sheet_2df(df, sheetName, all_data["header_fs2nimb"], atlas)


    def get_values(self, atlas, content, file_stats, stats_param, sub):
        if atlas in ('bs', 'hip', 'amy','tha'):
            if '.v12' in file_stats or '.v21' in file_stats:
                new_version = False
                new_files = ('segmentHA_T1.sh', 'segmentThalamicNuclei.sh',
                    'segmentBS.sh')
                for file in new_files:
                    if file in content[0]:
                        new_version = True
                if new_version:
                    values = {i.split(' ')[-1].strip('\n'):i.split(' ')[-2] for i in content[1:]}
                else:
                    values = {i.split(' ')[-2]:i.split(' ')[-1].strip('\n') for i in content}
                if values:
                    df = pd.DataFrame(values, index=[sub])
                else:
                    logger.info(f'    ERROR: file {file} has NO content')
                    index_df = all_data[stats_param]['header']
                    df=pd.DataFrame(np.repeat('nan',len(index_df)), columns=[sub], index=index_df)
                    df=df.T
            else:
                df = self.read_BS_HIP_v10(file_stats, sub)
        else:
            values_raw = content[content.index([x for x in content if 'ColHeaders' in x][0]):]
            if not all_data[stats_param]["two_hemi"]:
                values = [values_raw[0].split()[4:]]
                for line in values_raw[1:]:
                    values.append(line.split()[2:])
            else:
                values = [values_raw[0].split()[2:]]
                for line in values_raw[1:]:
                    values.append(line.split())
            df = pd.DataFrame(values[1:], columns=values[0])
        extra_measures = self.get_extra_measures(atlas, content)
        return df, extra_measures


    def define_parameter_for_sheet(self, parameters, fs_param):
        param = fs_param
        if self.use_params_nimb:
            param = parameters[fs_param]
        return param


    def read_BS_HIP_v10(self, file, sub):
        '''to read old version FS 6 and older of the brainstem and hippocampus
        stats file
        '''
        df=pd.read_table(file)
        df.loc[-1]=df.columns.values
        df.index=df.index+1
        df=df.sort_index()
        df.columns=['col']
        df['col'],df[sub]=df['col'].str.split(' ',1).str
        df.index=df['col']
        del df['col']
        return df.transpose()



    def get_extra_measures(self, atlas, content):
        '''aparc files have a list of additional parameters in the
        lines that start with the word "Measure"
        this scripts extract those parameters in a dict()
        Args:
            content that was extracted with open
        Return:
            {Region_Parameter: value}, where Region = e.g., Cortex, Parameter = e.g., NumVert
            value = float'''
        d = dict()
        for line in content:
            if 'Measure' in line:
                line_ls = line.split()
                region    = line_ls[2].strip(',')
                fs_param = line_ls[3].strip(',')
                value     = line_ls[-2].strip(',')
                if atlas == 'Subcort':
                    d[fs_param] = value
                else:
                    d[f'{region}_{fs_param}'] = value
        return d


    def populate_extra_measures(self, df, content, fs_param, measures, atlas):
        '''additional parameters extracted with the
        get_extra_measures
        are bieng added to corresponding sheets in the xlsx file
        Args:
            df = current pandas.DataFrame that is being populated
            fs_param = currently looped parameter used to create a sheet
            measures = dict() created with the get_extra_measures
        Return:
            new pandas.DataFrame with the newly populated measures'''

        if fs_param == 'Volume_mm3' and atlas == 'Subcort':
            for extra_param in measures:
                df[extra_param] = measures[extra_param]
        else:
            if fs_param in aparc_file_extra_measures:
                extra_param = aparc_file_extra_measures[fs_param]
                if extra_param in measures:
                    df[extra_param] = measures[extra_param]
                else:
                    df[extra_param] = 'nan'
        return df


    def add_sheet_2df(self, df, sheetname, header, atlas):
        '''adding a populated sheet
        '''
        if sheetname in self.sheetnames_fs:
            df.to_excel(self.writer_fs,
                        sheet_name=sheetname,
                        startcol=0,
                        startrow=self.row,
                        header=False,
                        index=True)
        else:
            df.to_excel(self.writer_fs,
                        sheet_name=sheetname,
                        startcol=0,
                        startrow=0,
                        header=True,
                        index=True)                
            self.sheetnames_fs.append(sheetname)

        if sheetname in self.sheetnames_nimb:
            df.to_excel(self.writer_nimb,
                        sheet_name=sheetname,
                        startcol=0,
                        startrow=self.row,
                        header=False,
                        index=True)
        else:
            if atlas == 'WMDK':
                df.rename(columns=lambda ROI: header[ROI.replace('wm-lh-','').replace('wm-rh-','').replace('Left-','').replace('Right-','')]+self.get_ending_wmdk(ROI[:5]), inplace=True)
            else:
                df.rename(columns=lambda ROI: header[ROI], inplace=True)
            df.to_excel(self.writer_nimb,
                        sheet_name=sheetname,
                        startcol=0,
                        startrow=0,
                        header=True,
                        index=True)
            self.sheetnames_nimb.append(sheetname)
        return df


    def get_ending_wmdk(self, str):
        if str == 'wm-lh' or str == 'Left-':
            ending = 'L'
        elif str == 'wm-rh' or  str == 'Right':
            ending = 'R'
        return ending


    def f_exists(self, f_abspath, file):
        f_exists = True
        if not path.isfile(f_abspath):
            f_exists = False
            logger.info(f'        ERROR {file} is missing')
        return f_exists


    def save_missing(self):
        if self.miss:
            logger.info('ERROR: some subjects are missing the required files. Check file: {}'.format(self.f_miss))
            self.save_json(self.miss, self.f_miss)


    def make_one_sheet(self):
        if self.big_file:
            from fs_stats_utils import FSStatsUtils
            fs_utils = FSStatsUtils(self.dataf_nimb,
                                    self.stats_DIR,
                                    self.project_vars["id_col"],
                                    self.sheetnames_nimb,
                                    self.sheet_subcort,
                                    Table)
            fs_utils.create_BIG_data_file(self.fname_fs_all_stats, self.file_type)
            if self.data_only_volumes:
                fs_utils.create_file_with_only_subcort_volumes(self.fname_fs_subcort_vol, self.file_type)


    def get_path(self, link1, link2):
        return path.join(link1, link2).replace(sep, '/')


    def save_json(self, d, f):
        with open(f, 'w') as jf:
            json.dump(d, jf, indent=4)

    # OLD SCRIPTS, were adjusted; 
    # def get_bs_hip_amy_tha(self, stats_dir_path, sub):
    #     '''Extracting Brainstem,  Hippocampus, Amygdala, Thalamus'''
    #     logger.info('    Brainstem,  Hippocampus, Amygdala, Thalamus running')
    #     for atlas_hemi in BS_Hip_Tha_stats_f:
    #         file_with_stats = [i for i in BS_Hip_Tha_stats_f[atlas_hemi] if path.exists(path.join(stats_dir_path.replace('/stats',''),i))][0]
    #         if file_with_stats:
    #             file = path.join(stats_dir_path.replace('/stats',''), file_with_stats)
    #             if '.v12' in file_with_stats or '.v21' in file_with_stats:
    #                 df = self.read_BS_HIP_AMY_THA_v12_v21(file, sub)
    #             else:
    #                 df = self.read_BS_HIP_v10(file, sub)
    #         else:
    #             logger.info('    ERROR, '+atlas_hemi+' stats file is missing\n')
    #             index_df = brstem_hip_header[atlas_hemi]
    #             df=pd.DataFrame(np.repeat('nan',len(index_df)), columns=[sub], index=index_df)
    #             df=df.T
    #         self.add_sheet_2df(df, atlas_hemi, brstem_hip_header['all'], atlas_hemi)


    # def read_BS_HIP_AMY_THA_v12_v21(self, file, sub):
    #     content=open(file,'r').readlines()
    #     if 'amygdalar-nuclei' in file or 'thalamic-nuclei' in file:
    #         d_data = {i.split(' ')[-1].strip('\n'):i.split(' ')[-2] for i in content[1:]}
    #     else:
    #         d_data = {i.split(' ')[-2]:i.split(' ')[-1].strip('\n') for i in content}
    #         if 'by' in d_data:
    #             d_data.pop('by', None)
    #         if d_data:
    #             if list(d_data.keys())[0] not in brstem_hip_header['all']:
    #                 new_d_data = dict()
    #                 for key in d_data:
    #                     new_d_data[d_data[key]] = key
    #                 d_data = new_d_data
    #         else:
    #             logger.info(f'    ERROR: file {file} has NO content')
    #             d_data = {'nan': 'nan'}
    #     return pd.DataFrame(d_data, index=[sub])


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

    parser.add_argument(
        "-stats_dir", required=False,
        default='home',
        help="path to save stats files",
    )

    parser.add_argument(
        "-dir_fs_stats", required=False,
        default='default',
        help="path to folder with FreeSurfer subjects/stats",
    )

    params = parser.parse_args()
    return params


if __name__ == "__main__":

    try:
        from pathlib import Path
    except ImportError as e:
        print('please install pathlib')
        sys.exit(e)

    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[2]
    sys.path.append(str(top))

    from setup.get_vars import Get_Vars
    from stats.db_processing import Table
    from distribution.distribution_definitions import DEFAULT

    project_ids = Get_Vars().get_projects_ids()
    params      = get_parameters(project_ids)
    all_vars    = Get_Vars(params)
    project_vars  = all_vars.projects[params.project]

    if params.stats_dir == 'home':
        all_vars.params.stats_dir = project_vars["STATS_PATHS"]["STATS_HOME"]
    if params.dir_fs_stats != 'default':
        project_vars["PROCESSED_FS_DIR"][1] = params.dir_fs_stats
    ls_subjects   = []

    # if "STATS_FILES" in project_vars:
    #     stats_files   = project_vars["STATS_FILES"]
    # else:
    #     stats_files   = {
    #    "fname_fs_per_param"     : "stats_FreeSurfer_per_param",
    #    "fname_fs_all_stats"     : "stats_FreeSurfer_all",
    #    "fname_fs_subcort_vol"   : "stats_FreeSurfer_subcortical",
    #    "file_type"              : "xlsx"}

    # getvars           = Get_Vars()
    # vars_stats        = getvars.stats_vars
    # default_stats_dir = vars_stats["STATS_PATHS"]["STATS_HOME"]

    # projects      = getvars.projects
    # all_projects  = [i for i in projects.keys() if 'EXPLANATION' not in i and 'LOCATION' not in i]
    # params        = get_parameters(all_projects, default_stats_dir)
    # project_vars  = projects[params.project]
    # ls_subjects   = []
    # stats_DIR     = params.stats_dir

    FSStats2Table(ls_subjects,
                    all_vars.params.stats_dir,
                    project_vars,
                    big_file = True,
                    use_params_nimb = True,
                    data_only_volumes=False,
                    new_date = True)

