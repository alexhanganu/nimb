#!/bin/python
#2020 06 21

'''
extract stats
zip subjects in subjects_processed
after that is necessary to zip the processed_fs_stats and move it to the corresponding
storage folder (i.e., for ADNI is beluga../projects/../adni)
'''
HOST = 'beluga.calculquebec.ca'
'''
username = 'string' # username to access the remote computer
mot_de_pass = 'string' # password to access the remote computer
HOST = 'name.address.com' # host name of the remote computer
'''


from os import listdir, system, mkdir, path, chdir, getuid, getenv, environ, remove
import shutil, getpass, time
import paramiko

environ['TZ'] = 'US/Eastern'
time.tzset()
dthm = time.strftime('%Y%m%d_%H%M')



def get_username():
    username = ''
    try:
        import pwd
        username = pwd.getpwuid( getuid() ) [0]
        print('username from pwd')
    except ImportError:
        print(e)
    if not username:
        try:
            import getpass
            username = getpass.getuse()
            print('username from getpass')
        except ImportError:
            print('getpass not installed')
    if not username:
        try:
            username = getenv('HOME').split('/')[-1]
            print('username from getenvn')
        except Exception as e:
            print(e)
    return username

username = get_username()
print(username)
path_credentials = path.join('/home',username) # path to the txt-like file named "credentials" that will contain the follow$




path_projects = path.join('/home',username,'projects','def-hanganua')
path_scratch = path.join('/scratch',username)
path_processed = path.join(path_projects,'subjects_processed')

dir_stats = 'processed_fs_stats'
zip_f = dir_stats+'_'+dthm+'.zip'

path_dst_dir_adni = path.join('adni','processed_fs') # on beluga
path_dst_dir_ppmi = path.join('ppmi','processed_fs') # on elm

path_dst_dir = path_dst_dir_adni
path_src = path.join(path_projects,'subjects_processed') # path that contains the files or folders t$
path_log = path.join(path_projects,'scripts','scp_log.txt') # path where a log file will be stored tha$
path_dst = path.join(path_projects,path_dst_dir) # path to the remote folder that the files/ folders w$





path_stats = path.join(path_scratch,dir_stats)


chdir(path_processed)

if not path.exists(path_stats):
    mkdir(path_stats)

stats_dirs = listdir(path_stats)

for subDIR in listdir(path_processed):
    if path.isdir(path.join(path_processed, subDIR)) and subDIR not in stats_dirs:
        print('extracting stats')
        mkdir(path_stats+'/'+subDIR)
        shutil.copytree(path.join(path_processed,subDIR,'stats'),path.join(path_stats,subDIR,'stats'))
        print('archiving ',subDIR)
        system('zip -q -r -m '+subDIR+'.zip '+subDIR)
    elif not path.isdir(path.join(path_processed, subDIR)):
        print(subDIR, ' not a directory')

chdir(path_scratch)
system('zip -q -r -m '+zip_f+' '+dir_stats)
shutil.move(path.join(path_scratch,zip_f), path.join(path_processed,zip_f))




# following scripts will copy from the local remote to the HOST remote at the path_dst path

shutil.copy(path.join(path_credentials,'credentials'), path.dirname(path.abspath(__file__))+'/credentials.py')
try:
        from credentials import mot_de_pass
        remove(path.dirname(path.abspath(__file__))+'/credentials.py')
except ImportError:
        print('file with credentials was not found')
        raise SystemExit()



def _get_client(HOST, username, mot_de_pass):

    # setting up the remote connection
    #  retrieving the list of files in the destination folder
    client = paramiko.SSHClient()
    host_keys = client.load_system_host_keys()
    return client.connect(HOST, username=username, password=mot_de_pass)




def get_ls2copy(client, path_dst, path_src):

    # retrieving the list of files in the source folder
    ls_src = [i for i in listdir(path_src) if '.zip' in i]

    # retrieving the list of files in the destination folder
    ls_dst = list()
    stdin, stdout, stderr = client.exec_command('ls '+path_dst)
    for line in stdout:
            ls_dst.append(line.strip('\n'))

    return [i for i in ls_src if i not in ls_dst]



def cp2remote_rm_from_local(client, ls_copy, path_src, username, HOST, path_dst, path_log):

    # copying the files 
    ls_copy_error = list()
    sftp = client.open_sftp()
    for val in ls_copy:
            size_src = path.getsize(path_src+'/'+val)
            # sftp.put(path_src+'/'+val, path_dst)
            print('left to copy: ',len(ls_copy[ls_copy.index(val):]))
            system('scp '+path_src+'/'+val+' '+username+'@'+HOST+':'+path_dst)
            size_dst = sftp.stat(path_dst+'/'+val).st_size
            if size_dst != size_src:
                    print('        copy error')
                    ls_copy_error.append(val)
            else:
                    remove(path_src+'/'+val)
    saving_ls2log(ls_copy_error, path_log)



def saving_ls2log(ls_copy_error, path_log):
    print('copy error: ',ls_copy_error)
    with open(path_log,'w') as f:
            for val in ls_copy_error:
                    f.write(val+'\n')



client = _get_client(HOST, username, mot_de_pass)
ls_copy = get_ls2copy(client, path_dst, path_src)
cp2remote_rm_from_local(client, ls_copy, path_src, username, HOST, path_dst)
client.close()