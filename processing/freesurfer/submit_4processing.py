from os import path, environ
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

class Submit_task():

    def __init__(self, vars_local, cmd, name, task, walltime, activate_freesurfer, cd_cmd):
        self.NIMB_tmp = vars_local['NIMB_tmp']
        self.vars_local = vars_local
        self.activate_freesurfer = activate_freesurfer
        self.cd_cmd = cd_cmd
        self.job_id = '0'
        if vars_local["PROCESSING"]["SUBMIT"] == 1:
            print('        SUBMITTING is ALLOWED')
            self.submit_4_processing(vars_local["PROCESSING"]["processing_env"],
                                    cmd, name, task, walltime)
        else:
            print('        SUBMITTING is stopped')
        
    def submit_4_processing(self, processing_env, cmd, name, task, walltime):
        if processing_env == 'slurm':
            sh_file = self.make_submit_file(cmd, name, task, walltime)
            self.submit_2scheduler(sh_file)
        elif processing_env == 'tmux':
            submit_2tmux(cmd, name)
        else:
            print('ERROR: processing environment not provided or incorrect')

    def get_submit_file_names(self, name, task):
        date=datetime.datetime.now()
        dt=str(date.year)+str(date.month)+str(date.day)
        sh_file = name+'_'+task+'_'+str(dt)+'.sh'
        out_file = name+'_'+task+'_'+str(dt)+'.out'
        return sh_file, out_file

    def make_submit_file(self, cmd, name, task, walltime):
        sh_file, out_file = self.get_submit_file_names(name, task)
        with open(path.join(self.vars_local["NIMB_tmp"], 'usedpbs', sh_file), 'w') as f:
            for line in self.vars_local["text4_scheduler"]:
                f.write(line+'\n')
            f.write(self.vars_local["batch_walltime_cmd"]+walltime+'\n')
            f.write(self.vars_local["batch_output_cmd"]+path.join(self.vars_local["NIMB_tmp"],'usedpbs',out_file)+'\n')
            if self.activate_freesurfer:
                f.write(self.vars_local["export_FreeSurfer_cmd"]+'\n')
                f.write(self.vars_local["source_FreeSurfer_cmd"]+'\n')
                f.write('export SUBJECTS_DIR='+self.vars_local["SUBJECTS_DIR"]+'\n')
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
        tmux_session = 'tmux_'+str(subjid)
        print('    submitting to tmux session:'+tmux_session)
        system('tmux new -d -s {}'.format(tmux_session))
        if self.activate_freesurfer:
            system('tmux send-keys -t {0} \"{1}\" ENTER'.format(str(tmux_session), self.vars_local["export_FreeSurfer_cmd"]))
            system('tmux send-keys -t {0} \"{1}\" ENTER'.format(str(tmux_session), self.vars_local["source_FreeSurfer_cmd"]))
            system('tmux send-keys -t {0} \"export SUBJECTS_DIR={1}\" ENTER'.format(str(tmux_session), self.vars_local["SUBJECTS_DIR"]))
        if self.cd_cmd:
            system('tmux send-keys -t {0} \"{1}\" ENTER'.format(str(tmux_session),self.cd_cmd+'\" ENTER'))
        system('tmux send-keys -t {0} \"{1}\" ENTER'.format(str(tmux_session),cmd))
        return tmux_session


def kill_tmux_session(session):
    system('tmux kill-session -t {}'.format(session))



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
        f.write('cd '+path.join(vars_local["NIMB_PATHS"]["NIMB_HOME"], 'processing', 'freesurfer')+'\n')
        f.write(vars_local['NIMB_PATHS']["miniconda_python_run"]+' fs_glm_runglm.py -project '+project)

    try:
        log = logging.getLogger(__name__)
        log.info('    '+sh_file+' submitting')
        resp = subprocess.run([vars_local['PROCESSING']["submit_cmd"],path.join(vars_local["NIMB_PATHS"]["NIMB_tmp"], 'usedpbs', sh_file)], stdout=subprocess.PIPE).stdout.decode('utf-8')
        print(list(filter(None, resp.split(' ')))[-1].strip('\n'))
    except Exception as e:
        print(e)