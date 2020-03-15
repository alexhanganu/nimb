# this contains the username and password to connect to cluster via SSH
import os
from a.lib import database

cname='all'
clusters = database._get_Table_Data('Clusters','all')
if 'elm' in clusters:
	cname = 'elm'
else:
	cname = 'defaultClusters'


user_name = clusters[cname]['Username']
user_password = clusters[cname]['Password']
#TODO: how acess username password like this clusters[0][0], it is in the exe.pyw

project_folder = clusters[cname]['HOME'] #'/home/hvt/projects/def-hanganua'
cmd_run = " python a/crun.py -submit true" #submit=true
#cmd_run = "sbatch a/run.pbs -submit true" #submit=true
load_python_3 = 'module load python/3.7.4;'
cmd_run_crun_on_cluster = load_python_3 +"cd " + project_folder + "; " + cmd_run
host_name = clusters[cname]['remote_address'] #"beluga.calculquebec.ca"

#
# note: if the paramiko has errors when connecting to beluga, change it to beluga1 or 2,3,4
a_folder = clusters[cname]['App_DIR']#'/home/hvt/projects/def-hanganua/a'
#subjects_folder = '/home/hvt/projects/def-hanganua/subjects'
subjects_folder = clusters[cname]['Subjects_raw_DIR']#'/home/hvt/test'
# cd /home/hvt/projects/def-hanganua; cd python a/crun.py
# print(cmd_run_crun_on_cluster)
