from os import path
from variables import text4_scheduler, batch_walltime_cmd, batch_walltime, batch_output_cmd, submit_cmd, python3_load_cmd, python3_run_cmd, nimb_dir, nimb_scratch_dir
import datetime, subprocess
import cdb



date=datetime.datetime.now()
dt=str(date.year)+str(date.month)+str(date.day)

if not path.exists(path.join(nimb_scratch_dir,'usedpbs')):
    mkdir(path.join(nimb_scratch_dir,'usedpbs'))


sh_file = 'nimb_run_'+str(dt)+'.sh'
out_file = 'nimb_run_'+str(dt)+'.out'

with open(nimb_scratch_dir+'usedpbs/'+sh_file,'a') as f:
    for line in text4_scheduler:
        f.write(line+'\n')
    f.write(batch_walltime_cmd+batch_walltime+'\n')
    f.write(batch_output_cmd+path.join(nimb_scratch_dir,'usedpbs',out_file)+'\n')
    f.write('\n')
    f.write('cd '+nimb_dir+'a/clib\n')
    f.write(python3_load_cmd+'\n')
    f.write(python3_run_cmd+' crun.py\n')

cdb.Update_status_log('    '+sh_file+' submitting')
try:
        resp = subprocess.run([submit_cmd,nimb_scratch_dir+'usedpbs/'+sh_file], stdout=subprocess.PIPE).stdout.decode('utf-8')
        print(list(filter(None, resp.split(' ')))[-1].strip('\n'))
except Exception as e:
        print(e)
