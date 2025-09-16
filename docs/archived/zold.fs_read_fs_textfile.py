#!/bin/python
'''
version: 20230318
Extract data from FreeSurfer text files

'''
import os
import pandas
import numpy

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from processing.atlases import atlas_definitions


class TextDataGet:
    '''extract data from text files
    Args:
        abspath to file
    Return:
        pandas.DataFrame() of values
    '''
    def __init__(self):
        self.atlas_data        = atlas_definitions.atlas_data
        params = atlas_definitions.params_vols
        subcort_atlas          = [i for i in self.atlas_data if self.atlas_data[i]["group"] == "subcortical"]
        subcort_param          = [i for i in params if "Vol" in i]
        self.criteria_4subcort = subcort_atlas + subcort_param
        self.nuclei_atlases    = [i for i in self.atlas_data if "nuclei" in self.atlas_data[i]["group"]]
        self.nuclei_new_stats  = ('segmentHA_T1.sh',
                                  'segmentThalamicNuclei.sh',
                                  'segmentBS.sh')

    def content_get(self,
                 file_abspath):
        self.file = file_abspath
        # logger.info(f'     file: {self.file}')
        content = ""
        if  os.path.isfile(self.file):
            try:
                content = list(open(self.file,'r'))
            except Exception as e:
                logger.info(e)
        else:
            logger.info(f'        ERROR {self.file} is missing')
        return content


    def get_values(self, atlas, file_abspath, file_name, sub):
        content = self.content_get(file_abspath)
        if not content:
            print("ERR! file: ", self.file, " is empty")

        values = ""
        if atlas in self.nuclei_atlases:
            new_version = False
            for file in self.nuclei_new_stats:
                if file in content[0]:
                    new_version = True

            if "Hypothalamic" in content[0]:
                values = {i.split(" ")[-1].strip("\n"):i.split(" ")[-3] for i in content}
                values.pop("Stats",None)
            elif new_version:
                values = {i.split(' ')[-1].strip('\n'):i.split(' ')[-2] for i in content[1:]}
            elif '.v10' in file_name:
                df = self.read_BS_HIP_v10(sub)
            else:
                values = {i.split(' ')[-2]:i.split(' ')[-1].strip('\n') for i in content}

            if values:
                df = pandas.DataFrame(values, index=[sub])
            else:
                logger.info(f'    ERROR: file {file_name} has NO content')
                index_df = self.atlas_data[atlas]['header']
                df=pandas.DataFrame(numpy.repeat('nan',len(index_df)), columns=[sub], index=index_df)
                df=df.T
        else:
            # alternatively, code written by nipy/nibabel probably Chris Markiewicz @effigies
            # with open(file_path, 'r') as f:
            # -        for line in f:
            # -            if re.findall(r'ColHeaders .*', line):
            # -                column_names = line.split()[2:]
            # -                break
            # -    f.close()
            # -    stats = np.loadtxt(file_path, comments='#', dtype=str)
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
            df = pandas.DataFrame(values[1:], columns=values[0])
        extra_measures = self.get_extra_measures(atlas, content)
        return df, extra_measures


    def read_BS_HIP_v10(self, sub):
        '''to read old version FS 6 and older of the brainstem and hippocampus
        stats file
        '''
        df=pandas.read_table(self.file)
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
