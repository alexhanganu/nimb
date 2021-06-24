# %% initiator for dipy pipeline
'''
Kim Pham Phuong, 20202026

dipy_sample_conn.ipynb: image donnée par Dipy et l'atlas Stanford, connectivité.
Dipy_apply_test.ipynb: appliquer sur image sur Cedar. Le label des images et la transformation des dimension - ne fonctionne pas.

dipy_apply_test2: matrice de connectivité utilisant Stanford atlas mais aucune connection des ROIs.
'''


import numpy as np
import matplotlib.pyplot as plt
from dipy.data import get_fnames
from dipy.io.image import load_nifti_data, load_nifti, save_nifti
from dipy.io.gradients import read_bvals_bvecs
from dipy.core.gradients import gradient_table
from scipy.ndimage.morphology import binary_dilation
from dipy.reconst import shm
from dipy.direction import peaks
from dipy.tracking import utils
from dipy.tracking.local_tracking import LocalTracking
from dipy.tracking.stopping_criterion import BinaryStoppingCriterion
from dipy.tracking.streamline import Streamlines


class SampleConnDipy:

    def __init__(self, all_vars):
        hardi_fname, hardi_bval_fname, hardi_bvec_fname = get_fnames('stanford_hardi')
        label_fname = get_fnames('stanford_labels')
        t1_fname = get_fnames('stanford_t1')
        data, affine, hardi_img = load_nifti(hardi_fname, return_img=True) 
        labels = load_nifti_data(label_fname)
        bvals, bvecs = read_bvals_bvecs(hardi_bval_fname, hardi_bvec_fname)
        gtab = gradient_table(bvals, bvecs)
        
        # ploting the middle slide and the label image 
        plt.subplot(1,2,1)
        plt.imshow(data[:,:,data.shape[2]//2, 0].T, cmap='gray')
        plt.subplot(1,2,2)
        plt.imshow(labels[:,:,labels.shape[2]//2].T, cmap='gray')
        
        # generate streamlines
        white_matter = binary_dilation((labels == 1) | (labels == 2))
        csamodel = shm.CsaOdfModel(gtab, 6)
        csapeaks = peaks.peaks_from_model(model=csamodel,
                                  data=data,
                                  sphere=peaks.default_sphere,
                                  relative_peak_threshold=.8,
                                  min_separation_angle=45,
                                  mask=white_matter)
                                  
        affine = np.eye(4)
        seeds = utils.seeds_from_mask(white_matter, affine, density=1)
        stopping_criterion = BinaryStoppingCriterion(white_matter)

        streamline_generator = LocalTracking(csapeaks, stopping_criterion, seeds,
                                             affine=affine, step_size=0.5)
        streamlines = Streamlines(streamline_generator)

        # ROI label = 2
        cc_slice = labels == 2
        cc_streamlines = utils.target(streamlines, affine, cc_slice)
        cc_streamlines = Streamlines(cc_streamlines)

        other_streamlines = utils.target(streamlines, affine, cc_slice,
                                         include=False)
        other_streamlines = Streamlines(other_streamlines)
        assert len(other_streamlines) + len(cc_streamlines) == len(streamlines)
        
        M, grouping = utils.connectivity_matrix(cc_streamlines, affine,
                                        labels.astype(np.uint8),
                                        return_mapping=True,
                                        mapping_as_streamlines=True)
        plt.imshow(np.log1p(M), interpolation='nearest')
        plt.savefig("connectivity.png")
        
        # All ROIs
        M1, grouping1 = utils.connectivity_matrix(streamlines, affine,
                                        labels.astype(np.uint8),
                                        return_mapping=True,
                                        mapping_as_streamlines=True)
                                        
        plt.imshow(np.log1p(M1), interpolation='nearest')
        
        

class DiffusionConnectivity:

    def __init__(self, all_vars):
    
        data, affine, img = load_nifti("nilearn/pdmci059/dwi/pdmci059BT2_DTI_64_dir.nii.gz", return_img=True)
        fn_bval = 'nilearn/pdmci059/dwi/pdmci059BT2_DTI_64_dir.bval'
        fn_bvec = 'nilearn/pdmci059/dwi/pdmci059BT2_DTI_64_dir.bvec'
        bvals, bvecs = read_bvals_bvecs(fn_bval, fn_bvec)
        gtab = gradient_table(bvals, bvecs)

        # Get the label from standfort atlas
        label_fname = get_fnames('stanford_labels')
        labels = load_nifti_data(label_fname)

        # View the image
        plt.subplot(1,2,1)
        plt.imshow(data[:,:,data.shape[2]//2, 0].T, cmap='gray')

        # CREATE MASK
        # Cropp the mask and image
        # vol_idx: list of volumes will be masked - of axis=3 of a 4D input_volume
        #b0_mask, mask = median_otsu(data,gtab.b0s_mask,3,1, autocrop=True)
        b0_mask, mask = median_otsu(data,vol_idx=range(data.shape[3]), 
                                     median_radius=3, numpass=1, autocrop=True, dilate=2)

        # View cropped mask
        plt.subplot(1,2,1)
        plt.imshow(b0_mask[:,:,b0_mask.shape[2]//2, 0].T, cmap='gray')
        plt.subplot(1,2,2)
        plt.imshow(mask[:,:,b0_mask.shape[2]//2].T, cmap='gray')

        # Getting fiber direction
        #     With cropped data

        # label_fname = get_fnames('stanford_labels')
        # labels = load_nifti_data(label_fname)

        # white_matter = binary_dilation((labels == 1) | (labels == 2))
        # csamodel = shm.CsaOdfModel(gtab, 6)
        # csapeaks = peaks_from_model(model=csamodel,
        #                                   data=b0_mask,
        #                                   sphere=default_sphere,
        #                                   relative_peak_threshold=.8,
        #                                   min_separation_angle=45,
        #                                   mask=white_matter)
        """

            CSD
            https://dipy.org/documentation/0.16.0./examples_built/tracking_quick_start/
            https://dipy.org/documentation/0.16.0./examples_built/introduction_to_basic_tracking/
            Another kind of tracking : https://dipy.org/documentation/1.2.0./examples_built/tracking_introduction_eudx/#example-tracking-introduction-eudx
                https://github.com/dipy/dipy/blob/master/doc/examples/tracking_deterministic.py


        """


        #For the Constrained Spherical Deconvolution we need to estimate the response function and create a model.
        response, ratio = auto_response(gtab, data, roi_radius=10, fa_thr=0.7)
        csd_model = ConstrainedSphericalDeconvModel(gtab, response)

        # Using peaks
        sphere = get_sphere('symmetric724')
        csd_peaks = peaks_from_model(model=csd_model,
                                     data=b0_mask,
                                     sphere=sphere, #peaks.default_sphere,
                                     mask=mask,
                                     relative_peak_threshold=.5,
                                     min_separation_angle=25,
                                     parallel=True)

        plt.subplot(1,2,1)
        plt.imshow(csd_peaks.gfa[:,:,35].T, cmap='gray')

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
        tensor_fit = tensor_model.fit(b0_mask)

        fa = tensor_fit.fa

        # check image
        plt.subplot(1,2,1)
        plt.imshow(fa2[:,:,35].T, cmap='gray')
            
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
        csd_fit = csd_model.fit(b0_mask, mask)
        prob_dg = ProbabilisticDirectionGetter.from_shcoeff(csd_fit.shm_coeff,
                                                            max_angle=30.,
                                                            sphere=default_sphere)
        # detmax_dg = DeterministicMaximumDirectionGetter.from_shcoeff(
        #     csd_fit.shm_coeff, max_angle=30., sphere=default_sphere)

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
    from distribution.logger import Log
    from distribution.utilities import load_json, save_json
    from distribution.distribution_definitions import DEFAULT
    from processing.schedule_helper import Scheduler, get_jobs_status
    from processing.nilearn import nl_helper

    project_ids = Get_Vars().get_projects_ids()
    params      = get_parameters(project_ids)
    project     = params.project
    all_vars    = Get_Vars(params)

    SampleConnDipy(all_vars)
    DiffusionConnectivity(all_vars)



