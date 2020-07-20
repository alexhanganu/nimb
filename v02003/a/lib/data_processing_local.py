#!/bin/python
#Alexandru Hanganu, 2018 April 05


from os import listdir, path, makedirs, rename, remove, symlink, readlink, system, lstat
try:
    from os import lchmod
except ImportError:
    pass
import shutil
from utility.SSHHelper import *
import pathlib
from a.lib import database

MainFolder = database._get_folder('Main')
DIRs_INCOMING = database._get_folder('MRI')

dirrawdata = MainFolder+'raw_t1/'

def chklog():
    print('testing check log')
    n2del=('.DS_Store','Thumbs.db','results.txt', 'notes.txt')
    lsmri = {}
    Processed_Subjects = {}
    for DIR in DIRs_INCOMING:
        ls = listdir(DIRs_INCOMING[DIR])
        for n in n2del:
            if n in ls:
                ls.remove(n)
        lsmri[DIR] = sorted(ls)
        Processed_Subjects[DIR] = database._get_list_processed_subjects(DIR)
    lsmiss = {}
    for DIR in lsmri:
        lsmiss[DIR] = [x for x in lsmri[DIR] if x not in Processed_Subjects[DIR]]
    return lsmiss


def predict_error(src, dst):   #code by Mithril
    if path.exists(dst):
        src_isdir = path.isdir(src)
        dst_isdir = path.isdir(dst)
        if src_isdir and dst_isdir:
            pass
        elif src_isdir and not dst_isdir:
            yield {dst:'src is dir but dst is file.'}
        elif not src_isdir and dst_isdir:
            yield {dst:'src is file but dst is dir.'}
        else:
            yield {dst:'already exists a file with same name in dst'}

    if path.isdir(src):
        for item in listdir(src):
            s = path.join(src, item)
            d = path.join(dst, item)
            for e in predict_error(s, d):
                yield e

def copytree(src, dst, symlinks=False, ignore=None, overwrite=False): #code by Mithril
    '''
    would overwrite if src and dst are both file
    but would not use folder overwrite file, or viceverse
    '''
    if not overwrite:
        errors = list(predict_error(src, dst))
        if errors:
            raise Exception('copy would overwrite some file, error detail:%s' % errors)

    if not path.exists(dst):
        makedirs(dst)
        shutil.copystat(src, dst)
    lst = listdir(src)
    if ignore:
        excl = ignore(src, lst)
        lst = [x for x in lst if x not in excl]
    for item in lst:
        s = path.join(src, item)
        d = path.join(dst, item)
        if symlinks and path.islink(s):
            if path.lexists(d):
                remove(d)
            symlink(readlink(s), d)
            try:
                st = lstat(s)
                mode = stat.S_IMODE(st.st_mode)
                lchmod(d, mode)
            except:
                pass  # lchmod not available
        elif path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            if not overwrite:
                if path.exists(d):
                    continue
            shutil.copy2(s, d)

def copy(src, dst):
    if path.isdir(dst):
        if len(listdir(src)) == len(listdir(dst)):
            print(time.strftime('%Y-%m-%d, %H:%M', time.localtime())+' '+dst+' folder already exists')
            with open(MainFolder+'logs/log_copylog.txt', 'a') as f:
                f.write('          folder already exists'+' '+dst+' '+time.strftime('%Y-%m-%d, %H:%M', time.localtime())+'\n')
            sum1 = sum(path.getsize(src+'/'+f) for f in listdir(src) if path.isfile(src+'/'+f))
            sum2 = sum(path.getsize(dst+'/'+f) for f in listdir(dst) if path.isfile(dst+'/'+f))
            if sum1 == sum2:
                f1 = listdir(src)
                f2 = listdir(dst)
                if f1[0] == f2[0]:
                    print('files similar, folders similar in size')
                    with open(MainFolder+'logs/log_copylog.txt', 'a') as f:
                        f.write('          folder already exists, files similar, '+' '+dst+' '+time.strftime('%Y-%m-%d, %H:%M', time.localtime())+'\n')
                else:
                    print('!!!!!!!!!!!!!!!FILES DIFFER')
                    with open(MainFolder+'logs/log_copylog.txt', 'a') as f:
                        f.write('          folder already exists, !!!!!!!!!!!!!!!FILES DIFFER'+' '+dst+' '+time.strftime('%Y-%m-%d, %H:%M', time.localtime())+'\n')

            else:
                print('DIFFERENT DATA', sum1, sum2)
                with open(MainFolder+'logs/log_copylog.txt', 'a') as f:
                    f.write('          folder already exists, DIFFERENT DATA'+' '+dst+' '+time.strftime('%Y-%m-%d, %H:%M', time.localtime())+'\n')

        else:
            print(time.strftime('%Y-%m-%d, %H:%M', time.localtime())+' ERRROR !!! file '+dst+' exists and differs from source')
            with open(MainFolder+'logs/log_copylog.txt', 'a') as f:
                f.write('          ERRROR !!! folder exists and differs from source'+dst+' '+time.strftime('%Y-%m-%d, %H:%M', time.localtime())+'\n')
            f1 = listdir(src)
            f2 = listdir(dst)
            if f1[0] == f2[0]:
                print('files similar')
                if len(listdir(src)) > len(listdir(dst)):
                    print('          ATTENTION!!! SOURCE folder has more files than DESTINATION folder and the first file names are similar, copying'+' '+src+' TO '+dst)
                    with open(MainFolder+'logs/log_copylog.txt', 'a') as f:
                        f.write('\n'+time.strftime('%Y-%m-%d, %H:%M', time.localtime())+'          ATTENTION!!! SOURCE folder has more files than DESTINATION folder and the first file names are similar, COPYING'+' '+src+' TO '+dst+'\n')
                    print('removing '+dst)
                    for file in listdir(dst):
                        remove(dst+'/'+file)
                    copytree(src,dst)
                else:
                    print('          ATTENTION!!! SOURCE folder has fewer files than DESTINATION folder, I will pass')
                    with open(MainFolder+'logs/log_copylog.txt', 'a') as f:
                        f.write('          ATTENTION!!! SOURCE folder has fewer files than DESTINATION folder, I will pass\n')
            else:
                print('!!!!!!!!!!!!!!!FILES DIFFER')
                dst_v2 = dst+'_v2'
                copytree(src,dst_v2)            
    else:
        print('copying'+' '+src+' TO '+dst)
        with open(MainFolder+'logs/log_copylog.txt', 'a') as f:
            f.write('\n'+time.strftime('%Y-%m-%d, %H:%M', time.localtime())+' COPYING'+' '+src+' TO '+dst+'\n')
        copytree(src,dst)


def define_SUBJID(DIR, id):
    name=('PDMCI','PD-MCI','PD_MCI', 'pdmci')
    SESSION_names = ['B','C']
    LONGITUDINAL_DEFINITION = ['T2','T3']

    if DIR == 'INCOMING':
                for n in name:
                    if any(n in i for i in id):
                        id=id[0]
                        pos_mci_in_id=[i for i, s in enumerate(id) if 'I' in s]
                        SUBJECT_NR=id[pos_mci_in_id[0]+1:]
                        SUBJECT_NR = SUBJECT_NR.replace('-','').replace('_','')
                        if SUBJECT_NR[0] =='0':
                            SUBJECT_NR = SUBJECT_NR[1:]
                session_ = ''
                for session in SESSION_names:
                    if session in SUBJECT_NR:
                        position = [i for i, s in enumerate(SUBJECT_NR) if session in s]
                        SUBJECT_NR = SUBJECT_NR.replace(SUBJECT_NR[position[0]], '')
                        session_ = session
                for LONG in LONGITUDINAL_DEFINITION:
                            if LONG in SUBJECT_NR:
                                longitudinal = True
                                longitudinal_name = LONG
                                break
                            else:
                                longitudinal = False
                if longitudinal:
                    SUBJECT_NR = SUBJECT_NR.replace(longitudinal_name, '')
                    SUBJECT_ID = 'pdmci'+SUBJECT_NR+longitudinal_name
                    FILE_name = SUBJECT_ID+session_
                else:
                    SUBJECT_ID = 'pdmci'+SUBJECT_NR
                    FILE_name = SUBJECT_ID+session_
    else:
                SUBJECT_ID = id[0].replace(' ','_')
                FILE_name = SUBJECT_ID

    database.update_ls_subj2fs(SUBJECT_ID)

    return(FILE_name)


def copy_T1_and_Flair_files(DIR, dir2read, lsdir, FILE_name):
    MR_T1 = ('IR-FSPGR','IRFSPGR','CCNA','MPRAGE','MPRage')
    MR_Flair = ('Flair','FLAIR')
    MR_PURE = ('PURE','PU')

    for T1 in MR_T1:
                if any(T1 in i for i in lsdir):
                    positionT1=[i for i, s in enumerate(lsdir) if T1 in s]
                    ls_pos_fT12cp = []
                    for posT1 in positionT1:
                        for PURE in MR_PURE:
                            if PURE in lsdir[posT1]:
                                if posT1 not in ls_pos_fT12cp:
                                    ls_pos_fT12cp.append(posT1)
                            elif T1 == 'MPRAGE' or T1 == 'MPRage':
                                if posT1 not in ls_pos_fT12cp:
                                    ls_pos_fT12cp.append(posT1)
                    if len(ls_pos_fT12cp) == 1:
                        if '.dcm' in listdir(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[ls_pos_fT12cp[0]])[0]:
                            src_T1=(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[ls_pos_fT12cp[0]])
                            dst_T1 = (dirrawdata+FILE_name+'_t1')
                            print(src_T1, dst_T1)
                            if path.isdir(src_T1):
                                copy(src_T1,dst_T1)
                                with open(MainFolder+'logs/f2cp','a') as f:
                                    f.write(FILE_name+'_t1'+'\n')
                            else:
                                print(src_T1+' is not a folder')
                        else:
                            ls_subDIRs = listdir(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[ls_pos_fT12cp[0]])
                            if len(ls_subDIRs) == 1:
                                    if '.dcm' in listdir(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[ls_pos_fT12cp[0]]+'/'+ls_subDIRs[0])[0]:
                                        src_T1=(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[ls_pos_fT12cp[0]]+'/'+ls_subDIRs[0])
                                        dst_T1 = (dirrawdata+FILE_name+'_t1')
                                        if path.isdir(src_T1):
                                            print(src_T1, dst_T1)
                                            copy(src_T1,dst_T1)
                                            with open(MainFolder+'logs/f2cp','a') as f:
                                                f.write(FILE_name+'_t1'+'\n')
                                        else:
                                            print(src_T1+' is not a folder')
                            else:
                                for subDIR in ls_subDIRs:
                                    if '.dcm' in listdir(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[ls_pos_fT12cp[0]]+'/'+subDIR)[0]:
                                        src_T1=(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[ls_pos_fT12cp[0]]+'/'+subDIR)
                                        dst_T1 = (dirrawdata+FILE_name+'_t1')
                                        if path.isdir(src_T1):
                                            print(src_T1, dst_T1)
                                            copy(src_T1,dst_T1)
                                            with open(MainFolder+'logs/f2cp','a') as f:
                                                f.write(FILE_name+'_t1'+'\n')
                                        else:
                                            print(src_T1+' is not a folder')
                    else:
                        n = 1
                        for pos_f2cp in ls_pos_fT12cp:
                            src_T1=(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[pos_f2cp])
                            if len(listdir(src_T1)) > 170:
                                v = '_v'+str(n)
                                dst_T1 = (dirrawdata+FILE_name+'_t1'+v)
                                print(src_T1, dst_T1)
                                if path.isdir(src_T1):
                                    copy(src_T1,dst_T1)
                                    with open(MainFolder+'logs/f2cp','a') as f:
                                        f.write(FILE_name+'_t1'+v+'\n')
                                else:
                                    print(src_T1+' is not a folder')
                                n += 1

    for Flair in MR_Flair:
                if any(Flair in i for i in lsdir):
                    position_Flair=[i for i, s in enumerate(lsdir) if Flair in s]
                    ls_pos_fFlair2cp = []
                    for posFlair in position_Flair:
                        for PURE in MR_PURE:
                            if PURE in lsdir[posFlair]:
                                if 'FLB' not in lsdir[posFlair]:
                                    if posFlair not in ls_pos_fFlair2cp:
                                        ls_pos_fFlair2cp.append(posFlair)
                        if len(ls_pos_fFlair2cp) == 0:
                            if MR_PURE[0] and MR_PURE[1] not in lsdir[posFlair]:
                                if len(position_Flair) == 1:
                                    ls_pos_fFlair2cp.append(posFlair)
                    if len(ls_pos_fFlair2cp) == 1:
                        src_Flair=(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[ls_pos_fFlair2cp[0]])
                        dst_Flair = (dirrawdata+FILE_name+'_flair')
                        print(src_Flair, dst_Flair)
                        if path.isdir(src_Flair):
                            copy(src_Flair,dst_Flair)
                            with open(MainFolder+'logs/f2cp','a') as f:
                                f.write(FILE_name+'_flair'+'\n')
                        else:
                            print(src_Flair+' is not a folder')
                    else:
                        n = 1
                        for pos_f2cp in ls_pos_fFlair2cp:
                            v = '_v'+str(n)
                            src_Flair=(DIRs_INCOMING[DIR]+dir2read+'/'+lsdir[pos_f2cp])
                            dst_Flair = (dirrawdata+FILE_name+'_flair'+v)
                            print(src_Flair, dst_Flair)
                            if path.isdir(src_Flair):
                                copy(src_Flair,dst_Flair)
                                with open(MainFolder+'logs/f2cp','a') as f:
                                    f.write(FILE_name+'_flair'+v+'\n')
                            else:
                                print(src_Flair+' is not a folder')
                            n+= 1
    print('FINISHED copying T1 and Flair for all subjects')


def copy_T1_file(DIR, dir2read, FILE_name):
    src_T1=(DIRs_INCOMING[DIR]+dir2read)
    if len(listdir(src_T1)) > 170:
                                dst_T1 = (dirrawdata+FILE_name+'_t1')
                                print(src_T1, dst_T1)
                                if path.isdir(src_T1):
                                    copy(src_T1,dst_T1)
                                    with open(MainFolder+'logs/f2cp','a') as f:
                                        f.write(FILE_name+'_t1'+'\n')
                                else:
                                    print(src_T1+' is not a folder')


def cpt1flair():
    '''
    will copy the t1 and flair files from the Incoming folder to the
    MainFolder raw_t1 folder based on the logmiss.xlsx file
    '''

    lsmiss = database._get_lsmiss()

    for DIR in lsmiss:
        for dir2read in lsmiss[DIR]:
            if path.isdir(DIRs_INCOMING[DIR]+dir2read):
                if len(listdir(DIRs_INCOMING[DIR]+dir2read))>0:
                    id=[dir2read]
                    FILE_name = define_SUBJID(DIR, id)
                    if '.dcm' in listdir(DIRs_INCOMING[DIR]+dir2read)[0]:
                        print('1 lvl: file name is: '+str(FILE_name))
                        copy_T1_file(DIR, dir2read, FILE_name)
                    elif len(listdir(DIRs_INCOMING[DIR]+dir2read)) ==1 and '.dcm' in listdir(DIRs_INCOMING[DIR]+dir2read+'/'+listdir(DIRs_INCOMING[DIR]+dir2read)[0])[0]:
                        print('1a lvl: file name is: '+str(FILE_name))
                        dir2cp = dir2read+'/'+listdir(DIRs_INCOMING[DIR]+dir2read)[0]
                        copy_T1_file(DIR, dir2cp, FILE_name)                  
                    else:
                        print('2 lvl: file name is: '+str(FILE_name))
                        lsdir = listdir(DIRs_INCOMING[DIR]+dir2read)
                        copy_T1_and_Flair_files(DIR, dir2read, lsdir, FILE_name)
                    database._update_list_processed_subjects(DIR, dir2read)
                else:
                    print(dir2read+' is empty')
            else:
                print(dir2read+' is not a folder; skipping')
            database._update_lsmiss(DIR, dir2read)

def cp2cluster():
    '''
    will copy the t1 and flair folders from the raw_t1 to the cluster
    in the "subjects" folder. Removes the logmiss.xlsx, subj2fs, f2cp files
    '''
    from sys import platform
    from a.lib.interface_cluster import start_cluster


    def platform_linux_darwin(cuser, caddress, subj2cp, dirs2cp, cmaindir):
            ls_complete_name = []
            system('sftp '+cuser+'@'+caddress)
            time.sleep(10)
            for dir2cp in dirs2cp:
                    system('mkdir subjects/'+dir2cp)
                    for file in listdir(MainFolder+'/'+dir2cp):
                        system('put '+MainFolder+'/'+dir2cp+'/'+file+' '+'subjects/'+dir2cp)
                    dir = dirrawdata+dir2cp
                    ls_complete_name.append(dir)
            onename_dirs2cp = ' '.join(ls_complete_name)
            system('scp -r '+onename_dirs2cp+' '+cuser+'@'+caddress+':'+cmaindir+'subjects/')
            system('put '++subj2cp+' '+cmaindir+'a/')
            system('exit')


    def platform_win(cuser, caddress, subj2cp, dirs2cp, cmaindir, cpw):
            print(MainFolder)
            open(MainFolder+'logs/psftpcp2cluster.scr','w').close()
            with open(MainFolder+'logs/psftpcp2cluster.scr','a') as scr:
                scr.write('put -r '+subj2cp+' '+cmaindir+'a/subj2fs\n')
            with open(MainFolder+'logs/psftpcp2cluster.scr','a') as scr:
                for dir2cp in dirs2cp:
                    scr.write('put -r '+dirrawdata+dir2cp+' '+cmaindir+'subjects/'+dir2cp+'\n')
            time.sleep(1)
            system('psftp '+cuser+'@'+caddress+' -pw '+cpw+' -b '+MainFolder+'logs/psftpcp2cluster.scr')
            #remove(MainFolder+'logs/psftpcp2cluster.scr')

    #print((MainFolder+'logs/subj2fs');
    MainFolder = "Z:/iugm_hoangvantien/nimb_01908/project1/"
    if path.isfile("Z:/iugm_hoangvantien/nimb_01908/project1/logs/subj2fs"):
        lssubj = [line.rstrip('\n') for line in open(MainFolder+'logs/subj2fs')]
        if len(lssubj)>1:
            print(str(len(lssubj))+' subjects need to be processed')
        dirs2cp = [line.rstrip('\n') for line in open(MainFolder+'logs/f2cp')]
        clusters = database._get_credentials('all')
        if len(clusters) == 1:
            for cred in clusters:
                cname = cred
                cuser = clusters[cred][0]
                caddress = clusters[cred][1]
                cmaindir = clusters[cred][2]
                cpw = clusters[cred][4]
                if platform == 'darwin' or platform == 'linux' or platform == 'linux2':
                    platform_linux_darwin(cuser, caddress, 'subj2fs', dirs2cp, cmaindir)
                elif platform == 'win32':
                    platform_win(cuser, caddress, 'subj2fs', dirs2cp, cmaindir, cpw)
            start_cluster()
        elif len(clusters) > 1:
            nr_clusters = len(clusters)
            nr_of_subjects_2_cp = int(len(lssubj)/nr_clusters)
            f_nr = 0
            val2start_count = 0
            val2end_count = nr_of_subjects_2_cp
            for cred in clusters:
                cuser = clusters[cred][0]
                caddress = clusters[cred][1]
                cmaindir = clusters[cred][2]
                tmp_dirs2cp = []
                with open(MainFolder+'logs/f2cp','a') as f:
                    with open(MainFolder+'logs/subj2fs'+str(f_nr),'a') as f2:
                            for subj in lssubj[val2start_count:val2end_count]:
                                f2.write(subj+'\n')
                                for dir in dirs2cp:
                                    if subj in dir:
                                        tmp_dirs2cp.append(dir)
                if platform == 'darwin' or platform == 'linux' or platform == 'linux2':
                    platform_linux_darwin(cuser, caddress, MainFolder+'subj2fs'+str(f_nr), tmp_dirs2cp, cmaindir)
                elif platform == 'win32':
                    platform_win(cuser, caddress, MainFolder+'subj2fs'+str(f_nr), tmp_dirs2cp, cmaindir)
                rename(MainFolder+'subj2fs'+str(f_nr), MainFolder+'logs/zold.subj2fs'+str(f_nr)+'_'+str(time.strftime('%Y%m%d', time.localtime())))
                val2start_count = val2start_count +nr_of_subjects_2_cp
                val2end_count = val2end_count + nr_of_subjects_2_cp
                if val2end_count < len(lssubj):
                    pass
                else:
                     val2end_count = len(lssubj)
                f_nr += 1
            start_cluster()

        #rename(MainFolder+'logs/subj2fs', MainFolder+'logs/zold.subj2fs'+str(time.strftime('%Y%m%d', time.localtime())))
        #rename(MainFolder+'logs/f2cp', MainFolder+'logs/zold.f2cp'+str(time.strftime('%Y%m%d', time.localtime())))

    else:
        print('no subj2fs file, no subjects to copy to cluster')

#
def cpFromCluster():
    """
    it copy the files from the cluster to the local folder, get files from Processed_SUBJECTS_DIR
    the remote location : source dir: is in the configuration, how?
    the local location : dest dir: is in the configuration also

    :return: None, nothing
    """
    # todo: for now, only working on windows
    # def platform_linux_darwin(cuser, caddress, cmaindir):
    #         ls_complete_name = []
    #         system('sftp '+cuser+'@'+caddress)
    #         time.sleep(10)
    #         for dir2cp in listdir():
    #             system('get '+cmaindir+'/freesurfer/subjects/'+dir2cp+' '+MainFolder+'/processed/')
    #         system('exit')
    #     # system('scp '+cuser+'@'+caddress+':'+cmaindir+'status_cluster '+freesurfer+'logs/')

    def platform_win(cuser, caddress, cmaindir,cpw):
        print(MainFolder) # not use now use to be local folder store the results
        file = MainFolder+'logs/psftpcpdb_from_cluster.scr' # do not use, can remove
        open(file, 'w').close()
        with open(file,'a') as f:
            f.write('get '+cmaindir+'a/db.py a/db.py\n') # this is the batch command: get a/db.py a/db.py
            f.write('quit')
        count = 0
        system('psftp '+cuser+'@'+caddress+' -pw '+cpw+' -b '+file)
        while count <4 and not path.exists('a/db.py'):
            time.sleep(2)
            count += 1
        #remove(file)
        if path.exists('a/db.py'):
            from a.db import PROCESSED # so cmaindir folder is the current folder :)
            if len(PROCESSED['cp2local']) > 0:
                file2cp = MainFolder+'logs/cp_processed_from_cluster.scr'
                open(file2cp, 'w').close()
                with open(file2cp,'a') as f:
                    for subjid in PROCESSED['cp2local']:
                        f.write('get '+cmaindir+'freesurfer/subjects/'+subjid+' '+MainFolder+'processed/\n')
                system('psftp '+cuser+'@'+caddress+' -pw '+cpw+' -b '+file2cp)
                #remove(file2cp)

    clusters = database._get_credentials('all')
    ssh_session = getSSHSession(host_name, user_name, user_password)
    scp = SCPClient(ssh_session.get_transport())
    ftp_client = ssh_session.open_sftp()

    if len(clusters) == 1:
        for cred in clusters:
            cuser = clusters[cred]['Username']
            caddress = clusters[cred]['remote_address']
            cmaindir = clusters[cred]['HOME']
            cpw =  clusters[cred]['Password']
            from sys import platform
            # platform_linux_darwin(cuser, caddress, cmaindir)
            # platform_win(cuser, caddress, cmaindir,cpw)
            # 1. download a/a.db to a/a.db
            remote_path = os.path.join(cmaindir,'a/db.py')
            # remote path is ????/projects/def-hanganua/a/db.py: subject folder
            current_path = pathlib.Path(__file__).parents[1] # it is v02003/a

            print(current_path)
            local_path = os.path.join(current_path,'db.py') #MainFolder+'processed/'
            print((remote_path,local_path))
            # local path is processed in this folder
            ftp_client.get(remote_path,local_path)
            print("downloaded {0} to {1}".format(remote_path, local_path))
            # 2. after download a.db
            if not path.exists('a/db.py'):
                print("a/db.py file does not exist")
                return
            # here db.py exist
            # todo: get user to input path to subject folder
            # set the cmaindir values: it is the location that contains the subjects
            result, _ = runCommandOverSSH(ssh_session, "echo $FREESURFER_HOME")
            if result:
                path_to_subjects = result
            else:
                print("Please set the FREESURFER_HOME in cluster environment to free surfer home."
                      " Try to search for subjects folder in ~/subjects ")
                result, _ = runCommandOverSSH(ssh_session, "file ~/subjects")
                if 'No such file or directory' in result:
                    print("The set the location of subjects: either is ~/subjects or FREESURFER_HOME/subjects before "
                          "downloading results")
                    return
            # path_to_subjects = '/home/hvt/projects/def-hanganua/' # for debug purpose
            MainFolder = "./" # current folder of the scripts
            from a.db import PROCESSED
            if len(PROCESSED['cp2local']) > 0:
                # file2cp = MainFolder+'logs/cp_processed_from_cluster.scr'
                # open(file2cp, 'w').close()
                ftp_client = ssh_session.open_sftp()
                for subjid in PROCESSED['cp2local']:
                    remote_path = os.path.join(path_to_subjects,'subjects/',subjid)
                    local_path = os.path.join(MainFolder,'processed/', subjid)
                    print("___", remote_path, local_path)
                    ftp_client.get(remote_path,local_path)
                    print("downloaded {0} to {1}".format(remote_path, local_path))
            # scp.close()
            ssh_session.close()