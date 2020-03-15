import time
from lib.var import local_maindir
from lib.clusters_data import clusters_data as clusters


def Update_status_log(cmd):
    dthm = time.strftime('%Y/%m/%d %H:%M')
    with open(local_maindir+'status.log','a') as f:
        f.write(dthm+' '+cmd+'\n')


def Update_DB(db):
    file = local_maindir+'a/db_local.py'
    open(file,'w').close()
    with open(file,'a') as f:
        for key in db:
            f.write(key+'={')
            for subkey in db[key]:
                f.write('\''+subkey+'\':[')
                for value in sorted(db[key][subkey]):
                    f.write('\''+value+'\',')
                f.write('],')
            f.write('}\n')


def update_subj2restart_cluster(subjid, cluster):
    file = 'subj2restart_'+cluster
    with open(local_maindir+'a/'+file,'a') as f:
        f.write(subjid+'\n')


def _get_credentials(cred):
    cuser = clusters[cred][0]
    caddress = clusters[cred][1]
    cmaindir = clusters[cred][2]
    cpw = clusters[cred][3]
    return cuser, caddress, cmaindir, cpw

