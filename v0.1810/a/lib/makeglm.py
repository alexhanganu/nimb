#!/bin/python
#Alexandru Hanganu, 2018 Mar 29

from os import system


class PerformGLM():
    def __init__(self):
        self.PATH = '/home/fsl/Desktop/'
        self.local_maindir = '/usr/local/'

        hemi = ['lh','rh']
        thresh = [10,]
        meas = ['thickness',]
        gd2mtx = ['doss','dods']
        contrast2groups = {'Avg-Intercept':'+1.00000 +1.00000', 'Diff-groups-Intercept':'+1.00000 -1.00000'}
        contrast = {'Avg-Intercept':'1 0', 'Diff-Intercept':'+0.00000 +1.00000 '}
        name = ['Avg-Intercept','Diff-Intercept', 'Diff-groups-Intercept']
        sim_direction = ['neg', 'pos', 'abs']
        glmdir = self.PATH+'fsglm'

        self.RUN_GLM(self.make_fsgd_1group(), 
                     thresh[0],
                     glmdir, hemi[0], name[2], meas[0], gd2mtx[1],
                     self.make_contrasts(glmdir, name[2], contrast2groups[name[2]]))
    # 'lh-Avg-Intercept-thickness.mat': '1.00000 +0.00000 ')#Does the average thickness/area differ from zero?
    # 'lh-Diff-f-m-Intercept-thickness.mat': '0.00000 1.00000 ')#Does the correlation between thickness/area and Value differ from zero?
    #the slope is the change of thickness with age
    #the intercepts/offset is the thicknes at age=0
    #DODS = different offset different slope


    def make_fsgd_2groups(self, variable,d_subjid):
        file = self.PATH+'qdec.fsgd'
        with open(file, 'a') as f:
            f.write('GroupDescriptorFile 1\nClass Class1 plus blue\nClass Class2 circle green\nVariables ')
            f.write(variable+'\n')
            for subjid in d_subjid:
            	f.write('Input '+subjid+' '+d_subjid[subjid][0]+' '+d_subjid[subjid][1]+'\n')
            f.write('DefaultVariable Age\n')
        return file

    def make_fsgd_1group(self):
        file = self.PATH+'qdec.fsgd'#file1group.fsgd'
        #with open(file, 'a') as f:
        #    f.write('
        #            GroupDescriptorFile 1\n
        #            Class Main plus blue\n\n
        #            Variables Age\n
        #            Input subjid1 Main 10\n
        #            Input subjid2 Main 20\n
        #            Input subjid3 Main 20\n
        #            DefaultVariable Age\n')
        return file

    def make_contrasts(self, glmdir, contrast_name, contrast):
        file = glmdir+'/'+contrast_name+'.mat'
        open(file, 'w').close()
        with open(file, 'a') as f:
            print('writing to C1.mat')
            f.write(contrast)
        return file

    def RUN_GLM(self, fsgd, thresh, glmdir, hemi, name, meas, gd2mtx, mat):
        mgh_f = glmdir+'/'+hemi+'.'+name+'.'+meas+'.'+str(thresh)+'.mgh'
        system('mris_preproc --fsgd '+fsgd+' --cache-in thickness.fwhm'+str(thresh)+'.fsaverage --target fsaverage --hemi '+hemi+' --out '+mgh_f)
        print('mri_glmfit --y '+mgh_f+' --fsgd '+fsgd+' '+gd2mtx+' --glmdir '+glmdir+' --surf fsaverage '+hemi+' --label '+self.local_maindir+'freesurfer/subjects/fsaverage/label/lh.aparc.label --C '+mat)
        system('mri_glmfit --y '+mgh_f+' --fsgd '+fsgd+' '+gd2mtx+' --glmdir '+glmdir+' --surf fsaverage '+hemi+' --label '+self.local_maindir+'freesurfer/subjects/fsaverage/label/lh.aparc.label --C '+mat)

    def RUN_sim(self, glmdir,sim_direction):
        system('--glmdir '+glmdir+' --cache 4 '+sim_direction+' --cwp 0.05 --2spaces')

    def make_images_results(self, hemi, glmdir, contrast_name):
        average = {'lh':''$SUBJECTS_DIR/fsaverage/surf/lh.inflated'',
                    'rh':'$SUBJECTS_DIR/fsaverage/surf/rh.inflated'}
        thresh = '4'
        img_name = 'sag1'
        system('freeview -f '+average[hemi]+':annot=aparc.annot:annot_outline=1:overlay='+glmdir+'/'+contrast_name+'/sig.mgh:overlay_threshold='+thresh+',5 -viewport 3d --ss '+img_name)




# X = np.linspace(-5.0, 5.0, 100)
# plt.title("PDF from Template")
# data = scipy.stats.norm.rvs(size=100000, loc=0, scale=1.5, random_state=123)
# histdata = np.histogram(data, bins=100)
# hist_distdata = scipy.stats.rv_histogram(histdata)
# plt.hist(data, normed=True, bins=100)
# plt.plot(X, hist_distdata.pdf(X), label='PDF')
# plt.plot(X, hist_distdata.cdf(X), label='CDF')
# plt.show()