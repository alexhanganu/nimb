#!/bin/python
# 2021.11.10
from os import path
import os

hemi = ['lh','rh']

class FreeSurferVersion:
    def __init__(self, freesurfer_version):
        self.version = freesurfer_version

    def fs_ver(self):
        if len(str(self.version)) > 1:
            return str(self.version[0])
        else:
            return str(self.version)

    def fs_ver2(self):
        if len(str(self.version)) > 1:
            return str(self.version.replace(".","")[:2])
        else:
            return str(self.version)


class FSProcesses:
    def __init__(self, freesurfer_version):
        """
        codes in atlas_chk key MUST be the same as atlas names in
        processing/atlases/atlas_definitions.atlas_data
        """
        self.processes = {
            "autorecon1":{
                        "group": "recon",
                        "run_step":1,
                        "isrun_f":"IsRunning.lh+rh",
                        "files_2chk":['mri/nu.mgz',
                                      'mri/orig.mgz',
                                      'mri/brainmask.mgz',],
                        "time_suggested":'05:00:00'},
            "autorecon2":{
                        "group": "recon",
                        "run_step":2,
                        "isrun_f":"IsRunning.lh+rh",
                        "files_2chk":['stats/lh.curv.stats',
                                      'stats/rh.curv.stats',],
                        "time_suggested":'12:00:00'},
            "autorecon3":{
                        "group": "recon",
                        "run_step":3,
                        "isrun_f":"IsRunning.lh+rh",
                        "files_2chk":['stats/aseg.stats',
                                      'stats/wmparc.stats',],
                        "time_suggested":'12:00:00'},
            "qcache"    :{
                        "group": "recon",
                        "run_step":4,
                        "isrun_f":"IsRunning.lh+rh",
                        "files_2chk":['surf/rh.w-g.pct.mgh.fsaverage.mgh',
                                      'surf/lh.thickness.fwhm10.fsaverage.mgh'],
                        "time_suggested":'03:00:00'},
            "brstem"    :{
                        "fsver"  :6,
                        "log"    :"brainstem-substructures-T1.log",
                        "log6"   :"brainstem-structures.log",
                        "group"  :"atlas",
                        "atlas_2chk": ['BS'],
                        "cmd6"   :"brainstem-structures",
                        "cmd"    :"segmentBS.sh",
                        "s_param":"",
                        "run_step":5,
                        "isrun_f":"IsRunningBSsubst",
                        "time_suggested":'03:00:00'},
            "hip"       :{
                        "fsver"  :6,
                        "log"    :"hippocampal-subfields-T1.log",
                        "group"  :"atlas",
                        "atlas_2chk": ['HIP', 'AMY'],
                        "cmd6"   :"hippocampal-subfields-T1",
                        "cmd"    :"segmentHA_T1.sh",
                        "s_param":"",
                        "run_step":6,
                        "isrun_f":"IsRunningHPsubT1.lh+rh",
                        "time_suggested":'03:00:00'},
            "tha"       :{
                        "fsver"  :7,
                        "log"    :"thalamic-nuclei-mainFreeSurferT1.log",
                        "group"  :"atlas",
                        "atlas_2chk": ['THA'],
                        "cmd"    :"segmentThalamicNuclei.sh",
                        "s_param":"",
                        "run_step":7,
                        "isrun_f":"IsRunningThalamicNuclei_mainFreeSurferT1",
                        "time_suggested":'03:00:00'},
            "hypotha"   :{
                        "fsver"  :72,
                        "log"    :"hypothalamic_subunits_volumes.log",
                        "group"  :"atlas",
                        "atlas_2chk": ['HypoTHA'],
                        "cmd"    :"mri_segment_hypothalamic_subunits",
                        "s_param":"--s",
                        "run_step":8,
                        "isrun_f":"IsRunningHypoThalamicNuclei_mainFreeSurferT1",
                        "time_suggested":'03:00:00'}}

        self.recons   = [i for i in self.processes if "recon" in self.processes[i]["group"]]
        self.atlas_proc = [i for i in self.processes if "atlas" in self.processes[i]["group"]]
        self.IsRunning_files = [self.processes[i]["isrun_f"] for i in self.atlas_proc] +\
                                [self.processes["autorecon1"]["isrun_f"]]
        self.fs_ver2 = FreeSurferVersion(freesurfer_version).fs_ver2()

    def log(self, process):
        if process in self.recons:
            file = 'recon-all.log'
        elif self.fs_ver2 == 6 and "log6" in self.processes[process]:
            file = self.processes[process]["log6"]
        else:
            file = self.processes[process]["log"]
        return os.path.join('scripts', file)

    def process_order(self):
        order_all = sorted(self.processes, key=lambda k: self.processes[k]["run_step"])
        if self.fs_ver2 < "7":
            fs7_atlases = [i for i in self.atlas_proc if self.processes[i]["fsver"] > 6]
            return [i for i in order_all if i not in fs7_atlases]
        elif self.fs_ver2 < "72":
            fs72_atlases = [i for i in self.atlas_proc if self.processes[i]["fsver"] == 72]
            return [i for i in order_all if i not in fs72_atlases]
        else:
            return order_all

    def cmd(self, process, _id, id_base = '', ls_tps = []):
        if process in self.recons:
            return f"recon-all -{process} -s {_id}"
        elif process == 'recbase':
            all_tps = ''.join([f" -tp {i}" for i in ls_tps])
            return f"recon-all -base {_id}{all_tps} -all"
        elif process == 'reclong':
            return f"recon-all -long {_id} {id_base} -all"
        elif self.processes[process]["group"] == 'atlas':
            return self.cmd_atlas(process, _id)
        elif process == 'masks':
            chdir = os.path.join(NIMB_HOME, 'processing', 'freesurfer')
            return f"cd {chdir}\npython run_masks.py {_id}"

    def cmd_atlas(self, process, _id):
        if self.fs_ver2 < "7":
            run_sh = self.processes[process]["cmd6"]
            return f"recon-all -s {_id} -{run_sh}"
        else:
            run_sh = self.processes[process]["cmd"]
            s_param = self.processes[process]["s_param"]
            if s_param:
                return f"{run_sh} {s_param} {_id}"
            else:
                return f"{run_sh} {_id}"

    def get_suggested_times(self):
        suggested_times = {
            'registration':'01:00:00',
            'recon'       :'30:00:00',
            'recbase'     :'30:00:00',
            'reclong'     :'23:00:00',
            'masks'       :'12:00:00',
            'archiving'   :'01:00:00',}
            # 'autorecon1'  :'05:00:00',
            # 'autorecon2'  :'12:00:00',
            # 'autorecon3'  :'12:00:00',
            # 'qcache'      :'03:00:00',
            # 'brstem'      :'03:00:00',
            # 'hip'         :'03:00:00',
            # 'tha'         :'03:00:00',
            # 'hypotha'     :'03:00:00',}
        for process in self.processes:
            suggested_times[process] = self.processes[process]["time_suggested"]
        return suggested_times


class ChkFSQcache:
    '''FS GLM requires two folders: surf and label
        script checks that both folders are present
        checks that all GLM files are present
    Args:
        path2chk: path to the folder with the subject
        _id: ID of the subject to chk
    Return:
        populates list of missing subjects
    '''
    def __init__(self, path2chk, _id, vars_fs):
        self.path2chk   = path2chk
        self._id        = _id
        self.GLM_meas   = vars_fs["GLM_measurements"]
        self.GLM_thresh = vars_fs["GLM_thresholds"]
        self.miss       = self.chk_f()

    def chk_f(self):
        miss = {}
        surf_dir = os.path.join(self.path2chk, self._id, 'surf')
        label_dir = os.path.join(self.path2chk, self._id, 'label')
        if os.path.exists(surf_dir) and os.path.exists(label_dir):
            for hemis in hemi:
                for meas in self.GLM_meas:
                    for thresh in self.GLM_thresh:
                        file = f'{hemis}.{meas}.fwhm{str(thresh)}.fsaverage.mgh'
                        file_abspath = os.path.join(surf_dir, file)
                        if not os.path.exists(file_abspath):
                            print("        files: MISSING", file, " id: ", self._id)
                            miss = self.populate_miss(miss, file)
            return miss
        else:
            return self.populate_miss(miss, 'surf label missing')

    def populate_miss(self, miss, file):
        if self._id not in miss:
            miss[self._id] = list()
        miss[self._id].append(file)
        return miss


class GLMVars:
    def __init__(self, proj_vars):
        self.proj_vars = proj_vars

    def f_ids_processed(self):
        return path.join(self.proj_vars['materials_DIR'][1], 'f_ids.json')


class FSGLMParams:
    def __init__(self, path_GLMdir):
        self.GLM_sim_fwhm4csd = {'thickness': {'lh': '15',
                                               'rh': '15'},
                                 'area'     : {'lh': '24',
                                               'rh': '25'},
                                 'volume'   : {'lh': '16',
                                               'rh': '16'},}
        self.mcz_sim_direction = ['pos', 'neg',]

        self.GLM_MCz_meas_codes = {'thickness':'th',
                                   'area'     :'ar',
                                   'volume'   :'vol'}
        self.PATHglm_glm           = path.join(path_GLMdir,   'glm')
        self.subjects_per_group    = path.join(path_GLMdir,   'ids_per_group.json')
        self.files_for_glm         = path.join(path_GLMdir,   'files_for_glm.json')
        self.PATH_img              = path.join(path_GLMdir,   'images')
        self.sig_fdr_json          = path.join(self.PATH_img, 'sig_fdr.json')
        self.sig_mc_json           = path.join(self.PATH_img, 'sig_mc.json')
        self.PATHglm_results       = path.join(path_GLMdir,   'results')
        self.err_mris_preproc_file = path.join(self.PATHglm_results,'error_mris_preproc.json')
        self.cluster_stats         = path.join(self.PATHglm_results,'cluster_stats.log')
        self.cluster_stats_2csv    = path.join(self.PATHglm_results,'cluster_stats.csv')
        self.sig_contrasts         = path.join(self.PATHglm_results,'sig_contrasts.log')

"""
suggested by Douglas Greve (https://www.mail-archive.com/freesurfer@nmr.mgh.harvard.edu/msg71630.html): 
when VARiable is provided, first test if the slopes are different: [0 0 -1 1]
if slopes are different, use the contrast [1 -1 0 0] DODS
is there is no difference between the slopes, use [1 -1 0] DOSS
To test if VAR changes cortical thickness regardless of Group (assuming there is no interaction), use [0 0 1] DOSS

"""
GLMcontrasts = {
        "contrasts" : {
            'g1v1':{'slope.mtx'         :['0 1',        'does the correlation between thickness and variable differ from zero ? is the slope equal to 0? contrast: 0 1; t-test with the slope>0 being positive',],},
            'g2v0':{'group.diff.mtx'    :['1 -1',       'is there a difference between groups? Is there a difference between the group intercepts? contrast 1 -1; t-test with Group1>Group2 being positive',],},
            'g2v1':{'group-x-var.mtx'   :['0 0 1 -1',   'is there a difference between the group VARiable slopes? contrast 0 0 1 -1; t-test with Group1>Group2 being positive; Note: this is an interaction between group and VARiable',],
                    'group.diff.mtx'    :['1 -1 0 0',   'is there a difference between groups regressing out the effect of VARiable? Is there a difference between the group intercepts? Is there a difference between groups when the VARiable has the value 0? contrast 1 -1 0 0; t-test with Group1>Group2 being positive',],
                    'g1g2.var.mtx'      :['0 0 0.5 0.5','does mean of group VARiable slope differ from 0? Is there an average affect of VARiable regressing out the effect of group? contrast 0 0 0.5 -0.5; t-test with (Group1+Group2)/2 > 0 being positive',],}
                            },
        "dods_doss" : {
            'g1v1':[       'dods',],
            'g2v0':['doss','dods',],
            'g2v1':[       'dods',],},
        "contrasts_not_used" : {
            'g1v0':{'intercept.mtx'     :['1',          't-test with intercept>0 being positive; is the intercept/mean equal to 0?',],},
            'g1v1':{'intercept.mtx'     :['1 0',        't-test with intercept>0 being positive; is the intercept equal to 0? Does the average thickness differ from zero ?',],},
            'g1v2':{'main.mtx'          :['1 0 0',      't-test with offset>0 being positive; the intercept/offset is different than 0 after regressing out the effects of var1 and var2',],
                    'var1.mtx'          :['0 1 0',      't-test with var1 slope>0 being positive',],
                    'var2.mtx'          :['0 0 1',      't-test with var2 slope>0 being positive',],},
            'g2v0':{'group1.mtx'        :['1 0',        't-test with Group1>0 being positive; is there a main effect of Group1? Does the mean of Group1 equal 0? Does the average thickness differ from zero ?',],
                    'group2.mtx'        :['0 1',        't-test with Group2>0 being positive; is there a main effect of Group2? Does the mean of Group2 equal 0? Does the correlation between thickness and group differ from zero ?',],
                    'g1g2.intercept.mtx':['0.5 0.5',    't-test with (Group1+Group2)/2 > 0 being positive (red/yellow). If the mean is < 0, then it will be displayed in blue/cyan; does mean of the group means differ from 0?',],},
            'g2v1':{'g1g2.intercept.mtx':['0.5 0.5 0 0','t-test with (Group1+Group2)/2 > 0 being positive (red/yellow). If the mean is < 0, then it will be displayed in blue/cyan; does mean of group intercepts differ from 0? Is there an average main effect regressing out age?',]}
                                },
        "dods_doss_not_used" : {
            'g1v0':['dods',],
            'g1v2':['dods',],}
                }
# https://surfer.nmr.mgh.harvard.edu/fswiki/Fsgdf2G2V


# def get_names_of_structures():
#     name_structures = list()

#     for val in segmentations_header:
#         name_structures.append(segmentations_header[val])
#     for val in parc_DK_header:
#         name_structures.append(parc_DK_header[val])
#     for val in brstem_hip_header['all']:
#         name_structures.append(brstem_hip_header['all'][val])
#     for val in parc_DS_header:
#         name_structures.append(parc_DS_header[val])

#     return name_structures

# def get_names_of_measurements():
#     name_measurement = ['Brainstem','HIPL','HIPR',]

#     for val in segmentation_parameters:
#         name_measurement.append('VolSeg'+val.replace('Volume_mm3',''))
#         name_measurement.append('VolSegWM'+val.replace('Volume_mm3','')+'_DK')

#     for hemi in ('L','R',):
#         for atlas in ('_DK','_DS',):
#             for meas in parc_parameters:
#                 name_measurement.append(parc_parameters[meas]+hemi+atlas)

#     return name_measurement



# class FilePerFSVersion:
#     def __init__(self, freesurfer_version):
#         self.processes = ['Subcort', 'DK', 'DKT', 'DS', 'WMDK', 'brstem', 'hip', 'amy', 'tha']
#         self.fs_ver = FreeSurferVersion(freesurfer_version).fs_ver()
#         self.fs_ver2 = FreeSurferVersion(freesurfer_version).fs_ver2()

#     def stats_f(self, process, _dir, hemi='lhrh'): #to be removed
#         hemi3 = {'lh':'lh.', 'rh':'rh.', 'lhrh':''}
#         stats_files = {
#             'stats': {
#                 'Subcort':{'7':'aseg.stats',                      '6':'aseg.stats',},
#                 'DK'     :{'7':'aparc.stats',                     '6':'aparc.stats',},
#                 'DKT'    :{'7':'aparc.DKTatlas.stats',            '6':'aparc.DKTatlas.stats',},
#                 'DS'     :{'7':'aparc.a2009s.stats',              '6':'aparc.a2009s.stats',},
#                 'WMDK'   :{'7':'wmparc.stats',                    '6':'',},
#                 'brstem'     :{'7':'brainstem.v12.stats',             '6':'brainstem.v10.stats',},
#                 'hip'    :{'7':'hipposubfields.T1.v21.stats',     '6':'hipposubfields.T1.v10.stats',},
#                 'amy'    :{'7':'amygdalar-nuclei.T1.v21.stats',   '6':'',},
#                 'tha'    :{'7':'thalamic-nuclei.v12.T1.stats',    '6':'',},
#                 'hypotha':{'7':'hypothalamic_subunits_volumes.v1.stats',    '6':'',}},
#             'stats_old': {
#                 'brstem'   :{'7':'aseg.brainstem.volume.stats',       '6':'aseg.brainstem.volume.stats',},
#                 'hip'  :{'7':'aseg.hippo.lh.volume.stats',        '6':'aseg.hippo.lh.volume.stats',},
#                 'amy'  :{'7':'amygdalar-nuclei.lh.T1.v21.stats',  '6':'',},
#                 'tha'  :{'7':'thalamic-nuclei.lh.v12.T1.stats',   '6':'',}},
#             'mri': {
#                 'brstem'   :{'7':'brainstemSsVolumes.v12.txt',        '6':'brainstemSsVolumes.v10',},
#                 'hip'  :{'7':'hippoSfVolumes-T1.v21.txt',         '6':'hippoSfVolumes-T1.v10.txt',},
#                 'amy'  :{'7':'amygNucVolumes-T1.v21.txt',         '6':'',},
#                 'tha'  :{'7':'ThalamicNuclei.v12.T1.volumes.txt', '6':'',}}
#                         }
#         hemi_ = hemi3[hemi]
#         f_4process = stats_files[_dir][process][self.fs_ver]
#         file = f'{hemi_}{f_4process}'
#         if _dir == 'stats_old' and process != 'brstem':
#             file = f'{f_4process}'
#             _dir = 'stats'
#             if hemi == 'rh':
#                 file = file.replace('lh', 'rh')
#         return path.join(_dir, file)


#     def log_f(self, process): #to be removed
#         log = {
#             'recon'     :{'7':'recon-all.log',                       '6':'recon-all.log'},
#             'autorecon1':{'7':'recon-all.log',                       '6':'recon-all.log'},
#             'autorecon2':{'7':'recon-all.log',                       '6':'recon-all.log'},
#             'autorecon3':{'7':'recon-all.log',                       '6':'recon-all.log'},
#             'qcache'    :{'7':'recon-all.log',                       '6':'recon-all.log'},
#             'brstem'        :{'7':'brainstem-substructures-T1.log',      '6':'brainstem-structures.log'},
#             'hip'       :{'7':'hippocampal-subfields-T1.log',        '6':'hippocampal-subfields-T1.log'},
#             'tha'       :{'7':'thalamic-nuclei-mainFreeSurferT1.log','6':''},
#             'hypotha'   :{'7':'hypothalamic_subunits_volumes.log',   '6':''}}
#         return path.join('scripts', log[process][self.fs_ver])


# processes_recon   = ["autorecon1",
#                      "autorecon2",
#                      "autorecon3",
#                      "qcache"]
# processes_subcort = ["brstem","hip","tha","hypotha"]
# process_order = ["registration",]+processes_recon+processes_subcort



# # must check for all files: https://surfer.nmr.mgh.harvard.edu/fswiki/ReconAllDevTable
# f_autorecon = {
#         1:['mri/nu.mgz','mri/orig.mgz','mri/brainmask.mgz',],
#         2:['stats/lh.curv.stats','stats/rh.curv.stats',],
#         3:['stats/aseg.stats','stats/wmparc.stats',]}
# files_created = {
#     'recon-all' : ['mri/wmparc.mgz',],
#     'autorecon1': ['mri/nu.mgz','mri/orig.mgz','mri/brainmask.mgz',],
#     'autorecon2': ['stats/lh.curv.stats','stats/rh.curv.stats',],
#     'autorecon3': ['stats/aseg.stats','stats/wmparc.stats',],
#     'qcache'    : ['surf/rh.w-g.pct.mgh.fsaverage.mgh', 'surf/lh.thickness.fwhm10.fsaverage.mgh']}


# all_data = {
#     'atlases':['bs','hip','amy','tha','hypotha','Subcort', 'CortexDK','CortexDKT','CortexDS', 'WMDK'],
#     "atlas_params" : {
#                 'bs' : {
#                     'atlas_param':'bs',
#                     'atlas_name' :'Brainstem segmentations'},
#                 'hip' : {
#                     'atlas_param':'hip',
#                     'atlas_name' :'Hippocampus segmentations'},
#                 'amy' : {
#                     'atlas_param':'amy',
#                     'atlas_name' :'Amygdala segmentations'},
#                 'tha' : {
#                     'atlas_param':'tha',
#                     'atlas_name' :'Thalamus segmentations'},
#                 'Subcort' : {
#                     'atlas_param':'Subcort',
#                     'atlas_name' :'Subcortical segmentations'},
#                 'DK' : {
#                     'atlas_param':'CortexDK',
#                     'atlas_name' :'Desikan'},
#                 'DKT': {
#                     'atlas_param':'CortexDKT',
#                     'atlas_name' :'Desikan-Tournoix'},
#                 'DS' : {
#                     'atlas_param':'CortexDS',
#                     'atlas_name' :'Destrieux'},
#                 'WMDK' : {
#                     'atlas_param':'WMDK',
#                     'atlas_name' :'White Matter subcortical segmentations based on Desikan atlas'},
#                 'hypotha':{"atlas_param":"hypotha", "atlas_name": "Hypothalamus segmentations"},
#                },
#     'bs':{
#         'two_hemi':False,
#         'hemi' : ['lhrh'],
#         'parameters' : {'Vol':'Vol'},
#         'header':['Medulla','Pons','SCP','Midbrain','Whole_brainstem',]},
#     'hip':{
#         'two_hemi':True,
#         'hemi' : ['lh','rh'],
#         'parameters' : {'Vol':'Vol'},
#         'header':['Hippocampal_tail','subiculum', 'subiculum-body', 'subiculum-head', 'CA1',
#                 'CA1-body', 'CA1-head', 'hippocampal-fissure',
#                 'presubiculum','presubiculum-body','presubiculum-head','parasubiculum','molecular_layer_HP',
#                 'molecular_layer_HP-head','molecular_layer_HP-body','GC-ML-DG','GC-ML-DG-body', 'GC-ML-DG-head'
#                 'CA3', 'CA3-body', 'CA3-head', 'CA4', 'CA4-body', 'CA4-head', 'fimbria','HATA','Whole_hippocampus',
#                 'Whole_hippocampal_body', 'Whole_hippocampal_head']},
#     'amy':{
#         'two_hemi':True,
#         'hemi' : ['lh','rh'],
#         'parameters' : {'Vol':'Vol'},
#         'header': ['Lateral-nucleus', 'Basal-nucleus', 'Accessory-Basal-nucleus', 'Anterior-amygdaloid-area-AAA',
#                     'Central-nucleus', 'Medial-nucleus', 'Cortical-nucleus', 'Corticoamygdaloid-transitio',
#                     'Paralaminar-nucleus', 'Whole_amygdala']},
#     'tha':{
#         'two_hemi':True,
#         'hemi' : ['lh','rh'],
#         'parameters' : {'Vol':'Vol'},
#         'header': ['AV', 'CeM', 'CL', 'CM', 'LD', 'LGN', 'LP', 'L-Sg', 'MDl', 'MDm', 'MGN', 'MV(Re)', 'Pc', 'Pf', 'Pt',
#                     'PuA', 'PuI', 'PuL', 'PuM', 'VA', 'VAmc', 'VLa', 'VLp', 'VM', 'VPL', 'Whole_thalamus']},
#     'hypotha':{
#         'two_hemi':True,
#         'hemi' : ['lh','rh'],
#         'parameters' : {'Vol':'Vol'},
#         'header': ['SON', 'PVN', 'TMN']},
#     'Subcort':{
#         'two_hemi':False,
#         'hemi' : ['lhrh'],
#         'parameters' : {'Volume_mm3':'Vol',         'NVoxels'    :'VolVoxNum',
#                         'normMean'  :'VolMeanNorm', 'normStdDev':'VolStdNorm',
#                         'normMin'   :'VolMinNorm',  'normMax'   :'VolMaxNorm',
#                         'normRange' :'VolRangeNorm'},
#         'header':['Left-Thalamus-Proper', 'Right-Thalamus-Proper', 'Left-Thalamus', 'Right-Thalamus', 'Left-Caudate',
#                 'Right-Caudate', 'Left-Putamen', 'Right-Putamen', 'Left-Pallidum', 'Right-Pallidum', 'Left-Hippocampus',
#                 'Right-Hippocampus', 'Left-Amygdala', 'Right-Amygdala', 'Left-Accumbens-area',
#                 'Right-Accumbens-area', 'Left-Lateral-Ventricle', 'Right-Lateral-Ventricle',
#                 'Left-Inf-Lat-Vent', 'Right-Inf-Lat-Vent', 'Left-Cerebellum-White-Matter',
#                 'Right-Cerebellum-White-Matter', 'Left-Cerebellum-Cortex', 'Right-Cerebellum-Cortex',
#                 'Left-VentralDC', 'Right-VentralDC', 'Left-vessel', 'Right-vessel', 'Left-choroid-plexus',
#                 'Right-choroid-plexus', 'Left-WM-hypointensities', 'Right-WM-hypointensities', 'Left-non-WM-hypointensities',
#                 'Right-non-WM-hypointensities', 'lhCortexVol', 'rhCortexVol', 'lhCerebralWhiteMatterVol',
#                 'rhCerebralWhiteMatterVol', 'lhSurfaceHoles', 'rhSurfaceHoles', '3rd-Ventricle',
#                 '4th-Ventricle', '5th-Ventricle', 'VentricleChoroidVol', 'Brain-Stem', 'CSF', 'Optic-Chiasm',
#                 'CC_Posterior', 'CC_Mid_Posterior', 'CC_Central', 'CC_Mid_Anterior', 'CC_Anterior', 'CortexVol',
#                 'SubCortGrayVol', 'TotalGrayVol', 'BrainSegVol', 'BrainSegVolNotVent', 'BrainSegVolNotVentSurf',
#                 'BrainSegVol-to-eTIV', 'CerebralWhiteMatterVol', 'SupraTentorialVol', 'SupraTentorialVolNotVent',
#                 'SupraTentorialVolNotVentVox', 'WM-hypointensities', 'non-WM-hypointensities', 'SurfaceHoles',
#                 'MaskVol', 'MaskVol-to-eTIV', 'eTIV']},

#     'CortexDK':{
#         'two_hemi':True,
#         'hemi' : ['lh','rh'],
#         'parameters' : {
#                 'GrayVol' :'Vol',
#                 'ThickAvg':'Thick',
#                 'SurfArea':'Area',
#                 'NumVert' :'VertexNum',
#                 'ThickStd':'ThickStd', 
#                 'FoldInd' :'FoldInd',
#                 'MeanCurv':'Curv',
#                 'GausCurv':'CurvGaus',
#                 'CurvInd' :'CurvInd'},
#         'header':['bankssts', 'caudalanteriorcingulate', 'caudalmiddlefrontal', 'cuneus', 'entorhinal', 'fusiform',
#                 'inferiorparietal', 'inferiortemporal', 'isthmuscingulate', 'lateraloccipital', 'lateralorbitofrontal',
#                 'lingual', 'medialorbitofrontal', 'middletemporal', 'parahippocampal', 'paracentral', 'parsopercularis',
#                 'parsorbitalis', 'parstriangularis', 'pericalcarine', 'postcentral', 'posteriorcingulate', 'precentral',
#                 'precuneus', 'rostralanteriorcingulate', 'rostralmiddlefrontal', 'superiorfrontal', 'superiorparietal',
#                 'superiortemporal', 'supramarginal', 'frontalpole', 'temporalpole', 'transversetemporal', 'insula',
#                 'Cortex_MeanThickness', 'Cortex_WhiteSurfArea', 'Cortex_CortexVol', 'Cortex_NumVert', 'UnsegmentedWhiteMatter']},
#     'CortexDKT':{
#         'two_hemi':True,
#         'hemi' : ['lh','rh'],
#         'parameters' : {
#                 'GrayVol' :'Vol',
#                 'ThickAvg':'Thick',
#                 'SurfArea':'Area',
#                 'NumVert' :'VertexNum',
#                 'ThickStd':'ThickStd', 
#                 'FoldInd' :'FoldInd',
#                 'MeanCurv':'Curv',
#                 'GausCurv':'CurvGaus',
#                 'CurvInd' :'CurvInd'},
#         'header':['caudalanteriorcingulate', 'caudalmiddlefrontal', 'cuneus', 'entorhinal', 'fusiform', 'inferiorparietal',
#                 'inferiortemporal', 'isthmuscingulate', 'lateraloccipital', 'lateralorbitofrontal', 'lingual', 'medialorbitofrontal',
#                 'middletemporal', 'parahippocampal', 'paracentral', 'parsopercularis', 'parsorbitalis', 'parstriangularis',
#                 'pericalcarine', 'postcentral', 'posteriorcingulate', 'precentral', 'precuneus', 'rostralanteriorcingulate',
#                 'rostralmiddlefrontal', 'superiorfrontal', 'superiorparietal', 'superiortemporal', 'supramarginal',
#                 'transversetemporal', 'insula', 'Cortex_MeanThickness', 'Cortex_WhiteSurfArea', 'Cortex_CortexVol',
#                 'Cortex_NumVert', 'UnsegmentedWhiteMatter']},
#     'CortexDS':{
#         'two_hemi':True,
#         'hemi' : ['lh','rh'],
#         'parameters' : {
#                 'GrayVol' :'Vol',
#                 'ThickAvg':'Thick',
#                 'SurfArea':'Area',
#                 'NumVert' :'VertexNum',
#                 'ThickStd':'ThickStd', 
#                 'FoldInd' :'FoldInd',
#                 'MeanCurv':'Curv',
#                 'GausCurv':'CurvGaus',
#                 'CurvInd' :'CurvInd'},
#         'header':['G&S_frontomargin', 'G_and_S_frontomargin', 'G&S_occipital_inf', 'G_and_S_occipital_inf', 'G&S_paracentral',
#                 'G_and_S_paracentral', 'G&S_subcentral', 'G_and_S_subcentral', 'G&S_transv_frontopol', 'G_and_S_transv_frontopol',
#                 'G&S_cingul-Ant', 'G_and_S_cingul-Ant', 'G&S_cingul-Mid-Ant', 'G_and_S_cingul-Mid-Ant', 'G&S_cingul-Mid-Post',
#                 'G_and_S_cingul-Mid-Post', 'G_cingul-Post-dorsal', 'G_cingul-Post-ventral', 'G_cuneus', 'G_front_inf-Opercular',
#                 'G_front_inf-Orbital', 'G_front_inf-Triangul', 'G_front_middle', 'G_front_sup', 'G_Ins_lg_and_S_cent_ins',
#                 'G_insular_short', 'G_occipital_middle', 'G_occipital_sup', 'G_oc-temp_lat-fusifor', 'G_oc-temp_med-Lingual',
#                 'G_oc-temp_med-Parahip', 'G_orbital', 'G_pariet_inf-Angular', 'G_pariet_inf-Supramar', 'G_parietal_sup',
#                 'G_postcentral', 'G_precentral', 'G_precuneus', 'G_rectus', 'G_subcallosal', 'G_temp_sup-G_T_transv',
#                 'G_temp_sup-Lateral', 'G_temp_sup-Plan_polar', 'G_temp_sup-Plan_tempo', 'G_temporal_inf', 'G_temporal_middle',
#                 'Lat_Fis-ant-Horizont', 'Lat_Fis-ant-Vertical', 'Lat_Fis-post', 'Pole_occipital', 'Pole_temporal', 'S_calcarine',
#                 'S_central', 'S_cingul-Marginalis', 'S_circular_insula_ant', 'S_circular_insula_inf', 'S_circular_insula_sup',
#                 'S_collat_transv_ant', 'S_collat_transv_post', 'S_front_inf', 'S_front_middle', 'S_front_sup', 'S_interm_prim-Jensen',
#                 'S_intrapariet_and_P_trans', 'S_oc_middle_and_Lunatus', 'S_oc_sup_and_transversal', 'S_occipital_ant', 'S_oc-temp_lat',
#                 'S_oc-temp_med_and_Lingual', 'S_orbital_lateral', 'S_orbital_med-olfact', 'S_orbital-H_Shaped', 'S_parieto_occipital',
#                 'S_pericallosal', 'S_postcentral', 'S_precentral-inf-part', 'S_precentral-sup-part', 'S_suborbital', 'S_subparietal',
#                 'S_temporal_inf', 'S_temporal_sup', 'S_temporal_transverse', 'Cortex_MeanThickness', 'Cortex_WhiteSurfArea',
#                 'Cortex_CortexVol', 'Cortex_NumVert', 'UnsegmentedWhiteMatter']},
#     'WMDK':{
#         'two_hemi':False,
#         'hemi' : ['lhrh'],
#         'parameters' : {'Volume_mm3':'Vol',         'NVoxels'    :'VolVoxNum',
#                         'normMean'  :'VolMeanNorm', 'normStdDev':'VolStdNorm',
#                         'normMin'   :'VolMinNorm',  'normMax'   :'VolMaxNorm',
#                         'normRange' :'VolRangeNorm'},
#         'header':['wm-lh-bankssts', 'wm-lh-caudalanteriorcingulate', 'wm-lh-caudalmiddlefrontal', 'wm-lh-cuneus',
#                 'wm-lh-entorhinal', 'wm-lh-fusiform', 'wm-lh-inferiorparietal', 'wm-lh-inferiortemporal',
#                 'wm-lh-isthmuscingulate', 'wm-lh-lateraloccipital', 'wm-lh-lateralorbitofrontal', 'wm-lh-lingual',
#                 'wm-lh-medialorbitofrontal', 'wm-lh-middletemporal', 'wm-lh-parahippocampal', 'wm-lh-paracentral',
#                 'wm-lh-parsopercularis', 'wm-lh-parsorbitalis', 'wm-lh-parstriangularis', 'wm-lh-pericalcarine',
#                 'wm-lh-postcentral', 'wm-lh-posteriorcingulate', 'wm-lh-precentral', 'wm-lh-precuneus',
#                 'wm-lh-rostralanteriorcingulate', 'wm-lh-rostralmiddlefrontal', 'wm-lh-superiorfrontal',
#                 'wm-lh-superiorparietal', 'wm-lh-superiortemporal', 'wm-lh-supramarginal', 'wm-lh-frontalpole',
#                 'wm-lh-temporalpole', 'wm-lh-transversetemporal', 'wm-lh-insula', 'wm-rh-bankssts',
#                 'wm-rh-caudalanteriorcingulate', 'wm-rh-caudalmiddlefrontal', 'wm-rh-cuneus', 'wm-rh-entorhinal',
#                 'wm-rh-fusiform', 'wm-rh-inferiorparietal', 'wm-rh-inferiortemporal', 'wm-rh-isthmuscingulate',
#                 'wm-rh-lateraloccipital', 'wm-rh-lateralorbitofrontal', 'wm-rh-lingual', 'wm-rh-medialorbitofrontal',
#                 'wm-rh-middletemporal', 'wm-rh-parahippocampal', 'wm-rh-paracentral', 'wm-rh-parsopercularis',
#                 'wm-rh-parsorbitalis', 'wm-rh-parstriangularis', 'wm-rh-pericalcarine', 'wm-rh-postcentral',
#                 'wm-rh-posteriorcingulate', 'wm-rh-precentral', 'wm-rh-precuneus', 'wm-rh-rostralanteriorcingulate',
#                 'wm-rh-rostralmiddlefrontal', 'wm-rh-superiorfrontal', 'wm-rh-superiorparietal', 'wm-rh-superiortemporal',
#                 'wm-rh-supramarginal', 'wm-rh-frontalpole', 'wm-rh-temporalpole', 'wm-rh-transversetemporal',
#                 'wm-rh-insula', 'Left-UnsegmentedWhiteMatter', 'Right-UnsegmentedWhiteMatter']},
#     'header_fs2nimb':{'Medulla':'medulla','Pons':'pons','SCP':'scp','Midbrain':'midbrain',
#                 'Whole_brainstem':'wholeBrainstem',
#                 'Hippocampal_tail':'hippocampal-tail',
#                 'subiculum':'subiculum','subiculum-body':'subiculum-body','subiculum-head':'subiculum-head',
#                 'CA1':'ca1','CA1-body':'ca1-body','CA1-head':'ca1-head','hippocampal-fissure':'fissureHippocampal',
#                 'presubiculum':'presubiculum','presubiculum-body':'presubiculum-body','presubiculum-head':'presubiculum-head',
#                 'parasubiculum':'parasubiculum',
#                 'molecular_layer_HP':'molecularLayerHP','molecular_layer_HP-head':'molecularLayerHP-head',
#                 'molecular_layer_HP-body':'molecularLayerHP-body',
#                 'GC-ML-DG':'gcmldg','GC-ML-DG-body':'gcmldg-body','GC-ML-DG-head':'gcmldg-head',
#                 'CA3':'ca3','CA3-body':'ca3-body','CA3-head':'ca3-head',
#                 'CA4':'ca4','CA4-body':'ca4-body','CA4-head':'ca4-head',
#                 'fimbria':'fimbria','HATA':'hata','Whole_hippocampal_body':'wholeHippocampus-body',
#                 'Whole_hippocampal_head':'wholeHippocampus-head',
#                 'Whole_hippocampus':'wholeHippocampus',
#                 'Lateral-nucleus': 'Lateral-nucleus', 'Basal-nucleus': 'Basal-nucleus', 'Accessory-Basal-nucleus': 'Accessory-Basal-nucleus',
#                 'Anterior-amygdaloid-area-AAA': 'Anterior-amygdaloid-area-AAA', 'Central-nucleus': 'Central-nucleus',
#                 'Medial-nucleus': 'Medial-nucleus', 'Cortical-nucleus': 'Cortical-nucleus',
#                 'Corticoamygdaloid-transitio': 'Corticoamygdaloid-transitio', 'Paralaminar-nucleus': 'Paralaminar-nucleus',
#                 'Whole_amygdala': 'WholeAmygdala',
#                 'AV': 'AV', 'CeM': 'CeM', 'CL': 'CL', 'CM': 'CM', 'LD': 'LD', 'LGN': 'LGN', 'LP': 'LP', 'L-Sg': 'L-Sg',
#                 'MDl':'MDl', 'MDm': 'MDm', 'MGN': 'MGN', 'MV(Re)': 'MV(Re)', 'Pc': 'Pc', 'Pf': 'Pf', 'Pt': 'Pt', 'PuA': 'PuA',
#                 'PuI':'PuI', 'PuL': 'PuL', 'PuM': 'PuM', 'VA': 'VA', 'VAmc': 'VAmc', 'VLa': 'VLa', 'VLp': 'VLp', 'VM': 'VM',
#                 'VPL':'VPL', 'Whole_thalamus': 'WholeThalamus',
#                 'Left-Thalamus-Proper'        :'thalamusProper_lh',        'Right-Thalamus-Proper'        :'thalamusProper_rh',
#                 'Left-Thalamus'               :'thalamusL',                'Right-Thalamus'               :'thalamusR',
#                 'Left-Caudate'                :'caudate_lh',               'Right-Caudate'                :'caudate_rh',
#                 'Left-Putamen'                :'putamen_lh',               'Right-Putamen'                :'putamen_rh',
#                 'Left-Pallidum'               :'pallidum_lh',              'Right-Pallidum'               :'pallidum_rh',
#                 'Left-Hippocampus'            :'hippocampus_lh',           'Right-Hippocampus'            :'hippocampus_rh',
#                 'Left-Amygdala'               :'amygdala_lh',              'Right-Amygdala'               :'amygdala_rh',
#                 'Left-Accumbens-area'         :'accumbensArea_lh',         'Right-Accumbens-area'         :'accumbensArea_rh',
#                 'Left-Lateral-Ventricle'      :'ventricleLateral_lh',      'Right-Lateral-Ventricle'      :'ventricleLateral_rh',
#                 'Left-Inf-Lat-Vent'           :'ventricleInfLateral_lh',   'Right-Inf-Lat-Vent'           :'ventricleInfLateral_rh',
#                 'Left-Cerebellum-White-Matter':'cerebellumWhiteMatter_lh', 'Right-Cerebellum-White-Matter':'cerebellumWhiteMatter_rh',
#                 'Left-Cerebellum-Cortex'      :'cerebellumCortex_lh',      'Right-Cerebellum-Cortex'      :'cerebellumCortex_rh',
#                 'Left-VentralDC'              :'ventralDC_lh',             'Right-VentralDC'              :'ventralDC_rh',
#                 'Left-vessel'                 :'vessel_lh',                'Right-vessel'                 :'vessel_rh',
#                 'Left-choroid-plexus'         :'choroidPlexus_lh',         'Right-choroid-plexus'         :'choroidPlexus_rh',
#                 'Left-WM-hypointensities'     :'wm_hypointensities_lh',    'Right-WM-hypointensities'     :'WMhypointensities_rh',
#                 'Left-non-WM-hypointensities' :'nonWMhypointensities_lh',  'Right-non-WM-hypointensities' :'nonWMhypointensities_rh',                
#                 'lhCortexVol'                 :'volCortex_lh',             'rhCortexVol'                  :'volCortex_rh',
#                 'lhCerebralWhiteMatterVol'    :'volCerebralWhiteMatter_lh','rhCerebralWhiteMatterVol'     :'volCerebralWhiteMatter_rh',
#                 'lhSurfaceHoles'              :'surfaceHoles_lh',          'rhSurfaceHoles'               :'surfaceHoles_rh',
#                 '3rd-Ventricle':'ventricle_3rd',
#                 '4th-Ventricle':'ventricle_4th',
#                 '5th-Ventricle':'ventricle_5th',
#                 'VentricleChoroidVol':'volVentricleChoroid',
#                 'Brain-Stem':'brainstem', 'CSF':'csf', 'Optic-Chiasm':'opticChiasm',
#                 'CC_Posterior':'ccPosterior','CC_Mid_Posterior':'ccMidPosterior',
#                 'CC_Central':'ccCentral',    'CC_Mid_Anterior':'ccMidAnterior',  'CC_Anterior':'ccAnterior',
#                 'CortexVol'                  :'volCortex',
#                 'SubCortGrayVol'             :'volSubCortGray',
#                 'TotalGrayVol'               :'volTotalGray',
#                 'BrainSegVol'                :'volBrainSeg',
#                 'BrainSegVolNotVent'         :'volBrainSegNotVent',
#                 'BrainSegVolNotVentSurf'     :'volBrainSegNotVentSurf',
#                 'BrainSegVol-to-eTIV'        :'volBrainSegtoeTIV',
#                 'CerebralWhiteMatterVol'     :'volCerebralWhiteMatter',
#                 'SupraTentorialVol'          :'volSupraTentorial',
#                 'SupraTentorialVolNotVent'   :'volSupraTentorialNotVent',
#                 'SupraTentorialVolNotVentVox':'volSupraTentorialNotVentVox',
#                 'WM-hypointensities'         :'wm_hypointensities',
#                 'non-WM-hypointensities'     :'nonWMhypointensities',
#                 'SurfaceHoles'               :'surfaceHoles',
#                 'MaskVol'                    :'volMask',
#                 'MaskVol-to-eTIV'            :'volMasktoeTIV',
#                 'eTIV'                       :'eTIV',
#                 'bankssts':'temporal_superior_sulcus_bank',
#                 'caudalanteriorcingulate':'cingulate_anterior_caudal',
#                 'caudalmiddlefrontal':'frontal_middle_caudal',
#                 'cuneus':'occipital_cuneus',
#                 'entorhinal':'temporal_entorhinal',
#                 'fusiform':'temporal_fusiform',
#                 'inferiorparietal':'parietal_inferior',
#                 'inferiortemporal':'temporal_inferior',
#                 'isthmuscingulate':'cingulate_isthmus',
#                 'lateraloccipital':'occipital_lateral',
#                 'lateralorbitofrontal':'frontal_orbitolateral',
#                 'lingual':'occipital_lingual',
#                 'medialorbitofrontal':'frontal_orbitomedial',
#                 'middletemporal':'temporal_middle',
#                 'parahippocampal':'temporal_parahippocampal',
#                 'paracentral':'frontal_paracentral',
#                 'parsopercularis':'frontal_parsopercularis',
#                 'parsorbitalis':'frontal_parsorbitalis',
#                 'parstriangularis':'frontal_parstriangularis',
#                 'pericalcarine':'occipital_pericalcarine',
#                 'postcentral':'parietal_postcentral',
#                 'posteriorcingulate':'cingulate_posterior',
#                 'precentral':'frontal_precentral',
#                 'precuneus':'parietal_precuneus',
#                 'rostralanteriorcingulate':'cingulate_anterior_rostral',
#                 'rostralmiddlefrontal':'frontal_middle_rostral',
#                 'superiorfrontal':'frontal_superior',
#                 'superiorparietal':'parietal_superior',
#                 'superiortemporal':'temporal_superior',
#                 'supramarginal':'parietal_supramarginal',
#                 'frontalpole':'frontal_pole',
#                 'temporalpole':'temporal_pole',
#                 'transversetemporal':'temporal_transverse',
#                 'insula':'insula',
#                 'Cortex_MeanThickness':'cortex_thickness',
#                 'Cortex_WhiteSurfArea':'cortex_area',
#                 'Cortex_CortexVol':'cortex_vol',
#                 'Cortex_NumVert':'cortex_numvert',
#                 'UnsegmentedWhiteMatter':'WMUnsegmented',
#                 'G&S_frontomargin': 'frontal_margin_GS',
#                 'G_and_S_frontomargin': 'frontal_margin_GS',
#                 'G&S_occipital_inf': 'occipital_inf_GS',
#                 'G_and_S_occipital_inf': 'occipital_inf_GS',
#                 'G&S_paracentral': 'frontal_paracentral_GS',
#                 'G_and_S_paracentral': 'frontal_paracentral_GS',
#                 'G&S_subcentral': 'frontal_subcentral_GS',
#                 'G_and_S_subcentral': 'frontal_subcentral_GS',
#                 'G&S_transv_frontopol': 'frontal_pol_transv_GS',
#                 'G_and_S_transv_frontopol': 'frontal_pol_transv_GS',
#                 'G&S_cingul-Ant': 'cingul_ant_GS',
#                 'G_and_S_cingul-Ant': 'cingul_ant_GS',
#                 'G&S_cingul-Mid-Ant': 'cingul_ant_mid_GS',
#                 'G_and_S_cingul-Mid-Ant': 'cingul_ant_mid_GS',
#                 'G&S_cingul-Mid-Post': 'cingul_Mid_Post_GS',
#                 'G_and_S_cingul-Mid-Post': 'cingul_Mid_Post_GS',
#                 'G_cingul-Post-dorsal': 'cingul_Post_dorsal_Gyr',
#                 'G_cingul-Post-ventral': 'cingul_Post_ventral_Gyr',
#                 'G_cuneus': 'occipital_cuneus_Gyr',
#                 'G_front_inf-Opercular': 'frontal_inf_Opercular_Gyr',
#                 'G_front_inf-Orbital': 'frontal_inf_Orbital_Gyr',
#                 'G_front_inf-Triangul': 'frontal_inf_Triangul_Gyr',
#                 'G_front_middle': 'frontal_middle_Gyr',
#                 'G_front_sup': 'frontal_sup_Gyr',
#                 'G_Ins_lg_and_S_cent_ins': 'insula_lg_S_cent_ins_Gyr',
#                 'G_insular_short': 'insular_short_Gyr',
#                 'G_occipital_middle': 'occipital_middle_Gyr',
#                 'G_occipital_sup': 'occipital_sup_Gyr',
#                 'G_oc-temp_lat-fusifor': 'temporal_lat_fusifor_Gyr',
#                 'G_oc-temp_med-Lingual': 'temporal_med_Lingual_Gyr',
#                 'G_oc-temp_med-Parahip': 'temporal_med_Parahip_Gyr',
#                 'G_orbital': 'frontal_orbital_Gyr',
#                 'G_pariet_inf-Angular': 'pariet_inf_Angular_Gyr',
#                 'G_pariet_inf-Supramar': 'pariet_inf_Supramar_Gyr',
#                 'G_parietal_sup': 'parietal_sup_Gyr',
#                 'G_postcentral': 'parietal_postcentral_Gyr',
#                 'G_precentral': 'frontal_precentral_Gyr',
#                 'G_precuneus': 'parietal_precuneus_Gyr',
#                 'G_rectus': 'rectus_Gyr',
#                 'G_subcallosal': 'cc_subcallosal_Gyr',
#                 'G_temp_sup-G_T_transv': 'temp_sup_G_T_transv_Gyr',
#                 'G_temp_sup-Lateral': 'temp_sup_Lateral_Gyr',
#                 'G_temp_sup-Plan_polar': 'temp_sup_Plan_polar_Gyr',
#                 'G_temp_sup-Plan_tempo': 'temp_sup_Plan_tempo_Gyr',
#                 'G_temporal_inf': 'temporal_inf_Gyr',
#                 'G_temporal_middle': 'temporal_middle_Gyr',
#                 'Lat_Fis-ant-Horizont': 'lat_Fis_ant_Horizont',
#                 'Lat_Fis-ant-Vertical': 'lat_Fis_ant_Vertical',
#                 'Lat_Fis-post': 'lat_Fis_post',
#                 'Pole_occipital': 'occipital_Pole',
#                 'Pole_temporal': 'temporal_pole',
#                 'S_calcarine': 'occipital_calcarine_Sulc',
#                 'S_central': 'frontal_central_Sulc',
#                 'S_cingul-Marginalis': 'cingul_Marginalis_Sulc',
#                 'S_circular_insula_ant': 'insula_circular_ant_Sulc',
#                 'S_circular_insula_inf': 'insula_circular_inf_Sulc',
#                 'S_circular_insula_sup': 'insula__circular_sup_Sulc',
#                 'S_collat_transv_ant': 'collat_transv_ant_Sulc',
#                 'S_collat_transv_post': 'collat_transv_post_Sulc',
#                 'S_front_inf': 'front_inf_Sulc',
#                 'S_front_middle': 'front_middle_Sulc',
#                 'S_front_sup': 'front_sup_Sulc',
#                 'S_interm_prim-Jensen': 'interm_prim_Jensen_Sulc',
#                 'S_intrapariet_and_P_trans': 'intrapariet_P_trans_Sulc',
#                 'S_oc_middle_and_Lunatus': 'occipital_middle_Lunatus_Sulc',
#                 'S_oc_sup_and_transversal': 'occipital_sup_transversal_Sulc',
#                 'S_occipital_ant': 'occipital_ant_Sulc',
#                 'S_oc-temp_lat': 'occipital_temp_lat_Sulc',
#                 'S_oc-temp_med_and_Lingual': 'occipital_temp_med_Lingual_Sulc',
#                 'S_orbital_lateral': 'frontal_orbital_lateral_Sulc',
#                 'S_orbital_med-olfact': 'frontal_orbital_med_olfact_Sulc',
#                 'S_orbital-H_Shaped': 'frontal_orbital_H_Shaped_Sulc',
#                 'S_parieto_occipital': 'parieto_occipital_Sulc',
#                 'S_pericallosal': 'cc_pericallosal_Sulc',
#                 'S_postcentral': 'parietal_postcentral_Sulc',
#                 'S_precentral-inf-part': 'frontal_precentral_inf_part_Sulc',
#                 'S_precentral-sup-part': 'frontal_precentral_sup_part_Sulc',
#                 'S_suborbital': 'frontal_suborbital_Sulc',
#                 'S_subparietal': 'parietal_subparietal_Sulc',
#                 'S_temporal_inf': 'temporal_inf_Sulc',
#                 'S_temporal_sup': 'temporal_sup_Sulc',
#                 'S_temporal_transverse': 'temporal_transverse_Sulc'},

# }






# BrStem_Hip_f2rd_stats={'Brainstem':'aseg.brainstem.volume.stats','HIPL':'aseg.hippo.lh.volume.stats',
#                  'HIPR':'aseg.hippo.rh.volume.stats'}
# BrStem_Hip_f2rd={'Brainstem':'brainstemSsVolumes.v10.txt','HIPL':'lh.hippoSfVolumes-T1.v10.txt',
#                  'HIPR':'rh.hippoSfVolumes-T1.v10.txt'}

# brstem_hip_header = {
#     'all':{'Medulla':'medulla','Pons':'pons','SCP':'scp','Midbrain':'midbrain',
#             'Whole_brainstem':'wholeBrainstem','Hippocampal_tail':'hippocampal-tail',
#             'subiculum':'subiculum','subiculum-body':'subiculum-body','subiculum-head':'subiculum-head',
#             'CA1':'ca1','CA1-body':'ca1-body','CA1-head':'ca1-head','hippocampal-fissure':'hippocampal-fissure',
#             'presubiculum':'presubiculum','presubiculum-body':'presubiculum-body','presubiculum-head':'presubiculum-head',
#             'parasubiculum':'parasubiculum',
#             'molecular_layer_HP':'molecularLayerHP','molecular_layer_HP-head':'molecularLayerHP-head','molecular_layer_HP-body':'molecularLayerHP-body',
#             'GC-ML-DG':'gcmldg','GC-ML-DG-body':'gcmldg-body','GC-ML-DG-head':'gcmldg-head',
#             'CA3':'ca3','CA3-body':'ca3-body','CA3-head':'ca3-head',
#             'CA4':'ca4','CA4-body':'ca4-body','CA4-head':'ca4-head',
#             'fimbria':'fimbria','HATA':'hata','Whole_hippocampal_body':'wholeHippocampus-body','Whole_hippocampal_head':'wholeHippocampus-head',
#             'Whole_hippocampus':'wholeHippocampus',
#             'Lateral-nucleus': 'Lateral-nucleus', 'Basal-nucleus': 'Basal-nucleus', 'Accessory-Basal-nucleus': 'Accessory-Basal-nucleus',
#             'Anterior-amygdaloid-area-AAA': 'Anterior-amygdaloid-area-AAA', 'Central-nucleus': 'Central-nucleus',
#             'Medial-nucleus': 'Medial-nucleus', 'Cortical-nucleus': 'Cortical-nucleus',
#             'Corticoamygdaloid-transitio': 'Corticoamygdaloid-transitio', 'Paralaminar-nucleus': 'Paralaminar-nucleus',
#             'Whole_amygdala': 'WholeAmygdala',
#             'AV': 'AV', 'CeM': 'CeM', 'CL': 'CL', 'CM': 'CM', 'LD': 'LD', 'LGN': 'LGN', 'LP': 'LP', 'L-Sg': 'L-Sg',
#             'MDl': 'MDl', 'MDm': 'MDm', 'MGN': 'MGN', 'MV(Re)': 'MV(Re)', 'Pc': 'Pc', 'Pf': 'Pf', 'Pt': 'Pt', 'PuA': 'PuA',
#             'PuI': 'PuI', 'PuL': 'PuL', 'PuM': 'PuM', 'VA': 'VA', 'VAmc': 'VAmc', 'VLa': 'VLa', 'VLp': 'VLp', 'VM': 'VM',
#             'VPL': 'VPL', 'Whole_thalamus': 'WholeThalamus'},
#     'Brainstem':['Medulla','Pons','SCP','Midbrain','Whole_brainstem',],
#     'HIPL':['Hippocampal_tail','subiculum','CA1','hippocampal-fissure',
#             'presubiculum','parasubiculum','molecular_layer_HP','GC-ML-DG',
#             'CA3','CA4','fimbria','HATA','Whole_hippocampus'],
#     'HIPR':['Hippocampal_tail','subiculum','CA1','hippocampal-fissure',
#             'presubiculum','parasubiculum','molecular_layer_HP','GC-ML-DG',
#             'CA3','CA4','fimbria','HATA','Whole_hippocampus'],}


# columns_main_DK_order = ('VolSeg','VolL_DK', 'VolR_DK', 'ThickL_DK', 'ThickR_DK', 'AreaL_DK', 'AreaR_DK', 'CurvL_DK', 'CurvR_DK',
#                      'NumVertL_DK','NumVertR_DK','FoldIndL_DK','FoldIndR_DK', 'CurvIndL_DK', 'CurvIndR_DK',
#                      'CurvGausL_DK','CurvGausR_DK', 'VolSegWM_DK',
#                      'ThickStdL_DS',  'ThickStdR_DS', 'eTIV')
# columns_main_DS_order = ('VolL_DS', 'VolR_DS','ThickL_DS', 'ThickR_DS', 'AreaL_DS', 'AreaR_DS', 'CurvL_DS', 'CurvR_DS',
#                      'NumVertL_DS', 'NumVertR_DS', 'FoldIndL_DS','FoldIndR_DS','CurvIndL_DS','CurvIndR_DS',
#                      'CurvGausL_DS','CurvGausR_DS',
#                       'ThickStdL_DS',  'ThickStdR_DS',)
# columns_secondary_order = ('VolSegWM_DK','VolSegNVoxels', 'VolSegnormMean', 'VolSegnormStdDev', 'VolSegnormMin',
#                      'NumVertL_DS', 'ThickStdL_DS', 'CurvIndL_DS', 'FoldIndL_DS', 'NumVertR_DS', 'ThickStdR_DS',
#                      'CurvGausR_DS', 'CurvIndR_DS', 'FoldIndR_DS', 'VolSegWMNVoxels_DK', 'VolSegWMnormMean_DK',
#                      'VolSegWMnormStdDev_DK', 'VolSegWMnormMin_DK', 'VolSegWMnormMax_DK', 'VolSegWMnormRange_DK')

# segmentation_parameters = ('Volume_mm3','NVoxels','normMean','normStdDev','normMin','normMax','normRange')
# segmentations_header = {'Left-Lateral-Ventricle':'ventricleLateralL','Left-Inf-Lat-Vent':'ventricleInfLateralL',
#                         'Left-Cerebellum-White-Matter':'cerebellumWhiteMatterL','Left-Cerebellum-Cortex':'cerebellumCortexL',
#                         'Left-Thalamus':'thalamusL','Left-Thalamus-Proper':'thalamusProperL','Left-Caudate':'caudateL','Left-Putamen':'putamenL',
#                         'Left-Pallidum':'pallidumL','3rd-Ventricle':'ventricle_3rd','4th-Ventricle':'ventricle_4th',
#                         'Brain-Stem':'brainstem','Left-Hippocampus':'hippocampusL','Left-Amygdala':'amygdalaL',
#                         'CSF':'csf','Left-Accumbens-area':'accumbensAreaL','Left-VentralDC':'ventralDCL',
#                         'Left-vessel':'vesselL','Left-choroid-plexus':'choroidPlexusL','Right-Lateral-Ventricle':'ventricleLateralR',
#                             'Right-Inf-Lat-Vent':'ventricleInfLateralR','Right-Cerebellum-White-Matter':'cerebellumWhiteMatterR',
#                             'Right-Cerebellum-Cortex':'cerebellumCortexR','Right-Thalamus-Proper':'thalamusProperR','Right-Thalamus':'thalamusR',
#                             'Right-Caudate':'caudateR','Right-Putamen':'putamenR','Right-Pallidum':'pallidumR',
#                             'Right-Hippocampus':'hippocampusR','Right-Amygdala':'amygdalaR','Right-Accumbens-area':'accumbensAreaR',
#                             'Right-VentralDC':'ventralDCR','Right-vessel':'vesselR','Right-choroid-plexus':'choroidPlexusR',
#                             '5th-Ventricle':'ventricle_5th','WM-hypointensities':'wm_hypointensities','Left-WM-hypointensities':'wm_hypointensitiesL',
#                             'Right-WM-hypointensities':'WMhypointensitiesR','non-WM-hypointensities':'nonWMhypointensities',
#                             'Left-non-WM-hypointensities':'nonWMhypointensitiesL','Right-non-WM-hypointensities':'nonWMhypointensitiesR',
#                             'Optic-Chiasm':'opticChiasm','CC_Posterior':'ccPosterior','CC_Mid_Posterior':'ccMidPosterior',
#                             'CC_Central':'ccCentral','CC_Mid_Anterior':'ccMidAnterior','CC_Anterior':'ccAnterior','BrainSegVol':'volBrainSeg',
#                             'BrainSegVolNotVent':'volBrainSegNotVent','BrainSegVolNotVentSurf':'volBrainSegNotVentSurf',
#                             'VentricleChoroidVol':'volVentricleChoroid','lhCortexVol':'volCortexL',
#                             'rhCortexVol':'volCortexR','CortexVol':'volCortex','lhCerebralWhiteMatterVol':'volCerebralWhiteMatterL',
#                             'rhCerebralWhiteMatterVol':'volCerebralWhiteMatterR','CerebralWhiteMatterVol':'volCerebralWhiteMatter',
#                             'SubCortGrayVol':'volSubCortGray','TotalGrayVol':'volTotalGray','SupraTentorialVol':'volSupraTentorial',
#                             'SupraTentorialVolNotVent':'volSupraTentorialNotVent','SupraTentorialVolNotVentVox':'volSupraTentorialNotVentVox',
#                             'MaskVol':'volMask','BrainSegVol-to-eTIV':'volBrainSegtoeTIV','MaskVol-to-eTIV':'volMasktoeTIV',
#                             'lhSurfaceHoles':'surfaceHolesL','rhSurfaceHoles':'surfaceHolesR','SurfaceHoles':'surfaceHoles','eTIV':'eTIV'}


# parc_parameters= {'ThickAvg':'Thick','SurfArea':'Area',
#                   'GrayVol':'Vol','MeanCurv':'Curv',
#                   'NumVert':'NumVert','ThickStd':'ThickStd',
#                   'GausCurv':'CurvGaus','CurvInd':'CurvInd',
#                   'FoldInd':'FoldInd'}
# parc_DK_header={'bankssts':'temporal_superior_sulcus_bank','caudalanteriorcingulate':'cingulate_anterior_caudal','caudalmiddlefrontal':'frontal_middle_caudal',
#             'cuneus':'occipital_cuneus','entorhinal':'temporal_entorhinal','fusiform':'temporal_fusiform','inferiorparietal':'parietal_inferior',
#             'inferiortemporal':'temporal_inferior','isthmuscingulate':'cingulate_isthmus','lateraloccipital':'occipital_lateral',
#             'lateralorbitofrontal':'frontal_orbitolateral','lingual':'occipital_lingual','medialorbitofrontal':'frontal_orbitomedial',
#             'middletemporal':'temporal_middle','parahippocampal':'temporal_parahippocampal','paracentral':'frontal_paracentral',
#             'parsopercularis':'frontal_parsopercularis','parsorbitalis':'frontal_parsorbitalis','parstriangularis':'frontal_parstriangularis',
#             'pericalcarine':'occipital_pericalcarine','postcentral':'parietal_postcentral','posteriorcingulate':'cingulate_posterior',
#             'precentral':'frontal_precentral','precuneus':'parietal_precuneus','rostralanteriorcingulate':'cingulate_anterior_rostral',
#             'rostralmiddlefrontal':'frontal_middle_rostral','superiorfrontal':'frontal_superior','superiorparietal':'parietal_superior',
#             'superiortemporal':'temporal_superior','supramarginal':'parietal_supramarginal',
#             'frontalpole':'frontal_pole',
#             'temporalpole':'temporal_pole','transversetemporal':'temporal_transverse','insula':'insula','Cortex_MeanThickness':'cortex_thickness',
#             'Cortex_WhiteSurfArea':'cortex_area','Cortex_CortexVol':'cortex_vol',
#             'Cortex_NumVert':'cortex_numvert',
#             'UnsegmentedWhiteMatter':'WMUnsegmented',}
# parc_DS_header={'G&S_frontomargin': 'frontal_margin_GS',
#                 'G_and_S_frontomargin': 'frontal_margin_GS',
#                 'G&S_occipital_inf': 'occipital_inf_GS',
#                 'G_and_S_occipital_inf': 'occipital_inf_GS',
#                 'G&S_paracentral': 'frontal_paracentral_GS',
#                 'G_and_S_paracentral': 'frontal_paracentral_GS',
#                 'G&S_subcentral': 'frontal_subcentral_GS',
#                 'G_and_S_subcentral': 'frontal_subcentral_GS',
#                 'G&S_transv_frontopol': 'frontal_pol_transv_GS',
#                 'G_and_S_transv_frontopol': 'frontal_pol_transv_GS',
#                 'G&S_cingul-Ant': 'cingul_ant_GS',
#                 'G_and_S_cingul-Ant': 'cingul_ant_GS',
#                 'G&S_cingul-Mid-Ant': 'cingul_ant_mid_GS',
#                 'G_and_S_cingul-Mid-Ant': 'cingul_ant_mid_GS',
#                 'G&S_cingul-Mid-Post': 'cingul_Mid_Post_GS',
#                 'G_and_S_cingul-Mid-Post': 'cingul_Mid_Post_GS',
#                 'G_cingul-Post-dorsal': 'cingul_Post_dorsal_Gyr',
#                 'G_cingul-Post-ventral': 'cingul_Post_ventral_Gyr',
#                 'G_cuneus': 'occipital_cuneus_Gyr',
#                 'G_front_inf-Opercular': 'frontal_inf_Opercular_Gyr',
#                 'G_front_inf-Orbital': 'frontal_inf_Orbital_Gyr',
#                 'G_front_inf-Triangul': 'frontal_inf_Triangul_Gyr',
#                 'G_front_middle': 'frontal_middle_Gyr',
#                 'G_front_sup': 'frontal_sup_Gyr',
#                 'G_Ins_lg_and_S_cent_ins': 'insula_lg_S_cent_ins_Gyr',
#                 'G_insular_short': 'insular_short_Gyr',
#                 'G_occipital_middle': 'occipital_middle_Gyr',
#                 'G_occipital_sup': 'occipital_sup_Gyr',
#                 'G_oc-temp_lat-fusifor': 'temporal_lat_fusifor_Gyr',
#                 'G_oc-temp_med-Lingual': 'temporal_med_Lingual_Gyr',
#                 'G_oc-temp_med-Parahip': 'temporal_med_Parahip_Gyr',
#                 'G_orbital': 'frontal_orbital_Gyr',
#                 'G_pariet_inf-Angular': 'pariet_inf_Angular_Gyr',
#                 'G_pariet_inf-Supramar': 'pariet_inf_Supramar_Gyr',
#                 'G_parietal_sup': 'parietal_sup_Gyr',
#                 'G_postcentral': 'parietal_postcentral_Gyr',
#                 'G_precentral': 'frontal_precentral_Gyr',
#                 'G_precuneus': 'parietal_precuneus_Gyr',
#                 'G_rectus': 'rectus_Gyr',
#                 'G_subcallosal': 'cc_subcallosal_Gyr',
#                 'G_temp_sup-G_T_transv': 'temp_sup_G_T_transv_Gyr',
#                 'G_temp_sup-Lateral': 'temp_sup_Lateral_Gyr',
#                 'G_temp_sup-Plan_polar': 'temp_sup_Plan_polar_Gyr',
#                 'G_temp_sup-Plan_tempo': 'temp_sup_Plan_tempo_Gyr',
#                 'G_temporal_inf': 'temporal_inf_Gyr',
#                 'G_temporal_middle': 'temporal_middle_Gyr',
#                 'Lat_Fis-ant-Horizont': 'lat_Fis_ant_Horizont',
#                 'Lat_Fis-ant-Vertical': 'lat_Fis_ant_Vertical',
#                 'Lat_Fis-post': 'lat_Fis_post',
#                 'Pole_occipital': 'occipital_Pole',
#                 'Pole_temporal': 'temporal_pole',
#                 'S_calcarine': 'occipital_calcarine_Sulc',
#                 'S_central': 'frontal_central_Sulc',
#                 'S_cingul-Marginalis': 'cingul_Marginalis_Sulc',
#                 'S_circular_insula_ant': 'insula_circular_ant_Sulc',
#                 'S_circular_insula_inf': 'insula_circular_inf_Sulc',
#                 'S_circular_insula_sup': 'insula__circular_sup_Sulc',
#                 'S_collat_transv_ant': 'collat_transv_ant_Sulc',
#                 'S_collat_transv_post': 'collat_transv_post_Sulc',
#                 'S_front_inf': 'front_inf_Sulc',
#                 'S_front_middle': 'front_middle_Sulc',
#                 'S_front_sup': 'front_sup_Sulc',
#                 'S_interm_prim-Jensen': 'interm_prim_Jensen_Sulc',
#                 'S_intrapariet_and_P_trans': 'intrapariet_P_trans_Sulc',
#                 'S_oc_middle_and_Lunatus': 'occipital_middle_Lunatus_Sulc',
#                 'S_oc_sup_and_transversal': 'occipital_sup_transversal_Sulc',
#                 'S_occipital_ant': 'occipital_ant_Sulc',
#                 'S_oc-temp_lat': 'occipital_temp_lat_Sulc',
#                 'S_oc-temp_med_and_Lingual': 'occipital_temp_med_Lingual_Sulc',
#                 'S_orbital_lateral': 'frontal_orbital_lateral_Sulc',
#                 'S_orbital_med-olfact': 'frontal_orbital_med_olfact_Sulc',
#                 'S_orbital-H_Shaped': 'frontal_orbital_H_Shaped_Sulc',
#                 'S_parieto_occipital': 'parieto_occipital_Sulc',
#                 'S_pericallosal': 'cc_pericallosal_Sulc',
#                 'S_postcentral': 'parietal_postcentral_Sulc',
#                 'S_precentral-inf-part': 'frontal_precentral_inf_part_Sulc',
#                 'S_precentral-sup-part': 'frontal_precentral_sup_part_Sulc',
#                 'S_suborbital': 'frontal_suborbital_Sulc',
#                 'S_subparietal': 'parietal_subparietal_Sulc',
#                 'S_temporal_inf': 'temporal_inf_Sulc',
#                 'S_temporal_sup': 'temporal_sup_Sulc',
#                 'S_temporal_transverse': 'temporal_transverse_Sulc'}





# def get_names_of_structures():
#     name_structures = list()

#     for val in segmentations_header:
#         name_structures.append(segmentations_header[val])
#     for val in parc_DK_header:
#         name_structures.append(parc_DK_header[val])
#     for val in brstem_hip_header['all']:
#         name_structures.append(brstem_hip_header['all'][val])
#     for val in parc_DS_header:
#         name_structures.append(parc_DS_header[val])

#     return name_structures

# name_structures = get_names_of_structures()



# def get_names_of_measurements():
#     name_measurement = ['Brainstem','HIPL','HIPR',]

#     for val in segmentation_parameters:
#         name_measurement.append('VolSeg'+val.replace('Volume_mm3',''))
#         name_measurement.append('VolSegWM'+val.replace('Volume_mm3','')+'_DK')

#     for hemi in ('L','R',):
#         for atlas in ('_DK','_DS',):
#             for meas in parc_parameters:
#                 name_measurement.append(parc_parameters[meas]+hemi+atlas)

#     return name_measurement

# name_measurement = get_names_of_measurements()



# def get_atlas_measurements():
#     measurements = {}
#     for meas in parc_parameters:
#         measurements[parc_parameters[meas]] = list()
#         for atlas in ('_DK','_DS',):
#             measurements[parc_parameters[meas]].append(parc_parameters[meas]+'L'+atlas)
#             measurements[parc_parameters[meas]].append(parc_parameters[meas]+'R'+atlas)
#     return measurements


# class cols_per_measure_per_atlas():

#     def __init__(self, ls_columns):
#         self.ls_columns = ls_columns
#         self.cols_to_meas_to_atlas = self.get_columns()

#     def get_columns(self):
#         result = dict()

#         for atlas in all_data['atlases']:
#             result[atlas] = dict()
#             for meas in all_data[atlas]['parameters']:
#                 result[atlas][meas] = list()

#         for col in self.ls_columns:
#             for atlas in all_data['atlases']:
#                 for meas in all_data[atlas]['parameters']:
#                     if all_data[atlas]['parameters'][meas] in col and all_data['atlas_ending'][atlas] in col:
#                         result[atlas][meas].append(self.ls_columns.index(col))
#         return result

# class GetFSStructureMeasurement:
#     def __init__(self):
#         self.ls_meas   = get_names_of_measurements()
#         self.ls_struct = get_names_of_structures()

#     def get(self, name, ls_err = list()):
#         meas_try1   = name[name.rfind('_')+1:]
#         struct_try1 = name.replace(f'_{meas_try1}','')
#         if struct_try1 in self.ls_struct and meas_try1 in self.ls_meas:
#             return meas_try1, struct_try1, ls_err
#         elif name == 'eTIV':
#             return 'eTIV', 'eTIV', ls_err
#         else:
#             measurement = name
#             structure = name
#             i = 0
#             while structure not in self.ls_struct and i<5:
#                 if measurement not in self.ls_meas:
#                     for meas in self.ls_meas:
#                         if meas in name:
#                             measurement = meas
#                             break
#                 else:
#                     self.ls_meas = self.ls_meas[self.ls_meas.index(measurement)+1:]
#                     for meas in self.ls_meas:
#                         if meas in name:
#                             measurement = meas
#                             break
#                 structure = name.replace('_'+measurement,'')
#                 i += 1
#             if f'{structure}_{measurement}' != name:
#                     ls_err.append(name)
#             return measurement, structure, ls_err



# suggested_times = {
#         'registration':'01:00:00',
#         'recon'       :'30:00:00',
#         'recbase'     :'30:00:00',
#         'reclong'     :'23:00:00',
#         'masks'       :'12:00:00',
#         'archiving'   :'01:00:00',
#         'autorecon1'  :'05:00:00',
#         'autorecon2'  :'12:00:00',
#         'autorecon3'  :'12:00:00',
#         'qcache'      :'03:00:00',
#         'brstem'      :'03:00:00',
#         'hip'         :'03:00:00',
#         'tha'         :'03:00:00',
#         'hypotha'     :'03:00:00',
#         }