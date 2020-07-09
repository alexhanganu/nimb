#!/bin/python
# 2020.07.07


from os import system, listdir, makedirs, path, remove
import shutil, linecache, sys


def _GET_Groups(df, id_col, group_col):
        groups = []
        subjects_per_group = {}
        for val in df[group_col]:
            if val not in groups:
                groups.append(val)
        for group in groups:
            subjects_per_group[group] = []
            for row in df.index.tolist():
                if df.at[row, group_col] == group:
                        subjects_per_group[group].append(df.at[row, id_col])
        return groups, subjects_per_group



class PrepareForGLM():

    #https://surfer.nmr.mgh.harvard.edu/fswiki/FsgdExamples
    def __init__(self, GLM_dir, df_groups_clin, id_col, group_col):
        self.PATH_GLM_dir = GLM_dir
        self.PATHfsgd = path.join(self.PATH_GLM_dir,'fsgd')
        self.PATHmtx = path.join(self.PATH_GLM_dir,'contrasts')
        if not path.isdir(self.PATHfsgd): makedirs(self.PATHfsgd)
        if not path.isdir(self.PATHmtx): makedirs(self.PATHmtx)
        print(self.PATHfsgd)
        self.group_col = group_col
        d_init = df_groups_clin.to_dict()
        self.d_subjid = {}
        ls_all_vars = [key for key in d_init if key != id_col]
        self.ls_groups = []
        for rownr in d_init[id_col]:
            id = d_init[id_col][rownr]
            self.d_subjid[id] = {}
            for key in ls_all_vars:
                self.d_subjid[id][key] = d_init[key][rownr]
        for id in self.d_subjid:
            if self.d_subjid[id][group_col] not in self.ls_groups:
                self.ls_groups.append(self.d_subjid[id][group_col])
        self.ls_vars_stats = ls_all_vars
        self.ls_vars_stats.remove(group_col)

        self.contrasts = {'g1v1':{'slope.mtx':['0 1','t-test with the slope>0 being positive; is the slope equal to 0? does the correlation between thickness and variable differ from zero ?',],},
            'g2v0':{'group.diff.mtx':['1 -1','t-test with Group1>Group2 being positive; is there a difference between the group intercepts? Is there a difference between groups?',],},
            'g2v1':{'group.diff.mtx':['1 -1 0 0','t-test with Group1>Group2 being positive; is there a difference between the group intercepts? Is there a difference between groups regressing out the effect of age?',],'group-x-var.mtx':['0 0 1 -1','t-test with Group1>Group2 being positive; is there a difference between the group age slopes? Note: this is an interaction between group and age. Note: not possible to test with DOSS',],
                    'g1g2.var.mtx':['0 0 0.5 0.5','This is a t-test with (Group1+Group2)/2 > 0 being positive (red/yellow). If the mean is < 0, then it will be displayed in blue/cyan; does mean of group age slope differ from 0? Is there an average affect of age regressing out the effect of group?',],}}
        # contrasts_not_used = 
                # {'g1v0':{'intercept.mtx':['1','t-test with the intercept>0 being positive; is the intercept/mean equal to 0?',],},
                # 'g1v1':{'intercept.mtx':['1 0','t-test with the intercept>0 being positive; is the intercept equal to 0? Does the average thickness differ from zero ?',],},
                # 'g1v2':{'main.mtx':['1 0 0','t-test with offset>0 being positive; the intercept/offset is different than 0 after regressing out the effects of var1 and var2',],'var1.mtx':['0 1 0','t-test with var1 slope>0 being positive',],'var2.mtx':['0 0 1','t-test with var2 slope>0 being positive',],},
                # 'g2v0':{'group1.mtx':['1 0','t-test with Group1>0 being positive; is there a main effect of Group1? Does the mean of Group1 equal 0?',],'group2.mtx':['0 1','t-test with Group2>0 being positive; is there a main effect of Group2? Does the mean of Group2 equal 0?',],'g1g2.intercept.mtx':['0.5 0.5','t-test with (Group1+Group2)/2 > 0 being positive (red/yellow). If the mean is < 0, then it will be displayed in blue/cyan; does mean of the group means differ from 0?',],}
                # 'g2v1':{'g1g2.intercept.mtx':['0.5 0.5 0 0','t-test with (Group1+Group2)/2 > 0 being positive (red/yellow). If the mean is < 0, then it will be displayed in blue/cyan; does mean of group intercepts differ from 0? Is there an average main effect regressing out age?',]},}
        gd2 = {'g1v1':['dods',],'g2v0':['doss','dods',],'g2v1':['dods',],}#gd2_not_used = {'g1v0':['dods',],'g1v2':['dods',],}
        self.files_glm = {}
        for contrast_type in self.contrasts:
            self.files_glm[contrast_type]={}
            self.files_glm[contrast_type]['fsgd'] = []
            self.files_glm[contrast_type]['mtx'] = []
            self.files_glm[contrast_type]['mtx_explanation'] = []
            self.files_glm[contrast_type]['gd2mtx'] = gd2[contrast_type]

        print('creating list of subjects')
        self.make_py_f_subjects(df_groups_clin, id_col)
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
        self.make_py_f()
        print('creating qdec fsgd files')
        self.make_qdec_fsgd_g2()

    def make_py_f_subjects(self, df_groups_clin, id_col):

        _, subjects_per_group = _GET_Groups(df_groups_clin, id_col, self.group_col)

        file = 'subjects_per_group.py'
        open(path.join(self.PATH_GLM_dir,file), 'w').close()
        with open(path.join(self.PATH_GLM_dir,file), 'a') as f:
            f.write('#!/bin/python/\nsubjects_per_group = {')
            for group in subjects_per_group:
                f.write('\''+group+'\':[')
                for subject in subjects_per_group[group]:
                    f.write('\''+subject+'\',')
                f.write('],')
            f.write('}')


    def make_fsgd_g1g2v0(self):
        file = 'g2v0'+'_'+self.ls_groups[0]+'_'+self.ls_groups[1]+'.fsgd'
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
        for contrast_type in self.contrasts:
            for contrast_name in self.contrasts[contrast_type]:
                file = contrast_type+'_'+contrast_name
                open(path.join(self.PATHmtx,file), 'w').close()
                with open(path.join(self.PATHmtx,file), 'a') as f:
                    f.write(self.contrasts[contrast_type][contrast_name][0])
                self.files_glm[contrast_type]['mtx'].append(file)
                self.files_glm[contrast_type]['mtx_explanation'].append(self.contrasts[contrast_type][contrast_name][1])



    def make_py_f(self):
        file = 'files_for_glm.py'
        open(path.join(self.PATH_GLM_dir,file), 'w').close()
        with open(path.join(self.PATH_GLM_dir,file), 'a') as f:
            f.write('#!/bin/python/\nfiles_for_glm = {')
            for contrast_type in self.files_glm:
                f.write('\''+contrast_type+'\':{')
                for group in self.files_glm[contrast_type]:
                    f.write('\''+group+'\':[')
                    for value in self.files_glm[contrast_type][group]:
                        f.write('\''+value+'\',')
                    f.write('],')
                f.write('},')
            f.write('}')




class PerformGLM():
    def __init__(self, PATHglm, FREESURFER_HOME, SUBJECTS_DIR, measurements, thresholds, cache):
        self.SUBJECTS_DIR = SUBJECTS_DIR
        self.PATHglm = PATHglm
        self.FREESURFER_HOME = FREESURFER_HOME

        self.PATHglm_glm = path.join(self.PATHglm,'glm/')
        self.PATHglm_results = path.join(self.PATHglm,'results')
        for subdir in (self.PATHglm_glm, self.PATHglm_results):
            if not path.isdir(subdir): makedirs(subdir)

        for file in ('subjects_per_group.py','files_for_glm.py'):
            shutil.copy(path.join(self.PATHglm,file), path.join(path.dirname(path.abspath(__file__)),file))
        try:
            from subjects_per_group import subjects_per_group
            remove(path.join(path.dirname(__file__),'subjects_per_group.py'))
            print('subjects per group imported')
            try:
                from files_for_glm import files_for_glm
                remove(path.join(path.dirname(__file__),'files_for_glm.py'))
                print('files for glm imported')
            except ImportError as e:
                print(e)
                sys.exit('files for glm is missing')
        except ImportError as e:
            print(e)
            sys.exit('subjects per group is missing')

        for group in subjects_per_group:
            for subject in subjects_per_group[group]:
                if subject not in listdir(SUBJECTS_DIR):
                    print(subject,' is missing in the freesurfer folder')
                    RUN = False
                else:
                    RUN = True
        if RUN:
            # self.fsgd_win_to_unix(files_for_glm)
            self.RUN_GLM(files_for_glm, measurements, thresholds, cache)
            print('\n\nGLM DONE')
        else:
            sys.exit('some subjects are missing from the freesurfer folder')

            

    # def fsgd_win_to_unix(self, files_for_glm):
    #     if not path.isdir(path.join(self.PATHglm,'fsgd_unix')): makedirs(path.join(self.PATHglm,'fsgd_unix'))
    #     for contrast_type in files_for_glm:
    #         for fsgd_file in files_for_glm[contrast_type]['fsgd']:
    #             fsgd_f_unix = path.join(self.PATHglm,'fsgd_unix',fsgd_file.replace('.fsgd','')+'_unix.fsgd')
    #             if not path.isfile(fsgd_f_unix):
    #                 system('cat '+path.join(self.PATHglm,'fsgd',fsgd_file)+' | sed \'s/\\r/\\n/g\' > '+fsgd_f_unix)

    def RUN_GLM(self, files_for_glm, measurements, thresholds, cache):
        print('performing GLM analysis using mri_glmfit')

        hemispheres = ['lh','rh']
        for contrast_type in files_for_glm:
            for fsgd_file in files_for_glm[contrast_type]['fsgd']:
                fsgd_f_unix = path.join(self.PATHglm,'fsgd',fsgd_file.replace('.fsgd','')+'_unix.fsgd')
                for hemi in hemispheres:
                    for meas in measurements:
                        for thresh in thresholds:
                            analysis_name = fsgd_file.replace('.fsgd','')+'.'+meas+'.'+hemi+'.fwhm'+str(thresh)
                            glmdir = path.join(self.PATHglm_glm,analysis_name)
                            mgh_f = path.join(glmdir,meas+'.'+hemi+'.fwhm'+str(thresh)+'.y.mgh')
                            if not path.isdir(glmdir):
                                self.run_mris_preproc(fsgd_f_unix, meas, thresh, hemi, mgh_f)
                                if not path.isfile(mgh_f):
                                    print(mgh_f+' not created; ERROR in mris_preproc')
                                    sys.exit('mris_preproc ERROR')
                                # system('mris_preproc --fsgd '+fsgd_f_unix+' --cache-in '+meas+'.fwhm'+str(thresh)+'.fsaverage --target fsaverage --hemi '+hemi+' --out '+mgh_f)
                                for contrast in files_for_glm[contrast_type]['mtx']:
                                    explanation = files_for_glm[contrast_type]['mtx_explanation'][files_for_glm[contrast_type]['mtx'].index(contrast)]
                                    for gd2mtx in files_for_glm[contrast_type]['gd2mtx']:
                                        self.run_mri_glmfit(mgh_f, fsgd_f_unix, gd2mtx, glmdir, hemi, contrast)
                                        # system('mri_glmfit --y '+mgh_f+' --fsgd '+fsgd_f_unix+' '+gd2mtx+' --glmdir '+glmdir+' --surf fsaverage '+hemi+' --label '+path.join(self.SUBJECTS_DIR,'fsaverage','label',hemi+'.aparc.label')+' --C '+path.join(self.PATHglm,'contrasts',contrast))
                                        if self.check_maxvox(glmdir, contrast.replace('.mtx','')):
                                            self.log_contrasts_with_significance(self, glmdir, contrast_name)
                                        self.run_mri_surfcluster(glmdir, contrast.replace('.mtx',''), hemi, contrast_type, analysis_name, meas, cache, explanation)

    def run_mris_preproc(self, fsgd_file, meas, thresh, hemi, mgh_f):
        system('mris_preproc --fsgd '+fsgd_file+' --cache-in '+meas+'.fwhm'+str(thresh)+'.fsaverage --target fsaverage --hemi '+hemi+' --out '+mgh_f)

    def run_mri_glmfit(self, mgh_f, fsgd_file, gd2mtx, glmdir, hemi, contrast):
        label_cmd = ' --label '+path.join(self.SUBJECTS_DIR,'fsaverage','label',hemi+'.aparc.label')
        contrast_cmd = ' --C '+path.join(self.PATHglm,'contrasts',contrast)
        cmd = 'mri_glmfit --y '+mgh_f+' --fsgd '+fsgd_file+' '+gd2mtx+' --glmdir '+glmdir+' --surf fsaverage '+hemi+label_cmd+contrast_cmd
        system(cmd)


    def run_mri_surfcluster(self, glmdir, contrast_name, hemi, contrast_type, analysis_name, meas, cache, explanation):
        sim_direction = ['pos', 'neg',]
        contrastdir = path.join(glmdir,contrast_name)
        fwhm = {'thickness': {'lh': '15','rh': '15'},'area': {'lh': '24','rh': '25'},'volume': {'lh': '16','rh': '16'},}
        measure_abbreviation = {'thickness':'th','area':'ar','volume':'vol'} # needs to be checked, it is possible that only .th is used
        for direction in sim_direction:
            sig_f = path.join(contrastdir,'sig.mgh')
            cwsig_mc_f = path.join(contrastdir,'mc-z.'+direction+'.'+measure_abbreviation[meas]+str(cache)+'.sig.cluster.mgh')
            vwsig_mc_f = path.join(contrastdir,'mc-z.'+direction+'.'+measure_abbreviation[meas]+str(cache)+'.sig.vertex.mgh')
            sum_mc_f = path.join(contrastdir,'mc-z.'+direction+'.'+measure_abbreviation[meas]+str(cache)+'.sig.cluster.summary')
            ocn_mc_f = path.join(contrastdir,'mc-z.'+direction+'.'+measure_abbreviation[meas]+str(cache)+'.sig.ocn.mgh')
            oannot_mc_f = path.join(contrastdir,'mc-z.'+direction+'.'+measure_abbreviation[meas]+str(cache)+'.sig.ocn.annot')
            csdpdf_mc_f = path.join(contrastdir,'mc-z.'+direction+'.'+measure_abbreviation[meas]+str(cache)+'.pdf.dat')
            if meas != 'curv':
                csd_mc_f = path.join(self.FREESURFER_HOME,'average','mult-comp-cor','fsaverage',hemi,'cortex','fwhm'+fwhm[meas][hemi],direction,'th'+str(cache),'mc-z.csd')
                system('mri_surfcluster --in '+sig_f+' --csd '+csd_mc_f+' --mask '+path.join(glmdir,'mask.mgh')+' --cwsig '+cwsig_mc_f+' --vwsig '+vwsig_mc_f+' --sum '+sum_mc_f+' --ocn '+ocn_mc_f+' --oannot '+oannot_mc_f+' --csdpdf '+csdpdf_mc_f+' --annot aparc --cwpvalthresh 0.05 --surf white')                                        
                if self.check_mcz_summary(sum_mc_f):
                    self.cluster_stats_to_file(analysis_name, sum_mc_f, contrast_name.replace(contrast_type+'_',''), direction, explanation)
            else:
                system('mri_glmfit-sim --glmdir '+path.join(glmdir,contrast_name)+' --cache '+str(cache)+' '+direction+' --cwp 0.05 --2spaces')

    def check_maxvox(self, glmdir, contrast_name):
        val = [i.strip() for i in open(path.join(glmdir,contrast_name,'maxvox.dat')).readlines()][0].split()[0]
        if float(val) > 3.0 or float(val) < -3.0:
            return True
        else:
            return False

    def check_mcz_summary(self, file):
        if len(linecache.getline(file, 42).strip('\n')) > 0:
            return True
        else:
            return False


    def cluster_stats_to_file(self, analysis_name, sum_mc_f, contrast_name, direction, explanation):
        file = path.join(self.PATHglm_results,'cluster_stats.log')
        if not path.isfile(file):
            open(file,'w').close()
        ls = list()
        for line in list(open(sum_mc_f))[41:sum(1 for line in open(sum_mc_f))]:
            ls.append(line.rstrip())
        with open(file, 'a') as f:
            f.write(analysis_name+'_'+contrast_name+'_'+direction+'\n')
            f.write(explanation+'\n')
            for value in ls:
                f.write(value+'\n')
            f.write('\n')

    def log_contrasts_with_significance(self, glmdir, contrast_name):
        file = path.join(self.PATHglm_results,'sig_contrasts.log')
        if not path.isfile(file):
            open(file,'w').close()
        with open(file, 'a') as f:
            f.write(glmdir+'_'+contrast_name'\n')




if __name__ == '__main__':
    try:
        import pandas as pd
        import xlrd
        from pathlib import Path
    except ImportError as e:
        sys.exit(e)

    print('Please check that all required variables for the GLM analysis are defined in the var.py file')
    print('before running the script, remember to source $FREESURFER_HOME')
    print('check if fsaverage is present in SUBJECTS_DIR')
    print('each subject must include at least the folders: surf and label')

    from var import cuser, FREESURFER_HOME, SUBJECTS_DIR, GLM_dir, GLM_file_group, id_col, group_col, variables_for_glm, GLM_measurements, GLM_thresholds, GLM_MCz_cache

    print('current variables are: '+
        '\n    FREESURFER_HOME: '+FREESURFER_HOME+
        '\n    SUBJECTS_DIR: '+SUBJECTS_DIR+
        '\n    GLM_dir: '+GLM_dir+
        '\n    GLM_file_group: '+GLM_file_group+
        '\n    id_col: '+id_col+
        '\n    group_col: '+group_col)


    print('doing GLM for file:'+GLM_file_group)
    if not path.isdir(GLM_dir): makedirs(GLM_dir)

    # shutil.copy(GLM_file_group, path.join(GLM_dir,Path(GLM_file_group).name))

    # if '.csv' in GLM_file_group:
    #     df_groups_clin = pd.read_csv(GLM_file_group)
    # elif '.xlsx' in GLM_file_group or '.xls' in file_group:
    #     df_groups_clin = pd.read_excel(GLM_file_group)
    # cols2drop = list()
    # for col in df_groups_clin.columns.tolist():
    #     if col not in variables_for_glm+[id_col,group_col]:
    #         cols2drop.append(col)
    # if cols2drop:
    #     df_groups_clin.drop(columns=cols2drop, inplace=True)

    # print('\nSTEP 1 of 2: creating files required for GLM')
    # PrepareForGLM(GLM_dir, df_groups_clin, id_col, group_col)

    print('\nSTEP 2 of 2: performing GLM analysis')
    PerformGLM(GLM_dir, FREESURFER_HOME, SUBJECTS_DIR, GLM_measurements, GLM_thresholds, GLM_MCz_cache)













# FOLLOWING script moved to fs_glm_extract_images.py
# class SaveGLMimages():

#     def __init__(self, GLM_dir, files_for_glm, measurements, thresholds, cache):
#         self.PATHglm = GLM_dir
#         self.PATHglm_glm = path.join(self.PATHglm,'glm/')

#         hemispheres = ['lh','rh']
#         sim_direction = ['pos', 'neg',]

#         for contrast_type in files_for_glm:
#             for fsgd_file in files_for_glm[contrast_type]['fsgd']:
#                 fsgd_f_unix = path.join(self.PATHglm,'fsgd_unix',fsgd_file.replace('.fsgd','')+'_unix.fsgd')
#                 for hemi in hemispheres:
#                     for meas in measurements:
#                         for thresh in thresholds:
#                             analysis_name = fsgd_file.replace('.fsgd','')+'.'+meas+'.'+hemi+'.fwhm'+str(thresh)
#                             glmdir = path.join(self.PATHglm_glm,analysis_name)
#                             contrastdir = glmdir+'/'+contrast_name+'/'

#                             for contrast in files_for_glm[contrast_type]['mtx']:
#                                 if self.check_maxvox(glmdir, contrast.replace('.mtx','')):
#                                     self.make_images_results_fdr(hemi, glmdir, contrast.replace('.mtx',''), 'sig.mgh', 3.0)
#                                 for direction in sim_direction:
#                                     sum_mc_f = contrastdir+'mc-z.'+direction+'.th'+str(cache)+'.sig.cluster.summary'
#                                     cwsig_mc_f = contrastdir+'mc-z.'+direction+'.th'+str(cache)+'.sig.cluster.mgh'
#                                     oannot_mc_f = contrastdir+'mc-z.'+direction+'.th'+str(cache)+'.sig.ocn.annot'
#                                     if self.check_mcz_summary(sum_mc_f):
#                                         self.make_images_results_mc(hemi, analysis_name, contrast.replace('.mtx','').replace(contrast_type+'_',''), direction, cwsig_mc_f, oannot_mc_f, str(cache), 1.3)



#     def check_maxvox(self, glmdir, contrast_name):
#         val = [i.strip() for i in open(path.join(glmdir,contrast_name,'maxvox.dat')).readlines()][0].split()[0]
#         if float(val) > 3.0 or float(val) < -3.0:
#             return True
#         else:
#             return False

#     def check_mcz_summary(self, file):
#         if len(linecache.getline(file, 42).strip('\n')) > 0:
#             return True
#         else:
#             return False

#     def make_images_results_mc(self, hemi, analysis_name, contrast, direction, cwsig_mc_f, oannot_mc_f, cache, thresh):
#         self.PATH_save_mc = self.PATHglm+'results/mc/'
#         if not path.isdir(self.PATH_save_mc):
#             makedirs(self.PATH_save_mc)
#         fv_cmds = ['-ss '+self.PATH_save_mc+analysis_name+'_'+contrast+'_lat_mc_'+direction+cache+'.tiff -noquit',
#                     '-cam Azimuth 180',
#                     '-ss '+self.PATH_save_mc+analysis_name+'_'+contrast+'_med_mc_'+direction+cache+'.tiff -quit',]
#         open('fv.cmd','w').close()
#         with open('fv.cmd','a') as f:
#             for line in fv_cmds:
#                 f.write(line+'\n')

#         system('freeview -f $SUBJECTS_DIR/fsaverage/surf/'+hemi+'.inflated:overlay='+cwsig_mc_f+':overlay_threshold='+str(thresh)+',5:annot='+oannot_mc_f+' -viewport 3d -layout 1 -cmd fv.cmd')


#     def make_images_results_fdr(self, hemi, glmdir, contrast_name, file, thresh):
#         self.PATH_save_fdr = self.PATHglm+'results/fdr/'
#         if not path.isdir(self.PATH_save_fdr):
#             makedirs(self.PATH_save_fdr)

#         tksurfer_cmds = ['set colscalebarflag 1', 'set scalebarflag 1', 'save_tiff '+self.PATH_save_fdr+contrast_name+'_'+str(3.0)+'_lat.tiff',
#         'rotate_brain_y 180', 'redraw', 'save_tiff '+self.PATH_save_fdr+contrast_name+'_'+str(3.0)+'_med.tiff',
#         'sclv_set_current_threshold_using_fdr 0.05 0', 'redraw', 'save_tiff '+self.PATH_save_fdr+contrast_name+'_fdr_med.tiff',
#         'rotate_brain_y 180', 'redraw', 'save_tiff '+self.PATH_save_fdr+contrast_name+'_fdr_lat.tiff','exit']
#         open('scr.tcl','w').close()
#         with open('scr.tcl','a') as f:
#             for line in tksurfer_cmds:
#                 f.write(line+'\n')
#         print('tksurfer fsaverage '+hemi+' inflated -overlay '+glmdir+'/'+contrast_name+'/'+file+' -fthresh '+str(thresh)+' -tcl scr.tcl')
#         system('tksurfer fsaverage '+hemi+' inflated -overlay '+glmdir+'/'+contrast_name+'/'+file+' -fthresh '+str(thresh)+' -tcl scr.tcl')

