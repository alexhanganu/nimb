# 2020.09.02

'''
script uses output data from the freesurfer glm
uses freeview to create the images
and saves the images
'''

from os import system, makedirs, path
import linecache, sys
import argparse
from fs_definitions import hemi, FSGLMParams



class SaveGLMimages():

    def __init__(self, vars_local, stats_vars):
        self.PATHglm           = stats_vars["STATS_PATHS"]["FS_GLM_dir"]
        self.param             = FSGLMParams(self.PATHglm)
        print(self.PATHglm)
        self.PATHglm_glm       = self.param.PATHglm_glm
        self.hemispheres       = hemi
        self.mcz_sim_direction = self.param.mcz_sim_direction
        self.f_with_cmds       = path.join(self.PATHglm, 'fv.cmd')

        self.fdr_thresh        = 3.0 #p = 0.001
        self.mc_cache_thresh   = vars_local["FREESURFER"]["GLM_MCz_cache"]
        self.mc_img_thresh     = 1.3 #p = 0.05

    def run(self):
        if path.exists(self.param.sig_fdr_json):
            print('reading images for FDR significant results')
            self.read_fdr_images()
        if path.exists(self.param.sig_mc_json):
            print('reding images with MC-z corrected results')
            self.read_mc_images()
        elif path.exists(self.param.files_for_glm):
            print('reading images after FreeSurfer GLM analysis')
            self.read_glm_subdirs()

        # cleaning unnecessary files:
        if path.exists(self.f_with_cmds):
            system('rm {}'.format(self.f_with_cmds))
        files_2rm = ('surfer.log', '.xdebug_tksurfer')
        for file in files_2rm:
            if path.exists(file):
                system(f'rm {file}')

        # checking if file with clusters - transformed to CSV, if not - retrying
        cluster_stats      = path.join(self.param.PATHglm_results,'cluster_stats.log')
        cluster_stats_2csv = path.join(self.param.PATHglm_results,'cluster_stats.csv')
        if path.exists(cluster_stats) and not path.exists(cluster_stats_2csv):
            print(f'\ntransforming file {cluster_stats} to file: {cluster_stats_2csv}')
            from fs_glm_runglm import ClusterFile2CSV
            ClusterFile2CSV(cluster_stats, cluster_stats_2csv)


    def read_fdr_images(self):
        img = load_json(self.param.sig_fdr_json)
        for sig in img:
            analysis_name = img[sig]['analysis_name']
            glmdir = path.join(self.param.PATH_img, analysis_name)
            self.make_images_results_fdr(img[sig]['hemi'], glmdir, analysis_name, img[sig]['fsgd_type_contrast'])

    def read_mc_images(self):
        img = load_json(self.param.sig_mc_json)
        for sig in img:
            analysis_name      = img[sig]['analysis_name']
            contrast           = img[sig]['contrast']
            cwsig_mc_f = path.join(self.param.PATH_img, img[sig]['cwsig_mc_f'])
            oannot_mc_f = path.join(self.param.PATH_img, img[sig]['oannot_mc_f'])
            self.make_images_results_mc(img[sig]['hemi'],
                                        analysis_name,
                                        contrast,
                                        img[sig]['direction'],
                                        cwsig_mc_f,
                                        oannot_mc_f)
    def read_glm_subdirs(self):
        files_glm = load_json(self.param.files_for_glm)
        for fsgd_type in files_glm:
            for fsgd_file in files_glm[fsgd_type]['fsgd']:
                fsgd_f_unix = path.join(self.PATHglm, 'fsgd_unix', '{}_unix.fsgd'.format(fsgd_file.replace('.fsgd','')))
                for hemi in hemispheres:
                    for meas in vars_local["FREESURFER"]["GLM_measurements"]:
                        mcz_meas = self.param.GLM_MCz_meas_codes[meas]
                        for thresh in vars_local["FREESURFER"]["GLM_thresholds"]:
                            analysis_name = '{}.{}.{}.fwhm{}'.format(fsgd_file.replace('.fsgd',''), meas, hemi, str(thresh))
                            glmdir = path.join(self.PATHglm_glm, analysis_name)
                            for contrast_file in files_glm[fsgd_type]['mtx']:
                                fsgd_type_contrast = contrast_file.replace('.mtx','')
                                contrast = fsgd_type_contrast.replace(fsgd_type+'_','')
                                path_2contrast = path.join(glmdir, fsgd_type_contrast)
                                if self.check_maxvox(glmdir, fsgd_type_contrast):
                                    self.make_images_results_fdr(hemi, glmdir, analysis_name, fsgd_type_contrast)
                                for direction in self.mcz_sim_direction:
                                    mcz_header  = 'mc-z.{}.{}{}'.format(direction, mcz_meas, str(self.mc_cache_thresh))
                                    sum_mc_f    = path.join(path_2contrast,'{}.sig.cluster.summary'.format(mcz_header))
                                    cwsig_mc_f  = path.join(path_2contrast,'{}.sig.cluster.mgh'.format(mcz_header))
                                    oannot_mc_f = path.join(path_2contrast,'{}.sig.ocn.annot'.format(mcz_header))
                                    if self.check_mcz_summary(sum_mc_f):
                                        self.make_images_results_mc(hemi, analysis_name,
                                                                    contrast, direction, 
                                                                    cwsig_mc_f, oannot_mc_f)

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

    def make_images_results_mc(self, hemi, analysis_name,
                                    contrast, direction,
                                    cwsig_mc_f, oannot_mc_f):
        # must check the file exists:
        # G2V1_1_2_...thickness.rh.fwhm10/g2v1_group_x-var/mc-z.pos.th13.sig.ocn.annot
        # in some cases this file is missing and makes an error blocking the saving of images

        self.PATH_save_mc = path.join(self.PATHglm, 'results', 'mc')
        if not path.isdir(self.PATH_save_mc):
            makedirs(self.PATH_save_mc)
        file_lat_mc = path.join(self.PATH_save_mc, '{}_{}_lat_mc_{}{}.tiff'.format(
                                analysis_name, contrast, direction, str(self.mc_cache_thresh)))
        file_med_mc = path.join(self.PATH_save_mc, '{}_{}_med_mc_{}{}.tiff'.format(
                                analysis_name, contrast, direction, str(self.mc_cache_thresh)))
        fv_cmds = ['-ss {} -noquit'.format(file_lat_mc),
                    '-cam Azimuth 180',
                    '-ss {} -quit'.format(file_med_mc),
                  ]

        write_txt(self.f_with_cmds, fv_cmds, write_type = 'w')
        # f_with_cmds = path.join(self.PATHglm, 'fv.cmd')
        # with open(f_with_cmds,'w') as f:
        #     for line in fv_cmds:
        #         f.write(line+'\n')
        system('freeview -f $SUBJECTS_DIR/fsaverage/surf/{}.inflated:overlay={}:overlay_threshold={},5:annot={} -viewport 3d -layout 1 -cmd {}'.format(
                                                                                hemi, cwsig_mc_f, str(self.mc_img_thresh), oannot_mc_f, self.f_with_cmds))


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
                                                        'save_tiff '  +path.join(self.PATH_save_fdr, '{}_{}_{}_lat.tiff'.format(
                                                                            analysis_name, fsgd_type_contrast, str(self.fdr_thresh))),
                         'rotate_brain_y 180', 'redraw',
                                                        'save_tiff '  +path.join(self.PATH_save_fdr, '{}_{}_{}_med.tiff'.format(
                                                                            analysis_name, fsgd_type_contrast, str(self.fdr_thresh))),
                         'sclv_set_current_threshold_using_fdr 0.05 0', 
                                               'redraw','save_tiff '  +path.join(self.PATH_save_fdr, '{}_{}_fdr005_med.tiff'.format(
                                                                            analysis_name, fsgd_type_contrast)),
                         'rotate_brain_y 180', 'redraw',
                                                        'save_tiff '  +path.join(self.PATH_save_fdr, '{}_{}_fdr005_lat.tiff'.format(
                                                                            analysis_name, fsgd_type_contrast)), 
                         'exit']
        write_txt(self.f_with_cmds, tksurfer_cmds, write_type = 'w')
        # with open(self.f_with_cmds,'w') as f:
        #     for line in tksurfer_cmds:
        #         f.write(line+'\n')
        # print('tksurfer fsaverage {} inflated -overlay {} -fthresh {} -tcl {}'.format(
        #         hemi, path.join(glmdir, fsgd_type_contrast, sig_file), str(self.fdr_thresh), self.f_with_cmds))
        system('tksurfer fsaverage {} inflated -overlay {} -fthresh {} -tcl {}'.format(
                hemi, path.join(glmdir, fsgd_type_contrast, sig_file), str(self.fdr_thresh), self.f_with_cmds))
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


if __name__ == '__main__':

    from pathlib import Path
    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[2]
    sys.path.append(str(top))

    from setup.get_vars import Get_Vars, SetProject
    from distribution.utilities import load_json, write_txt
    getvars = Get_Vars()
    vars_local = getvars.location_vars['local']
    projects = getvars.projects
    params = get_parameters([i for i in projects.keys() if 'EXPLANATION' not in i and 'LOCATION' not in i])
    project = params.project
    vars_project = getvars.projects[project]
    NIMB_tmp = vars_local['NIMB_PATHS']['NIMB_tmp']
    fname_groups = projects[project]["fname_groups"]
    stats_vars = SetProject(NIMB_tmp, getvars.stats_vars, project, fname_groups).stats

    print('extracting glm images')
    SaveGLMimages(vars_local, stats_vars).run()
