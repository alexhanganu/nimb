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

    def __init__(self, all_vars):

        project = all_vars.params.project
        self.vars_fs           = all_vars.location_vars['local']["FREESURFER"]
        self.PATHglm           = all_vars.projects[project]["STATS_PATHS"]["FS_GLM_dir"]
        self.param             = FSGLMParams(self.PATHglm)
        self.PATHglm_glm       = self.param.PATHglm_glm
        self.hemispheres       = hemi
        self.mcz_sim_direction = self.param.mcz_sim_direction
        self.measures          = self.vars_fs["GLM_measurements"]
        self.threshs           = self.vars_fs["GLM_thresholds"]
        self.f_with_cmds       = path.join(self.PATHglm, 'fv.cmd')

        self.fdr_thresh        = 3.0 #p = 0.001
        self.mc_cache_thresh   = self.vars_fs["GLM_MCz_cache"]
        self.mc_img_thresh     = 1.3 #p = 0.05
        print('    extracting glm images to: ', self.PATHglm)


    def run(self):
        if path.exists(self.param.sig_fdr_json):
            print('    reading images for FDR significant results')
            self.read_fdr_images()
        else:
            print('    folder with glm results is missing at:', self.param.sig_fdr_json)
        if path.exists(self.param.sig_mc_json):
            print('    reading images with MC-z corrected results')
            self.read_mc_images()
        else:
            print('    folder with glm results is missing at:', self.param.sig_mc_json)

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
            print(f'\n    transforming file {cluster_stats} to file: {cluster_stats_2csv}')
            from fs_glm_runglm import ClusterFile2CSV
            ClusterFile2CSV(cluster_stats, cluster_stats_2csv)


    def read_fdr_images(self):
        img = load_json(self.param.sig_fdr_json)
        ls_img = list(img.keys())
        for sig in img:
            analysis_name = img[sig]['analysis_name']
            glmdir = path.join(self.param.PATH_img, analysis_name)
            self.make_images_results_fdr(img[sig]['hemi'], glmdir, analysis_name, img[sig]['fsgd_type_contrast'])
            print(f"    \n\n\n{len(ls_img[ls_img.index(sig):])} images LEFT for extraction")


    def read_mc_images(self):
        img = load_json(self.param.sig_mc_json)
        ls_img = list(img.keys())
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
            print(f"    \n\n\n{len(ls_img[ls_img.index(sig):])} images LEFT for extraction")


    def make_images_results_mc(self, hemi, analysis_name,
                                    contrast, direction,
                                    cwsig_mc_f, oannot_mc_f):
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
        print('    !!!! Attention, tksurfer is deprecated in FS7.3. Try tksurferfv')
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

    project_ids = Get_Vars().get_projects_ids()

    all_vars   = Get_Vars()
    params     = get_parameters(project_ids)
    all_vars    = Get_Vars(params)

    SaveGLMimages(all_vars).run()
