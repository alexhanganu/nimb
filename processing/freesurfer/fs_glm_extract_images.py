# 2020.07.07

'''
script uses output data from the freesurfer glm
uses freeview to create the images
and saves the images
'''



from os import system, listdir, makedirs, path, getcwd, chdir, remove
import shutil, linecache, sys



class SaveGLMimages():

    def __init__(self, GLM_dir, files_for_glm, measurements, thresholds, cache):
        self.PATHglm = GLM_dir
        self.PATHglm_glm = path.join(self.PATHglm,'glm/')

        hemispheres = ['lh','rh']
        sim_direction = ['pos', 'neg',]

        for contrast_type in files_for_glm:
            for fsgd_file in files_for_glm[contrast_type]['fsgd']:
                fsgd_f_unix = path.join(self.PATHglm,'fsgd_unix',fsgd_file.replace('.fsgd','')+'_unix.fsgd')
                for hemi in hemispheres:
                    for meas in measurements:
                        for thresh in thresholds:
                            analysis_name = fsgd_file.replace('.fsgd','')+'.'+meas+'.'+hemi+'.fwhm'+str(thresh)
                            glmdir = path.join(self.PATHglm_glm,analysis_name)
                            contrastdir = glmdir+'/'+contrast_name+'/'

                            for contrast in files_for_glm[contrast_type]['mtx']:
                                if self.check_maxvox(glmdir, contrast.replace('.mtx','')):
                                    self.make_images_results_fdr(hemi, glmdir, contrast.replace('.mtx',''), 'sig.mgh', 3.0)
                                for direction in sim_direction:
                                    sum_mc_f = contrastdir+'mc-z.'+direction+'.th'+str(cache)+'.sig.cluster.summary'
                                    cwsig_mc_f = contrastdir+'mc-z.'+direction+'.th'+str(cache)+'.sig.cluster.mgh'
                                    oannot_mc_f = contrastdir+'mc-z.'+direction+'.th'+str(cache)+'.sig.ocn.annot'
                                    if self.check_mcz_summary(sum_mc_f):
                                        self.make_images_results_mc(hemi, analysis_name, contrast.replace('.mtx','').replace(contrast_type+'_',''), direction, cwsig_mc_f, oannot_mc_f, str(cache), 1.3)



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

    def make_images_results_mc(self, hemi, analysis_name, contrast, direction, cwsig_mc_f, oannot_mc_f, cache, thresh):
        self.PATH_save_mc = self.PATHglm+'results/mc/'
        if not path.isdir(self.PATH_save_mc):
            makedirs(self.PATH_save_mc)
        fv_cmds = ['-ss '+self.PATH_save_mc+analysis_name+'_'+contrast+'_lat_mc_'+direction+cache+'.tiff -noquit',
                    '-cam Azimuth 180',
                    '-ss '+self.PATH_save_mc+analysis_name+'_'+contrast+'_med_mc_'+direction+cache+'.tiff -quit',]
        open('fv.cmd','w').close()
        with open('fv.cmd','a') as f:
            for line in fv_cmds:
                f.write(line+'\n')

        system('freeview -f $SUBJECTS_DIR/fsaverage/surf/'+hemi+'.inflated:overlay='+cwsig_mc_f+':overlay_threshold='+str(thresh)+',5:annot='+oannot_mc_f+' -viewport 3d -layout 1 -cmd fv.cmd')


    def make_images_results_fdr(self, hemi, glmdir, contrast_name, file, thresh):
        self.PATH_save_fdr = self.PATHglm+'results/fdr/'
        if not path.isdir(self.PATH_save_fdr):
            makedirs(self.PATH_save_fdr)

        tksurfer_cmds = ['set colscalebarflag 1', 'set scalebarflag 1', 'save_tiff '+self.PATH_save_fdr+contrast_name+'_'+str(3.0)+'_lat.tiff',
        'rotate_brain_y 180', 'redraw', 'save_tiff '+self.PATH_save_fdr+contrast_name+'_'+str(3.0)+'_med.tiff',
        'sclv_set_current_threshold_using_fdr 0.05 0', 'redraw', 'save_tiff '+self.PATH_save_fdr+contrast_name+'_fdr_med.tiff',
        'rotate_brain_y 180', 'redraw', 'save_tiff '+self.PATH_save_fdr+contrast_name+'_fdr_lat.tiff','exit']
        open('scr.tcl','w').close()
        with open('scr.tcl','a') as f:
            for line in tksurfer_cmds:
                f.write(line+'\n')
        print('tksurfer fsaverage '+hemi+' inflated -overlay '+glmdir+'/'+contrast_name+'/'+file+' -fthresh '+str(thresh)+' -tcl scr.tcl')
        system('tksurfer fsaverage '+hemi+' inflated -overlay '+glmdir+'/'+contrast_name+'/'+file+' -fthresh '+str(thresh)+' -tcl scr.tcl')





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

    shutil.copy(GLM_file_group, path.join(GLM_dir,Path(GLM_file_group).name))

    if '.csv' in GLM_file_group:
        df_groups_clin = pd.read_csv(GLM_file_group)
    elif '.xlsx' in GLM_file_group or '.xls' in file_group:
        df_groups_clin = pd.read_excel(GLM_file_group)
    cols2drop = list()
    for col in df_groups_clin.columns.tolist():
        if col not in variables_for_glm+[id_col,group_col]:
            cols2drop.append(col)
    if cols2drop:
        df_groups_clin.drop(columns=cols2drop, inplace=True)

    print('\nSTEP 1 of 2: creating files required for GLM')
    PrepareForGLM(GLM_dir, df_groups_clin, id_col, group_col)

    print('\nSTEP 2 of 2: performing GLM analysis')
    PerformGLM(GLM_dir, FREESURFER_HOME, SUBJECTS_DIR, GLM_measurements, GLM_thresholds, GLM_MCz_cache)


    # shutil.copy(path.join(GLM_dir,'files_for_glm.py'), path.join(path.dirname(__file__),'files_for_glm.py'))
    # try:
    #     from files_for_glm import files_for_glm
    #     remove(path.join(path.dirname(__file__),'files_for_glm.py'))
    #     print('files for glm imported')
    #     SaveGLMimages(GLM_dir, files_for_glm, GLM_measurements, GLM_thresholds, GLM_MCz_cache)
    # except ImportError as e:
    #     print(e)
    #     sys.exit('files_for_glm per group is missing')
