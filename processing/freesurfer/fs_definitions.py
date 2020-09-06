#!/bin/python
# 2020.09.04

suggested_times = {
        'registration':'01:00:00',
        'recon':'30:00:00',
        'autorecon1':'5:00:00',
        'autorecon2':'12:00:00',
        'autorecon3':'12:00:00',
        'recbase':'30:00:00',
        'reclong':'23:00:00',
        'qcache':'03:00:00',
        'brstem':'03:00:00',
        'hip':'03:00:00',
        'tha':'03:00:00',
        'masks':'12:00:00',
        }

IsRunning_files = ['IsRunning.lh+rh', 'IsRunningBSsubst', 'IsRunningHPsubT1.lh+rh', 'IsRunningThalamicNuclei_mainFreeSurferT1']

f_autorecon = {1:['mri/nu.mgz','mri/orig.mgz','mri/brainmask.mgz',],
                2:['stats/lh.curv.stats','stats/rh.curv.stats',],
                3:['stats/aseg.stats','stats/wmparc.stats',]}

 '''must check for all files: https://surfer.nmr.mgh.harvard.edu/fswiki/ReconAllDevTable '''
files_created = {
    'recon-all' : ['mri/wmparc.mgz',],
    'autorecon1': ['mri/nu.mgz','mri/orig.mgz','mri/brainmask.mgz',],
    'autorecon2': ['stats/lh.curv.stats','stats/rh.curv.stats',],
    'autorecon3': ['stats/aseg.stats','stats/wmparc.stats',],
    'qcache'    : ['surf/rh.w-g.pct.mgh.fsaverage.mgh', 'surf/lh.thickness.fwhm10.fsaverage.mgh']
}

log_files = {
    'bs':{
        7:'brainstem-substructures-T1.log', 6:'brainstem-structures.log',
          },
    'hip':{
        7:'hippocampal-subfields-T1.log', 6:'hippocampal-subfields-T1.log',
          },
    'tha':{
        7:'thalamic-nuclei-mainFreeSurferT1.log', 6:'',
          },
}


bs_hip_tha_stats_file_inmri = {
    'bs':{
        7:'brainstemSsVolumes.v12.txt', 6:'brainstemSsVolumes.v10',},
    'hipL':{
        7:'lh.hippoSfVolumes-T1.v21.txt', 6:'lh.hippoSfVolumes-T1.v10.txt',},
    'hipR':{
        7:'rh.hippoSfVolumes-T1.v21.txt', 6:'rh.hippoSfVolumes-T1.v10.txt',},
    'amyL':{
        7:'lh.amygNucVolumes-T1.v21.txt', 6:'',},
    'amyR':{
        7:'rh.amygNucVolumes-T1.v21.txt', 6:'',},
    'tha':{
        7:'ThalamicNuclei.v12.T1.volumes.txt', 6:'',},
                         }

bs_hip_tha_stats_file_instats = {
    'bs':{
        7:'brainstem.v12.stats', 6:'brainstem.v10.stats',},
    'hipL':{
        7:'lh.hipposubfields.T1.v21.stats', 6:'lh.hipposubfields.T1.v10.stats',},
    'hipR':{
        7:'rh.hipposubfields.T1.v21.stats', 6:'rh.hipposubfields.T1.v10.stats',},
    'amyL':{
        7:'lh.amygdalar-nuclei.T1.v21.stats', 6:'',},
    'amyR':{
        7:'rh.amygdalar-nuclei.T1.v21.stats', 6:'',},
    'tha':{
        7:'thalamic-nuclei.v12.T1.stats', 6:'',},
                       }

fs_structure_codes = {'left_hippocampus':17,'right_hippocampus':53,
                    'left_thalamus':10,'right_thalamus':49,'left_caudate':11,'right_caudate':50,
                    'left_putamen':12,'right_putamen':51,'left_pallidum':13,'right_pallidum':52,
                    'left_amygdala':18,'right_amygdala':54,'left_accumbens':26,'right_accumbens':58,
                    'left_hippocampus_CA2':550,'right_hippocampus_CA2':500,
                    'left_hippocampus_CA1':552,'right_hippocampus_CA1':502,
                    'left_hippocampus_CA4':556,'right_hippocampus_CA4':506,
                    'left_hippocampus_fissure':555,'right_hippocampus_fissure':505,
                    'left_amygdala_subiculum':557,'right_amygdala_subiculum':507,
                    'left_amygdala_presubiculum':554,'right_amygdala_presubiculum':504,
                    }

