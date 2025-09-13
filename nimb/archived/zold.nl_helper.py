import os

import pandas as pd
import numpy as np

from nilearn import input_data, datasets
from nilearn.connectome import ConnectivityMeasure
from nilearn import surface


class Havard_Atlas():

    def extract_label_rois(self, nifti_image):
        """Extract the 2D ROIs from 4D BOLD image using atlas labels get from nilearn"""

        atlas = datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm')
        # get filename containing atlas info
        atlas_filename = atlas.maps
        # Create a masker object to extract signal on the parcellation
        masker = input_data.NiftiLabelsMasker(labels_img=atlas_filename)
        # Turned the Nifti data to time-series where each column is a ROI
        rois_ts = masker.fit_transform(nifti_image)

        return atlas.labels, rois_ts


    def extract_connectivity_zFisher(self, nifti_image, output_loc, output_name):
        """Compute correlations across multiple brain regions from 4D BOLD image """

        # Turned the 4D Nifti function image to 2D time-series where each column is a ROI
        rois = self.extract_label_rois(nifti_image)[1]
        # Calculate the correlation of each parcel with every other parcel
        correlation_measure = ConnectivityMeasure(kind='correlation')
        corr_ROIs_brain = correlation_measure.fit_transform([rois])[0]
        # Calculate the correlation fisher_z
        corr_ROIs_brain_fisher_z = np.arctanh(corr_ROIs_brain)
        # Convert to dataframe
        output_name = os.path.join(output_loc,output_name)
        df_corr_ROIs_brain_fisher_z = pd.DataFrame(corr_ROIs_brain_fisher_z)
        df_corr_ROIs_brain_fisher_z.to_csv(output_name, index=False, header=None)

        return corr_ROIs_brain_fisher_z


    def extract_seed_time_series(self, seed, nifti_image):
        """Extract the time_series from 1 seed of 3 coords (x,y,z) """
        seed_masker = input_data.NiftiSpheresMasker(
            seed, radius=8,
            detrend=True, standardize=True,
            low_pass=0.1, high_pass=0.01, t_r=2,
            memory='nilearn_cache', memory_level=1, verbose=0)
        seed_time_series = seed_masker.fit_transform(nifti_image)

        return seed_time_series


    def extract_zFisher_1_region(self, seed, nifti_image):
        """Extract Fisher score a seed of 3 coords (x,y,z) and 4D BOLD image """

        #Extract the time_series from 4D BOLD image
        brain_masker = input_data.NiftiMasker(smoothing_fwhm=6,
                                              detrend=True, standardize=True,
                                              low_pass=0.1, high_pass=0.01, t_r=2,
                                              memory='nilearn_cache', memory_level=1, verbose=0)
        brain_time_series = brain_masker.fit_transform(nifti_image)
        # extract time series of 1 region
        seed_time_series = self.extract_seed_time_series(seed, nifti_image)
        # correlate seed with every brain voxel
        seed_to_voxel_correlations = (np.dot(brain_time_series.T, seed_time_series) /
                                      seed_time_series.shape[0])
        # calculate the z-fisher
        seed_to_voxel_correlations_fisher_z = np.arctanh(seed_to_voxel_correlations)
        # Tranform the correlation array back to a Nifti image object, that we can save.
        seed_to_voxel_correlations_fisher_z_img = brain_masker.inverse_transform(
            seed_to_voxel_correlations_fisher_z.T)
        seed_to_voxel_correlations_fisher_z_img.to_filename(
            'pcc_seed_correlation_z.nii.gz')

        # display values to verify
        print("pcc_coords: %.3f" % seed)
        # print("Seed-to-voxel correlation shape: (%s, %s)" %seed_to_voxel_correlations.shape)
        print("Seed-to-voxel correlation: min = %.3f; max = %.3f" % (
            seed_to_voxel_correlations.min(), seed_to_voxel_correlations.max()))
        print("Seed-to-voxel correlation Fisher-z transformed: min = %.3f; max = %.3f"
              % (seed_to_voxel_correlations_fisher_z.min(),
                 seed_to_voxel_correlations_fisher_z.max()))

        return seed_to_voxel_correlations, seed_to_voxel_correlations_fisher_z



# https://nilearn.github.io/auto_examples/01_plotting/plot_surf_stat_map.html#sphx-glr-auto-examples-01-plotting-plot-surf-stat-map-py
class Destrieux_Atlas():
    def extract_correlation_hemi(self, nifti_image, output_file, mesh, hemi='map_left'):
        """
        Input params:
            - hemi (hemisphere) = 'map_left' or 'map_right'
            - mesh : 'fsaverage.infl_left'
                    'fsaverage.infl_right'
                    'fsaverage.pial_left'
                    'fsaverage.pial_right'
                    'fsaverage.sulc_left'
                    'fsaverage.sulc_right'
        Output param:
            - correlation matrix and its zFisher values
            - Save the correlation matrix to csv file
        """
        # extract surface data from nifti image ###################
        surface_data = surface.vol_to_surf(nifti_image, surf_mesh=mesh)
        timeseries = surface.load_surf_data(surface_data)
        # fill Nan value with 0 and infinity with large finite numbers
        timeseries = np.nan_to_num(timeseries)
        # get destrieux atlas ######################################
        destrieux_atlas = datasets.fetch_atlas_surf_destrieux()
        labels = destrieux_atlas['labels']  # get labels
        parcellation = destrieux_atlas[hemi] # get parcellation

        # convert timeseries surface to 2D matrix where each column is a ROI
        rois = []
        for i in range(len(labels)):
            pcc_labels = np.where(parcellation == i)[0]
            # each parcellation to 1D matrix
            seed_timeseries = np.mean(timeseries[pcc_labels], axis=0)
            rois.append(np.array(seed_timeseries))
        rois = np.array(rois).T
        rois = np.nan_to_num(rois)

        # extract correlation matrix
        correlation_measure = ConnectivityMeasure(kind='correlation')
        corr_rois = correlation_measure.fit_transform([rois])[0]
        corr_rois_z = np.arctanh(corr_rois) # normalize to z-fisher

        # save the correlation to csv
        df = pd.DataFrame(corr_rois_z)
        df.to_csv(output_file, index=False, header=None)

        return corr_rois, corr_rois_z

    def extract_correlation(self, nifti_image, output_loc, output_left, output_right):
        # getting the mesh for surface mapping #####################
        fsaverage = datasets.fetch_surf_fsaverage()
        output_left = os.path.join(output_loc,output_left)
        output_right = os.path.join(output_loc, output_right)

        self.extract_correlation_hemi(nifti_image, output_left,
                                      mesh = fsaverage.infl_left)
        self.extract_correlation_hemi(nifti_image, output_right,
                                      hemi='map_right',
                                      mesh=fsaverage.infl_right)