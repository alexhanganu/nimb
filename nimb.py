# -*- coding: utf-8 -*-
# 2020 07 21

"""nimb module"""

import argparse
from os import path
import sys
from setup.get_vars import Get_Vars, SetProject
from classification import classify_bids
from distribution.distribution_helper import DistributionHelper
from distribution.distribution_helper import ErrorMessages

__version__ = 'v1'

class NIMB(object):
    """ Object to initiate pipeline
    Args:
        process: initiates pipeline
    """

    def __init__(
        self,
        credentials_home,
        projects,
        locations,
        installers,
        process,
        project,
    ):

        self.projects  = projects
        self.locations = locations
        self.process   = process
        self.project   = project
        self.distribution = DistributionHelper(credentials_home, projects,
                                               locations, installers, project)

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
                                     self.locations['local']['NIMB_PATHS']['NIMB_NEW_SUBJECTS'],
                                     self.locations['local']['NIMB_PATHS']['NIMB_HOME'],
                                     self.locations['local']['NIMB_PATHS']['NIMB_tmp'],
                                     self.locations['local']['FREESURFER']['multiple_T1_entries'],
                                     self.locations['local']['FREESURFER']['flair_t2_add'])

        if self.process == 'freesurfer':
            if not self.distribution.fs_ready():
                print("FreeSurfer is not ready or freesurfer_install is set to 0. Please check the configuration files.")
                sys.exit()
            else:
                from processing.freesurfer import submit_4processing
                submit_4processing.Submit_task(self.locations['local'],                                                                                                                                           self.locations['local']['PROCESSING']["python3_load_cmd"]+'\n'+self.locations['local']['PROCESSING']["python3_run_cmd"]+' crun.py',
                                               'nimb','run', self.locations['local']['PROCESSING']["batch_walltime"],
                                               False, 'cd '+path.join(self.locations['local']["NIMB_PATHS"]["NIMB_HOME"], 'processing', 'freesurfer'))

        if self.process == 'fs-stats':
            if not self.distribution.nimb_stats_ready():
                print("NIMB is not ready to perform statistics. Please check the configuration files.")
                sys.exit()
            else:
                PROCESSED_FS_DIR = self.distribution.fs_stats(self.project)
                print(PROCESSED_FS_DIR)
                from stats import fs_stats2table

                fs_stats2table.chk_if_subjects_ready(self.locations["local"]["STATS_PATHS"]["STATS_HOME"], PROCESSED_FS_DIR)
                fs_stats2table.stats2table_v7(
                                   self.locations["local"]["STATS_PATHS"]["STATS_HOME"],
                                   PROCESSED_FS_DIR, data_only_volumes=False)

        if self.process == 'fs-glm':
            if self.distribution.fs_ready():
                self.distribution.fs_glm()
                from processing.freesurfer import submit_4processing
                print('Please check that all required variables for the GLM analysis are defined in the var.py file')
                print('before running the script, remember to source $FREESURFER_HOME')
                print('check if fsaverage is present in SUBJECTS_DIR')
                print('each subject must include at least the folders: surf and label')
                submit_4processing.Submit_task(self.locations['local'], self.locations['local']['NIMB_PATHS']["miniconda_python_run"]+' fs_glm_run_glm.py -project '+self.project,
                                               'fs_glm','run_glm', self.locations['local']['PROCESSING']["batch_walltime"],
                                               True, 'cd '+path.join(self.locations['local']["NIMB_PATHS"]["NIMB_HOME"], 'processing', 'freesurfer'))


        if self.process == 'fs-glm-image':
            if self.distribution.fs_ready():
                from processing.freesurfer import submit_4processing
                print('before running the script, remember to source $FREESURFER_HOME')
                submit_4processing.Submit_task(self.locations['local'], self.locations['local']['NIMB_PATHS']["miniconda_python_run"]+' fs_glm_extract_images.py -project '+self.project,
                                               'fs_glm','extract_images', self.locations['local']['PROCESSING']["batch_walltime"],
                                               True, 'cd '+path.join(self.locations['local']["NIMB_PATHS"]["NIMB_HOME"], 'processing', 'freesurfer'))
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
        choices = ['ready', 'freesurfer', 'classify', 'fs-stats', 'fs-glm', 'fs-glm-image', 'stats-general'],
        help="freesurfer (start FreeSurfer pipeline), classify (classify MRIs) fs-stats (extract freesurfer stats from subjid/stats/* to an excel file), fs-glm (perform freesurfer mri_glmfit GLM analsysis), stats-general (perform statistical analysis)",
    )

    parser.add_argument(
        "-project", required=False,
        default=projects[:1][0],
        choices = projects,
        help="names of projects located in credentials_path.py/nimb/projects.json -> PROJECTS",
    )

    params = parser.parse_args()
    return params


def main():

    getvars = Get_Vars()
    credentials_home = getvars.credentials_home
    projects = getvars.projects
    locations = getvars.location_vars
    installers = getvars.installers

    params = get_parameters(projects['PROJECTS'])
    locations['local']['STATS_PATHS'] = SetProject(locations['local']['NIMB_PATHS']['NIMB_HOME'], locations['local']['STATS_PATHS'], params.project).STATS_PATHS

    app = NIMB(credentials_home, projects, locations, installers, params.process, params.project)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
