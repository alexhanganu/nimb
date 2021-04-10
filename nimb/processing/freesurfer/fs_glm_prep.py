'''
last update: 20201218
check that all subjects are present in the FS_SUBJECTS_DIR folder
in order to perform the FreeSurfer glm
'''

import os
import sys
import json
import shutil
import linecache
from setup.interminal_setup import get_yes_no
from stats.db_processing import Table
from distribution.utilities import save_json

try:
    import pandas as pd
    import xlrd
    import openpyxl
    from pathlib import Path
except ImportError as e:
    print('could not import modules: pandas or xlrd or openpyxl.\
        try to install them using pip, or use the miniconda run with the command located \
        in credentials_path.py/local.json -> miniconda_python_run')
    sys.exit(e)

class ChkFSQcache:
    '''FS GLM requires two folders: surf and label
        script checks that both folders are present
        checks that all GLM files are present
    Args:
        path2chk: path to the folder with the subject
        _id: ID of the subject to chk
    Return:
        populates list of missing subjects
    '''
    def __init__(self, path2chk, _id, vars_fs):
        self.miss       = {}
        self.path2chk   = path2chk
        self._id        = _id
        self.GLM_meas   = vars_fs["GLM_measurements"]
        self.GLM_thresh = vars_fs["GLM_thresholds"]
        self.chk_f()

    def chk_f(self):
        if os.path.exists(os.path.join(self.path2chk, self._id, 'surf')) and os.path.exists(os.path.join(self.path2chk, self._id, 'label')):
            for hemi in ['lh','rh']:
                for meas in self.GLM_meas:
                    for thresh in self.GLM_thresh:
                        file = '{}.{}.fwhm{}.fsaverage.mgh'.format(hemi, meas, str(thresh))
                        if not os.path.exists(os.path.join(self.path2chk, self._id, 'surf', file)):
                            self.populate_miss(file)
        else:
            self.populate_miss('surf label missing')

    def populate_miss(self, file):
        if self._id not in self.miss:
            self.miss[self._id] = list()
        self.miss[self._id].append(file)


class CheckIfReady4GLM():

    def __init__(self, nimb_vars, fs_vars, proj_vars, f_ids_processed, f_GLM_group, FS_GLM_dir):
        self.proj_vars         = proj_vars
        self.vars_fs           = fs_vars
        self.FS_SUBJECTS_DIR   = fs_vars['FS_SUBJECTS_DIR']
        self.NIMB_PROCESSED_FS = nimb_vars["NIMB_PROCESSED_FS"]
        self.f_ids_processed   = f_ids_processed
        self.f_GLM_group       = f_GLM_group
        self.FS_GLM_dir        = FS_GLM_dir
        self.archive_type      = '.zip'
        self.tab               = Table()
        self.miss              = dict()
        self.ids_4fs_glm       = dict()
        self.df                = self.tab.get_df(self.f_GLM_group)
        self.bids_ids          = self.df[self.proj_vars['id_col']].tolist()

    def chk_if_subjects_ready(self):

        fs_proc_ids = self.get_ids_processed('fs')
        miss_bids_ids = [i for i in self.bids_ids if i not in fs_proc_ids.keys()]
        if miss_bids_ids:
            print(f'    some IDs are missing from the {self.f_ids_processed} file: {miss_bids_ids}')
            for bids_id in miss_bids_ids:
                self.add_to_miss(bids_id, 'id_missing')

        if len(miss_bids_ids) < len(fs_proc_ids.keys()):
            for bids_id in [i for i in self.bids_ids if i not in miss_bids_ids]:
                fs_proc_id = fs_proc_ids[bids_id].replace(self.archive_type,'')
                if os.path.exists(os.path.join(self.FS_SUBJECTS_DIR, bids_id)):
                    self.ids_4fs_glm[bids_id] = bids_id
                    self.chk_glm_files(bids_id)
                elif os.path.exists(os.path.join(self.FS_SUBJECTS_DIR, fs_proc_id)):
                    self.ids_4fs_glm[bids_id] = fs_proc_id
                    # self.chk_glm_files(fs_proc_id) #!!!!!!!!!!!!!!!!!! UNCOMMENT
                else:
                    print(f'id {bids_id} or freesurfer id {fs_proc_id} \
                        are missing from the {self.FS_SUBJECTS_DIR} folder')
                    self.add_to_miss(bids_id, 'id_missing')
            if self.miss.keys():
                save_json(self.miss, os.path.join(self.FS_GLM_dir, 'excluded_from_glm.json'))
                subjs_missing = len(self.miss.keys())
                subjs_present = len(self.ids_4fs_glm.keys())
                print(f'    {subjs_missing} missing \n\
    {subjs_present} present\n\
         in the folder: {self.FS_SUBJECTS_DIR}')
                if get_yes_no('do you want to do glm analysis with current subjects ? (y/n)') == 1:
                    self.create_fs_glm_df()
                    return True, list()
                else:
                    return False, list(self.miss.keys())
            else:
                self.create_fs_glm_df()
                return True, list()
        else:
            print('no ids found')
            return False, list()

    def chk_glm_files(self, bids_id):
        '''it is expected that the BIDS IDs are located in FS_SUBJECTS_DIR
            script checks if subjects are present
        Args:
            bids_id: ID of the subject to chk
        Return:
            populates list of missing subjects
            populates dict with ids
        '''
        files_ok = ChkFSQcache(self.FS_SUBJECTS_DIR, bids_id, self.vars_fs)
        if not files_ok:
            for file in files_ok:
                self.add_to_miss(bids_id, file)
            return False
        else:
            return True

    def create_fs_glm_df(self):
        self.rm_missing_ids()
        tmp_id = 'fs_id'
        print('    creating the glm file for FreeSurfer GLM analysis')
        d_ids = {self.proj_vars['id_col']: [i for i in list(self.ids_4fs_glm.keys())],
                tmp_id                   : [i for i in list(self.ids_4fs_glm.values())]}
        fs_proc_df     = self.tab.create_df_from_dict(d_ids)
        fs_proc_df     = self.tab.change_index(fs_proc_df, self.proj_vars['id_col'])
        grid_fs_df_pre = self.tab.change_index(self.df,    self.proj_vars['id_col'])
        self.df_ids     = self.tab.join_dfs(grid_fs_df_pre, fs_proc_df, how='outer')
        self.df_ids.rename(columns={tmp_id: self.proj_vars['id_col']}, inplace=True)
        self.df_ids = self.tab.change_index(self.df_ids, self.proj_vars['id_col'])
        self.tab.save_df(self.df_ids, self.f_GLM_group)
        PrepareForGLM(self.FS_SUBJECTS_DIR,
                    self.FS_GLM_dir,
                    self.f_GLM_group, 
                    self.proj_vars,
                    self.vars_fs)

    def rm_missing_ids(self):
        ls_ix_2rm = list()
        for ix in self.df.index:
            bids_id = self.df.at[ix, self.proj_vars['id_col']]
            if bids_id not in self.ids_4fs_glm.keys():
                ls_ix_2rm.append(ix)
        print(f'        {len(ls_ix_2rm)} subjects are missing and will be removed from futher analysis')
        self.df = self.df.drop(ls_ix_2rm)


    def get_ids_processed(self, method):
        '''retrieves the bids names of the IDs provided in the GLM file.
            It is expected that each project had a group of subjects that are present in the dataset
            it is expected that BIDS names are the ones used in the groups_glm file for the ids
            the f_ids.json has the BIDS names of the subjects, and for each BIDS name
            has the corresponding names of the source file/freesurfer/nilearn/dipy processed ziped files
            see nimb/example/f_ids.json
        '''
        print('extracting list of ids')
        from distribution.distribution_definitions import get_keys_processed
        self.ids_bids_proc_all = self.read_json(self.f_ids_processed)
        return {i: self.ids_bids_proc_all[i][get_keys_processed(method)] for i in self.ids_bids_proc_all}
        # return {i: 'path' for i in self.ids_bids_proc_all if self.ids_bids_proc_all[i]['source'] in ids_src_glm_file} #old version


    def add_to_miss(self, bids_id, file):
        '''add to the list of missing subjects
        '''
        if bids_id not in self.miss:
            self.miss[bids_id] = list()
        self.miss[bids_id].append(file)

    def read_json(self, f):
        '''read a json file
        '''
        with open(f, 'r') as jf:
            return json.load(jf)


class PrepareForGLM():

    #https://surfer.nmr.mgh.harvard.edu/fswiki/FsgdExamples
    def __init__(self, SUBJECTS_DIR, GLM_dir, GLM_file_group, proj_vars, vars_fs):
        self.PATH_GLM_dir = GLM_dir
        self.group_col = proj_vars["group_col"]
        self.id_col = proj_vars["id_col"]
        self.PATHfsgd = os.path.join(self.PATH_GLM_dir,'fsgd')
        self.PATHmtx = os.path.join(self.PATH_GLM_dir,'contrasts')

        if not os.path.isdir(self.PATH_GLM_dir): os.makedirs(self.PATH_GLM_dir)
        if Path(GLM_file_group).name not in os.listdir(self.PATH_GLM_dir):
            shutil.copy(GLM_file_group, os.path.join(self.PATH_GLM_dir, Path(GLM_file_group).name))
        if not os.path.isdir(self.PATHfsgd): os.makedirs(self.PATHfsgd)
        if not os.path.isdir(self.PATHmtx): os.makedirs(self.PATHmtx)
        cols_2use = proj_vars["variables_for_glm"]+[self.id_col, self.group_col]
        df_groups_clin = Table().get_df_with_columns(GLM_file_group, cols_2use)

        self.ids = self.get_ids_ready4glm(SUBJECTS_DIR, df_groups_clin[self.id_col].tolist(), vars_fs)
        d_init = df_groups_clin.to_dict()
        self.d_subjid = {}
        self.ls_vars_stats = [key for key in d_init if key != self.id_col]
        for rownr in d_init[self.id_col]:
            _id = d_init[self.id_col][rownr]
            if _id in self.ids:
                self.d_subjid[_id] = {}
                for var in self.ls_vars_stats:
                    self.d_subjid[_id][var] = d_init[var][rownr]
        self.ls_vars_stats.remove(self.group_col)

        self.contrasts = {
            'g1v1':{'slope.mtx'         :['0 1',        't-test with the slope>0 being positive; is the slope equal to 0? does the correlation between thickness and variable differ from zero ?',],},
            'g2v0':{'group.diff.mtx'    :['1 -1',       't-test with Group1>Group2 being positive; is there a difference between the group intercepts? Is there a difference between groups?',],},
            'g2v1':{'group.diff.mtx'    :['1 -1 0 0',   't-test with Group1>Group2 being positive; is there a difference between the group intercepts? Is there a difference between groups regressing out the effect of age?',],
                    'group-x-var.mtx'   :['0 0 1 -1',   't-test with Group1>Group2 being positive; is there a difference between the group age slopes? Note: this is an interaction between group and age. Note: not possible to test with DOSS',],
                    'g1g2.var.mtx'      :['0 0 0.5 0.5','t-test with (Group1+Group2)/2 > 0 being positive (red/yellow). If mean < 0, then it will be displayed in blue/cyan; does mean of group age slope differ from 0? Is there an average affect of age regressing out the effect of group?',],}
                            }
        dods_doss = {
            'g1v1':[       'dods',],
            'g2v0':['doss','dods',],
            'g2v1':[       'dods',],}
        contrasts_not_used = {
            'g1v0':{'intercept.mtx'     :['1',          't-test with intercept>0 being positive; is the intercept/mean equal to 0?',],},
            'g1v1':{'intercept.mtx'     :['1 0',        't-test with intercept>0 being positive; is the intercept equal to 0? Does the average thickness differ from zero ?',],},
            'g1v2':{'main.mtx'          :['1 0 0',      't-test with offset>0 being positive; the intercept/offset is different than 0 after regressing out the effects of var1 and var2',],
                    'var1.mtx'          :['0 1 0',      't-test with var1 slope>0 being positive',],
                    'var2.mtx'          :['0 0 1',      't-test with var2 slope>0 being positive',],},
            'g2v0':{'group1.mtx'        :['1 0',        't-test with Group1>0 being positive; is there a main effect of Group1? Does the mean of Group1 equal 0?',],
                    'group2.mtx'        :['0 1',        't-test with Group2>0 being positive; is there a main effect of Group2? Does the mean of Group2 equal 0?',],
                    'g1g2.intercept.mtx':['0.5 0.5',    't-test with (Group1+Group2)/2 > 0 being positive (red/yellow). If the mean is < 0, then it will be displayed in blue/cyan; does mean of the group means differ from 0?',],},
            'g2v1':{'g1g2.intercept.mtx':['0.5 0.5 0 0','t-test with (Group1+Group2)/2 > 0 being positive (red/yellow). If the mean is < 0, then it will be displayed in blue/cyan; does mean of group intercepts differ from 0? Is there an average main effect regressing out age?',]}
                                }
        dods_doss_not_used = {
            'g1v0':['dods',],
            'g1v2':['dods',],}
        self.files_glm = {}
        for fsgd_type in self.contrasts:
            self.files_glm[fsgd_type]={
                                        'fsgd' : [],
                                        'mtx' : [],
                                        'mtx_explanation' : [],
                                        'gd2mtx' : dods_doss[fsgd_type]}

        # print('creating list of subjects')
        self.make_subjects_per_group(df_groups_clin)
        # print('creating fsgd for g1g2v0')
        self.make_fsgd_g1g2v0()
        # print('creating fsgd for g1v1')
        self.make_fsgd_g1v1()
        # print('creating fsgd for g1v2')
        # self.make_fsgd_g1v2()
        # print('creating fsgd for g2v1')
        self.make_fsgd_g2v1()
        # print('creating unix version of fsgd files, to convert Windows tabulations to unix')
        self.fsgd_win_to_unix()
        # print('creating contrasts')
        self.make_contrasts()
        # print('creating py file with all data')
        self.make_files_for_glm()
        # print('creating qdec fsgd files')
        self.make_qdec_fsgd_g2()

    def get_ids_ready4glm(self, SUBJECTS_DIR, ids, vars_fs):
        miss = {}
        for _id in ids:
            files_ok = ChkFSQcache(SUBJECTS_DIR, _id, vars_fs)
            if not files_ok:
                miss.update(files_ok)
        if miss.keys():
            print('some subjects or files are missing: {}'.format(miss))
        return [i for i in ids if i not in miss.keys()]

    def make_subjects_per_group(self, df):
        self.ls_groups = pd.unique(df[self.group_col]).tolist()
        subjects_per_group = dict()
        for group in self.ls_groups:
            subjects_per_group[group] = []
            for row in df.index.tolist():
                if df.at[row, self.group_col] == group and df.at[row, self.id_col] in self.ids:
                    subjects_per_group[group].append(df.at[row, self.id_col])
            print('        group: {}, has {} subjects'.format(group, len(subjects_per_group[group])))

        file = 'subjects_per_group.json'
        with open(os.path.join(self.PATH_GLM_dir, file), 'w') as f:
            json.dump(subjects_per_group, f, indent=4)


    def make_fsgd_g1g2v0(self):
        file = 'g2v0_{}_{}.fsgd'.format(self.ls_groups[0], self.ls_groups[1])
        open(os.path.join(self.PATHfsgd,file), 'w').close()
        with open(os.path.join(self.PATHfsgd,file), 'a') as f:
            f.write('GroupDescriptorFile 1\nClass {} plus blue\nClass {} circle green\n'.format(
                                                            self.ls_groups[0], self.ls_groups[1]))
            # f.write('GroupDescriptorFile 1\nClass '+self.ls_groups[0]+' plus blue\nClass '+self.ls_groups[1]+' circle green\n')
            for subjid in self.d_subjid:
                f.write(f'Input {subjid} {self.d_subjid[subjid][self.group_col]}\n')
        self.files_glm['g2v0']['fsgd'].append(file)
        # for group in self.ls_groups:
            # file = 'g1v0'+'_'+group+'.fsgd'
            # open(os.path.join(self.PATHfsgd,file), 'w').close()
            # with open(os.path.join(self.PATHfsgd,file), 'a') as f:
                # f.write('GroupDescriptorFile 1\nClass Main\n')
                # for subjid in self.d_subjid:
                    # if self.d_subjid[subjid][self.group_col] == group:
                        # f.write('Input '+subjid+' Main\n')
            # self.files_glm['g1v0']['fsgd'].append(file)

    def check_var_zero(self, var, group):
        ls = []
        for subjid in self.d_subjid:
            if self.d_subjid[subjid][self.group_col] == group:
                ls.append(self.d_subjid[subjid][var])
        return all(v == 0 for v in ls)

    def make_fsgd_g1v1(self):
        for group in self.ls_groups:
            for variable in self.ls_vars_stats:
                if not self.check_var_zero(variable, group):
                    file = 'g1v1_{}_{}.fsgd'.format(group, variable)
                    open(os.path.join(self.PATHfsgd,file), 'w').close()
                    with open(os.path.join(self.PATHfsgd,file), 'a') as f:
                        f.write('GroupDescriptorFile 1\nClass Main\nVariables {}\n'.format(variable))
                        for subjid in self.d_subjid:
                            if self.d_subjid[subjid][self.group_col] == group:
                                f.write('Input {} Main {}\n'.format(subjid, str(self.d_subjid[subjid][variable])))
                    self.files_glm['g1v1']['fsgd'].append(file)


    def make_fsgd_g1v2(self):
        for group in self.ls_groups:
            for variable in self.ls_vars_stats[:-1]:
                if not self.check_var_zero(variable, group):
                    for variable2 in self.ls_vars_stats[self.ls_vars_stats.index(variable)+1:]:
                        if not self.check_var_zero(variable2, group):
                            file = 'g1v2_{}_{}_{}.fsgd'.format(group, str(variable), str(variable2))
                            open(os.path.join(self.PATHfsgd,file), 'w').close()
                            with open(os.path.join(self.PATHfsgd,file), 'a') as f:
                                f.write('GroupDescriptorFile 1\nClass Main\nVariables {} {}\n'.format(
                                                                    str(variable), str(variable2)))
                                for subjid in self.d_subjid:
                                    if self.d_subjid[subjid][self.group_col] == group:
                                        f.write('Input {} Main {} {}\n'.format(
                                            subjid, str(self.d_subjid[subjid][variable]), str(self.d_subjid[subjid][variable2])))
                            self.files_glm['g1v2']['fsgd'].append(file)

    def make_fsgd_g2v1(self):
        for variable in self.ls_vars_stats:
            if not self.check_var_zero(variable, self.ls_groups[0]) and not self.check_var_zero(variable, self.ls_groups[1]):
                file = 'g2v1_{}_{}_{}.fsgd'.format(self.ls_groups[0], self.ls_groups[1], variable)
                open(os.path.join(self.PATHfsgd,file), 'w').close()
                with open(os.path.join(self.PATHfsgd,file), 'a') as f:
                    f.write('GroupDescriptorFile 1\nClass {} plus blue\nClass {} circle green\nVariables '.format(
                                                            self.ls_groups[0], self.ls_groups[1]))
                    f.write(variable+'\n')
                    for subjid in self.d_subjid:
                        f.write('Input {} {} {}\n'.format(
                            subjid, self.d_subjid[subjid][self.group_col], str(self.d_subjid[subjid][variable])))
                self.files_glm['g2v1']['fsgd'].append(file)

    def fsgd_win_to_unix(self):
        for contrast_type in self.files_glm:
            for fsgd_file in self.files_glm[contrast_type]['fsgd']:
                fsgd_f_unix = os.path.join(self.PATH_GLM_dir,'fsgd', '{}_unix.fsgd'.format(fsgd_file.replace('.fsgd','')))
                if not os.path.isfile(fsgd_f_unix):
                    os.system('cat {} | sed \'s/\\r/\\n/g\' > {}'.format(
                        os.path.join(self.PATH_GLM_dir,'fsgd',fsgd_file), fsgd_f_unix))

    def make_qdec_fsgd_g2(self):
        file = 'qdec_g2.fsgd'
        open(os.path.join(self.PATH_GLM_dir,file), 'w').close()
        with open(os.path.join(self.PATH_GLM_dir,file), 'a') as f:
            f.write('fsid group ')
            for variable in self.ls_vars_stats:
                if not self.check_var_zero(variable, self.ls_groups[0]) and not self.check_var_zero(variable, self.ls_groups[1]):
                    f.write(variable+' ')
            f.write('\n')
            for _id in self.d_subjid:
                f.write('{} {} '.format(_id, self.d_subjid[_id][self.group_col]))
                for variable in self.ls_vars_stats:
                    f.write(str(self.d_subjid[_id][variable])+' ')
                f.write('\n')


    def make_contrasts(self):
        for fsgd_type in self.contrasts:
            for contrast_mtx in self.contrasts[fsgd_type]:
                file = '{}_{}'.format(fsgd_type, contrast_mtx)
                open(os.path.join(self.PATHmtx,file), 'w').close()
                with open(os.path.join(self.PATHmtx, file), 'a') as f:
                    f.write(self.contrasts[fsgd_type][contrast_mtx][0])
                self.files_glm[fsgd_type]['mtx'].append(file)
                self.files_glm[fsgd_type]['mtx_explanation'].append(self.contrasts[fsgd_type][contrast_mtx][1])


    def make_files_for_glm(self):
        file = 'files_for_glm.json'
        with open(os.path.join(self.PATH_GLM_dir, file), 'w') as f:
            json.dump(self.files_glm, f, indent=4)

