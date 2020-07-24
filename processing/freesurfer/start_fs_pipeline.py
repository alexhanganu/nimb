from os import path, mkdir, environ
import time
import subprocess
import json
from . import cdb

environ['TZ'] = 'US/Eastern'
time.tzset()


if path.isfile('processing/freesurfer/vars.json'):
    with open('processing/freesurfer/vars.json') as vars_json:
        vars = json.load(vars_json)
else:
    print('ERROR: vars.json file MISSING')



datehour = time.strftime("%Y%m%d_%H%M",time.localtime(time.time()))

if not path.exists(path.join(vars["NIMB_PATHS"]["NIMB_tmp"],'usedpbs')):
    mkdir(path.join(vars["NIMB_PATHS"]["NIMB_tmp"],'usedpbs'))


sh_file = 'nimb_run_'+datehour+'.sh'
out_file = 'nimb_run_'+datehour+'.out'

with open(path.join(vars["NIMB_PATHS"]["NIMB_tmp"], 'usedpbs', sh_file),'w') as f:
    for line in vars['PROCESSING']["text4_scheduler"]:
        f.write(line+'\n')
    f.write(vars['PROCESSING']["batch_walltime_cmd"]+vars['PROCESSING']["batch_walltime"]+'\n')
    f.write(vars['PROCESSING']["batch_output_cmd"]+path.join(vars["NIMB_PATHS"]["NIMB_tmp"],'usedpbs',out_file)+'\n')
    f.write('\n')
    f.write('cd '+path.join(vars["NIMB_PATHS"]["NIMB_HOME"], 'procesing', 'freesurfer')+'\n')
    f.write(vars['PROCESSING']["python3_load_cmd"]+'\n')
    f.write(vars['PROCESSING']["python3_run_cmd"]+' crun.py')

cdb.Update_status_log(vars["NIMB_PATHS"]["NIMB_tmp"],'    '+sh_file+' submitting')
try:
        resp = subprocess.run([vars['PROCESSING']["submit_cmd"],path.join(vars["NIMB_PATHS"]["NIMB_tmp"],'usedpbs',sh_file)], stdout=subprocess.PIPE).stdout.decode('utf-8')
        print(list(filter(None, resp.split(' ')))[-1].strip('\n'))
except Exception as e:
        print(e)
