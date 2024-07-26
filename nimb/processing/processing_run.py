#!/bin/python
# 2020.09.10

# uncomment lines:
# 93 (searching new subjects)
# 118 (resending processin_run to scheduler
# 185 (moving subject to destination)
# initiating run of processing app: 264 line

import os
from os import path, system, chdir, environ, rename, listdir
import time
import shutil
import json
import argparse
import sys

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
        self.project       = all_vars.params.project
        self.project_vars  = all_vars.projects[self.project]
        self.vars_local    = all_vars.location_vars['local']
        vars_processing    = self.vars_local["PROCESSING"]

        # defining files and paths
        self.NIMB_tmp      = self.vars_local['NIMB_PATHS']['NIMB_tmp']
        self.NIMB_HOME     = self.vars_local["NIMB_PATHS"]["NIMB_HOME"]
        materials_dir_pt   = all_vars.projects[self.project]["materials_DIR"][1]
        self.f_running     = os.path.join(self.NIMB_tmp, DEFAULT.f_running_process)
        self.python_run    = self.vars_local["PROCESSING"]["python3_run_cmd"]

        self.log           = logger
        self.apps          = list(DEFAULT.app_files.keys())
        self.vars_apps_populate()
        self.schedule      = Scheduler(self.vars_local)

        t0           = time.time()
        time_elapsed = 0
        count_run    = 0

        self.log.info('    processing pipeline started')
        self.update_running(1)

        self.log.info('    processing database reading')
        self.DBc = DB(all_vars, logger)
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

        while len_all_running >0 and time.strftime("%H:%M:%S",time.gmtime(time_elapsed)) < max_batch_running:
            count_run += 1
            self.log.info('starting run, '+str(count_run))
            time_elapsed_strftime = time.strftime("%H:%M",time.gmtime(time_elapsed))
            batch_time_hm = vars_processing["batch_walltime"][:-6]
            self.log.info(f'elapsed time: {time_elapsed_strftime}; max walltime: {batch_time_hm}')
    #         if count_run % 5 == 0:
    #             self.log.info('    NEW SUBJECTS searching:')
    #             self.db = self.DBc.update_db_new_subjects(self.db)
    #             self.DBc.update_db(self.db)
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
            cd_cmd     = f'cd {os.path.join(self.NIMB_HOME, "processing")}'
            cmd        = f'{self.python_run} processing_run.py -project {self.project}'
            self.log.info(f'    Sending new processing batch to scheduler with cd_cmd: {cd_cmd} ')
#         self.schedule.submit_4_processing(cmd, 'nimb_processing','run', cd_cmd)

    def vars_apps_populate(self):
        self.vars_apps = dict()
        for app in self.apps:
            self.vars_apps[app] = self.vars_local[app.upper()]
            app_ver = self.vars_local[app.upper()]['version']
            self.log.info(f"{app} version is: {app_ver}")
            if app == "freesurfer":
                app_home = self.vars_local[app.upper()][f'{app.upper()}_HOME']
                process_order = ["registration"] + FSProcesses(app_home).process_order()
                self.vars_apps[app]["process_order"] = process_order
            if app == "nilearn":
                self.vars_apps[app]["process_order"] = ['connectivity',]
            if app == "dipy":
                self.vars_apps[app]["process_order"] = ['connectivity',]


    def get_ids_per_app(self, app):
        _ids_in_app_db = list()
        print("app is: ", app)
        self.app_db = AppDBManage(self.vars_local, app, DEFAULT, atlas_definitions)
        db_per_app = self.app_db.get_db(app, self.vars_apps[app])
        for ls_bids_ids in db_per_app[app]["LONG_DIRS"].values():
            _ids_in_app_db = _ids_in_app_db + ls_bids_ids
        self.log.info(f"there are: {len(_ids_in_app_db)} participants being processed with {app}")
        return _ids_in_app_db


    def loop_run(self):
        self.log.info('    starting the processing loop')
        self.start_app = False
        for app in self.apps:
            app_abbrev = DEFAULT.app_files[app]["name_abbrev"]
            db_proc_app_key = f'PROCESS_{app_abbrev}'
            _ids_in_app_db     = self.get_ids_per_app(app)
            _ids_2proc_onlocal = list()
            for _id in list(self.db[db_proc_app_key].keys()):
                if self.db[db_proc_app_key][_id] == 'local':
                    if _id not in _ids_in_app_db:
                        _ids_2proc_onlocal.append(_id)
            self.update_db_app(app, _ids_2proc_onlocal)
            self.chk_start_processing_app(app)
        # self.chk_subj_if_processed(app)



    def chk_subj_if_processed(self, app):
        subjects_ls = list(self.db[f'PROCESS_{app}'].keys())
        _id_bids_2app_proc_d = dict() # {bids_id : app_processed_id.zip}
        dir_processed_nimb = DEFAULT.app_files[app]["dir_nimb_proc"]
        _dir_processed_nimb_app = self.vars_local["NIMB_PATHS"][dir_processed_nimb]
        dir_processed_store = DEFAULT.app_files[app]["dir_store_proc"]
        _dir_store = self.project_vars[dir_processed_store][1]
        for bids_id in subjects_ls:
            subj_processed = f'{bids_id}.zip'
            if self.db[f'PROCESS_{app}'][bids_id] == 'local':
                if subj_processed in os.listdir(_dir_processed_nimb_app):
                    _id_bids_2app_proc_d[bids_id] = subj_processed
            else:
                remote = self.db[f'PROCESS_{app}'][bids_id]
                self.log.info(f'    {bids_id} is on being processed on the remote: {remote}')
        for bids_id in _id_bids_2app_proc_d:
            subj_processed = _id_bids_2app_proc_d[bids_id]
            src = os.path.join(_dir_processed_nimb_app, subj_processed)
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


    def update_db_app(self, app, _ids_2proc_onlocal):
        self.log.info(f"there are: {len(_ids_2proc_onlocal)} participants that must be processed with {app} on local")
        f_new_subjects_app = os.path.join(self.NIMB_tmp, DEFAULT.app_files[app]["new_subjects"])

        update = False
        if _ids_2proc_onlocal:
            _ids2process = dict()
            f_subjects2proc = os.path.join(self.NIMB_tmp, f_new_subjects_app)
            if os.path.exists(f_subjects2proc):
                _ids2process = load_json(f_subjects2proc)
            else:
                self.log.info(f'    file with with subjects to process {f_subjects2proc} is MISSING in: {self.NIMB_tmp}')

            if _ids2process:
                # print(_ids2process)
                new_subjects = dict()
                for _id_bids in _ids_2proc_onlocal:
                    if _id_bids in _ids2process:
                        files_per_id = _ids2process[_id_bids]
                        if self.chk_if_files_exist(files_per_id["anat"]["t1"]):
                            ok2add = True
                            if app == "nilearn":
                                if "func" in files_per_id:
                                    if not self.chk_if_files_exist(files_per_id["func"]["bold"]):
                                        ok2add = False
                            elif app == "dipy":
                                if "dwi" in files_per_id:
                                    if not self.chk_if_files_exist(files_per_id["dwi"]["dwi"]):
                                        ok2add = False
                            if ok2add:
                                new_subjects[_id_bids] = _ids2process[_id_bids]
                            else:
                                self.log.info(f"!!!ERR: files are missing for app: {app}")
                    else:
                        self.log.info(f'    ERR!!: {_id_bids} is missing from file: {f_subjects2proc}')
                save_json(new_subjects, f_new_subjects_app)
                self.start_app = True


    def chk_if_files_exist(self, ls):
        ok_files = False
        for file in ls:
            if not path.exists(file):
                ls.remove(file)
        if ls:
            ok_files = True
        return ok_files


    def chk_start_processing_app(self, app):
        self.log.info("starting processing part")
        running_f = os.path.join(self.NIMB_tmp, f'{DEFAULT.app_files[app]["running"]}0')
        if not os.path.exists(running_f):
            open(running_f, "w").close()

        if self.start_app:
            path_2cd = os.path.join(self.NIMB_HOME, 'processing', str(app))
            cd_cmd   = f"cd {path_2cd}"
            cmd      = f'{self.python_run} {DEFAULT.app_files[app]["run_file"]}'
            batch_file_name = f"nimb_{app}"
            self.log.info(f'initiating new run of {app} processing')
            self.schedule.submit_4_processing(cmd, batch_file_name,'run', cd_cmd,
                                            activate_fs = False,
                                            python_load = True)
            self.start_app = False


    def count_timesleep(self):
        time2sleep = 36000 # 600 minutes
        len_all_running = 0
        for app in self.apps:
            app_abbrev = DEFAULT.app_files[app]["name_abbrev"]
            len_app_running = len(list(self.db[f'PROCESS_{app_abbrev}'].keys()))
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

    def __init__(self, all_vars, logger):
        self.log          = logger
        self.project      = all_vars.params.project
        self.project_vars = all_vars.projects[self.project]
        vars_nimb         = all_vars.location_vars['local']['NIMB_PATHS']
        self.NIMB_tmp     = vars_nimb['NIMB_tmp']
        self.db_f         = os.path.join(self.NIMB_tmp, DEFAULT.process_db_name)
        self.apps         = list(DEFAULT.app_files.keys())
        self.srcdata_dir  = self.project_vars["SOURCE_SUBJECTS_DIR"][1]
        self.distrib_hlp  = DistributionHelper(all_vars)
        self.dcm2bids     = DCM2BIDS_helper(self.project_vars,
                                        self.project,
                                        DICOM_DIR = self.srcdata_dir,
                                        tmp_dir = self.NIMB_tmp)
        self.ses      = all_vars.location_vars['local']['NIMB_PATHS']["long_abbrevs"]
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
                db[f'PROCESS_{DEFAULT.app_files[app]["name_abbrev"]}'] = {}
        return db


    def update_db_new_subjects(self, db):
        '''
        populating the processing database with ids
        from the file DEFAULT.f_subjects2process
        '''
        self.db = db

        '''populating the database with subjects
        if subjects have the corresponding files for analysis
        '''
        if self.project not in db['PROJECTS']:
            self.db['PROJECTS'][self.project] = list()

        for app in self.apps:
            app_abbrev = DEFAULT.app_files[app]["name_abbrev"]
            f_subjects2proc = os.path.join(self.NIMB_tmp, DEFAULT.app_files[app]["new_subjects"])
            if os.path.exists(f_subjects2proc):
                content = load_json(f_subjects2proc)
                for _id_bids in content:
                    if _id_bids not in self.db["PROJECTS"][self.project]:
                        self.db['PROJECTS'][self.project].append(_id_bids)
                        self.db[f'PROCESS_{app_abbrev}'][_id_bids] = 'local'
                        self.update_db(db)
            else:
                self.log.info(f'    no new subjects to process: {DEFAULT.app_files[app]["new_subjects"]}')
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
            app_abbrev = DEFAULT.app_files[app]["name_abbrev"]
            if bids_id in db[f'PROCESS_{app_abbrev}']:
                rm = False
                self.log.info(f'    {bids_id} is present in PROCESS_{app_abbrev}')
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

    parser.add_argument(
    "-test", required=False,
    action = 'store_true',
    help   = "when used, nimb will run only 2 participants",
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
    project_ids = Get_Vars().get_projects_ids()
    params      = get_parameters(project_ids)
    all_vars    = Get_Vars(params)

    from processing.app_db import AppDBManage
    from processing.schedule_helper import Scheduler
    from processing.atlases import atlas_definitions
    from processing.freesurfer.fs_definitions import FSProcesses
    from distribution.distribution_helper import  DistributionHelper
    from distribution.distribution_definitions import DEFAULT
    from distribution.utilities import load_json, save_json
    from distribution.project_helper import  ProjectManager
    from classification.dcm2bids_helper import DCM2BIDS_helper
    # try:
    #     from distribution.logger import Log
    #     logger = Log(all_vars.location_vars['local']['NIMB_PATHS']['NIMB_tmp']).logger
    # except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    # logging.basicConfig(format='%(asctime)s| %(message)s')
    logging.basicConfig(format='{asctime} : {message}')
    logger.setLevel(logging.INFO)

    RUNProcessing(all_vars, logger)

