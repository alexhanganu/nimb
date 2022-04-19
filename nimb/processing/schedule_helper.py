from os import path, environ, system
import time
import subprocess
import logging
from datetime import datetime, timedelta
from processing.freesurfer.fs_definitions import FSProcesses
from distribution.distribution_definitions import DEFAULT
from sys import platform

environ['TZ'] = 'US/Eastern'
if platform != "win32":
    time.tzset()

class Scheduler():

    def __init__(self, vars_local):
        self.vars_local       = vars_local
        self.NIMB_tmp         = self.vars_local["NIMB_PATHS"]['NIMB_tmp']
        self.fs_subjects_dir  = self.vars_local["FREESURFER"]["SUBJECTS_DIR"]
        self.export_freesurfer_cmd = self.vars_local["FREESURFER"]["export_FreeSurfer_cmd"]
        self.source_freesurfer_cmd = self.vars_local["FREESURFER"]["source_FreeSurfer_cmd"]
        self.processing_env   = self.vars_local["PROCESSING"]["processing_env"]
        self.python_load_cmd       = self.vars_local['PROCESSING']["python3_load_cmd"]


    def submit_4_processing(self, cmd, name, task, cd_cmd = '',
                            activate_fs = True,
                            python_load = False):
        self.activate_fs = activate_fs
        self.python_load = python_load
        self.job_id = '0'
        if self.vars_local["PROCESSING"]["SUBMIT"] == 1:
            if self.processing_env == 'slurm':
                self.make_submit_file(cmd, name, task, cd_cmd)
                self.submit_2scheduler()
            elif self.processing_env == 'tmux':
                self.submit_2tmux(cmd, name, cd_cmd)
            else:
                print('ERROR: processing environment not provided or incorrect')
        else:
            print('        SUBMITTING is stopped')
        return self.job_id


    def get_submit_file_names(self, name, task):
        dt = time.strftime("%Y%m%d_%H%M",time.localtime(time.time()))
        files_root = f'{name}_{task}_{str(dt)}'
        sh_file = f'{files_root}.sh'
        out_file = f'{files_root}.out'
        return sh_file, out_file


    def Get_walltime(self, process):
        FSProcs = FSProcesses("7.2.0")
        max_walltime = self.vars_local['PROCESSING']["batch_walltime"]
        walltime = max_walltime
        duration = FSProcs.get_suggested_times()

        if process in duration:
            if duration[process] <= max_walltime:
                walltime = duration[process]
        return walltime


    def get_time_end_of_walltime(self, process):
        if process == 'now':
            return str(format(datetime.now(), "%Y%m%d_%H%M"))
        else:
            cluster_time_format = self.vars_local['PROCESSING']["walltime_format"]
            nr_hours = datetime.strptime(self.Get_walltime(process), cluster_time_format).hour
            return str(format(datetime.now()+timedelta(hours=nr_hours), DEFAULT.nimb_time_format))


    def make_submit_file(self, cmd, name, task, cd_cmd):
        sh_file, out_file = self.get_submit_file_names(name, task)
        self.sh_f_abspath = path.join(self.NIMB_tmp, 'usedpbs', sh_file)
        out_file_abspath  = path.join(self.NIMB_tmp, 'usedpbs', out_file)
        walltime_cmd      = self.vars_local['PROCESSING']["batch_walltime_cmd"]
        output_cmd        = self.vars_local['PROCESSING']["batch_output_cmd"]
        scheduler_text    = self.vars_local['PROCESSING']["text4_scheduler"]

        with open(self.sh_f_abspath, 'w') as f:
            for line in scheduler_text:
                f.write(line+'\n')
            f.write(walltime_cmd+self.Get_walltime(task)+'\n')
            f.write(output_cmd+out_file_abspath+'\n')
            if self.activate_fs:
                f.write(self.export_freesurfer_cmd+'\n')
                f.write(self.source_freesurfer_cmd+'\n')
                f.write('export SUBJECTS_DIR='+self.fs_subjects_dir+'\n')
            if cd_cmd:
                f.write(cd_cmd+'\n')
            if self.python_load:
                f.write(self.python_load_cmd+'\n')
            f.write(cmd+'\n')


    def submit_2scheduler(self):
        print(f'        submitting {self.sh_f_abspath}')
        time.sleep(1)
        try:
            resp = subprocess.run(['sbatch', self.sh_f_abspath], stdout=subprocess.PIPE).stdout.decode('utf-8')
            self.job_id = list(filter(None, resp.split(' ')))[-1].strip('\n')
        except Exception as e:
            print(e)


    def submit_2tmux(self, cmd, subjid, cd_cmd):
        dt = time.strftime("%Y%m%d_%H%M",time.localtime(time.time()))
        self.job_id = str(f'tmux_{str(subjid)}_{dt}')
        print(f'        submitting to tmux session: {self.job_id}')
        system(f'tmux new -d -s {self.job_id}')
        if self.activate_fs:
            system(f"tmux send-keys -t '{self.job_id}' '{self.export_freesurfer_cmd}' ENTER")
            system(f"tmux send-keys -t '{self.job_id}' 'export SUBJECTS_DIR=' '{self.fs_subjects_dir}' ENTER")
            system(f"tmux send-keys -t '{self.job_id}' '{self.source_freesurfer_cmd}' ENTER")
        if cd_cmd:
            system(f"tmux send-keys -t '{self.job_id}' '{cd_cmd}' ENTER")
        if self.python_load:
            system(f"tmux send-keys -t '{self.job_id}' '{self.python_load_cmd}' ENTER")
        system(f"tmux send-keys -t '{self.job_id}' '{cmd}' ENTER")


    def kill_tmux_session(self, session):
        system('tmux kill-session -t {}'.format(session))


    def get_jobs_status(self, user, RUNNING_JOBS):
        if self.processing_env == 'slurm':
            return self.get_scheduler_jobs(user)
        elif self.processing_env == 'tmux':
            return self.get_tmux_jobs(RUNNING_JOBS)


    def get_scheduler_jobs(self, user):
        scheduler_jobs = dict()
        queue = list(filter(None,subprocess.run(['squeue','-u',user], stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')))
        for line in queue[1:]:
                vals = list(filter(None,line.split(' ')))
                scheduler_jobs[vals[0]] = [vals[3], vals[4]]
        return scheduler_jobs

    def get_tmux_jobs(self, RUNNING_JOBS):
        return {i:[k, 'tmux'] for k, i in RUNNING_JOBS.items() if type(i) == str and 'tmux' in i}


def get_jobs_status(user):
    scheduler_jobs = dict()
    queue = list(filter(None,subprocess.run(['squeue','-u',user], stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')))
    for line in queue[1:]:
            vals = list(filter(None,line.split(' ')))
            scheduler_jobs[vals[0]] = [vals[3], vals[4]]
    return scheduler_jobs
