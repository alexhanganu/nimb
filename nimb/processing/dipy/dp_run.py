# %% initiator for dipy pipeline
'''
adjusted: Alexandru Hanganu 20211001:
1st version: Kim Pham Phuong, 20202026
'''

import os

import numpy as np
import matplotlib.pyplot as plt
from dipy.data import get_fnames
from dipy.io.image import load_nifti_data, load_nifti, save_nifti
from dipy.segment.mask import median_otsu
from dipy.io.gradients import read_bvals_bvecs
from dipy.core.gradients import gradient_table
from scipy.ndimage.morphology import binary_dilation
from dipy.reconst import shm
from dipy.direction import peaks
from dipy.tracking import utils
from dipy.tracking.local_tracking import LocalTracking
from dipy.tracking.stopping_criterion import BinaryStoppingCriterion
from dipy.tracking.streamline import Streamlines        
        

class RUNProcessingDIPY:

    def __init__(self, all_vars):
        self.app        = "dipy"
        self.all_vars   = all_vars
        self.project    = all_vars.params.project
        vars_local      = all_vars.location_vars['local']
        self.NIMB_tmp   = vars_local['NIMB_PATHS']['NIMB_tmp']
        self.output_loc = vars_local['NIMB_PATHS']['NIMB_PROCESSED_DIPY']
        self.db_dp      = dict()

        self.get_subjects()
        self.run_connectivity_analysis()


    def get_subjects(self):
        new_subjects_f_name = DEFAULT.app_files[self.app]["new_subjects"]
        new_subjects_f_path = os.path.join(self.NIMB_tmp, new_subjects_f_name)
        if os.path.isfile(new_subjects_f_path):
            print(f'{LogLVL.lvl1}reading new subjects to process')
            new_subj = load_json(new_subjects_f_path)
            self.db_dp = new_subj
        else:
            print(f'{LogLVL.lvl1}ERR: file with subjects is MISSING')


    def run_connectivity_analysis(self):
        print(f'{LogLVL.lvl1}performing connectivity analysis with stanford atlas')
        # Get the label from standfort atlas
        label_fname = get_fnames('stanford_labels')
        self.labels = load_nifti_data(label_fname)
        for subj_id in self.db_dp:
            gtab = self.get_dwi_data(subj_id)
            self.save_plot(self.data[:,:,self.data.shape[2]//2, 0].T,
                            "data")
            self.create_mask()
            csapeaks  = self.get_fiber_direction(gtab)
            csd_peaks = self.make_csd()
            self.make_tensor()
            self.make_streamlines()


    def get_dwi_data(self, subj_id):
        print(f"{LogLVL.lvl2}subject: {subj_id}")
        self.data, affine, img = load_nifti(self.db_dp[subj_id]["dwi"]["dwi"][0],
                                        return_img=True)
        bvals, bvecs = read_bvals_bvecs(self.db_dp[subj_id]["dwi"]["bval"][0],
                                        self.db_dp[subj_id]["dwi"]["bvec"][0]) #f_name.bval; f_name.bvec
        gtab = gradient_table(bvals, bvecs)
        return gtab


    def get_fiber_direction(self, gtab):
        # Getting fiber direction
        #     With cropped data
        white_matter = binary_dilation((self.labels == 1) | (self.labels == 2))
        csamodel     = shm.CsaOdfModel(gtab, 6)
        csapeaks     = peaks.peaks_from_model(model=csamodel,
                                          data=self.data,
                                          sphere=peaks.default_sphere,
                                          relative_peak_threshold=.8,
                                          min_separation_angle=45,
                                          mask=white_matter)
        # csapeaks     = peaks.peaks_from_model(model=csamodel,
        #                                   data=self.b0_mask,
        #                                   sphere=peaks.default_sphere,
        #                                   relative_peak_threshold=.8,
        #                                   min_separation_angle=45,
        #                                   mask=white_matter)
        return csapeaks



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
                        "b0_mask")
        self.save_plot(mask[:,:,self.b0_mask.shape[2]//2].T,
                        "mask")


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
        self.save_plot(csd_peaks.gfa[:,:,35].T, "csd")
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
        self.save_plot(fa2[:,:,35].T, "tensor")


    def make_streamlines(self):            
        # Generate streamlines

        #    Using GFA of peaks

        # Define the “seed” (begin) the fiber tracking
        seeds = utils.random_seeds_from_mask(fa > 0.3, seeds_count=1, affine=np.eye(4))

        # faster but less exact (by visulizing)
        stopping_criterion = ThresholdStoppingCriterion(fa, .1)

        streamline_generator1 = LocalTracking(csd_peaks, stopping_criterion,
                                             seeds, affine=np.eye(4),
                                             step_size=0.5)
        streamlines1 = Streamlines(streamline_generator1)

        interactive = False
        if has_fury:
            # Prepare the display objects.
            color = cmap.line_colors(streamlines1)

            streamlines_actor = actor.line(streamlines1,
                                           cmap.line_colors(streamlines1))

            # Create the 3D display.
            scene = window.Scene()
            scene.add(streamlines_actor)

            window.record(scene, out_path='streamline_1.png', size=(800, 800))
            if interactive:
                window.show(scene)
                
        # Using ProbabilisticDirectionGetter
        # slower
        from dipy.direction import ProbabilisticDirectionGetter

        stopping_criterion = ThresholdStoppingCriterion(fa, .25)
        csd_fit = csd_model.fit(self.b0_mask, mask)
        prob_dg = ProbabilisticDirectionGetter.from_shcoeff(csd_fit.shm_coeff,
                                                            max_angle=30.,
                                                            sphere=peaks.default_sphere)
        # detmax_dg = DeterministicMaximumDirectionGetter.from_shcoeff(
        #     csd_fit.shm_coeff, max_angle=30., sphere=peaks.default_sphere)

        streamline_generator2 = LocalTracking(prob_dg, stopping_criterion,
                                             seeds, affine=np.eye(4),
                                             step_size=0.5, max_cross=1)
        streamlines2 = Streamlines(streamline_generator2)

        # View streamline
        interactive = True
        if has_fury:
            # Prepare the display objects.
            color = cmap.line_colors(streamlines2)

            streamlines_actor = actor.line(streamlines2,
                                           cmap.line_colors(streamlines2))

            # Create the 3D display.
            scene = window.Scene()
            scene.add(streamlines_actor)

            window.record(scene, out_path='streamline_2.png', size=(800, 800))
            if interactive:
                window.show(scene)
                
        # it runs very slow -> should try other method 
        affine = np.eye(4)
        M, grouping = utils.connectivity_matrix(streamlines2, affine,
                                                labels.astype(np.uint8),
                                                inclusive=True,
                                                return_mapping=True,
                                                mapping_as_streamlines=True)        

        # -> How to evaluate if this matrix is generated correctly ?

        import numpy as np
        import matplotlib.pyplot as plt
        plt.imshow(np.log1p(M), interpolation='nearest')
        # plt.savefig("connectivity.png")


        fig = plt.figure(figsize=(11,10))
        M[:3, :] = 0
        M[:, :3] = 0
        plt.imshow(np.arctanh(M), interpolation='None', cmap='RdYlBu_r')
        plt.title('Parcellation correlation matrix')
        plt.colorbar();


    def save_plot(self, data, f_name):
        plt.subplot(1,2,1)
        plt.pcolor(data, cmap = 'gray')
        # plt.yticks(range(len(rois_labels)), rois_labels[0:]);
        # plt.xticks(range(len(rois_labels)), rois_labels[0:], rotation=90);
        plt.title(f'Title')
        plt.colorbar();
        img_name = os.path.join(self.output_loc, f_name)
        plt.savefig(img_name)
        plt.close()


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
