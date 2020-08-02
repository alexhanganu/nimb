#!/bin/python
#Alexandru Hanganu, 2018 June 26
# sys.path.append('../..')
# sys.path.insert(0,'..')
from os import rename, path, listdir, system, makedirs, remove
import datetime, time, shutil
from lib.var import local_maindir
# from .. import local_runfs, local_db
from ..lib import local_runfs, local_db

date=datetime.datetime.now()
dt=str(date.year)+str(date.month)+str(date.day)
dth=str(date.year)+'/'+str(date.month)+'/'+str(date.day)+' '+str(date.hour)+'h'

fsDIR = local_maindir+'freesurfer/subjects/'
process_order = ('registration','recon','qcache','hip','brstem','masks')#,'lgi','qcache_lgi')


DO_main = {'registration':[],'recon':[],'hip':[],'brstem':[],'masks':[],'qcache':[],'stats':[],'lgi':[],'qcache_lgi':[],'cp2local':[]}
QUEUE_main = {'registration':[],'recon':[],'hip':[],'brstem':[],'masks':[],'qcache':[],'stats':[],'lgi':[],'qcache_lgi':[]}
RUNNING_main = {'registration':[],'recon':[],'hip':[],'brstem':[],'masks':[],'qcache':[],'lgi':[],'qcache_lgi':[]}
CHECK_main = {'registration':[],'recon':[],'hip':[],'brstem':[],'masks':[],'qcache':[],'stats':[],'lgi':[],'qcache_lgi':[]}
ERROR_main ={'registration':[],'recon':[],'hip':[],'brstem':[],'masks':[],'qcache':[],'stats':[],'IsRunning':[],'lgi':[],'qcache_lgi':[]}
CLUSTER_main = {'hip':[],'brstem':[],'stats':[],'error':[]}

db = {}

if path.isfile(local_maindir+'a/db_local.py'):
    from db_local import DO, QUEUE, RUNNING, CHECK, ERROR, CLUSTER
    db['DO'] = DO
    db['QUEUE'] = QUEUE
    db['RUNNING'] = RUNNING
    db['CHECK'] = CHECK
    db['ERROR'] = ERROR
    db['CLUSTER'] = CLUSTER
else:
    db['DO'] = DO_main
    db['QUEUE'] = QUEUE_main
    db['RUNNING'] = RUNNING_main
    db['CHECK'] = CHECK_main
    db['ERROR'] = ERROR_main
    db['CLUSTER'] = CLUSTER_main
        

def chk_subj2fs():
    if path.isfile(local_maindir+"a/subj2fs"):
        with open(local_maindir+"a/subj2fs",'rt') as readls:
            for line in readls:
                if not local_runfs.chksubjidinfs(line.strip('\r\n')):
                    db['DO']['registration'].append(line.strip('\r\n'))
                else:
                    db['ERROR']['registration'].append(line.strip('\r\n'))
                    local_db.Update_status_log('ERROR: subj2fs was read and wasn\'t added to database')
        rename(local_maindir+'a/subj2fs',local_maindir+'a/z_used_subj2fs'+dt)
        print('subj2fs was read')
        local_db.Update_status_log('subj2fs was read')
    local_db.Update_DB(db)


def chk_subj_in_fsDIR():
    print('reading subjects in freesurfer/subjects folder')
    ls_subjid = []
    for subDIR in listdir(fsDIR):
        if path.isdir(fsDIR+subDIR):
            if 'average' not in subDIR and 'cvs' not in subDIR and 'bert' not in subDIR:
                ls_subjid.append(subDIR)
    print('there are '+str(len(ls_subjid))+' subjects in freesurfer/subjects folder')
    def check_if_subjid_in_db(subjid):
        for GROUP in db:
            for process in db[GROUP]:
                if subjid in db[GROUP][process]:
                    return True
                    break
                else:
                    return False
    while len(ls_subjid)>0:
        for subjid in ls_subjid:
            if not check_if_subjid_in_db(subjid):
                if not local_runfs.chkIsRunning(subjid):
                    if not local_runfs.chk_if_recon_done(subjid):
                        db['DO']['recon'].append(subjid)
                        print(subjid+' DO/recon')
                    elif not local_runfs.chk_masks(subjid):
                        db['DO']['masks'].append(subjid)
                        print(subjid+' DO/masks')
                    elif not local_runfs.chk_if_qcache_done(subjid):
                        db['DO']['qcache'].append(subjid)
                        print(subjid+' DO/qcache')
                    elif not local_runfs.chkhipf(subjid):
                        db['DO']['hip'].append(subjid)
                        print(subjid+' DO/hip')
                    elif not local_runfs.chkbrstemf(subjid):
                        db['DO']['brstem'].append(subjid)
                        print(subjid+' DO/brstem')
                    elif not local_runfs.check_stats(subjid):
                        db['DO']['stats'].append(subjid)
                        print(subjid+' DO/stats')
                    else:
                        if subjid not in db['DO']['cp2local']:
                            db['DO']['cp2local'].append(subjid)
                            print(subjid+' DO/cp2local')
            ls_subjid.remove(subjid)
    local_db.Update_DB(db)


def chk_subj_on_clusters():
    from lib.clusters_data import clusters_data as clusters
    print('CHECKING subjects on clusters')
    for cred in clusters:
        cuser, caddress, cmaindir, cpw = local_db._get_credentials(cred)
        system('sshpass -p '+cpw+' scp '+cuser+'@'+caddress+':'+cmaindir+'a/db.py '+local_maindir+'a/db_from_cluster.py')
        print('checking done')
        if path.isfile(local_maindir+'a/db_from_cluster.py'):
            from db_from_cluster import ERROR
            if len(ERROR['hip'])>0 or len(ERROR['stats'])>0:
                db['CLUSTER']['hip'] = ERROR['hip']
                db['CLUSTER']['stats'] = ERROR['stats']
            local_db.Update_DB(db)
            remove(local_maindir+'a/db_from_cluster.py')
            process_subjects_from_CLUSTER(cred)


def process_subjects_from_CLUSTER(cred):
    cuser, caddress, cmaindir, cpw = local_db._get_credentials(cred)
    while len(db['CLUSTER']['hip'])>0:
        subjid  = db['CLUSTER']['hip'][0]
        print('copying from cluster subjects: '+subjid)
        system('sshpass -p '+cpw+' scp -r '+cuser+'@'+caddress+':'+cmaindir+'freesurfer/subjects/'+subjid+' '+local_maindir+'freesurfer/subjects/')
        if not local_runfs.chkIsRunning(subjid):
            if not local_runfs.chkhipf(subjid):
                local_runfs.runhip(subjid)
                db['CLUSTER']['hip'].remove(subjid)
                db['CLUSTER']['brstem'].append(subjid)
                local_db.Update_DB(db)
                local_runfs.runbrstem(subjid)
                db['CLUSTER']['brstem'].remove(subjid)
                db['CLUSTER']['stats'].append(subjid)
                local_db.Update_DB(db)
                local_runfs.stats(subjid)
            local_db.update_subj2restart_cluster(subjid, cred)
            move_subjects_2_CLUSTER(cred, subjid)
        else:
            remove(fsDIR+subjid+'/scripts/IsRunning.lh+rh')
            db['CLUSTER']['hip'].remove(subjid)
            db['ERROR']['hip'].append(subjid)
    while len(db['CLUSTER']['stats'])>0:
        subjid  = db['CLUSTER']['stats'][0]
        system('sshpass -p '+cpw+' scp -r '+cuser+'@'+caddress+':'+cmaindir+'freesurfer/subjects/'+subjid+' '+local_maindir+'freesurfer/subjects/')
        if not local_runfs.chkIsRunning(subjid):
            if not local_runfs.check_stats(subjid):
                local_runfs.stats(subjid)
                local_db.update_subj2restart_cluster(subjid, cred)
                move_subjects_2_CLUSTER(cred, subjid)
        else:
            db['CLUSTER']['stats'].remove(subjid)
            db['ERROR']['stats'].append(subjid)
    print('copying subj2restart file: '+local_maindir+'a/subj2restart_'+cred+' to location: '+cuser+'@'+caddress+':'+cmaindir+'a/')
    system('sshpass -p '+cpw+' scp -r '+local_maindir+'a/subj2restart_'+cred+' '+cuser+'@'+caddress+':'+cmaindir+'a/')
    remove(local_maindir+'a/subj2restart_'+cred)



def move_subjects_2_CLUSTER(cred,  subjid):
    cuser, caddress, cmaindir, cpw = local_db._get_credentials(cred)
    if local_runfs.chkhipf(subjid) and local_runfs.chkbrstemf(subjid) and local_runfs.check_stats(subjid):
        print('copying to cluster, subject: '+subjid)
        system('sshpass -p '+cpw+' scp -r '+local_maindir+'freesurfer/subjects/'+subjid+' '+cuser+'@'+caddress+':'+cmaindir+'freesurfer/subjects/')
        system('rm -r '+local_maindir+'freesurfer/subjects/'+subjid)
        system('sshpass -p '+cpw+' scp '+local_maindir+'a/res/stats/* '+cuser+'@'+caddress+':'+cmaindir+'a/res/stats/')
        system('rm '+local_maindir+'a/res/stats/*')
        db['CLUSTER']['stats'].remove(subjid)
        local_db.Update_DB(db)			
    else:
        if not path.isdir(local_maindir+'ERROR_from_cluster'):
            makedirs(local_maindir+'ERROR_from_cluster')
        shutil.move(local_maindir+'freesurfer/subjects/'+subjid, local_maindir+'ERROR_from_cluster/'+subjid)
        db['CLUSTER']['stats'].remove(subjid)
        db['CLUSTER']['error'].append(subjid)
        local_db.Update_DB(db)			


def do(process):
    if process == 'registration':
        local_db.Update_status_log('DOING registration active')
        ls_to_register = []
        while len(db['DO']['registration']) != 0:
            for subjid in db['DO']['registration']:
                if not local_runfs.chksubjidinfs(subjid):
                    db['RUNNING']['registration'].append(subjid)
                else:
                    db['CHECK']['registration'].append(subjid)
                db['DO']['registration'].remove(subjid)
        local_runfs.makesubmitpbs_registration(db['RUNNING']['registration'])
        local_db.Update_DB(db)
        local_db.Update_status_log('registration finished')
    elif process == 'recon':
        while len(db['DO']['recon']) > 0:
            for subjid in db['DO']['recon']:
                if not local_runfs.chkIsRunning(subjid):
                    if 'fsaverage' in listdir(fsDIR):
                        if 'xhemi' in listdir(fsDIR+'fsaverage'):
                            db['RUNNING']['recon'].append(subjid)
                            local_runfs.runrecon_all(subjid)
                        else:
                            local_db.Update_status_log('ERROR: fsaverage is MISSING: ' + subjid)
                            db['ERROR']['recon'].append(subjid)
                    else:
                        local_db.Update_status_log('ERROR: fsaverage is MISSING: ' + subjid)
                        db['ERROR']['recon'].append(subjid)
                else:
                    local_db.Update_status_log('ERROR: IsRunning file present: ' + subjid)
                    db['ERROR']['IsRunning'].append(subjid)	
                db['DO']['recon'].remove(subjid)
        db['DO']['recon'] = sorted(db['DO']['recon'])
        local_db.Update_DB(db)
    elif process == 'masks':
        while len(db['DO']['masks']) > 0:
            for subjid in db['DO']['masks']:
                if not local_runfs.chkIsRunning(subjid):
                    db['DO']['masks'].remove(subjid)
                    db['RUNNING']['masks'].append(subjid)
                    local_db.Update_DB(db)
                    print('RUNNING masks for: '+subjid)
                    local_runfs.run_make_masks(subjid)
                    db['RUNNING']['masks'].remove(subjid)
                    db['CHECK']['masks'].append(subjid)
                    local_db.Update_DB(db)
    else:
        while len(db['DO'][process]) > 0:
            for subjid in db['DO'][process]:
                db['DO'][process].remove(subjid)
                db['DO'][process] = sorted(db['DO'][process])
                if not local_runfs.chkIsRunning(subjid):
                    db['RUNNING'][process].append(subjid)
                    local_db.Update_DB(db)
                    if process == 'qcache':
                        local_runfs.runqcache(subjid)
                    elif process == 'hip':
                        local_runfs.runhip(subjid)
                    elif process == 'brstem':
                        local_runfs.runbrstem(subjid)
                    elif process == 'lgi':
                        pass
                        #local_runfs.runlgi(subjid)
                    elif process == 'qcache_lgi':
                        pass
                        #local_runfs.runqcache_lgi(subjid)
                    db['RUNNING'][process].remove(subjid)
                    db['CHECK'][process].append(subjid)
                    local_db.Update_DB(db)
                else:
                    db['ERROR']['IsRunning'].append(subjid)
                    local_db.Update_status_log('ERROR: IsRunning file present: ' + subjid)
                    local_db.Update_DB(db)


def running(process):
    local_db.Update_status_log('RUNNING ' + process)
    for subjid in db['RUNNING'][process]:
        if path.isdir(fsDIR+subjid):
            if not local_runfs.chkIsRunning(subjid):
                local_db.Update_status_log('moving ' + subjid + ' from RUNNING ' + process + ' to CHECK ' + process)
                db['CHECK'][process].append(subjid)
                db['RUNNING'][process].remove(subjid)
                db['CHECK'][process] = sorted(db['CHECK'][process])
                db['RUNNING'][process] = sorted(db['RUNNING'][process])
                local_db.Update_DB(db)


def check(process):
    count = 1
    while len(db['CHECK'][process])>0:
        local_db.Update_status_log('CHECKING ' + process + ' active ' + str(count))
        for subjid in db['CHECK'][process]:
            if not local_runfs.chkIsRunning(subjid):
                if local_runfs.chkreconf(subjid):
                    if process == 'registration':
                        db['DO']['recon'].append(subjid)
                        local_db.Update_status_log('moving ' + subjid + ' from CHECK ' + process + ' to DO recon')
                    elif process == 'recon':
                        if local_runfs.chk_if_recon_done(subjid):
                            if not local_runfs.chk_masks(subjid):
                                db['DO']['masks'].append(subjid)
                                local_db.Update_status_log('moving ' + subjid + ' from CHECK ' + process + ' to DO masks')
                            else:
                                db['CHECK']['qcache'].append(subjid)
                        else:
                            db['ERROR'][process].append(subjid)
                    elif process == 'masks':
                        if local_runfs.chk_masks(subjid):
                            if not local_runfs.chk_if_qcache_done(subjid):
                                db['DO']['qcache'].append(subjid)
                                local_db.Update_status_log('moving ' + subjid + ' from CHECK ' + process + ' to DO qcache')
                            else:
                                db['CHECK']['hip'].append(subjid)
                        else:
                            db['ERROR'][process].append(subjid)
                    elif process == 'qcache':
                        if not local_runfs.chkhipf(subjid):
                            db['DO']['hip'].append(subjid)
                            local_db.Update_status_log('moving ' + subjid + ' from CHECK ' + process + ' to DO hip')
                        else:
                            db['CHECK']['brstem'].append(subjid)
                    elif process == 'hip':
                        if local_runfs.chkhipf(subjid):
                            if not local_runfs.chkbrstemf(subjid):
                                db['DO']['brstem'].append(subjid)
                                local_db.Update_status_log('moving ' + subjid + ' from CHECK ' + process + ' to DO brstem')
                            else:
                                db['CHECK']['stats'].append(subjid)
                        else:
                            db['ERROR']['hip'].append(subjid)
                    elif process == 'brstem':
                        if local_runfs.chkbrstemf(subjid):
                            if not local_runfs.check_stats(subjid):
                                if subjid not in db['DO']['stats']:
                                    db['DO']['stats'].append(subjid)
                                    local_db.Update_status_log('moving ' + subjid + ' from CHECK ' + process + ' to DO stats')
                                    #db['DO']['lgi'].append(subjid) 
                            else:
                                db['DO']['cp2local'].append(subjid)
                        else:
                            db['ERROR'][process].append(subjid)
                    elif process == 'lgi':
                            pass
                            #db['DO']['qcache_lgi'].append(subjid)
                    elif process == 'qcache_lgi':
                            pass
                else:
                    local_db.Update_status_log('ERROR: ' + subjid + ' : recon-all finished with error for :' + process)
                    db['ERROR'][process].append(subjid)
            else:
                db['ERROR']['IsRunning'].append(subjid)
            db['CHECK'][process].remove(subjid)
            db['CHECK'][process] = sorted(db['CHECK'][process])
            local_db.Update_DB(db)
        count += 1


def run():
    chk_subj2fs()
    for process in process_order:
        if len(db['DO'][process])>0:
            do(process)
        if len(db['RUNNING'][process])>0:
            running(process)
        if len(db['CHECK'][process])>0:
            check(process)

    if len(db['DO']['stats'])>0:
        for subjid in db['DO']['stats']:
            if not local_runfs.chkIsRunning(subjid):
                local_runfs.stats(subjid)
                db['CHECK']['stats'].append(subjid)
            else:
                db['ERROR']['IsRunning'].append(subjid)
            db['DO']['stats'].remove(subjid)
            local_db.Update_DB(db)

    if len(db['CHECK']['stats'])>0:
        for subjid in db['CHECK']['stats']:
                if local_runfs.check_stats(subjid):
                    db['DO']['cp2local'].append(subjid)
                else:
                    db['ERROR']['stats'].append(subjid)
                db['CHECK']['stats'].remove(subjid)
                local_db.Update_DB(db)
    else:
        local_db.Update_status_log('finished checking all clusters')


def check_active_tasks(db):
    active_subjects = 0
    error = 0
    finished = len(db['DO']['cp2local'])
    for PROCESS in db['ERROR']:
        error = error + len(db['ERROR'][PROCESS])
    for ACTION in db:
        for PROCESS in db[ACTION]:
            active_subjects = active_subjects + len(db[ACTION][PROCESS])
    active_subjects = active_subjects-(finished+error)
    local_db.Update_status_log(str(active_subjects) + ' subjects are being processed' + ' ' + str(finished) + ' subjects were finished' + ' ' + str(error) + ' subjects with errors')
    print(str(active_subjects)+' subjects are being processed'+' '+str(finished)+' subjects were finished'+' '+str(error)+' subjects with errors')
    return active_subjects

open(local_maindir+'status.log','w').close()
chk_subj2fs()
chk_subj_in_fsDIR()
chk_subj_on_clusters()

active_subjects = check_active_tasks(db)
count_run = 0
while active_subjects >0 :
    count_run += 1
    local_db.Update_status_log('restarting run, ' + str(count_run))
    run()
    if len(db['RUNNING']['hip'])>0 or len(db['RUNNING']['brstem'])>0 or len(db['RUNNING']['qcache'])>0:
        time2sleep = 600
    elif len(db['RUNNING']['recon'])>0 and len(db['RUNNING']['registration'])==0 and len(db['RUNNING']['hip'])==0 and len(db['RUNNING']['brstem'])==0 and len(db['RUNNING']['qcache'])==0:
        time2sleep = 1500
    else:
        time2sleep = 60
    print(str(dth)+'; waiting: '+str(time2sleep))
    time.sleep(time2sleep)
    active_subjects = check_active_tasks(db)
print('ALL TASKS FINISHED')
local_db.Update_status_log('ALL TASKS FINISHED')
	
