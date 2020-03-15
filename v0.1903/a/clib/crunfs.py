#!/bin/python
#Alexandru Hanganu, 2019 November 16
'''
run registration - check if works
add FS QA tools to rm scans with low SNR (Koh et al 2017)
? add different output folder for the out. files

'''

SUBMIT = True

from os import listdir, path, mkdir, system, remove
import shutil
import datetime
from var import supervisor_ccri, text4_scheduler, batch_walltime_cmd, max_walltime, batch_output_cmd, pbs_file_FS_setup, submit_cmd, LONGITUDINAL_DEFINITION
import cdb
import subprocess

_, dir_home , dir_scratch, SUBJECTS_DIR , _, dir_new_subjects = cdb.get_vars()


def checks_from_runfs(process, subjid):

    if process == 'registration':
        result = chksubjidinfs(subjid)

    if process == 'recon':
        result = chk_if_recon_done(subjid)

    if process == 'qcache':
        result = chk_if_qcache_done(subjid)

    if process == 'hip':
        result = chkhipf(subjid)

    if process == 'brstem':
        result = chkbrstemf(subjid)

    if process == 'masks':
        result = chk_masks(subjid)

    return result


def chksubjidinfs(subjid):

    lsallsubjid=listdir(SUBJECTS_DIR)

    if subjid in lsallsubjid:
        return True

    else:
        return False


def chkIsRunning(subjid):

    lsscripts=listdir(SUBJECTS_DIR+subjid+'/scripts')

    if any('IsRunning.lh+rh' in i for i in lsscripts):
        return True

    else:
        return False


def chkreconf_if_without_error(subjid):

    if 'recon-all-status.log' in listdir(SUBJECTS_DIR+subjid+'/scripts/'):
        f = open(SUBJECTS_DIR+subjid+'/scripts/recon-all-status.log','r').readlines()

        for line in reversed(f):
                    if 'exited with ERRORS' in line:
                        cdb.Update_status_log('exited with ERRORS line is present')
                        return False
                    elif 'finished without error' in line:
                        return True
                    elif 'recon-all -s' in line:
                        return False
                        break
                    else:
                        cdb.Update_status_log('it\'s not clear whether subject finished with or without ERROR')
                        return False
    else:
        return False        


def chk_if_recon_done(subjid):

    '''must check for all files: https://surfer.nmr.mgh.harvard.edu/fswiki/ReconAllDevTable
	'''
    if 'wmparc.mgz' in listdir(SUBJECTS_DIR+subjid+'/mri/'):
        return True
    else:
        return False


def chk_if_qcache_done(subjid):

    if 'rh.w-g.pct.mgh.fsaverage.mgh' and 'lh.thickness.fwhm10.fsaverage.mgh' in listdir(SUBJECTS_DIR+subjid+'/surf/'):
        return True
    else:
        return False


def chkhipf(subjid):

    lsscripts=listdir(SUBJECTS_DIR+subjid+'/scripts/')
    if any('hippocampal-subfields-T1' in i for i in lsscripts):
        with open(SUBJECTS_DIR+subjid+'/scripts/hippocampal-subfields-T1.log','rt') as readlog:
            for line in readlog:
                line2read=[line]
                if any('Everything done' in i for i in line2read):
                    lsmri=listdir(SUBJECTS_DIR+subjid+'/mri/')
                    if any('lh.hippoSfVolumes-T1.v10.txt' in i for i in lsmri):
                        shutil.copy(SUBJECTS_DIR+subjid+'/mri/lh.hippoSfVolumes-T1.v10.txt',SUBJECTS_DIR+subjid+'/stats/aseg.hippo.lh.volume.stats')
                        if any('rh.hippoSfVolumes-T1.v10.txt' in i for i in lsmri):
                            shutil.copy(SUBJECTS_DIR+subjid+'/mri/rh.hippoSfVolumes-T1.v10.txt',SUBJECTS_DIR+subjid+'/stats/aseg.hippo.rh.volume.stats')
                            return True
                    else:
                        return False
    else:
        return False


def chkbrstemf(subjid):

    lsscripts=listdir(SUBJECTS_DIR+subjid+'/scripts/')
    if any('brainstem-structures' in i for i in lsscripts):
        with open(SUBJECTS_DIR+subjid+'/scripts/brainstem-structures.log','rt') as readlog:
            for line in readlog:
                line2read=[line]
                if any('Everything done' in i for i in line2read):
                    lsmri=listdir(SUBJECTS_DIR+subjid+'/mri/')
                    if any('brainstemSsVolumes' in i for i in lsmri):
                        shutil.copy(SUBJECTS_DIR+subjid+'/mri/brainstemSsVolumes.v10.txt', SUBJECTS_DIR+subjid+'/stats/aseg.brainstem.volume.stats')
                        return True
                    else:
                        return False
    else:
        return False 


def makesubmitpbs(cmd, subjid, run, walltime):

    date=datetime.datetime.now()
    dt=str(date.year)+str(date.month)+str(date.day)

    if not path.exists(dir_scratch+'usedpbs'):
        mkdir(dir_scratch+'usedpbs')
    sh_file = subjid+'_'+run+'_'+str(dt)+'.sh'
    out_file = subjid+'_'+run+'_'+str(dt)+'.out'

    with open(dir_scratch+'usedpbs/'+sh_file,'a') as f:
        for line in text4_scheduler:
            f.write(line+'\n')
        f.write(batch_walltime_cmd+walltime+'\n')
        f.write(batch_output_cmd+dir_scratch+'usedpbs/'+out_file+'\n')
        f.write('\n')
        f.write('cd '+dir_home+'\n')
        f.write('\n')
        for line in pbs_file_FS_setup:
            f.write(line+'\n')
        f.write('export SUBJECTS_DIR='+SUBJECTS_DIR+'\n')
        f.write('\n')
        f.write(cmd+'\n')
    print('submitting '+sh_file)
    if SUBMIT:
        resp = subprocess.run([submit_cmd,dir_scratch+'usedpbs/'+sh_file], stdout=subprocess.PIPE).stdout.decode('utf-8')
        return list(filter(None, resp.split(' ')))[-1].strip('\n')
    else:
    	return ''


structure_codes = {'left_hippocampus':17,'right_hippocampus':53,
                    'left_thalamus':10,'right_thalamus':49,'left_caudate':11,'right_caudate':50,
                    'left_putamen':12,'right_putamen':51,'left_pallidum':13,'right_pallidum':52,
                    'left_amygdala':18,'right_amygdala':54,'left_accumbens':26,'right_accumbens':58,
                    'left_hippocampus_CA2':550,'right_hippocampus_CA2':500,
                    'left_hippocampus_CA1':552,'right_hippocampus_CA1':502,
                    'left_hippocampus_CA4':556,'right_hippocampus_CA4':506,
                    'left_hippocampus_fissure':555,'right_hippocampus_fissure':505,
                    'left_amygdala_subiculum':557,'right_amygdala_subiculum':507,
                    'left_amygdala_presubiculum':554,'right_amygdala_presubiculum':504,}

def run_make_masks(subjid):

    from os import system
    subj_dir = SUBJECTS_DIR+subjid
    if not path.isdir(subj_dir+'/masks'):
        mkdir(subj_dir+'/masks')
    mask_dir = subj_dir+'/masks/'

    for structure in structure_codes:
        aseg_mgz = subj_dir+'/mri/aseg.mgz'
        orig001_mgz = subj_dir+'/mri/orig/001.mgz'
        mask_mgz = mask_dir+structure+'.mgz'
        mask_nii = mask_dir+structure+'.nii'
        system('mri_binarize --match '+str(structure_codes[structure])+' --i '+aseg_mgz+' --o '+mask_mgz)
        system('mri_convert -rl '+orig001_mgz+' -rt nearest '+mask_mgz+' '+mask_nii)


def chk_masks(subjid):

    if path.isdir(SUBJECTS_DIR+subjid+'/masks/'):
        for structure in structure_codes:
            if structure+'.nii' not in listdir(SUBJECTS_DIR+subjid+'/masks/'):
                return False
                break
            else:
                return True
    else:
        return False




def remove_all_IsRunning():

    for subDIR in listdir(SUBJECTS_DIR):
        if path.isdir(SUBJECTS_DIR+subDIR+'/scripts'):
            if any('IsRunning.lh+rh' in i for i in listdir(SUBJECTS_DIR+subDIR+'/scripts/')):
                remove(SUBJECTS_DIR+subDIR+'/scripts/IsRunning.lh+rh')
            else:
                pass
