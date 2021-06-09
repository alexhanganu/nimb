#!/bin/python
# 2020.09.10

# uncomment lines: 89, 120, 156

import os
from os import path, system, chdir, environ, rename, listdir
import time
import shutil
import json

environ['TZ'] = 'US/Eastern'
time.tzset()




class RUNProcessing:

    def __init__(self, all_vars, logger):

        #defining working variables
        self.project      = all_vars.params.project
        self.project_vars = all_vars.projects[self.project]
        self.vars_local   = all_vars.location_vars['local']
        vars_processing   = self.vars_local["PROCESSING"]
        self.log          = logger #logging.getLogger(__name__)

        # defining files and paths
        self.NIMB_tmp    = self.vars_local['NIMB_PATHS']['NIMB_tmp']
        self.NIMB_HOME   = self.vars_local["NIMB_PATHS"]["NIMB_HOME"]
        materials_dir_pt = all_vars.projects[self.project]["materials_DIR"][1]
        self.f_running   = os.path.join(self.NIMB_tmp, DEFAULT.f_running_process)
        self.start_fs_processing = False
        self.schedule     = Scheduler(self.vars_local)

        t0           = time.time()
        time_elapsed = 0
        count_run    = 0

        self.log.info('    processing pipeline started')
        self.update_running(1)

        self.log.info('    processing database reading')
        self.DBc = DB(all_vars)
        self.db = self.DBc.get_db()

        self.log.info('    NEW SUBJECTS searching:')    
        self.db = self.DBc.update_db_new_subjects(self.db)

    #     self.DBc.update_db(db, NIMB_tmp)

        # extracting 40 minutes from the maximum time for the batch to run
        # since it is expected that less then 35 minutes will be required for the pipeline to perform all the steps
        # while the batch is running, and start new batch
        max_batch_running = time.strftime('%H:%M:%S',time.localtime(time.mktime(time.strptime(vars_processing["batch_walltime"],"%H:%M:%S")) - 2400))
        _, len_all_running = self.count_timesleep()

        while len_all_running >0 and time.strftime("%H:%M:%S",time.gmtime(time_elapsed)) < max_batch_running:
            count_run += 1
            self.log.info('restarting run, '+str(count_run))
            time_elapsed_strftime = time.strftime("%H:%M",time.gmtime(time_elapsed))
            batch_time_hm = vars_processing["batch_walltime"][:-6]
            self.log.info(f'elapsed time: {time_elapsed_strftime}; max walltime: {batch_time_hm}')
    #         if count_run % 5 == 0:
    #             self.log.info('    NEW SUBJECTS searching:')
    #             self.db = self.DBc.update_db_new_subjects(self.db)
    #             self.DBc.update_db(self.db, NIMB_tmp)
            self.loop_run()

            time_to_sleep, len_all_running = self.count_timesleep()
            next_run_time = str(time.strftime("%H:%M",time.localtime(time.time()+time_to_sleep)))
            self.log.info('\n\nWAITING. \nNext run at: '+next_run_time)

            time_elapsed = time.time() - t0

            time.sleep(time_to_sleep)

            time_elapsed = time.time() - t0
            _, len_all_running = self.count_timesleep()

        if len_all_running == 0:
                self.update_running(0)
                self.log.info('ALL TASKS FINISHED')
                ProjectManager(all_vars).get_stats_fs()
        else:
            self.python_run = self.local_vars["PROCESSING"]["python3_run_cmd"]
            cd_cmd     = f'cd {os.path.join(self.NIMB_HOME, "processing")}'
            cmd        = f'{self.python_run} processing_run.py -project {self.project}'
            self.log.info(f'    Sending new processing batch to scheduler with cd_cmd: {cd_cmd} ')
#         self.schedule.submit_4_processing(cmd, 'nimb_processing','run', cd_cmd)


    def loop_run(self):
        print('    starting the processing loop')
        fs_db = self.get_db("fs")
        ls_subj_in_fs_db = list()
        for ls_bids_ids in fs_db["LONG_DIRS"].values():
            ls_subj_in_fs_db = ls_subj_in_fs_db + ls_bids_ids

        db_key = "PROCESS_FS"
        ls_fs_subjects = list(self.db[db_key].keys())
        ls_2process_with_fs = list()
        for subjid in ls_fs_subjects:
            if self.db[db_key][subjid] == 'local':
                if subjid not in ls_subj_in_fs_db:
                    ls_2process_with_fs.append(subjid)

        # NOT READ, no link
        db_key = "PROCESS_NL"
        ls_nl_subjects = list(self.db[db_key].keys())
        ls_2process_with_nl = list()
        for subjid in ls_nl_subjects:
            if self.db[db_key][subjid] == 'local':
                # MUST change this part because NL and DP don't have a db now
                if subjid not in ls_subj_in_fs_db:
                    ls_2process_with_nl.append(subjid)


        # NOT READ, no link
        db_key = "PROCESS_DP"
        ls_dp_subjects = list(self.db[db_key].keys())
        ls_2process_with_dp = list()
        for subjid in ls_dp_subjects:
            if self.db[db_key][subjid] == 'local':
                # MUST change this part because NL and DP don't have a db now
                if subjid not in ls_subj_in_fs_db:
                    ls_2process_with_dp.append(subjid)

        print(len(ls_subj_in_fs_db))
        print(len(ls_2process_with_fs))

        self.update_fs_processing(ls_2process_with_fs)
        if self.start_fs_processing:
            self.chk_start_processing()
        self.chk_subj_if_processed()


    def get_db(self, app):
        if app == "fs":
            db_app = os.path.join(self.NIMB_tmp, DEFAULT.fs_db_name)
            return load_json(db_app)


    def chk_subj_if_processed(self):
        app = 'fs'
        ls_fs_subjects = list(self.db["PROCESS_FS"].keys())
        d_id_bids_to_fs_proc = dict() # {bids_id : fs_processed_id.zip}
        _dir_fs_processed = self.local_vars["FREESURFER"]["NIMB_PROCESSED_FS"]
        for bids_id in ls_fs_subjects:
            subj_processed = f'{bids_id}.zip'
            if self.db['PROCESS_FS'][bids_id] == 'local':
                if subj_processed in os.path.listdir(_dir_fs_processed):
                    d_id_bids_to_fs_proc[bids_id] = subj_processed
            else:
                remote = self.db['PROCESS_FS'][bids_id]
                print(f'    {bids_id} is on being processed on the remote: {remote}')
        _dir_store = self.project_vars["PROCESSED_FS_DIR"][1]
        for bids_id in d_id_bids_to_fs_proc:
            subj_processed = d_id_bids_to_fs_proc[bids_id]
            src = os.path.join(_dir_fs_processed, subj_processed)
            dst = os.path.join(_dir_store, subj_processed)
            print(f'    moving {subj_processed} from {src} to storage folder: {dst}')
            # shutil.move(src, dst)
            self.update_project_data(bids_id, subj_processed, app)


    def update_project_data(self, bids_id, subj_processed, app):
        '''update f_ids
        '''
        f_ids_name       = self.vars_local["NIMB_PATHS"]['file_ids_processed']
        new_subjects_dir = self.vars_local["NIMB_PATHS"]["NIMB_NEW_SUBJECTS"]
        path_stats_dir   = self.project_vars["STATS_PATHS"]["STATS_HOME"]
        f_ids_abspath    = os.path.join(path_stats_dir, f_ids_name)
        id_all_key = get_keys_processed(app)

        self._ids_all    = load_json(f_ids_abspath)
        if id_all_key not in self._ids_all[bids_id]:
            self._ids_all[bids_id][id_all_key] = ''
        self._ids_all[bids_id][id_all_key] = subj_processed
        print(f'    saving new updated version of f_ids.json at: {f_ids_abspath}')
        save_json(self._ids_all, f_ids_abspath)


    def update_fs_processing(self, ls_2process_with_fs):
        update = False
        if ls_2process_with_fs:
            new_subjects_dir = self.vars_local['NIMB_PATHS']['NIMB_NEW_SUBJECTS']

            f_classif_in_src = os.path.join(new_subjects_dir, DEFAULT.f_nimb_classified)
            f_new_subjects   = os.path.join(self.NIMB_tmp, DEFAULT.f_subjects2proc)

            if os.path.exists(f_classif_in_src):
                classif_subjects = load_json(f_classif_in_src)
                update = True
            if os.path.exists(f_new_subjects):
                new_subjects = load_json(f_new_subjects)
            else:
                new_subjects = dict()
            if update:
                for subjid in ls_2process_with_fs:
                    print(f'    adding subjects {subjid} for fs_new_subjects')
#                    if check_that_all_files_are_accessible(ls_files):
#                        add_to_new_subjects
                    _id, ses = self.DBc.get_id_ses(subjid)
                    print(_id, ses)
                    new_subjects[_id] = {ses: {'anat': {}}}
                    new_subjects[_id][ses]['anat'] = classif_subjects[_id][ses]['anat']
                print(f'    saving file new_subjects at: {f_new_subjects}')
#                save_json(new_subjects, f_new_subjects)
                self.start_fs_processing = True


    def check_that_all_files_are_accessible(self, ls):
        for file in ls:
            if not path.exists(file):
                ls.remove(file)
        return ls


    def chk_start_processing(self):
        f_fs_running = os.path.join(self.NIMB_tmp, f'{DEFAULT.f_running_fs}0')
        if os.path.exists(f_fs_running):
            path_2cd = os.path.join(self.NIMB_HOME, 'processing', 'freesurfer')
            cd_cmd = f"cd {path_2cd}"
            cmd = f'{self.python_run} crun.py'
#                self.schedule.submit_4_processing(cmd, 'nimb','run', cd_cmd,
#                                                activate_fs = False,
#                                                python_load = True)
        else:
            print(f'    file {f_fs_running} is missing')


    def count_timesleep(self):
        time2sleep = 36000 # 600 minutes
        len_running_fs = len(list(self.db['PROCESS_FS'].keys()))
        len_running_nl = len(list(self.db['PROCESS_NL'].keys()))
        len_running_dp = len(list(self.db['PROCESS_DP'].keys()))

        len_all_running = len_running_fs + len_running_nl + len_running_dp
        self.log.info('    running: '+str(len_all_running))
        if len_running_nl > 0:
            time2sleep = 1800 # 30 minutes
        elif len_running_dp > 0:
            time2sleep = 3600 # 60 minutes
        return time2sleep, len_all_running


    def update_running(self, cmd):
        if cmd == 1:
            if path.isfile(f'{self.f_running}0'):
                rename(f'{self.f_running}0', f'{self.f_running}1')
            else:
                open(f'{self.f_running}1', 'w').close()
        else:
            if path.isfile(f'{self.f_running}1'):
                rename(f'{self.f_running}1', f'{self.f_running}0')




class DB:

    def __init__(self, all_vars):
        self.log      = logger #logging.getLogger(__name__)
        self.project  = all_vars.params.project
        vars_nimb     = all_vars.location_vars['local']['NIMB_PATHS']
        self.NIMB_tmp = vars_nimb['NIMB_tmp']
        self.db_f = os.path.join(self.NIMB_tmp, DEFAULT.process_db_name)
        self.ses  = all_vars.location_vars['local']['FREESURFER']["long_name"]


    def get_db(self):
        '''
        PROJECTS  : {'project_name: [subj1, subj2]'}
        PROCESS_FS: {'subj1': 'local', 'subj2': 'remote1', 'subj3': 'remote2'}
        PROCESS_NL: {'subj1': 'local', 'subj2': 'remote1', 'subj3': 'remote2'}
        PROCESS_DP: {'subj1': 'local', 'subj2': 'remote1', 'subj3': 'remote2'}
        PROCESSED : {"cp2storage": [], "error":[]}
        '''
        self.log.info(f"Database file: {self.db_f}")
        if os.path.isfile(self.db_f):
            with open(self.db_f) as db_f_open:
                db = json.load(db_f_open)
        else:
            db = dict()
            db['REGISTRATION'] = {}
            db['PROJECTS'] = {}
            db['PROCESSED'] = {"cp2storage": [], "error":[]}
            apps = ('FS', 'NL', 'DP')
            for app in apps:
                db[f'PROCESS_{app}'] = {}
        return db


    def get_ids(self, all_vars):
        '''extract list of subjects to process
        -> it is expected that f_ids is located in the materials_dir
            and will be copied to the stats folder
        -> it is expected that nimb_classified file is located in the
            NIMB_tmp/nimb_new_subjects folder
        '''
        distrib_hlp      = DistributionHelper(all_vars)
        vars_local       = all_vars.location_vars['local']
        f_ids_name       = vars_local["NIMB_PATHS"]['file_ids_processed']
        new_subjects_dir = vars_local["NIMB_PATHS"]["NIMB_NEW_SUBJECTS"]
        path_stats_dir   = all_vars.projects[self.project]["STATS_PATHS"]["STATS_HOME"]

        f_ids_abspath    = os.path.join(path_stats_dir, f_ids_name)
        f_classif_in_src = os.path.join(new_subjects_dir, DEFAULT.f_nimb_classified)
        self._ids_all         = dict()
        self._ids_classified  = dict()

        if distrib_hlp.get_files_for_stats(path_stats_dir, [f_ids_name,]):
            self._ids_all        = load_json(f_ids_abspath)
        if os.path.exists(f_classif_in_src):
            self._ids_classified = load_json(f_classif_in_src)
        else:
            print(f'    file with nimb classified ids is MISSING in: {new_subjects_dir}')


    def update_db_new_subjects(self, db):
        self.db = db
        if self.project not in db['PROJECTS']:
            self.get_ids(all_vars)
            self.db['PROJECTS'][self.project] = list(self._ids_all.keys())
            self.populate_db()
        else:
            print(f'{self.project} is already registered in the database')
        return self.db


    def populate_db(self):
        for bids_id in self._ids_all:
            if self._ids_all[bids_id][get_keys_processed('src')]:
                self.add_2db(bids_id)


    def get_id_ses(self, bids_id):
        '''extract the _id and the session
        from the provided bids_id
        based on the used defined session abbreviation'''
        _id = bids_id
        if self.ses in bids_id:
            ses = bids_id[bids_id.find(self.ses):]
            _id = bids_id.replace(f'_{ses}','')
        else:
            ses = f'{self.ses}01'
        return _id, ses


    def add_2db(self, bids_id):
        '''populating the database with subjects
        if subjects have the corresponding files for analysis
        '''
        _id, ses = self.get_id_ses(bids_id)
        # print(_id, ses)
        fs_key = get_keys_processed('fs')
        nl_key = get_keys_processed('nilearn')
        dp_key = get_keys_processed('dipy')
        for key in (fs_key, nl_key, dp_key):
            if key not in self._ids_all[bids_id]:
                self._ids_all[bids_id][key] = ''

        # populating
        if not self._ids_all[bids_id][fs_key]:
            if 'anat' in self._ids_classified[_id][ses]:
                if 't1' in self._ids_classified[_id][ses]['anat']:
                    # print('    ready to add to FS processing')
                    self.db['PROCESS_FS'][bids_id] = 'local'
        if not self._ids_all[bids_id][nl_key]:
            if 'anat' in self._ids_classified[_id][ses] and \
                'func' in self._ids_classified[_id][ses]:
                if 't1' in self._ids_classified[_id][ses]['anat']:
                    # print('    ready to add to NILEARN processing')
                    self.db['PROCESS_NL'][bids_id] = 'local'
        if not self._ids_all[bids_id][dp_key]:
            if 'anat' in self._ids_classified[_id][ses] and \
                'dwi' in self._ids_classified[_id][ses]:
                if 't1' in self._ids_classified[_id][ses]['anat']:
                    # print('    ready to add to DIPY processing')
                    self.db['PROCESS_DP'][bids_id] = 'local'
        self.update_db()


    def update_db(self):
        with open(self.db_f, 'w') as jf:
            json.dump(self.db, jf, indent=4)
        system(f'chmod 777 {self.db_f}')




def get_parameters(projects):
    """get parameters for nimb"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-project", required=False,
        default=projects[0],
        choices = projects,
        help="names of projects located in credentials_path.py/nimb/projects.json -> PROJECTS",
    )

    params = parser.parse_args()
    return params




if __name__ == "__main__":


    try:
        from pathlib import Path
    except ImportError as e:
        print('please install pathlib')
        sys.exit(e)
    import argparse
    import sys
    import logging

    top = Path(__file__).resolve().parents[1]
    sys.path.append(str(top))

    from setup.get_vars import Get_Vars
    from distribution.distribution_helper import  DistributionHelper
    from distribution.logger import Log
    from distribution.distribution_definitions import DEFAULT, get_keys_processed
    from distribution.utilities import load_json, save_json, makedir_ifnot_exist
    from distribution.project_helper import  ProjectManager
    from processing import processing_db as proc_db
    from processing.schedule_helper import Scheduler, get_jobs_status
    from stats.db_processing import Table

    project_ids = Get_Vars().get_projects_ids()
    params      = get_parameters(project_ids)
    all_vars    = Get_Vars(params)

    NIMB_tmp    = all_vars.location_vars['local']['NIMB_PATHS']['NIMB_tmp']
    fs_version  = all_vars.location_vars['local']['FREESURFER']['freesurfer_version']
    logger      = Log(NIMB_tmp, fs_version).logger
    RUNProcessing(all_vars, logger)
