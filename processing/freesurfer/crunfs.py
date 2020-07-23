#!/bin/python
# 2020.07.23


from os import listdir, path, mkdir, system
import subprocess
import shutil
import datetime
import cdb



def submit_4_processing(processing_env, cmd, subjid, run, walltime):
    if processing_env == 'slurm':
        job_id = makesubmitpbs(cmd, subjid, run, walltime)
    elif processing_env == 'tmux':
        job_id = submit_tmux(cmd, subjid)
    else:
        print('ERROR: processing environment not provided or incorrect')
    return job_id


def makesubmitpbs(cmd, subjid, run, walltime, params):

    date=datetime.datetime.now()
    dt=str(date.year)+str(date.month)+str(date.day)

    if not path.exists(params["NIMB_tmp"]+'usedpbs'):
        mkdir(params["NIMB_tmp"]+'usedpbs')
    sh_file = subjid+'_'+run+'_'+str(dt)+'.sh'
    out_file = subjid+'_'+run+'_'+str(dt)+'.out'

    with open(params["NIMB_tmp"]+'usedpbs/'+sh_file,'a') as f:
        for line in params["text4_scheduler"]:
            f.write(line+'\n')
        f.write(params["batch_walltime_cmd"]+walltime+'\n')
        f.write(params["batch_output_cmd"]+params["NIMB_tmp"]+'usedpbs/'+out_file+'\n')
        f.write('\n')
        f.write('cd '+params["NIMB_HOME"]+'\n')
        f.write('\n')
        f.write(params["export_FreeSurfer_cmd"]+'\n')
        f.write('source '+params["source_FreeSurfer_cmd"]+'\n')
        f.write('export SUBJECTS_DIR='+params["SUBJECTS_DIR"]+'\n')
        f.write('\n')
        f.write(cmd+'\n')
    print('    submitting '+sh_file)
    if params["SUBMIT"]:
        try:
            resp = subprocess.run(['sbatch',params["NIMB_tmp"]+'usedpbs/'+sh_file], stdout=subprocess.PIPE).stdout.decode('utf-8')
            return list(filter(None, resp.split(' ')))[-1].strip('\n')
        except Exception as e:
            print(e)
            return 0
    else:
        return 0

def submit_tmux(cmd, subjid):
    #https://gist.github.com/henrik/1967800
    tmux_session = 'tmux_'+str(subjid)

    make_tmux_screen = 'tmux new -d -s '+tmux_session
    system('tmux send-keys -t '+str(tmux_session)+' '+cmd+' ENTER') #tmux send-keys -t session "echo 'Hello world'" ENTER
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



def checks_from_runfs(SUBJECTS_DIR, process, subjid, freesurfer_version, masks):

    if process == 'registration':
        result = chksubjidinfs(SUBJECTS_DIR, subjid)

    if process == 'autorecon1':
        result = chk_if_autorecon_done(SUBJECTS_DIR, 1, subjid)

    if process == 'autorecon2':
        result = chk_if_autorecon_done(SUBJECTS_DIR, 2, subjid)

    if process == 'autorecon3':
        result = chk_if_autorecon_done(SUBJECTS_DIR, 3, subjid)

    if process == 'recon':
        result = chk_if_recon_done(SUBJECTS_DIR, subjid)

    if process == 'qcache':
        result = chk_if_qcache_done(SUBJECTS_DIR, subjid)

    if process == 'brstem':
        result = chkbrstemf(SUBJECTS_DIR, subjid, freesurfer_version)

    if process == 'hip':
        result = chkhipf(SUBJECTS_DIR, subjid)

    if process == 'tha':
        result = chkthaf(SUBJECTS_DIR, subjid)

    if process == 'masks':
        result = chk_masks(SUBJECTS_DIR, subjid, masks)

    return result

def chksubjidinfs(SUBJECTS_DIR, subjid):

    lsallsubjid=listdir(SUBJECTS_DIR)

    if subjid in lsallsubjid:
        return True

    else:
        return False


def chkIsRunning(SUBJECTS_DIR, subjid):

    #script does not check for presence of IsRunning files for the brainstem, hippocampus and thalamus
    IsRunning_files = ['IsRunning.lh+rh','IsRunningThalamicNuclei_mainFreeSurferT1',]
    try:
        for file in IsRunning_files:
            if path.exists(path.join(SUBJECTS_DIR,subjid,'scripts',file)):
                return True
        else:
            return False
    except Exception as e:
        print(e)
        return True

    # try:
    #     if any('IsRunning.lh+rh' in i for i in listdir(path.join(SUBJECTS_DIR,subjid,'scripts'))):
    #         print('    IsRunning file present: True')
    #         return True
    #     else:
    #         return False
    # except Exception as e:
    #     print(e)
    #     return True



def chkreconf_if_without_error(subjid, SUBJECTS_DIR):

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


def chk_if_autorecon_done(SUBJECTS_DIR, lvl, subjid):
    f_autorecon = {1:['mri/nu.mgz','mri/orig.mgz','mri/brainmask.mgz',],
                2:['stats/lh.curv.stats','stats/rh.curv.stats',],
                3:['stats/aseg.stats','stats/wmparc.stats',]}
    for path_f in f_autorecon[lvl]:
            if not path.exists(SUBJECTS_DIR+subjid+'/'+path_f):# file not in listdir(SUBJECTS_DIR+subjid+'/'+file):
                return False
                break
            else:
                return True



def chk_if_recon_done(SUBJECTS_DIR, subjid):

    '''must check for all files: https://surfer.nmr.mgh.harvard.edu/fswiki/ReconAllDevTable
	'''
    if 'wmparc.mgz' in listdir(SUBJECTS_DIR+subjid+'/mri/'):
        return True
    else:
        return False



def chk_if_qcache_done(SUBJECTS_DIR, subjid):

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


def chkbrstemf(SUBJECTS_DIR, subjid, freesurfer_version):

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
def chkhipf(SUBJECTS_DIR, subjid):

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


def chkthaf(SUBJECTS_DIR, subjid):

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


def chk_masks(SUBJECTS_DIR, subjid, masks):

    if path.isdir(path.join(SUBJECTS_DIR,subjid,'masks')):
        for structure in masks:
            if structure+'.nii' not in listdir(path.join(SUBJECTS_DIR,subjid,'masks')):
                return False
            else:
                return True
    else:
        return False



def fs_find_error(subjid, SUBJECTS_DIR):
    error = ''
    print('identifying THE error')
    file_2read = path.join(SUBJECTS_DIR,subjid,'scripts','recon-all.log')
    try:
        if path.exists(file_2read):
            f = open(file_2read,'r').readlines()
            for line in reversed(f):
                if 'ERROR: Talairach failed!' in line:
                    cdb.Update_status_log('        ERROR: Manual Talairach alignment may be necessary, or include the -notal-check flag to skip this test, making sure the -notal-check flag follows -all or -autorecon1 in the command string.')
                    error = 'talfail'
                    break
                elif  'ERROR: MultiRegistration::loadMovables: images have different voxel sizes.' in line:
                    cdb.Update_status_log('        ERROR: Voxel size is different, Multiregistration is not supported; consider making conform')
                    error = 'voxsizediff'
                    break
                elif 'ERROR: no run data found' in line:
                    error = 'noreg'
                    break
                elif 'ERROR: inputs have mismatched dimensions!' in line:
                    error = 'regdim'
                    break
                elif 'error: MRISreadCurvature:' in line:
                    error = 'errCurvature'
                    break
                elif 'ERROR: cannot find' in line:
                    error = 'cannotfind'
                    break
        else:
            cdb.Update_status_log('        ERROR: '+file_2read+' not in '+path.join(SUBJECTS_DIR,subjid,'scripts'))
    except FileNotFoundError as e:
        print(e)
        cdb.Update_status_log('    '+subjid+' '+str(e))
    return error


def solve_error(subjid, error, SUBJECTS_DIR):
    file_2read = path.join(SUBJECTS_DIR,subjid,'scripts','recon-all.log')
    f = open(file_2read,'r').readlines()
    if error == "errCurvature":
        for line in reversed(f):
            if 'error: MRISreadCurvature:' in line:
                line_nr = f.index(line)
                break
        if line_nr:
            if [i for i in f[line_nr:line_nr+20] if 'Skipping this (and any remaining) curvature files' in i]:
                return 'continue'
        else:
            return 'unsolved'
    if error == 'voxsizediff':
        return 'voxreg'