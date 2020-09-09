# -*- coding: utf-8 -*-
# 2020 07 21

"""nimb module"""

import argparse
from os import path
import sys
from setup.get_vars import Get_Vars, SetProject
from classification import classify_bids
from distribution.distribution_helper import DistributionHelper
from distribution.utilities import ErrorMessages

__version__ = 'v1'

class NIMB(object):
    """ Object to initiate pipeline
    Args:
        process: initiates pipeline
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
        self.locations   = all_vars.location_vars
        self.stats_vars  = all_vars.stats_vars
        self.vars_local  = self.locations['local']

        self.distribution = DistributionHelper(all_vars.credentials_home, self.projects,
                                               self.locations, all_vars.installers, self.project)

    def run(self):
        """Run nimb"""

        if self.process == 'ready':
            self.distribution.ready()

        if self.process == 'classify':
            print('starting')
            if not self.distribution.classify_ready():
                ErrorMessages.error_classify()
                sys.exit()
            else:
                return classify_bids.get_dict_MR_files2process(
                                     self.vars_local['NIMB_PATHS']['NIMB_NEW_SUBJECTS'],
                                     self.vars_local['NIMB_PATHS']['NIMB_HOME'],
                                     self.vars_local['NIMB_PATHS']['NIMB_tmp'],
                                     self.vars_local['FREESURFER']['multiple_T1_entries'],
                                     self.vars_local['FREESURFER']['flair_t2_add'])

        if self.process == 'check-new':
            self.check_new()

        if self.process == 'freesurfer':
            if not self.distribution.fs_ready():
                print("FreeSurfer is not ready or freesurfer_install is set to 0. Please check the configuration files.")
                sys.exit()
            else:
                from processing.freesurfer import submit_4processing
                submit_4processing.Submit_task(self.vars_local,                                                                                                                                           self.vars_local['PROCESSING']["python3_load_cmd"]+'\n'+self.vars_local['PROCESSING']["python3_run_cmd"]+' crun.py',
                                               'nimb','run', self.vars_local['PROCESSING']["batch_walltime"],
                                               False, 'cd '+path.join(self.vars_local["NIMB_PATHS"]["NIMB_HOME"], 'processing', 'freesurfer'))

        if self.process == 'fs-get-stats':
            if not self.distribution.nimb_stats_ready():
                print("NIMB is not ready to extract the FreeSurfer statistics per user. Please check the configuration files.")
                sys.exit()
            else:
                PROCESSED_FS_DIR = self.distribution.fs_stats(self.project)
                print(PROCESSED_FS_DIR)
                from stats import fs_stats2table

                fs_stats2table.chk_if_subjects_ready(self.stats_vars["STATS_HOME"], PROCESSED_FS_DIR)
                fs_stats2table.stats2table_v7(
                                   self.stats_vars["STATS_HOME"],
                                   PROCESSED_FS_DIR, data_only_volumes=False)

        if self.process == 'fs-glm':
            if self.distribution.fs_ready():
                self.distribution.fs_glm()
                from processing.freesurfer import submit_4processing
                print('Please check that all required variables for the GLM analysis are defined in the var.py file')
                print('before running the script, remember to source $FREESURFER_HOME')
                print('check if fsaverage is present in SUBJECTS_DIR')
                print('each subject must include at least the folders: surf and label')
                submit_4processing.Submit_task(self.vars_local, self.vars_local['NIMB_PATHS']["miniconda_python_run"]+' fs_glm_run_glm.py -project '+self.project,
                                               'fs_glm','run_glm', self.vars_local['PROCESSING']["batch_walltime"],
                                               True, 'cd '+path.join(self.vars_local["NIMB_PATHS"]["NIMB_HOME"], 'processing', 'freesurfer'))


        if self.process == 'fs-glm-image':
            if self.distribution.fs_ready():
                from processing.freesurfer import submit_4processing
                print('before running the script, remember to source $FREESURFER_HOME')
                submit_4processing.Submit_task(self.vars_local, self.vars_local['NIMB_PATHS']["miniconda_python_run"]+' fs_glm_extract_images.py -project '+self.project,
                                               'fs_glm','extract_images', self.vars_local['PROCESSING']["batch_walltime"],
                                               True, 'cd '+path.join(self.vars_local["NIMB_PATHS"]["NIMB_HOME"], 'processing', 'freesurfer'))
        if self.process == 'run-stats':
            self.stats_vars = SetProject(self.vars_local['NIMB_PATHS']['NIMB_tmp'], self.stats_vars, self.project).stats
            if not self.distribution.run_stats_ready():
                print("NIMB is not ready to run the stats. Please check the configuration files.")
                sys.exit()
            else:
                from stats import stats_helper
                stats_helper.RUN_stats(self.stats_vars, self.projects[self.project]).run_stats()
        return 1

    def check_new(self):
        print('checking new')
        self.distribution.download_processed_subject(local_destination, remote_path, remote_host, remote_username, remote_password)
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
        choices = ['ready', 'check-new', 'freesurfer', 'classify', 'fs-get-stats', 'fs-glm', 'fs-glm-image', 'run-stats'],
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

    params = get_parameters(projects['PROJECTS'])
    app = NIMB(params.process, params.project, projects, all_vars)
    return app.run()


if __name__ == "__main__":
    main()
    # sys.exit(main())
