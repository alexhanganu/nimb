# -*- coding: utf-8 -*-
# 2020 07 21

"""nimb module"""

import argparse
import sys
import json
from distribution.pipeline_management import Management
from setup.get_vars import Get_Vars
from os import path
from classification import classify_bids

__version__ = 'v1'

class NIMB(object):
    """ Object to initiate pipeline
    Args:
        process: initiates pipeline
    """

    def __init__(
        self,
        process,
        **_
    ):

        self.process = process
        getvars = Get_Vars()
        self.vars = getvars.d_all_vars
        print('local user is: '+self.vars['local']['USER']['user'])
        self.ready()

    def ready(self):
        task = Management(self.process, self.vars)
        task.freesurfer()
        return True
        

    def run(self):
        """Run nimb"""
        task = Management(self.process, self.vars)

        if self.process == 'classify':
            if self.ready():
                return classify_bids.get_dict_MR_files2process(
                                     self.vars['local']['NIMB_PATHS']['NIMB_NEW_SUBJECTS'],
                                     self.vars['local']['NIMB_PATHS']['NIMB_HOME'],
                                     self.vars['local']['NIMB_PATHS']['NIMB_tmp'],
                                     self.vars['local']['FREESURFER']['flair_t2_add'])

        if self.process == 'freesurfer':
            if self.ready():
                vars_f = path.join(self.vars['local']['NIMB_PATHS']['NIMB_HOME'],'processing','freesurfer','vars.json')
                with open(vars_f,'w') as jf:
                    json.dump(self.vars['local'], jf, indent=4)
                from processing.freesurfer import start_fs_pipeline
                start_fs_pipeline.start_fs_pipeline()

        if self.process == 'fs-stats':
            if self.ready():
                PROCESSED_FS_DIR = task.fs_stats()
                print(PROCESSED_FS_DIR)
                from stats import fs_stats2table

                fs_stats2table.chk_if_subjects_ready(self.vars["local"]["STATS_PATHS"]["STATS_HOME"], PROCESSED_FS_DIR)
                fs_stats2table.stats2table_v7(
                                   self.vars["local"]["STATS_PATHS"]["STATS_HOME"],
                                   PROCESSED_FS_DIR, data_only_volumes=False)

        if self.process == 'fs-glm':
            if self.ready():
                task.fs_glm()
                from processing.freesurfer import fs_runglm



def get_parameters():
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

    params = parser.parse_args()
    return params


def main():

    params = get_parameters()

    app = NIMB(**vars(params))
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
