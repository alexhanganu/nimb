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
import os
import sys
import argparse
from os import path, listdir, sep, system

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
                    all_vars,
                    project,
                    big_file = True,
                    use_params_nimb = True,
                    data_only_volumes=False,
                    new_date = True):
        self.ls_subjects       = ls_subjects
        self.stats_DIR         = all_vars.params.stats_dir
        self.project           = project
        self.project_vars      = all_vars.projects[project]
        self.PATH2subjects     = self.project_vars["PROCESSED_FS_DIR"][1]
        self.big_file          = big_file
        self.data_only_volumes = data_only_volumes
        self.use_params_nimb   = use_params_nimb
        self.fs_home           = all_vars.location_vars['local']["FREESURFER"]["FREESURFER_HOME"]
        user_fs_version        = all_vars.location_vars['local']["FREESURFER"]["version"]
        self.fsver, _, _, _    = fs_definitions.fs_version(self.fs_home, user_fs_version)

        self.atlas_data        = atlas_definitions.atlas_data
        self.stats_files       = atlas_definitions.all_stats_files(self.fsver)
        self.miss              = dict()
        logger.info(f"    FreeSurfer version is: {self.fsver}")
        self.define_file_names(new_date)
        self.define_atlas_criteria()
        self.get_data          = fs_read_fs_textfile.TextDataGet()
        self.run()


    def define_file_names(self, new_date):
        fname_fs_per_param = self.project_vars["STATS_FILES"]["fname_fs_per_param"]
        if fname_fs_per_param == 'default':
            fname_fs_per_param = DEFAULT.fname_fs_per_param
        f_miss_name = 'subjects_with_missing_files.json'

        if new_date:
            date = str(time.strftime('%Y%m%d', time.localtime()))
            file_name_fs_vars        = f'stats_fs_with_fs_var_names_{date}.xlsx'
            file_name_nimb_vars      = f"{fname_fs_per_param}_{date}.xlsx"
            file_name_fs_vars_miss   = f'stats_fs_with_fs_var_names_missing_data_{date}.xlsx'
            file_name_nimb_vars_miss = f"{fname_fs_per_param}_missing_data_{date}.xlsx"
        else:
            file_name_fs_vars        = 'stats_fs_with_fs_var_names.xlsx'
            file_name_nimb_vars      = f"{fname_fs_per_param}.xlsx"
            file_name_fs_vars_miss   = 'stats_fs_with_fs_var_names_missing_data.xlsx'
            file_name_nimb_vars_miss = f"{fname_fs_per_param}_missing_data.xlsx"

        self.dataf_fs        = self.get_path(self.stats_DIR, file_name_fs_vars)
        self.dataf_nimb      = self.get_path(self.stats_DIR, file_name_nimb_vars)
        self.f_miss          = self.get_path(self.stats_DIR, f_miss_name)
        self.dataf_fs_miss   = self.get_path(self.stats_DIR, file_name_fs_vars_miss)
        self.dataf_nimb_miss = self.get_path(self.stats_DIR, file_name_nimb_vars_miss)


    def define_atlas_criteria(self):
        self.nuclei_atlases    = [i for i in self.atlas_data if "nuclei" in self.atlas_data[i]["group"]]
        # aiming to create independent sheet for subcortical structures;
        # Name MUST be similar to atlas in atlas_definitions.atlas_data
        params = atlas_definitions.params_vols
        subcort_atlas          = [i for i in self.atlas_data if self.atlas_data[i]["group"] == "subcortical"]
        # will use only the Vol parameter
        subcort_param          = [i for i in params if "Vol" in i]
        self.criteria_4subcort = subcort_atlas + subcort_param
        self.sheet_subcort     = subcort_atlas[0] + "_"+params[subcort_param[0]]


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

        self.d_file_subjects = dict()
        for sub in self.ls_subjects:
            path_2sub        = self.get_path(self.PATH2subjects, sub)
            self.chk_if_all_stats_present(sub, path_2sub)
        if self.d_file_subjects:
            logger.info(f'ERR: multiple subject have missing files:')
            for file in self.d_file_subjects:
                logger.info(f'     file: {file}, is missing in {len(self.d_file_subjects[file])} participants')

        logger.info(f'\n\n')
        for sub in self.ls_subjects:
            archived, _ = is_archive(sub)
            if not archived:
                subs_left = len(self.ls_subjects[self.ls_subjects.index(sub):])
                path_2sub        = self.get_path(self.PATH2subjects, sub)
                logger.info(f'    extracting stats for {sub}; left: {subs_left}')
                self.get_fs_stats_2table(path_2sub, sub)
                self.row += 1
            else:
                logger.info(f'subject: {sub} is archived. Please run:')
                logger.info(f'    cd {self.fs_home}')
                logger.info(f'    python nimb.py -project {self.project} -process run -do fs-get-stats')
        self.writer_fs.save()
        self.writer_nimb.save()
        self.save_missing()

        if self.big_file:
            self.make_one_sheet()


    def chk_if_all_stats_present(self,
                                _SUBJECT,
                                path_2sub):
        ''' check if subject has all stats files
        Args:
            _SUBJECT: sub to check, str
            path_2sub: path to _SUBJECT
        Return:
            populates self.miss with new missing _SUBJECT or missing files
        '''
        for atlas in self.stats_files:
            for file in self.stats_files[atlas]:
                if not path.isfile(path.join(path_2sub, file)):
                    if _SUBJECT not in self.miss:
                        self.miss[_SUBJECT] = list()
                    self.miss[_SUBJECT].append(file)
                    if file not in self.d_file_subjects:
                        self.d_file_subjects[file] = list()
                    self.d_file_subjects[file].append(_SUBJECT)


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
                    # content = ""
                    # try:
                    #     content = list(open(self.f_stats_abspath,'r'))
                    # except Exception as e:
                    #     print(e)
                    # if not content:
                    #     print("ERR! file: ", self.f_stats_abspath, " is empty")
                    #     break
                    df, extra_measures = self.get_data.get_values(atlas, self.f_stats_abspath, file, sub)
                    # df, extra_measures = self.get_values(atlas, content, file, sub)
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
                            df2 = self.populate_extra_measures(df2, fs_param, extra_measures, atlas)
                            self.add_sheet_2df(df2, sheetName, header_fs2nimb_dict, atlas)
                    else:
                        param = list(parameters.keys())[0]
                        sheetName = f'{atlas}_{param}_{hemisphere}'
                        self.add_sheet_2df(df, sheetName, header_fs2nimb_dict, atlas)


    def define_parameter_for_sheet(self, parameters, fs_param):
        param = fs_param
        if self.use_params_nimb:
            param = parameters[fs_param]
        return param


    def populate_extra_measures(self, df, fs_param, measures, atlas):
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
        from fs_stats_utils import FSStatsUtils
        file_type = self.project_vars["STATS_FILES"]["file_type"]
        if file_type == 'default':
            file_type = DEFAULT.file_type
        fname_fs_all_stats = self.project_vars["STATS_FILES"]["fname_fs_all_stats"]
        if fname_fs_all_stats == 'default':
            fname_fs_all_stats = DEFAULT.fname_fs_all_stats
        fname_fs_subcort_vol = self.project_vars["STATS_FILES"]["fname_fs_subcort_vol"]
        if fname_fs_subcort_vol == 'default':
            fname_fs_subcort_vol = DEFAULT.fname_fs_subcort_vol

        fs_utils = FSStatsUtils(self.dataf_nimb,
                                self.stats_DIR,
                                self.project_vars["id_col"],
                                self.sheetnames_nimb,
                                self.sheet_subcort,
                                Table)
        fs_utils.create_BIG_data_file(fname_fs_all_stats,
                                    file_type)
        if self.data_only_volumes:
            fs_utils.create_file_with_only_subcort_volumes(fname_fs_subcort_vol, file_type)


    def get_path(self, link1, link2):
        return path.join(link1, link2).replace(sep, '/')


    def save_json(self, d, f):
        with open(f, 'w') as jf:
            json.dump(d, jf, indent=4)

    # MOVED TO fs_read_fs_textfile on 20230318. Goal was to make on file that would read all FreeSurfer text files
    # def get_values(self, atlas, content, file_name, sub):
    #     # alternatively, code written by nipy/nibabel probably Chris Markiewicz @effigies
    #     # with open(file_path, 'r') as f:
    #     # -        for line in f:
    #     # -            if re.findall(r'ColHeaders .*', line):
    #     # -                column_names = line.split()[2:]
    #     # -                break
    #     # -    f.close()
    #     # -    stats = np.loadtxt(file_path, comments='#', dtype=str)
    #     if atlas in self.nuclei_atlases:
    #         values = ""
    #         if '.v12' in file_name or '.v21' in file_name:
    #             new_version = False
    #             new_files = ('segmentHA_T1.sh',
    #                         'segmentThalamicNuclei.sh',
    #                         'segmentBS.sh')
    #             for file in new_files:
    #                 if file in content[0]:
    #                     new_version = True
    #             if new_version:
    #                 values = {i.split(' ')[-1].strip('\n'):i.split(' ')[-2] for i in content[1:]}
    #             else:
    #                 values = {i.split(' ')[-2]:i.split(' ')[-1].strip('\n') for i in content}
    #         elif "Hypothalamic" in content[0]:
    #             values = {i.split(" ")[-1].strip("\n"):i.split(" ")[-3] for i in content}
    #             values.pop("Stats",None)
    #         else:
    #             df = self.read_BS_HIP_v10(sub)

    #         if values:
    #             df = pd.DataFrame(values, index=[sub])
    #         else:
    #             logger.info(f'    ERROR: file {file_name} has NO content')
    #             index_df = self.atlas_data[atlas]['header']
    #             df=pd.DataFrame(np.repeat('nan',len(index_df)), columns=[sub], index=index_df)
    #             df=df.T
    #     else:
    #         values_raw = content[content.index([x for x in content if 'ColHeaders' in x][0]):]
    #         if len(self.atlas_data[atlas]["hemi"]) < 2:
    #         # if not fs_definitions.all_data[stats_param]["two_hemi"]:
    #             values = [values_raw[0].split()[4:]]
    #             for line in values_raw[1:]:
    #                 values.append(line.split()[2:])
    #         else:
    #             values = [values_raw[0].split()[2:]]
    #             for line in values_raw[1:]:
    #                 values.append(line.split())
    #         df = pd.DataFrame(values[1:], columns=values[0])
    #     extra_measures = self.get_extra_measures(atlas, content)
    #     return df, extra_measures


    # def read_BS_HIP_v10(self, sub):
    #     '''to read old version FS 6 and older of the brainstem and hippocampus
    #     stats file
    #     '''
    #     df=pd.read_table(self.f_stats_abspath)
    #     df.loc[-1]=df.columns.values
    #     df.index=df.index+1
    #     df=df.sort_index()
    #     df.columns=['col']
    #     df['col'],df[sub]=df['col'].str.split(' ',1).str
    #     df.index=df['col']
    #     del df['col']
    #     return df.transpose()


    # def get_extra_measures(self, atlas, content):
    #     '''aparc files have a list of additional parameters in the
    #     lines that start with the word "Measure"
    #     this scripts extract those parameters in a dict()
    #     Args:
    #         content that was extracted with open
    #     Return:
    #         {Region_Parameter: value}, where Region = e.g., Cortex, Parameter = e.g., NumVert
    #         value = float'''
    #     d = dict()
    #     for line in content:
    #         if 'Measure' in line:
    #             line_ls  = line.split()
    #             region   = line_ls[2].strip(',')
    #             fs_param = line_ls[3].strip(',')
    #             value    = line_ls[-2].strip(',')
    #             if atlas in self.criteria_4subcort:
    #                 d[fs_param] = value
    #             else:
    #                 d[f'{region}_{fs_param}'] = value
    #     return d


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
        help="list of subjects to be processed, e.g.,: \"subject1\", \"subject2\", written between brackets and devided by commma",
    )

    params = parser.parse_args()
    return params


if __name__ == "__main__":

    try:
        import pathlib
        file = pathlib.Path(__file__).resolve()
        top = file.parents[2]
    except ImportError as e:
        print('please install pathlib', e)
        "/".join(os.path.abspath(file_).split("/")[:-3])

    sys.path.append(str(top))

    from setup.get_vars import Get_Vars
    from stats.db_processing import Table
    from distribution.distribution_definitions import DEFAULT
    from distribution.manage_archive import is_archive
    from processing.atlases import atlas_definitions
    import fs_definitions
    import fs_read_fs_textfile

    project_ids  = Get_Vars().get_projects_ids()
    params       = get_parameters(project_ids)
    all_vars     = Get_Vars(params)
    project      = params.project
    project_vars = all_vars.projects[project]

    if params.stats_dir == 'home':
        all_vars.params.stats_dir = project_vars["STATS_PATHS"]["STATS_HOME"]
    if params.dir_fs_stats != 'default':
        all_vars.projects[project]["PROCESSED_FS_DIR"][1] = params.dir_fs_stats
    ls_subjects = params.list_of_subjects
    if ls_subjects:
        ls_subjects =  ls_subjects.split(",")



    FSStats2Table(ls_subjects,
                    all_vars,
                    project,
                    big_file = True,
                    use_params_nimb = True,
                    data_only_volumes=False,
                    new_date = True)

