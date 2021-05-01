# -*- coding: utf-8 -*-

"""nimb module"""

import argparse
from os import path
import sys
from setup.get_vars import Get_Vars, SetProject
from distribution.distribution_helper import DistributionHelper
from distribution.distribution_ready import DistributionReady
from distribution.utilities import ErrorMessages
from distribution.logger import Log
from processing.schedule_helper import Scheduler
from setup.version import __version__

class NIMB(object):
    """ Object to initiate pipeline
    Args:
        all_vars: all variables of local.json, all remotes.json, stats.json
                 as defiend in credentials_path/projects.json -> LOCATION
                 and params defined by user
    """

    def __init__(self, all_vars):

        self.all_vars     = all_vars
        self.process      = all_vars.params.process
        self.project      = all_vars.params.project
        self.fix_spaces   = all_vars.params.fix_spaces
        self.project_vars = all_vars.projects[self.project]
        self.stats_vars   = all_vars.stats_vars
        self.locations    = all_vars.location_vars
        self.vars_local   = self.locations['local']
        self.NIMB_HOME    = self.vars_local['NIMB_PATHS']['NIMB_HOME']
        self.NIMB_tmp     = self.vars_local['NIMB_PATHS']['NIMB_tmp']
        self.logger       = Log(self.NIMB_tmp, self.vars_local['FREESURFER']['freesurfer_version']).logger
        self.schedule     = Scheduler(self.vars_local)
        self.py_run_cmd   = self.vars_local['PROCESSING']["python3_run_cmd"]


    def run(self):
        """Run nimb"""

        if self.process == 'ready':
            DistributionReady(self.all_vars).check_ready()

        if self.process == 'classify':
            print('checking if ready to classify')
            if not DistributionReady(self.all_vars).classify_ready():
                ErrorMessages.error_classify()
                sys.exit()
            else:
                SUBJ_2Classify = DistributionHelper(self.all_vars).get_subj_2classify()
                if SUBJ_2Classify:
                    from classification.classify_bids import MakeBIDS_subj2process
                    return MakeBIDS_subj2process(SUBJ_2Classify,
                                         self.NIMB_tmp,
                                         self.fix_spaces,
                                         self.vars_local['FREESURFER']['multiple_T1_entries'],
                                         self.vars_local['FREESURFER']['flair_t2_add']).run()

        if self.process == 'run-stats':
            if not DistributionReady(self.all_vars).chk_if_ready_for_stats():
                print("NIMB is not ready to run the stats. Please check the configuration files.")
                sys.exit()
            else:
                fname_groups = DistributionHelper(self.all_vars).prep_4stats()
                if fname_groups:
                    self.vars_local['PROCESSING']['processing_env']  = "tmux" #probably works with slurm, must be checked
                    schedule = Scheduler(self.vars_local)
                    cd_cmd = 'cd {}'.format(path.join(self.NIMB_HOME, 'stats'))
                    cmd = f'{self.py_run_cmd} stats_helper.py -project {self.project}'
                    schedule.submit_4_processing(cmd, 'nimb_stats','run', cd_cmd)

        # FreeSurfer related codes: "freesurfer"   - performs preprocessing
        #							"fs-get-stats" - extracts statistical data an an xls/ xlsx/ csv file
        # 							"fs-glm"       - performs FreeSurfer GLM analysis with mri_glm_fit
        # 							"fs-glm-image" - extracts the images for significant results after the GLM
        if self.process == 'freesurfer':
            if not DistributionReady(self.all_vars).fs_ready():
                print("FreeSurfer is not ready or freesurfer_install is set to 0. Please check the configuration files.")
                sys.exit()
            else:
                cd_cmd = 'cd {}'.format(path.join(self.NIMB_HOME, 'processing', 'freesurfer'))
                cmd = f'{self.py_run_cmd} crun.py'
                self.schedule.submit_4_processing(cmd, 'nimb','run', cd_cmd,
                                                activate_fs = False,
                                                python_load = True)
        if self.process == 'fs-get-stats':
            if DistributionReady(self.all_vars).chk_if_ready_for_stats():
                PROCESSED_FS_DIR = DistributionHelper(self.all_vars).prep_4fs_stats()
                if PROCESSED_FS_DIR:
                    self.vars_local['PROCESSING']['processing_env']  = "tmux" #probably works with slurm, must be checked
                    schedule = Scheduler(self.vars_local)
                    dir_4stats = self.stats_vars["STATS_PATHS"]["STATS_HOME"]
                    cmd = f'{self.py_run_cmd} fs_stats2table.py -project {self.project} -stats_dir {dir_4stats}'
                    cd_cmd = 'cd {}'.format(path.join(self.NIMB_HOME, 'processing', 'freesurfer'))
                    schedule.submit_4_processing(cmd, 'fs_stats','get_stats', cd_cmd)
        if self.process == 'fs-glm':
            '''checks that all subjects are present in the SUBJECTS_DIR folder that will be used for GLM analysis,
                sends cmd to batch to initiate FreeSurfer GLM running script
            '''
            fs_glm_dir   = self.stats_vars["STATS_PATHS"]["FS_GLM_dir"]
            fname_groups = self.project_vars['fname_groups']
            if DistributionReady(self.all_vars).chk_if_ready_for_fs_glm():
                GLM_file_path, GLM_dir = DistributionHelper(self.all_vars).prep_4fs_glm(fs_glm_dir,
                                                                            fname_groups)
                FS_SUBJECTS_DIR = self.vars_local['FREESURFER']['FS_SUBJECTS_DIR']
                DistributionReady(self.all_vars).fs_chk_fsaverage_ready(FS_SUBJECTS_DIR)
                if GLM_file_path:
                    print('    GLM file path is:',GLM_file_path)
                    self.vars_local['PROCESSING']['processing_env']  = "tmux"
                    schedule_fsglm = Scheduler(self.vars_local)
                    cd_cmd = 'cd {}'.format(path.join(self.NIMB_HOME, 'processing', 'freesurfer'))
                    cmd = f'{self.py_run_cmd} fs_glm_runglm.py -project {self.project} -glm_dir {GLM_dir}'
                    schedule_fsglm.submit_4_processing(cmd, 'fs_glm','run_glm', cd_cmd)
        if self.process == 'fs-glm-image':
            '''extracts FS-GLM images for p<0.05 and MCz-corrected results
            requires FreeSurfer to be installed in order to access tksurfer and freeview
            '''
            if not "export_screen" in self.vars_local['FREESURFER']:
                print("PLEASE check that you can export your screen or you can run screen-based applications. \
                                    This is necessary for Freeview and Tksurfer. \
                                    Check the variable: export_screen in file {}".format(
                                        "credentials_path.py/nimb/local.json"))
            elif self.vars_local['FREESURFER']["export_screen"] == 0:
                print("Current environment is not ready to export screen. Please define a compute where the screen can \
                                    be used for FreeSurfer Freeview and tksurfer")
            if DistributionReady(self.all_vars).fs_ready():
                print('before running the script, remember to source $FREESURFER_HOME')
                cmd = '{} fs_glm_extract_images.py -project {}'.format(self.py_run_cmd, self.project)
                cd_cmd = 'cd '+path.join(self.NIMB_HOME, 'processing', 'freesurfer')
                self.schedule.submit_4_processing(cmd, 'fs_glm','extract_images', cd_cmd)

        # Nilearn related codes: "nilearn" - performs preprocessing of rsfMRI data
        if self.process == 'nilearn':
            if not DistributionReady(self.all_vars).nilearn_ready():
                print("Nilearn is not ready.")
                sys.exit()
            else:
                cmd = f'{self.py_run_cmd} crun.py'
                cd_cmd = 'cd '+path.join(self.NIMB_HOME, 'processing', 'nilearn')
                self.schedule.submit_4_processing(cmd, 'nilearn','run', cd_cmd,
                                                activate_fs = False,
                                                python_load = True)

        # Dipy related codes: "dipy" - performs preprocessing of DWI data
        if self.process == 'dipy':
            if not DistributionReady(self.all_vars).dipy_ready():
                print("Dipy is not ready.")
                sys.exit()
            else:
                cmd = f'{self.py_run_cmd} crun.py'
                cd_cmd = 'cd '+path.join(self.NIMB_HOME, 'processing', 'dipy')
                self.schedule.submit_4_processing(cmd, 'dipy','run', cd_cmd,
                                                activate_fs = False,
                                                python_load = True)

        if self.process == 'classify_dcm2bids':
            print("initiating dcm2bids transformation for project: {}".format(self.project))
            from classification.dcm2bids_helper import DCM2BIDS_helper
            return DCM2BIDS_helper(self.project_vars, self.project).run()

        if self.process == 'run':
            from distribution.project_helper import ProjectManager
            ProjectManager(self.all_vars).run()

        if self.process == 'check-new':
            print('checking for new subject to be processed')
            DistributionHelper(self.all_vars).check_new()

        if self.process == 'fs-get-masks':
            if DistributionReady(self.all_vars).fs_ready():
                print('running mask extraction')
                cmd = '{} run_masks.py -project {}'.format(self.py_run_cmd, self.project)
                cd_cmd = 'cd '+path.join(self.NIMB_HOME, 'processing', 'freesurfer')
                self.schedule.submit_4_processing(cmd, 'fs','run_masks', cd_cmd)
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
    """
        projects: parameters of all projects from credentials_path/projects.json
        params  : from parameters defined by user, process, project
    """
    all_vars  = Get_Vars()
    projects  = all_vars.projects
    all_projects = [i for i in projects.keys() if i not in ('EXPLANATION', 'LOCATION')]
    all_vars.params    = get_parameters(all_projects)
    project   = all_vars.params.project
    if project == all_projects[0]:
        print(f'    no project was defined - working with project in first position: {project}')

    all_vars.stats_vars = SetProject(all_vars.location_vars['local']['NIMB_PATHS']['NIMB_tmp'],
                                all_vars.stats_vars,
                                project,
                                projects[project]['fname_groups']).stats
    app = NIMB(all_vars)
    return app.run()


if __name__ == "__main__":
    main()
