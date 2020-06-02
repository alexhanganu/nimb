#!/bin/python
# 2020.06.02

'''
add FS QA tools to rm scans with low SNR (Koh et al 2017)
https://surfer.nmr.mgh.harvard.edu/fswiki/QATools

'''

SUBMIT = True
print('SUBMITTING is: ', SUBMIT)

from os import listdir, path, mkdir, system
import shutil
import datetime
from var import supervisor_ccri, text4_scheduler, batch_walltime_cmd, max_walltime, batch_output_cmd, submit_cmd
import cdb, var
import subprocess

_, nimb_dir , nimb_scratch_dir, SUBJECTS_DIR , _, _, export_FreeSurfer_cmd, source_FreeSurfer_cmd = var.get_vars()



def makesubmitpbs(cmd, subjid, run, walltime):

    date=datetime.datetime.now()
    dt=str(date.year)+str(date.month)+str(date.day)

    if not path.exists(nimb_scratch_dir+'usedpbs'):
        mkdir(nimb_scratch_dir+'usedpbs')
    sh_file = subjid+'_'+run+'_'+str(dt)+'.sh'
    out_file = subjid+'_'+run+'_'+str(dt)+'.out'

    with open(nimb_scratch_dir+'usedpbs/'+sh_file,'a') as f:
        for line in text4_scheduler:
            f.write(line+'\n')
        f.write(batch_walltime_cmd+walltime+'\n')
        f.write(batch_output_cmd+nimb_scratch_dir+'usedpbs/'+out_file+'\n')
        f.write('\n')
        f.write('cd '+nimb_dir+'\n')
        f.write('\n')
        f.write(export_FreeSurfer_cmd+'\n')
        f.write('source '+source_FreeSurfer_cmd+'\n')
        f.write('export SUBJECTS_DIR='+SUBJECTS_DIR+'\n')
        f.write('\n')
        f.write(cmd+'\n')
    print('submitting '+sh_file)
    if SUBMIT:
        resp = subprocess.run([submit_cmd,nimb_scratch_dir+'usedpbs/'+sh_file], stdout=subprocess.PIPE).stdout.decode('utf-8')
        return list(filter(None, resp.split(' ')))[-1].strip('\n')
    else:
    	return ''


def submit_4_run(cmd, subjid, run, walltime): #to join with makesubmitpbs
    if remote_type == 'tmux': #https://gist.github.com/henrik/1967800
        last_session = cdb.get_RUNNING_JOBS('tmux')
        if len(last_session)>0:
            session = 'tmux_'+str(int(last_session[-1][last_session[-1].find('-'):])+1) #get job id from cdb
        else:
            session = 'tmux_1'

        make_tmux_screen = 'tmux new -d -s session'
        system(submit_cmd+' send-keys -t '+str(session)+' '+cmd+' ENTER') #tmux send-keys -t session "echo 'Hello world'" ENTER
        return session


def run_make_masks(subjid):

    subj_dir = SUBJECTS_DIR+subjid
    if not path.isdir(subj_dir+'/masks'):
        mkdir(subj_dir+'/masks')
    mask_dir = subj_dir+'/masks/'

    for structure in cdb.get_mask_codes():
        aseg_mgz = subj_dir+'/mri/aseg.mgz'
        orig001_mgz = subj_dir+'/mri/orig/001.mgz'
        mask_mgz = mask_dir+structure+'.mgz'
        mask_nii = mask_dir+structure+'.nii'
        system('mri_binarize --match '+str(structure_codes[structure])+' --i '+aseg_mgz+' --o '+mask_mgz)
        system('mri_convert -rl '+orig001_mgz+' -rt nearest '+mask_mgz+' '+mask_nii)



def FS_ready(SUBJECTS_DIR):
    ready = False
    if 'fsaverage' not in listdir(SUBJECTS_DIR):
        print(' fsaverage is missing in SUBJECTS_DIR')
    if path.isdir(SUBJECTS_DIR+'fsaverage'):
        if 'xhemi' not in listdir(SUBJECTS_DIR+'fsaverage'):
            print(' fsaverage/xhemi is mising')
    if 'fsaverage' in listdir(SUBJECTS_DIR) and 'xhemi' in listdir(SUBJECTS_DIR+'fsaverage'):
        ready = True
    return ready


def checks_from_runfs(process, subjid):

    if process == 'registration':
        result = chksubjidinfs(subjid)

    if process == 'autorecon1':
        result = chk_if_autorecon_done(1, subjid)

    if process == 'autorecon2':
        result = chk_if_autorecon_done(2, subjid)

    if process == 'autorecon3':
        result = chk_if_autorecon_done(3, subjid)

    if process == 'recon':
        result = chk_if_recon_done(subjid)

    if process == 'qcache':
        result = chk_if_qcache_done(subjid)

    if process == 'brstem':
        result = chkbrstemf(subjid)

    if process == 'hip':
        result = chkhipf(subjid)

    if process == 'tha':
        result = chkthaf(subjid)

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

    if any('IsRunning.lh+rh' in i for i in listdir(SUBJECTS_DIR+subjid+'/scripts')):
        print('    IsRunning file present: True')
        return True
    else:
        return False



def chkreconf_if_without_error(subjid):

    if 'recon-all-status.log' in listdir(SUBJECTS_DIR+subjid+'/scripts/'):
        f = open(SUBJECTS_DIR+subjid+'/scripts/recon-all-status.log','r').readlines()

        for line in reversed(f):
                    if 'exited with ERRORS' in line:
                        cdb.Update_status_log(subjid+' exited with ERRORS line is present')
                        return False
                    elif 'finished without error' in line:
                        return True
                    elif 'recon-all -s' in line:
                        return False
                        break
                    else:
                        cdb.Update_status_log(subjid+' it\'s not clear whether subject finished with or without ERROR')
                        return False
    else:
        return False        


def chk_if_autorecon_done(lvl, subjid):
    f_autorecon = {1:['mri/nu.mgz','mri/orig.mgz','mri/brainmask.mgz',],
                2:['stats/lh.curv.stats','stats/rh.curv.stats',],
                3:['stats/aseg.stats','stats/wmparc.stats',]}
    for path_f in f_autorecon[lvl]:
            if not path.exists(SUBJECTS_DIR+subjid+'/'+path_f):# file not in listdir(SUBJECTS_DIR+subjid+'/'+file):
                return False
                break
            else:
                return True



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



def chkbrstemf(subjid):

    lsscripts=listdir(SUBJECTS_DIR+subjid+'/scripts/')
    if any('brainstem-structures' in i for i in lsscripts):
        with open(SUBJECTS_DIR+subjid+'/scripts/brainstem-structures.log','rt') as readlog:
            for line in readlog:
                line2read=[line]
                if any('Everything done' in i for i in line2read):
                    lsmri=listdir(SUBJECTS_DIR+subjid+'/mri/')
                    bs_f_stats = [i for in in lsmri if 'brainstemSsVolumes' in i][0]
                    if bs_f_stats:
                    # if any('brainstemSsVolumes' in i for i in lsmri):
                        shutil.copy(SUBJECTS_DIR+subjid+'/'+bs_f_stats, SUBJECTS_DIR+subjid+'/stats/aseg.brainstem.volume.stats')
                        # shutil.copy(SUBJECTS_DIR+subjid+'/mri/brainstemSsVolumes.v10.txt', SUBJECTS_DIR+subjid+'/stats/aseg.brainstem.volume.stats')
                        return True
                    else:
                        return False
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
                    elif any('lh.hippoSfVolumes-T1.v21.txt' in i for i in lsmri):
                        shutil.copy(SUBJECTS_DIR+subjid+'/mri/lh.hippoSfVolumes-T1.v21.txt',SUBJECTS_DIR+subjid+'/stats/aseg.hippo.lh.volume.stats')
                        if any('rh.hippoSfVolumes-T1.v21.txt' in i for i in lsmri):
                            shutil.copy(SUBJECTS_DIR+subjid+'/mri/rh.hippoSfVolumes-T1.v21.txt',SUBJECTS_DIR+subjid+'/stats/aseg.hippo.rh.volume.stats')
                        if any('lh.amygNucVolumes-T1.v21.txt ' in i for i in lsmri):
                            shutil.copy(SUBJECTS_DIR+subjid+'/mri/lh.amygNucVolumes-T1.v21.txt',SUBJECTS_DIR+subjid+'/stats/aseg.amyg.lh.volume.stats')
                        if any('rh.amygNucVolumes-T1.v21.txt' in i for i in lsmri):
                            shutil.copy(SUBJECTS_DIR+subjid+'/mri/rh.amygNucVolumes-T1.v21.txt',SUBJECTS_DIR+subjid+'/stats/aseg.amyg.rh.volume.stats')
                            return True
                    else:
                        return False
    else:
        return False


def chkthaf(subjid):

    lsscripts=listdir(SUBJECTS_DIR+subjid+'/scripts/')
    if any('thalamic-nuclei-mainFreeSurferT1.log' in i for i in lsscripts):
        with open(SUBJECTS_DIR+subjid+'/scripts/thalamic-nuclei-mainFreeSurferT1.log','rt') as readlog:
            for line in readlog:
                line2read=[line]
                if any('Everything done' in i for i in line2read):
                    lsmri=listdir(SUBJECTS_DIR+subjid+'/mri/')
                    if any('ThalamicNuclei.v12.T1.volumes.txt' in i for i in lsmri):
                        shutil.copy(SUBJECTS_DIR+subjid+'/mri/ThalamicNuclei.v12.T1.volumes.txt',SUBJECTS_DIR+subjid+'/stats/aseg.tha.volume.stats')
                        return True
                    else:
                        return False
    else:
        return False


def chk_masks(subjid):

    if path.isdir(SUBJECTS_DIR+subjid+'/masks/'):
        for structure in cdb.get_mask_codes():
            if structure+'.nii' not in listdir(SUBJECTS_DIR+subjid+'/masks/'):
                return False
                break
            else:
                return True
    else:
        return False
