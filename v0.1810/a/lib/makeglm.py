#!/bin/python
#Alexandru Hanganu, 2018 Mar 29

from os import system


def PerformGLM():
    def GLM_2groups():
        with open('file2groups.fsgd', w) as f:
            f.write('
                    GroupDescriptorFile 1\n
                    Class Class1 plus blue\n
                    Class Class2 circle green\n
                    Variables Age\n
                    Input subjid1 Class1 10\n
                    Input subjid2 Class2 20\n
                    Input subjid3 Class2 20\n
                    DefaultVariable Age\n')

        with open('lh-Avg-Intercept-thickness.mat', w) as f:
            f.write('+1.00000 +1.00000 ')
        with open('lh-Diff-f-m-Intercept-thickness.mat', w) as f:
            f.write('+1.00000 -1.00000 ')

        mri_glmfit --y lh.gender_age.thickness.10.mgh --fsgd file.fsgd dods --glmdir Untitled --surf fsaverage lh --label /usr/local/freesurfer/subjects/fsaverage/label/lh.aparc.label --C lh-Avg-Intercept-thickness.mat --C lh-Diff-f-m-Intercept-thickness.mat


    def GLM_1group():

        with open('file2groups.fsgd', w) as f:
            f.write('
                    GroupDescriptorFile 1\n
                    Class Main plus blue\n\n
                    Variables Age\n
                    Input subjid1 Main 10\n
                    Input subjid2 Main 20\n
                    Input subjid3 Main 20\n
                    DefaultVariable Age\n')

        with open('lh-Avg-Intercept-thickness.mat', w) as f:
            f.write('1.00000 +0.00000 ')#Does the average thickness/area differ from zero?
        with open('lh-Diff-f-m-Intercept-thickness.mat', w) as f:
            f.write('0.00000 1.00000 ')#Does the correlation between thickness/area and Value differ from zero?
     #mri_glmfit --y lh.gender_age.thickness.10.mgh --fsgd file.fsgd dods --glmdir Untitled --surf fsaverage lh --label /usr/local/freesurfer/subjects/fsaverage/label/lh.aparc.label --C lh-Avg-Intercept-thickness.mat --C lh-Diff-f-m-Intercept-thickness.mat


    #mris_preproc --fsgd file.fsgd --cache-in thickness.fwhm10.fsaverage --target fsaverage --hemi lh --out lh.gender_age.thickness.10.mgh



    # with open('run.txt', w) as f:
        # f.write('-v /usr/local/freesurfer/subjects/qdec/corrt1t1/lh-Avg-thickness/sig.mgh\n'+
                # '-viewport sagittal -slice 80 127, 127 -ss sag1\n'+
                # '-viewport sagittal -slice 127 127, 127 -ss sag2\n'+
                # '-quit')


# X = np.linspace(-5.0, 5.0, 100)
# plt.title("PDF from Template")
# data = scipy.stats.norm.rvs(size=100000, loc=0, scale=1.5, random_state=123)
# histdata = np.histogram(data, bins=100)
# hist_distdata = scipy.stats.rv_histogram(histdata)
# plt.hist(data, normed=True, bins=100)
# plt.plot(X, hist_distdata.pdf(X), label='PDF')
# plt.plot(X, hist_distdata.cdf(X), label='CDF')
# plt.show()

