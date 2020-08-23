from os import path, environ
import time
import subprocess
import logging

environ['TZ'] = 'US/Eastern'
time.tzset()


class Submit2Process():

    def __init__(self, vars_local):
        self.NIMB_tmp = vars_local['NIMB_tmp']
        self.job_id = '0'
        if params["SUBMIT"] == 1:
            print('SUBMITTING is ALLOWED')

        
    def submit_4_processing(self, processing_env, cmd, subjid, run, walltime):
        if processing_env == 'slurm':
            makesubmitpbs(cmd, subjid, run, walltime)
        elif processing_env == 'tmux':
            submit_tmux(cmd, subjid)
        else:
            print('ERROR: processing environment not provided or incorrect')
        return job_id


    def submit_scheduler(self, cmd, subjid, run, walltime, params):

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

            time.sleep(2)
            try:
                resp = subprocess.run(['sbatch',path.join(params["NIMB_tmp"],'usedpbs',sh_file)], stdout=subprocess.PIPE).stdout.decode('utf-8')
                self.job_id = list(filter(None, resp.split(' ')))[-1].strip('\n')
            except Exception as e:
                print(e)
        else:
            print('SUBMITTING is stopped')


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
        f.write(vars_local['PROCESSING']["python3_load_cmd"]+'\n')
        f.write(vars_local['PROCESSING']["python3_run_cmd"]+' crun.py')

    try:
        log = logging.getLogger(__name__)
        log.info('    '+sh_file+' submitting')
        resp = subprocess.run([vars_local['PROCESSING']["submit_cmd"],path.join(vars_local["NIMB_PATHS"]["NIMB_tmp"], 'usedpbs', sh_file)], stdout=subprocess.PIPE).stdout.decode('utf-8')
        print(list(filter(None, resp.split(' ')))[-1].strip('\n'))
    except Exception as e:
        print(e)


