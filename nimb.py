# -*- coding: utf-8 -*-
# 2020 07 21

"""nimb module"""

import argparse
import sys
from distribution.pipeline_management import Management
from setup.get_vars import get_vars


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
            task.classify(self.vars)

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