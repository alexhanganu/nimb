"""
goals are to check the disk space
the function of this file is intended to run at the server
"""

import glob
import subprocess, re
from distribution.SSHHelper import *

class DiskspaceUtility:
    
    @staticmethod
    def get_free_space( path):
        """
        return the space in MB of NIMB_NEW_SUBJECTS, FS_SUBJECTS_DIR, folder, by running this command <df -hm ~> on local computer
        :param self:
        :param path: path to calculate the size
        :return: int, size in MG, this number is round(realsize) + 1
        """
        # todo: not clear how to do it, b/c the meaning of free space
        # todo: is this the free space of home folder or not?
        # note: use this
        # return int(subprocess.check_output(['du', '-shcm', path]).split()[0].decode('utf-8')) - 1
        home_folder = "~"
        command = f"df -hm {home_folder}" # h: human readable, m = megabyte
        out = subprocess.check_output(command, shell=True)

        if 'Available' not in out:
            return 0 # command failed
        out = int(out.decode('utf8')[1].split()[-3])
        return out

    @staticmethod
    def get_free_space_remote(ssh_session):
        """
        return the space in MB

        :param self:
        :output the output of diskusage_report running at remote server,
        output is got from this line (out, err) = runCommandOverSSH(ssh_session, f"ls  {PROCESSED_FS_DIR}/*.gz")
        :param sshconnection: the ssh connection to the remote server
        :return: int, size in MG, this number is round(realsize) + 1
        """
        (output, err) = runCommandOverSSH(ssh_session, "diskusage_report")
        print("It would talke long time to get diskusage_report ")
        # first_line = output.decode("utf8").split("\n")[1].strip()
        first_line = output.split("\n")[1].strip()
        results = re.sub("\s{4,}", "@@", first_line) #'/home (user hvt) 1173M/50G 20k/500k'
        results = results.split("@@")[1].lstrip().strip() # 1173M/50G
        usage_space = re.findall("\d+", results)[0] # 1173
        total_space = re.findall("\d+", results)[1] # 50
        free_space = int(total_space)*1024 - int(usage_space)
        return free_space


    @staticmethod
    def get_files_upto_size( size, path, extension="*.*" ):
        """
        get all files up to certain size
        :param self:
        :param size: total size can get, in MG
        :param path: path of the folder
        :param extension *.zip or *.gzip. default is *.*
        :return: list of files, which sum[ size of those file ] < total size
        """
        # extension = "*." + extension
        if size < 0:
            print("There is no file to be processed anymore")
            return []
        total_size = 0
        list_files = []
        os.chdir(path)
        for file in glob.glob(extension):
            # print(file)
            fp = os.path.join(path, file) # full path
            total_size += os.path.getsize(fp)
            size_in_MB = total_size/1024.0/1024.0

            if size_in_MB < size:
                list_files.append(fp)
            else:
                break
        return list_files



    @staticmethod
    def get_subject_upto_size(size, unprocessed_subject_list):
        """
        :param self:
        :param path
        :param size: total size can get, in MG
        :param unprocessed_subject_list list of unprocess subject
        :param path: path of the folder
        :param extension *.zip or *.gzip. default is *.*
        :return: list of files, which sum[ size of those file ] < total size
        """
        # extension = "*." + extension
        if size < 0:
            print("There is no file to be processed anymore")
            return []
        total_size = 0
        list_files = []
        for file in unprocessed_subject_list:
            total_size += os.path.getsize(file)
            size_in_MB = total_size / 1024.0 / 1024.0
            if size_in_MB < size:
                list_files.append(file)
            else:
                break
        return list_files

    @staticmethod
    def get_subject_to_be_process_with_free_space(unprocessed_subject_list ):
        """

        get_files_upto_freespace_in_home_folder
        :param unprocessed_subject_list:
        :return:
        """
        home = str(Path.home())
        size = DiskspaceUtility.get_free_space(home)
        return DiskspaceUtility.get_subject_upto_size(size,unprocessed_subject_list)

class ListSubjectHelper:

    @staticmethod
    def get_all_subjects(subject_path, extension=["*.zip","*.gz"]):
        """
        get all subject in SOURCE_SUBJECTS_DIR
        :param subject_path: must be absolute path
        :param extension:
        :return: all files with defined extensions, not full path, names only
        """
        os.chdir(subject_path)
        files = []
        for ext in extension:
            # files_1 = [os.path.join(subject_path, file) for file in glob.glob(ext)] full path
            files_1 = [file for file in glob.glob(ext)]
            files.extend(files_1)
        return files

    @staticmethod
    def get_all_subjects_at_remote(PROCESSED_FS_DIR,
                                   remote_host, remote_username, remote_password,
                                   extension=["*.zip", "*.gz"]):
        """
        get all subject in SOURCE_SUBJECTS_DIR
        :param subject_path: must be absolute path
        :param extension:
        :return: all files with defined extensions, such as ID.zip or ID.gz,
                and are not in full path
        """
        ssh_session = getSSHSession(remote_host, remote_username, remote_password)
        all_subjects = []
        for ext in extension:
            command = f" cd {PROCESSED_FS_DIR}; ls {ext}"
            (out, err) = runCommandOverSSH(ssh_session,command)
            if "No such file or directory" in err:
                continue
            all_subjects.append(out.split("\n")[1:-1])
        return all_subjects

    @staticmethod
    def get_to_be_processed_subject_local(SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR):
        """

        :param SOURCE_SUBJECTS_DIR: absolute path
        :param PROCESSED_FS_DIR: absolute path
        :return: [] or a list of to-be-processed object
        """
        all_subjects = ListSubjectHelper.get_all_subjects(SOURCE_SUBJECTS_DIR)

        processed_sbuject = ListSubjectHelper.get_all_subjects(PROCESSED_FS_DIR)
        # must get the file name only

        unprocessed_subject = set(all_subjects) - set(processed_sbuject)
        return list(unprocessed_subject)

if __name__ == "__main__":
    size = DiskspaceUtility.get_free_space("../v02003/utility")
    print(f"current size is {size} ")
    py = DiskspaceUtility.get_files_upto_size(1, "../v02003/utility", "*.*")
    print(f"list of python {py}")

