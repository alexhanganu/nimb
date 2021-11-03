# %% initiator for dipy pipeline
'''
adjusted: Alexandru Hanganu 20211001:
1st version: Kim Pham Phuong, 20202026
'''

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dipy.data import get_fnames
from dipy.io.image import load_nifti_data, load_nifti, save_nifti
from dipy.io.gradients import read_bvals_bvecs
from dipy.core.gradients import gradient_table
from scipy.ndimage.morphology import binary_dilation
from dipy.reconst import shm
from dipy.direction import peaks
from dipy.tracking import utils
from dipy.tracking.stopping_criterion import BinaryStoppingCriterion
from dipy.tracking.local_tracking import LocalTracking
from dipy.tracking.streamline import Streamlines
from dipy.tracking.metrics import length
from dipy.segment.mask import median_otsu


class RUNProcessingDIPY:

    def __init__(self, all_vars):
        self.app        = "dipy"
        self.all_vars   = all_vars
        self.project    = all_vars.params.project
        vars_local      = all_vars.location_vars['local']
        self.NIMB_tmp   = vars_local['NIMB_PATHS']['NIMB_tmp']
        self.output_loc = vars_local['NIMB_PATHS']['NIMB_PROCESSED_DIPY']
        self.db_dp      = dict()
        self.test       = all_vars.params.test

        self.run()


    def run(self):
        label_fname = get_fnames('stanford_labels')
        self.labels = load_nifti_data(label_fname)
        """
        labels are the image aparc-reduced.nii.gz, which is a modified version
        of FreeSurfer label map aparc+aseg.mgz.
        The corpus callosum region is a combination of FreeSurfer labels 251-255
        Remaining FreeSurfer labels were re-mapped and reduced
        so that they lie between 0 and 88.
        To see the FreeSurfer region, label and name, represented by each value
        see label_info.txt in ~/.dipy/stanford_hardi.
        """
        csapeaks = None
        if self.test:
            print(f"{LogLVL.lvl1}testing is activated")
            gtab = self.run_test_subject()
            self.run_connectivity_analysis(gtab)
        else:
            self.get_subjects()
            for self.subj_id in self.db_dp:
                gtab = self.get_dwi_data()
                self.run_connectivity_analysis(gtab)


    def get_subjects(self):
        new_subjects_f_name = DEFAULT.app_files[self.app]["new_subjects"]
        new_subjects_f_path = os.path.join(self.NIMB_tmp, new_subjects_f_name)
        if os.path.isfile(new_subjects_f_path):
            print(f'{LogLVL.lvl1}reading new subjects to process')
            new_subj = load_json(new_subjects_f_path)
            self.db_dp = new_subj
        else:
            print(f'{LogLVL.lvl1}ERR: file with subjects is MISSING')


    def run_connectivity_analysis(self, gtab):
        print(f'{LogLVL.lvl1}connectivity analysis with stanford atlas, is being performed')
        # Get the label from standfort atlas
        csapeaks, white_matter  = self.get_fiber_direction(gtab, self.data)
        if csapeaks:
            print("ok for csapeaks")
            self.make_streamlines(csapeaks, white_matter)
            # self.create_mask()
            # csapeaks  = self.get_fiber_direction(gtab, self.b0_mask)
            # csd_peaks = self.make_csd()
            # self.make_tensor()
            # self.make_streamlines_random()


    def run_test_subject(self):
        self.subj_id = "stanford_hardi"
        hardi_fname, hardi_bval_fname, hardi_bvec_fname = get_fnames('stanford_hardi')
        self.data, affine, hardi_img = load_nifti(hardi_fname, return_img=True)
        bvals, bvecs = read_bvals_bvecs(hardi_bval_fname, hardi_bvec_fname)
        gtab = gradient_table(bvals, bvecs)
        return gtab


    def get_dwi_data(self):
        print(f"{LogLVL.lvl2}subject: {self.subj_id}")
        self.data, affine, img = load_nifti(self.db_dp[self.subj_id]["dwi"]["dwi"][0],
                                            return_img=True)
        bvals, bvecs = read_bvals_bvecs(self.db_dp[self.subj_id]["dwi"]["bval"][0],
                                        self.db_dp[self.subj_id]["dwi"]["bvec"][0])
                                        #f_name.bval; f_name.bvec
        gtab = gradient_table(bvals, bvecs)
        self.save_plot(self.data[:,:,self.data.shape[2]//2, 0].T,
                        f"{self.subj_id}_data")
        return gtab


    def get_fiber_direction(self, gtab, data):
        # Getting fiber direction
        csamodel     = shm.CsaOdfModel(gtab, 6)
        white_matter = binary_dilation((self.labels == 1) | (self.labels == 2))
        if data.shape[:3] == white_matter.shape:
            csapeaks     = peaks.peaks_from_model(model=csamodel,
                                              data=data,
                                              sphere=peaks.default_sphere,
                                              relative_peak_threshold=.8,
                                              min_separation_angle=45,
                                              mask=white_matter)
        else:
            print(f"{LogLVL.lvl1}ERR: dimensions are different:")
            print(f"{LogLVL.lvl2} data shape:         {data.shape}")
            print(f"{LogLVL.lvl2} white matter shape: {white_matter.shape}")
            print(f"{LogLVL.lvl1}ERR: cannot continue")
            csapeaks = None
        return csapeaks, white_matter


    def create_mask(self):
        # CREATE MASK
        # Cropp the mask and image
        # https://dipy.org/documentation/1.0.0./examples_built/brain_extraction_dwi/
        # vol_idx: list of volumes will be masked - of axis=3 of a 4D input_volume
        #b0_mask, mask = median_otsu(data,gtab.b0s_mask,3,1, autocrop=True)
        self.b0_mask, mask = median_otsu(self.data,
                                    vol_idx=range(self.data.shape[3]), 
                                    median_radius=3,
                                    numpass=1,
                                    autocrop=True,
                                    dilate=2)
        self.save_plot(self.b0_mask[:,:,self.b0_mask.shape[2]//2, 0].T,
                        f"{self.subj_id}_b0_mask")
        self.save_plot(mask[:,:,self.b0_mask.shape[2]//2].T,
                        f"{self.subj_id}_mask")


    def make_csd(self):
        """
            CSD
            https://dipy.org/documentation/0.16.0./examples_built/tracking_quick_start/
            https://dipy.org/documentation/0.16.0./examples_built/introduction_to_basic_tracking/
            Another kind of tracking : https://dipy.org/documentation/1.2.0./examples_built/tracking_introduction_eudx/#example-tracking-introduction-eudx
                https://github.com/dipy/dipy/blob/master/doc/examples/tracking_deterministic.py
        """


        #For the Constrained Spherical Deconvolution we need to estimate the response function and create a model.
        response, ratio = auto_response(gtab, self.data, roi_radius=10, fa_thr=0.7)
        csd_model = ConstrainedSphericalDeconvModel(gtab, response)

        # Using peaks
        sphere = get_sphere('symmetric724')
        csd_peaks = peaks.peaks_from_model(model=csd_model,
                                     data=self.b0_mask,
                                     sphere=sphere, #peaks.default_sphere,
                                     mask=mask,
                                     relative_peak_threshold=.5,
                                     min_separation_angle=25,
                                     parallel=True)
        self.save_plot(csd_peaks.gfa[:,:,35].T, f"{self.subj_id}csd")
        return csd_peaks


    def make_tensor(self):
        # ==> The GFA values of these FODs don’t classify gray matter and white matter well

        #    View csd_peaks

        # from dipy.viz import window, actor, has_fury, colormap as cmap

        # interactive = True
        # if has_fury:
        #     scene = window.Scene()
        #     scene.add(actor.peak_slicer(csd_peaks.peak_dirs,
        #                                 csd_peaks.peak_values,
        #                                 colors=None))

        #     window.record(scene, out_path='csd_direction_field.png', size=(900, 900))

        #     if interactive:
        #         window.show(scene, size=(800, 800))
        ##  Restrict the fiber tracking to areas with good directionality information using tensor model
        # - with cropped data
        from dipy.reconst.dti import TensorModel
        tensor_model = TensorModel(gtab)
        tensor_fit = tensor_model.fit(self.b0_mask)

        fa = tensor_fit.fa

        # check image
        self.save_plot(fa2[:,:,35].T, f"{self.subj_id}tensor")


    def make_streamlines(self, csapeaks, white_matter):
        affine = np.eye(4)
        seeds = utils.seeds_from_mask(white_matter, affine, density=1)
        stopping_criterion = BinaryStoppingCriterion(white_matter)
        streamline_generator = LocalTracking(csapeaks, stopping_criterion, seeds,
                                             affine=affine, step_size=0.5)
        streamlines = Streamlines(streamline_generator)
        M, grouping = utils.connectivity_matrix(streamlines, affine,
                                                self.labels.astype(np.uint8),
                                                return_mapping=True,
                                                mapping_as_streamlines=True)
        self.save_plot(np.log1p(M),
                    f"{self.subj_id}_connectivity_all_rois")
        self.save_metrics(streamlines)

        """
        https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3931231/
        streamlines found to intersect with the yellow mask in the
        corpus callosum (CC) using target.
        Then we used these streamlines
        to investigate which areas of the cortex are connected using a
        modified aparc+aseg.mgz label map created by FreeSurfer
        (Fischl, 2012) of 89 regions.
        https://dipy.org/documentation/1.0.0./examples_built/segment_clustering_metrics/
        """
        # # Using streamlines per ROI
        # # Corpus callosum
        # cc_slice = self.labels == 2
        # cc_streamlines    = utils.target(streamlines, affine, cc_slice)
        # cc_streamlines    = Streamlines(cc_streamlines)
        # M_cc, grouping_cc = utils.connectivity_matrix(cc_streamlines, affine,
        #                                             self.labels.astype(np.uint8),
        #                                             return_mapping=True,
        #                                             mapping_as_streamlines=True)
        # self.save_plot(np.log1p(M_cc),
        #             f"{self.subj_id}_corpuscallosum_connectivity")

        # # Left_Right_SuperiorFrontal
        # lr_superiorfrontal_track = grouping[11, 54]
        # shape     = labels.shape
        # dm        = utils.density_map(lr_superiorfrontal_track, affine, shape)
        # lr_sf_trk = Streamlines(lr_superiorfrontal_track)


    def save_metrics(self, streamlines):
        """
        script to extract metrics
        and save to a tabular file
        """
        # saving lengths of streamlines
        lengths = [length(s) for s in streamlines]
        lengths = np.array(lengths)
        average_length = lengths.mean()
        standard_deviation_lengths = lengths.std()

        """
        spline for spline interpolation
        centre_of_mass
        mean_curvature,
        mean_orientation
        the frenet_serret framework for curvature
        torsion calculations along a streamline.
        https://dipy.org/documentation/1.4.1./reference/dipy.tracking/
        https://dipy.org/documentation/1.1.1./reference/dipy.tracking/
        """
        # Saving to tabular file

        df = pd.DataFrame(lengths).T
        df["average_length"] = average_length
        df["std"] = standard_deviation_lengths
        df.to_csv(os.path.join(self.output_loc, "lengths.csv"))



        # from dipy.segment.metric import AveragePointwiseEuclideanMetric
        # from dipy.segment.clustering import QuickBundles
        # # Create the instance of `AveragePointwiseEuclideanMetric` to use.
        # metric = AveragePointwiseEuclideanMetric()
        # qb = QuickBundles(threshold=10., metric=metric)
        # clusters = qb.cluster(streamlines)
        """
        chk:
        https://nipype.readthedocs.io/en/latest/users/examples/dmri_connectivity_advanced.html
        """


    def save_plot(self, data, f_name):
        # fig = plt.figure(figsize=(11,10))
        plt.subplot(1,2,1)
        plt.pcolor(data, cmap = 'gray') #interpolation='None', cmap='RdYlBu_r'
        # plt.yticks(range(len(rois_labels)), rois_labels[0:]);
        # plt.xticks(range(len(rois_labels)), rois_labels[0:], rotation=90);
        plt.title(f'Title')
        plt.colorbar();
        img_name = os.path.join(self.output_loc, f_name)
        plt.savefig(img_name)
        plt.close()


    # def make_streamlines_random(self):
    #     # Generate streamlines
    #     # Define the “seed” (begin) the fiber tracking
    #     from dipy.direction import ProbabilisticDirectionGetter # slower

    #     self.labels == 2
    #     affine = np.eye(4)
    #     seeds = utils.random_seeds_from_mask(fa > 0.3, seeds_count=1, affine=affine)
    #     stopping_criterion_1  = ThresholdStoppingCriterion(fa, .1)
    #     stopping_criterion_25 = ThresholdStoppingCriterion(fa, .25)


    #     csd_fit = csd_model.fit(self.b0_mask, mask)
    #     prob_dg = ProbabilisticDirectionGetter.from_shcoeff(csd_fit.shm_coeff,
    #                                                         max_angle=30.,
    #                                                         sphere=peaks.default_sphere)
    #     # detmax_dg = DeterministicMaximumDirectionGetter.from_shcoeff(
    #     #     csd_fit.shm_coeff, max_angle=30., sphere=peaks.default_sphere)

    #     streamline_generator2 = LocalTracking(csd_peaks, stopping_criterion_1,
    #                                          seeds, affine=affine, step_size=0.5) #faster, less exact
    #     streamline_generator3 = LocalTracking(prob_dg, stopping_criterion_25,
    #                                          seeds, affine=affine,
    #                                          step_size=0.5, max_cross=1)

    #     streamlines2 = Streamlines(streamline_generator2)
    #     streamlines3 = Streamlines(streamline_generator3)

        # # View streamline


        # interactive = False
        # if has_fury:
        #     # Prepare the display objects.
        #     color = cmap.line_colors(streamlines2)

        #     streamlines_actor = actor.line(streamlines2,
        #                                    cmap.line_colors(streamlines2))

        #     # Create the 3D display.
        #     scene = window.Scene()
        #     scene.add(streamlines_actor)

        #     window.record(scene, out_path='streamline_1.png', size=(800, 800))
        #     if interactive:
        #         window.show(scene)

        # interactive = True
        # if has_fury:
        #     # Prepare the display objects.
        #     color = cmap.line_colors(streamlines3)

        #     streamlines_actor = actor.line(streamlines3,
        #                                    cmap.line_colors(streamlines3))

        #     # Create the 3D display.
        #     scene = window.Scene()
        #     scene.add(streamlines_actor)

        #     window.record(scene, out_path='streamline_2.png', size=(800, 800))
        #     if interactive:
        #         window.show(scene)

        # M2, grouping = utils.connectivity_matrix(streamlines2, affine,
        #                                         self.labels.astype(np.uint8),
        #                                         inclusive=True,
        #                                         return_mapping=True,
        #                                         mapping_as_streamlines=True)
        # self.save_plot(np.log1p(M2), f"{self.subj_id}_streamlines_threshold1")

        # M3, grouping = utils.connectivity_matrix(streamlines3, affine,
        #                                         self.labels.astype(np.uint8),
        #                                         inclusive=True,
        #                                         return_mapping=True,
        #                                         mapping_as_streamlines=True)
        # self.save_plot(np.log1p(M3), f"{self.subj_id}_streamlines_threshold.25")




def get_parameters(projects):
    """get parameters for nimb"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-project", required=False,
        default=projects[0],
        choices = projects,
        help="names of projects located in credentials_path.py/nimb/projects.json -> PROJECTS",
    )

    parser.add_argument(
        "-test", required=False,
        action='store_true',
        help="if used a test will be run initially on the default subject",
    )

    params = parser.parse_args()
    return params


if __name__ == "__main__":

    import argparse
    import sys
    try:
        from pathlib import Path
    except ImportError as e:
        print('please install pathlib')
        sys.exit(e)

    top = Path(__file__).resolve().parents[2]
    sys.path.append(str(top))

    from setup.get_vars import Get_Vars
    from distribution.logger import Log, LogLVL
    from distribution.utilities import load_json, save_json
    from distribution.distribution_definitions import DEFAULT
    from processing.schedule_helper import Scheduler, get_jobs_status
    from processing.nilearn import nl_helper

    project_ids = Get_Vars().get_projects_ids()
    params      = get_parameters(project_ids)
    project     = params.project
    all_vars    = Get_Vars(params)

    RUNProcessingDIPY(all_vars)
