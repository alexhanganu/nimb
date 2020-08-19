# 2020-08-13
# works only with python 3

from distribution import database
from tkinter import Tk, ttk, Menu, N, W, E, S, StringVar, HORIZONTAL
from sys import platform
from setup.get_vars import Get_Vars
from distribution.distribution_helper import DistributionHelper

root = Tk()
root.title("NIMB")

mainframe = ttk.Frame(root, padding="3 3 12 12")

mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

label = ttk.Label
button = ttk.Button


menubar = Menu(root)
filemenu = Menu(menubar, tearoff=0)
menubar.add_cascade(label='actions', menu=filemenu)
# filemenu.add_command(label='stop all active tasks',
                     # command=lambda: StopAllActiveTasks())
root.config(menu=menubar)


def set_Project_Data(Project):
    from setup.guitk_setup import SetProjectData
    SetProjectData(Project)

def setupcredentials():
    from setup.guitk_setup import setupcredentials
    if setupcredentials():
        clusters = database._get_Table_Data("Clusters", "all")
        # ccredentials_txt.set(clusters[0][1]+'@'+clusters[0][2])


getvars = Get_Vars()
projects = getvars.projects
locations = getvars.location_vars
distribution = DistributionHelper(projects, locations)
distribution.ready()

row = 0
for Project in projects['PROJECTS']:
        col = 0
        button(mainframe, text=Project, command=lambda: set_Project_Data(
            Project)).grid(row=row, column=col)
        col += 1
        button(mainframe, text="do processing", command=lambda: distribution.run(
            Project)).grid(row=row, column=col)
        col += 1

        button(mainframe, text="copy subjects to cluster",
               command=lambda: distribution.run_copy_subject_to_cluster(Project)).grid(row=row, column=col)
        col += 1
        # button(mainframe, text="Check new MRI all data", command=lambda: distribution.chkmri(Project)).grid(column=5, row=row, columnspan=2, sticky=W)
        
        row += 1

ttk.Separator(mainframe, orient=HORIZONTAL).grid(
    row=row, column=0, columnspan=7, sticky='ew')
row += 1


for location in projects['LOCATION']:
    button(mainframe, text=location, command=setupcredentials).grid(
        row=row, column=0, sticky=W)
    row += 1

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)

root.mainloop()
