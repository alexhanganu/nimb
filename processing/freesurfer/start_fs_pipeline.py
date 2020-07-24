from os import path
import datetime
import subprocess
import cdb

if path.isfile('vars.json'):
    with open('vars.json') as vars_json:
        vars = json.load(vars_json)
else:
    print('ERROR: vars.json file MISSING')



date=datetime.datetime.now()
dt=str(date.year)+str(date.month)+str(date.day)

if not path.exists(path.join(vars["NIMB_PATHS"]["NIMB_tmp"],'usedpbs')):
    mkdir(path.join(vars["NIMB_PATHS"]["NIMB_tmp"],'usedpbs'))


sh_file = 'nimb_run_'+str(dt)+'.sh'
out_file = 'nimb_run_'+str(dt)+'.out'

with open(vars["NIMB_PATHS"]["NIMB_tmp"]+'usedpbs/'+sh_file,'w') as f:
    for line in vars["text4_scheduler"]:
        f.write(line+'\n')
    f.write(vars["batch_walltime_cmd"]+vars["batch_walltime"]+'\n')
    f.write(vars["batch_output_cmd"]+path.join(vars["NIMB_PATHS"]["NIMB_tmp"],'usedpbs',out_file)+'\n')
    f.write('\n')
    f.write('cd '+vars["NIMB_PATHS"]["NIMB_HOME"]+'\n')
    f.write(vars["python3_load_cmd"]+'\n')
    f.write(vars["python3_run_cmd"]+' processing/freesurfer/crun.py\n')

cdb.Update_status_log('    '+sh_file+' submitting')
try:
        resp = subprocess.run([vars["submit_cmd"],vars["NIMB_PATHS"]["NIMB_tmp"]+'usedpbs/'+sh_file], stdout=subprocess.PIPE).stdout.decode('utf-8')
        print(list(filter(None, resp.split(' ')))[-1].strip('\n'))
except Exception as e:
        print(e)
