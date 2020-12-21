#!/bin/python
# 2020.09.04
from os import path
processes_recon   = ["autorecon1",
                     "autorecon2",
                     "autorecon3",
                     "qcache"]
processes_subcort = ["brstem","hip","tha"]

process_order = ["registration",]+processes_recon+processes_subcort

GLM_measurements = {'thickness':'th',
                    'area'     :'ar',
                    'volume'   :'vol'}
GLM_sim_fwhm4csd = {'thickness': {'lh': '15',
                                  'rh': '15'},
                    'area'     : {'lh': '24',
                                  'rh': '25'},
                    'volume'   : {'lh': '16',
                                  'rh': '16'},
                    }
GLM_sim_directions = ['pos', 'neg']

suggested_times = {
        'registration':'01:00:00',
        'recon'       :'30:00:00',
        'autorecon1'  :'05:00:00',
        'autorecon2'  :'12:00:00',
        'autorecon3'  :'12:00:00',
        'recbase'     :'30:00:00',
        'reclong'     :'23:00:00',
        'qcache'      :'03:00:00',
        'brstem'      :'03:00:00',
        'hip'         :'03:00:00',
        'tha'         :'03:00:00',
        'masks'       :'12:00:00',
        }

IsRunning_files = ['IsRunning.lh+rh',
                   'IsRunningBSsubst',
                   'IsRunningHPsubT1.lh+rh',
                   'IsRunningThalamicNuclei_mainFreeSurferT1']

f_autorecon = {
        1:['mri/nu.mgz','mri/orig.mgz','mri/brainmask.mgz',],
        2:['stats/lh.curv.stats','stats/rh.curv.stats',],
        3:['stats/aseg.stats','stats/wmparc.stats',]
        }

hemi = ['lh','rh']

class FreeSurferVersion:
    def __init__(self, freesurfer_version):
        self.version = freesurfer_version

    def fs_ver(self):
        if len(str(self.version)) > 1:
            return str(self.version[0])
        else:
            return str(self.version)


class FilePerFSVersion:
    def __init__(self, freesurfer_version):
        # self.fs_ver    = freesurfer_version
        self.processes = ['bs', 'hip', 'amy', 'tha']
        self.log       = {
                'recon':{'7':'recon-all.log',                       '6':'recon-all.log'},
                'bs'   :{'7':'brainstem-substructures-T1.log',      '6':'brainstem-structures.log'},
                'hip'  :{'7':'hippocampal-subfields-T1.log',        '6':'hippocampal-subfields-T1.log'},
                'tha'  :{'7':'thalamic-nuclei-mainFreeSurferT1.log','6':''}
                          }
        self.stats_files = {
            'stats': {
                'bs'   :{'7':'brainstem.v12.stats'   ,              '6':'brainstem.v10.stats',},
                'hip'  :{'7':'hipposubfields.T1.v21.stats',         '6':'hipposubfields.T1.v10.stats',},
                'amy'  :{'7':'amygdalar-nuclei.T1.v21.stats',       '6':'',},
                'tha'  :{'7':'thalamic-nuclei.v12.T1.stats',        '6':'',}
                },
            'mri': {
                'bs'   :{'7':'brainstemSsVolumes.v12.txt',          '6':'brainstemSsVolumes.v10',},
                'hip'  :{'7':'hippoSfVolumes-T1.v21.txt',           '6':'hippoSfVolumes-T1.v10.txt',},
                'amy'  :{'7':'amygNucVolumes-T1.v21.txt',           '6':'',},
                'tha'  :{'7':'ThalamicNuclei.v12.T1.volumes.txt',   '6':'',}
                }
                        }
        self.hemi = {'lh':'lh.', 'rh':'rh.', 'lhrh':''}
        self.fs_ver = FreeSurferVersion(freesurfer_version).fs_ver()
    
    def log_f(self, process):
        return path.join('scripts', self.log[process][self.fs_ver])
        
    def stats_f(self, process, dir, hemi='lhrh'):
        file = '{}{}'.format(self.hemi[hemi], self.stats_files[dir][process][self.fs_ver])
        return path.join(dir, file)

# must check for all files: https://surfer.nmr.mgh.harvard.edu/fswiki/ReconAllDevTable
files_created = {
    'recon-all' : ['mri/wmparc.mgz',],
    'autorecon1': ['mri/nu.mgz','mri/orig.mgz','mri/brainmask.mgz',],
    'autorecon2': ['stats/lh.curv.stats','stats/rh.curv.stats',],
    'autorecon3': ['stats/aseg.stats','stats/wmparc.stats',],
    'qcache'    : ['surf/rh.w-g.pct.mgh.fsaverage.mgh', 'surf/lh.thickness.fwhm10.fsaverage.mgh']
}

class GLMVars:
    def __init__(self, proj_vars):
        self.proj_vars = proj_vars

    def f_ids_processed(self):
        return path.join(self.proj_vars['materials_DIR'][1], 'f_ids.json')
