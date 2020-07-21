# -*- coding: utf-8 -*-
# 2020 07 21

"""nimb module"""

import argparse
import sys
from distribution.pipeline_management import Management
from setup.get_vars import get_vars
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
        self.vars = get_vars()


    def run(self):
        """Run nimb"""
        task = Management(self.process)

        if self.process == 'classify':
            print(self.vars)
             SUBJECTS_DIR_RAW = ""
             NIMB_tmp = ""
             classify_bids.get_dict_MR_files2process(SUBJECTS_DIR_RAW, NIMB_tmp)

        if self.process == 'freesurfer':
            task.freesurfer()

        if self.process == 'stats':
            task.stats()

        if self.process == 'fsglm':
            task.fsglm()




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
