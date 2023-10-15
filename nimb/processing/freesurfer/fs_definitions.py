#!/bin/python
# 2021.11.10
from os import path
import os

hemi = ['lh','rh']

def fs_version(fs_home,
               user_fs_version = None):
    """get FreeSurfer version from builld file
    Args:
        fs_home: path to FreeSurfer installation
    Return:
        version: str() 0.0.0, FreeSurfer version in a 3 values format devided by comma
        opsys: str() Operating system used for FreeSurfer as per installation file
    """
    build_file = os.path.join(fs_home, "build-stamp.txt")
    version = None
    opsys = None
    user_sys_ver_similar = True
    if os.path.exists(build_file):
        print("reading build file for FreeSurfer at: ", build_file)
        content = open(build_file, "r").readlines()[0].strip("\n").split("-")
        opsys, version = content[2], content[3]
        version_2numbers = version.replace(".","")[:2]
    else:
        print("build file for FreeSurfer is missing at: ", build_file)

    if user_fs_version:
        if user_fs_version != version:
            user_sys_ver_similar = False

    return version, opsys, version_2numbers, user_sys_ver_similar


class FSProcesses:
    def __init__(self,
                 fs_home,
                 freesurfer_version = None):
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
                        "files_2chk":['surf/lh.white.preaparc.H',
                                      'surf/rh.white.preaparc.H',],
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
                        "cmd"    :"segmentBS.sh",
                        "cmd6"   :"brainstem-structures",
                        "s_param":"",
                        "run_step":5,
                        "isrun_f":"IsRunningBSsubst",
                        "time_suggested":'03:00:00'},
            "hip"       :{
                        "fsver"  :6,
                        "log"    :"hippocampal-subfields-T1.log",
                        "group"  :"atlas",
                        "atlas_2chk": ['HIP', 'AMY'],
                        "cmd"    :"segmentHA_T1.sh",
                        "cmd6"   :"hippocampal-subfields-T1",
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
                        "time_suggested":'03:00:00'}}#,
            # "hypotha"   :{
            #             "fsver"  :73,
            #             "log"    :"thalamic-nuclei-mainFreeSurferT1.log",
            #             "group"  :"atlas",
            #             "atlas_2chk": ['HypoTHA'],
            #             "cmd"    :"mri_segment_hypothalamic_subunits",
            #             "s_param":"--s",
            #             "run_step":8,
            #             "isrun_f":"IsRunningHypoThalamicNuclei_mainFreeSurferT1",
            #             "time_suggested":'01:00:00'}}

        self.recons   = [i for i in self.processes if "recon" in self.processes[i]["group"]]
        self.atlas_proc = [i for i in self.processes if "atlas" in self.processes[i]["group"]]
        self.IsRunning_files = [self.processes[i]["isrun_f"] for i in self.atlas_proc] +\
                                [self.processes["autorecon1"]["isrun_f"]]
        # self.fs_ver2 = FreeSurferVersion(freesurfer_version).fs_ver2() #!!!! Obsolete
        version, _, self.fs_ver2nr, _ = fs_version(fs_home, freesurfer_version)

    def log(self, process):
        if process in self.recons:
            file = 'recon-all.log'
        elif self.fs_ver2nr == 6 and "log6" in self.processes[process]:
            file = self.processes[process]["log6"]
        else:
            file = self.processes[process]["log"]
        return os.path.join('scripts', file)

    def process_order(self):
        order_all = sorted(self.processes, key=lambda k: self.processes[k]["run_step"])
        if self.fs_ver2nr < "7":
            fs7_atlases = [i for i in self.atlas_proc if self.processes[i]["fsver"] > 6]
            return [i for i in order_all if i not in fs7_atlases]
        elif self.fs_ver2nr.replace(".","") < "72":
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
            return f"python run_masks.py {_id}"

    def cmd_atlas(self, process, _id):
        if self.fs_ver2nr < "7":
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
            'registration'  :'01:00:00',
            'recon'         :'30:00:00',
            'recbase'       :'30:00:00',
            'reclong'       :'23:00:00',
            'masks'         :'12:00:00',
            'archiving'     :'01:00:00',
            'fs_glm'        :'23:00:00',
            'moving'        :'01:00:00',
            'glm_preproc'   :'03:00:00',
            'glmfit'        :'03:00:00',
            'glmfit-sim'    :'10:00:00',
            'glm_montecarlo':'02:00:00',}
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
            'g1v0':{'intercept.mtx'     :['1',          't-test with intercept>0 being positive; is the intercept/mean equal to 0?']},
            'g1v1':{'intercept.mtx'     :['1 0',        't-test with intercept>0 being positive; is the intercept equal to 0? Does the average thickness differ from zero ?'],
                    'slope.mtx'         :['0 1',        'does the correlation between thickness and variable differ from zero ? is the slope equal to 0? contrast: 0 1; t-test with the slope>0 being positive'],},
            'g2v0':{'group.diff.mtx'    :['1 -1',       'is there a difference between groups? Is there a difference between the group intercepts? contrast 1 -1; t-test with Group1>Group2 being positive',],
                    'group1.mtx'        :['1 0',        't-test with Group1>0 being positive; is there a main effect of Group1? Does the mean of Group1 equal 0? Does the average thickness differ from zero ?',],
                    'group2.mtx'        :['0 1',        't-test with Group2>0 being positive; is there a main effect of Group2? Does the mean of Group2 equal 0? Does the correlation between thickness and group differ from zero ?',],
                    'g1g2.intercept.mtx':['0.5 0.5',    't-test with (Group1+Group2)/2 > 0 being positive (red/yellow). If the mean is < 0, then it will be displayed in blue/cyan; does mean of the group means differ from 0?']},
            'g2v1':{'group-x-var.mtx'   :['0 0 1 -1',   'is there a difference between the group VARiable slopes? contrast 0 0 1 -1; t-test with Group1>Group2 being positive; Note: this is an interaction between group and VARiable',],
                    'group.diff.mtx'    :['1 -1 0 0',   'is there a difference between groups regressing out the effect of VARiable? Is there a difference between the group intercepts? Is there a difference between groups when the VARiable has the value 0? contrast 1 -1 0 0; t-test with Group1>Group2 being positive',],
                    'g1g2.var.mtx'      :['0 0 0.5 0.5','does mean of group VARiable slope differ from 0? Is there an average affect of VARiable regressing out the effect of group? contrast 0 0 0.5 -0.5; t-test with (Group1+Group2)/2 > 0 being positive'],
                    'g1g2.intercept.mtx':['0.5 0.5 0 0','t-test with (Group1+Group2)/2 > 0 being positive (red/yellow). If the mean is < 0, then it will be displayed in blue/cyan; does mean of group intercepts differ from 0? Is there an average main effect regressing out age?']},
            'g3v0':{
                    'group.effect_g1g2g3.mtx':['0.5 0.5 -1',     'is there an effect of group'],
                    'group.diff_g1g2.mtx'    :['1 -1 0',         'is there a difference between groups? Is there a difference between the group intercepts? contrast 1 -1; t-test with Group1>Group2 being positive'],
                    'group.diff_g1g3.mtx'    :['1 0 -1',         'is there a difference between groups? Is there a difference between the group intercepts? contrast 1 -1; t-test with Group1>Group2 being positive'],
                    'group.diff_g2g2.mtx'    :['0 1 -1',         'is there a difference between groups? Is there a difference between the group intercepts? contrast 1 -1; t-test with Group1>Group2 being positive'],},
            'g3v1':{
                    'group-x-var_g1g2.mtx'   :['0 0 0 1 -1 0',   'is there a difference between the group VARiable slopes? contrast 0 0 1 -1; t-test with Group1>Group2 being positive; Note: this is an interaction between group and VARiable',],
                    'group-x-var_g1g3.mtx'   :['0 0 0 1 0 -1',   'is there a difference between the group VARiable slopes? contrast 0 0 1 -1; t-test with Group1>Group2 being positive; Note: this is an interaction between group and VARiable',],
                    'group-x-var_g2g3.mtx'   :['0 0 0 0 1 -1',   'is there a difference between the group VARiable slopes? contrast 0 0 1 -1; t-test with Group1>Group2 being positive; Note: this is an interaction between group and VARiable',],
                    'group.diff_g1g2.mtx'    :['1 -1 0 0 0 0',   'is there a difference between groups regressing out the effect of VARiable? Is there a difference between the group intercepts? Is there a difference between groups when the VARiable has the value 0? contrast 1 -1 0 0; t-test with Group1>Group2 being positive',],
                    'group.diff_g1g3.mtx'    :['1 0 1 0 0 0',    'is there a difference between groups regressing out the effect of VARiable? Is there a difference between the group intercepts? Is there a difference between groups when the VARiable has the value 0? contrast 1 -1 0 0; t-test with Group1>Group2 being positive',],
                    'group.diff_g2g3.mtx'    :['0 1 -1 0 0 0',   'is there a difference between groups regressing out the effect of VARiable? Is there a difference between the group intercepts? Is there a difference between groups when the VARiable has the value 0? contrast 1 -1 0 0; t-test with Group1>Group2 being positive',],
                    'g1g2.var_g1g2.mtx'      :['0 0 0 0.5 0.5 0','does mean of group VARiable slope differ from 0? Is there an average affect of VARiable regressing out the effect of group? contrast 0 0 0.5 -0.5; t-test with (Group1+Group2)/2 > 0 being positive',],
                    'g1g2.var_g1g3.mtx'      :['0 0 0 0.5 0 0.5','does mean of group VARiable slope differ from 0? Is there an average affect of VARiable regressing out the effect of group? contrast 0 0 0.5 -0.5; t-test with (Group1+Group2)/2 > 0 being positive',],
                    'g1g2.var_g2g3.mtx'      :['0 0 0 0 0.5 0.5','does mean of group VARiable slope differ from 0? Is there an average affect of VARiable regressing out the effect of group? contrast 0 0 0.5 -0.5; t-test with (Group1+Group2)/2 > 0 being positive',],
                    }
                            },
        "dods_doss" : {
            'g1v0':[       'dods',],
            'g1v1':[       'dods',],
            'g1v2':[       'dods',],
            'g2v0':['doss','dods',],
            'g2v1':[       'dods',],
            'g3v0':['doss','dods',],
            'g3v1':[       'dods',],},
        "contrasts_not_used" : {
            'g1v2':{'main.mtx'          :['1 0 0',      't-test with offset>0 being positive; the intercept/offset is different than 0 after regressing out the effects of var1 and var2',],
                    'var1.mtx'          :['0 1 0',      't-test with var1 slope>0 being positive',],
                    'var2.mtx'          :['0 0 1',      't-test with var2 slope>0 being positive',],}
                                },
                }
