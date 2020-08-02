# 2020 Jan 10
# modules to install: pandas, scipy, glob, shutil, openpyxl, xlrd(data_processing_local.chklog)
from v02003.a.build import build
from v02003.a.lib import interface_cluster
from v02003.a.lib import database
from v02003.utility import SSHHelper
from tkinter import Tk, ttk, Menu, N, W, E, S, StringVar, HORIZONTAL
from sys import platform, version_info

if not version_info[0] >= 3:
    from os import system

    print('INSTALLING PYTHON 3 for CENTOS 7')
    system('sudo yum install -y https://centos7.iuscommunity.org/ius-release.rpm')
    system('sudo yum update')
    system('sudo yum install -y python36u python36u-libs python36u-devel python36u-pip')


root = Tk()
root.title("NIMB, "+build)

mainframe = ttk.Frame(root, padding="3 3 12 12")

mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

label = ttk.Label
button = ttk.Button


menubar = Menu(root)
filemenu = Menu(menubar, tearoff=0)
menubar.add_cascade(label='actions', menu=filemenu)
filemenu.add_command(label='stop all active tasks',
                     command=lambda: StopAllActiveTasks())
root.config(menu=menubar)

ccredentials_txt = StringVar()
freesurfer_address_var = StringVar()
status = StringVar()
folder_for_glm = StringVar()

freesurfer = database._get_folder('Main')


def setupcredentials():
    from v02003.a.setup import setupcredentials
    if setupcredentials():
        clusters = database._get_Table_Data('Clusters','all')
        # ccredentials_txt.set(clusters[0][1]+'@'+clusters[0][2])


def set_Project_Data(Project):
    from v02003.a.setup import SetProjectData
    SetProjectData(Project)


def set_MainFolder(Project):
    from v02003.a.setup import set_MainFolder
    freesurfer = set_MainFolder(Project)
    freesurfer_address_var.set(freesurfer)
    print(freesurfer)


def set_LocalProcessingFolder():
    from v02003.a.setup import set_LocalProcessingFolder
    local = set_LocalProcessingFolder()
    local_fs_address.set(local) # where local_fs_address?


def set_Folder(group, Project):
    from v02003.a.setup import set_Folder
    Projects_all[Project][group].set(set_Folder(group, Project)) # where it is?


def cstatus():
    try:
        clusters = database._get_Table_Data('Clusters','all')
        from v02003.a.lib.interface_cluster import check_cluster_status
        cuser = clusters[0][1]
        caddress = clusters[0][2]
        cpw = clusters[0][5]
        cmaindir = clusters[0][3]
        status.set('Checking the Cluster')
        status.set('There are '
                   + str(check_cluster_status(cuser,
                                              caddress, cpw, cmaindir)[0])
                   + ' sessions and '
                   + str(check_cluster_status(cuser,
                                              caddress, cpw, cmaindir)[1])
                   + ' are queued')
    except FileNotFoundError:
        setupcredentials()
        clusters = database._get_Table_Data('Clusters','all')
        cstatus()


def StopAllActiveTasks():
    from v02003.a.lib.interface_cluster import delete_all_running_tasks_on_cluster
    clusters = database._get_Table_Data('Clusters','all')
    delete_all_running_tasks_on_cluster(
        clusters[0][1], clusters[0][2], clusters[0][5], clusters[0][3])


def xtrctdata():
    try:
        from a.lib import makestats
        status.set('Copying data from Cluster and creating Excel file')
        makestats.cpfromclusterxtrctdata()
    except ImportError:
        print('error importing the makestats file from a.lib')
        pass


def runstats(Project_Data, Project):
    id_col = 'id'
    group_col = 'group'

    from os import makedirs, path, listdir
    from datetime import datetime

    file_groups = Project_Data[Project][3]
    if len(file_groups) > 0:
        print('file groups present, starting making fsgd files')
        try:
            from a.lib import makestats_groups
            status.set('Creating FSGD files for GLM analysis')
            GLM_dir = Project_Data[Project][2]+Project+'/'+str(datetime.now().year)+str(
                datetime.now().month)+str(datetime.now().day)+'/'
            if not path.isdir(GLM_dir):
                makedirs(GLM_dir)
            makestats_groups.MakeStatsForGroups(
                GLM_dir, file_groups, id_col, group_col, Project_Data[Project][1])
        except ImportError:
            print('error importing the makestats_groups from a.lib')
            pass
    if platform == 'darwin' or platform == 'linux' or platform == 'linux2':
        if len(listdir(Project_Data[Project][2])) > 0 and len(database._get_folder('LocalProcessing')) > 0:
            print('GLM dir not empty, local processing present, performing glm')
            try:
                from a.lib import makeglm
                status.set('Performing GLM')
                GLM_dir = Project_Data[Project][2]+Project+'/'
                for folder in listdir(GLM_dir):
                    if 'results' not in listdir(GLM_dir+folder):
                        PATH_4glm = GLM_dir+folder+'/'
                        makeglm.PerformGLM(
                            PATH_4glm, database._get_folder('LocalProcessing'))
                    else:
                        print('results created')
            except ImportError:
                print('ERROR importing makeglm module')
                pass


def runplots():
    from v02003.a.lib import makestats
    makestats.mkstatisticsfplots()


def run_processing_on_cluster_2():
    '''
    this is an enhanced version of run_processing_on_cluster
    it does not need to use th config.py to get data
    :return:
    '''
    # version 2: add username, password, and command line to run here
    clusters = database._get_Table_Data('Clusters','all')
    user_name = clusters[list(clusters)[0]]['Username']
    user_password = clusters[list(clusters)[0]]['Password']
    project_folder = clusters[list(clusters)[0]]['HOME']
    cmd_run = " python a/crun.py -submit false" #submit=true
    load_python_3 = 'module load python/3.7.4;'
    cmd_run_crun_on_cluster = load_python_3 +"cd " + "/home/hvt/" + "; " + cmd_run
    print("command: "+ cmd_run_crun_on_cluster)
    host_name = clusters[list(clusters)[0]]['remote_address']

    print("Start running the the command via SSH in cluster: python a/crun.py")
    SSHHelper.running_command_ssh_2(host_name=host_name, user_name=user_name,
                                    user_password=user_password,
                                    cmd_run_crun_on_cluster=cmd_run_crun_on_cluster)





def run(Project):
    # 0 check the variables
    # check if all the variabled are defined
    check_defined_variable(Project)
    # it can do better by reading the eml.json or beluga.json and check for the missing var
    # 1. install required library and software on the local computer, including freesurfer
    setting_up_local_computer()
    # 2. check and install required library on remote computer
    print("Setting up the remote server")
    setting_up_remote_linux_with_freesurfer()

    print("get list of un-process subject. to be send to the server")
    # must set SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR before calling
    # DistributionHelper.get_list_subject_to_be_processed_remote(SOURCE_SUBJECTS_DIR, PROCESSED_FS_DIR)
    # how this part work?
    status.set('Copying data to cluster ')
    #  copy subjects to cluster
    run_copy_subject_to_cluster(Project)

    status.set('Cluster analysis started')
    status.set("Cluster analysing running....")



    run_processing_on_cluster_2()
    print("Do processing here, temporary block that function")
    # do the processing here
    # check the status of running application
    #
    # set_MainFolder(Project)
    # cpFromCluster() # todo: dead here
    #
    # status.set('Copying processed data from cluster')
    #
    # if platform == 'darwin' or platform == 'linux' or platform == 'linux2':
    #     print('starting local analysis')
    #     from os import system
    #     # define LocalProcessing folder
    #     print("here is the error: " + database._get_folder('LocalProcessing'))
    #     system('python '+database._get_folder('LocalProcessing')+'a/local_run.py')
    # path = 'a/lib/local_run.py '
    # system('python a/lib/local_run.py')

def setting_up_local_computer():
    if platform.startswith('linux'):
        print("Currently only support setting up on Ubuntu-based system")
        # do the job here
        setting_up_local_linux_with_freesurfer()
    elif platform in ["win32"]:
        print("The system is not fully supported in Windows OS. The application quits now .")
        exit()
    else: # like freebsd,
        print("This platform is not supported")
        exit()
def setting_up_local_linux_with_freesurfer():
    """
    install the require libarary
    :return:
    """
    try:
        from v02003.a.setup import SETUP_LOCAL_v2
    except:
        from v02003.a.setup import SETUP_LOCAL_v2

    SETUP_LOCAL_v2()

def setting_up_remote_linux_with_freesurfer():
    # go the remote server by ssh, enter the $HOME (~) folder
    # execute following commands
    # 0. prepare the python load the python 3.7.4
    # 1. git clone the repository
    # 2. run the python file remote_setupv2.py

    clusters = database._get_Table_Data('Clusters', 'all')
    user_name = clusters[list(clusters)[0]]['Username']
    user_password = clusters[list(clusters)[0]]['Password']
    #todo:
    git_repo = "https://github.com/alexhanganu/nimb/"
    load_python_3 = 'module load python/3.7.4;'
    cmd_git = f" cd ~; git clone {git_repo};  "
    cmd_run_setup = " cd nimb/setup; python remote_setupv2.py"

    cmd_run_crun_on_cluster = load_python_3 + cmd_git + cmd_run_setup
    print("command: " + cmd_run_crun_on_cluster)
    host_name = clusters[list(clusters)[0]]['remote_address']
    # todo: how to know if the setting up is failed?
    print("Setting up the remote cluster")
    SSHHelper.running_command_ssh_2(host_name=host_name, user_name=user_name,
                                    user_password=user_password,
                                    cmd_run_crun_on_cluster=cmd_run_crun_on_cluster)

def error_message(variable):
    print(f"{variable} is empty or not defined, please check it again ")
    print("The application is now exit")
    exit()


def check_defined_variable(Project):
    """
    The application with immediately quit if any of these variable is not define
    :param Project:
    :return: None
    """
    # todo: refactor to remove duplicate code
    # todo:
    clusters = database._get_Table_Data('Clusters', 'all')
    cname = [*clusters.keys()][0]
    password = clusters[cname]['Password']
    supervisor_ccri = clusters[cname]['Supervisor_CCRI']
    if not password:
        error_message("password to login to remote cluster")
    if not supervisor_ccri:
        error_message("supervisor_ccri")
    if not cname:
        error_message("cluster name ")
    project_folder = clusters[cname]['HOME']
    if not project_folder:
        error_message("your home folder")
    a_folder = clusters[cname]['App_DIR']
    if not a_folder:
        error_message("a_folder")
    subjects_folder = clusters[cname]['Subjects_raw_DIR']
    if not subjects_folder:
        error_message("Subjects_raw_DIR")
    # mri_path = database._get_Table_Data('Projects', Project)[Project]['mri_dir']
    # mri path is not in the sqlite location. must be updated


def run_copy_subject_to_cluster(Project):
    '''
    copy the subjects from subject json file to cluster
    :param Project: the json file of that project
    :return: None
    '''
    # todo: how to get the active cluster for this project
    clusters = database._get_Table_Data('Clusters', 'all')
    cname = [*clusters.keys()][0]
    project_folder = clusters[cname]['HOME']
    a_folder = clusters[cname]['App_DIR']
    subjects_folder = clusters[cname]['Subjects_raw_DIR']
    # the json path is getting from mri path,
    mri_path = database._get_Table_Data('Projects', Project)[Project]['mri_dir']
    print(mri_path)
    print("subject json: " + mri_path)
    interface_cluster.copy_subjects_to_cluster(mri_path, subjects_folder, a_folder)


row = 0
Project_Data = database._get_Table_Data('Projects', 'all')
if len(Project_Data) > 0:
    for Project in Project_Data:
        col = 0
        button(mainframe, text=Project, command=lambda: set_Project_Data(
            Project)).grid(row=row, column=col)
        col += 1
        # if platform == 'darwin' or platform == 'linux' or platform == 'linux2':
        #     local_fs_address.set(database._get_folder('LocalProcessing'))
        #     button(mainframe, textvariable=local_fs_address,
        #            command=set_LocalProcessingFolder).grid(row=row, column=col, sticky=W)
        #     col += 1
        button(mainframe, text="do processing", command=lambda: run(
            Project)).grid(row=row, column=col)
        col += 1

        button(mainframe, text="copy subjects to cluster",
               command=lambda: run_copy_subject_to_cluster(Project)).grid(row=row, column=col)
        mri_path = database._get_Table_Data('Projects', Project)[Project]['mri_dir']
        col += 1

        # button(mainframe, text="do stats", command=lambda: runstats(
        #     Project_Data, Project)).grid(row=row, column=col, sticky=W)
        row += 1

ttk.Separator(mainframe, orient=HORIZONTAL).grid(
    row=row, column=0, columnspan=7, sticky='ew')
row += 1

# button(mainframe, text="Check new MRI all data", command=chkmri).grid(column=5, row=row, columnspan=2, sticky=W)
# button(mainframe, text="Extract data all subjects", command=xtrctdata).grid(row=row+1, column=5, columnspan=2, sticky=W)
# row += 1

clusters = database._get_Table_Data('Clusters', 'all')
cred = ['not set']
####
# clusters = database._get_credentials('all')
# cuser = clusters[0][1]
# caddress = clusters[0][2]
# cpw = clusters[0][5]
# cmaindir = clusters[0][3]

####

for cred in clusters:
    button(mainframe, text=cred, command=setupcredentials).grid(
        row=row, column=0, sticky=W)
    row += 1

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)

root.mainloop()

'''
this script was written for a specific lab, it is probably not needed anymore.

def chkmri():
    from a.setup import SETUP_APP
    if not SETUP_APP():
        print('SETUP not finished')
        pass
    try:
        from a.lib.data_processing_local import chklog

        status.set('Scanning for new data in the INCOMING folder')
        print('Scanning for new data in the INCOMING folder')
        lsmiss = chklog()
        print(lsmiss)
        count = 0
        for DIR in lsmiss:
            count = count + len(lsmiss[DIR])
        if count > 0:
            status.set(str(count)+' subjects need to be processed')
            database.create_lsmiss(lsmiss)
            try:
                from a.lib.data_processing_local import cpt1flair
                status.set('Copying data to '+freesurfer+'raw_data_dcm/')
                cpt1flair()
            except ImportError:
                print('Can\'t copy T1-Flair file - ERROR importing file')
                pass
        else:
            status.set('No new uploads in the INCOMING folder')
    except ImportError:
        status.set('ERROR importing the working file')
        print('ERROR importing the working file')
'''
