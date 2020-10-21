from os import path, environ, system
import time
import subprocess
import logging
log = logging.getLogger(__name__)

environ['TZ'] = 'US/Eastern'
time.tzset()


class Submit_task():

    def __init__(self, vars_local, cmd, name, task, walltime, activate_freesurfer, cd_cmd):
        self.NIMB_tmp = vars_local["NIMB_PATHS"]['NIMB_tmp']
        self.vars_local = vars_local
        self.activate_freesurfer = activate_freesurfer
        self.cd_cmd = cd_cmd
        self.job_id = '0'
        self.submit_4_processing(vars_local["PROCESSING"]["processing_env"],
                                    cmd, name, task, walltime)

    def submit_4_processing(self, processing_env, cmd, name, task, walltime):
        if self.vars_local["PROCESSING"]["SUBMIT"] == 1:
            if processing_env == 'slurm':
                sh_file = self.make_submit_file(cmd, name, task, walltime)
                self.submit_2scheduler(sh_file)
            elif processing_env == 'tmux':
                self.submit_2tmux(cmd, name)
            else:
                log.info('ERROR: processing environment not provided or incorrect')
        else:
            log.info('        SUBMITTING is stopped')

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
        log.info('        submitting {}'.format(sh_file))
        time.sleep(1)
        try:
            resp = subprocess.run(['sbatch',path.join(self.NIMB_tmp,'usedpbs',sh_file)], stdout=subprocess.PIPE).stdout.decode('utf-8')
            self.job_id = list(filter(None, resp.split(' ')))[-1].strip('\n')
        except Exception as e:
            log.info(e)

    def submit_2tmux(self, cmd, subjid):
        self.job_id = 'tmux_'+str(subjid)
        log.info('        submitting to tmux session: {}'.format(self.job_id))
        system('tmux new -d -s {}'.format(self.job_id))
        if self.activate_freesurfer:
            system("tmux send-keys -t '{}' '{}' ENTER".format(str(self.job_id), self.vars_local["FREESURFER"]["export_FreeSurfer_cmd"]))
            system("tmux send-keys -t '{}' 'export SUBJECTS_DIR=' '{}' ENTER".format(str(self.job_id), self.vars_local["FREESURFER"]["FS_SUBJECTS_DIR"]))
            system("tmux send-keys -t '{}' '{}' ENTER".format(str(self.job_id), self.vars_local["FREESURFER"]["source_FreeSurfer_cmd"]))
        if self.cd_cmd:
            system("tmux send-keys -t '{}' '{}' ENTER".format(str(self.job_id), self.cd_cmd))
        system("tmux send-keys -t '{}' '{}' ENTER".format(str(self.job_id), cmd))


def kill_tmux_session(session):
    system('tmux kill-session -t {}'.format(session))


def get_jobs_status(user):
    scheduler_jobs = dict()
    queue = list(filter(None,subprocess.run(['squeue','-u',user], stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')))
    for line in queue[1:]:
            vals = list(filter(None,line.split(' ')))
            scheduler_jobs[vals[0]] = [vals[3], vals[4]]
    return scheduler_jobs


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

