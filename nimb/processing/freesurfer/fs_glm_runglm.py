#!/bin/python
# last update: 20201218


from os import system, listdir, makedirs, path
import linecache, sys
import json
import shutil
from fs_definitions import hemi, FSGLMParams


class PerformGLM():
    def __init__(self, PATHglm, FREESURFER_HOME, SUBJECTS_DIR,
                                measurements, thresholds,
                                GLM_MCz_thresh, sig_fdr_thresh):
        self.SUBJECTS_DIR          = SUBJECTS_DIR
        self.PATHglm               = PATHglm
        self.FREESURFER_HOME       = FREESURFER_HOME
        self.sig_fdr_thresh        = sig_fdr_thresh
        self.mc_cache_thresh       = GLM_MCz_thresh
        param                      = FSGLMParams(PATHglm)

        self.PATHglm_glm           = param.PATHglm_glm
        self.PATH_img              = param.PATH_img
        self.PATHglm_results       = param.PATHglm_results
        self.sig_fdr_json          = param.sig_fdr_json
        self.sig_mc_json           = param.sig_mc_json
        self.err_mris_preproc_file = param.err_mris_preproc_file
        self.mcz_sim_direction     = param.mcz_sim_direction
        self.hemispheres           = hemi
        self.GLM_sim_fwhm4csd      = param.GLM_sim_fwhm4csd
        self.GLM_MCz_meas_codes    = param.GLM_MCz_meas_codes
        self.cluster_stats         = path.join(self.PATHglm_results,'cluster_stats.log')
        self.sig_contrasts         = path.join(self.PATHglm_results,'sig_contrasts.log')

        for subdir in (self.PATHglm_glm, self.PATHglm_results, self.PATH_img):
            if not path.isdir(subdir): makedirs(subdir)
        self.sig_fdr_data = dict()
        self.sig_mc_data  = dict()
        self.err_preproc  = list()

        try:
            with open(param.subjects_per_group,'r') as jf:
                subjects_per_group = json.load(jf)
                print('subjects per group imported')
        except Exception as e:
            print(e)
            sys.exit('subjects per group is missing')
        try:
            with open(param.files_for_glm,'r') as jf:
                files_glm = json.load(jf)
                print('files for glm imported')
        except ImportError as e:
                print(e)
                sys.exit('files for glm is missing')

        print('subjects are located in: {}'.format(SUBJECTS_DIR))
        for group in subjects_per_group:
            for subject in subjects_per_group[group]:
                if subject not in listdir(SUBJECTS_DIR):
                    print(subject,' is missing in the freesurfer folder')
                    RUN = False
                else:
                    RUN = True
        if RUN:
            self.run_loop(files_glm, measurements, thresholds)
            if self.err_preproc:
                with open(self.err_mris_preproc_file, 'w') as jf:
                    json.dump(self.err_preproc, jf, indent = 4)
            if self.sig_fdr_data:
                with open(self.sig_fdr_json, 'w') as jf:
                    json.dump(self.sig_fdr_data, jf, indent = 4)
            if self.sig_mc_data:
                with open(self.sig_mc_json, 'w') as jf:
                    json.dump(self.sig_mc_data, jf, indent = 4)
            if path.exists(self.cluster_stats):
                self.cluster_log_to_csv()
            print('\n\nGLM DONE')
        else:
            sys.exit('some subjects are missing from the freesurfer folder')

    def run_loop(self, files_glm, measurements, thresholds):
        print('performing GLM analysis using mri_glmfit')
        for fsgd_type in files_glm:
            for fsgd_file in files_glm[fsgd_type]['fsgd']:
                fsgd_f_unix = path.join(self.PATHglm,'fsgd',fsgd_file.replace('.fsgd','')+'_unix.fsgd')
                for hemi in self.hemispheres:
                    for meas in measurements:
                        for thresh in thresholds:
                            self.RUN_GLM(fsgd_type, files_glm, fsgd_file,
                                         fsgd_f_unix, hemi, meas, thresh)


    def RUN_GLM(self, fsgd_type, files_glm, fsgd_file, fsgd_f_unix,
                      hemi, meas, thresh):
        glm_analysis = '{}.{}.fwhm{}'.format(meas, hemi, str(thresh))
        analysis_name = '{}.{}'.format(fsgd_file.replace('.fsgd',''), glm_analysis)
        glmdir = path.join(self.PATHglm_glm, analysis_name)
        mgh_f = path.join(glmdir, '{}.y.mgh'.format(glm_analysis))
        if not path.isdir(glmdir):
            self.run_mris_preproc(fsgd_f_unix, meas, thresh, hemi, mgh_f)
            if path.isfile(mgh_f):
                for contrast_file in files_glm[fsgd_type]['mtx']:
                    fsgd_type_contrast = contrast_file.replace('.mtx','')
                    contrast = fsgd_type_contrast.replace(fsgd_type+'_','')
                    contrast_f_ix = files_glm[fsgd_type]['mtx'].index(contrast_file)
                    explanation = files_glm[fsgd_type]['mtx_explanation'][contrast_f_ix]
                    for gd2mtx in files_glm[fsgd_type]['gd2mtx']:
                        self.run_mri_glmfit(mgh_f, fsgd_f_unix, gd2mtx, glmdir,
                                            hemi, contrast_file)
                        if self.check_maxvox(glmdir, fsgd_type_contrast):
                            self.log_contrasts_with_significance(analysis_name, fsgd_type_contrast)
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
        system('mris_preproc --fsgd {} --cache-in {}{}'.format(fsgd_file, f_cache, cmd_tail))

    def run_mri_glmfit(self, mgh_f, fsgd_file, gd2mtx, glmdir, hemi, contrast_file):
        cmd_header   = 'mri_glmfit --y {} --fsgd {} {}'.format(mgh_f, fsgd_file, gd2mtx)
        glmdir_cmd   = '--glmdir {}'.format(glmdir)
        path_2label  = path.join(self.SUBJECTS_DIR, 'fsaverage', 'label', hemi+'.aparc.label')
        surf_label   = '--surf fsaverage {} --label {}'.format(hemi, path_2label)
        contrast_cmd = '--C {}'.format(path.join(self.PATHglm, 'contrasts', contrast_file))
        cmd          = '{} {} {} {}'.format(cmd_header, glmdir_cmd, surf_label, contrast_cmd)
        system(cmd)


    def run_mri_surfcluster(self, glmdir, fsgd_type_contrast, hemi,
                                  contrast, analysis_name, meas, explanation):
        path_2contrast = path.join(glmdir, fsgd_type_contrast)
        mcz_meas = self.GLM_MCz_meas_codes[meas]
        for direction in self.mcz_sim_direction:
            mcz_header  = 'mc-z.{}.{}{}'.format(direction, mcz_meas, str(self.mc_cache_thresh))
            sig_f       = path.join(path_2contrast,'sig.mgh')
            cwsig_mc_f  = path.join(path_2contrast,'{}.sig.cluster.mgh'.format(mcz_header))
            vwsig_mc_f  = path.join(path_2contrast,'{}.sig.vertex.mgh'.format(mcz_header))
            sum_mc_f    = path.join(path_2contrast,'{}.sig.cluster.summary'.format(mcz_header))
            ocn_mc_f    = path.join(path_2contrast,'{}.sig.ocn.mgh'.format(mcz_header))
            oannot_mc_f = path.join(path_2contrast,'{}.sig.ocn.annot'.format(mcz_header))
            csdpdf_mc_f = path.join(path_2contrast,'{}.pdf.dat'.format(mcz_header))
            if meas != 'curv':
                path_2fsavg = path.join(self.FREESURFER_HOME, 'average', 'mult-comp-cor', 'fsaverage')
                fwhm = 'fwhm{}'.format(self.GLM_sim_fwhm4csd[meas][hemi])
                th   = 'th{}'.format(str(self.mc_cache_thresh))
                csd_mc_f = path.join(path_2fsavg, hemi, 'cortex', fwhm, direction, th, 'mc-z.csd')
                cmd_header = 'mri_surfcluster --in {} --csd {}'.format(sig_f, csd_mc_f)
                mask_cmd   = '--mask {}'.format(path.join(glmdir,'mask.mgh'))
                cmd_params = '--cwsig {} --vwsig {} --sum {} --ocn {} --oannot {} --csdpdf {}'.format(
                                cwsig_mc_f, vwsig_mc_f, sum_mc_f, ocn_mc_f, oannot_mc_f, csdpdf_mc_f)
                cmd_tail   = '--annot aparc --cwpvalthresh 0.05 --surf white'
                system('{} {} {} {}'.format(cmd_header, mask_cmd, cmd_params, cmd_tail))
                if self.check_mcz_summary(sum_mc_f):
                    self.cluster_stats_to_file(analysis_name, sum_mc_f, contrast, direction, explanation)
                    self.prepare_for_image_extraction_mc(hemi, analysis_name, path_2contrast,
                                                        fsgd_type_contrast, contrast, direction,
                                                        cwsig_mc_f, oannot_mc_f)
            else:
                cmd_header = 'mri_glmfit-sim --glmdir {}'.format(path.join(glmdir, fsgd_type_contrast))
                cmd_cache  = '--cache {} {}'.format(str(self.mc_cache_thresh), direction)
                system('{} {} --cwp 0.05 --2spaces'.format(cmd_header, cmd_cache))
                if self.check_mcz_summary(sum_mc_f):
                    self.cluster_stats_to_file(analysis_name, sum_mc_f, contrast, direction, explanation)

    def check_maxvox(self, glmdir, fsgd_type_contrast):
        res = False
        maxvox = path.join(glmdir, fsgd_type_contrast, 'maxvox.dat')
        if path.exists(maxvox):
            val = [i.strip() for i in open(maxvox).readlines()][0].split()[0]
            if float(val) > self.sig_fdr_thresh or float(val) < -self.sig_fdr_thresh:
                res = True
        return res

    def check_mcz_summary(self, file):
        if len(linecache.getline(file, 42).strip('\n')) > 0:
            return True
        else:
            return False


    def cluster_stats_to_file(self, analysis_name, sum_mc_f, contrast,
                                    direction, explanation):
        file = self.cluster_stats
        if not path.isfile(file):
            open(file,'w').close()
        ls = list()
        for line in list(open(sum_mc_f))[41:sum(1 for line in open(sum_mc_f))]:
            ls.append(line.rstrip())
        with open(file, 'a') as f:
            f.write('{}_{}_{}\n'.format(analysis_name, contrast, direction))
            f.write(explanation+'\n')
            for value in ls:
                f.write(value+'\n')
            f.write('\n')

    def log_contrasts_with_significance(self, analysis_name, fsgd_type_contrast):
        file = self.sig_contrasts
        if not path.isfile(file):
            open(file,'w').close()
        with open(file, 'a') as f:
            f.write('{}/{}\n'.format(analysis_name, fsgd_type_contrast))

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
        glm_image_dir = path.join(self.PATH_img, analysis_name, fsgd_type_contrast)
        if not path.exists(glm_image_dir):
            makedirs(glm_image_dir)
        sig_file = 'sig.mgh'
        shutil.copy(path.join(glmdir, fsgd_type_contrast, sig_file), glm_image_dir)
        
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
        glm_image_dir = path.join(self.PATH_img, analysis_name, fsgd_type_contrast)
        if not path.exists(glm_image_dir):
            makedirs(glm_image_dir)
        shutil.copy(cwsig_mc_f, glm_image_dir)
        shutil.copy(oannot_mc_f, glm_image_dir)
        cwsig_mc_f_copy  = path.join(analysis_name, fsgd_type_contrast, cwsig_mc_f.replace(path_2contrast+'/', ''))
        oannot_mc_f_copy = path.join(analysis_name, fsgd_type_contrast, oannot_mc_f.replace(path_2contrast+'/', ''))

        sig_mc_count = len(self.sig_mc_data.keys())+1
        self.sig_mc_data[sig_mc_count] = {
                                'hemi'              : hemi,
                                'analysis_name'     : analysis_name,
                                'contrast'          : contrast,
                                'direction'         : direction,
                                'cwsig_mc_f'        : cwsig_mc_f_copy,
                                'oannot_mc_f'       : oannot_mc_f_copy}

    def chk_contrast(self, line):
        '''checks if contrast is present in the str(line)
        must import constrast from fs_definitions
        '''
        exists = False
        for contrast in contrasts.keys():
            if contrast in line:
                exists = True
                break
        return exists

    def cluster_log_to_csv(self):
        '''transforming the cluster_stats.log file into
            cluster_stats.csv
        '''
        # must add header
        # send contrasts name (e.g., g2v1..) to one cell
        # send contrast comments to additional external cell, for quick removal
        # split all values in different cells
        print("working on transforming cluster log to csv")
        # content = open(self.cluster_stats, 'r').readlines()


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
    sh_file = path.join(vars_local["NIMB_PATHS"]["NIMB_tmp"], 'source_fs.sh')
    with open(sh_file, 'w') as f:
        f.write(vars_local["FREESURFER"]["export_FreeSurfer_cmd"]+'\n')
        f.write("export SUBJECTS_DIR="+vars_local["FREESURFER"]["FS_SUBJECTS_DIR"]+'\n')
        f.write(vars_local["FREESURFER"]["source_FreeSurfer_cmd"]+'\n')
    system("chmod +x {}".format(sh_file))
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
    from setup.get_vars import Get_Vars, SetProject
    getvars      = Get_Vars()
    vars_local   = getvars.location_vars['local']
    projects     = getvars.projects
    all_projects = [i for i in projects.keys() if 'EXPLANATION' not in i and 'LOCATION' not in i]
    NIMB_tmp     = vars_local['NIMB_PATHS']['NIMB_tmp']
    stats_vars   = SetProject(NIMB_tmp,
                                getvars.stats_vars,
                                all_projects[0],
                                projects[all_projects[0]]['fname_groups']).stats
    FS_GLM_DIR   = stats_vars["STATS_PATHS"]["FS_GLM_dir"]

    params       = get_parameters(all_projects, FS_GLM_DIR)
    GLM_DIR      = params.glm_dir

    fs_start_cmd = initiate_fs_from_sh(vars_local)
    sig_fdr_thresh= 3.0 #p = 0.001; for p=0.05 use value 1.3, but it should be used ONLY for visualisation.

    print('please initiate freesurfer using the command: \n    {}'.format(fs_start_cmd))
    try:
        subprocess.run(['mri_info'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    except Exception as e:
        print(e)
        print('please initiate freesurfer using the command: \n    {}'.format(fs_start_cmd))

    PerformGLM(GLM_DIR,
               vars_local["FREESURFER"]["FREESURFER_HOME"],
               vars_local["FREESURFER"]["FS_SUBJECTS_DIR"],
               vars_local["FREESURFER"]["GLM_measurements"],
               vars_local["FREESURFER"]["GLM_thresholds"],
               vars_local["FREESURFER"]["GLM_MCz_cache"],
               sig_fdr_thresh)
