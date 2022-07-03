#!/bin/python
'''
version: 20220630
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

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
                    fs_ver,
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
        self.miss              = dict()
        self.fsver             = fs_ver#'7.2.0'
        self.atlas_data        = atlas_definitions.atlas_data
        self.stats_files       = atlas_definitions.all_stats_files()
        # aiming to create independent sheet for subcortical structures;
        # Name MUST be similar to atlas in atlas_definitions.atlas_data
        self.nuclei_atlases    = [i for i in self.atlas_data if "nuclei" in self.atlas_data[i]["group"]]
        self.criteria_4subcort = ['SubCtx', 'Volume_mm3']
        self.sheet_subcort     = "SubCtx_Volmm3"

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
            ready           = self.chk_if_all_stats_present(sub,
                                                            path_2sub)
            if ready:
                logger.info('    extracting stats for {}'.format(sub))
                self.get_fs_stats_2table(path_2sub, sub)
                self.row += 1
        self.writer_fs.save()
        self.writer_nimb.save()
        self.save_missing()
        self.make_one_sheet()


    def chk_if_all_stats_present(self,
                                _SUBJECT,
                                path_2sub):
        ''' check if subject has all stats files
        Args:
            _SUBJECT: sub to check, str
            path_2sub: path to _SUBJECT
        Return:
            ready: _SUBJECT has all required files and is ready to undergo stats extraction
            populates self.miss with new missing _SUBJECT or missing files
        '''
        def add_2dict(_SUBJECT, file):
            if _SUBJECT not in self.miss:
                self.miss[_SUBJECT] = list()
            self.miss[_SUBJECT].append(file)

        ready = True
        archived, _ = is_archive(_SUBJECT)
        if archived:
            logger.info(f'subject: {_SUBJECT} is archived. Please run through nimb.py -project PROJECT_NAME -process run -do fs-get-stats')
            ready = False
        else:
            for atlas in self.stats_files:
                for file in self.stats_files[atlas]:
                    if not path.isfile(path.join(path_2sub
                                                file)):
                        logger.info(f'missing: {file}')
                        ready = False
                        add_2dict(_SUBJECT, file)
        return ready


    def get_fs_stats_2table(self, path_2sub, sub):
        '''Extracting SEGMENTATIONS and PARCELLATIONS'''
        # for atlas  in atlases:
        header_fs2nimb_dict = atlas_definitions.header_fs2nimb
        for atlas in self.atlas_data:
            name = self.atlas_data[atlas]['atlas_name']
            logger.info(f'    Atlas: {name}')
            for hemisphere in self.atlas_data[atlas]['hemi']:
                file = atlas_definitions.stats_f(self.fsver, atlas, 'stats', hemisphere)
                self.f_stats_abspath = path.join(path_2sub, file)
                if not self.f_exists(self.f_stats_abspath):
                    file = atlas_definitions.stats_f(self.fsver, atlas,
                                                    'stats_old', hemisphere)
                    self.f_stats_abspath = path.join(path_2sub, file)
                    logger.info(f'        using old version of {file}')
                if self.f_exists(self.f_stats_abspath):
                    content = ""
                    try:
                        content = list(open(self.f_stats_abspath,'r'))
                    except Exception as e:
                        print(e)
                    if not content:
                        print("ERR! file: ", self.f_stats_abspath, " is empty")
                        break
                    df, extra_measures = self.get_values(atlas, content, file, sub)
                    parameters = self.atlas_data[atlas]['parameters']
                    if len(parameters) > 1:
                        for fs_param in parameters:
                            param = self.define_parameter_for_sheet(parameters, fs_param)
                            sheetName = f'{atlas}_{param}_{hemisphere}'
                            if atlas in self.criteria_4subcort and fs_param in self.criteria_4subcort:
                                self.sheet_subcort = sheetName
                            df2 = pd.DataFrame()
                            df2[sub] = df[fs_param]
                            df2.index = df['StructName']
                            df2 = df2.transpose()
                            df2 = self.populate_extra_measures(df2, content, fs_param, extra_measures, atlas)
                            self.add_sheet_2df(df2, sheetName, header_fs2nimb_dict, atlas)
                    else:
                        param = list(parameters.keys())[0]
                        sheetName = f'{atlas}_{param}_{hemisphere}'
                        self.add_sheet_2df(df, sheetName, header_fs2nimb_dict, atlas)


    def get_values(self, atlas, content, file_name, sub):
        if atlas in self.nuclei_atlases:
            if '.v12' in file_name or '.v21' in file_name:
                new_version = False
                new_files = ('segmentHA_T1.sh',
                            'segmentThalamicNuclei.sh',
                            'segmentBS.sh')
                for file in new_files:
                    if file in content[0]:
                        new_version = True
                if new_version:
                    values = {i.split(' ')[-1].strip('\n'):i.split(' ')[-2] for i in content[1:]}
                else:
                    values = {i.split(' ')[-2]:i.split(' ')[-1].strip('\n') for i in content}
            elif "Hypothalamic" in content[0]:
                values = {i.split(" ")[-1].strip("\n"):i.split(" ")[-3] for i in content}
                values.pop("Stats",None)
            else:
                df = self.read_BS_HIP_v10(sub)

            if values:
                df = pd.DataFrame(values, index=[sub])
            else:
                logger.info(f'    ERROR: file {file} has NO content')
                index_df = self.atlas_data[atlas]['header']
                # index_df = fs_definitions.all_data[stats_param]['header']
                df=pd.DataFrame(np.repeat('nan',len(index_df)), columns=[sub], index=index_df)
                df=df.T
        else:
            values_raw = content[content.index([x for x in content if 'ColHeaders' in x][0]):]
            if len(self.atlas_data[atlas]["hemi"]) < 2:
            # if not fs_definitions.all_data[stats_param]["two_hemi"]:
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


    def read_BS_HIP_v10(self, sub):
        '''to read old version FS 6 and older of the brainstem and hippocampus
        stats file
        '''
        df=pd.read_table(self.f_stats_abspath)
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
                line_ls  = line.split()
                region   = line_ls[2].strip(',')
                fs_param = line_ls[3].strip(',')
                value    = line_ls[-2].strip(',')
                if atlas in self.criteria_4subcort:
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

        if fs_param in self.criteria_4subcort and atlas in self.criteria_4subcort:
            for extra_param in measures:
                df[extra_param] = measures[extra_param]
        else:
            if fs_param in atlas_definitions.aparc_file_extra_measures:
                extra_param = atlas_definitions.aparc_file_extra_measures[fs_param]
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


    def f_exists(self, f_abspath):
        f_exists = True
        if not path.isfile(f_abspath):
            f_exists = False
            logger.info(f'        ERROR {f_abspath} is missing')
        return f_exists


    def save_missing(self):
        if self.miss:
            logger.info(f'ERROR: some subjects are missing the required files. Check file: {self.f_miss}')
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

    parser.add_argument(
        "-list_of_subjects", required=False,
        default=[],
        help="list of subjects to be processed, e.g.,: subject1, subject2",
    )

    params = parser.parse_args()
    return params


# archives_supported = ('.zip', '.gz', '.tar.gz')

# def is_archive(file):
#     archived = False
#     archive_type = 'none'
#     for ending in archives_supported:
#         if file.endswith(ending):
#             archived = True
#             archive_type = ending
#             break
#     return archived, archive_type


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
    from distribution.manage_archive import is_archive
    from processing.atlases import atlas_definitions
    import fs_definitions

    project_ids  = Get_Vars().get_projects_ids()
    params       = get_parameters(project_ids)
    all_vars     = Get_Vars(params)
    project_vars = all_vars.projects[params.project]
    fs_ver_long  = all_vars.location_vars['local']["FREESURFER"]["freesurfer_version"]
    fs_ver       = fs_definitions.FreeSurferVersion(fs_ver_long).fs_ver()

    if params.stats_dir == 'home':
        all_vars.params.stats_dir = project_vars["STATS_PATHS"]["STATS_HOME"]
    if params.dir_fs_stats != 'default':
        project_vars["PROCESSED_FS_DIR"][1] = params.dir_fs_stats
    ls_subjects_testing = params.list_of_subjects
    print("list subjects testing is:", ls_subjects_testing)
    ls_subjects   = []


    FSStats2Table(ls_subjects,
                    all_vars.params.stats_dir,
                    project_vars,
                    fs_ver,
                    big_file = True,
                    use_params_nimb = True,
                    data_only_volumes=False,
                    new_date = True)

