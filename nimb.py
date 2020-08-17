# -*- coding: utf-8 -*-
# 2020 07 21

"""nimb module"""

import argparse
import sys
import json
from setup.get_vars import Get_Vars
from os import path
from classification import classify_bids
# from distribution.distribution_helper import  DistributionHelper
__version__ = 'v1'

class NIMB(object):
    """ Object to initiate pipeline
    Args:
        process: initiates pipeline
    """

    def __init__(
        self,
        projects,
        locations,
        installers,
        process,
        project,
        **_
    ):

        self.projects  = projects
        self.locations = locations
        self.installers = installers
        self.process   = process
        self.project   = project
        print('local user is: '+self.locations['local']['USER']['user'])
        self.ready()

    def ready(self):
       # DistributionHelper.freesurfer(self.installers)
       return True


    def run(self):
        """Run nimb"""

        if self.process == 'classify':
            # if not DistributionHelper.is_setup_vars_folders(config_file="../setup/local.json", is_nimb_classification=True):
                # print("Please check the configuration files. There is some missing!")
                # sys.exit()
            # send the data
            # DistributionHelper.send_subject_data(config_file="../setup/local.json")
            if self.ready():
                return classify_bids.get_dict_MR_files2process(
                                     self.locations['local']['NIMB_PATHS']['NIMB_NEW_SUBJECTS'],
                                     self.locations['local']['NIMB_PATHS']['NIMB_HOME'],
                                     self.locations['local']['NIMB_PATHS']['NIMB_tmp'],
                                     self.locations['local']['FREESURFER']['flair_t2_add'])

        if self.process == 'freesurfer':
            # send the data
            # DistributionHelper.send_subject_data(config_file="../setup/local.json")
            # if not DistributionHelper.is_setup_vars_folders(config_file="../setup/local.json", is_freesurfer_nim=True):
                # print("Please check the configuration files. There is some missing!")
                # sys.exit()
            if self.ready():
                vars_f = path.join(self.locations['local']['NIMB_PATHS']['NIMB_HOME'],'processing','freesurfer','vars.json')
                with open(vars_f,'w') as jf:
                    json.dump(self.locations['local'], jf, indent=4)
                from processing.freesurfer import start_fs_pipeline
                start_fs_pipeline.start_fs_pipeline()

        if self.process == 'fs-stats':
            # if not DistributionHelper.is_setup_vars_folders(config_file="../setup/local.json", is_nimb_fs_stats=True):
                # print("Please check the configuration files. There is some missing!")
                # sys.exit()
            if self.ready():
                PROCESSED_FS_DIR = DistributionHelper.fs_stats(self.project)
                print(PROCESSED_FS_DIR)
                from stats import fs_stats2table

                fs_stats2table.chk_if_subjects_ready(self.locations["local"]["STATS_PATHS"]["STATS_HOME"], PROCESSED_FS_DIR)
                fs_stats2table.stats2table_v7(
                                   self.locations["local"]["STATS_PATHS"]["STATS_HOME"],
                                   PROCESSED_FS_DIR, data_only_volumes=False)

        if self.process == 'fs-glm':
            if self.ready():
                DistributionHelper.fs_glm()
                from processing.freesurfer import fs_runglm



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
        choices = ['ready', 'freesurfer', 'classify', 'fs-stats', 'fs-glm', 'stats-general'],
        help="freesurfer (start FreeSurfer pipeline), classify (classify MRIs) fs-stats (extract freesurfer stats from subjid/stats/* to an excel file), fs-glm (perform freesurfer mri_glmfit GLM analsysis), stats-general (perform statistical analysis)",
    )
    
    parser.add_argument(
        "-project", required=False,
        default=projects[:1],
        choices = projects,
        help="names of projects located in setup/projects.json -> PROJECTS",
    )

    params = parser.parse_args()
    return params


def main():

    getvars = Get_Vars()
    projects = getvars.projects
    locations = getvars.d_all_vars
    installers = getvars.installers
    params = get_parameters(projects['PROJECTS'])

    app = NIMB(projects, locations, installers, **vars(params))
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
