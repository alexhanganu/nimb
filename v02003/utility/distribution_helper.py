from .SSHHelper import *
from .check_disk_space import *

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
    def get_list_subject_to_be_processed(SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR):
        """
        1. get the list of un-processed subject
        2. get the current available space on hard-disk of user
        2. calculate the list of
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
        (out, err) = runCommandOverSSH(ssh_session, f"ls  {PROCESSED_FS_DIR}/*.gz")
        free_space = DiskspaceUtility.get_free_space_remote(out)
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
        # interface_cluster.copy_subjects_to_cluster(mri_path, subjects_folder, a_folder)
        pass

    @staticmethod
    def check_status_of_free_surfer():
        # todo: ask alex the exisitng function
        pass
