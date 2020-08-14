from sqlite3 import connect, OperationalError
from os import listdir, path, remove
from sys import platform
from credentials_path import credentials_home

'''DATABASE ACTIONS
connecting to DB
if no table - create it
provide column names
'''

def __connect_db__():
    conn = connect(path.join(credentials_home, platform+'.db'), check_same_thread=False)
    try:
        conn.execute('select count(*) from Clusters')
    except OperationalError:
        __create_table__(conn)    
    return conn


def __create_table__(conn):
    for TAB in ('Clusters','Projects','Folders'):
        conn.execute('''create table if not exists {0} {1}'''.format(TAB,__get_table_cols(TAB)))
    conn.commit()


def __get_table_cols(table):
    TABLES = {
        'Clusters':('id', 'Username', 'remote_address', 'HOME', 'SCRATCH', 'App_DIR', 'Subjects_raw_DIR','Processed_SUBJECTS_DIR', 'Password', 'Supervisor_CCRI'),
        'Projects':('id', 'mri_dir', 'results_dir', 'glm_dir', 'file_groups'),
        'Folders':('id', 'folder_type', 'folder_id', 'folder_address'),
        'defaultClusters':('username','remote.com','/home','/scratch','/home/username/nimb','/home/username/subjects','/scratch/username/processed','',''),
        'defaultProjects':('','','','',),
    }
    return TABLES[table]



'''REMOTE/CLUSTER DATA SETTINGS:

setting/changing the data for tables
gettin them
deleting them
'''

def _set_Table_Data(Table, data_requested, _id):
    conn = __connect_db__()
    if conn.execute('''SELECT count(*) from {0} WHERE id = "{1}" '''.format(Table, _id)).fetchone()[0] != 0:
        Table_Data = _get_Table_Data(Table,_id)
        for key in Table_Data[_id]:
            if data_requested[_id][key] != Table_Data[_id][key]:
                conn.execute('''UPDATE {0} SET {1} = "{2}" WHERE id = "{3}" '''.format(Table, key, data_requested[_id][key], _id))
    else:
        data = [_id]
        for key in __get_table_cols(Table)[1:]:
            data.append(data_requested[_id][key])
        question_marks = ", ".join(["?"] * len(data_requested[_id]))
        conn.execute('''INSERT INTO {0} VALUES ({1})'''.format(Table,question_marks), data)
    conn.commit()
    conn.close()


def _get_Table_Data(Table, _id):
    conn = __connect_db__()
    credentials = {}
    if _id == 'all':
        data = conn.execute('''SELECT * FROM {}'''.format(Table)).fetchall()
    else:
        data = conn.execute('SELECT * FROM {0} WHERE id = "{1}" '.format(Table,_id)).fetchall()
    ls_col_names = __get_table_cols(Table)[1:]

    if len(data)>0:
        for cred in data:
            _id = cred[0]
            ls_credentials = cred[1:]
            credentials[_id] = {}
            for col in ls_col_names:
                credentials[_id][col] = ls_credentials[ls_col_names.index(col)]            
    else:
        _id = 'default'+str(Table)
        credentials_default = __get_table_cols(_id)
        credentials[_id] = {}
        for col in ls_col_names:
            credentials[_id][col] = credentials_default[ls_col_names.index(col)]
    conn.close()
    return credentials


def _delete_Table_Data(Table, _id):
    conn = __connect_db__()
    conn.execute('DELETE FROM {0} WHERE id = "{1}" '.format(Table, _id)).fetchall()
    conn.commit()
    conn.close()





# to delete: 

# def __get_table_(conn):
#     conn = __connect_db__()
#     c = conn.cursor()
#     for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'"):
#         table = row
#     return table[0]
# def __get_table_cols(table):
#     if table == 'Clusters':
#         t_cols = ('id', 'Username', 'remote_address', 'HOME', 'SCRATCH', 'App_DIR', 'Subjects_raw_DIR','Processed_SUBJECTS_DIR', 'Password', 'Supervisor_CCRI')
#     elif table == 'Projects':
#         t_cols = ('id', 'mri_dir', 'results_dir', 'glm_dir', 'file_groups')
#     elif table == 'Folders':
#         t_cols = ('folder_type', 'folder_id', 'folder_address')
#     elif table == 'default':
#         t_cols = ('username','remote.com','/home','/scratch','/home/username/nimb','/home/username/subjects','/scratch/username/processed','','')
#     # for row in conn.execute("PRAGMA table_info (Clusters)"):
#     #     print(row)
#     return t_cols
# def __create_table__(conn):
#     for TAB in ('Clusters','Projects','Folders'):
#         conn.execute('''create table if not exists {0} {1}'''.format(TAB,__get_table_cols('Clusters')))
# #        conn.execute('''create table if not exists Projects {0}'''.format(__get_table_cols('Projects')))
# #        conn.execute('''create table if not exists Folders {0}'''.format(__get_table_cols('Folders')))
#     conn.commit()



def _set_credentials(credentials, cname):
    conn = __connect_db__()
    if conn.execute('''SELECT count(*) from Clusters WHERE id = "{0}" '''.format(cname)).fetchone()[0] != 0:
        cred = _get_credentials(cname)
        for key in cred[cname]:
            if credentials[cname][key] != cred[cname][key]:
                conn.execute('''UPDATE Clusters SET {0} = "{1}" WHERE id = "{2}" '''.format(key, credentials[cname][key], cname))
    else:
        data = [cname,]
        for key in __get_table_cols('Clusters')[1:]:
            data.append(credentials[cname][key])
        conn.execute('''INSERT INTO Clusters VALUES (?,?,?,?,?,?,?,?,?,?)''', data)
    conn.commit()
    conn.close()
def _get_credentials(cname):
    conn = __connect_db__()
    credentials = {}
    if cname == 'all':
        data = conn.execute('''SELECT * FROM Clusters''').fetchall()
    else:
        data = conn.execute('SELECT * FROM Clusters WHERE id = "{}" '.format(cname)).fetchall()
    ls_col_names = __get_table_cols('Clusters')[1:]
    if len(data)>0:
        for cred in data:
            _id = cred[0]
            ls_credentials = cred[1:]
            credentials[_id] = {}
            for col in ls_col_names:
                credentials[_id][col] = ls_credentials[ls_col_names.index(col)]
    else:
        _id = 'defaultClusters'
        credentials_default = __get_table_cols(_id)
        credentials[_id] = {}
        for col in ls_col_names:
            credentials[_id][col] = credentials_default[ls_col_names.index(col)]

    conn.close()
    return credentials
def _delete_credentials(cname):
    conn = __connect_db__()
    conn.execute('DELETE FROM Clusters WHERE id = "{}" '.format(cname)).fetchall()
    conn.commit()
    conn.close()


'''FOLDER DATA CHANGES'''
def _set_folder(folder_type, folder_id, folder_address):
    conn = __connect_db__()
    if conn.execute('''SELECT count(*) from Folders WHERE folder_address = "{0}" '''.format(folder_address)).fetchone()[0] != 0:
        if folder_type != conn.execute('''SELECT folder_type from Folders WHERE folder_address = "{0}" '''.format(folder_address)).fetchone()[0]:
            conn.execute('''UPDATE Folders SET folder_type = "{0}" WHERE folder_address = "{1}" '''.format(folder_type, folder_address))
        elif folder_id != conn.execute('''SELECT folder_id from Folders WHERE folder_address = "{0}" '''.format(folder_address)).fetchone()[0]:
            conn.execute('''UPDATE Folders SET folder_id = "{0}" WHERE folder_address = "{1}" '''.format(folder_id, folder_address))
    elif folder_type == 'Main' or folder_type == 'LocalProcessing' and conn.execute('''SELECT count(*) from Folders WHERE folder_type = "{0}" '''.format(folder_type)).fetchone()[0] != 0:
        conn.execute('''UPDATE Folders SET folder_address = "{0}" WHERE folder_type = "{1}" '''.format(folder_address, folder_type))
    else:
        data = [(folder_type, folder_id, folder_address)]
        conn.executemany('''INSERT INTO Folders VALUES (?,?,?)''', data)
    # print(folder_type, folder_id, folder_address)
    conn.commit()
    conn.close()
def _get_folder(folder_type):
    conn = __connect_db__()
    DIRs_INCOMING = {}
    if folder_type == 'Main':
        if conn.execute('''SELECT count(*) from Folders WHERE folder_type = 'Main' ''').fetchone()[0] != 0:
            folder = conn.execute('''SELECT folder_address from Folders WHERE folder_type = 'Main' ''').fetchone()[0]
        else:
            folder = 'not defined'
        return folder
    if folder_type == 'LocalProcessing':
        if conn.execute('''SELECT count(*) from Folders WHERE folder_type = 'LocalProcessing' ''').fetchone()[0] != 0:
            folder = conn.execute('''SELECT folder_address from Folders WHERE folder_type = 'LocalProcessing' ''').fetchone()[0]
        else:
            folder = 'not defined'
        return folder
    else:
        if conn.execute('''SELECT count(*) from Folders WHERE folder_type = "{0}" '''.format(folder_type)).fetchone()[0] != 0:
            for folder in conn.execute('''SELECT * from Folders WHERE folder_type = "{0}" '''.format(folder_type)).fetchall():
                DIRs_INCOMING[folder[1]] = folder[2]
        else:
                DIRs_INCOMING['no project'] = 'dir not set'
    conn.close()
    return DIRs_INCOMING        

def _set_Project_Data(id, mri_dir, results_dir, glm_dir, file_groups):
    conn = __connect_db__()
    if conn.execute('''SELECT count(*) from Projects WHERE id = "{0}" '''.format(id)).fetchone()[0] != 0:
        Project_Data = _get_Project_Data(id)
        if mri_dir != Project_Data[id][0]:
                conn.execute('''UPDATE Projects SET mri_dir = "{0}" WHERE id = "{1}" '''.format(mri_dir, id))
        elif results_dir != Project_Data[id][1]:
                conn.execute('''UPDATE Projects SET results_dir = "{0}" WHERE id = "{1}" '''.format(results_dir, id))
        elif glm_dir != Project_Data[id][2]:
                conn.execute('''UPDATE Projects SET glm_dir = "{0}" WHERE id = "{1}" '''.format(glm_dir, id))
        elif file_groups != Project_Data[id][3]:
                conn.execute('''UPDATE Projects SET file_groups = "{0}" WHERE id = "{1}" '''.format(file_groups, id))
    else:
        data = [id,mri_dir, results_dir, glm_dir, file_groups]
        conn.execute('''INSERT INTO Projects VALUES (?,?,?,?,?)''', data)
    conn.commit()
    conn.close()
def _get_Project_Data(Project):
    conn = __connect_db__()
    Project_Data = {}
    if Project == 'all':
        data = conn.execute('''SELECT * FROM Projects''').fetchall()
    else:
        data = conn.execute('SELECT * FROM Projects WHERE id = "{}" '.format(Project)).fetchall()
    ls_col_names = __get_table_cols('Projects')[1:]

    if len(data)==1:
        Project_Data[data[0][0]] = [data[0][1],data[0][2],data[0][3],data[0][4]]
        return Project_Data
    elif len(data)>1:
        for project in data:
            Project_Data[project[0]] = [project[1],project[2],project[3],project[4]]
			
    else:
        Project_Data['not set'] = ['','','','',]
    conn.close()
    return Project_Data

def _set_Project_Data_d(id, group, var):
    print(id, group, var)
    conn = __connect_db__()
    if group == '':
        conn.execute('''INSERT INTO Projects VALUES (?,?,?,?,?)''', [var, '', '', '', ''])
    else:
        Project_Data = _get_Project_Data_d(id)
        if Project_Data[id][group] != var:
            conn.execute('''UPDATE Projects SET {0} = "{1}" WHERE id = "{2}" '''.format(group, var, id))
    conn.commit()
    conn.close()
def _get_Project_Data_d(Project):
    Project_Data_d = dict()
    Project_Data = _get_Project_Data(Project)
    for project in Project_Data:
        Project_Data_d[project]={}
        Project_Data_d[project]['mri_dir'] = Project_Data[project][0]
        Project_Data_d[project]['results_dir'] = Project_Data[project][1]
        Project_Data_d[project]['glm_dir'] = Project_Data[project][2]
        Project_Data_d[project]['file_groups'] = Project_Data[project][3]
    return Project_Data_d
	
def _delete_Project(Project):
    conn = __connect_db__()
    conn.execute('DELETE FROM Projects WHERE id = "{}" '.format(Project)).fetchall()
    conn.commit()
    conn.close()

def Clear_DIR_incoming():
    print("cleaning")
    if path.isfile(path.join(home,'folder_incoming.py')):
        open(path.join(home,'folder_incoming.py'), 'w').close()


def _get_list_processed_subjects(DIR):
    MainFolder = _get_folder('Main')
    ls = []
    if path.isfile(MainFolder+'logs/processed_subjects_'+DIR+'.txt'):
        with open(MainFolder+'logs/processed_subjects_'+DIR+'.txt', 'r') as f:
            for line in f:
                ls.append(line.strip('\n'))
    else:
        print(MainFolder+'logs/processed_subjects_'+DIR+'.txt is not SETUP yet')
    return ls

def _update_list_processed_subjects(DIR, dir2read):
    Processed_Subjects = {}
    Processed_Subjects[DIR] = []
    MainFolder = _get_folder('Main')
    if path.isfile(MainFolder+'logs/processed_subjects_'+DIR+'.txt'):
        ls = []
        with open(MainFolder+'logs/processed_subjects_'+DIR+'.txt', 'r') as f:
                for line in f:
                    ls.append(line.strip('\n'))
        Processed_Subjects[DIR] = ls[1:]
    Processed_Subjects[DIR].append(dir2read)
    open(MainFolder+'logs/processed_subjects_'+DIR+'.txt','w').close()
    with open(MainFolder+'logs/processed_subjects_'+DIR+'.txt','a') as f:
        f.write(DIR+'\n')
        for subject in Processed_Subjects[DIR]:
            f.write(subject+'\n')        


def create_lsmiss(lsmiss):
    MainFolder = _get_folder('Main')
    for DIR in lsmiss:
        if path.isfile(MainFolder+'logs/miss_'+DIR+'.txt'):
            ls = []	
            with open(MainFolder+'logs/miss_'+DIR+'.txt','r') as f:
                for line in f:
                    ls.append(line.strip('\n'))
            for value in lsmiss[DIR]:
                if value in ls[1:]:
                    lsmiss[DIR].remove(value)
            for value in ls[1:]:
                if value not in lsmiss[DIR]:
                    lsmiss[DIR].append(value)
            lsmiss[DIR] = sorted(lsmiss[DIR])
        open(MainFolder+'logs/miss_'+DIR+'.txt','w').close()
        with open(MainFolder+'logs/miss_'+DIR+'.txt','a') as f:
            f.write(DIR+'\n')
            for subject in lsmiss[DIR]:
                f.write(subject+'\n')


def _get_lsmiss():
    MainFolder = _get_folder('Main')
    lsmiss = {}
    for file in listdir(MainFolder+'logs/'):
        if 'miss_' in file:
            ls = []
            with open(MainFolder+'logs/'+file, 'r') as f:
                for line in f:
                    ls.append(line.strip('\n'))
            lsmiss[ls[0]] = ls[1:]
    print('lsmiss from get_lsmiss is: ',lsmiss)
    return lsmiss

def _update_lsmiss(DIR, dir2read):
    MainFolder = _get_folder('Main')
    lsmiss = {}
    if path.isfile(MainFolder+'logs/miss_'+DIR+'.txt'):
        ls = []
        with open(MainFolder+'logs/miss_'+DIR+'.txt', 'r') as f:
            for line in f:
                ls.append(line.strip('\n'))
        lsmiss[ls[0]] = ls[1:]
        lsmiss[DIR].remove(dir2read)
        if len(lsmiss[DIR])>0:
            open(MainFolder+'logs/miss_'+DIR+'.txt','w').close()
            with open(MainFolder+'logs/miss_'+DIR+'.txt','a') as f:
                f.write(DIR+'\n')
                for subject in lsmiss[DIR]:
                    f.write(subject+'\n')
        else:
            remove(MainFolder+'logs/miss_'+DIR+'.txt')
    else:
        print(MainFolder+'logs/miss_'+DIR+'.txt'+' is not a file')


def update_ls_subj2fs(SUBJECT_ID):
    '''subj2fs file is the list of subjects that need to undergo the FS pipeline processing? '''
    newlssubj = []
    MainFolder = _get_folder('Main')
    if path.isfile(MainFolder+'logs/subj2fs'):
        lssubj = [line.rstrip('\n') for line in open(MainFolder+'logs/subj2fs')]
        for subjid in lssubj:
            if subjid not in newlssubj:
                newlssubj.append(subjid)
    newlssubj.append(SUBJECT_ID)
    open(MainFolder+'logs/subj2fs','w').close()
    with open(MainFolder+'logs/subj2fs','a') as f:
        for subj in newlssubj:
            f.write(subj+'\n')
