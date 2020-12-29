# -*- coding: utf-8 -*-

"""nimb module"""

import argparse
from os import path
import sys
import logging
from setup.get_vars import Get_Vars
from distribution.distribution_helper import DistributionHelper
from distribution.distribution_ready import DistributionReady
from distribution.utilities import ErrorMessages
from distribution.logger import Log
from processing.schedule_helper import Scheduler
from setup.version import __version__


class NIMB(object):
    """ Object to initiate pipeline
    Args:
        params  : from parameters defined by user, process, project
        projects: parameters of all projects from credentials_path/projects.json
        projects: parameters of all projects
        all_vars: all variables of local.json and all remotes.json as defiend in credentials_path/projects.json -> LOCATION
    """

    def __init__(
        self,
        params,
        projects,
        all_vars
    ):


        self.process      = params.process
        self.project      = params.project
        self.projects     = projects
        self.project_vars = projects[self.project]
        self.all_vars     = all_vars
        self.locations    = all_vars.location_vars
        self.stats_vars   = all_vars.stats_vars
        self.vars_local   = self.locations['local']
        self.NIMB_HOME    = self.vars_local['NIMB_PATHS']['NIMB_HOME']
        self.NIMB_tmp     = self.vars_local['NIMB_PATHS']['NIMB_tmp']
        self.fix_spaces   = params.fix_spaces
        self.logger       = Log(self.NIMB_tmp, self.vars_local['FREESURFER']['freesurfer_version']).logger
        self.schedule     = Scheduler(self.vars_local)
        if self.process == 'fs-get-stats' or self.process == 'fs-glm' or self.process == 'run-stats':
            from setup.get_vars import SetProject
            self.stats_vars = SetProject(self.NIMB_tmp, self.stats_vars, self.project).stats

    def run(self):
        """Run nimb"""

        if self.process == 'ready':
            DistributionReady(self.all_vars, self.project_vars, self.logger).check_ready()

        if self.process == 'run':
            from distribution.project_helper import ProjectManager
            ProjectManager(self.project_vars).run()

        if self.process == 'check-new':
            self.logger.info('checking for new subject to be processed')
            DistributionHelper(self.all_vars, self.project_vars, self.logger).check_new()

        if self.process == 'classify':
            self.logger.info('checking if ready to classify')
            if not DistributionReady(self.all_vars, self.project_vars, self.logger).classify_ready():
                ErrorMessages.error_classify()
                sys.exit()
            else:
                SUBJ_2Classify = DistributionHelper(self.all_vars, self.project_vars, self.logger).get_subj_2classify()
                if SUBJ_2Classify:
                    from classification.classify_bids import MakeBIDS_subj2process
                    return MakeBIDS_subj2process(SUBJ_2Classify,
                                         self.NIMB_tmp,
                                         self.fix_spaces,
                                         self.vars_local['FREESURFER']['multiple_T1_entries'],
                                         self.vars_local['FREESURFER']['flair_t2_add']).run()

        if self.process == 'classify_dcm2bids':
            self.logger.info("initiating dcm2bids transformation for project: {}".format(self.project))
            from classification.dcm2bids_helper import DCM2BIDS_helper
            return DCM2BIDS_helper(self.project_vars, self.project).run()

        if self.process == 'freesurfer':
            if not DistributionReady(self.all_vars, self.project_vars, self.logger).fs_ready():
                self.logger.info("FreeSurfer is not ready or freesurfer_install is set to 0. Please check the configuration files.")
                sys.exit()
            else:
                cd_cmd = 'cd {}'.format(path.join(self.NIMB_HOME, 'processing', 'freesurfer'))
                cmd = '{} crun.py'.format(self.vars_local['PROCESSING']["python3_run_cmd"])
                self.schedule.submit_4_processing(cmd, 'nimb','run', cd_cmd,
                                                activate_fs = False,
                                                python_load = True)

        if self.process == 'nilearn':
            if not DistributionReady(self.all_vars, self.project_vars, self.logger).nilearn_ready():
                self.logger.info("Nilearn is not ready.")
                sys.exit()
            else:
                cmd = '{} crun.py'.format(self.vars_local['PROCESSING']["python3_run_cmd"])
                cd_cmd = 'cd '+path.join(self.NIMB_HOME, 'processing', 'nilearn')
                self.schedule.submit_4_processing(cmd, 'nilearn','run', cd_cmd,
                                                activate_fs = False,
                                                python_load = True)

        if self.process == 'dipy':
            if not DistributionReady(self.all_vars, self.project_vars, self.logger).dipy_ready():
                self.logger.info("Dipy is not ready.")
                sys.exit()
            else:
                cmd = '{} crun.py'.format(self.vars_local['PROCESSING']["python3_run_cmd"])
                cd_cmd = 'cd '+path.join(self.NIMB_HOME, 'processing', 'dipy')
                self.schedule.submit_4_processing(cmd, 'dipy','run', cd_cmd,
                                                activate_fs = False,
                                                python_load = True)

        if self.process == 'fs-get-stats':
            if not DistributionReady(self.all_vars, self.project_vars, self.logger).nimb_stats_ready():
                self.logger.info("NIMB is not ready to extract the FreeSurfer statistics per user. Please check the configuration files.")
                sys.exit()
            else:
                helper = DistributionHelper(self.all_vars, self.project_vars, self.logger)
                PROCESSED_FS_DIR = helper.get_local_remote_dir(self.project_vars["PROCESSED_FS_DIR"])
                from stats.fs_stats2table import FSStats2Table
                FSStats2Table(self.stats_vars["STATS_PATHS"]["STATS_HOME"],
                              PROCESSED_FS_DIR, self.NIMB_tmp,
                              data_only_volumes=False)

        if self.process == 'fs-glm':
            '''checks that all subjects are present in the SUBJECTS_DIR folder that will be used for GLM analysis,
                sends cmd to batch to initiate FreeSurfer GLM running script
            '''
            if DistributionReady(self.all_vars, self.project_vars, self.logger).fs_glm_ready():
                GLM_file_path, GLM_dir = DistributionHelper(self.all_vars, self.project_vars, self.logger).fs_glm_prep(self.stats_vars["STATS_PATHS"]["FS_GLM_dir"])
                DistributionReady(self.all_vars, self.project_vars, self.logger).fs_chk_fsaverage_ready(self.vars_local['FREESURFER']['FS_SUBJECTS_DIR'])
                if GLM_file_path:
                    self.vars_local['PROCESSING']['processing_env']  = "tmux"
                    schedule_fsglm = Scheduler(self.vars_local)
                    python_run_cmd = path.join(self.vars_local["NIMB_PATHS"]["conda_home"], 'bin', 'python3.7')
                    cmd = f'{python_run_cmd} fs_glm_runglm.py -project {self.project} -glm_dir {GLM_dir}'
                    cd_cmd = 'cd {}'.format(path.join(self.NIMB_HOME, 'processing', 'freesurfer'))
                    schedule_fsglm.submit_4_processing(cmd, 'fs_glm','run_glm', cd_cmd)
        if self.process == 'fs-glm-image':
            if not "export_screen" in self.vars_local['FREESURFER']:
                self.logger.info("PLEASE check that you can export your screen or you can run screen-based applications. \
                                    This is necessary for Freeview and Tksurfer. \
                                    Check the variable: export_screen in file {}".format(
                                        "credentials_path.py/nimb/local.json"))
            elif self.vars_local['FREESURFER']["export_screen"] == 0:
                self.logger.info("Current environment is not ready to export screen. Please define a compute where the screen can \
                                    be used for FreeSurfer Freeview and tksurfer")
            if DistributionReady(self.all_vars, self.project_vars, self.logger).fs_ready():
                self.logger.info('before running the script, remember to source $FREESURFER_HOME')
                cmd = '{} fs_glm_extract_images.py -project {}'.format(self.vars_local['PROCESSING']["python3_run_cmd"], self.project)
                cd_cmd = 'cd '+path.join(self.NIMB_HOME, 'processing', 'freesurfer')
                self.schedule.submit_4_processing(cmd, 'fs_glm','extract_images', cd_cmd)
        if self.process == 'fs-get-masks':
            if DistributionReady(self.all_vars, self.project_vars, self.logger).fs_ready():
                self.logger.info('running mask extraction')
                cmd = '{} run_masks.py -project {}'.format(self.vars_local['PROCESSING']["python3_run_cmd"], self.project)
                cd_cmd = 'cd '+path.join(self.NIMB_HOME, 'processing', 'freesurfer')
                self.schedule.submit_4_processing(cmd, 'fs','run_masks', cd_cmd)
        if self.process == 'run-stats':
            if not DistributionReady(self.all_vars, self.project_vars, self.logger).check_stats_ready():
                self.logger.info("NIMB is not ready to run the stats. Please check the configuration files.")
                sys.exit()
            else:
                from stats import stats_helper
                stats_helper.RUN_stats(self.stats_vars, self.project_vars).run_stats()
        return 1

def get_parameters(projects):
    """get parameters for nimb"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""text {}""".format(
            __version__
        ),
        epilog="""
            Documentation at https://github.com/alexhanganu/nimb
            """,
    )

    parser.add_argument(
        "-process", required=False,
        default='ready',
        choices = ['ready', 'run', 'check-new',
                    'classify', 'classify_dcm2bids',
                    'freesurfer', 'nilearn', 'dipy',
                    'fs-glm', 'fs-glm-image',
                    'fs-get-stats', 'run-stats',
                    'fs-get-masks'],
        help="ready (verifies that nimb is ready)\
        freesurfer (start FreeSurfer pipeline), \
            classify (classify MRIs) \
            fs-glm (perform freesurfer mri_glmfit GLM analsysis), \
            fs-glm-images (extracts images after FS GLM analysis, using Freeview and TKsurfer. Requires export screen),\
            fs-get-stats (extract freesurfer stats from subjid/stats/* to an excel file), \
            run-stats (perform statistical analysis),\
            run (NOT READY. runs a project),\
            check-new (NOT READY. verfies for new subjects if processed),\
            classify_bids (NOT READY. performs classification of MRI data according to BIDS structure, using UNF-Montreal/DCM2BIDS),\
            nilearn (NOT READY. performs resting state functional analysis, extract ROI z-Fisher correlational values),\
            dipy (NOT READY. performs DWI analysis with dipy. extracts ROI HARDI statistics),\
            fs-get-masks (NOT READY. extract ROI masks based on FreeSurfer parameters)"
    )

    parser.add_argument(
        "-project", required=False,
        default=projects[:1][0],
        choices = projects,
        help="names of projects are located in credentials_path.py/nimb/projects.json -> PROJECTS",
    )

    parser.add_argument(
        "-fix-spaces", required=False,
        action='store_true',
        help="paths that contain spaces will not be read by FreeSurfer. This parameter will tell nimb to change spaces to underscores during the classification",
    )


    params = parser.parse_args()
    return params


def main():

    all_vars = Get_Vars()
    projects = all_vars.projects
    all_projects = [i for i in projects.keys() if 'EXPLANATION' not in i and 'LOCATION' not in i]
    params = get_parameters(all_projects)
    app = NIMB(params, projects, all_vars)
    return app.run()


if __name__ == "__main__":
    main()
    # sys.exit(main())
