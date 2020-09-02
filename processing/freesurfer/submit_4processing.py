from os import path, environ, system
import time
import subprocess
import logging

environ['TZ'] = 'US/Eastern'
time.tzset()


def start_fs_pipeline(vars_local):

    datehour = time.strftime("%Y%m%d_%H%M",time.localtime(time.time()))

    sh_file = 'nimb_run_'+datehour+'.sh'
    out_file = 'nimb_run_'+datehour+'.out'

    with open(path.join(vars_local["NIMB_PATHS"]["NIMB_tmp"], 'usedpbs', sh_file),'w') as f:
        for line in vars_local['PROCESSING']["text4_scheduler"]:
            f.write(line+'\n')
        f.write(vars_local['PROCESSING']["batch_walltime_cmd"]+vars_local['PROCESSING']["batch_walltime"]+'\n')
        f.write(vars_local['PROCESSING']["batch_output_cmd"]+path.join(vars_local["NIMB_PATHS"]["NIMB_tmp"],'usedpbs',out_file)+'\n')
        f.write('\n')
        f.write('cd '+path.join(vars_local["NIMB_PATHS"]["NIMB_HOME"], 'processing', 'freesurfer')+'\n')
        f.write(vars_local['PROCESSING']["python3_load_cmd"]+'\n'+vars_local['PROCESSING']["python3_run_cmd"]+' crun.py')

    try:
        log = logging.getLogger(__name__)
        log.info('    '+sh_file+' submitting')
        resp = subprocess.run([vars_local['PROCESSING']["submit_cmd"],path.join(vars_local["NIMB_PATHS"]["NIMB_tmp"], 'usedpbs', sh_file)], stdout=subprocess.PIPE).stdout.decode('utf-8')
        print(list(filter(None, resp.split(' ')))[-1].strip('\n'))
    except Exception as e:
        print(e)

# start_fs_pipeline =
# Submit_task(vars_local,
#             vars_local['PROCESSING']["python3_load_cmd"]+'\n'+vars_local['PROCESSING']["python3_run_cmd"]+' crun.py',
#           'nimb','run', vars_local['PROCESSING']["batch_walltime"],
#            False, 'cd '+path.join(vars_local["NIMB_PATHS"]["NIMB_HOME"], 'processing', 'freesurfer')

class Submit_task():

    def __init__(self, vars_local, cmd, name, task, walltime, activate_freesurfer, cd_cmd):
        self.NIMB_tmp = vars_local["NIMB_PATHS"]['NIMB_tmp']
        self.vars_local = vars_local
        self.activate_freesurfer = activate_freesurfer
        self.cd_cmd = cd_cmd
        self.job_id = '0'
        self.submit_4_processing(vars_local["PROCESSING"]["processing_env"],
                                    cmd, name, task, walltime)
        print(self.job_id)

    def submit_4_processing(self, processing_env, cmd, name, task, walltime):
        if processing_env == 'slurm':
            sh_file = self.make_submit_file(cmd, name, task, walltime)
            if self.vars_local["PROCESSING"]["SUBMIT"] == 1:
                print('        SUBMITTING is ALLOWED')
                self.submit_2scheduler(sh_file)
            else:
                print('        SUBMITTING is stopped')
        elif processing_env == 'tmux':
            if self.vars_local["PROCESSING"]["SUBMIT"] == 1:
                print('        SUBMITTING is ALLOWED')
                submit_2tmux(cmd, name)
            else:
                print('        SUBMITTING is stopped')
        else:
            print('ERROR: processing environment not provided or incorrect')

    def get_submit_file_names(self, name, task):
        dt = time.strftime("%Y%m%d_%H%M",time.localtime(time.time()))
        sh_file = name+'_'+task+'_'+str(dt)+'.sh'
        out_file = name+'_'+task+'_'+str(dt)+'.out'
        return sh_file, out_file

    def make_submit_file(self, cmd, name, task, walltime):
        sh_file, out_file = self.get_submit_file_names(name, task)
        with open(path.join(self.NIMB_tmp, 'usedpbs', sh_file), 'w') as f:
            for line in self.vars_local['PROCESSING']["text4_scheduler"]:
                f.write(line+'\n')
            f.write(self.vars_local['PROCESSING']["batch_walltime_cmd"]+walltime+'\n')
            f.write(self.vars_local['PROCESSING']["batch_output_cmd"]+path.join(self.NIMB_tmp,'usedpbs',out_file)+'\n')
            if self.activate_freesurfer:
                f.write(self.vars_local['FREESURFER']["export_FreeSurfer_cmd"]+'\n')
                f.write(self.vars_local['FREESURFER']["source_FreeSurfer_cmd"]+'\n')
                f.write('export SUBJECTS_DIR='+self.vars_local['FREESURFER']["FS_SUBJECTS_DIR"]+'\n')
            if self.cd_cmd:
                f.write(self.cd_cmd+'\n')
            f.write(cmd+'\n')
        return sh_file
    
    def submit_2scheduler(self, sh_file):
        print('    submitting '+sh_file)
        time.sleep(1)
        try:
            resp = subprocess.run(['sbatch',path.join(self.NIMB_tmp,'usedpbs',sh_file)], stdout=subprocess.PIPE).stdout.decode('utf-8')
            self.job_id = list(filter(None, resp.split(' ')))[-1].strip('\n')
        except Exception as e:
            print(e)

    def submit_2tmux(cmd, subjid):
        self.job_id = 'tmux_'+str(subjid)
        print('    submitting to tmux session:'+self.job_id)
        system('tmux new -d -s {}'.format(self.job_id))
        if self.activate_freesurfer:
            system('tmux send-keys -t {0} \"{1}\" ENTER'.format(str(self.job_id), self.vars_local['FREESURFER']["export_FreeSurfer_cmd"]))
            system('tmux send-keys -t {0} \"{1}\" ENTER'.format(str(self.job_id), self.vars_local['FREESURFER']["source_FreeSurfer_cmd"]))
            system('tmux send-keys -t {0} \"export SUBJECTS_DIR={1}\" ENTER'.format(str(self.job_id), self.vars_local['FREESURFER']["FS_SUBJECTS_DIR"]))
        if self.cd_cmd:
            system('tmux send-keys -t {0} \"{1}\" ENTER'.format(str(self.job_id),self.cd_cmd+'\" ENTER'))
        system('tmux send-keys -t {0} \"{1}\" ENTER'.format(str(self.job_id),cmd))


def kill_tmux_session(session):
    system('tmux kill-session -t {}'.format(session))


# start_fs_pipeline =
# Submit_task(vars_local,
#             vars_local['NIMB_PATHS']["miniconda_python_run"]+' fs_glm_runglm.py -project '+project,
#           'nimb','fs_glm_run', vars_local['PROCESSING']["batch_walltime"],
#            True, 'cd '+path.join(vars_local["NIMB_PATHS"]["NIMB_HOME"], 'processing', 'freesurfer')

def start_fs_glm_runglm(vars_local, project):

    datehour = time.strftime("%Y%m%d_%H%M",time.localtime(time.time()))

    sh_file = 'nimb_fs_glm_run_'+datehour+'.sh'
    out_file = 'nimb_fs_glm_run_'+datehour+'.out'

    with open(path.join(vars_local["NIMB_PATHS"]["NIMB_tmp"], 'usedpbs', sh_file),'w') as f:
        for line in vars_local['PROCESSING']["text4_scheduler"]:
            f.write(line+'\n')
        f.write(vars_local['PROCESSING']["batch_walltime_cmd"]+vars_local['PROCESSING']["batch_walltime"]+'\n')
        f.write(vars_local['PROCESSING']["batch_output_cmd"]+path.join(vars_local["NIMB_PATHS"]["NIMB_tmp"],'usedpbs',out_file)+'\n')
        f.write('\n')
        f.write(vars_local['FREESURFER']["export_FreeSurfer_cmd"]+'\n')
        f.write(vars_local['FREESURFER']["source_FreeSurfer_cmd"]+'\n')
        f.write('export SUBJECTS_DIR='+vars_local['FREESURFER']["FS_SUBJECTS_DIR"]+'\n')
        f.write('cd '+path.join(vars_local["NIMB_PATHS"]["NIMB_HOME"], 'processing', 'freesurfer')+'\n')
        f.write(vars_local['NIMB_PATHS']["miniconda_python_run"]+' fs_glm_runglm.py -project '+project)

    try:
        log = logging.getLogger(__name__)
        log.info('    '+sh_file+' submitting')
        resp = subprocess.run([vars_local['PROCESSING']["submit_cmd"],path.join(vars_local["NIMB_PATHS"]["NIMB_tmp"], 'usedpbs', sh_file)], stdout=subprocess.PIPE).stdout.decode('utf-8')
        print(list(filter(None, resp.split(' ')))[-1].strip('\n'))
    except Exception as e:
        print(e)



