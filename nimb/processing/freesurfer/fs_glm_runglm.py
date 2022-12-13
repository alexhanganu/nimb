#!/bin/python
# last update: 20201218

import os
import sys
import linecache
import shutil
try:
    from processing.freesurfer import fs_definitions
except ImportError:
    import fs_definitions


class PerformGLM():

    def __init__(self,
                all_vars,
                PATHglm,
                sig_fdr_thresh = 3.0):
        '''
        sig_fdr_thresh at 3.0 corresponds to p = 0.001;
        for p=0.05 use value 1.3,
        but it should be used ONLY for visualisation.
        '''

        vars_fs                    = all_vars.location_vars['local']["FREESURFER"]
        self.FREESURFER_HOME       = vars_fs["FREESURFER_HOME"]
        self.SUBJECTS_DIR          = vars_fs["SUBJECTS_DIR"]
        self.measurements          = vars_fs["GLM_measurements"]
        self.thresholds            = vars_fs["GLM_thresholds"]
        self.mc_cache_thresh       = vars_fs["GLM_MCz_cache"]
        param                      = fs_definitions.FSGLMParams(PATHglm)
        self.PATHglm               = PATHglm
        self.sig_fdr_thresh        = sig_fdr_thresh

        self.PATHglm_glm           = param.PATHglm_glm
        self.PATH_img              = param.PATH_img
        self.PATHglm_results       = param.PATHglm_results
        self.sig_fdr_json          = param.sig_fdr_json
        self.sig_mc_json           = param.sig_mc_json
        self.err_mris_preproc_file = param.err_mris_preproc_file
        self.mcz_sim_direction     = param.mcz_sim_direction
        self.hemispheres           = fs_definitions.hemi
        self.GLM_sim_fwhm4csd      = param.GLM_sim_fwhm4csd
        self.GLM_MCz_meas_codes    = param.GLM_MCz_meas_codes
        self.cluster_stats         = param.cluster_stats
        self.cluster_stats_2csv    = param.cluster_stats_2csv
        self.sig_contrasts         = param.sig_contrasts

        RUN = True
        # get files_glm.
        try:
            files_glm = load_json(param.files_for_glm)
            print(f'    successfully uploaded file: {param.files_for_glm}')
        except ImportError as e:
            print(e)
            print(f'    file {param.files_for_glm} is missing')
            RUN = False

        # get file with subjects per group
        try:
            subjects_per_group = load_json(param.subjects_per_group)
            print(f'    successfully uploaded file: {param.subjects_per_group}')
        except Exception as e:
            print(e)
            print(f'    file {param.subjects_per_group} is missing')
            RUN = False

        # checking that all subjects are present
        print('    subjects are located in: {}'.format(self.SUBJECTS_DIR))
        for group in subjects_per_group:
            for subject in subjects_per_group[group]:
                if subject not in os.listdir(self.SUBJECTS_DIR):
                    print(f' subject is missing from FreeSurfer Subjects folder: {subject}')
                    RUN = False
                    break

        for subdir in (self.PATHglm_glm, self.PATHglm_results, self.PATH_img):
            if not os.path.isdir(subdir): os.makedirs(subdir)
        if not os.path.isfile(self.sig_contrasts):
            open(self.sig_contrasts,'w').close()

        if RUN:
            self.err_preproc  = list()
            self.sig_fdr_data = dict()
            self.sig_mc_data  = dict()
            self.run_loop(files_glm)
            if self.err_preproc:
                save_json(self.err_preproc, self.err_mris_preproc_file)
            if self.sig_fdr_data:
                save_json(self.sig_fdr_data, self.sig_fdr_json)
            if self.sig_mc_data:
                save_json(self.sig_mc_data, self.sig_mc_json)
            if os.path.exists(self.cluster_stats):
                ClusterFile2CSV(self.cluster_stats,
                                self.cluster_stats_2csv)
            print('\n\nGLM DONE')
        else:
            sys.exit('some ERRORS were found. Cannot perform FreeSurfer GLM')


    def run_loop(self, files_glm):
        print('    performing GLM analysis using mri_glmfit')
        for fsgd_type in files_glm:
            for fsgd_file in files_glm[fsgd_type]['fsgd']:
                fsgd_file_name = fsgd_file.split("/")[-1].replace('.fsgd','')
                fsgd_f_unix = os.path.join(self.PATHglm,'fsgd',fsgd_file_name+'_unix.fsgd')
                for hemi in self.hemispheres:
                    for meas in self.measurements:
                        for thresh in self.thresholds:
                            self.RUN_GLM(fsgd_type, files_glm, fsgd_file_name,
                                         fsgd_f_unix, hemi, meas, thresh)


    def RUN_GLM(self, fsgd_type, files_glm, fsgd_file_name, fsgd_f_unix,
                      hemi, meas, thresh):
        """do GLM using mri_glmfit
            can add flags:
                --skew: to compute skew and p-value for skew
                --kurtosis: to compute kurtosis and p-value for kurtosis
                --pca: perform pca/svd analysis on residual
                --save-yhat: save signal estimate
            can run mri_glmfit only for ROIs with command:
                mri_glmfit --label or
                mri_glmfit --tale (instead of --y)
                    the table must be created with the first column being subject name
                    and first row being clustername (Cluter 1, Cluster 2)
                    col = 1, row = 1 can by dummy string (e.g., "dummy")
        """
        glm_analysis = '{}.{}.fwhm{}'.format(meas, hemi, str(thresh))
        analysis_name = '{}.{}'.format(fsgd_file_name, glm_analysis)
        glmdir = os.path.join(self.PATHglm_glm, analysis_name)
        mgh_f = os.path.join(glmdir, '{}.y.mgh'.format(glm_analysis))
        if not os.path.isdir(glmdir):
            self.run_mris_preproc(fsgd_f_unix, meas, thresh, hemi, mgh_f)
            if os.path.isfile(mgh_f):
                for contrast_file in files_glm[fsgd_type]['mtx']:
                    fsgd_type_contrast = contrast_file.replace('.mtx','')
                    contrast = fsgd_type_contrast.replace(fsgd_type+'_','')
                    contrast_f_ix = files_glm[fsgd_type]['mtx'].index(contrast_file)
                    explanation = files_glm[fsgd_type]['mtx_explanation'][contrast_f_ix]
                    for gd2mtx in files_glm[fsgd_type]['gd2mtx']:
                        self.run_mri_glmfit(mgh_f, fsgd_f_unix, gd2mtx, glmdir,
                                            hemi, contrast_file)
                        if self.check_maxvox(glmdir, fsgd_type_contrast):
                            self.log_contrasts_with_significance(analysis_name,
                                                                fsgd_type_contrast)
                            self.prepare_for_image_extraction_fdr(hemi, glmdir, analysis_name,
                                                                  fsgd_type_contrast)
                        self.run_mri_surfcluster(glmdir, fsgd_type_contrast,
                                                 hemi, contrast, analysis_name,
                                                 meas, explanation)
            else:
                print('{} not created; ERROR in mris_preproc'.format(mgh_f))
                self.err_preproc.append(mgh_f)


    def run_mris_preproc(self, fsgd_file, meas, thresh, hemi, mgh_f):
        f_cache = '{}.fwhm{}.fsaverage'.format(meas, str(thresh))
        cmd_tail = ' --target fsaverage --hemi {} --out {}'.format(hemi, mgh_f)
        os.system('mris_preproc --fsgd {} --cache-in {}{}'.format(fsgd_file, f_cache, cmd_tail))


    def run_mri_glmfit(self, mgh_f, fsgd_file, gd2mtx, glmdir, hemi, contrast_file):
        cmd_header   = 'mri_glmfit --y {} --fsgd {} {}'.format(mgh_f, fsgd_file, gd2mtx)
        glmdir_cmd   = '--glmdir {}'.format(glmdir)
        path_2label  = os.path.join(self.SUBJECTS_DIR, 'fsaverage', 'label', hemi+'.aparc.label')
        surf_label   = '--surf fsaverage {} --label {}'.format(hemi, path_2label)
        contrast_cmd = '--C {}'.format(os.path.join(self.PATHglm, 'contrasts', contrast_file))
        cmd          = '{} {} {} {}'.format(cmd_header, glmdir_cmd, surf_label, contrast_cmd)
        os.system(cmd)


    def check_maxvox(self, glmdir, fsgd_type_contrast):
        res = False
        maxvox = os.path.join(glmdir, fsgd_type_contrast, 'maxvox.dat')
        if os.path.exists(maxvox):
            val = [i.strip() for i in open(maxvox).readlines()][0].split()[0]
            if float(val) > self.sig_fdr_thresh or float(val) < -self.sig_fdr_thresh:
                res = True
        return res


    def log_contrasts_with_significance(self, analysis_name, fsgd_type_contrast):
        with open(self.sig_contrasts, 'a') as f:
            f.write(f'{analysis_name}/{fsgd_type_contrast}\n')


    def run_mri_surfcluster(self,
                            glmdir,
                            fsgd_type_contrast,
                            hemi,
                            contrast,
                            analysis_name,
                            meas,
                            explanation):
        '''
            https://surfer.nmr.mgh.harvard.edu/fswiki/FsTutorial/MultipleComparisonsV6.0Perm
            --glmdir: Specify the same GLM directory
            --perm: Run a permuation simulation 
            Vertex-wise/cluster-forming threshold of (13 = p < .05, 2 = p < .01).
            direction: the sign of analysis ("neg" for negative, "pos" for positive, or "abs" for absolute/unsigned)
            --cwp 0.05 : Keep clusters that have cluster-wise p-values < 0.05. To see all clusters, set to .999
            --2spaces : adjust p-values for two hemispheres
        '''
        path_2contrast = os.path.join(glmdir, fsgd_type_contrast)
        mcz_meas = self.GLM_MCz_meas_codes[meas]
        for direction in self.mcz_sim_direction:
            mcz_header  = 'mc-z.{}.{}{}'.format(direction, mcz_meas, str(self.mc_cache_thresh))
            sig_f       = os.path.join(path_2contrast,'sig.mgh')
            cwsig_mc_f  = os.path.join(path_2contrast,'{}.sig.cluster.mgh'.format(mcz_header))
            vwsig_mc_f  = os.path.join(path_2contrast,'{}.sig.vertex.mgh'.format(mcz_header))
            sum_mc_f    = os.path.join(path_2contrast,'{}.sig.cluster.summary'.format(mcz_header))
            ocn_mc_f    = os.path.join(path_2contrast,'{}.sig.ocn.mgh'.format(mcz_header))
            oannot_mc_f = os.path.join(path_2contrast,'{}.sig.ocn.annot'.format(mcz_header))
            csdpdf_mc_f = os.path.join(path_2contrast,'{}.pdf.dat'.format(mcz_header))
            if meas != 'curv':
                path_2fsavg = os.path.join(self.FREESURFER_HOME, 'average', 'mult-comp-cor', 'fsaverage')
                fwhm = 'fwhm{}'.format(self.GLM_sim_fwhm4csd[meas][hemi])
                th   = 'th{}'.format(str(self.mc_cache_thresh))
                csd_mc_f = os.path.join(path_2fsavg, hemi, 'cortex', fwhm, direction, th, 'mc-z.csd')
                cmd_header = 'mri_surfcluster --in {} --csd {}'.format(sig_f, csd_mc_f)
                mask_cmd   = '--mask {}'.format(os.path.join(glmdir,'mask.mgh'))
                cmd_params = '--cwsig {} --vwsig {} --sum {} --ocn {} --oannot {} --csdpdf {}'.format(
                                cwsig_mc_f, vwsig_mc_f, sum_mc_f, ocn_mc_f, oannot_mc_f, csdpdf_mc_f)
                cmd_tail   = '--annot aparc --cwpvalthresh 0.05 --surf white'
                os.system('{} {} {} {}'.format(cmd_header, mask_cmd, cmd_params, cmd_tail))
                if self.check_mcz_summary(sum_mc_f):
                    # self.get_cohensd_mean_per_contrast(path_2contrast,
                    #                                     ocn_mc_f)
                    self.cluster_stats_to_file(analysis_name,
                                                sum_mc_f,
                                                contrast,
                                                direction,
                                                explanation)
                    self.prepare_for_image_extraction_mc(hemi, analysis_name, path_2contrast,
                                                        fsgd_type_contrast, contrast, direction,
                                                        cwsig_mc_f, oannot_mc_f)
            else:
                glmdir_fsgd_contrast = os.path.join(glmdir, fsgd_type_contrast)
                cmd_header = f'mri_glmfit-sim --glmdir {glmdir_fsgd_contrast}'
                cmd_cache  = f'--cache {str(self.mc_cache_thresh)} {direction}'
                cmd_perm   = f'--perm 1000 1.3 {direction}'
                cmd_tail   = f'--cwp 0.05 --2spaces'
                os.system(f'{cmd_header} {cmd_cache} {cmd_tail}')
                if self.check_mcz_summary(sum_mc_f):
                    self.cluster_stats_to_file(analysis_name,
                                                sum_mc_f,
                                                contrast,
                                                direction,
                                                explanation)
                os.system(f'{cmd_header} {cmd_perm} {cmd_tail}')


    def check_mcz_summary(self, file):
        if len(linecache.getline(file, 42).strip('\n')) > 0:
            return True
        else:
            return False


    def get_cohensd_mean_per_contrast(self,
                                    path_2contrast,
                                    ocn_mc_f):
        """extract the Mean value per contrast
            that represents the effect size
            as per: https://www.mail-archive.com/freesurfer@nmr.mgh.harvard.edu/msg52144.html
                    https://www.mail-archive.com/freesurfer@nmr.mgh.harvard.edu/msg57316.html
        """
        cohensd_sum_filename = "cohensd.sum.dat"
        pcc_r_filename = "pcc.r.dat"
        os.system(f'cd {path_2contrast}')
        os.system('fscalc gamma.mgh div ../rstd.mgh -o cohensd.mgh')
        os.system(f'mri_segstats --i cohensd.mgh --seg {ocn_mc_f} --exclude 0 --o {cohensd_sum_filename}')
        self.cohensd_sum = os.path.join(path_2contrast, cohensd_sum_filename)
        print(f'    extracting partial correlation coefficient R from pcc.mgh')
        os.system(f'mri_segstats --i pcc.mgh --seg {ocn_mc_f} --exclude 0 --o {pcc_r_filename}')
        # The mean in file sum.dat is the the mean column
        # Probably: Cohen's D mean


    def cluster_stats_to_file(self,
                                analysis_name,
                                sum_mc_f,
                                contrast,
                                direction,
                                explanation):
        if not os.path.isfile(self.cluster_stats):
            open(self.cluster_stats,'w').close()
        ls = list()
        for line in list(open(sum_mc_f))[41:sum(1 for line in open(sum_mc_f))]:
            ls.append(line.rstrip())
        with open(self.cluster_stats, 'a') as f:
            f.write('{}_{}_{}\n'.format(analysis_name, contrast, direction))
            f.write(explanation+'\n')
            for value in ls:
                f.write(value+'\n')
            f.write('\n')


    def prepare_for_image_extraction_fdr(self, hemi, glmdir, analysis_name, fsgd_type_contrast):
        '''copying sig.mgh file from the contrasts to the image/contrast folder
            populating dict with significant fdr data, that contains the data to access the sig.mgh file
        Args:
            hemi: hemisphere
            glmdir: dir for the analysis = self.PATHglm_glm + analysis_name
            analysis_name: name of the folder for glm analysis
            fsgd_type_contrast: name of the folder for the specific contrast used
        Return:
            none
            creates corresponding folder in the self.PATH_img folder
            populates the sig_fdr_data dictionary
        '''
        glm_image_dir = os.path.join(self.PATH_img, analysis_name, fsgd_type_contrast)
        if not os.path.exists(glm_image_dir):
            os.makedirs(glm_image_dir)
        sig_file = 'sig.mgh'
        shutil.copy(os.path.join(glmdir, fsgd_type_contrast, sig_file), glm_image_dir)

        sig_count = len(self.sig_fdr_data.keys())+1
        self.sig_fdr_data[sig_count] = {
                                'hemi'         : hemi,
                                'analysis_name': analysis_name,
                                'fsgd_type_contrast': fsgd_type_contrast,
                                'sig_thresh'   : self.sig_fdr_thresh}


    def prepare_for_image_extraction_mc(self, hemi, analysis_name, path_2contrast,
                                            fsgd_type_contrast, contrast, direction,
                                            cwsig_mc_f, oannot_mc_f):
        '''copying MCz significancy files file from the contrasts to the image/analysis_name/fsgd_type_contrast folder
            populating dict with significant MCz data, in order to extract the images
        Args:
            hemi: hemisphere
            analysis_name: as previous defined
            path_2contrast: folder where the post FS-GLM files are stores
            fsgd_type_contrast: specific folder in the path_2contrast
            contrast: name of the contrast used
            direction: direction of the MCz analysis
            cwsig_mc_f: file with significant MCz results
            oannot_mc_f: file with significant MCz annotations
        Return:
            none
            creates corresponding folder in the self.PATH_img folder
            populates the sig_mc_data dictionary
        '''
        glm_image_dir = os.path.join(self.PATH_img, analysis_name, fsgd_type_contrast)
        if not os.path.exists(glm_image_dir):
            os.makedirs(glm_image_dir)
        shutil.copy(cwsig_mc_f, glm_image_dir)
        shutil.copy(oannot_mc_f, glm_image_dir)
        cwsig_mc_f_copy  = os.path.join(analysis_name, fsgd_type_contrast, cwsig_mc_f.replace(path_2contrast+'/', ''))
        oannot_mc_f_copy = os.path.join(analysis_name, fsgd_type_contrast, oannot_mc_f.replace(path_2contrast+'/', ''))

        sig_mc_count = len(self.sig_mc_data.keys())+1
        self.sig_mc_data[sig_mc_count] = {
                                'hemi'              : hemi,
                                'analysis_name'     : analysis_name,
                                'contrast'          : contrast,
                                'direction'         : direction,
                                'cwsig_mc_f'        : cwsig_mc_f_copy,
                                'oannot_mc_f'       : oannot_mc_f_copy}


class ClusterFile2CSV():

    def __init__(self,
                file_abspath,
                result_abspath):
        from stats.db_processing import Table
        self.contrasts = fs_definitions.GLMcontrasts['contrasts']
        self.get_explanations()

        self.col_4constrasts = "Contrast"
        self.header = ("ClusterNo",
                      "Max", "VtxMax", "Size(mm^2)", 
                      "TalX", "TalY", "TalZ",
                      "CWP", "CWPLow", "CWPHi",
                      "NVtxs", "WghtVtx",
                      "Annot", self.col_4constrasts, "Explanation")
        self.length_matrix = len(self.header)
        self.content = open(file_abspath, 'r').readlines()
        self.result_abspath = result_abspath
        self.tab = Table()
        self.ls_vals_2chk = self.contrasts.keys()
        self.run()

    def run(self):
        d = dict()
        i = 0

        while i < len(self.content):
            line = self.content[i].replace('\n','')
            if self.chk_if_vals_in_line(line):
                expl = self.content[i+1].replace('\n','').replace(';','.')
                d[i] = ['','','','','','','','','','','','','', line, expl,]
                i += 2
            else:
                line = self.clean_nans_from_list(line.split(' '))
                i += 1
                if len(line) != 0:
                    d[i] = line + ['','']
        self.save_2table(d)

    def save_2table(self, d):
        df = self.tab.create_df_from_dict(d).T
        column_names = {i[0]:i[1] for i in list(zip(df.columns, self.header))}
        df = df.rename(columns = column_names)
        df = df.set_index(df[self.col_4constrasts])
        df = df.drop(columns = [self.col_4constrasts])
        self.tab.save_df(df, self.result_abspath)

    def chk_if_vals_in_line(self, line):
        '''will use each value from self.ls_vals_2chk
            if present in the line:
            will return True and break
            else: return False
        '''
        exists     = False

        for val_2chk in self.ls_vals_2chk:
            if val_2chk in line:
                exists = True
                break
        return exists

    def clean_nans_from_list(self, ls):
        for i in ls[::-1]:
            if i == '':
                ls.remove(i)
        return ls

    def get_explanations(self):
        self.explanations = list()
        for key in self.contrasts:
            for file_name in self.contrasts[key]:
                self.explanations.append(self.contrasts[key][file_name][1])



def get_parameters(projects, FS_GLM_DIR):
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
        "-glm_dir", required=False,
        default=FS_GLM_DIR,
        help="path to GLM folder",
    )

    params = parser.parse_args()
    return params


def initiate_fs_from_sh(vars_local):
    """
    FreeSurfer needs to be initiated with source and export
    this functions tries to automate this
    """
    sh_file = os.path.join(vars_local["NIMB_PATHS"]["NIMB_tmp"], 'source_fs.sh')
    with open(sh_file, 'w') as f:
        f.write(vars_local["FREESURFER"]["export_FreeSurfer_cmd"]+'\n')
        f.write("export SUBJECTS_DIR="+vars_local["FREESURFER"]["SUBJECTS_DIR"]+'\n')
        f.write(vars_local["FREESURFER"]["source_FreeSurfer_cmd"]+'\n')
    os.system("chmod +x {}".format(sh_file))
    return ("source {}".format(sh_file))


if __name__ == "__main__":

    import argparse
    try:
        from pathlib import Path
    except ImportError as e:
        print('please install pathlib')
        sys.exit(e)

    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[2]
    sys.path.append(str(top))

    import subprocess
    from distribution.logger import Log
    from distribution.utilities import load_json, save_json
    from setup.get_vars import Get_Vars, SetProject
    from stats.db_processing import Table
    from processing.freesurfer import fs_definitions

    all_vars     = Get_Vars()
    projects     = all_vars.projects
    project_ids  = all_vars.project_ids

    NIMB_tmp     = all_vars.location_vars['local']['NIMB_PATHS']['NIMB_tmp']
    stats_vars   = SetProject(NIMB_tmp,
                                all_vars.stats_vars,
                                project_ids[0],
                                projects).stats
    FS_GLM_DIR   = stats_vars["STATS_PATHS"]["FS_GLM_dir"]

    params       = get_parameters(project_ids, FS_GLM_DIR)
    GLM_DIR      = params.glm_dir

    fs_start_cmd = initiate_fs_from_sh(all_vars.location_vars['local'])
    run_ok = True

    try:
        subprocess.run(['mri_info'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    except Exception as e:
        print(e)
        print(f'ERROR: please initiate freesurfer using the command: \n    {fs_start_cmd}')
        run_ok = False

    if run_ok:
        PerformGLM(all_vars, GLM_DIR, sig_fdr_thresh = 3.0)
