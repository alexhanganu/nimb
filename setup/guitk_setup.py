#2020 jan 15

from sys import platform, modules
import os, threading, time, shutil
from os import listdir, system, path, makedirs, getcwd, remove, chdir

from tkinter import Tk, Frame, ttk, Entry, Label, StringVar, filedialog, simpledialog

from distribution import database

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
