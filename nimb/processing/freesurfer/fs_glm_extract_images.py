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

    def __init__(self, vars_local, stats_vars):
        self.PATHglm         = stats_vars["STATS_PATHS"]["FS_GLM_dir"]
        self.PATHglm_glm     = path.join(self.PATHglm,'glm')
        self.fdr_thresh      = 3.0 #p = 0.001
        self.mc_cache_thresh = vars_local["FREESURFER"]["GLM_MCz_cache"]
        self.mc_img_thresh   = 1.3 #p = 0.05

        hemispheres = ['lh','rh']
        sim_direction = ['pos', 'neg',]

        with open(path.join(self.PATHglm, "files_for_glm.json"), 'rt') as f:
            files_glm = json.load(f)

        for fsgd_type in files_glm:
            for fsgd_file in files_glm[fsgd_type]['fsgd']:
                fsgd_f_unix = path.join(self.PATHglm, 'fsgd_unix', fsgd_file.replace('.fsgd','')+'_unix.fsgd')
                for hemi in hemispheres:
                    for meas in vars_local["FREESURFER"]["GLM_measurements"]:
                        for thresh in vars_local["FREESURFER"]["GLM_thresholds"]:
                            analysis_name = fsgd_file.replace('.fsgd','')+'.'+meas+'.'+hemi+'.fwhm'+str(thresh)
                            glmdir = path.join(self.PATHglm_glm, analysis_name)
                            for contrast_file in files_glm[fsgd_type]['mtx']:
                                fsgd_type_contrast = contrast_file.replace('.mtx','')
                                contrast = fsgd_type_contrast.replace(fsgd_type+'_','')
                                dir_glm_fsgd_type_contrast = path.join(glmdir, fsgd_type_contrast)
                                if self.check_maxvox(glmdir, fsgd_type_contrast):
                                    self.make_images_results_fdr(hemi, glmdir, analysis_name, fsgd_type_contrast)
                                for direction in sim_direction:
                                    sum_mc_f = path.join(dir_glm_fsgd_type_contrast, 'mc-z.{}.th{}.sig.cluster.summary'.format(direction, str(self.mc_cache_thresh)))
                                    if self.check_mcz_summary(sum_mc_f):
                                        self.make_images_results_mc(hemi,
                                                                    analysis_name,
                                                                    dir_glm_fsgd_type_contrast,
                                                                    contrast,
                                                                    direction)

    def check_maxvox(self, glmdir, fsgd_type_contrast):
        val = [i.strip() for i in open(path.join(glmdir, fsgd_type_contrast, 'maxvox.dat')).readlines()][0].split()[0]
        if float(val) > 3.0 or float(val) < -3.0:
            return True
        else:
            return False


    def check_mcz_summary(self, file):
        if len(linecache.getline(file, 42).strip('\n')) > 0:
            return True
        else:
            return False

    def make_images_results_mc(self, hemi, analysis_name, dir_glm_fsgd_type_contrast, contrast, direction):
        self.PATH_save_mc = path.join(self.PATHglm, 'results', 'mc')
        if not path.isdir(self.PATH_save_mc):
            makedirs(self.PATH_save_mc)
        file_lat_mc = path.join(self.PATH_save_mc, '{}_{}_lat_mc_{}{}.tiff'.format(analysis_name, contrast, direction, str(self.mc_cache_thresh)))
        file_med_mc = path.join(self.PATH_save_mc, '{}_{}_med_mc_{}{}.tiff'.format(analysis_name, contrast, direction, str(self.mc_cache_thresh)))
        fv_cmds = ['-ss {} -noquit'.format(file_lat_mc),
                    '-cam Azimuth 180',
                    '-ss {} -quit'.format(file_med_mc),
                  ]
        f_with_cmds = path.join(self.PATHglm, 'fv.cmd')
        with open(f_with_cmds,'w') as f:
            for line in fv_cmds:
                f.write(line+'\n')
        cwsig_mc_f  = path.join(dir_glm_fsgd_type_contrast, 'mc-z.{}.th{}.sig.cluster.mgh'.format(direction, str(self.mc_cache_thresh)))
        oannot_mc_f = path.join(dir_glm_fsgd_type_contrast, 'mc-z.{}.th{}.sig.ocn.annot'.format(direction, str(self.mc_cache_thresh)))

        system('freeview -f $SUBJECTS_DIR/fsaverage/surf/{}.inflated:overlay={}:overlay_threshold={},5:annot={} -viewport 3d -layout 1 -cmd {}'.format(hemi, cwsig_mc_f, str(self.mc_img_thresh), oannot_mc_f, f_with_cmds))


    def make_images_results_fdr(self, hemi, glmdir, analysis_name, fsgd_type_contrast):
        sig_file   = 'sig.mgh'
        thresh = self.fdr_thresh
        self.PATH_save_fdr = path.join(self.PATHglm, 'results', 'fdr')
        if not path.isdir(self.PATH_save_fdr):
            makedirs(self.PATH_save_fdr)

#        tksurfer_cmds = ['set colscalebarflag 1', 'set scalebarflag 1', 'save_tiff '+self.PATH_save_fdr+'/'+fsgd_type_contrast+'_'+str(3.0)+'_lat.tiff',
#         'rotate_brain_y 180', 'redraw', 'save_tiff '+self.PATH_save_fdr+'/'+fsgd_type_contrast+'_'+str(3.0)+'_med.tiff',
#         'sclv_set_current_threshold_using_fdr 0.05 0', 'redraw', 'save_tiff '+self.PATH_save_fdr+'/'+fsgd_type_contrast+'_fdr_med.tiff',
#         'rotate_brain_y 180', 'redraw', 'save_tiff '+self.PATH_save_fdr+'/'+fsgd_type_contrast+'_fdr_lat.tiff','exit']

        tksurfer_cmds = ['set colscalebarflag 1', 'set scalebarflag 1', 
                                                        'save_tiff '  +path.join(self.PATH_save_fdr, '{}_{}_{}_lat.tiff'.format(analysis_name, fsgd_type_contrast, str(self.fdr_thresh))),
                         'rotate_brain_y 180', 'redraw',
                                                        'save_tiff '  +path.join(self.PATH_save_fdr, '{}_{}_{}_med.tiff'.format(analysis_name, fsgd_type_contrast, str(self.fdr_thresh))),
                         'sclv_set_current_threshold_using_fdr 0.05 0', 
                                               'redraw','save_tiff '  +path.join(self.PATH_save_fdr, '{}_{}_fdr005_med.tiff'.format(analysis_name, fsgd_type_contrast)),
                         'rotate_brain_y 180', 'redraw',
                                                        'save_tiff '  +path.join(self.PATH_save_fdr, '{}_{}_fdr005_lat.tiff'.format(analysis_name, fsgd_type_contrast)), 
                         'exit']
        f_with_tkcmds = path.join(self.PATHglm, 'tkcmd.cmd')
        with open(f_with_tkcmds,'w') as f:
            for line in tksurfer_cmds:
                f.write(line+'\n')
        print('tksurfer fsaverage {} inflated -overlay {} -fthresh {} -tcl {}'.format(hemi, path.join(glmdir, fsgd_type_contrast, sig_file), str(self.fdr_thresh), f_with_tkcmds))
        system('tksurfer fsaverage {} inflated -overlay {} -fthresh {} -tcl {}'.format(hemi, path.join(glmdir, fsgd_type_contrast, sig_file), str(self.fdr_thresh), f_with_tkcmds))
#        system('tksurfer fsaverage '+hemi+' inflated -overlay '+path.join(glmdir, fsgd_type_contrast, sig_file)+' -fthresh '+str(self.fdr_thresh)+' -tcl '+f_with_tkcmds)




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
    """
    FreeSurfer needs to be initiated with source and export
    this functions tries to automate this
    """
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
    params = get_parameters([i for i in projects.keys() if 'EXPLANATION' not in i and 'LOCATION' not in i])
    vars_project = getvars.projects[params.project]
    SetProject(vars_local['NIMB_PATHS']['NIMB_tmp'], getvars.stats_vars, params.project)
    fs_start_cmd = initiate_fs_from_sh(vars_local)

    try:
        subprocess.run(['mri_info'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    except Exception as e:
        print(e)
        print('please initiate freesurfer using the command: \n    {}'.format(fs_start_cmd))

    print('extracting glm images')
    SaveGLMimages(vars_local, getvars.stats_vars)
