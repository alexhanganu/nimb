# -*- coding: utf-8 -*-

"""
NIMB Main Module
"""

import sys
import os
from setup.config_manager import ConfigManager
from distribution.distribution_manager import DistributionManager
from distribution.project_helper import ProjectManager
from processing.schedule_helper import Scheduler
from classification.classifier import ClassificationManager
from setup.version import __version__


class NIMB:
    """
    Main object to orchestrate the NIMB pipeline.
    """
    def __init__(self, all_vars):
        self.all_vars = all_vars
        self.params = all_vars.params
        self.project_vars = all_vars.projects[self.params.project]
        self.locations = all_vars.location_vars
        self.vars_local = self.locations['local']
        self.NIMB_HOME = self.vars_local['NIMB_PATHS']['NIMB_HOME']
        self.NIMB_tmp = self.vars_local['NIMB_PATHS']['NIMB_tmp']
        
        self.logger = all_vars.logger
        self.logger.info("NIMB application initialized.")

        # Initialize managers
        self.dist_manager = DistributionManager(all_vars)
        self.proj_manager = ProjectManager(all_vars, self.dist_manager)
        self.scheduler = Scheduler(self.vars_local)
        self.classifier = ClassificationManager(all_vars) # New classifier

        self.py_run_cmd = self.vars_local['PROCESSING']["python3_run_cmd"]

        self.process_handlers = {
            'ready': self._handle_ready,
            'run': self._handle_run,
            'classify': self._handle_classify,
            'classify2bids': self._handle_classify_2_bids,
            'fs-get-stats': self._handle_fs_get_stats,
            'fs-glm': self._handle_fs_glm,
            'fs-glm-image': self._handle_fs_glm_image,
            'run-stats': self._handle_run_stats,
        }

    def run(self):
        """Dispatches the appropriate process based on user parameters."""
        handler = self.process_handlers.get(self.params.process)
        if handler:
            self.logger.info(f"Running process: {self.params.process}")
            handler()
        else:
            self.logger.error(f"Unknown process: {self.params.process}")
            sys.exit(1)

    def _handle_ready(self):
        """Checks if the environment is ready."""
        self.dist_manager.check_ready()

    def _handle_run(self):
        """Runs the main project pipeline."""
        self.proj_manager.run()

    def _handle_classify(self):
        """
        Handles the first stage of classification: scanning source directories
        and creating an intermediate 'nimb_classified.json' file.
        """
        self.logger.info("Initiating source directory scan...")
        if not self.dist_manager.is_classify_ready():
            self.logger.error("Classification readiness check failed.")
            return

        # The manager now handles finding subjects internally
        self.classifier.generate_scan_report(update=True)

    def _handle_classify_2_bids(self):
        """
        Handles the second stage: converting scanned data to BIDS format
        using the 'nimb_classified.json' report.
        """
        self.logger.info("Initiating conversion to BIDS format...")
        self.classifier.convert_to_bids()

    def _handle_fs_get_stats(self):
        """Handles FreeSurfer stats extraction."""
        if self.dist_manager.is_ready_for_stats():
            PROCESSED_FS_DIR = self.dist_manager.prep_4fs_stats()
            if PROCESSED_FS_DIR:
                self.vars_local['PROCESSING']['processing_env'] = "tmux"
                dir_4stats = self.project_vars['STATS_PATHS']["STATS_HOME"]
                cmd = (f'{self.py_run_cmd} fs_stats2table.py -project {self.params.project} '
                       f'-stats_dir {dir_4stats} -dir_fs_stats {PROCESSED_FS_DIR}')
                cd_cmd = f"cd {os.path.join(self.NIMB_HOME, 'processing', 'freesurfer')}"
                self.scheduler.submit_4_processing(cmd, 'fs_stats', 'get_stats', cd_cmd)

    def _handle_fs_glm(self):
        """Handles FreeSurfer GLM analysis."""
        if self.dist_manager.is_ready_for_fs_glm():
            GLM_file_path, GLM_dir = distrib.prep_4fs_glm(fs_glm_dir,
                                                            fname_groups)
            FS_SUBJECTS_DIR = self.vars_local['FREESURFER']['SUBJECTS_DIR']
            DistributionReady(self.all_vars).fs_chk_fsaverage_ready(FS_SUBJECTS_DIR)
            if GLM_file_path and not self.all_vars.params.test:
                glmcontrast = self.all_vars.params.glmcontrast
                glmpermutations = self.all_vars.params.glmpermutations
                add_correct = ""
                glmcorrected = self.all_vars.params.glmcorrected
                if glmcorrected:
                    add_correct = f" -corrected"
                schedule_fsglm = Scheduler(self.vars_local)
                cd_cmd = f"cd {os.path.join(self.NIMB_HOME, 'processing', 'freesurfer')}"
                cmd = f'{self.py_run_cmd} fs_glm_runglm.py -project {self.project} -glm_dir {GLM_dir} -contrast {" ".join(glmcontrast)}{add_correct} -permutations {glmpermutations}'
                schedule_fsglm.submit_4_processing(cmd, 'fs_glm','run_glm', cd_cmd)
            else:
                print("    TESTING")

    def _handle_fs_glm_image(self):
        """Handles extraction of FS-GLM images."""
        if not "export_screen" in self.vars_local['FREESURFER']:
            print("PLEASE check that you can export your screen or you can run screen-based applications. \
                                This is necessary for Freeview and Tksurfer. \
                                Check the variable: export_screen in file {}".format(
                                    "credentials_path.py/nimb/local.json"))
        elif self.vars_local['FREESURFER']["export_screen"] == 0:
            print("ERROR!: Current environment is not ready to export screen.")
            print("    Provide a computer where the screen can be used")
            print("    to run FreeSurfer Freeview and tksurfer")
        if self.dist_manager.is_ready_for_fs_glm_image():
            print('before running the script, remember to source $FREESURFER_HOME')
            cmd = '{} fs_glm_extract_images.py -project {}'.format(self.py_run_cmd, self.project)
            cd_cmd = f"cd {os.path.join(self.NIMB_HOME, 'processing', 'freesurfer')}"
            self.schedule.submit_4_processing(cmd, 'fs_glm','extract_images', cd_cmd)

    def _handle_run_stats(self):
        """Handles running statistical analysis."""
        if self.dist_manager.is_ready_for_stats():
            fname_groups = DistributionHelper(self.all_vars).prep_4stats()
            if fname_groups:
                self.vars_local['PROCESSING']['processing_env']  = "tmux" #probably works with slurm, must be checked
                schedule = Scheduler(self.vars_local)
                step_stats = self.all_vars.params.step
                cd_cmd = f"cd {os.path.join(self.NIMB_HOME, 'stats')}"
                cmd = f'{self.py_run_cmd} stats_helper.py -project {self.project} -step {step_stats}'
                schedule.submit_4_processing(cmd, 'nimb_stats','run', cd_cmd)



def main():
    """
    Main function to run the NIMB application.
    """
    if sys.version_info < (3, 6):
        sys.stdout.write("NIMB requires Python 3.6 or higher.\n")
        sys.exit(1)

    try:
        all_vars = ConfigManager()
        app = NIMB(all_vars)
        app.run()
    except Exception as e:
        # A global exception handler
        print(f"FATAL: An unexpected error occurred: {e}", file=sys.stderr)
        # For debugging, you might want to re-raise the exception
        # raise
        sys.exit(1)


if __name__ == "__main__":
    main()

