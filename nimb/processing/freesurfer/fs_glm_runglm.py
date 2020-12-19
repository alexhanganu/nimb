#!/bin/python
# last update: 20201218


from os import system, listdir, makedirs, path
import linecache, sys
import json


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

        print('subjects are located in: {}'.format(SUBJECTS_DIR))
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
        self.err_preproc = list()

        hemispheres = ['lh','rh']
        for contrast_type in files_for_glm:
            for fsgd_file in files_for_glm[contrast_type]['fsgd']:
                fsgd_f_unix = path.join(self.PATHglm,'fsgd',fsgd_file.replace('.fsgd','')+'_unix.fsgd')
                for hemi in hemispheres:
                    for meas in measurements:
                        for thresh in thresholds:
                            glm_analysis = '{}.{}.fwhm{}'.format(meas, hemi, str(thresh))
                            analysis_name = '{}.{}'.format(fsgd_file.replace('.fsgd',''), glm_analysis)
                            glmdir = path.join(self.PATHglm_glm, analysis_name)
                            mgh_f = path.join(glmdir, '{}.y.mgh'.format(glm_analysis))
                            if not path.isdir(glmdir):
                                self.run_mris_preproc(fsgd_f_unix, meas, thresh, hemi, mgh_f)
                                if path.isfile(mgh_f):
                                    for contrast in files_for_glm[contrast_type]['mtx']:
                                        explanation = files_for_glm[contrast_type]['mtx_explanation'][files_for_glm[contrast_type]['mtx'].index(contrast)]
                                        for gd2mtx in files_for_glm[contrast_type]['gd2mtx']:
                                            self.run_mri_glmfit(mgh_f, fsgd_f_unix, gd2mtx, glmdir, hemi, contrast)
                                            if self.check_maxvox(glmdir, contrast.replace('.mtx','')):
                                                self.log_contrasts_with_significance(glmdir, contrast.replace('.mtx',''))
                                            self.run_mri_surfcluster(glmdir, contrast.replace('.mtx',''), hemi, contrast_type, analysis_name, meas, cache, explanation)
                                else:
                                    print('{} not created; ERROR in mris_preproc'.format(mgh_f))
                                    self.err_preproc.append(mgh_f)
        if self.err_preproc:
            file = path.join(self.PATHglm_results,'error_mris_preproc.json')
            with open(file, 'w') as jf:
                json.dump(self.err_preproc, jf, indent = 4)

    def run_mris_preproc(self, fsgd_file, meas, thresh, hemi, mgh_f):
        system('mris_preproc --fsgd {} --cache-in {}.fwhm{}.fsaverage --target fsaverage --hemi {} --out {}'.format(fsgd_file, meas, str(thresh), hemi, mgh_f))
        # system('mris_preproc --fsgd '+fsgd_f_unix+' --cache-in '+meas+'.fwhm'+str(thresh)+'.fsaverage --target fsaverage --hemi '+hemi+' --out '+mgh_f)

    def run_mri_glmfit(self, mgh_f, fsgd_file, gd2mtx, glmdir, hemi, contrast):
        # system('mri_glmfit --y '+mgh_f+' --fsgd '+fsgd_f_unix+' '+gd2mtx+' --glmdir '+glmdir+' --surf fsaverage '+hemi+' --label '+path.join(self.SUBJECTS_DIR,'fsaverage','label',hemi+'.aparc.label')+' --C '+path.join(self.PATHglm,'contrasts',contrast))
        label_cmd    = ' --label {}'.format(path.join(self.SUBJECTS_DIR, 'fsaverage', 'label', hemi+'.aparc.label'))
        contrast_cmd = ' --C {}'.format(path.join(self.PATHglm, 'contrasts', contrast))
        cmd          = 'mri_glmfit --y {} --fsgd {} {} --glmdir {} --surf fsaverage {}{}{}'.format(mgh_f, fsgd_file, gd2mtx, glmdir, hemi, label_cmd, contrast_cmd)
        system(cmd)


    def run_mri_surfcluster(self, glmdir, contrast_name, hemi, contrast_type, analysis_name, meas, cache, explanation):
        sim_direction = ['pos', 'neg',]
        contrastdir = path.join(glmdir, contrast_name)
        GLM_sim_fwhm4csd = {'thickness': {'lh': '15','rh': '15'},'area': {'lh': '24','rh': '25'},'volume': {'lh': '16','rh': '16'},}
        GLM_measurements = {'thickness':'th','area':'ar','volume':'vol'}
        for direction in sim_direction:
            contrast_dir = '{}.{}{}'.format(direction, GLM_measurements[meas], str(cache))
            sig_f = path.join(contrastdir,'sig.mgh')
            cwsig_mc_f = path.join(contrastdir,'mc-z.{}.sig.cluster.mgh'.format(contrast_dir))
            vwsig_mc_f = path.join(contrastdir,'mc-z.{}.sig.vertex.mgh'.format(contrast_dir))
            sum_mc_f = path.join(contrastdir,'mc-z.{}.sig.cluster.summary'.format(contrast_dir))
            ocn_mc_f = path.join(contrastdir,'mc-z.{}.sig.ocn.mgh'.format(contrast_dir))
            oannot_mc_f = path.join(contrastdir,'mc-z.{}.sig.ocn.annot'.format(contrast_dir))
            csdpdf_mc_f = path.join(contrastdir,'mc-z.{}.pdf.dat'.format(contrast_dir))
            if meas != 'curv':
                csd_mc_f = path.join(self.FREESURFER_HOME, 'average', 'mult-comp-cor', 'fsaverage', hemi, 'cortex', 'fwhm'+GLM_sim_fwhm4csd[meas][hemi],direction, 'th'+str(cache), 'mc-z.csd')
                system('mri_surfcluster --in {} --csd {} --mask {} --cwsig {} --vwsig {} --sum {} --ocn {} --oannot {} --csdpdf {} --annot aparc --cwpvalthresh 0.05 --surf white'.format(sig_f, csd_mc_f, path.join(glmdir,'mask.mgh'), cwsig_mc_f, vwsig_mc_f, sum_mc_f, ocn_mc_f, oannot_mc_f, csdpdf_mc_f))                                        
                if self.check_mcz_summary(sum_mc_f):
                    self.cluster_stats_to_file(analysis_name, sum_mc_f, contrast_name.replace(contrast_type+'_',''), direction, explanation)
            else:
                system('mri_glmfit-sim --glmdir {} --cache {} {} --cwp 0.05 --2spaces'.format(path.join(glmdir, contrast_name), str(cache), direction))

    def check_maxvox(self, glmdir, contrast_name):
        res = False
        maxvox = path.join(glmdir, contrast_name, 'maxvox.dat')
        if path.exists(maxvox):
            val = [i.strip() for i in open(maxvox).readlines()][0].split()[0]
            if float(val) > 3.0 or float(val) < -3.0:
                res = True
        return res

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




def get_parameters(projects, vars_local):
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

    parser.add_argument(
        "-subjects_dir", required=False,
        default=vars_local["FREESURFER"]["FS_SUBJECTS_DIR"],
        choices = [vars_local["FREESURFER"]["FS_SUBJECTS_DIR"], vars_local["NIMB_PATHS"]["NIMB_PROCESSED_FS"]],
        help="path to SUBJECTS_DIR if different from default",
    )

    parser.add_argument(
        "-glm_file_path", required=False,
        default='none',
        help="path to SUBJECTS_DIR if different from default",
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
    params       = get_parameters([i for i in projects.keys() if 'EXPLANATION' not in i and 'LOCATION' not in i], vars_local)
    SUBJECTS_DIR = params.subjects_dir
    stats_vars   = SetProject(vars_local['NIMB_PATHS']['NIMB_tmp'], getvars.stats_vars, params.project).stats
    fs_start_cmd = initiate_fs_from_sh(vars_local)

    print('please initiate freesurfer using the command: \n    {}'.format(fs_start_cmd))
    try:
        subprocess.run(['mri_info'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    except Exception as e:
        print(e)
        print('please initiate freesurfer using the command: \n    {}'.format(fs_start_cmd))

    PerformGLM(stats_vars["STATS_PATHS"]["FS_GLM_dir"],
               vars_local["FREESURFER"]["FREESURFER_HOME"],
               SUBJECTS_DIR,
               vars_local["FREESURFER"]["GLM_measurements"],
               vars_local["FREESURFER"]["GLM_thresholds"],
               vars_local["FREESURFER"]["GLM_MCz_cache"])

