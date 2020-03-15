#!/bin/python

from os import system


class PerformGLM():
    def __init__(self, table, PATH, local_maindir):
        self.PATH = PATH
        self.local_maindir = local_maindir

        hemi = ['lh','rh']
        thresh = [10,]
        meas = ['thickness',]
        gd2mtx = ['doss','dods']
        contrast2groups = {'Avg-Intercept':'+1.00000 +1.00000', 'Diff-groups-Intercept':'+1.00000 -1.00000'}
        contrast = {'Avg-Intercept':'+1.00000 +0.00000', 'Diff-Intercept':'+0.00000 +1.00000 '}
        name = ['Avg-Intercept','Diff-Intercept', 'Diff-groups-Intercept']
        sim_direction = ['neg', 'pos', 'abs']
        glmdir = self.PATH+'fsglm'

        self.RUN_GLM(self.make_fsgd(table), 
                     thresh[0],
                     glmdir, hemi[0], name[2], meas[0], gd2mtx[1],
                     self.make_contrasts(glmdir, name[2], contrast2groups[name[2]]))

    def RUN_GLM(self, fsgd, thresh, glmdir, hemi, name, meas, gd2mtx, mat):
        mgh_f = glmdir+'/'+hemi+'.'+name+'.'+meas+'.'+str(thresh)+'.mgh'
        system('mris_preproc --fsgd '+fsgd+' --cache-in thickness.fwhm'+str(thresh)+'.fsaverage --target fsaverage --hemi '+hemi+' --out '+mgh_f)
        print('mri_glmfit --y '+mgh_f+' --fsgd '+fsgd+' '+gd2mtx+' --glmdir '+glmdir+' --surf fsaverage '+hemi+' --label '+self.local_maindir+'freesurfer/subjects/fsaverage/label/lh.aparc.label --C '+mat)
        system('mri_glmfit --y '+mgh_f+' --fsgd '+fsgd+' '+gd2mtx+' --glmdir '+glmdir+' --surf fsaverage '+hemi+' --label '+self.local_maindir+'freesurfer/subjects/fsaverage/label/lh.aparc.label --C '+mat)

    def RUN_sim(self, glmdir,sim_direction):
        system('--glmdir '+glmdir+' --cache 4 '+sim_direction+' --cwp 0.05 --2spaces')

    def make_images_results(self, hemi, glmdir, contrast_name):
        cmds = ['set colscalebarflag 1', 'set scalebarflag 1', 'save_tiff /home/fsl/Desktop/'+contrast_name+'_30_lat.tiff',
        'rotate_brain_y 180', 'redraw', 'save_tiff /home/fsl/Desktop/'+contrast_name+'_30_med.tiff',
        'sclv_set_current_threshold_using_fdr 0.05 0', 'redraw', 'save_tiff /home/fsl/Desktop/'+contrast_name+'_fdr_med.tiff',
        'rotate_brain_y 180', 'redraw', 'save_tiff /home/fsl/Desktop/'+contrast_name+'_fdr_lat.tiff',]
        open('scr.tcl','w').close()
        with open('scr.tcl','a') as f:
            for line in cmds:
                f.write(line+'\n')
        system('tksurfer fsaverage '+hemi+' inflated -overlay '+glmdir+'/'+contrast_name+'/sig.mgh -fthresh 3.0 -tcl scr.tcl')
