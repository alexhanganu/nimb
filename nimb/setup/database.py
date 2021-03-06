from sqlite3 import connect, OperationalError
from os import listdir, path, remove
from sys import platform

'''DATABASE ACTIONS
connecting to DB
if no table - create it
provide column names
'''
from setup.get_credentials_home import _get_credentials_home

TABLES = {
        'remotes':('id', 'username', 'host', 'password'),
        }

def __connect_db__():
    conn = connect(path.join(_get_credentials_home(), platform+'.db'), check_same_thread=False)
    try:
        conn.execute('select count(*) from Clusters')
    except OperationalError:
        __create_table__(conn)
    return conn


def __create_table__(conn):
    for TAB in TABLES:
        conn.execute('''create table if not exists {0} {1}'''.format(TAB, TABLES[TAB]))
    conn.commit()


def _set_Table_Data(Table, data_requested, _id):
    conn = __connect_db__()
    if conn.execute('''SELECT count(*) from {0} WHERE id = "{1}" '''.format(Table, _id)).fetchone()[0] != 0:
        Table_Data = _get_Table_Data(Table,_id)
        for key in Table_Data[_id]:
            if data_requested[_id][key] != Table_Data[_id][key]:
                conn.execute('''UPDATE {0} SET {1} = "{2}" WHERE id = "{3}" '''.format(Table, key, data_requested[_id][key], _id))
    else:
        data = [_id]
        for key in data_requested[_id]:
            data.append(data_requested[_id][key])
        question_marks = ", ".join(["?"] * len(data))
        conn.execute('''INSERT INTO {0} VALUES ({1})'''.format(Table, question_marks), data)
        _set_Location_json(Table, data_requested, _id)
    conn.commit()
    conn.close()


def _get_Table_Data(Table, _id):
    conn = __connect_db__()
    table_data = {}
    if _id == 'all':
        data = conn.execute('''SELECT * FROM {}'''.format(Table)).fetchall()
    else:
        data = conn.execute('SELECT * FROM {0} WHERE id = "{1}" '.format(Table, _id)).fetchall()
    ls_col_names = TABLES[Table][1:]

    if len(data)>0:
        for param in data:
            _id = param[0]
            ls_params = param[1:]
            table_data[_id] = {}
            for col in ls_col_names:
                table_data[_id][col] = ls_params[ls_col_names.index(col)]
    else:
        print('parameters for {} are missing'.format(_id))
        _id = 'default'
        table_data[_id] = {}
        for col in ls_col_names:
            table_data[_id][col] = ''
    conn.close()
    return table_data

def _delete_Table_Data(Table, _id):
    conn = __connect_db__()
    conn.execute('DELETE FROM {0} WHERE id = "{1}" '.format(Table, _id)).fetchall()
    conn.commit()
    conn.close()

def _set_Location_json(Table, data_requested, _id):
    if Table == 'remotes':
        from setup.get_vars import SetLocation
        SetLocation(data_requested, _id)
