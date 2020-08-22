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
        f.write(vars_local['PROCESSING']["python3_load_cmd"]+'\n')
        f.write(vars_local['PROCESSING']["python3_run_cmd"]+' crun.py')

    try:
        log = logging.getLogger(__name__)
        log.info('    '+sh_file+' submitting')
        print('ready to start fs pipeline')
        resp = subprocess.run([vars_local['PROCESSING']["submit_cmd"],path.join(vars_local["NIMB_PATHS"]["NIMB_tmp"], 'usedpbs', sh_file)], stdout=subprocess.PIPE).stdout.decode('utf-8')
        print(list(filter(None, resp.split(' ')))[-1].strip('\n'))
    except Exception as e:
        print(e)


