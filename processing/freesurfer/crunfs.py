
#!/bin/python
# 2020.07.31


from os import listdir, path, system, remove
import subprocess
import shutil
import datetime
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
        f.write(params["source_FreeSurfer_cmd"]+'\n')
        f.write('export SUBJECTS_DIR='+params["SUBJECTS_DIR"]+'\n')
        f.write('\n')
        f.write(cmd+'\n')
    print('    submitting '+sh_file)
    if params["SUBMIT"] == 1:
        print('SUBMITTING is ALLOWED')

        time.sleep(2)
        try:
            resp = subprocess.run(['sbatch',path.join(params["NIMB_tmp"],'usedpbs',sh_file)], stdout=subprocess.PIPE).stdout.decode('utf-8')
            return list(filter(None, resp.split(' ')))[-1].strip('\n')
        except Exception as e:
            print(e)
            return 0
    else:
        print('SUBMITTING is stopped')
        return 0

def submit_tmux(cmd, subjid):
    tmux_session = 'tmux_'+str(subjid)
    make_tmux_screen = 'tmux new -d -s '+tmux_session
    system('tmux send-keys -t '+str(tmux_session)+' '+cmd+' ENTER') #tmux send-keys -t session "echo 'Hello world'" ENTER
    return tmux_session

# class tmux_env():
    # https://gist.github.com/henrik/1967800
    # https://unix.stackexchange.com/questions/409861/its-possible-to-send-input-to-a-tmux-session-without-connecting-to-it
    # batch_output_cmd = 'screen -S minecraft -p 0 -X stuff "stop^M"'

    # PROJECT_PATH = 'path_to_your_project'
    # ACTIVATE_VENV = '. path_to_your_virtualenv/bin/activate'
    # # example: one tab with vim, other tab with two consoles (vertical split)
    # # with virtualenvs on the project, and a third tab with the server running

    # # vim in project
    # tmux('select-window -t 0')
    # tmux_shell('cd %s' % PROJECT_PATH)
    # tmux_shell('vim')
    # tmux('rename-window "vim"')

    # # console in project
    # tmux('new-window')
    # tmux('select-window -t 1')
    # tmux_shell('cd %s' % PROJECT_PATH)
    # tmux_shell(ACTIVATE_VENV)
    # tmux('rename-window "consola"')
    # # second console as split
    # tmux('split-window -v')
    # tmux('select-pane -t 1')
    # tmux_shell('cd %s' % PROJECT_PATH)
    # tmux_shell(ACTIVATE_VENV)
    # tmux('rename-window "consola"')

    # # local server
    # tmux('new-window')
    # tmux('select-window -t 2')
    # tmux_shell('cd %s' % PROJECT_PATH)
    # tmux_shell(ACTIVATE_VENV)
    # tmux_shell('python manage.py runserver')
    # tmux('rename-window "server"')

    # # go back to the first window
    # tmux('select-window -t 0')

    # def tmux(command):
        # system('tmux %s' % command)

    # def tmux_shell(command):
        # tmux('send-keys "%s" "C-m"' % command)

    # def bash_run():
        # function flask-boilerplate-tmux
        # {
            # # https://github.com/swaroopch/flask-boilerplate
            # BASE="$HOME/code/flask-boilerplate"
            # cd $BASE

            # tmux start-server
            # tmux new-session -d -s flaskboilerplate -n model
            # tmux new-window -t flaskboilerplate:2 -n controller
            # tmux new-window -t flaskboilerplate:3 -n view
            # tmux new-window -t flaskboilerplate:4 -n console
            # tmux new-window -t flaskboilerplate:5 -n tests
            # tmux new-window -t flaskboilerplate:6 -n git

            # tmux send-keys -t flaskboilerplate:1 "cd $BASE/flask_application; vim models.py" C-m
            # tmux send-keys -t flaskboilerplate:2 "cd $BASE/flask_application/controllers; ls" C-m
            # tmux send-keys -t flaskboilerplate:3 "cd $BASE/flask_application/templates; ls" C-m
            # tmux send-keys -t flaskboilerplate:4 "bpython -i play.py" C-m
            # tmux send-keys -t flaskboilerplate:5 "python tests.py" C-m
            # tmux send-keys -t flaskboilerplate:6 "git status" C-m

            # tmux select-window -t flaskboilerplate:1
            # tmux attach-session -t flaskboilerplate
        # }

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
        result = chkhipf(SUBJECTS_DIR, subjid, freesurfer_version)

    if process == 'tha':
        result = chkthaf(SUBJECTS_DIR, subjid, freesurfer_version)

    if process == 'masks':
        result = chk_masks(SUBJECTS_DIR, subjid, masks)

    return result



def chk_if_all_done(SUBJECTS_DIR, subjid, process_order, NIMB_tmp, freesurfer_version, masks):
        result = True
        if not chkIsRunning(SUBJECTS_DIR, subjid):
            for process in process_order[1:]:
                if not checks_from_runfs(SUBJECTS_DIR, process, subjid, freesurfer_version, masks):
                    log.info('        '+subjid+' is missing '+process)
                    result = False
                    break
        else:
            log.info('            IsRunning file present ')
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
            if not path.exists(path.join(SUBJECTS_DIR, subjid, path_f)):
                return False
                break
            else:
                return True


def chk_if_recon_done(SUBJECTS_DIR, subjid):

    '''must check for all files: https://surfer.nmr.mgh.harvard.edu/fswiki/ReconAllDevTable
    '''
    if path.exists(path.join(SUBJECTS_DIR,subjid, 'mri', 'wmparc.mgz')):
        return True
    else:
        return False


def chk_if_qcache_done(SUBJECTS_DIR, subjid):

    if 'rh.w-g.pct.mgh.fsaverage.mgh' and 'lh.thickness.fwhm10.fsaverage.mgh' in listdir(path.join(SUBJECTS_DIR, subjid, 'surf')):
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

def bs_hip_tha_chk_log_if_done(process, SUBJECTS_DIR, subjid, freesurfer_version):
    log_file = path.join(SUBJECTS_DIR, subjid, 'scripts', log_files[process][freesurfer_version])
    if path.exists(log_file) and any('Everything done' in i for i in open(log_file, 'rt').readlines()):
        return True
    else
        return False

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
        7:'rh.hipposubfields.T1.v21.stats', 6:'rh.hipposubfields.T1.v10.txt',},
    'amyL':{
        7:'lh.amygdalar-nuclei.T1.v21.stats', 6:'',},
    'amyR':{
        7:'rh.amygdalar-nuclei.T1.v21.stats', 6:'',},
    'tha':{
        7:'thalamic-nuclei.v12.T1.stats', 6:'',},
                         }

def bs_hip_tha_get_stats_file(process, SUBJECTS_DIR, subjid, freesurfer_version):
    lsmri = listdir(path.join(SUBJECTS_DIR, subjid, 'mri'))
    file_stats = path.join(SUBJECTS_DIR, subjid, 'mri', bs_hip_tha_stats_file_inmri[process][freesurfer_version])
    if path.exists(file_stats):
        try:
            shutil.copy(path.join(SUBJECTS_DIR, subjid, 'mri', file_stats),
                        path.join(SUBJECTS_DIR, subjid, 'stats', bs_hip_tha_stats_file_instats[process][freesurfer_version]))
        except Exception as e:
            print(e)
        return file_stats
    else
        return ''


def chkbrstemf(SUBJECTS_DIR, subjid, freesurfer_version):
    if bs_hip_tha_chk_log_if_done('bs', SUBJECTS_DIR, subjid, freesurfer_version):
        file_stats = bs_hip_tha_get_stats_file('bs', SUBJECTS_DIR, subjid, freesurfer_version)
        if file_stats:
            return True
        else:
            return False
    else:
        return False


def chkhipf(SUBJECTS_DIR, subjid, freesurfer_version):
    if bs_hip_tha_chk_log_if_done('hip', SUBJECTS_DIR, subjid, freesurfer_version):
        if path.exists(path.join(SUBJECTS_DIR, subjid, 'mri', bs_hip_tha_stats_file_inmri['hipR'][freesurfer_version])):
            for file in ['hipL', 'hipR', 'amyL', 'amyR']:
                file_stats = bs_hip_tha_get_stats_file(file, SUBJECTS_DIR, subjid, freesurfer_version)
            return True
        else:
            return False
    else:
        return False


def chkthaf(SUBJECTS_DIR, subjid, freesurfer_version):
    if bs_hip_tha_chk_log_if_done('tha', SUBJECTS_DIR, subjid, freesurfer_version):
        file_stats = bs_hip_tha_get_stats_file('tha', SUBJECTS_DIR, subjid, freesurfer_version)
        if file_stats:
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
                    log.info('        ERROR: Voxel size is different, Multiregistration is not supported; consider registration with less entries')
                    error = 'voxsizediff'
                    break
                elif  'error: mghRead' in line:
                    log.info('        ERROR: orig bad registration, probably due to multiple -i entries, rerun with less entries')
                    error = 'errorigmgz'
                    break
                elif 'error: MRISreadCurvature:' in line:
                    log.info('                    ERROR: MRISreadCurvature')
                    error = 'errCurvature'
                    break
                if 'ERROR: Talairach failed!' in line or 'error: transforms/talairach.m3z' in line:
                    log.info('        ERROR: Manual Talairach alignment may be necessary, or include the -notal-check flag to skip this test, making sure the -notal-check flag follows -all or -autorecon1 in the command string.')
                    error = 'talfail'
                    break
                elif 'ERROR: no run data found' in line:
                    log.info('        ERROR: file has no registration')
                    error = 'noreg'
                    break
                elif 'ERROR: inputs have mismatched dimensions!' in line:
                    log.info('        ERROR: files have mismatched dimension, repeat registration will be performed')
                    error = 'regdim'
                    break
                elif 'ERROR: cannot find' in line:
                    log.info('        ERROR: cannot find files')
                    error = 'cannotfind'
                    break
                elif 'error: MRIresample():' in line:
                    log.info('        ERROR: MRIresample error')
                    error = 'errMRIresample'
                    break
        else:
            log.info('        ERROR: '+file_2read+' not in '+path.join(SUBJECTS_DIR,subjid,'scripts'))
    except FileNotFoundError as e:
        print(e)
        log.info('    '+subjid+' '+str(e))
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
                log.info('                        MRISreadCurvature error, but is skipped')
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
                    log.info('        exited with ERRORS')
                    return False
                    break
                elif 'recon-all -s' in line:
                    return False
                    break
                else:
                    log.info('        not clear if finished with or without ERROR')
                    return False
                    break
        else:
            return False
    except FileNotFoundError as e:
        print(e)
        log.info('    '+subjid+' '+str(e))



def get_batch_jobs_status(cuser, cusers_list):

    def get_jobs(jobs, queue):

        for line in queue[1:]:
                vals = list(filter(None,line.split(' ')))
                if vals[0] not in jobs:
                    jobs[vals[0]] = vals[4]
        return jobs


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
