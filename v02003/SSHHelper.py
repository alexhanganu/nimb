"""
This module is to execute the remote commands in cluster
notes: code is modified from hw5
# todo: make this script becomes a class in Singleton design pattern for the SSH session
"""
import json
import logging
import tempfile
import time
import os
from sys import platform
try:
    import paramiko
    from scp import SCPClient, SCPException
except ImportError:
    print('Please install paramiko and scp using: pip install scp paramiko')

import json
from pathlib import Path

from a.lib import database
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(module)s %(levelname)s: %(message)s')
# logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)
#configuration
cname='all'
clusters = database._get_Table_Data('Clusters','all')
if 'elm' in clusters:
    cname = 'elm'
else:
    cname = 'defaultClusters'


user_name = clusters[cname]['Username']
user_password = clusters[cname]['Password']
project_folder = clusters[cname]['HOME'] #'/home/hvt/projects/def-hanganua'
cmd_run = " python a/crun.py -submit true" #submit=true
load_python_3 = 'module load python/3.7.4;'
cmd_run_crun_on_cluster = load_python_3 +"cd " + project_folder + "; " + cmd_run
host_name = clusters[cname]['remote_address'] #"beluga.calculquebec.ca"
# note: if the paramiko has errors when connecting to beluga, change it to beluga1 or 2,3,4
a_folder = clusters[cname]['App_DIR']#'/home/hvt/projects/def-hanganua/a'

subjects_folder = clusters[cname]['Subjects_raw_DIR']#'/home/hvt/test'


ANAT = 'anat'
BASELINE = 'baseline'
T1 = 't1'
FLAIR = 'flair'
T2 = 't2'
SES_1 = "ses-1"

# when there is failed uploading to server, file names and path in both cluster and local machine
# are written to this file
# each time the script running, it will check if this file exists. If this file exists, it will be
# rename by adding the time add the end. Otherwise, it is created when there is failed uploading
FAILED_UPLOAD_FILE = "fail_upload_.log"



def getSSHSession(targetIP, username, password):
    """
    :param targetIP: the ip address of cluster server or the name of the server
    :param username: username of ssh user
    :param password: password to login
    :return: a paramiko sshsession object
    """
    # Set up SSH
    logger.debug((username, password,targetIP))
    sshSession = paramiko.SSHClient()
    sshSession.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    while True:
        try:
            sshSession.connect(targetIP, username = username, password = password)
            logger.debug("SSH to %s successful" % targetIP)
            break
        except Exception as e:
            logger.debug(e)
            logger.debug("Waiting for SSH daemon to come up in %s..." % targetIP)
            time.sleep(5)

    return sshSession


def runCommandOverSSH(sshSession, command):
    """
    :param sshSession: paramiko sshsession
    :param command: the command to run
    :return: tuple(output of command, error) or None if error
    """
    assert type(sshSession) is paramiko.client.SSHClient, \
        "'sshSession' is type %s" % type(sshSession)
    # assert type(command) in (str, unicode), "'command' is type %s" % type(command)
    logger.debug("Running command in host %s" % sshSession._transport.sock.getpeername()[0])
    logger.debug("\t\"%s\"" % command)

    try:
        stdin, stdout, stderr = sshSession.exec_command(command)

        # Wait for command to finish (may take a while for long commands)
        while not stdout.channel.exit_status_ready() or \
                not stderr.channel.exit_status_ready():
            time.sleep(1)
    except Exception as e:
        logger.error(e)
        logger.error("ERROR: Unable to execute command over SSH:")
        logger.error("\t%s" % command)

        return None
    else:
        # Check if command printed anything to stderr
        err = stderr.readlines()
        err = ''.join(err) # Convert to single string
        if err:
            logger.error("%s\n" % err)

        out = stdout.readlines()
        out = ''.join(out) # Convert to single string
        if out:
            logger.debug("%s\n" % out)

        return (out, err)


def running_command_ssh():
    ssh_session = getSSHSession(host_name, user_name, user_password)

    (out, err) = runCommandOverSSH(ssh_session, cmd_run_crun_on_cluster)
    print(out, err)

def running_command_ssh_2(host_name, user_name, user_password, cmd_run_crun_on_cluster):
    ssh_session = getSSHSession(host_name, user_name, user_password)

    (out, err) = runCommandOverSSH(ssh_session, cmd_run_crun_on_cluster)
    print(out, err)

def read_json(json_file_name):
    """
    read the json file, return the dictionary the content
    return type:dict if sucess, otherwise None
    """
    with open(json_file_name, 'r') as p:
        return json.load(p)


def make_folder_at_cluster(sftp, remote_path):
    """
    create a folder at cluster if not exist
    @param sftp: sftp object from paramiko
    @param remote_path: the remote path to be create
    @return:
    """
    logger.debug("Remote path is %s", remote_path)
    try:
        # TODO: using pathlib for this function
        sftp.chdir(remote_path)
        logger.debug("The folder is alread existed %s", remote_path)
    # except IOError:
    except FileNotFoundError:
        logger.debug("Creating folder %s    ",remote_path)
        sftp.mkdir(remote_path)

def make_destination_folders(ssh_session, dest_folder,subject_id_folder_name):
    """
    make all the folder in the list_subfolder inside the subjects_folder
    @param subject_id: the subject id
    @param ssh_session: ssh session, paramiko ojbect
    @param dest_folder: destination folder in the cluster
    @param list_subfolder:
    Do not return anything
    """
    logger.info('Making folder for %s', subject_id_folder_name)
    sftp = paramiko.SFTPClient.from_transport(ssh_session.get_transport())
    new_folder = dest_folder +"/" + subject_id_folder_name
    make_folder_at_cluster(sftp, new_folder)
    return True

"""
def get_all_files(path):
    '''
    get all files in the path, must be absolute path
    :param t1_path:
    :return: a list of all files or an empty list
    '''
        files = Path(path).glob("*.*")
    list_files = [file_path.as_posix() for file_path in files ]
    print(type(list_files), list_files)
    return list_files
"""

def get_all_files(path,extension_list):
    print("kp_begin")
    '''
    get all files in the path, must be absolute path
    :param t1_path:
    :return: a list of all files or an empty list
    '''
    if len(extension_list) > 0:
        list_files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(extension_list)]
    else:
        list_files = [os.path.join(path, f) for f in os.listdir(path)]
    return list_files

def __progress(filename, size, sent):
    """Display SCP progess."""
    logger.debug("%s\'s progress: %.2f%%   \r" % (filename, float(sent) / float(size) * 100))

def upload_single_file_to_cluster(scp, dest_folder, file_, failed_upload_files = FAILED_UPLOAD_FILE):
    '''
    copy files to the cluster server
    :param ssh_session: paramiko object
    :param dest_folder: destination folder
    :param file_: file to be copied
    :return: None
    '''
    logger.info("Uploading file to server %s to %s", file_, dest_folder)
    try:
        scp.put(file_,
                recursive=True,
                remote_path=dest_folder)

        logger.debug("Finish uploading files")
    except SCPException:
        logger.debug("Error uploading files to cluster %s", SCPException.message)
        # TODO: create new file or reuse the existing file?
        with open(failed_upload_files, "a+") as f:
            f.write(file_ + "@@" + dest_folder + '\n')
        raise SCPException.message

def retry_upload_files(ssh_session, file_name = FAILED_UPLOAD_FILE):
    '''
    if files are not uploaded sucessfull, they will be reupload here.
    The list of failed uploaded files are in FAILED_UPLOAD_FILE
    :param scp: scp object from paramiko transport
    :param file_name: the file contains the list of all failed uploading files
    :return:
    '''
    # if that file does not exist. Nice! get out immediately
    if not Path(FAILED_UPLOAD_FILE).is_file():
        return
    scp = SCPClient(ssh_session.get_transport(), progress=__progress)
    all_files = open(file_name)
    # remove the \n line
    all_files = [line for line in all_files if len(line) > 1]
    logger.info("RE-Uploading file to server %s ", str(all_files))
    for line in all_files:
        src_dest_pair = line.split('@@')
        dest_folder = src_dest_pair[-1].strip()
        source_file = src_dest_pair[0].strip()
        try:
            scp.put(source_file, remote_path=dest_folder)
            logger.debug('uploading %s to %s', source_file, dest_folder)
        except SCPException as e:
            logger.debug('Cannot upload %s to %s', source_file, dest_folder)
            logger.debug(str(e))
    scp.close()


def upload_multiple_files_to_cluster(ssh_session, dest_folder, file_list):
    '''
    upload all files to cluster, one by one
    This is to keep track of which file is failed to upload
    :param ssh_session:
    :param dest_folder:
    :param file_list:
    :return:
    '''
    logger.debug("Uploading files to server ")
    scp = SCPClient(ssh_session.get_transport(), progress = __progress)
    for file_ in file_list:
        upload_single_file_to_cluster(scp, dest_folder, file_, failed_upload_files=FAILED_UPLOAD_FILE)
    scp.close()

def upload_files_to_cluster(ssh_session, dest_folder, file_):
    '''
    upload multiple files to cluster, cannot keep track which file is fail upload.
    :param ssh_session: paramiko object
    :param dest_folder: destination folder
    :param file_: file to be copied
    :return:
    '''
    logger.info("Uploading files to server ")
    scp = SCPClient(ssh_session.get_transport(),progress = __progress)
    try:
        scp.put(file_,
                recursive=True,
                remote_path=dest_folder)
        logger.debug("Finish uploading files")
    except SCPException:
        logger.debug("Error uploading files to cluster %s", SCPException.message)
        raise SCPException.message
    finally:
        scp.close()


def rename_existed_failed_upload_files_list(file_name = FAILED_UPLOAD_FILE):
    if not Path(file_name).exists():
        return
    import datetime
    current_time = str(datetime.datetime.now()).replace(":","-")
    Path(file_name).rename(current_time +" " +FAILED_UPLOAD_FILE)

#kp
def get_files_inside_subject_id(subject_dicts, subject_id):
    t1_path = []
    t2_path = []
    flair_path = []

    key_inside_ANAT = list(subject_dicts[subject_id][SES_1][ANAT].keys())

    if T1 in key_inside_ANAT:
        t1_path = subject_dicts[subject_id][SES_1][ANAT][T1]
        logger.debug("kp_t1_path:", t1_path)
        #t1_path = t1_path[0] #because this is a list
    if T2 in key_inside_ANAT:
        t2_path = subject_dicts[subject_id][SES_1][ANAT][T2]
    if FLAIR in key_inside_ANAT:
        flair_path = subject_dicts[subject_id][SES_1][ANAT][FLAIR]
    logger.debug("paths are: %s %s %s ",t1_path, t2_path, flair_path)

    return t1_path, t2_path, flair_path

def upload_all_subjects(subjects_json_file, subjects_folder, a_folder):
    '''
    upload all subject in the json file to remote cluster
    Kp_ and copy the json file updated to the "a" folder
    path in subjects_json_file will be updated for cluster path and uploaded to a_folder
    :param subjects_json_file: the json files of subject id
    :param subjects_folder: the destination on remote folder
    :return: None
    '''

    subject_dicts = read_json(subjects_json_file)
    subject_dicts_a = {} # this is for copying the json file to the "a" folder
    subject_dicts_a.update(subject_dicts)
    extension_file_list = ('.dcm','.nii.gz')

    for subject_id in subject_dicts.keys():
        t1_path, t2_path, flair_path = \
            get_files_inside_subject_id(subject_dicts, subject_id)
        ssh_session = getSSHSession(host_name, user_name, user_password)

        rename_existed_failed_upload_files_list(file_name=FAILED_UPLOAD_FILE)

        ####################################
        # read all folder of T1, T2, flair #
        # and copy all files of all folder #
        # to the new  T1, T2, flair folder #
        ####################################
        if len(t1_path) > 0:
            # make the new folder in the cluster as template pls_hc000_ses-1_t1
            subject_id_folder_name = subject_id + "_" + SES_1 + "_" + T1
            make_destination_folders(ssh_session, subjects_folder, subject_id_folder_name)
            subject_id_folder = subjects_folder + "/" + subject_id_folder_name
            # update the path of the json on the cluster
            subject_dicts_a[subject_id][SES_1][ANAT][T1] = subject_id_folder

            # Note: Not considering the confliction of file_name in different folders of 1 MRI_type
            for i in range(len(t1_path)):
                all_t1_files = get_all_files(t1_path[i],extension_file_list)
                upload_multiple_files_to_cluster(ssh_session, subject_id_folder, all_t1_files)

        if len(t2_path) > 0:
            subject_id_folder_name = subject_id + "_" + SES_1 + "_" + T2
            make_destination_folders(ssh_session, subjects_folder, subject_id_folder_name)
            subject_id_folder = subjects_folder + "/" + subject_id_folder_name
            # update the path of the json on the cluster
            subject_dicts_a[subject_id][SES_1][ANAT][T2] = subject_id_folder

            for i in range(len(t2_path)):
                all_t2_files = get_all_files(t2_path[i],extension_file_list)
                upload_multiple_files_to_cluster(ssh_session, subject_id_folder, all_t2_files)

        if len(flair_path) > 0:
            subject_id_folder_name = subject_id + "_" + SES_1 + "_" + FLAIR
            make_destination_folders(ssh_session, subjects_folder, subject_id_folder_name)
            subject_id_folder = subjects_folder + "/" + subject_id_folder_name
            # update the path of the json on the cluster
            subject_dicts_a[subject_id][SES_1][ANAT][FLAIR] = subject_id_folder

            for i in range(len(flair_path)):
                all_flair_files = get_all_files(flair_path[i],extension_file_list)
                upload_multiple_files_to_cluster(ssh_session, subject_id_folder, all_flair_files)

        # retry upload the file
        retry_upload_files(ssh_session, file_name=FAILED_UPLOAD_FILE)
        logger.info("Finish uploading all files!")

    # create tempo folder for storing new subjects_json_file
    # json_file_name_only =
    if platform == "linux" or platform == "darwin":
        json_file_name_only = Path(subjects_json_file).name
    if platform == "win32" or platform == "win64":
        from pathlib import PureWindowsPath
        json_file_name_only = PureWindowsPath(subjects_json_file).name
    new_file = os.path.join(tempfile.gettempdir(), json_file_name_only)
    # upload the new json file (path file) to the "a" folder in the remote cluster
    with open(new_file, 'w') as outfile:
        json.dump(subject_dicts_a, outfile)
    # do the final job!
    upload_subject_json_to_server(new_file, a_folder, ssh_session)


def upload_subject_json_to_server(new_subjects_json_file, dest_folder, ssh_session):
    scp = SCPClient(ssh_session.get_transport(), progress=__progress)
    upload_single_file_to_cluster(scp, dest_folder, new_subjects_json_file, failed_upload_files=FAILED_UPLOAD_FILE)
    scp.close()




def download_files_from_server(local_folder, remote_folder):
    """
    download files from server
    :param local_folder:
    :type local_folder:
    :param remote_folder:
    :type remote_folder:
    """
    ssh_session = getSSHSession(host_name, user_name, user_password)
    scp = SCPClient(ssh_session.get_transport(), progress=__progress)
    #     ftp_client=ssh_client.open_sftp()
    # ftp_client.get(‘remotefileth’,’localfilepath’)
    # ftp_client.close()
    ftp_client = ssh_session.open_sftp()
    ftp_client.get('/home/hvt/projects/def-hanganua/a','/Users/van/Downloads/git/nimb/v02003/tmp/make_subj2fs.py')



# kp for testing
def test():
    """tes the function"""
    from a.lib import database
    clusters = database._get_credentials('all')
    ssh_session = getSSHSession(host_name, user_name, user_password)
    print("ls; cd " + project_folder + "; ls")
    (out, err) = runCommandOverSSH(ssh_session, "ls; cd " + project_folder + "; ls" )
    print(out, err)
    print("finish")

if __name__ == "__main__":
    if True:
        test()
    if False:
        json_path = 'new_subjects.json'
        upload_all_subjects(subjects_json_file = json_path, subjects_folder="/home/hvt/test",
                        a_folder ='/home/hvt/projects/def-hanganua/a')