#!/bin/python
# 2020.07.31


from os import listdir, path, mkdir, system, remove
import subprocess
import shutil
import datetime
import cdb
import time
import logging


log = logging.getLogger(__name__)


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

    sh_file = subjid+'_'+run+'_'+str(dt)+'.sh'
    out_file = subjid+'_'+run+'_'+str(dt)+'.out'

    with open(path.join(params["NIMB_tmp"], 'usedpbs', sh_file), 'w') as f:
        for line in params["text4_scheduler"]:
            f.write(line+'\n')
        f.write(params["batch_walltime_cmd"]+walltime+'\n')
        f.write(params["batch_output_cmd"]+path.join(params["NIMB_tmp"],'usedpbs',out_file)+'\n')
        f.write('\n')
        f.write('\n')
        f.write(params["export_FreeSurfer_cmd"]+'\n')
        f.write('source '+params["source_FreeSurfer_cmd"]+'\n')
        f.write('export SUBJECTS_DIR='+params["SUBJECTS_DIR"]+'\n')
        f.write('\n')
        f.write(cmd+'\n')
    print('    submitting '+sh_file)
    if params["SUBMIT"]:

        time.sleep(2)
        try:
            resp = subprocess.run(['sbatch',path.join(params["NIMB_tmp"],'usedpbs',sh_file)], stdout=subprocess.PIPE).stdout.decode('utf-8')
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




def chkIsRunning(SUBJECTS_DIR, subjid):

    IsRunning_files = ['IsRunning.lh+rh', 'IsRunningBSsubst', 'IsRunningHPsubT1.lh+rh', 'IsRunningThalamicNuclei_mainFreeSurferT1']
    try:
        for file in IsRunning_files:
            if path.exists(path.join(SUBJECTS_DIR,subjid,'scripts',file)):
                return True
        else:
            return False
    except Exception as e:
        print(e)
        return True


def IsRunning_rm(SUBJECTS_DIR, subjid):
    IsRunning_files = ['IsRunning.lh+rh', 'IsRunningBSsubst', 'IsRunningHPsubT1.lh+rh', 'IsRunningThalamicNuclei_mainFreeSurferT1']
    try:
        remove(path.join(SUBJECTS_DIR, subjid, 'scripts', [i for i in IsRunning_files if path.exists(path.join(SUBJECTS_DIR, subjid, 'scripts', i))][0]))
    except Exception as e:
        print(e)



def checks_from_runfs(SUBJECTS_DIR, process, subjid, freesurfer_version, masks):

    if process == 'registration':
        result = chksubjidinfs(SUBJECTS_DIR, subjid)

    if process == 'autorecon1':
        result = chk_if_autorecon_done(SUBJECTS_DIR, 1, subjid)

    if process == 'autorecon2':
        result = chk_if_autorecon_done(SUBJECTS_DIR, 2, subjid)

    if process == 'autorecon3':
        result = chk_if_autorecon_done(SUBJECTS_DIR, 3, subjid)

    if process == 'recon-all':
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



def chk_if_all_done(SUBJECTS_DIR, subjid, process_order, NIMB_tmp, freesurfer_version, masks):
        result = True
        if not chkIsRunning(SUBJECTS_DIR, subjid):
            for process in process_order[1:]:
                if not checks_from_runfs(SUBJECTS_DIR, process, subjid, freesurfer_version, masks):
                    cdb.Update_status_log(NIMB_tmp, '        '+subjid+' is missing '+process)
                    result = False
                    break
        else:
            cdb.Update_status_log(NIMB_tmp, '            IsRunning file present ')
            result = False
        return result



def chksubjidinfs(SUBJECTS_DIR, subjid):

    lsallsubjid=listdir(SUBJECTS_DIR)

    if subjid in lsallsubjid:
        return True

    else:
        return False




def chk_if_autorecon_done(SUBJECTS_DIR, lvl, subjid):
    f_autorecon = {1:['mri/nu.mgz','mri/orig.mgz','mri/brainmask.mgz',],
                2:['stats/lh.curv.stats','stats/rh.curv.stats',],
                3:['stats/aseg.stats','stats/wmparc.stats',]}
    for path_f in f_autorecon[lvl]:
            if not path.exists(path.join(SUBJECTS_DIR,subjid,path_f)):
                return False
                break
            else:
                return True



def chk_if_recon_done(SUBJECTS_DIR, subjid):

    '''must check for all files: https://surfer.nmr.mgh.harvard.edu/fswiki/ReconAllDevTable
	'''
    if 'wmparc.mgz' in listdir(path.join(SUBJECTS_DIR,subjid,'mri')):
        return True
    else:
        return False



def chk_if_qcache_done(SUBJECTS_DIR, subjid):

    if 'rh.w-g.pct.mgh.fsaverage.mgh' and 'lh.thickness.fwhm10.fsaverage.mgh' in listdir(path.join(SUBJECTS_DIR,subjid,'surf')):
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

    lsscripts=listdir(path.join(SUBJECTS_DIR,subjid,'scripts'))
    log_file = log_files['bs'][freesurfer_version]
    if any(log_file in i for i in lsscripts):
        with open(path.join(SUBJECTS_DIR, subjid, 'scripts', log_file), 'rt') as readlog:
            for line in readlog:
                line2read=[line]
                if any('Everything done' in i for i in line2read):
                    lsmri = listdir(path.join(SUBJECTS_DIR, subjid, 'mri'))
                    bs_f_stats = [i for i in lsmri if 'brainstemSsVolumes' in i][0]
                    if bs_f_stats:
                        if 'brainstemSsVolumes.v10' in bs_f_stats:
                            try:
                                shutil.copy(path.join(SUBJECTS_DIR, subjid, 'mri', bs_f_stats), path.join(SUBJECTS_DIR, subjid, 'stats', 'brainstem.v10.stats'))
                            except Exception as e:
                                print(e)
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

    lsscripts = listdir(path.join(SUBJECTS_DIR, subjid, 'scripts'))
    if any('hippocampal-subfields-T1' in i for i in lsscripts):
        with open(path.join(SUBJECTS_DIR, subjid, 'scripts', 'hippocampal-subfields-T1.log'), 'rt') as readlog:
            for line in readlog:
                line2read = [line]
                if any('Everything done' in i for i in line2read):
                    lsmri = listdir(path.join(SUBJECTS_DIR, subjid, 'mri'))
                    if any('rh.hippoSfVolumes-T1.v10.txt' in i for i in lsmri):
                        try:
                            shutil.copy(path.join(SUBJECTS_DIR, subjid, 'mri', 'lh.hippoSfVolumes-T1.v10.txt'), path.join(SUBJECTS_DIR, subjid, 'stats', 'lh.hipposubfields.T1.v10.stats'))
                            shutil.copy(path.join(SUBJECTS_DIR, subjid, 'mri', 'rh.hippoSfVolumes-T1.v10.txt'), path.join(SUBJECTS_DIR, subjid, 'stats', 'rh.hipposubfields.T1.v10.stats'))
                        except Exception as e:
                            print(e)
                        return True
                    elif any('rh.hippoSfVolumes-T1.v21.txt' in i for i in lsmri):
                            try:
                                for file in files_hip_amy21_mri:
                                    shutil.copy(path.join(SUBJECTS_DIR, subjid, 'mri', file), path.join(SUBJECTS_DIR, subjid, 'stats', files_hip_amy21_mri[file]))
                            except Exception as e:
                                print(e)
                            return True
                    else:
                        return False
    else:
        return False



def chkthaf(SUBJECTS_DIR, subjid):

    lsscripts=listdir(path.join(SUBJECTS_DIR,subjid,'scripts'))
    if any('thalamic-nuclei-mainFreeSurferT1.log' in i for i in lsscripts):
        with open(path.join(SUBJECTS_DIR, subjid, 'scripts', 'thalamic-nuclei-mainFreeSurferT1.log'), 'rt') as readlog:
            for line in readlog:
                line2read = [line]
                if any('Everything done' in i for i in line2read):
                    lsmri = listdir(path.join(SUBJECTS_DIR, subjid, 'mri'))
                    if any('ThalamicNuclei.v12.T1.volumes.txt' in i for i in lsmri):
                            try:
                                shutil.copy(path.join(SUBJECTS_DIR, subjid, 'mri', 'ThalamicNuclei.v12.T1.volumes.txt'), path.join(SUBJECTS_DIR, subjid, 'stats', 'thalamic-nuclei.v12.T1.stats'))
                            except Exception as e:
                                print(e)
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



def fs_find_error(subjid, SUBJECTS_DIR, NIMB_tmp):
    error = ''
    print('                identifying THE error')
    file_2read = path.join(SUBJECTS_DIR,subjid,'scripts','recon-all.log')
    try:
        if path.exists(file_2read):
            f = open(file_2read,'r').readlines()
            for line in reversed(f):
                if  'ERROR: MultiRegistration::loadMovables: images have different voxel sizes.' in line:
                    cdb.Update_status_log(NIMB_tmp,'        ERROR: Voxel size is different, Multiregistration is not supported; consider registration with less entries')
                    error = 'voxsizediff'
                    break
                elif  'error: mghRead' in line:
                    cdb.Update_status_log(NIMB_tmp,'        ERROR: orig bad registration, probably due to multiple -i entries, rerun with less entries')
                    error = 'errorigmgz'
                    break
                elif 'error: MRISreadCurvature:' in line:
                    cdb.Update_status_log(NIMB_tmp,'                    ERROR: MRISreadCurvature')
                    error = 'errCurvature'
                    break
                if 'ERROR: Talairach failed!' in line or 'error: transforms/talairach.m3z' in line:
                    cdb.Update_status_log(NIMB_tmp,'        ERROR: Manual Talairach alignment may be necessary, or include the -notal-check flag to skip this test, making sure the -notal-check flag follows -all or -autorecon1 in the command string.')
                    error = 'talfail'
                    break
                elif 'ERROR: no run data found' in line:
                    cdb.Update_status_log(NIMB_tmp,'        ERROR: file has no registration')
                    error = 'noreg'
                    break
                elif 'ERROR: inputs have mismatched dimensions!' in line:
                    cdb.Update_status_log(NIMB_tmp,'        ERROR: files have mismatched dimension, repeat registration will be performed')
                    error = 'regdim'
                    break
                elif 'ERROR: cannot find' in line:
                    cdb.Update_status_log(NIMB_tmp,'        ERROR: cannot find files')
                    error = 'cannotfind'
                    break
                elif 'error: MRIresample():' in line:
                    cdb.Update_status_log(NIMB_tmp,'        ERROR: MRIresample error')
                    error = 'errMRIresample'
                    break
        else:
            cdb.Update_status_log(NIMB_tmp,'        ERROR: '+file_2read+' not in '+path.join(SUBJECTS_DIR,subjid,'scripts'))
    except FileNotFoundError as e:
        print(e)
        cdb.Update_status_log(NIMB_tmp,'    '+subjid+' '+str(e))
    return error


def solve_error(subjid, error, SUBJECTS_DIR, NIMB_tmp):
    file_2read = path.join(SUBJECTS_DIR,subjid,'scripts','recon-all.log')
    f = open(file_2read,'r').readlines()
    if error == "errCurvature":
        for line in reversed(f):
            if 'error: MRISreadCurvature:' in line:
                line_nr = f.index(line)
                break
        if line_nr:
            if [i for i in f[line_nr:line_nr+20] if 'Skipping this (and any remaining) curvature files' in i]:
                cdb.Update_status_log(NIMB_tmp,'                        MRISreadCurvature error, but is skipped')
                return 'continue'
        else:
            return 'unsolved'
    if error == 'voxsizediff' or error == 'errorigmgz':
        return 'voxreg'



def chkreconf_if_without_error(NIMB_tmp, subjid, SUBJECTS_DIR):

    file_2read = 'recon-all-status.log'
    try:
        if file_2read in listdir(path.join(SUBJECTS_DIR,subjid,'scripts')):
            f = open(path.join(SUBJECTS_DIR,subjid,'scripts',file_2read),'r').readlines()

            for line in reversed(f):
                if 'finished without error' in line:
                    return True
                    break
                elif 'exited with ERRORS' in line:
                    cdb.Update_status_log(NIMB_tmp,'        exited with ERRORS')
                    return False
                    break
                elif 'recon-all -s' in line:
                    return False
                    break
                else:
                    cdb.Update_status_log(NIMB_tmp,'        not clear if finished with or without ERROR')
                    return False
                    break
        else:
            return False
    except FileNotFoundError as e:
        print(e)
        cdb.Update_status_log(NIMB_tmp,'    '+subjid+' '+str(e))



def get_batch_jobs_status(cuser, cusers_list):

    def get_jobs(jobs, queue):

        for line in queue[1:]:
                vals = list(filter(None,line.split(' ')))
                if vals[0] not in jobs:
                    jobs[vals[0]] = vals[4]
        return jobs


    import subprocess

    jobs = dict()
    for cuser in cusers_list:
        queue = list(filter(None,subprocess.run(['squeue','-u',cuser], stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')))
        jobs.update(get_jobs(jobs, queue))

    return jobs



def get_diskusage_report(cuser, cusers_list):
    '''script to read the available space
    on compute canada clusters
    the command diskusage_report is used'''

    def get_diskspace(diskusage, queue):

        for line in queue[1:]:
                vals = list(filter(None,line.split(' ')))
                diskusage[vals[0]] = vals[4][:-5].strip('k')
        return diskusage


    import subprocess

    diskusage = dict()
    for cuser in cusers_list:
        queue = list(filter(None,subprocess.run(['diskusage_report'], stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')))
        diskusage = get_diskspace(diskusage, queue)

    return diskusage


def get_mask_codes(structure):
    structure_codes = {'left_hippocampus':17,'right_hippocampus':53,
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
    return structure_codes[structure]




def get_batch_job_status_table():
    import pandas as pd

    system('squeue -u hanganua > batch_queue')
    try:
         df = pd.read_csv(file, sep=' ')

         df.drop(df.iloc[:, 0:8], inplace=True, axis=1)
         df.drop(df.iloc[:, 1:3], inplace=True, axis=1)
         df.drop(df.iloc[:, 1:14], inplace=True, axis=1)

         job_ids = df.iloc[:,0].tolist()
         batch_files = df.iloc[:,1].dropna().tolist()+df.iloc[:,2].dropna().tolist()

         start_batch_cmd = 'sbatch '
         cacel_batch_cmd = 'scancel -i '
    except Exception as e:
        print(e)

