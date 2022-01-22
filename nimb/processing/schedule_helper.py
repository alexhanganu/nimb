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
        self.processing_env   = self.vars_local["PROCESSING"]["processing_env"]


    def submit_4_processing(self, cmd, name, task, cd_cmd = '',
                            activate_fs = True,
                            python_load = False):
        self.activate_fs = activate_fs
        self.python_load = python_load
        self.job_id = '0'
        if self.vars_local["PROCESSING"]["SUBMIT"] == 1:
            if self.processing_env == 'slurm':
                sh_file = self.make_submit_file(cmd, name, task, cd_cmd)
                self.submit_2scheduler(sh_file)
            elif self.processing_env == 'tmux':
                self.submit_2tmux(cmd, name, cd_cmd)
            else:
                print('ERROR: processing environment not provided or incorrect')
        else:
            print('        SUBMITTING is stopped')
        return self.job_id


    def get_submit_file_names(self, name, task):
        dt = time.strftime("%Y%m%d_%H%M",time.localtime(time.time()))
        sh_file = '{}_{}_{}.sh'.format(name, task, str(dt))
        out_file = '{}_{}_{}.out'.format(name, task, str(dt))
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
        with open(path.join(self.NIMB_tmp, 'usedpbs', sh_file), 'w') as f:
            for line in self.vars_local['PROCESSING']["text4_scheduler"]:
                f.write(line+'\n')
            f.write(self.vars_local['PROCESSING']["batch_walltime_cmd"]+self.Get_walltime(task)+'\n')
            f.write(self.vars_local['PROCESSING']["batch_output_cmd"]+path.join(self.NIMB_tmp,'usedpbs',out_file)+'\n')
            if self.activate_fs:
                f.write(self.vars_local['FREESURFER']["export_FreeSurfer_cmd"]+'\n')
                f.write(self.vars_local['FREESURFER']["source_FreeSurfer_cmd"]+'\n')
                f.write('export SUBJECTS_DIR='+self.vars_local['FREESURFER']["FS_SUBJECTS_DIR"]+'\n')
            if cd_cmd:
                f.write(cd_cmd+'\n')
            if self.python_load:
                f.write(self.vars_local['PROCESSING']["python3_load_cmd"]+'\n')
            f.write(cmd+'\n')
        return sh_file


    def submit_2scheduler(self, sh_file):
        print('        submitting {}'.format(sh_file))
        time.sleep(1)
        try:
            resp = subprocess.run(['sbatch',path.join(self.NIMB_tmp,'usedpbs',sh_file)], stdout=subprocess.PIPE).stdout.decode('utf-8')
            self.job_id = list(filter(None, resp.split(' ')))[-1].strip('\n')
        except Exception as e:
            print(e)


    def submit_2tmux(self, cmd, subjid, cd_cmd):
        dt = time.strftime("%Y%m%d_%H%M",time.localtime(time.time()))
        self.job_id = 'tmux_'+str(subjid)+"_"+dt
        print('        submitting to tmux session: {}'.format(self.job_id))
        system('tmux new -d -s {}'.format(self.job_id))
        if self.activate_fs:
            system("tmux send-keys -t '{}' '{}' ENTER".format(str(self.job_id), self.vars_local["FREESURFER"]["export_FreeSurfer_cmd"]))
            system("tmux send-keys -t '{}' 'export SUBJECTS_DIR=' '{}' ENTER".format(str(self.job_id), self.vars_local["FREESURFER"]["FS_SUBJECTS_DIR"]))
            system("tmux send-keys -t '{}' '{}' ENTER".format(str(self.job_id), self.vars_local["FREESURFER"]["source_FreeSurfer_cmd"]))
        if cd_cmd:
            system("tmux send-keys -t '{}' '{}' ENTER".format(str(self.job_id), cd_cmd))
        if self.python_load:
            system("tmux send-keys -t '{}' '{}' ENTER".format(str(self.job_id),
                                                              self.vars_local['PROCESSING']["python3_load_cmd"]))
        system("tmux send-keys -t '{}' '{}' ENTER".format(str(self.job_id), cmd))


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
