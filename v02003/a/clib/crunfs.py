#!/bin/python
# 2020.07.14

'''
add FS QA tools to rm scans with low SNR (Koh et al 2017)
https://surfer.nmr.mgh.harvard.edu/fswiki/QATools

'''


from os import listdir, path, mkdir, system
import shutil
import datetime
from var import text4_scheduler, batch_walltime_cmd, max_walltime, batch_output_cmd, freesurfer_version, nimb_dir, nimb_scratch_dir, SUBJECTS_DIR, export_FreeSurfer_cmd, source_FreeSurfer_cmd, SUBMIT
import cdb, var
import subprocess
print('SUBMITTING is: ', SUBMIT)



def submit_4_processing(processing_env, cmd, subjid, run, walltime):
    if processing_env == 'slurm':
        submit_cmd = 'sbatch'
        makesubmitpbs(submit_cmd, subjid, run, walltime)
    elif processing_env == 'tmux':
        submit_cmd = 'tmux'
        submit_tmux(submit_cmd, cmd, subjid)
    else:
        print('ERROR: processing environment not provided or incorrect')



def makesubmitpbs(submit_cmd, cmd, subjid, run, walltime):

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
    cdb.Update_status_log('    '+sh_file+' submitting')
    if SUBMIT:
        try:
            resp = subprocess.run([submit_cmd,nimb_scratch_dir+'usedpbs/'+sh_file], stdout=subprocess.PIPE).stdout.decode('utf-8')
            return list(filter(None, resp.split(' ')))[-1].strip('\n')
        except Exception as e:
            print(e)
            return ''
    else:
        return ''


def submit_tmux(submit_cmd, cmd, subjid):
    #https://gist.github.com/henrik/1967800
    tmux_session = 'tmux_'+str(subjid)

    make_tmux_screen = 'tmux new -d -s '+tmux_session
    system(submit_cmd+' send-keys -t '+str(tmux_session)+' '+cmd+' ENTER') #tmux send-keys -t session "echo 'Hello world'" ENTER
    return tmux_session



def FS_ready(SUBJECTS_DIR):
    if 'fsaverage' in listdir(SUBJECTS_DIR):
        if 'xhemi' in listdir(path.join(SUBJECTS_DIR,'fsaverage')):
            return True
        else:
            print(' fsaverage/xhemi is missing')
            return False
    else:
        print(' fsaverage is missing in SUBJECTS_DIR')
        return False



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

    try:
        if any('IsRunning.lh+rh' in i for i in listdir(path.join(SUBJECTS_DIR,subjid,'scripts'))):
            print('    IsRunning file present: True')
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return True



def chkreconf_if_without_error(subjid):

    file_2read = 'recon-all-status.log'
    try:
        if file_2read in listdir(path.join(SUBJECTS_DIR,subjid,'scripts')):
            f = open(path.join(SUBJECTS_DIR,subjid,'scripts',file_2read),'r').readlines()

            for line in reversed(f):
                if 'exited with ERRORS' in line:
                    cdb.Update_status_log('        exited with ERRORS')
                    return False
                elif 'finished without error' in line:
                    return True
                elif 'recon-all -s' in line:
                    return False
                    break
                else:
                    cdb.Update_status_log('        not clear if finished with or without ERROR')
                    return False
        else:
            return False
    except FileNotFoundError as e:
        print(e)
        cdb.Update_status_log('    '+subjid+' '+str(e))


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


def chkbrstemf(subjid):

    lsscripts=listdir(SUBJECTS_DIR+subjid+'/scripts/')
    log_file = log_files['bs'][freesurfer_version]
    if any(log_file in i for i in lsscripts):
        with open(SUBJECTS_DIR+subjid+'/scripts/'+log_file,'rt') as readlog:
            for line in readlog:
                line2read=[line]
                if any('Everything done' in i for i in line2read):
                    lsmri=listdir(SUBJECTS_DIR+subjid+'/mri/')
                    bs_f_stats = [i for i in lsmri if 'brainstemSsVolumes' in i][0]
                    if bs_f_stats:
                        if 'brainstemSsVolumes.v10' in bs_f_stats:
                            shutil.copy(path.join(SUBJECTS_DIR,subjid,bs_f_stats), path.join(SUBJECTS_DIR,subjid,'stats','brainstem.v10.stats'))
                        return True
                    else:
                        return False
    else:
        return False 


files_hip_amy21_mri = {
    'lh.hippoSfVolumes-T1.v21.txt':'lh.hipposubfields.T1.v21.stats',
    'rh.hippoSfVolumes-T1.v21.txt':'rh.hipposubfields.T1.v21.stats',
    'lh.amygNucVolumes-T1.v21.txt':'lh.amygdalar-nuclei.T1.v21.stats',
    'rh.amygNucVolumes-T1.v21.txt':'rh.amygdalar-nuclei.T1.v21.stats',
}
def chkhipf(subjid):

    lsscripts=listdir(SUBJECTS_DIR+subjid+'/scripts/')
    if any('hippocampal-subfields-T1' in i for i in lsscripts):
        # if 'IsRunningHPsubT1.lh+rh' not in lsscripts
        with open(SUBJECTS_DIR+subjid+'/scripts/hippocampal-subfields-T1.log','rt') as readlog:
            for line in readlog:
                line2read=[line]
                if any('Everything done' in i for i in line2read):
                    lsmri=listdir(SUBJECTS_DIR+subjid+'/mri/')
                    if any('lh.hippoSfVolumes-T1.v10.txt' in i for i in lsmri):
                        try:
                            shutil.copy(path.join(SUBJECTS_DIR,subjid,'mri','lh.hippoSfVolumes-T1.v10.txt'),path.join(SUBJECTS_DIR,subjid,'stats','lh.hipposubfields.T1.v10.stats'))
                            shutil.copy(path.join(SUBJECTS_DIR,subjid,'mri','rh.hippoSfVolumes-T1.v10.txt'),path.join(SUBJECTS_DIR,subjid,'stats','rh.hipposubfields.T1.v10.stats'))
                            return True
                        except Exception as e:
                            print(e)
                    elif any('lh.hippoSfVolumes-T1.v21.txt' in i for i in lsmri):
                        try:
                            for file in files_hip_amy21_mri:
                                shutil.copy(path.join(SUBJECTS_DIR,subjid,'mri',file),path.join(SUBJECTS_DIR,subjid,'stats',files_hip_amy21_mri[file]))
                            return True
                        except Exception as e:
                            print(e)
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
                        shutil.copy(path.join(SUBJECTS_DIR,subjid,'mri','ThalamicNuclei.v12.T1.volumes.txt'),path.join(SUBJECTS_DIR,subjid,'stats','thalamic-nuclei.v12.T1.stats'))
                        return True
                    else:
                        return False
    else:
        return False


def chk_masks(subjid):

    if path.isdir(path.join(SUBJECTS_DIR,subjid,'masks')):
        for structure in var.masks:
            if structure+'.nii' not in listdir(path.join(SUBJECTS_DIR,subjid,'masks')):
                return False
            else:
                return True
    else:
        return False


def fs_find_error(subjid):
    error = ''
    print('seraching for THE error')

    file_2read = 'recon-all.log'
    try:
        if file_2read in listdir(path.join(SUBJECTS_DIR,subjid,'scripts')):
            f = open(path.join(SUBJECTS_DIR,subjid,'scripts',file_2read),'r').readlines()

            for line in reversed(f):
                if 'ERROR: Talairach failed!' in line:
                    cdb.Update_status_log('        ERROR: Manual Talairach alignment may be necessary, or include the -notal-check flag to skip this test, making sure the -notal-check flag follows -all or -autorecon1 in the command string.')
                    error = 'talfail'
                    break
                if  'ERROR: MultiRegistration::loadMovables: images have different voxel sizes.':
                    cdb.Update_status_log('        ERROR: Voxel size is different, Multiregistration is not supported; consider making conform')
                    error = 'voxsizediff'
                    break
        else:
            cdb.Update_status_log('        ERROR: '+file_2read+' not in '+path.join(SUBJECTS_DIR,subjid,'scripts'))
    except FileNotFoundError as e:
        print(e)
        cdb.Update_status_log('    '+subjid+' '+str(e))

    return error
