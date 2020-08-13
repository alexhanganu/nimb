from distribution.check_disk_space import *

class DistributionHelper():
    """
    document here
    """
    @staticmethod
    def is_all_subject_processed(SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR):
        """
        must be absolute path
        :param SOURCE_SUBJECTS_DIR:
        :param PROCESSED_FS_DIR:
        :return:
        """
        un_process_sj = ListSubjectHelper.get_to_be_processed_subject_local(SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR)
        if len(un_process_sj) > 0:
            return True
        return False

    @staticmethod
    def get_list_subject_to_be_processed_local(SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR):
        """
        1. get the list of un-processed subject
        2. get the current available space on hard-disk of user
        2. calculate the list of
		initial script in database -> create_lsmiss
        :param SOURCE_SUBJECTS_DIR:
        :return:
        """
        # get the list of unprocessed subjects
        un_process_sj = ListSubjectHelper.get_to_be_processed_subject_local(SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR)
        # based on availabe space
        to_be_process_subject = DiskspaceUtility.get_subject_to_be_process_with_free_space(un_process_sj)
        #
    @staticmethod
    def helper(ls_output):
        return ls_output.split("\n")[1:-1]
    @staticmethod
    def get_list_subject_to_be_processed_remote(SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR,
                                                remote_host, remote_username, remote_password):
        """
        1. connect to the remote host
        2. get local process subjects
        3. get remote processed subjects
        4. get un-processs subjects from local
        5. get available space on remote computer
        6. get to-be-process subjects
        7. (other functions) send those subjects to the remote server
        :param SOURCE_SUBJECTS_DIR: MUST BE FULL PATHS
        :param PROCESSED_FS_DIR:
        :return:
        """
        ssh_session = getSSHSession(remote_host, remote_username, remote_password)
        (zip_out, err) = runCommandOverSSH(ssh_session, f" cd {PROCESSED_FS_DIR}; ls *.zip") #
        (gz_out, err) = runCommandOverSSH(ssh_session, f"cd {PROCESSED_FS_DIR}; ls *.gz")
        # at remote
        all_processed_file_remote = DistributionHelper.helper(gz_out) + DistributionHelper.helper(zip_out) # only file name, no path
        # at local
        all_subjects_at_local = ListSubjectHelper.get_all_subjects(SOURCE_SUBJECTS_DIR) # full path
        all_subjects_at_local_short_name = [short_name.split("/")[-1] for short_name in all_subjects_at_local ]
        # get free space remotely
        free_space = DiskspaceUtility.get_free_space_remote(ssh_session)
        to_be_process_subject = set(all_subjects_at_local_short_name) - set(all_processed_file_remote) # not consider space yet
        # consider the space available the remote server
        to_be_process_subject = DiskspaceUtility.get_subject_upto_size(free_space, to_be_process_subject)

        print("Remote server has {0}MB free, it can stored {1} subjects".format(free_space, len(to_be_process_subject)))
        ssh_session.close()
        return [os.path.join(SOURCE_SUBJECTS_DIR,subject) for subject in to_be_process_subject] # full path
        #return to_be_process_subject



    @staticmethod
    def upload_un_process_subject_to_remote():
        # call the ssh helper to upload the file
        # to NIMB_NEW_SUBJECTS
        # interface_cluster.copy_subjects_to_cluster(mri_path, subjects_folder, a_folder)
        pass

    @staticmethod
    def check_status_of_free_surfer():
        # not important now. todo: ask alex the exisitng function
        pass

    @staticmethod
    def move_processed_to_storage():
        '''
        this script is a copy paste, it must be adapted. Storage folder (i.e., for ADNI is beluga../projects/../adni)
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

        path_credentials = path.join('/home',username) # path to the txt-like file named "credentials" that will contain the follow$
        path_log = path.join(path.join('/home',username,'projects','def-hanganua'), 'scripts', 'scp_log.txt') # path where a log file will be stored tha$
        path_src = path.join(path.join('/home',username,'projects','def-hanganua'), 'subjects_processed') # path that contains the files or folders t$
        path_dst_dir = path.join(path.join('/home',username,'projects','def-hanganua'), 'adni', 'processed_fs') # on beluga

        path_scratch = path.join('/scratch',username)
        path_processed = path.join(path_projects,'subjects_processed')


        shutil.copy(path.join(path_credentials,'credentials'), path.dirname(path.abspath(__file__))+'/credentials.py')
        try:
                from credentials import mot_de_pass
                remove(path.dirname(path.abspath(__file__))+'/credentials.py')
        except ImportError:
                print('file with credentials was not found')
                raise SystemExit()

        def _get_client(HOST, username, mot_de_pass):
            # setting up the remote connection
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

