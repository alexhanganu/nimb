# -*- coding: utf-8 -*-
# 2020 07 21

"""nimb module"""

import argparse
import sys
import json
from distribution.pipeline_management import Management
from setup.get_vars import Get_Vars
from processing.freesurfer import start_fs_pipeline

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
        print('local user is: '+self.vars['local']['user'])


    def run(self):
        """Run nimb"""
        task = Management(self.process, self.vars)
        self.SOURCE_SUBJECTS_DIR = self.vars['local']['PATHS']['SOURCE_SUBJECTS_DIR']
        self.NIMB_tmp              = self.vars['local']['PATHS']['NIMB_tmp']

        if self.process == 'classify':
            self.classify(task.freesurfer())

        if self.process == 'freesurfer':
            with open(path.join(self.vars['local']['PATHS']['NIMB_HOME'],'processing','freesurfer','vars.json')) as jf:
                json.dump(self.vars['local'], jf, indent=4)
            start_fs_pipeline()

        if self.process == 'stats':
            task.stats()

        if self.process == 'fsglm':
            task.fsglm()

    def classify(self, ready):
        if ready:
            return classify_bids.get_dict_MR_files2process(self.SOURCE_SUBJECTS_DIR, self.NIMB_tmp)





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
        default='freesurfer', 
        choices = ['freesurfer','classify','stats','fsglm'],
        help="freesurfer (start FreeSurfer pipeline), classify (classify MRIs) stats (perform statistical analysis), fsglm (perform freesurfer mri_glmfit GLM analsysis)",
    )


    params = parser.parse_args()
    return params


def main():

    params = get_parameters()

    app = NIMB(**vars(params))
    return app.run()


if __name__ == "__main__":
    sys.exit(main())



# cusers_list = users_list
# cuser = user
# nimb_dir = NIMB_HOME
# SUBJECTS_DIR = FS_SUBJECTS_DIR
# processed_SUBJECTS_DIR = path.join('/home',user,'projects',supervisor_account,'processed_subjects') #must be changed to NIMB_HOME/processed_nimb/processed_fs
# dir_new_subjects=path.join('/home',user,'projects',supervisor_account,'new_subjects')  #must be changed to NIMB_RHOME/new_subjects
