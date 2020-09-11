#!/bin/python
# 2020.09.02


from os import system, listdir, makedirs, path, remove
import shutil, linecache, sys, json
import argparse

try:
    import pandas as pd
    import xlrd
    from pathlib import Path
except ImportError as e:
    sys.exit(e)

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
    def __init__(self, GLM_dir, GLM_file_group, id_col, group_col, variables, vars_fs):

        self.PATH_GLM_dir = GLM_dir
        self.group_col = group_col
        self.id_col = id_col
        self.PATHfsgd = path.join(self.PATH_GLM_dir,'fsgd')
        self.PATHmtx = path.join(self.PATH_GLM_dir,'contrasts')

        if not path.isdir(self.PATH_GLM_dir): makedirs(self.PATH_GLM_dir)
        shutil.copy(GLM_file_group, path.join(self.PATH_GLM_dir, Path(GLM_file_group).name))
        if not path.isdir(self.PATHfsgd): makedirs(self.PATHfsgd)
        if not path.isdir(self.PATHmtx): makedirs(self.PATHmtx)
        print(self.PATHfsgd)

        df_groups_clin = self.get_df_for_variables(GLM_file_group, variables)
        if not self.check_ready4glm(df_groups_clin[self.id_col].tolist(), vars_fs):
            sys.exit()
        d_init = df_groups_clin.to_dict()
        self.d_subjid = {}
        ls_all_vars = [key for key in d_init if key != self.id_col]
        self.ls_groups = []
        for rownr in d_init[self.id_col]:
            id = d_init[self.id_col][rownr]
            self.d_subjid[id] = {}
            for key in ls_all_vars:
                self.d_subjid[id][key] = d_init[key][rownr]
        for id in self.d_subjid:
            if self.d_subjid[id][self.group_col] not in self.ls_groups:
                self.ls_groups.append(self.d_subjid[id][self.group_col])
        self.ls_vars_stats = ls_all_vars
        self.ls_vars_stats.remove(self.group_col)

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

    def check_ready4glm(self, ids, vars_fs):

        def add_to_miss(miss, _id, file):
            if _id not in miss:
                miss[_id] = list()
            miss[_id].append(file)
            return miss

        res = True
        miss = {}
        for _id in ids:
            if path.exists(path.join(vars_fs["FS_SUBJECTS_DIR"], _id)):
                for hemi in ['lh','rh']:
                    for meas in vars_fs["GLM_measurements"]:
                        for thresh in vars_fs["GLM_thresholds"]:
                            file = hemi+'.'+meas+'.fwhm'+str(thresh)+'.fsaverage.mgh'
                            if not path.exists(path.join(vars_fs["FS_SUBJECTS_DIR"], _id, 'surf', file)):
                                miss = add_to_miss(miss, _id, file)
            else:
                miss = add_to_miss(miss, _id, 'none')
        if miss.keys():
            print('some subjects or files are missing: {}'.format(miss))
            res = False
        return res

    def make_subjects_per_group(self, df_groups_clin):
        _, subjects_per_group = _GET_Groups(df_groups_clin, self.id_col, self.group_col)
        file = 'subjects_per_group.json'
        with open(path.join(self.PATH_GLM_dir, file), 'w') as f:
            json.dump(subjects_per_group, f, indent=4)


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


    def make_files_for_glm(self):
        file = 'files_for_glm.json'
        with open(path.join(self.PATH_GLM_dir, file), 'w') as f:
            json.dump(self.files_glm, f, indent=4)




class PerformGLM():
    def __init__(self, PATHglm, FREESURFER_HOME, SUBJECTS_DIR, measurements, thresholds, cache):
        self.SUBJECTS_DIR = SUBJECTS_DIR
        self.PATHglm = PATHglm
        self.FREESURFER_HOME = FREESURFER_HOME

        self.PATHglm_glm = path.join(self.PATHglm,'glm/')
        self.PATHglm_results = path.join(self.PATHglm,'results')
        for subdir in (self.PATHglm_glm, self.PATHglm_results):
            if not path.isdir(subdir): makedirs(subdir)

        try:
            with open(path.join(self.PATHglm, 'subjects_per_group.json'),'r') as jf:
                subjects_per_group = json.load(jf)
                print('subjects per group imported')
        except Exception as e:
            print(e)
            sys.exit('subjects per group is missing')
        try:
            with open(path.join(self.PATHglm, 'files_for_glm.json'),'r') as jf:
                files_for_glm = json.load(jf)
                print('files for glm imported')
        except ImportError as e:
                print(e)
                sys.exit('files for glm is missing')

        for group in subjects_per_group:
            for subject in subjects_per_group[group]:
                if subject not in listdir(SUBJECTS_DIR):
                    print(subject,' is missing in the freesurfer folder')
                    RUN = False
                else:
                    RUN = True
        if RUN:
            self.RUN_GLM(files_for_glm, measurements, thresholds, cache)
            print('\n\nGLM DONE')
        else:
            sys.exit('some subjects are missing from the freesurfer folder')


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
                                            self.log_contrasts_with_significance(glmdir, contrast.replace('.mtx',''))
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
            f.write(path.join(glmdir,contrast_name)+'\n')


def get_parameters(projects):
    """get parameters for nimb"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-project", required=False,
        default=projects[:1][0],
        choices = projects,
        help="names of projects located in credentials_path.py/nimb/projects.json -> PROJECTS",
    )

    params = parser.parse_args()
    return params


def initiate_fs_from_sh(vars_local):
    sh_file = path.join(vars_local["NIMB_PATHS"]["NIMB_tmp"], 'source_fs.sh')
    with open(sh_file, 'w') as f:
        f.write(vars_local["FREESURFER"]["export_FreeSurfer_cmd"]+'\n')
        f.write(vars_local["FREESURFER"]["source_FreeSurfer_cmd"]+'\n')
        f.write("export SUBJECTS_DIR="+vars_local["FREESURFER"]["FS_SUBJECTS_DIR"]+'\n')
    system("chmod +x {}".format(sh_file))
    return ("source {}".format(sh_file))



if __name__ == "__main__":

    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[2]
    sys.path.append(str(top))

    import subprocess
    from distribution.logger import Log
    from setup.get_vars import Get_Vars, SetProject
    getvars = Get_Vars()
    vars_local = getvars.location_vars['local']
    projects = getvars.projects
    params = get_parameters(projects['PROJECTS'])
    vars_project = getvars.projects[params.project]
    SetProject(vars_local['NIMB_PATHS']['NIMB_tmp'], vars_local['STATS_PATHS'], params.project)
    fs_start_cmd = initiate_fs_from_sh(vars_local)

    try:
        subprocess.run(['mri_info'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    except Exception as e:
        print(e)
        print('please initiate freesurfer using the command: \n    {}'.format(fs_start_cmd))

    print('\nSTEP 1 of 2: preparing data for GLM analysis')
    PrepareForGLM(vars_local["STATS_PATHS"]["FS_GLM_dir"],
                  vars_project["GLM_file_group"],
                  vars_project["id_col"],
                  vars_project["group_col"],
                  vars_project["variables_for_glm"],
                  vars_local["FREESURFER"])

    print('\nSTEP 2 of 2: performing GLM analysis')
    PerformGLM(vars_local["STATS_PATHS"]["FS_GLM_dir"],
                            vars_local["FREESURFER"]["FREESURFER_HOME"],
                            vars_local["FREESURFER"]["FS_SUBJECTS_DIR"],
                            vars_local["FREESURFER"]["GLM_measurements"],
                            vars_local["FREESURFER"]["GLM_thresholds"],
                            vars_local["FREESURFER"]["GLM_MCz_cache"])

