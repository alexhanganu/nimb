'''
last update: 20201218
check that all subjects are present in the FS_SUBJECTS_DIR folder
in order to perform the FreeSurfer glm
'''

from os import listdir, path, system, makedirs
import sys
import json
import shutil
import linecache

try:
    import pandas as pd
    import xlrd
    import openpyxl
    from pathlib import Path
except ImportError as e:
    print('could not import modules: pandas or xlrd or openpyxl')
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
        if path.exists(path.join(self.path2chk, self._id, 'surf')) and path.exists(path.join(self.path2chk, self._id, 'label')):
            for hemi in ['lh','rh']:
                for meas in self.GLM_meas:
                    for thresh in self.GLM_thresh:
                        file = '{}.{}.fwhm{}.fsaverage.mgh'.format(hemi, meas, str(thresh))
                        if not path.exists(path.join(self.path2chk, self._id, 'surf', file)):
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

    def chk_if_subjects_ready(self):
        self.miss = {}
        self.ids = self.get_ids_processed()
        if self.ids:
            for _id in self.ids:
                self.define_subjects_path(_id)
            if self.miss.keys():
                ids_ok = {i:self.ids[i] for i in self.ids if i not in self.miss.keys()}
                print('{} subjects are missing and {} are present in the processing folder'.format(len(self.miss.keys()), len(ids_ok.keys())))
                return False, list(self.miss.keys())
            elif self.defined_path:
                print(self.defined_path)
                self.SUBJECTS_DIR = max(self.defined_path, key = self.defined_path.count)
                print(self.SUBJECTS_DIR)
                self.create_glm_df([i for i in self.ids if self.SUBJECTS_DIR in self.ids[i]])
                PrepareForGLM(self.SUBJECTS_DIR,
                                self.FS_GLM_dir,
                                self.f_GLM_group, 
                                self.proj_vars,
                                self.vars_fs)
                return self.SUBJECTS_DIR, list()
        else:
            print('no ids found')
            return False, list()

    def chk_path(self, path2chk, _id):
        files_ok = ChkFSQcache(path2chk, _id, self.vars_fs)
        if not files_ok:
            self.miss.update(files_ok)
            return False
        else:
            return True

        # if path.exists(path.join(path2chk, _id, 'surf')) and path.exists(path.join(path2chk, _id, 'label')):
            # for hemi in ['lh','rh']:
                # for meas in self.vars_fs["GLM_measurements"]:
                    # for thresh in self.vars_fs["GLM_thresholds"]:
                        # file = '{}.{}.fwhm{}.fsaverage.mgh'.format(hemi, meas, str(thresh))
                        # if not path.exists(path.join(path2chk, _id, 'surf', file)):
                            # print('    id {} misses file {}'.format(_id, file))
                            # self.add_to_miss(_id, file)
        # else:
            # self.add_to_miss(_id, 'surf label missing')
        # if _id not in self.miss:
            # return True
        # else:
            # return False

    def define_subjects_path(self, _id):
        '''it is expected that the BIDS IDs after processing are located in one of the two folders
            script defines the the folder for analysis
            checks if subjects are present
        Args:
            _id: ID of the subject to chk
        Return:
            populates list of missing subjects
            populates dict with ids
            Folder with Subjects for GLM analysis
        '''
        self.defined_path = list()
        path_id_processed = ''
        for path_subjs in [self.FS_SUBJECTS_DIR, self.NIMB_PROCESSED_FS]:
            path2chk = path.join(path_subjs, _id)
            if path.exists(path2chk):
                path_id_processed = path_subjs
                break
        if path_id_processed:
            if self.chk_path(path_id_processed, _id):
                self.defined_path.append(path_id_processed)
                self.ids[_id] = path_id_processed
        else:
            print('id is missing {}'.format(_id))
            self.add_to_miss(_id, 'id_missing')

    def create_glm_df(self, ls_ids):
        ls_ix_2rm = list()
        self.df['fs_id'] = ''
        for ix in self.df.index:
            src_id = self.df.at[ix, self.proj_vars['id_col']]
            bids_id = [i for i in self.ids_all if self.ids_all[i]['source'] == src_id][0]
            self.df.at[ix, 'fs_id'] = bids_id
            if bids_id not in ls_ids:
                ls_ix_2rm.append(ix)
        self.df_new = self.df.drop(ls_ix_2rm)
        self.df_new.drop(columns=[self.proj_vars['id_col']], inplace=True)
        self.df_new.rename(columns={'fs_id': self.proj_vars['id_col']}, inplace=True)
        self.df_new.to_excel(self.f_GLM_group)

    def get_ids_processed(self):
        '''retrieves the bids names of the IDs provided in the GLM file.
            It is expected that each project had a group of subjects that are present in the dataset
            the f_ids.json has the BIDS names of the subjects, the source names and the freesurfer/nilearn/dipy names
            see nimb/example/f_ids.json
        '''
        print('extracting list of ids')
        self.ids_all = self.read_json(self.f_ids_processed)
        self.df = self.get_df()
        ids_glm_file = self.df[self.proj_vars['id_col']].tolist()
        return {i: 'path' for i in self.ids_all if self.ids_all[i]['source'] in ids_glm_file}


    def add_to_miss(self, _id, file):
        '''add to the list of missing subjects
        '''
        if _id not in self.miss:
            self.miss[_id] = list()
        self.miss[_id].append(file)

    def read_json(self, f):
        '''read a json file
        '''
        with open(f, 'r') as jf:
            return json.load(jf)

    def get_df(self):
        '''reads a csv or an xlsx file
        '''
        if '.csv' in self.f_GLM_group:
            return pd.read_csv(self.f_GLM_group)
        elif '.xlsx' in self.f_GLM_group or '.xls' in self.f_GLM_group:
            return pd.read_excel(self.f_GLM_group)




class PrepareForGLM():

    #https://surfer.nmr.mgh.harvard.edu/fswiki/FsgdExamples
    def __init__(self, SUBJECTS_DIR, GLM_dir, GLM_file_group, proj_vars, vars_fs):
        self.PATH_GLM_dir = GLM_dir
        self.group_col = proj_vars["group_col"]
        self.id_col = proj_vars["id_col"]
        self.PATHfsgd = path.join(self.PATH_GLM_dir,'fsgd')
        self.PATHmtx = path.join(self.PATH_GLM_dir,'contrasts')

        if not path.isdir(self.PATH_GLM_dir): makedirs(self.PATH_GLM_dir)
        if Path(GLM_file_group).name not in listdir(self.PATH_GLM_dir):
            shutil.copy(GLM_file_group, path.join(self.PATH_GLM_dir, Path(GLM_file_group).name))
        if not path.isdir(self.PATHfsgd): makedirs(self.PATHfsgd)
        if not path.isdir(self.PATHmtx): makedirs(self.PATHmtx)

        df_groups_clin = self.get_df_for_variables(GLM_file_group, proj_vars["variables_for_glm"])
        self.ids = self.get_ids_ready4glm(SUBJECTS_DIR, df_groups_clin[self.id_col].tolist(), vars_fs)
        d_init = df_groups_clin.to_dict()
        self.d_subjid = {}
        self.ls_vars_stats = [key for key in d_init if key != self.id_col]
        for rownr in d_init[self.id_col]:
            id = d_init[self.id_col][rownr]
            if id in self.ids:
                self.d_subjid[id] = {}
                for var in self.ls_vars_stats:
                    self.d_subjid[id][var] = d_init[var][rownr]
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

        print('creating list of subjects')
        self.make_subjects_per_group(df_groups_clin)
        print('creating fsgd for g1g2v0')
        self.make_fsgd_g1g2v0()
        print('creating fsgd for g1v1')
        self.make_fsgd_g1v1()
        print('creating fsgd for g1v2')
        # self.make_fsgd_g1v2()
        # print('creating fsgd for g2v1')
        self.make_fsgd_g2v1()
        print('creating unix version of fsgd files, to convert Windows tabulations to unix')
        self.fsgd_win_to_unix()
        print('creating contrasts')
        self.make_contrasts()
        print('creating py file with all data')
        self.make_files_for_glm()
        print('creating qdec fsgd files')
        self.make_qdec_fsgd_g2()

    def get_df_for_variables(self, GLM_file_group, variables):
        if '.csv' in GLM_file_group:
            df = pd.read_csv(GLM_file_group)
        elif '.xlsx' in GLM_file_group or '.xls' in file_group:
            df = pd.read_excel(GLM_file_group)
        cols2drop = list()
        for col in df.columns.tolist():
            if col not in variables+[self.id_col, self.group_col]:
                cols2drop.append(col)
        if cols2drop:
            df.drop(columns=cols2drop, inplace=True)
        return df

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
        print(subjects_per_group)

        file = 'subjects_per_group.json'
        with open(path.join(self.PATH_GLM_dir, file), 'w') as f:
            json.dump(subjects_per_group, f, indent=4)


    def make_fsgd_g1g2v0(self):
        file = 'g2v0_{}_{}.fsgd'.format(self.ls_groups[0], self.ls_groups[1])
        open(path.join(self.PATHfsgd,file), 'w').close()
        with open(path.join(self.PATHfsgd,file), 'a') as f:
            f.write('GroupDescriptorFile 1\nClass '+self.ls_groups[0]+' plus blue\nClass '+self.ls_groups[1]+' circle green\n')
            for subjid in self.d_subjid:
                f.write('Input '+subjid+' '+self.d_subjid[subjid][self.group_col]+'\n')
        self.files_glm['g2v0']['fsgd'].append(file)
        # for group in self.ls_groups:
            # file = 'g1v0'+'_'+group+'.fsgd'
            # open(path.join(self.PATHfsgd,file), 'w').close()
            # with open(path.join(self.PATHfsgd,file), 'a') as f:
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
                    file = 'g1v1'+'_'+group+'_'+variable+'.fsgd'
                    open(path.join(self.PATHfsgd,file), 'w').close()
                    with open(path.join(self.PATHfsgd,file), 'a') as f:
                        f.write('GroupDescriptorFile 1\nClass Main\nVariables '+variable+'\n')
                        for subjid in self.d_subjid:
                            if self.d_subjid[subjid][self.group_col] == group:
                                f.write('Input '+subjid+' Main '+str(self.d_subjid[subjid][variable])+'\n')
                    self.files_glm['g1v1']['fsgd'].append(file)


    def make_fsgd_g1v2(self):
        for group in self.ls_groups:
            for variable in self.ls_vars_stats[:-1]:
                if not self.check_var_zero(variable, group):
                    for variable2 in self.ls_vars_stats[self.ls_vars_stats.index(variable)+1:]:
                        if not self.check_var_zero(variable2, group):
                            file = 'g1v2'+'_'+group+'_'+str(variable)+'_'+str(variable2)+'.fsgd'
                            open(path.join(self.PATHfsgd,file), 'w').close()
                            with open(path.join(self.PATHfsgd,file), 'a') as f:
                                f.write('GroupDescriptorFile 1\nClass Main\nVariables '+str(variable)+' '+str(variable2)+'\n')
                                for subjid in self.d_subjid:
                                    if self.d_subjid[subjid][self.group_col] == group:
                                        f.write('Input '+subjid+' Main '+str(self.d_subjid[subjid][variable])+' '+str(self.d_subjid[subjid][variable2])+'\n')
                            self.files_glm['g1v2']['fsgd'].append(file)

    def make_fsgd_g2v1(self):
        for variable in self.ls_vars_stats:
            if not self.check_var_zero(variable, self.ls_groups[0]) and not self.check_var_zero(variable, self.ls_groups[1]):
                file = 'g2v1'+'_'+self.ls_groups[0]+'_'+self.ls_groups[1]+'_'+variable+'.fsgd'
                open(path.join(self.PATHfsgd,file), 'w').close()
                with open(path.join(self.PATHfsgd,file), 'a') as f:
                    f.write('GroupDescriptorFile 1\nClass '+self.ls_groups[0]+' plus blue\nClass '+self.ls_groups[1]+' circle green\nVariables ')
                    f.write(variable+'\n')
                    for subjid in self.d_subjid:
                        f.write('Input '+subjid+' '+self.d_subjid[subjid][self.group_col]+' '+str(self.d_subjid[subjid][variable])+'\n')
                self.files_glm['g2v1']['fsgd'].append(file)

    def fsgd_win_to_unix(self):
        for contrast_type in self.files_glm:
            for fsgd_file in self.files_glm[contrast_type]['fsgd']:
                fsgd_f_unix = path.join(self.PATH_GLM_dir,'fsgd',fsgd_file.replace('.fsgd','')+'_unix.fsgd')
                if not path.isfile(fsgd_f_unix):
                    system('cat '+path.join(self.PATH_GLM_dir,'fsgd',fsgd_file)+' | sed \'s/\\r/\\n/g\' > '+fsgd_f_unix)

    def make_qdec_fsgd_g2(self):
        file = 'qdec_g2.fsgd'
        open(path.join(self.PATH_GLM_dir,file), 'w').close()
        with open(path.join(self.PATH_GLM_dir,file), 'a') as f:
            f.write('fsid group ')
            for variable in self.ls_vars_stats:
                if not self.check_var_zero(variable, self.ls_groups[0]) and not self.check_var_zero(variable, self.ls_groups[1]):
                    f.write(variable+' ')
            f.write('\n')
            for id in self.d_subjid:
                f.write(id+' '+self.d_subjid[id][self.group_col]+' ')
                for variable in self.ls_vars_stats:
                    f.write(str(self.d_subjid[id][variable])+' ')
                f.write('\n')


    def make_contrasts(self):
        for fsgd_type in self.contrasts:
            for contrast_mtx in self.contrasts[fsgd_type]:
                file = '{}_{}'.format(fsgd_type, contrast_mtx)
                open(path.join(self.PATHmtx,file), 'w').close()
                with open(path.join(self.PATHmtx, file), 'a') as f:
                    f.write(self.contrasts[fsgd_type][contrast_mtx][0])
                self.files_glm[fsgd_type]['mtx'].append(file)
                self.files_glm[fsgd_type]['mtx_explanation'].append(self.contrasts[fsgd_type][contrast_mtx][1])


    def make_files_for_glm(self):
        file = 'files_for_glm.json'
        with open(path.join(self.PATH_GLM_dir, file), 'w') as f:
            json.dump(self.files_glm, f, indent=4)

