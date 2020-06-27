#2020 jan 15
#add bash to chk if python is installed

from sys import platform, modules#, version_info
import os, threading, time, shutil
from os import listdir, system, path, makedirs, getcwd, remove, chdir

from tkinter import Tk, Frame, ttk, Entry, Label, StringVar, filedialog, simpledialog

from a.clib.var import freesurfer_version
from a.lib import database

win_netframework_download_address = 'https://www.microsoft.com/en-us/download/details.aspx?id=48137'
win_visualstudio_download_address = 'http://landinghub.visualstudio.com/visual-cpp-build-tools'
win_visualstudio_download_address2 = 'https://www.visualstudio.com/thank-you-downloading-visual-studio/?sku=BuildTools&rel=15'
win_putty_download_address = 'https://www.ssh.com/a/putty-0.70-installer.msi'
freesurfer71_centos6_download_address = 'https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.1.0/freesurfer-linux-centos6_x86_64-7.1.0.tar.gz'
freesurfer71_centos7_download_address = 'https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.1.0/freesurfer-linux-centos7_x86_64-7.1.0.tar.gz'
freesurfer71_centos8_download_address = 'https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.1.0/freesurfer-linux-centos8_x86_64-7.1.0.tar.gz'
freesurfer60_download_address = 'ftp://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/6.0.0/freesurfer-Linux-centos6_x86_64-stable-pub-v6.0.0.tar.gz'
# https://surfer.nmr.mgh.harvard.edu/fswiki/MatlabRuntime

if freesurfer_version>6:
    matlab_runtime_download_address_FS7 = 'https://ssd.mathworks.com/supportfiles/downloads/R2014b/deployment_files/R2014b/installers/glnxa64/MCR_R2014b_glnxa64_installer.zip'
else:
    matlab_runtime_download_address_FS6 = 'https://ssd.mathworks.com/supportfiles/MCR_Runtime/R2012b/MCR_R2012b_glnxa64_installer.zip -o installer.zip'
    matlab_runtime_download_address_FS6 = 'http://surfer.nmr.mgh.harvard.edu/fswiki/MatlabRuntime?action=AttachFile&do=get&target=runtime2012bLinux.tar.gz'




miniconda_installation = 'curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh'

freesurfer_download_address = freesurfer71_centos7_download_address

'''chmod +x Anaconda3-5
./Anaconda3-5
echo "export PATH=~../anaconda_path/bin:$PATH >> $HOME/.bashrc"
conda install -c conda-forge dcm2niix                                                                    
pip install dcm2bids
'''

class setupcredentials():
    def __init__(self):
        self.main = Tk()
        self.main.title("Setup Credentials")

        note = ttk.Notebook(self.main)
    
        clusters = database._get_credentials('all')
        for rname in clusters:
            tab = ttk.Frame(note)
            note.add(tab, text=rname)
            self.ListClusters(tab,clusters,rname)
        note.pack()

    def ListClusters(self,tab,clusters,rname):
        row = 1
        for key in clusters[rname]:
            if key != 'Password':
                Label(tab, text=key).grid(row = row, column = 0)
                Label(tab, text=clusters[rname][key]).grid(row = row, column = 1)
                row += 1

        ttk.Button(tab, text='Change data', command=lambda: self.ChangeAddCluster(clusters, rname)).grid(row=row +1, column=0)
        ttk.Button(tab, text='Add cluster', command=lambda: self.ChangeAddCluster(database._get_Table_Data('Clusters','defaultClusters'), 'defaultClusters')).grid(row=row +1, column=1)
        # ttk.Button(tab, text='Add cluster', command=lambda: self.ChangeAddCluster(database._get_credentials('default'), 'default')).grid(row=row +1, column=1)
        
    def ChangeAddCluster(self, clusters,rname):
            self.ChangeAddClusterFrame = Tk()
            row = 0
            Label(self.ChangeAddClusterFrame, text='remote Name:').grid(row = row, column = 0)
            self.EntryClusterName = Entry(self.ChangeAddClusterFrame)
            self.EntryClusterName.grid(row=row, column=1)
            self.EntryClusterName.insert(0, rname)

            row += 1
            Label(self.ChangeAddClusterFrame, text='remote Username:').grid(row = row, column = 0)
            self.EntryUser = Entry(self.ChangeAddClusterFrame)
            self.EntryUser.grid(row=row, column=1)
            self.EntryUser.insert(0, clusters[rname]['Username'])

            row += 1
            Label(self.ChangeAddClusterFrame, text='remote address:').grid(row = row, column = 0)
            self.EntryAddress = Entry(self.ChangeAddClusterFrame)
            self.EntryAddress.grid(row=row, column=1)
            self.EntryAddress.insert(0, clusters[rname]['remote_address'])

            row += 1
            Label(self.ChangeAddClusterFrame, text='remote Home folder:').grid(row = row, column = 0)
            self.EntryHomeDir = Entry(self.ChangeAddClusterFrame)
            self.EntryHomeDir.grid(row=row, column=1)
            if len(clusters[rname]['HOME']) >1:
                self.EntryHomeDir.insert(0, clusters[rname]['HOME'])
            else:
                self.EntryHomeDir.insert(0, '/home')

            row += 1
            Label(self.ChangeAddClusterFrame, text='remote Scratch folder:').grid(row = row, column = 0)
            self.EntryScratchDir = Entry(self.ChangeAddClusterFrame)
            self.EntryScratchDir.grid(row=row, column=1)
            if len(clusters[rname]['SCRATCH']) >1:
                self.EntryScratchDir.insert(0, clusters[rname]['SCRATCH'])
            else:
                self.EntryScratchDir.insert(0, '/scratch')

            row += 1
            Label(self.ChangeAddClusterFrame, text='remote NIMB folder:').grid(row = row, column = 0)
            self.EntryNIMBFolder = Entry(self.ChangeAddClusterFrame)
            self.EntryNIMBFolder.grid(row=row, column=1)
            if len(clusters[rname]['App_DIR']) >1:
                self.EntryNIMBFolder.insert(0, clusters[rname]['App_DIR'])
            else:
                self.EntryNIMBFolder.insert(0, '/home/USER/a')

            row += 1
            Label(self.ChangeAddClusterFrame, text='remote Subjects Folder:').grid(row = row, column = 0)
            self.EntrySubjectFolder = Entry(self.ChangeAddClusterFrame)
            self.EntrySubjectFolder.grid(row=row, column=1)
            if len(clusters[rname]['Subjects_raw_DIR']) >1:
                self.EntrySubjectFolder.insert(0, clusters[rname]['Subjects_raw_DIR'])
            else:
                self.EntrySubjectFolder.insert(0, '/home/USER/subjects')

            row += 1
            Label(self.ChangeAddClusterFrame, text='remote processed SUBJECTS folder:').grid(row = row, column = 0)
            self.EntryProcessedSubjectsDir = Entry(self.ChangeAddClusterFrame)
            self.EntryProcessedSubjectsDir.grid(row=row, column=1)
            if len(clusters[rname]['Processed_SUBJECTS_DIR']) >1:
                self.EntryProcessedSubjectsDir.insert(0, clusters[rname]['Processed_SUBJECTS_DIR'])
            else:
                self.EntryProcessedSubjectsDir.insert(0, '/scratch/USER/processed')
                
            row += 1
            Label(self.ChangeAddClusterFrame, text='Password:').grid(row = row, column = 0)
            self.EntryPW = Entry(self.ChangeAddClusterFrame, show='*')
            self.EntryPW.grid(row=row, column=1)
            self.EntryPW.insert(0, clusters[rname]['Password'])

            row += 1
            Label(self.ChangeAddClusterFrame, text='Supervisor CCRI:').grid(row = row, column = 0)
            self.EntrySupervisorCCRI = Entry(self.ChangeAddClusterFrame)
            self.EntrySupervisorCCRI.grid(row=row, column=1)
            self.EntrySupervisorCCRI.insert(0, clusters[rname]['Supervisor_CCRI'])

            row += 1
            ttk.Button(self.ChangeAddClusterFrame, text='Submit', command=self.SetCluster).grid(row=row, column=0)
            ttk.Button(self.ChangeAddClusterFrame, text='Delete', command=self.DeleteCluster).grid(row=row, column=1)
	
    def SetCluster(self):

        cname = str(self.EntryClusterName.get())
		
        credentials = {}
        credentials[cname] = {}
        #database.__get_table_cols('Clusters')[1:]
        credentials[cname]['Username'] = str(self.EntryUser.get())
        credentials[cname]['remote_address'] = str(self.EntryAddress.get())
        credentials[cname]['HOME'] = str(self.EntryHomeDir.get())
        credentials[cname]['SCRATCH'] = str(self.EntryScratchDir.get())
        credentials[cname]['App_DIR'] = str(self.EntryNIMBFolder.get())
        credentials[cname]['Subjects_raw_DIR'] = str(self.EntrySubjectFolder.get())
        credentials[cname]['Processed_SUBJECTS_DIR'] = str(self.EntryProcessedSubjectsDir.get())
        credentials[cname]['Password'] = str(self.EntryPW.get())
        credentials[cname]['Supervisor_CCRI'] = str(self.EntrySupervisorCCRI.get())


        database._set_credentials(credentials, cname)
        #send_2_thread(SETUP_CLUSTER(cname, cuser, caddress, chome_dir, cscratch_dir, cpw, supervisor_ccri)
        self.ChangeAddClusterFrame.destroy()
        self.main.destroy()		

    def DeleteCluster(self):
        cname = str(self.EntryClusterName.get())
        database._delete_credentials(cname)
        self.ChangeAddClusterFrame.destroy()
        self.main.destroy()		


def send_2_thread(program):
    threading.Thread(target=program).start()


class SetProjectData():
    def __init__(self, Project):
        self.main = Tk()
        self.main.title("Set Project Data")
        self.tmp_project = dict()
        note = ttk.Notebook(self.main)

        Project_Data = database._get_Table_Data('Projects','all')
        # Project_Data = database._get_Project_Data('all')
        for Project in Project_Data:
            self.tmp_project[Project] = {
            'mri_dir':StringVar(), 'results_dir':StringVar(), 'glm_dir':StringVar(), 'file_groups':StringVar()}
            tab = ttk.Frame(note)
            note.add(tab, text=Project)
            self.ListProjects(tab,Project_Data,Project)
        note.pack()

    def ListProjects(self,tab,Project_Data,Project):
        if Project != 'not set':
            print(Project_Data)
            self.tmp_project[Project]['mri_dir'].set(Project_Data[Project]['mri_dir'])
            self.tmp_project[Project]['results_dir'].set(Project_Data[Project]['results_dir'])
            self.tmp_project[Project]['glm_dir'].set(Project_Data[Project]['glm_dir'])
            self.tmp_project[Project]['file_groups'].set(Project_Data[Project]['file_groups'])
			
            Label(tab, text='Project:').grid(row = 1, column = 0)
            ttk.Button(tab, text=Project,command=lambda: self.set_Project_name(Project)).grid(row=1, column=1)

            Label(tab, text='MRI folder or .json file:').grid(row = 2, column = 0)
            ttk.Button(tab, text=self.tmp_project[Project]['mri_dir'].get(),command=lambda: self.set_Project_file(Project, 'mri_dir')).grid(row=2, column=1)

            Label(tab, text='Results folder:').grid(row = 3, column = 0)
            ttk.Button(tab, text=self.tmp_project[Project]['results_dir'].get(),command=lambda: self.set_Project_folder(Project, 'results_dir')).grid(row=3, column=1)
			
            Label(tab, text='GLM folder:').grid(row = 4, column = 0)
            ttk.Button(tab, text=self.tmp_project[Project]['glm_dir'].get(),command=lambda: self.set_Project_folder(Project, 'glm_dir')).grid(row=4, column=1)

            Label(tab, text='file with clinical data and groups:').grid(row = 5, column = 0)
            ttk.Button(tab, text=self.tmp_project[Project]['file_groups'].get(),command=lambda: self.set_Project_file(Project, 'file_groups')).grid(row=5, column=1)

            #ttk.Button(tab, text='Change data', command=lambda: self.ChangeAddProject(Project_Data, Project)).grid(row=7, column=0)
            ttk.Button(tab, text='Add Project', command=lambda: self.ChangeAddProject({"":['None','None','None','None']},'')).grid(row=7, column=1)
        else:
            self.Project_var = StringVar()
            self.Project_var.set(Project)
            Label(tab, text='Project:').grid(row = 1, column = 0)
            ttk.Button(tab, text=self.Project_var.get(),command=lambda: self.set_Project_name(Project)).grid(row=1, column=1)


    def set_Project_name(self, Project):
        answer = simpledialog.askstring('Project name:', '')
        if answer is not None:
            self.Project_var.set(answer)
            database._set_Project_Data_d(Project, '', answer)
        else:
            pass
    def set_Project_folder(self, Project, group):
        setdir = filedialog.askdirectory()+'/'
        self.tmp_project[Project][group].set(setdir)
        database._set_Project_Data_d(Project, group, setdir)

    def set_Project_file(self, Project, group):
        set_file = filedialog.askopenfilename(title='Select file',)
        self.tmp_project[Project][group].set(set_file)
        database._set_Project_Data_d(Project, group, set_file)

    def ChangeAddProject(self, Project_Data,Project):	
            self.ChangeAddProjectFrame = Tk()
            self.ChangeAddProjectFrame.grab_set()
            Label(self.ChangeAddProjectFrame, text='Project Name:').grid(row = 0, column = 0)
            self.EntryProjectID = Entry(self.ChangeAddProjectFrame)
            self.EntryProjectID.grid(row=0, column=1)
            self.EntryProjectID.insert(0, Project)

            Label(self.ChangeAddProjectFrame, text='MRI folder:').grid(row = 1, column = 0)
            self.EntryMRIDir = Entry(self.ChangeAddProjectFrame)
            self.EntryMRIDir.grid(row=1, column=1)
            self.EntryMRIDir.insert(0, Project_Data[Project][0])

            Label(self.ChangeAddProjectFrame, text='Results folder:').grid(row = 2, column = 0)
            self.EntryResultsDir = Entry(self.ChangeAddProjectFrame)
            self.EntryResultsDir.grid(row=2, column=1)
            self.EntryResultsDir.insert(0, Project_Data[Project][1])

            Label(self.ChangeAddProjectFrame, text='GLM folder:').grid(row = 3, column = 0)
            self.EntryGLMDir = Entry(self.ChangeAddProjectFrame)
            self.EntryGLMDir.grid(row=3, column=1)
            self.EntryGLMDir.insert(0, Project_Data[Project][2])

            Label(self.ChangeAddProjectFrame, text='File with groups:').grid(row = 4, column = 0)
            self.EntryFileWithGroups = Entry(self.ChangeAddProjectFrame)
            self.EntryFileWithGroups.grid(row=4, column=1)
            self.EntryFileWithGroups.insert(0, Project_Data[Project][3])

            ttk.Button(self.ChangeAddProjectFrame, text='Submit', command=self.SetProject).grid(row=7, column=0)
            ttk.Button(self.ChangeAddProjectFrame, text='Delete', command=self.DeleteProject).grid(row=7, column=1)


    def SetProject(self):
        id = str(self.EntryProjectID.get())

        data_requested = {}
        data_requested[_id] = {}
        data_requested[_id]['id'] = _id
        data_requested[_id]['mri_dir'] = str(self.EntryMRIDir.get())
        data_requested[_id]['results_dir'] = str(self.EntryResultsDir.get())
        data_requested[_id]['glm_dir'] = str(self.EntryGLMDir.get())
        data_requested[_id]['file_groups'] = str(self.EntryFileWithGroups.get())

        database._set_Table_Data('Projects',data_requested,_id)
        # mri_dir = str(self.EntryMRIDir.get())
        # results_dir = str(self.EntryResultsDir.get())
        # glm_dir = str(self.EntryGLMDir.get())
        # file_groups = str(self.EntryFileWithGroups.get())

        # database._set_Project_Data(id, mri_dir, results_dir, glm_dir, file_groups)
        self.ChangeAddProjectFrame.destroy()
        self.main.destroy()		

    def DeleteProject(self):
        id = str(self.EntryProjectID.get())
        database._delete_Project(id)
        self.ChangeAddProjectFrame.destroy()
        self.main.destroy()		

def set_MainFolder(Project):
    setdir = filedialog.askdirectory()
    MainFolder=setdir+'/'
    database._set_folder('Main', 'Main Folder', MainFolder)
    return MainFolder


def set_LocalProcessingFolder():
    setdir = filedialog.askdirectory()
    LocalProcessingFolder=setdir+'/'
    database._set_folder('LocalProcessing', 'Local Processing Folder', LocalProcessingFolder)
    return LocalProcessingFolder
    send_2_thread(SETUP_LOCAL(LocalProcessingFolder))


def set_FileWithGroupsForStats():
    file = filedialog.askopenfilename(initialdir = "/", title="Select Excel file", 
                filetypes=(("excel files","*.xlsx"),("excel file","*.xls")))
    #database._set_folder('LocalProcessing', 'Local Processing Folder', file)
    return file

def set_Folder(group,Project):
    Project_Data = database._get_Project_Data(Project)
    if group == 'file_groups':
        result=filedialog.askopenfilename()
        Project_Data[Project][3] = result
    else:
        result=filedialog.askdirectory()+'/'
        if group == 'mri_dir':
            Project_Data[Project][0] = result
        if group == 'results_dir':
            Project_Data[Project][1] = result
        if group == 'glm_dir':
            Project_Data[Project][2] = result
    database._set_Project_Data(Project, Project_Data[Project][0], Project_Data[Project][1], Project_Data[Project][2], Project_Data[Project][3])
    return result

	
def SETUP_APP():
    MainFolder = database._get_folder('Main')
    if not os.path.exists(MainFolder+'logs/'):
        makedirs(MainFolder+'logs/')
    if not os.path.exists(MainFolder+'processed/'):
        makedirs(MainFolder+'processed/')
    if not os.path.exists(MainFolder+'raw_t1/'):
        makedirs(MainFolder+'raw_t1/')
    if not os.path.exists(MainFolder+'statistics/'):
        makedirs(MainFolder+'statistics/')
    if not os.path.exists(MainFolder+'statistics/stats/'):
        makedirs(MainFolder+'statistics/stats/')
    if platform in ["linux", "linux2"]:
        os.system(f"chmod -R 777 {MainFolder}")
        # must use python3
    #!!!!!!!!!!! modules works only when soft imported. Otherwise - the answer is showing that module is missing.
    if platform == 'win32':
        if 'version_dotcom_Net_Framework < 4.6' not in modules:
            print('Net Framework 4.6 or higher is needed; go to: '+win_netframework_download_address)
        if 'Microsoft Visual C++ 14.0' not in modules:
            print('Microsoft Visual Studio is required, get it with: '+win_visualstudio_download_address)
            system(win_visualstudio_download_address2)
        if 'psftp' not in modules:
            print('please install putty: '+win_putty_download_address)
            # system('set PATH=%PATH%C:\Program Files\PuTTY\psftp')
    if 'pip' not in modules:
        path = []
        system('echo %PATH% >> path_ls.txt')
        with open('path_ls.txt','r') as f:
            for line in f:
                path = line.strip('\n')
        path_ls = path.split(';')
        ls_py_path = []
        for path in path_ls:
            if 'Python' in path:
                ls_py_path.append(path)
        for path in ls_py_path:
            if '\Scripts' not in path:
                if os.path.exists(path):
                    if os.path.exists(path.replace(' ','')+'\Scripts'):
                        if any('pip' in i for i in listdir(path.replace(' ','')+'\Scripts')):
                            pip_path = path
                            print(pip_path)
                            # system('set PATH=%PATH%;'+pip_path')
                            # system('python -m pip install --upgrade pip')
    if 'pandas' not in modules:
        system('pip3 install pandas')
    if 'xlrd' not in modules:
        system('pip3 install xlrd')
    if 'xlsxwriter' not in modules:
        system('pip3 install xlsxwriter')
    if 'pydicom' not in modules:
        system('pip3 install pydicom')
    if 'pandas' and 'xlrd' and 'xlsxwriter' and 'pip' in modules:
        setup = True
    else:
        setup = False
    return setup


def create_setup_cluster_file(cname, cuser, cmaindir, cscratch_dir, supervisor_ccri, pwd, file):

    #batch_file_header, batch_walltime_cmd, max_walltime, batch_output_cmd, pbs_file_FS_setup, avail_processes, max_nr_running_batches, submit_cmd = database.Commands_cluster_scheduler(cname,cuser, supervisor_ccri)
    # text4_scheduler = '","'.join(batch_file_header)
    # text_FS_scheduler = '","'.join(pbs_file_FS_setup)
    # ls_process_order = '","'.join(avail_processes)

    py_file_header = ('#!/usr/bin/env python','# coding: utf-8')
    setup_file_content = ('import os','import shutil','\n''cmaindir=\"'+cmaindir+'\"',
                        '\n'
                        'pbs_files_and_content = {\'run.pbs\':(\'cd '+cmaindir+'\',\'python a/crun.py\')}',
                        # 'pbs_file_header = (\"'+text4_scheduler+'\")',
                        # 'pbs_file_FS_setup = (\"'+text_FS_scheduler+'\")',
                        '\n'
                        'if not os.path.exists(cmaindir+\'subjects/\'):','    os.makedirs(cmaindir+\'subjects/\')',
                        'if not os.path.exists(cmaindir+\'a/\'):','    os.makedirs(cmaindir+\'a/\')',
                        'if not os.path.exists(cscratch_dir+\'a_tmp/\'):','    os.makedirs(cscratch_dir+\'a_tmp/\')',
                        'if os.path.exists(cmaindir+\'crun.py\'):',
                        '    shutil.move(cmaindir+\'crun.py\', cmaindir+\'a/crun.py\')',
                        '    shutil.move(cmaindir+\'crunfs.py\', cmaindir+\'a/crunfs.py\')',
                        '    shutil.move(cmaindir+\'cdb.py\', cmaindir+\'a/cdb.py\')',
                        '\n'
                        'if not os.path.exists(cmaindir+\'a/__init__.py\'):',
                        '    open(cmaindir+\'a/__init__.py\',\'w\').close()',
                        '    with open(cmaindir+\'a/__init__.py\',\'a\') as f:',
                        '        f.write(\'__all__ = [\"crun, crunfs, cdb, cwalltime,var"]\')',
                        'open(cmaindir+\'a/var.py\',\'w\').close()',
                        'with open(cmaindir+\'a/var.py\',\'a\') as f:',
                        '        f.write(\'#!/bin/python\\n\')',
                        '        f.write(\'cname=\"'+cname+'\"\\n\')',
                        '        f.write(\'cuser=\"'+cuser+'\"\\n\')',
                        '        f.write(\'supervisor_ccri=\"'+supervisor_ccri+'\"\\n\')',
                        '        f.write(\'cmaindir=\"'+cmaindir+'\"\\n\')',
                        '        f.write(\'cscratch_dir=\"'+cscratch_dir+'\"\\n\')',
                        # '        f.write(\'text_4_scheduler=(\"'+text4_scheduler+'\")\\n\')',
                        # '        f.write(\'batch_walltime_cmd=(\"'+batch_walltime_cmd+'\")\\n\')',
                        # '        f.write(\'max_walltime=(\"'+max_walltime+'\")\\n\')',
                        # '        f.write(\'batch_output_cmd=(\"'+batch_output_cmd+'\")\\n\')',
                        # '        f.write(\'pbs_file_FS_setup=(\"'+text_FS_scheduler+'\")\\n\')',
                        # '        f.write(\'submit_cmd=(\"'+submit_cmd+'\")\\n\')',
                        # '        f.write(\'process_order='+ls_process_order+'\\n\')',
                        # '        f.write(\'max_nr_running_batches=(\"'+str(max_nr_running_batches)+'\")\\n\')',
                        '\n'
                        'for file in pbs_files_and_content:',
                        '    with open(cmaindir+\'a/\'+file,\'w\') as f:',
                        '        for line in pbs_file_header:',
                        '            f.write(line+\'\\n\')',
                        '        f.write(\'\\n\')',
                        '        for line in pbs_file_FS_setup:',
                        '            f.write(line+\'\\n\')',
                        '        f.write(\'\\n\')',
                        '        for line in pbs_files_and_content[file]:',
                        '            f.write(line+\'\\n\')',
                        '\n'
                        'if not os.path.exists(cmaindir+\'freesurfer/\'):',
                        '    os.chdir(cmaindir)',
                        '    os.system(\'curl "'+freesurfer_download_address+'" -o "freesurfer_installation.tar.gz" \')',
                        '    while not os.path.isfile(cmaindir+\'freesurfer_installation.tar.gz\'):',
                        '        time.sleep(1000)',
                        '    os.system(\'tar xvf freesurfer_installation.tar.gz\')',
                        '    os.remove(\'freesurfer_installation.tar.gz\')',
                        'shutil.move(cmaindir+\'.license\', cmaindir+\'freesurfer/.license\')',
                        'if not os.path.exists(cmaindir+\'freesurfer/MCRv80\'):',
                        '    os.chdir(cmaindir+\'freesurfer\')',
                        '    os.system(\'curl "'+matlab_FS_install_cmd_long+'" -o "matlab_runtime.tar.gz" \')',
                        '    while not os.path.isfile(cmaindir+\'freesurfer/matlab_runtime.tar.gz\'):',
                        '        time.sleep(30)',
                        '    os.system(\'tar xvf matlab_runtime.tar.gz\')',
                        '    os.remove(\'matlab_runtime.tar.gz\')',
                        'print(\'SETUP FINISHED\')',)

                        #os.system(\'curl -O https://repo.continuum.io/archive/Anaconda3-5.0.1-Linux-x86_64.sh \')',
                        #os.system(\'bash '+cmaindir+'Anaconda3-5.0.1-Linux-x86_64.sh\')',
                        #os.system(\'\')',
                        #print('yes')
                        #os.system(\'\')',
                        #print('yes')
                        #os.system(\'anaconda3/bin/conda install -c conda-forge dipy \')',
                        #print('y')
                        #nipype doesn\'t work
                        #os.system(\'anaconda3/bin/conda install -channel conda-forge nipype \')',

    open(pwd+file,'w').close()
    with open(pwd+file, 'a') as f:
        for line in py_file_header:
            f.write(line+'\n')
        f.write('\n')
        for line in setup_file_content:
            f.write(line+'\n')


def setup_pbs_file(pwd,cname,supervisor_ccri,cmaindir):
    batch_file_header, _, _, _, _ = database.Commands_cluster_scheduler(cname,supervisor_ccri)

    open(pwd+'a/clib/run_setup.pbs','w').close()
    with open(pwd+'a/clib/run_setup.pbs','a') as f:
                for line in batch_file_header:
                    f.write(line+'\n')
                f.write('\n')
                f.write('cd '+cmaindir+'\n')
                f.write('python setup_cluster_file.py\n')
                f.write('rm setup_cluster_file.py\n')
                f.write('rm run_setup.pbs\n')


def SETUP_CLUSTER(cname, cuser, caddress, cmaindir, cscratch_dir, cpw, supervisor_ccri):
    print('SETTING UP THE CLUSTER')
    pwd = getcwd().replace(path.sep, '/')+'/'

    create_setup_cluster_file(cname, cuser, cmaindir, cscratch_dir, supervisor_ccri, pwd, 'a/clib/setup_cluster_file.py')
    setup_pbs_file(pwd,cname,supervisor_ccri,cmaindir)
    files2cp = ('crun.py','crunfs.py','cdb.py','.license','setup_cluster_file.py','run_setup.pbs')

    ccmd_qsub = 'qsub '+cmaindir+'run_setup.pbs'
    ccmd_python = 'python '+cmaindir+'setup_cluster_file.py'

    if platform == 'linux' or platform == 'linux2':
        for file in files2cp:
            system('sshpass -p '+cpw+' scp '+pwd+'a/clib/'+file+' '+cuser+'@'+caddress+':'+cmaindir+file)
        time.sleep(5)
        system('sshpass -p '+cpw+' ssh -t '+cuser+'@'+caddress+' '+ccmd_qsub)

    elif platform == 'darwin':
        system('sftp '+cuser+'@'+caddress)
        time.sleep(10)
        for file in files2cp:
            system('put '+pwd+'a/clib/'+file+' '+cmaindir+file)
        system('quit\n')
        time.sleep(5)
        cmd = ('ssh '+cuser+'@'+caddress+' nohup '+ccmd_qsub)
        system(cmd)
    elif platform == 'win32':
        open(pwd+'a/clib/psftpcsetup.scr','w').close()
        with open(pwd+'a/clib/psftpcsetup.scr','a') as scr:
            scr.write('cd '+cmaindir+'\n')
            for file in files2cp:
                scr.write('put '+pwd+'a/clib/'+file+' '+cmaindir+file+'\n')
            scr.write('quit\n')
        cmd = ('psftp '+cuser+'@'+caddress+' -pw '+cpw+' -b '+pwd+'/a/clib/psftpcsetup.scr')
        system(cmd)
        time.sleep(5)
        remove(pwd+'a/clib/psftpcsetup.scr')
        open(pwd+'a/clib/crun_qsub.scr','w').close()
        with open(pwd+'a/clib/crun_qsub.scr','a') as scr:
            scr.write(ccmd_python)
        cmd = ('putty.exe -ssh -2 '+cuser+'@'+caddress+' -pw '+cpw+' -m '+pwd+'a/clib/crun_qsub.scr')
        system(cmd)
        remove(pwd+'a/clib/crun_qsub.scr')

    remove(pwd+'a/clib/setup_cluster_file.py')
    remove(pwd+'a/clib/run_setup.pbs')
    print('FINISHED SETTING UP THE CLUSTER')
    

def SETUP_LOCAL(local_maindir):
    print('SETTING UP LOCAL')
    pwd = getcwd().replace(path.sep, '/')+'/'
    system('sudo chmod 777 '+local_maindir) # why sudo here?
    # check if sudo is needed, what happens if user is not in sudo group ==> script failed
    # if sudo fail, run the normal command, for now, not check if command fails
    system('chmod 777 ' + local_maindir)  # why sudo here?
    # notes: default mode of makedir is 777
    if not path.exists(local_maindir+'a/'):
        makedirs(local_maindir+'a/')
    if not path.exists(local_maindir+'a/lib/'):
        makedirs(local_maindir+'a/lib/')
    if not path.exists(local_maindir+'a/res/'):
        makedirs(local_maindir+'a/res/')
    if not path.exists(local_maindir+'a/res/log/'):
        makedirs(local_maindir+'a/res/log/')
    if not path.exists(local_maindir+'a/res/pbs/'):
        makedirs(local_maindir+'a/res/pbs/')
    if not path.exists(local_maindir+'a/res/stats/'):
        makedirs(local_maindir+'a/res/stats/')
    if not path.exists(local_maindir+'a/__init__.py'):
        open(local_maindir+'a/__init__.py','w').close()
        with open(local_maindir+'a/__init__.py','a') as f:
            f.write('__all__ = [\"local_run, local_runfs\"]')
    # force the mode=777 recursive for all sub-folders
    # todo: check the needed of this chmod +R 777 later within the documents
    # just make sure its mode is 777 for all files, in case of fire!
    system('sudo chmod -R 777 ' + local_maindir)
    # in case that the user is not in sudo group, run again
    system('chmod -R 777 ' + local_maindir)
    shutil.copy('a/lib/local_run.py', local_maindir+'a/local_run.py')
    shutil.copy('a/lib/local_runfs.py', local_maindir+'a/local_runfs.py')
    shutil.copy('a/lib/local_db.py', local_maindir+'a/local_db.py')
    clusters = database._get_credentials('all')
    clusters_data = []
    for cred in clusters:
        clusters_data[cred] = []
        clusters_data[cred].append(clusters[cred][0])
        clusters_data[cred].append(clusters[cred][1])
        clusters_data[cred].append(clusters[cred][2])
        clusters_data[cred].append(clusters[cred][4])
    open(local_maindir+'a/lib/clusters_data.py','w').close()
    with open(local_maindir+'a/lib/clusters_data.py', 'a') as f:
        f.write('clusters_data={')
        for cred in clusters_data:
            f.write('\''+cred+'\':[')
            for value in clusters_data[cred]:
                f.write('\''+value+'\',')
            f.write(']')
        f.write('}')
    if not path.exists(local_maindir+'a/lib/__init__.py'):
        open(local_maindir+'a/lib/__init__.py','w').close()
        with open(local_maindir+'a/lib/__init__.py','a') as f:
            f.write('__all__ = []')
    if not path.exists(local_maindir+'a/lib/var.py'):
        open(local_maindir+'a/lib/var.py','w').close()
        with open(local_maindir+'a/lib/var.py','a') as f:
            f.write('#!/bin/python\n')
            f.write('local_maindir=\''+local_maindir+'\'')
    r = system('curl -V')
    if r == 32512:
        system('sudo apt install curl')
        print('y')
    if not path.exists(local_maindir+'freesurfer/'):
        chdir(local_maindir)
        system('curl '+freesurfer_download_address+' -o freesurfer_installation.tar.gz')
        while not path.isfile(local_maindir+'freesurfer_installation.tar.gz'):
            time.sleep(1000)
        system('tar xvf freesurfer_installation.tar.gz')
        remove('freesurfer_installation.tar.gz')
        shutil.move(pwd+'a/clib/.license', local_maindir+'freesurfer/.license')
    if not path.exists(local_maindir+'freesurfer/MCRv80'):
            chdir(local_maindir+'freesurfer')
            system('curl '+matlab_runtime_download_address+' -o matlab_runtime.tar.gz')
            while not path.isfile(local_maindir+'freesurfer/matlab_runtime.tar.gz'):
                time.sleep(30)
            system('tar xvf matlab_runtime.tar.gz')
            remove('matlab_runtime.tar.gz')
    system('sudo apt-get install sshpass')
    system('sudo yum install sshpass')
    chdir(local_maindir)
    system('sudo apt-get install tcsh')
    system('echo \'export FREESURFER_HOME='+local_maindir+'freesurfer\' >> ~/.bashrc')
    system('echo \'source $FREESURFER_HOME/SetUpFreeSurfer.sh\' >> ~/.bashrc')
    if not path.exists(local_maindir+'fsl'):
        system('curl https://fsl.fmrib.ox.ac.uk/fsldownloads/fslinstaller.py -o fslinstaller.py')
        while not path.isfile(local_maindir+'fslinstaller.py'):
                time.sleep(30)
        system('python fslinstaller.py')
        print('')
        remove('fslinstaller.py')
    #system('git clone https://github.com/nipy/dipy.git')
    #chdir(local_maindir+'dipy')
    #system('sudo python setup.py install')
    #system('sudo python setup.py build_ext --inplace')
    #system('echo \'export PYTHONPATH='+local_maindir+'dipy:$PYTHONPATH\' >> ~/.bashrc')
    #system('sudo apt-get install python-dev python-setuptools')
    #print('y')
    #system('sudo apt-get install python-numpy python-scipy')
    #system('sudo apt-get install cython')
    #system('sudo apt install python-pip')
    #print('y')
    #system('sudo pip install nibabel')
    system('sudo apt-get install python-nipype')
    print('y')
    system('pip3 install --user nipy') #http://nipy.org/nipy/users/installation.html
    #system('sudo apt-get install git')
    #print('y')
    #system('sudo apt-get install cmake')
    #print('y')
    #system('git clone git://github.com/stnava/ANTs.git') #http://advants.sourceforge.net/Developer/installation.html
    #system('mkdir '+local_maindir+'antsbin/')
    #chdir(local_maindir+'antsbin')
    #system('cmake ../ANTs')
    #system('cmake')
    #print('c')
    #print('g')
    #print('exit to terminal')
    #system('make -j 4')
    #system('curl https://github.com/stnava/ANTs/tarball/master -o ants.tar.zip')
    print('FINISHED SETTING UP LOCAL')




'''In order to setup Tractoflow on the cluster, singularity is needed;
on cedar singularity does not allow installation
saying there is not sudo
probably Tractflow can be installed and run only on a local with sudo'''

# print('TRYING to setup TractoFlow for DWI analysis')
# from os import system
# def chk(module):
#     system('module spider '+module+' >> tmp')
#     res = open('tmp','r').readlines()
#     remove('tmp')
#     for val in res:
#         if 'module spider '+module in val:
#             line = val.strip('\n')
#             return line.split(' ')[-1]

# module_v = chk_if_module_present('singularity')
# if module_v:
#     chdir(cmaindir)
    # system('module load '+module_v)
    # system('wget http://scil.usherbrooke.ca/containers_list/tractoflow_2.1.0_feb64b9_2020-05-29.img')
    # system('git clone https://github.com/scilus/containers-tractoflow.git')
    # system('singularity build singularity_name.img containers-tractoflow/singularity_tractoflow.def')

