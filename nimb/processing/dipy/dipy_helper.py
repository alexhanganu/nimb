# -*- coding: utf-8 -*-
"""
This module contains the core scientific logic for the DIPY processing pipeline.
"""
import os
import numpy as np
import matplotlib.pyplot as plt

from dipy.io.image import load_nifti
from dipy.io.gradients import read_bvals_bvecs
from dipy.core.gradients import gradient_table
from dipy.denoise.patch2self import patch2self
from dipy.reconst.dti import TensorModel
from dipy.reconst.csdeconv import auto_response_ssst
from dipy.reconst.shm import CsaOdfModel
from dipy.data import get_sphere
from dipy.direction import DeterministicMaximumDirectionGetter
from dipy.tracking.stopping_criterion import ThresholdStoppingCriterion
from dipy.tracking.local_tracking import LocalTracking
from dipy.tracking.streamline import Streamlines
from dipy.tracking import utils
from dipy.viz import window, actor

class DipyHelper:
    """
    Handles the computational steps of the DIPY pipeline.
    """
    def __init__(self, dwi_path, bval_path, bvec_path, output_dir, subject_id):
        self.dwi_path = dwi_path
        self.bval_path = bval_path
        self.bvec_path = bvec_path
        self.output_dir = output_dir
        self.subject_id = subject_id

        # Load data
        self.data, self.affine = load_nifti(self.dwi_path)
        bvals, bvecs = read_bvals_bvecs(self.bval_path, self.bvec_path)
        self.gtab = gradient_table(bvals, bvecs)

        self.denoised_data = None
        self.tenfit = None
        self.streamlines = None

    def run_denoising(self):
        """Applies patch2self denoising to the DWI data."""
        self.denoised_data = patch2self(self.data, self.gtab.bvals)
    
    def run_dti_fitting(self):
        """Fits a DTI model to the denoised data."""
        if self.denoised_data is None:
            raise RuntimeError("Denoising must be run before DTI fitting.")
        
        tenmodel = TensorModel(self.gtab)
        self.tenfit = tenmodel.fit(self.denoised_data)

    def run_streamline_extraction(self):
        """Extracts streamlines using deterministic tracking."""
        if self.tenfit is None:
            raise RuntimeError("DTI fitting must be run before streamline extraction.")
            
        response, _ = auto_response_ssst(self.gtab, self.denoised_data, roi_radii=10, fa_thr=0.7)
        csa_model = CsaOdfModel(self.gtab, sh_order=6)
        sphere = get_sphere('symmetric724')
        det_dg = DeterministicMaximumDirectionGetter.from_shcoeff(
            csa_model.fit(self.denoised_data).shm_coeff,
            max_angle=30.,
            sphere=sphere
        )
        
        stopping_criterion = ThresholdStoppingCriterion(self.tenfit.fa, .2)
        seeds = utils.seeds_from_mask(self.tenfit.fa > 0.3, self.affine, density=1)
        
        streamline_generator = LocalTracking(
            det_dg,
            stopping_criterion,
            seeds,
            self.affine,
            step_size=.5
        )
        self.streamlines = Streamlines(streamline_generator)

    def run_connectivity_matrix(self):
        """Generates a connectivity matrix from the streamlines."""
        if self.streamlines is None:
            raise RuntimeError("Streamline extraction must be run before connectivity matrix generation.")
        
        # This requires a label/atlas file, which needs to be configured.
        # For now, we will just save the streamlines.
        # In a full implementation, you would load an atlas Nifti file here.
        # e.g., labels, _ = load_nifti('path_to_atlas.nii.gz')
        # M, _ = utils.connectivity_matrix(self.streamlines, self.affine, labels, return_mapping=False)
        
        # For now, let's just visualize and save the streamlines
        if window.have_fury:
            scene = window.Scene()
            streamlines_actor = actor.line(self.streamlines)
            scene.add(streamlines_actor)
            
            output_path = os.path.join(self.output_dir, f"{self.subject_id}_streamlines.png")
            window.record(scene, out_path=output_path, size=(800, 800))
