# -*- coding: utf-8 -*-
"""
This script processes MRI data using the DIPY library for diffusion imaging analysis.
It performs fiber tracking, computes connectivity matrices, and extracts metrics
for regions of interest (ROIs) based on specified atlases.

Originally authored by:
- Emmanuelle Mazur-Laine (ROI-based, Desikan atlas, saving to CSV)
- Kim Pham Phuong (2nd version)
- Alexandru Hanganu (1st version, adjustments, automation, integration with NIMB)

Refactored for improved structure, readability, and modularity.
Key changes:
- Replaced prints with logging.
- Modularized methods for better separation of concerns.
- Used pathlib for path handling where appropriate.
- Improved error handling and configuration loading.
- Removed unused code and commented-out sections.
- Consistent naming conventions.
- Integrated with provided utilities, logger, and definitions.
"""

import os
import logging
from pathlib import Path
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.ndimage import binary_dilation
from dipy.data import get_fnames
from dipy.io.image import load_nifti
from dipy.io.gradients import read_bvals_bvecs
from dipy.core.gradients import gradient_table
from dipy.align.reslice import reslice
from dipy.reconst import shm
from dipy.reconst.csdeconv import ConstrainedSphericalDeconvModel, auto_response_ssst
from dipy.direction import peaks
from dipy.tracking import utils
from dipy.tracking.stopping_criterion import ThresholdStoppingCriterion
from dipy.tracking.local_tracking import LocalTracking
from dipy.tracking.streamline import Streamlines
from dipy.tracking.metrics import length

# Local imports from provided files
from distribution.utilities import load_json, save_json
from distribution.logger import Log
from distribution.distribution_definitions import DEFAULT
from processing.schedule_helper import Scheduler
from setup.get_vars import Get_Vars  # Assuming this is updated from zold.get_vars.py via setup.py integration

class DIPYProcessor:
    """
    Main class for running DIPY processing pipeline.
    Handles loading data, tracking fibers, computing connectivity, and saving metrics.
    """

    def __init__(self, all_vars):
        self.app = "dipy"
        self.all_vars = all_vars
        vars_local = all_vars.location_vars['local']
        self.nimb_tmp = vars_local['NIMB_PATHS']['NIMB_tmp']
        self.output_loc = vars_local['DIPY']['NIMB_PROCESSED']
        self.project = all_vars.params.project
        self.proj_vars = all_vars.projects[self.project]
        self.test = all_vars.params.test
        self.atlas = "desikan"  # Default to Desikan; can be overridden
        self.id_col = self.proj_vars['id_col']
        self.db_dp = {}
        self.logger = Log(self.nimb_tmp).logger  # Initialize logger
        self.logger.info(f"Initializing DIPYProcessor for project: {self.project}")
        self._load_atlas_labels()

    def _load_atlas_labels(self):
        """
        Loads atlas labels and creates a dictionary mapping label values to names.
        Supports Stanford, Desikan, and Destrieux atlases.
        """
        current_location = Path(__file__).parent.resolve()
        atlas_dir = current_location.parent / "atlases"  # Assuming atlases folder structure

        if self.atlas == "stanford":
            label_fname, label_file = get_fnames('stanford_labels'), 'label_info.txt'
        elif self.atlas == "desikan":
            label_fname = atlas_dir / "aparcaseg.nii.gz"
            label_file = atlas_dir / "FreeSurferColorLUT.txt"
        elif self.atlas == "destrieux":
            label_fname = atlas_dir / "aparc.a2009saseg.nii.gz"
            label_file = atlas_dir / "FreeSurferColorLUT.txt"
        else:
            raise ValueError(f"Unsupported atlas: {self.atlas}")

        self.labels_all = {}
        with open(label_file, "r") as f:
            for line in f:
                split_line = line.split()
                if split_line and split_line[0].isdigit():
                    label_id = int(split_line[0])
                    label_name = split_line[1] if self.atlas != "stanford" else split_line[2][2:-2]
                    self.labels_all[label_id] = label_name
        if self.atlas != "stanford":
            self.labels_all.pop(0, None)

        self.labels, self.labels_affine, self.labels_voxel_size = load_nifti(str(label_fname), return_voxsize=True)
        self.logger.info(f"Loaded atlas: {self.atlas} with {len(self.labels_all)} labels")

    def run(self):
        """
        Main entry point for the processing pipeline.
        Handles test mode or processing multiple subjects.
        """
        if self.test:
            self.logger.info("Test mode activated")
            self._process_test_subject()
        else:
            self._load_subjects()
            for self.subj_id in self.db_dp:
                self._load_dwi_data()
                self._adjust_labels_to_data()
                self._perform_connectivity_analysis()
        self.logger.info("Processing completed")

    def _process_test_subject(self):
        """Loads and processes the Stanford HARDI test dataset."""
        self.subj_id = "stanford_hardi"
        hardi_fname, hardi_bval_fname, hardi_bvec_fname = get_fnames('stanford_hardi')
        self.data, self.affine, _ = load_nifti(hardi_fname, return_img=True)
        bvals, bvecs = read_bvals_bvecs(hardi_bval_fname, hardi_bvec_fname)
        self.gtab = gradient_table(bvals, bvecs)
        self._adjust_labels_to_data()
        self._perform_connectivity_analysis()

    def _load_subjects(self):
        """Loads subjects from the new_subjects JSON file."""
        new_subjects_f_name = DEFAULT.app_files[self.app]["new_subjects"]
        new_subjects_f_path = os.path.join(self.nimb_tmp, new_subjects_f_name)
        if os.path.isfile(new_subjects_f_path):
            self.db_dp = load_json(new_subjects_f_path)
            self.logger.info(f"Loaded {len(self.db_dp)} subjects from {new_subjects_f_path}")
        else:
            self.logger.error(f"Subjects file missing: {new_subjects_f_path}")
            raise FileNotFoundError(f"Subjects file not found: {new_subjects_f_path}")

    def _load_dwi_data(self):
        """Loads DWI data for the current subject."""
        self.logger.info(f"Loading DWI data for subject: {self.subj_id}")
        dwi_path = self.db_dp[self.subj_id]["dwi"]["dwi"][0]
        bval_path = self.db_dp[self.subj_id]["dwi"]["bval"][0]
        bvec_path = self.db_dp[self.subj_id]["dwi"]["bvec"][0]
        self.data, self.affine, _ = load_nifti(dwi_path, return_img=True)
        bvals, bvecs = read_bvals_bvecs(bval_path, bvec_path)
        self.gtab = gradient_table(bvals, bvecs)
        self._save_plot(self.data[:, :, self.data.shape[2] // 2, 0].T, f"{self.subj_id}_data")

    def _adjust_labels_to_data(self):
        """Reslices labels to match data dimensions if necessary."""
        if self.data.shape[:3] != self.labels.shape:
            self.logger.warning("Data and labels have different dimensions. Reslicing labels.")
            new_voxel_size = (
                self.labels.shape[0] * self.labels_voxel_size[0] / self.data.shape[0],
                self.labels.shape[1] * self.labels_voxel_size[1] / self.data.shape[1],
                self.labels.shape[2] * self.labels_voxel_size[2] / self.data.shape[2]
            )
            self.labels, self.labels_affine = reslice(self.labels, self.labels_affine, self.labels_voxel_size, new_voxel_size)

    def _perform_connectivity_analysis(self):
        """
        Performs the core connectivity analysis: fiber tracking, matrix computation, and metrics extraction.
        """
        self.logger.info(f"Starting connectivity analysis for subject: {self.subj_id}")

        # Step 1: Model fitting and direction getting
        response, _ = auto_response_ssst(self.gtab, self.data, roi_radii=10, fa_thr=0.7)
        csd_model = ConstrainedSphericalDeconvModel(self.gtab, response, sh_order=6)
        csd_fit = csd_model.fit(self.data, mask=self.white_matter)

        gfa = csd_fit.gfa
        stopping_criterion = ThresholdStoppingCriterion(gfa, 0.25)

        csamodel = shm.CsaOdfModel(self.gtab, sh_order=6)
        csapeaks = peaks.peaks_from_model(model=csamodel, data=self.data, sphere=peaks.default_sphere,
                                          relative_peak_threshold=0.8, min_separation_angle=45,
                                          mask=self.white_matter)

        # Step 2: Seed generation
        if self.atlas == "stanford":
            self.white_matter = binary_dilation((self.labels == 1) | (self.labels == 2))
        elif self.atlas == "desikan":
            self.white_matter = binary_dilation((self.labels == 41) | (self.labels == 2))
        else:
            raise ValueError(f"White matter definition not supported for atlas: {self.atlas}")

        seeds = utils.seeds_from_mask(self.white_matter, self.affine, density=2)

        # Step 3: Fiber tracking
        streamline_generator = LocalTracking(csapeaks, stopping_criterion, seeds, affine=self.affine, step_size=0.5)
        streamlines = Streamlines(streamline_generator)
        if self.test:
            from dipy.io.stateful_tractogram import Space, StatefulTractogram
            from dipy.io.streamline import save_tractogram
            sft = StatefulTractogram(streamlines, hardi_img, Space.RASMM)
            save_tractogram(sft, f"{self.subj_id}_tractogram.trk")

        # Step 4: Connectivity matrix and grouping
        M, grouping = utils.connectivity_matrix(streamlines, self.affine, self.labels.astype(np.uint8),
                                                return_mapping=True, mapping_as_streamlines=True)
        self._save_plot(np.log1p(M), f"{self.subj_id}_connectivity")

        # Step 5: Save metrics
        self._save_metrics(streamlines, grouping)

    def _save_metrics(self, streamlines, grouping):
        """Computes and saves metrics for ROIs and ROI pairs to CSV."""
        df = pd.DataFrame()
        max_streamline_count = 0

        # Metrics per single ROI
        for roi in self.labels_all:
            roi_slice = (self.labels == roi)
            target_streamlines = utils.target(streamlines, self.affine, roi_slice)
            roi_streamlines = Streamlines(target_streamlines)
            metrics_dict = self._compute_metrics(roi_streamlines)
            df = self._populate_dataframe(df, metrics_dict, [self.labels_all[roi]] * len(metrics_dict))
            max_streamline_count = max(max_streamline_count, len(roi_streamlines))

            # Metrics per ROI pair
            for comb in self._get_roi_combinations():
                if roi in comb:
                    roi1, roi2 = comb
                    pair_key = f"{self.labels_all[roi1]}_{self.labels_all[roi2]}"
                    pair_streamlines = Streamlines(grouping.get((roi1, roi2), []))
                    if len(pair_streamlines) > 0:
                        metrics_dict = self._compute_metrics(pair_streamlines)
                        df = self._populate_dataframe(df, metrics_dict, [pair_key] * len(metrics_dict))
                    max_streamline_count = max(max_streamline_count, len(pair_streamlines))

        # Set multi-index and save
        index = pd.MultiIndex.from_tuples([(self.subj_id, i) for i in range(1, max_streamline_count + 1)],
                                          names=[self.id_col, "Streamlines"])
        df = df.set_index(index)
        output_path = os.path.join(self.output_loc, f"{self.subj_id}_all_streamlines_metrics.csv")
        df.to_csv(output_path)
        self.logger.info(f"Saved metrics to: {output_path}")

    def _compute_metrics(self, streamlines):
        """Computes metrics for a set of streamlines (count, mean/std/min/max length)."""
        if not streamlines:
            return {}
        lengths = [length(s) for s in streamlines]
        return {
            "streamline_count": len(streamlines),
            "mean_length": np.mean(lengths),
            "std_length": np.std(lengths),
            "min_length": np.min(lengths),
            "max_length": np.max(lengths)
        }

    def _populate_dataframe(self, df, metrics_dict, roi_list):
        """Populates a DataFrame with metrics for given ROIs."""
        columns = pd.MultiIndex.from_tuples(list(zip(roi_list, metrics_dict.keys())), names=["ROI", "Metrics"])
        df_values = pd.DataFrame([list(metrics_dict.values())])
        new_df = pd.DataFrame(df_values.values, columns=columns)
        return pd.concat([df, new_df], axis=1)

    def _get_roi_combinations(self):
        """Generates unique ordered pairs of ROIs."""
        combinations = []
        labels = list(self.labels_all.keys())
        for i, roi1 in enumerate(labels):
            for roi2 in labels[i + 1:]:
                combinations.append([roi1, roi2])
                combinations.append([roi2, roi1])
        return combinations

    def _save_plot(self, data, filename):
        """Saves a matplotlib plot to file."""
        plt.imshow(data, origin="lower")
        plt.savefig(f"{filename}.png")
        plt.close()

def get_parameters(projects):
    """Parses command-line arguments for project selection and test mode."""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-project", required=False, default=projects[0], choices=projects,
                        help="Project name from projects.json")
    parser.add_argument("-test", action='store_true', help="Run in test mode")
    return parser.parse_args()

if __name__ == "__main__":
    # Load variables using Get_Vars (integrated from setup.py/zold.get_vars.py)
    all_vars = Get_Vars()  # Assuming Get_Vars handles params from args
    project_ids = all_vars.get_projects_ids()
    params = get_parameters(project_ids)
    all_vars = Get_Vars(params)  # Re-init with params

    # Run the processor
    processor = DIPYProcessor(all_vars)
    processor.run()