#!/bin/python

from os import system, listdir, makedirs, path, getcwd
import shutil, linecache, sys

class PerformGLM():
    def __init__(self, PATHglm, local_maindir):
        self.local_maindir = local_maindir
        for file in listdir(PATHglm):
            if '.py' in file:
                shutil.copy(PATHglm+file, getcwd()+'/'+file)
        self.PATH = PATHglm
        self.glmPATH = PATHglm+'glm/'
        if not path.isdir(self.glmPATH):
            makedirs(self.glmPATH)
        try:
            from subjects_per_group import subjects_per_group
            from files_for_glm import files_for_glm
            print('All GLM analysis DONE')
        except ImportError:
            print('no files_for_glm.py file')

        for group in subjects_per_group:
            for subject in subjects_per_group[group]:
                if subject not in listdir(local_maindir+'freesurfer/subjects/'):
                    print(subject,' is missing in the freesurfer folder')
                    RUN = False
                else:
                    RUN = True
        if RUN:
            self.fsgd_win_to_unix(files_for_glm)
            self.RUN_GLM(files_for_glm)
            print('\n\nGLM DONE')
        else:
            sys.exit('some subjects are missing from the freesurfer folder')
            

    def fsgd_win_to_unix(self, files_for_glm):
        if not path.isdir(self.PATH+'fsgd_unix'):
            makedirs(self.PATH+'fsgd_unix')
        for contrast_type in files_for_glm:
            for fsgd_file in files_for_glm[contrast_type]['fsgd']:
                fsgd_f_unix = self.PATH+'fsgd_unix/'+fsgd_file.replace('.fsgd','')+'_unix.fsgd'
                if not path.isfile(fsgd_f_unix):
                    system('cat '+self.PATH+'fsgd/'+fsgd_file+' | sed \'s/\\r/\\n/g\' > '+fsgd_f_unix)

    def RUN_GLM(self, files_for_glm):
        print('running')
        hemispheres = ['lh','rh']
        measurements = ['thickness','area','volume',]#'curv']
        thresholds = [10,]#5,15,20,25]
        for contrast_type in files_for_glm:
            for fsgd_file in files_for_glm[contrast_type]['fsgd']:
                fsgd_f_unix = self.PATH+'fsgd_unix/'+fsgd_file.replace('.fsgd','')+'_unix.fsgd'
                for hemi in hemispheres:
                    for meas in measurements:
                        for thresh in thresholds:
                            analysis_name = fsgd_file.replace('.fsgd','')+'.'+meas+'.'+hemi+'.fwhm'+str(thresh)
                            glmdir = self.glmPATH+analysis_name
                            mgh_f = glmdir+'/'+meas+'.'+hemi+'.fwhm'+str(thresh)+'.y.mgh'
                            system('mris_preproc --fsgd '+fsgd_f_unix+' --cache-in '+meas+'.fwhm'+str(thresh)+'.fsaverage --target fsaverage --hemi '+hemi+' --out '+mgh_f)
                            for contrast in files_for_glm[contrast_type]['mtx']:
                                explanation = files_for_glm[contrast_type]['mtx_explanation'][files_for_glm[contrast_type]['mtx'].index(contrast)]
                                for gd2mtx in files_for_glm[contrast_type]['gd2mtx']:
                                    system('mri_glmfit --y '+mgh_f+' --fsgd '+fsgd_f_unix+' '+gd2mtx+' --glmdir '+glmdir+' --surf fsaverage '+hemi+' --label '+self.local_maindir+'freesurfer/subjects/fsaverage/label/'+hemi+'.aparc.label --C '+self.PATH+'contrasts/'+contrast)
                                    self.RUN_sim(glmdir, contrast.replace('.mtx',''), hemi, contrast_type, analysis_name, meas, explanation)
                                    # if self.check_maxvox(glmdir, contrast.replace('.mtx','')):
                                        # self.make_images_results_fdr(hemi, glmdir, contrast.replace('.mtx',''), 'sig.mgh', 3.0)

    def check_maxvox(self, glmdir, contrast_name):
        val = [i.strip() for i in open(glmdir+'/'+contrast_name+'/maxvox.dat').readlines()][0].split()[0]
        if float(val) > 3.0 or float(val) < -3.0:
            return True
        else:
            return False

    def check_mcz_summary(self, file):
        if len(linecache.getline(file, 42).strip('\n')) > 0:
            return True
        else:
            return False


    def RUN_sim(self, glmdir, contrast_name, hemi, contrast_type, analysis_name, meas, explanation):
        sim_direction = ['pos', 'neg',]
        contrastdir = glmdir+'/'+contrast_name+'/'
        cache = 13
        fwhm = {'thickness': {'lh': '15','rh': '15'},'area': {'lh': '24','rh': '25'},'volume': {'lh': '16','rh': '16'},}
        for direction in sim_direction:
            if meas != 'curv':
                csd_mc_f = self.local_maindir+'freesurfer/average/mult-comp-cor/fsaverage/'+hemi+'/cortex/fwhm'+fwhm[meas][hemi]+'/'+direction+'/th'+str(cache)+'/mc-z.csd'
                sig_f = contrastdir+'sig.mgh'
                cwsig_mc_f = contrastdir+'mc-z.'+direction+'.th'+str(cache)+'.sig.cluster.mgh'
                vwsig_mc_f = contrastdir+'mc-z.'+direction+'.th'+str(cache)+'.sig.vertex.mgh'
                sum_mc_f = contrastdir+'mc-z.'+direction+'.th'+str(cache)+'.sig.cluster.summary'
                ocn_mc_f = contrastdir+'mc-z.'+direction+'.th'+str(cache)+'.sig.ocn.mgh'
                oannot_mc_f = contrastdir+'mc-z.'+direction+'.th'+str(cache)+'.sig.ocn.annot'
                csdpdf_mc_f = contrastdir+'mc-z.'+direction+'.th'+str(cache)+'.pdf.dat'
                system('mri_surfcluster --in '+sig_f+' --csd '+csd_mc_f+' --mask '+glmdir+'/mask.mgh --cwsig '+cwsig_mc_f+' --vwsig '+vwsig_mc_f+' --sum '+sum_mc_f+' --ocn '+ocn_mc_f+' --oannot '+oannot_mc_f+' --csdpdf '+csdpdf_mc_f+' --annot aparc --cwpvalthresh 0.05 --surf white')                        				
                if self.check_mcz_summary(sum_mc_f):
                    self.make_images_results_mc(hemi, analysis_name, contrast_name.replace(contrast_type+'_',''), direction, cwsig_mc_f, oannot_mc_f, str(cache), 1.3)
                    self.cluster_stats_to_file(analysis_name, sum_mc_f, contrast_name.replace(contrast_type+'_',''), direction, explanation)
            else:
                system('mri_glmfit-sim --glmdir '+glmdir+'/'+contrast_name+' --cache '+str(cache)+' '+direction+' --cwp 0.05 --2spaces')
#                if self.check_mcz_summary(sum_mc_f):
#                    self.make_images_results_mc(hemi, analysis_name, contrast_name.replace(contrast_type+'_',''), direction, cwsig_mc_f, oannot_mc_f, str(cache), 1.3)

    def make_images_results_mc(self, hemi, analysis_name, contrast, direction, cwsig_mc_f, oannot_mc_f, cache, thresh):
        self.PATH_save_mc = self.PATH+'results/mc/'
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
        self.PATH_save_fdr = self.PATH+'results/fdr/'
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

    def cluster_stats_to_file(self, analysis_name, sum_mc_f, contrast_name, direction, explanation):
        file = self.PATH+'results/cluster_stats.log'
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
