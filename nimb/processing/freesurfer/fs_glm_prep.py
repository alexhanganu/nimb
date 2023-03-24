'''
last update: 20221028
check that all subjects are present in the SUBJECTS_DIR folder
in order to perform the FreeSurfer GLM
create required files to perform FreeSurfer GLM
'''



"""
Must check that variables are continuous numbers

GLM suggestions from FreeSurfer community:
* don't use gender as a continuous covariate (Douglas N. Greve)
* Make sure to normalize your covariates (Douglas N. Greve)
    FSGD:
        GroupDescriptorFile 1
        Title Between-group
        Class int_male
        Class int_female
        Class con_male
        Class con_female
        Variables age mmse
        Input 001.MR int_male      30     25
        Input 002.MR int_female    40     22
        Input 003.MR con_male      60     29
        Input 004.MR con_female    60     21
    contrast matrix
        +0.5 +0.5 -0.5 -0.5 +0 +0 +0 +0 +0 +0 +0 +0
    With the above contrast matrix, our interpretation would be:
        Intervention > control = positive result
        Intervention < control = negative result

"""
import os
import sys
import json
import shutil
import linecache
import itertools

from setup.interminal_setup import get_yes_no
from stats.db_processing import Table
from distribution.utilities import save_json
from distribution.distribution_definitions import DEFAULT

try:
    from processing.freesurfer import fs_definitions
except ModuleNotFoundError:
    import fs_definitions
    print('    EXCEPTION: module fs_definitions was read directly')

try:
    import pandas as pd
    import xlrd
    import openpyxl
    from pathlib import Path
except ImportError as e:
    print('could not import modules: pandas or xlrd or openpyxl.\
            please try to install using pip,\
            or use miniconda run with the command located \
            in credentials_path.py/local.json -> miniconda_python_run')
    sys.exit(e)


class CheckIfReady4GLM():

    def __init__(self, nimb_vars, fs_vars, proj_vars, f_ids_processed, f_GLM_group, FS_GLM_dir):
        self.proj_vars         = proj_vars
        self.vars_fs           = fs_vars
        self.FS_SUBJECTS_DIR   = fs_vars['SUBJECTS_DIR']
        self.NIMB_PROCESSED_FS = fs_vars['NIMB_PROCESSED']
        self.f_ids_processed   = f_ids_processed
        self.f_GLM_group       = f_GLM_group
        self.FS_GLM_dir        = FS_GLM_dir
        self.archive_type      = '.zip'
        self.tab               = Table()
        self.miss              = dict()
        self.ids_4fs_glm       = dict()
        self.df                = self.tab.get_df(self.f_GLM_group)
        self.bids_ids          = self.df[self.proj_vars['id_col']].tolist()
        self.ids_exclude_glm   = os.path.join(self.FS_GLM_dir, 'excluded_from_glm.json')


    def chk_if_subjects_ready(self):

        fs_proc_ids = self.get_ids_processed()
        miss_bids_ids = [i for i in self.bids_ids if i not in fs_proc_ids.keys()]
        if miss_bids_ids:
            print(f'    {len(miss_bids_ids)} IDs are missing from file: {self.f_ids_processed}')
            print(f'        first 5 IDs are: {self.f_ids_processed[:5]}')
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
                    self.chk_glm_files(fs_proc_id)
                else:
                    print(f'id {bids_id} or freesurfer id {fs_proc_id} \
                        are missing from the {self.FS_SUBJECTS_DIR} folder')
                    self.add_to_miss(bids_id, 'id_missing')
            if self.miss.keys():
                print("    missing files and ids: ", self.miss)
                save_json(self.miss, self.ids_exclude_glm, print_space = 8)
                subjs_missing = len(self.miss.keys())
                subjs_present = len(self.ids_4fs_glm.keys())
                print(f'    Number of participants ready for FreeSurfer GLM:')
                print(f'        in the folder: {self.FS_SUBJECTS_DIR}')
                print(f'        {subjs_present} present')
                print(f'        {subjs_missing} missing')
                not_ready = [i for i in self.miss if "id_missing" not in self.miss[i]]
                maybe_archived = [i for i in self.miss if i not in not_ready]
                if maybe_archived:
                    print("   MAYBE archived: ", maybe_archived)
                    q = "    EXCEPTION! Some IDs are missing, but they could be archived.\n\
                    Do you want to do glm analysis with current subjects (y) or try to check the archive (n) ? (y/n)\n\
                        (note: if you answer NO, you will be asked to unarchive the \n\
                        processed folders of IDs if they are present in FREESURFER_PROCESSED)"
                    if get_yes_no(q) == 1:
                        self.create_fs_glm_df()
                        return True, list()
                    else:
                        return False, maybe_archived
                if not_ready:
                    print("    MISSING FILES: these participant CANNOT be included in the GLM analysis: ", not_ready)
                    q = "    EXCEPTION! Some IDs have missing files and they MUST be excluded from analysis.\n\
                    Do you want to continue without excluded IDs ? (y/n)"
                    if get_yes_no(q) == 1:
                        self.create_fs_glm_df()
                        return True, list()
                    else:
                        return False, not_ready
            else:
                self.create_fs_glm_df()
                return True, list()
        else:
            print('    no ids found')
            return False, list()

    def chk_glm_files(self, bids_id):
        '''it is expected that the BIDS IDs are located in FREESURFER -> SUBJECTS_DIR
            script checks if subjects are present
        Args:
            bids_id: ID of the subject to chk
        Return:
            populates list of missing subjects
            populates dict with ids
        '''
        files_not_ok = fs_definitions.ChkFSQcache(self.FS_SUBJECTS_DIR,
                                            bids_id,
                                            self.vars_fs).miss
        if files_not_ok:
            for file in files_not_ok[bids_id]:
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
        len_miss = len(ls_ix_2rm)
        if len_miss == 0:
            print(f'        ALL subjects are present')
        else:
            print(f'        {len_miss} subjects are missing')
            print(f'            they will be removed from futher analysis')
        self.df = self.df.drop(ls_ix_2rm)


    def get_ids_processed(self):
        '''retrieves the bids names of the IDs provided in the GLM file.
            It is expected that each project had a group of subjects that are present in the dataset
            it is expected that BIDS names are the ones used in the groups_glm file for the ids
            the f_ids.json has the BIDS names of the subjects, and for each BIDS name
            has the corresponding names of the source file/freesurfer/nilearn/dipy processed ziped files
            see nimb/example/f_ids.json
        '''
        print('    extracting list of ids that were processed with FreeSurfer')
        print(f'        in the file{self.f_ids_processed}')
        self.ids_bids_proc_all = self.read_json(self.f_ids_processed)
        return {i: self.ids_bids_proc_all[i][DEFAULT.apps_keys["freesurfer"]] for i in self.ids_bids_proc_all}
        # return {i: 'path' for i in self.ids_bids_proc_all if self.ids_bids_proc_all[i]['source'] in ids_src_glm_file} #old version


    def add_to_miss(self, bids_id, file):
        '''add to the list of missing subjects
        '''
        if bids_id not in self.miss:
            self.miss[bids_id] = list()
        self.miss[bids_id].append(file)
        if bids_id in self.ids_4fs_glm:
            self.ids_4fs_glm.pop(bids_id, None)


    def read_json(self, f):
        '''read a json file
        '''
        with open(f, 'r') as jf:
            return json.load(jf)


class PrepareForGLM():

    #https://surfer.nmr.mgh.harvard.edu/fswiki/FsgdExamples
    def __init__(self,
                SUBJECTS_DIR,
                GLM_dir,
                GLM_file_group,
                proj_vars,
                vars_fs):
        self.SUBJECTS_DIR = SUBJECTS_DIR
        self.group_col    = proj_vars["group_col"]
        self.id_col       = proj_vars["id_col"]

        self.make_folders(GLM_dir,
                        GLM_file_group)
        self.get_groups_and_variables(proj_vars,
                                    GLM_file_group,
                                    vars_fs)
        self.fsgd_run_populate()
        self.make_contrasts_save_file()

        # print('creating unix version of fsgd files, to convert Windows tabulations to unix')
        self.fsgd_win_to_unix(GLM_dir)
        # self.make_qdec_fsgd_g2() #QDEC is deprecated in FreeSurfer version >7.3


    def make_folders(self,
                    GLM_dir,
                    GLM_file_group):
        """creating corresponding folders
        """
        params            = fs_definitions.FSGLMParams(GLM_dir)
        self.PATHfsgd     = os.path.join(GLM_dir,'fsgd')
        self.PATHmtx      = os.path.join(GLM_dir,'contrasts')
        # self.PATHqdec     = os.path.join(GLM_dir,'qdec')
        self.file_for_glm = os.path.join(GLM_dir, 'files_for_glm.json')
        self.ids_groups   = os.path.join(GLM_dir, 'ids_per_group.json')

        for _dir in [GLM_dir, self.PATHfsgd, self.PATHmtx]:
            if not os.path.exists(_dir):
                os.makedirs(_dir)

        # copying GLM_file_group to folder for GLM
        glm_file_name = Path(GLM_file_group).name
        if glm_file_name not in os.listdir(GLM_dir):
            shutil.copy(GLM_file_group,
                        os.path.join(GLM_dir, glm_file_name))


    def get_groups_and_variables(self,
                                proj_vars,
                                GLM_file_group,
                                vars_fs):
        """creating working variables and dictionaries
        """
        self.ls_vars_stats = proj_vars["variables_for_glm"]
        self.ls_vars_correct = proj_vars["vars_for_correction"]
        self.ls_all_vars = self.ls_vars_stats + self.ls_vars_correct+[self.id_col, self.group_col]
        df_groups_clin = Table().get_df_with_columns(GLM_file_group, self.ls_all_vars)
        d_init = df_groups_clin.to_dict()

        if not self.ls_vars_stats:
            self.ls_vars_stats = [key for key in d_init if key != self.id_col]
        self.ls_all_vars = self.ls_vars_stats + self.ls_vars_correct+[self.id_col, self.group_col]

        self.ls_groups = pd.unique(df_groups_clin[self.group_col]).tolist()
        self.ids = self.get_ids_ready4glm(df_groups_clin[self.id_col].tolist(),
                                            vars_fs)

        self.d_subjid = {}
        for rownr in d_init[self.id_col]:
            _id = d_init[self.id_col][rownr]
            if _id in self.ids:
                self.d_subjid[_id] = {}
                for var in self.ls_all_vars:
                    self.d_subjid[_id][var] = d_init[var][rownr]
        if self.group_col in self.ls_vars_stats:
            self.ls_vars_stats.remove(self.group_col)
        self.make_subjects_per_group(df_groups_clin)


    def get_ids_ready4glm(self,
                            ids,
                            vars_fs):
        """extract ids that are ready to be included in the GLM analysis
            specifically, they are being checked that all Qcache files are present
        """
        # removing NaNs from ids
        ids = [i for i in ids if not(pd.isnull(i))] 

        miss = {}
        for _id in ids:
            files_ok = fs_definitions.ChkFSQcache(self.SUBJECTS_DIR,
                                                    _id,
                                                    vars_fs)
            if not files_ok:
                miss.update(files_ok)
        if miss.keys():
            print('        some subjects or files are missing: {}'.format(miss))
        return [i for i in ids if i not in miss.keys()]


    def make_subjects_per_group(self, df):
        """creates a dictionary with all subjects per group
            saved to a json file
            for log purposes
        Args:
            df = pandas.DataFrame with ids
        """
        subjects_per_group = dict()
        for group in self.ls_groups:
            subjects_per_group[group] = []
            for row in df.index.tolist():
                if df.at[row, self.group_col] == group and df.at[row, self.id_col] in self.ids:
                    subjects_per_group[group].append(df.at[row, self.id_col])
            print(f'        group: {group}')
            print(f'            has {len(subjects_per_group[group])} subjects')
        # save file
        with open(self.ids_groups, 'w') as f:
            json.dump(subjects_per_group, f, indent=4)


    def fsgd_run_populate(self):
        """creating fsgd files
        """
        self.contrasts = fs_definitions.GLMcontrasts['contrasts']
        self.files_glm = {}
        for contrast in self.contrasts:
            dods_doss = fs_definitions.GLMcontrasts['dods_doss'][contrast]
            self.files_glm[contrast]={'fsgd' : [],
                                      'mtx'  : [],
                                      'mtx_explanation' : [],
                                      'gd2mtx' : dods_doss}
            if self.ls_vars_correct:
                self.files_glm[f"{contrast}_cor"]={'fsgd' : [],
                                                  'mtx'  : [],
                                                  'mtx_explanation' : [],
                                                  'gd2mtx' : dods_doss}
            groups_2include = int(contrast[1])
            vars_2include   = int(contrast[-1])
            groups_combined = self.combinations_get(self.ls_groups,
                                                    lvl = groups_2include)
            vars_combined   = self.combinations_get(self.ls_vars_stats,
                                                    lvl = vars_2include)
            for groups in groups_combined:
                for contrast_name in self.contrasts[contrast]:
                    contrast_txt = self.contrasts[contrast][contrast_name][0]
                    contrast_explanation = self.contrasts[contrast][contrast_name][1]
                    file_contrast = f'{contrast}_{contrast_name}'
                    self.files_glm[contrast]['mtx'].append(file_contrast)
                    self.files_glm[contrast]['mtx_explanation'].append(contrast_explanation)
                    if self.ls_vars_correct:
                        nr_zeros = len(groups)*len(self.ls_vars_correct)
                        zeros = [i for i in "".ljust(nr_zeros, "0")]
                        contrast_txt = contrast_txt + " +" + " +".join(zeros)
                        file_contrast = f'{contrast}_cor_{contrast_name}'
                        self.files_glm[f"{contrast}_cor"]['mtx'].append(file_contrast)
                        self.files_glm[f"{contrast}_cor"]['mtx_explanation'].append(contrast_explanation)
                    open(os.path.join(self.PATHmtx, file_contrast), 'w').close()
                    with open(os.path.join(self.PATHmtx, file_contrast), 'a') as f:
                        f.write(contrast_txt)

                group_in_file_name = f'_{"_".join(groups)}'
                self.fsgd_vars_add(contrast,
                                   vars_combined,
                                   group_in_file_name,
                                   groups)

        """
        add 3 groups:
        https://surfer.nmr.mgh.harvard.edu/fswiki/Fsgdf3G0V
        https://www.mail-archive.com/freesurfer@nmr.mgh.harvard.edu/msg42014.html
        https://www.mail-archive.com/freesurfer@nmr.mgh.harvard.edu/msg42279.html

        GroupDescriptorFile 1
        Title OSGM
        Class Normal
        Class MCI
        Class AD
        Input subject1 Normal
        Input subject2 MCI
        Input subject3 AD

        The the CAG is a nuisance variable and you are interested in testing for 
        the differnces in thickness with CAG regressed out, then you should do a 
        two step procedure. First run with DODS and test for differences between 
        groups in CAG. This is the contrast you will need:
        0 0 0 1 -1 0
        0 0 0 1 0 -1


        Put this in a single file. The multiple rows mean that it will be an 
        F-test. Verify that no regions survive multiple comparisons. Then run 
        with DOSS with
        1 -1 0 0
        1 0 -1 0

        This will also be an Ftest looking for a group effect. If you want to 
        make univariate tests, you can do that too.

        If the first test above fails, you can still proceed to the 2nd. If you 
        find areas that are sig in the 2nd that do not overlap the 1st, then you 
        can report them. Significant areas in the 1st test can not be 
        interpreted easily in the 2nd test.

        doug


        On 07/26/2015 09:20 AM, Dr Sampada Sinha wrote:
        > Dear freesurfer experts,
        >
        > I am trying to  find group difference (thickness) among 3 groups 
        > (SCA1, SCA2, SCA3) taking in account one covariate (CAG levels). Will 
        > you please let me know if I need to use DODS or DOSS, though I am more 
        > interested in using DODS. I read the FSGD examples page 
        > (https://surfer.nmr.mgh.harvard.edu/fswiki/Fsgdf3G0V) and I made the 
        > fsgd file (One Factor/Three Levels), one Covariate (please see the 
        > attached fsgd file). Now, my problem is how to create the contrast 
        > file. I know with DODS Nregressors will be 6. How do I create the 
        > contrasts matrix to run the mri_glmfit command?
        >
        > I could create only three .mtx file, which are:
        > 3 classes 1 variable
        >
        > contrast 1.mtx - diff SCA1 vs SCA2 1 -1 0 0 0 0
        > contrast 2.mtx - diff SCA1 vs SCA3 1 0 -1 0 0 0
        > contrast 3.mtx - diff SCA2 vs SCA3 0 1 -1 0 0 0
        > Will you please let me know what other three contrasts matrix I should add?I 
        > did go through the freesurfer forum and found this one query particularly 
        > related to the same problem I am having 
        > (http://www.mail-archive.com/freesurfer%40nmr.mgh.harvard.edu/msg33172.html).
        > Do I go by this contrasts matrix format which Stefania has come up with?
        >
        > Forever appreciative of all your efforts and time given to me.
        >
        >
        >
        >
        > -- 
        > ​S
        > ​ ampada
        > AIIMS, New Delhi​ 
        """


    def fsgd_vars_add(self, contrast, vars_combined, group_in_file_name, groups):
        var_name = ''
        vars_zeros = False

        for variables in vars_combined:
            if variables:
                var_name = f'_{"_".join(variables)}'
                if self.check_var_zero(variables, groups):
                    print(f'        variables {variables} for groups: {groups} are all zeros')
                    print(f'            will not be added to GLM')
                    vars_zeros = True
            if not vars_zeros:
                file_name = f'{contrast}{group_in_file_name}{var_name}.fsgd'
                file = os.path.join(self.PATHfsgd, file_name)
                open(file, 'w').close()
                self.files_glm[contrast]['fsgd'].append(file)
                self.fsgd_populate(file, groups, variables)

                if self.ls_vars_correct:
                    var_cor_name = f'_{"_".join(self.ls_vars_correct)}'
                    file_name = f'{contrast}{group_in_file_name}{var_name}_corrected{var_cor_name}.fsgd'
                    file = os.path.join(self.PATHfsgd, file_name)
                    open(file, 'w').close()
                    self.files_glm[f"{contrast}_cor"]['fsgd'].append(file)
                    self.fsgd_populate(file, groups, variables, corrected = True)


    def fsgd_populate(self, file, groups, variables, corrected = False):
        all_vars = variables
        if corrected:
            vars_correcting_2add = [i for i in self.ls_vars_correct if i not in variables]
            try:
                all_vars = [i for i in variables] + vars_correcting_2add
            except TypeError:
                all_vars = [variables[0],] + vars_correcting_2add
        with open(file, 'a') as f:
            f.write('GroupDescriptorFile 1\n')
            if len(groups) == 1:
                f.write(f'Class Main\n')
                group = "Main"
            else:
                f.write(f'Class {groups[0]} plus blue\n')
                f.write(f'Class {groups[1]} circle green\n')
            if all_vars:
                    f.write(f'Variables {str(" ".join(all_vars))}\n')
            for subjid in self.d_subjid:
                vars_2write = " "
                if all_vars:
                    vars_2add = list()
                    for var in all_vars:
                        vars_2add.append(self.d_subjid[subjid][var])
                    vars_2write = " "+" ".join([str(i) for i in vars_2add])
                if len(groups) == 1:
                    if self.d_subjid[subjid][self.group_col] == groups[0]:
                        f.write(f'Input {subjid} {group}{vars_2write}\n')
                else:
                    group = self.d_subjid[subjid][self.group_col]
                    if group in groups:
                        f.write(f'Input {subjid} {group}{vars_2write}\n')
        return file


    def make_contrasts_save_file(self):
        for fsgd_type in self.contrasts:
            for contrast_mtx in self.contrasts[fsgd_type]:
                file = f'{fsgd_type}_{contrast_mtx}'
                open(os.path.join(self.PATHmtx, file), 'w').close()
                with open(os.path.join(self.PATHmtx, file), 'a') as f:
                    f.write(self.contrasts[fsgd_type][contrast_mtx][0])
                self.files_glm[fsgd_type]['mtx'].append(file)
                self.files_glm[fsgd_type]['mtx_explanation'].append(self.contrasts[fsgd_type][contrast_mtx][1])

        # saving the file
        with open(self.file_for_glm, 'w') as f:
            json.dump(self.files_glm, f, indent=4)


    def fsgd_win_to_unix(self, GLM_dir):
        """must transform files that were created in Windows OS
            to adapt to linux OS
        """
        for contrast_type in self.files_glm:
            for fsgd_file in self.files_glm[contrast_type]['fsgd']:
                fsgd_file_name = fsgd_file.replace('.fsgd','')
                fsgd_f_unix = os.path.join(self.PATHfsgd,
                                            f'{fsgd_file_name}_unix.fsgd')
                if not os.path.isfile(fsgd_f_unix):
                    os.system('cat {} | sed \'s/\\r/\\n/g\' > {}'.format(
                        os.path.join(self.PATHfsgd, fsgd_file), fsgd_f_unix))


    def combinations_get(self, ls, lvl = 0):
        """combining values from ls
        Args:
            ls = initial list() with values to be combined
            lvl = int() of number of values to be combined,
                    0 = blank tuple,
                    1 = tuple with 1 value,
                    2 = tuples of 2 values
        Return:
            combined = final list() that containes tuples() with combinations
        """
        if lvl == 0:
            return [tuple()]
        elif lvl ==1:
            return [(i,) for i in ls]
        elif lvl == 2:
            result = list()
            combined = list(itertools.product(ls, ls))
            combined_diff = [i for i in combined if i[0] != i[1]]
            for i in combined_diff:
                if i not in result and (i[1], i[0]) not in result:
                    result.append(i)
            return result
        else:
            print("    requests for combinations higher then 2\
                cannot be performed because FreeSurfer does not take them")


    def check_var_zero(self, variables, groups):
        """checks if all variables are zeros for a specific group
        Args:
            variables = tuple(var1, var2) for var1, var2 to be checked
            groups    = tuple(group1, group2) for group1, group2 to be checked
        Return:
            vars_zeros = Bool. True means all are zeros
        """
        values = list()
        vars_zeros = False
        for group in groups:
            for subjid in self.d_subjid:
                for var in variables:
                    if self.d_subjid[subjid][self.group_col] == group:
                        values.append(self.d_subjid[subjid][var])
        if all(v == 0 for v in values):
            vars_zeros = True
        return vars_zeros


    # def make_qdec_fsgd_g2(self):
    #     """creates the corresponding file to be used for QDEC analysis
    #         QDEC is deprecated in new FreeSurfer versions
    #     """
    #     groups_combined = self.combinations_get(self.ls_groups,
    #                                     lvl = 2)
    #     vars_2add = list()
    #     for groups in groups_combined:
    #         # checking variables for zeros, per group
    #         for variable in self.ls_vars_stats:
    #             vars_zeros = self.check_var_zero((variable,), groups)
    #             if not vars_zeros:
    #                 vars_2add.append(variable)

    #         # populating file
    #         file_name = f'qdec_g2_{groups[0]}_{groups[1]}.fsgd'
    #         file = os.path.join(self.PATHqdec, file_name)
    #         open(file, 'w').close()
    #         with open(file, 'a') as f:
    #             f.write('fsid group ')
    #             for variable in vars_2add:
    #                 f.write(f'{variable} ')
    #             f.write('\n')
    #             for _id in self.d_subjid:
    #                 group = self.d_subjid[_id][self.group_col]
    #                 if group in groups:
    #                     f.write(f'{_id} {group} ')
    #                     for variable in vars_2add:
    #                         value = str(self.d_subjid[_id][variable])
    #                         f.write(f'{value} ')
    #                     f.write('\n')
