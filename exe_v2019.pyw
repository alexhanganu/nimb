
#Alexandru Hanganu, 2018 April 11
#modules to install: pandas, scipy, glob, shutil, openpyxl, xlrd(data_processing_local.chklog)

from sys import platform, exit, version_info
    
if not version_info[0] >= 3:
    from os import system
    print('INSTALLING PYTHON 3 for CENTOS 7')
    system('sudo yum install -y https://centos7.iuscommunity.org/ius-release.rpm')
    system('sudo yum update')
    system('sudo yum install -y python36u python36u-libs python36u-devel python36u-pip')
from tkinter import Tk, Frame, ttk, Label, Menu, N, W, E, S, StringVar

from a.lib import database
from a.build import build

root = Tk()
root.title("NIMB, "+build)

mainframe = ttk.Frame(root, padding="3 3 12 12")

mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

label = ttk.Label
button = ttk.Button


menubar = Menu(root)
filemenu = Menu(menubar, tearoff = 0)
menubar.add_cascade(label='actions', menu = filemenu)
filemenu.add_command(label='stop all active tasks', command = lambda: StopAllActiveTasks())
root.config(menu=menubar)

ccredentials_txt = StringVar()
freesurfer_address_var = StringVar()
status = StringVar()
	
def setupcredentials():
    from a.setup import setupcredentials
    if setupcredentials():
        clusters = database._get_credentials('all')
        # ccredentials_txt.set(clusters[0][1]+'@'+clusters[0][2])

def set_incoming_dir():
    from a.setup import set_incoming_dir
    set_incoming_dir()

def set_MainFolder():
    from a.setup import set_MainFolder
    freesurfer = set_MainFolder()
    freesurfer_address_var.set(freesurfer)

def set_LocalProcessingFolder():
    from a.setup import set_LocalProcessingFolder
    local = set_LocalProcessingFolder()
    local_fs_address.set(local)


def cstatus():
    try:
        clusters = database._get_credentials('all')
        from a.lib.interface_cluster import check_cluster_status
        cuser = clusters[0][1]
        caddress = clusters[0][2]
        cpw = clusters[0][5]
        cmaindir = clusters[0][3]
        status.set('Checking the Cluster')
        status.set('There are '+str(check_cluster_status(cuser, caddress, cpw, cmaindir)[0])+' sessions and '+str(check_cluster_status(cuser, caddress, cpw, cmaindir)[1])+' are queued')
    except FileNotFoundError:
        setupcredentials()
        clusters = database._get_credentials('all')
        cstatus()


def StopAllActiveTasks():
    from a.lib.interface_cluster import delete_all_running_tasks_on_cluster
    clusters = database._get_credentials('all')
    delete_all_running_tasks_on_cluster(clusters[0][1], clusters[0][2], clusters[0][5], clusters[0][3])
		

def xtrctdata():
    try:
        from a.lib import makestats
        status = StringVar()
        status.set('Copying data from Cluster and creating Excel file')
        makestats.cpfromclusterxtrctdata()
    except ImportError:
        print('error importing the makestats file from a.lib')
        pass

def runstats():
    try:
        from a.lib import makestats
        status = StringVar()
        status.set('Creating the file with statistical results')
        makestats.mkstatisticsf()
    except ImportError:
        print('error importing the makestats file from a.lib')
        pass

def runplots():
    from a.lib import makestats
    makestats.mkstatisticsfplots()
	
def chkmri():
    from a.setup import SETUP_APP
    if not SETUP_APP():
        print('SETUP not finished')
        pass
    try:
        from a.lib.data_processing_local import chklog

        status.set('Scanning for new data in the INCOMING folder')
        print('Scanning for new data in the INCOMING folder')
        lsmiss=chklog()
        print(lsmiss)
        count = 0
        for DIR in lsmiss:
            count = count +len(lsmiss[DIR])
        if count>0:
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

def run():
    from a.lib.data_processing_local import cp2cluster
    from a.lib.data_processing_local import cpFromCluster
    status.set('Copying data to cluster ...')
    cp2cluster()
    status.set('Cluster analysis started')
    cpFromCluster()
    status.set('Copying processed data from cluster')

    if platform == 'darwin' or platform == 'linux' or platform == 'linux2':
        print('starting local analysis')
        from os import system
        system('python '+database._get_folder('LocalProcessing')+'a/local_run.py')



freesurfer = database._get_folder('Main')
DIRs_INCOMING = database._get_folder('MRI')

row = 1

if len(DIRs_INCOMING)>0:
    for DIR in DIRs_INCOMING:
        label(mainframe, text='MRI in: '+DIR).grid(column=0, row=row, sticky=E)
        button(mainframe, text=str(DIRs_INCOMING[DIR]), command=set_incoming_dir).grid(column=1, row=row, sticky=W)
        row += 1
else:
    label(mainframe, text='MRI folder not set').grid(column=0, row=row, sticky=E)
    button(mainframe, text='set folder', command=set_incoming_dir).grid(column=1, row=row, sticky=W)
    row += 1

freesurfer_address_var.set(freesurfer)
label(mainframe, text="folder for results : ").grid(column=0, row=row, sticky=E)
button(mainframe, textvariable=freesurfer_address_var, command=set_MainFolder).grid(column=1, row=row, sticky=W)
row += 1

if platform == 'darwin' or platform == 'linux' or platform == 'linux2':
    local_processing_folder = database._get_folder('LocalProcessing')
    local_fs_address = StringVar()
    local_fs_address.set(local_processing_folder)
    label(mainframe, text="folder for local processing : ").grid(column=0, row=row, sticky=E)
    button(mainframe, textvariable=local_fs_address, command=set_LocalProcessingFolder).grid(column=1, row=row, columnspan=2, sticky=W)
    row += 1

button(mainframe, text="clusters for processing :", command=setupcredentials).grid(column=0, row=row, sticky=E)
clusters = database._get_credentials('all')
name = []
for cred in clusters:
    name.append(cred)
ccredentials_txt.set(', '.join(name))
label(mainframe, textvariable=ccredentials_txt).grid(column=1, row=row, sticky=W)
row += 1

status.set('online')
label(mainframe, text="Status on clusters: ").grid(column=0, row=row, sticky=E)
button(mainframe, textvariable=status, command=cstatus).grid(column=1, row=row, sticky=W)
row += 1

button(mainframe, text="Check for new MRI data", command=chkmri).grid(column=0, row=row, sticky=W)
button(mainframe, text="Extract data from all subjects", command=xtrctdata).grid(column=1, row=row, sticky=W)
row += 1

button(mainframe, text="RUN", command=run).grid(column=0, row=row, sticky=W)
button(mainframe, text="Create statistics for groups", command=runstats).grid(column=1, row=row, sticky=W)

for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

root.mainloop()
