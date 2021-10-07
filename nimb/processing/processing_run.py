#!/bin/python
# 2020.09.10

# uncomment lines: 89, 120, 156

import os
from os import path, system, chdir, environ, rename, listdir
import time
import shutil
import json
import argparse
import sys
import logging

environ['TZ'] = 'US/Eastern'
time.tzset()




#         - after each 2 hours check the local/remote NIMB_PROCESSED_FS and NIMB_PROCESSED_FS_ERROR folders. 
#             If not empty: mv (or copy/rm) to the path provided in the ~/nimb/projects.json → project → local 
#                 or remote $PROCESSED_FS_DIR folder
#         - if SOURCE_BIDS_DIR is provided: moves the processed subjects to 
#             corresponding SOURCE_BIDS_DIR/subject/session/processed_fs folder
#     - populating rule:
#         - continue populating until the volume of subjects + volume of estimated processed subjects 
#             (900Mb per subject) is less then 75% of the available disk space
#         - populate local.json - NIMB_PATHS - NIMB_NEW_SUBJECTS based on populating rule
#         - If there are more than one computer ready to perform freesurfer:
#             - send archived subjects to each of them based on the estimated time required to process 
#                 one subject and choose the methods that would deliver the lowest estimated time to process.
#         - once copied to the NIMB_NEW_SUBJECTS:
#             - add subject to distrib-DATABSE → LOCATION → remote_name
#             - move subject in distrib-DATABASE → ACTION notprocessed → copied2process
#     # to_be_process_subject = DiskspaceUtility.get_subject_upto_size(free_space, to_be_process_subject)


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
        self.python_run  = self.vars_local["PROCESSING"]["python3_run_cmd"]
        self.schedule    = Scheduler(self.vars_local)

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


        self.DBc.update_db(self.db)

        # extracting 40 minutes from the maximum time for the batch to run
        # since it is expected that less then 35 minutes will be required for the pipeline to perform all the steps
        # while the batch is running, and start new batch
        time_batchwalltime = time.strptime(vars_processing["batch_walltime"],"%H:%M:%S")
        time_extracted = time.mktime(time_batchwalltime) - 2400
        max_batch_running = time.strftime('%H:%M:%S',time.localtime(time_extracted))
        _, len_all_running = self.count_timesleep()
        print(max_batch_running, len_all_running)

        while len_all_running >0 and time.strftime("%H:%M:%S",time.gmtime(time_elapsed)) < max_batch_running:
            count_run += 1
            self.log.info('restarting run, '+str(count_run))
            time_elapsed_strftime = time.strftime("%H:%M",time.gmtime(time_elapsed))
            batch_time_hm = vars_processing["batch_walltime"][:-6]
            self.log.info(f'elapsed time: {time_elapsed_strftime}; max walltime: {batch_time_hm}')
    #         if count_run % 5 == 0:
    #             self.log.info('    NEW SUBJECTS searching:')
    #             self.db = self.DBc.update_db_new_subjects(self.db)
    #             self.DBc.update_db(self.db)
            # self.loop_run()

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
            cd_cmd     = f'cd {os.path.join(self.NIMB_HOME, "processing")}'
            cmd        = f'{self.python_run} processing_run.py -project {self.project}'
            self.log.info(f'    Sending new processing batch to scheduler with cd_cmd: {cd_cmd} ')
#         self.schedule.submit_4_processing(cmd, 'nimb_processing','run', cd_cmd)


    def loop_run(self):
        self.log.info('    starting the processing loop')
        fs_db = load_json(os.path.join(self.NIMB_tmp, DEFAULT.fs_db_name))
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

        self.log.info(len(ls_subj_in_fs_db))
        self.log.info(len(ls_2process_with_fs))

        self.update_fs_processing(ls_2process_with_fs)
        if self.start_fs_processing:
            self.chk_start_processing()
        self.chk_subj_if_processed()


    def chk_subj_if_processed(self):
        app = 'fs'
        ls_fs_subjects = list(self.db["PROCESS_FS"].keys())
        d_id_bids_to_fs_proc = dict() # {bids_id : fs_processed_id.zip}
        _dir_fs_processed = self.vars_local["NIMB_PATHS"]["NIMB_PROCESSED_FS"]
        for bids_id in ls_fs_subjects:
            subj_processed = f'{bids_id}.zip'
            if self.db['PROCESS_FS'][bids_id] == 'local':
                if subj_processed in os.listdir(_dir_fs_processed):
                    d_id_bids_to_fs_proc[bids_id] = subj_processed
            else:
                remote = self.db['PROCESS_FS'][bids_id]
                self.log.info(f'    {bids_id} is on being processed on the remote: {remote}')
        _dir_store = self.project_vars["PROCESSED_FS_DIR"][1]
        for bids_id in d_id_bids_to_fs_proc:
            subj_processed = d_id_bids_to_fs_proc[bids_id]
            src = os.path.join(_dir_fs_processed, subj_processed)
            dst = os.path.join(_dir_store, subj_processed)
            self.log.info(f'    moving {subj_processed} from {src} to storage folder: {dst}')
            # shutil.move(src, dst)
            self.db = self.DBc.rm_from_db(bids_id, app, self.db)
            self.update_project_data(bids_id, subj_processed, app)


    def update_project_data(self, bids_id, subj_processed, app):
        '''update f_ids
        '''
        f_ids_name       = self.vars_local["NIMB_PATHS"]['file_ids_processed']
        new_subjects_dir = self.vars_local["NIMB_PATHS"]["NIMB_NEW_SUBJECTS"]
        path_stats_dir   = self.project_vars["STATS_PATHS"]["STATS_HOME"]
        f_ids_abspath    = os.path.join(path_stats_dir, f_ids_name)
        id_all_key       = DEFAULT.apps_keys[app]

        self._ids_all    = load_json(f_ids_abspath)
        if id_all_key not in self._ids_all[bids_id]:
            self._ids_all[bids_id][id_all_key] = ''
        self._ids_all[bids_id][id_all_key] = subj_processed
        self.log.info(f'    saving new updated version of f_ids.json at: {f_ids_abspath}')
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
                    self.log.info(f'    adding subject {subjid} for fs_new_subjects')
#                    if check_that_all_files_are_accessible(ls_files):
#                        add_to_new_subjects
                    _id, ses = self.DBc.get_id_ses(subjid)
                    self.log.info(_id, ses)
                    new_subjects[subjid] = classif_subjects[_id][ses]

                    # changing the structure of f_ids to subject id, not bids_id
                    # new_subjects[_id] = {ses: {'anat': {}}}
                    # new_subjects[_id][ses]['anat'] = classif_subjects[_id][ses]['anat']
                self.log.info(f'    saving file new_subjects at: {f_new_subjects}')
                save_json(new_subjects, f_new_subjects)
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
            self.log.info(f'    file {f_fs_running} is missing')


    def count_timesleep(self):
        time2sleep = 36000 # 600 minutes
        len_all_running = 0
        for app in DEFAULT.apps_per_type.values():
            len_app_running = len(list(self.db[f'PROCESS_{app}'].keys()))
            len_all_running = len_all_running + len_app_running
        self.log.info('    running: '+str(len_all_running))
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
        try:
            self.log      = logger #logging.getLogger(__name__)
        except Exception as e:
            self.log      = logging.getLogger(__name__)
        self.project      = all_vars.params.project
        self.project_vars = all_vars.projects[self.project]
        vars_nimb         = all_vars.location_vars['local']['NIMB_PATHS']
        self.NIMB_tmp     = vars_nimb['NIMB_tmp']
        self.db_f         = os.path.join(self.NIMB_tmp, DEFAULT.process_db_name)
        self.apps         = DEFAULT.apps_per_type.values()
        self.srcdata_dir  = self.project_vars["SOURCE_SUBJECTS_DIR"][1]
        self.distrib_hlp  = DistributionHelper(all_vars)
        self.dcm2bids     = DCM2BIDS_helper(self.project_vars,
                                        self.project,
                                        DICOM_DIR = self.srcdata_dir,
                                        tmp_dir = self.NIMB_tmp)
        self.ses      = all_vars.location_vars['local']['FREESURFER']["long_name"]
        # self.db   = self.get_db()


    def get_db(self):
        '''
        Create database for processing
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
            for app in self.apps:
                db[f'PROCESS_{app}'] = {}
        return db


    def update_db_new_subjects(self, db):
        '''
        populating the processing database with ids
        from the file DEFAULT.f_subjects2process
        '''
        self.db = db
        print(self.db)

        self._ids2process  = dict()
        f_subjects2proc = os.path.join(self.NIMB_tmp, DEFAULT.f_subjects2proc)
        if os.path.exists(f_subjects2proc):
            self._ids2process = load_json(f_subjects2proc)
        else:
            self.log.info(f'    file with with subjects to process is MISSING in: {self.NIMB_tmp}')

        '''populating the database with subjects
        if subjects have the corresponding files for analysis
        '''
        if self.project not in db['PROJECTS']:
            self.db['PROJECTS'][self.project] = list()
        for _id_bids in self._ids2process:
            if _id_bids not in self.db["PROJECTS"][self.project]:
                self.db['PROJECTS'][self.project].append(_id_bids)
                if 'anat' in self._ids2process[_id_bids]:
                    if 't1' in self._ids2process[_id_bids]['anat']:
                        self.db[f'PROCESS_{DEFAULT.apps_per_type["anat"]}'][_id_bids] = 'local'
                        if 'func' in self._ids2process[_id_bids]:
                            self.db[f'PROCESS_{DEFAULT.apps_per_type["func"]}'][_id_bids] = 'local'
                        if 'dwi' in self._ids2process[_id_bids]:
                            self.db[f'PROCESS_{DEFAULT.apps_per_type["dwi"]}'][_id_bids] = 'local'
                self.update_db(db)
        else:
            self.log.info(f'{self.project} is already registered in the database')
        return self.db


    def rm_from_db(self, bids_id, app, db):
        self.db = db
        rm = True
        update = False
        if app == "fs":
            if bids_id in db['PROCESS_FS']:
                db['PROCESS_FS'].pop(bids_id, None)
                update = True
            else:
                self.log.info(f'    {bids_id} not in db PROCESS_FS')
        for app in self.apps:
            if bids_id in db[f'PROCESS_{app}']:
                rm = False
                self.log.info(f'    {bids_id} is present in PROCESS_{app}')
                break
        if rm:
            if bids_id in db['PROJECTS'][self.project]:
                db['PROJECTS'][self.project].pop(bids_id, None)
                update = True
            else:
                self.log.info(f'    {bids_id} not in db PROJECTS')

        if update:
            self.update_db(db)
        return self.db


    def update_db(self, db):
        with open(self.db_f, 'w') as jf:
            json.dump(db, jf, indent=4)
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

    top = Path(__file__).resolve().parents[1]
    sys.path.append(str(top))

    from setup.get_vars import Get_Vars
    from distribution.distribution_helper import  DistributionHelper
    from distribution.logger import Log
    from distribution.distribution_definitions import DEFAULT
    from distribution.utilities import load_json, save_json, makedir_ifnot_exist
    from distribution.project_helper import  ProjectManager
    from classification.dcm2bids_helper import DCM2BIDS_helper 
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
