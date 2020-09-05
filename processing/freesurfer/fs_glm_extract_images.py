# 2020.09.02

'''
script uses output data from the freesurfer glm
uses freeview to create the images
and saves the images
'''

from os import system, listdir, makedirs, path, remove, getcwd, chdir
import shutil, linecache, sys, json
import argparse
import subprocess

try:
    import pandas as pd
    import xlrd
    from pathlib import Path
except ImportError as e:
    sys.exit(e)


class SaveGLMimages():

    def __init__(self, vars_local):
        self.cache = vars_local["FREESURFER"]["GLM_MCz_cache"]
        self.PATHglm = vars_local["STATS_PATHS"]["FS_GLM_dir"]
        self.PATHglm_glm = path.join(self.PATHglm,'glm/')

        hemispheres = ['lh','rh']
        sim_direction = ['pos', 'neg',]

        with open(path.join(self.PATHglm, "files_for_glm.json"), 'rt') as f:
            files_for_glm = json.load(f)

        for contrast_type in files_for_glm:
            for fsgd_file in files_for_glm[contrast_type]['fsgd']:
                fsgd_f_unix = path.join(self.PATHglm, 'fsgd_unix', fsgd_file.replace('.fsgd','')+'_unix.fsgd')
                for hemi in hemispheres:
                    for meas in vars_local["FREESURFER"]["GLM_measurements"]:
                        for thresh in vars_local["FREESURFER"]["GLM_thresholds"]:
                            analysis_name = fsgd_file.replace('.fsgd','')+'.'+meas+'.'+hemi+'.fwhm'+str(thresh)
                            glmdir = path.join(self.PATHglm_glm, analysis_name)
                            for contrast in files_for_glm[contrast_type]['mtx']:
                                contrast_name = contrast.replace('.mtx','')
                                contrastdir = path.join(glmdir, contrast_name)
                                if self.check_maxvox(glmdir, contrast_name):
                                    self.make_images_results_fdr(hemi, glmdir, contrast_name, 'sig.mgh', 3.0)
                                for direction in sim_direction:
                                    sum_mc_f = path.join(contrastdir, 'mc-z.'+direction+'.th'+str(self.cache)+'.sig.cluster.summary')
                                    cwsig_mc_f = path.join(contrastdir, 'mc-z.'+direction+'.th'+str(self.cache)+'.sig.cluster.mgh')
                                    oannot_mc_f = path.join(contrastdir, 'mc-z.'+direction+'.th'+str(self.cache)+'.sig.ocn.annot')
                                    if self.check_mcz_summary(sum_mc_f):
                                        self.make_images_results_mc(hemi,
                                                                    analysis_name,
                                                                    contrast_name.replace(contrast_type+'_',''),
                                                                    direction,
                                                                    cwsig_mc_f,
                                                                    oannot_mc_f, str(self.cache), 1.3)

    def check_maxvox(self, glmdir, contrast_name):
        val = [i.strip() for i in open(path.join(glmdir, contrast_name, 'maxvox.dat')).readlines()][0].split()[0]
        if float(val) > 3.0 or float(val) < -3.0:
            return True
        else:
            return False


    def check_mcz_summary(self, file):
        if len(linecache.getline(file, 42).strip('\n')) > 0:
            return True
        else:
            return False

    def make_images_results_mc(self, hemi, analysis_name, contrast, direction, cwsig_mc_f, oannot_mc_f, cache, thresh):
        self.PATH_save_mc = path.join(self.PATHglm, 'results', 'mc')
        if not path.isdir(self.PATH_save_mc):
            makedirs(self.PATH_save_mc)
        fv_cmds = ['-ss '+path.join(self.PATH_save_mc, analysis_name+'_'+contrast+'_lat_mc_'+direction+cache+'.tiff -noquit'),
                    '-cam Azimuth 180',
                    '-ss '+path.join(self.PATH_save_mc, analysis_name+'_'+contrast+'_med_mc_'+direction+cache+'.tiff -quit'),]
        f_with_cmds = path.join(self.PATHglm, 'fv.cmd')
        with open(f_with_cmds,'w') as f:
            for line in fv_cmds:
                f.write(line+'\n')

        system('freeview -f $SUBJECTS_DIR/fsaverage/surf/'+hemi+'.inflated:overlay='+cwsig_mc_f+':overlay_threshold='+str(thresh)+',5:annot='+oannot_mc_f+' -viewport 3d -layout 1 -cmd '+f_with_cmds)


    def make_images_results_fdr(self, hemi, glmdir, contrast_name, file, thresh):
        self.PATH_save_fdr = path.join(self.PATHglm, 'results', 'fdr')
        if not path.isdir(self.PATH_save_fdr):
            makedirs(self.PATH_save_fdr)

#        tksurfer_cmds = ['set colscalebarflag 1', 'set scalebarflag 1', 'save_tiff '+self.PATH_save_fdr+'/'+contrast_name+'_'+str(3.0)+'_lat.tiff',
#         'rotate_brain_y 180', 'redraw', 'save_tiff '+self.PATH_save_fdr+'/'+contrast_name+'_'+str(3.0)+'_med.tiff',
#         'sclv_set_current_threshold_using_fdr 0.05 0', 'redraw', 'save_tiff '+self.PATH_save_fdr+'/'+contrast_name+'_fdr_med.tiff',
#         'rotate_brain_y 180', 'redraw', 'save_tiff '+self.PATH_save_fdr+'/'+contrast_name+'_fdr_lat.tiff','exit']

        tksurfer_cmds = ['set colscalebarflag 1', 'set scalebarflag 1', 'save_tiff '+path.join(self.PATH_save_fdr, contrast_name+'_'+str(3.0)+'_lat.tiff'),
                         'rotate_brain_y 180', 'redraw', 'save_tiff '+path.join(self.PATH_save_fdr, contrast_name+'_'+str(3.0)+'_med.tiff'),
                         'sclv_set_current_threshold_using_fdr 0.05 0', 'redraw', 'save_tiff '+path.join(self.PATH_save_fdr, contrast_name+'_fdr_med.tiff'),
                         'rotate_brain_y 180', 'redraw', 'save_tiff '+path.join(self.PATH_save_fdr, contrast_name+'_fdr_lat.tiff'), 'exit']
        f_with_tkcmds = path.join(self.PATHglm, 'tkcmd.cmd')
        with open(f_with_tkcmds,'w') as f:
            for line in tksurfer_cmds:
                f.write(line+'\n')
        print('tksurfer fsaverage '+hemi+' inflated -overlay '+path.join(glmdir, contrast_name, file+' -fthresh '+str(thresh)+' -tcl '+f_with_tkcmds))
        system('tksurfer fsaverage '+hemi+' inflated -overlay '+path.join(glmdir, contrast_name, file+' -fthresh '+str(thresh)+' -tcl '+f_with_tkcmds))




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
    system("./{}".format(sh_file))
    return ("source {}".format(sh_file))


if __name__ == '__main__':


    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[2]
    sys.path.append(str(top))

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

    print('extracting glm images')
    SaveGLMimages(vars_local)
