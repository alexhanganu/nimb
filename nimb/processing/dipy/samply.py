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
        
output_loc = os.path.join(os.environ['HOME'],'Desktop')

def save_plot(data, f_name):
        plt.subplot(1,2,1)
        plt.pcolor(data, cmap = 'gray')
        # plt.yticks(range(len(rois_labels)), rois_labels[0:]);
        # plt.xticks(range(len(rois_labels)), rois_labels[0:], rotation=90);
        plt.title(f'Title')
        plt.colorbar();
        img_name = os.path.join(output_loc, f_name)
        plt.savefig(img_name)


class SampleConnDipy:

    def __init__(self):
        """this is a sample class
            to check the working steps as defined in the cours
        """
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
