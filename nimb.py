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
        process: process to be initiated
        project: project name, if not provided first is taken, credentials_path/projects.json
        projects: parameters of all projects
        all_vars: all variables of local.json and all remotes.json 
    """

    def __init__(
        self,
        process,
        project,
        projects,
        all_vars
    ):

        self.process     = process
        self.project     = project
        self.projects    = projects
        self.all_vars    = all_vars
        self.locations   = all_vars.location_vars
        self.stats_vars  = all_vars.stats_vars
        self.vars_local  = self.locations['local']
        self.NIMB_HOME   = self.vars_local['NIMB_PATHS']['NIMB_HOME']
        self.NIMB_tmp   = self.vars_local['NIMB_PATHS']['NIMB_tmp']
        Log(self.NIMB_tmp, self.vars_local['FREESURFER']['freesurfer_version'])
        self.logger = logging.getLogger(__name__)
        self.schedule = Scheduler(self.vars_local)

    def run(self):
        """Run nimb"""

        if self.process == 'ready':
            DistributionReady(self.all_vars, self.projects, self.project).check_ready()

        if self.process == 'check-new':
            self.logger.info('checking for new subject to be processed')
            DistributionHelper(self.all_vars, self.projects, self.project).check_new()

        if self.process == 'classify':
            self.logger.info('checking if ready to classify')
            if not DistributionReady(self.all_vars, self.projects, self.project).classify_ready():
                ErrorMessages.error_classify()
                sys.exit()
            else:
                SUBJ_2Classify = DistributionHelper(self.all_vars, self.projects, self.project).get_subj_2classify()
                from classification.classify_bids import MakeBIDS_subj2process
                return MakeBIDS_subj2process(SUBJ_2Classify,
                                     self.NIMB_tmp,
                                     self.vars_local['FREESURFER']['multiple_T1_entries'],
                                     self.vars_local['FREESURFER']['flair_t2_add']).run()

        if self.process == 'classify_dcm2bids':
            self.logger.info("initiating dcm2bids transformation for project: {}".format(self.project))
            from classification.dcm2bids_helper import DCM2BIDS_helper
            return DCM2BIDS_helper(self.projects[self.project], self.project).run()

        if self.process == 'freesurfer':
            if not DistributionReady(self.all_vars, self.projects, self.project).fs_ready():
                self.logger.info("FreeSurfer is not ready or freesurfer_install is set to 0. Please check the configuration files.")
                sys.exit()
            else:
                cmd = '{} crun.py'.format(self.vars_local['PROCESSING']["python3_run_cmd"])
                cd_cmd = 'cd '+path.join(self.NIMB_HOME, 'processing', 'freesurfer')
                self.schedule.submit_4_processing(cmd, 'nimb','run', cd_cmd,
                                                activate_fs = False,
                                                python_load = True)

        if self.process == 'fs-get-stats':
            if not DistributionReady(self.all_vars, self.projects, self.project).nimb_stats_ready():
                self.logger.info("NIMB is not ready to extract the FreeSurfer statistics per user. Please check the configuration files.")
                sys.exit()
            else:
                PROCESSED_FS_DIR = DistributionHelper(self.all_vars, self.projects, self.project).get_stats_dir()
                self.logger.info(PROCESSED_FS_DIR)
                from stats import fs_stats2table
                fs_stats2table.chk_if_subjects_ready(self.stats_vars["STATS_HOME"], PROCESSED_FS_DIR)
                fs_stats2table.stats2table_v7(
                                   self.stats_vars["STATS_HOME"],
                                   PROCESSED_FS_DIR, data_only_volumes=False)

        if self.process == 'fs-glm':
            if DistributionReady(self.all_vars, self.projects, self.project).fs_ready():
                self.logger.info('Please check that all required variables for the GLM analysis are defined in the var.py file')
                cmd = '{} fs_glm_runglm.py -project {}'.format(self.vars_local['PROCESSING']["python3_run_cmd"], self.project)
                cd_cmd = 'cd '+path.join(self.NIMB_HOME, 'processing', 'freesurfer')
                self.schedule.submit_4_processing(cmd, 'fs_glm','run_glm', cd_cmd)

        if self.process == 'fs-glm-image':
            if DistributionReady(self.all_vars, self.projects, self.project).fs_ready():
                self.logger.info('before running the script, remember to source $FREESURFER_HOME')
                cmd = '{} fs_glm_extract_images.py -project {}'.format(self.vars_local['PROCESSING']["python3_run_cmd"], self.project)
                cd_cmd = 'cd '+path.join(self.NIMB_HOME, 'processing', 'freesurfer')
                self.schedule.submit_4_processing(cmd, 'fs_glm','extract_images', cd_cmd)
        if self.process == 'run-stats':
            from setup.get_vars import SetProject
            self.stats_vars = SetProject(self.NIMB_tmp, self.stats_vars, self.project).stats
            if not DistributionReady(self.all_vars, self.projects, self.project).check_stats_ready():
                self.logger.info("NIMB is not ready to run the stats. Please check the configuration files.")
                sys.exit()
            else:
                from stats import stats_helper
                stats_helper.RUN_stats(self.stats_vars, self.projects[self.project]).run_stats()
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
        choices = ['ready', 'check-new', 'freesurfer', 'classify', 'classify_dcm2bids', 'fs-get-stats', 'fs-glm', 'fs-glm-image', 'run-stats'],
        help="freesurfer (start FreeSurfer pipeline), classify (classify MRIs) fs-stats (extract freesurfer stats from subjid/stats/* to an excel file), fs-glm (perform freesurfer mri_glmfit GLM analsysis), stats-general (perform statistical analysis)",
    )

    parser.add_argument(
        "-project", required=False,
        default=projects[:1][0],
        choices = projects,
        help="names of projects are located in credentials_path.py/nimb/projects.json -> PROJECTS",
    )

    params = parser.parse_args()
    return params


def main():

    all_vars = Get_Vars()
    projects = all_vars.projects
    params = get_parameters([i for i in projects.keys() if 'EXPLANATION' not in i and 'LOCATION' not in i])
    app = NIMB(params.process, params.project, projects, all_vars)
    return app.run()


if __name__ == "__main__":
    main()
    # sys.exit(main())
