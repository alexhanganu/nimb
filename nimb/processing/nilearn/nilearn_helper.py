
# -*- coding: utf-8 -*-
"""
This module contains helper classes for performing connectivity analysis using Nilearn
with different brain atlases.
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from nilearn import datasets, input_data, image
from nilearn.connectome import ConnectivityMeasure

class HarvardAtlas:
    """
    Performs connectivity analysis using the Harvard-Oxford cortical atlas.
    """
    def __init__(self):
        self.atlas = datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm')
        self.atlas_filename = self.atlas.maps
        self.labels = self.atlas.labels

    def extract_label_rois(self, nifti_image_path):
        """Extracts time-series data for each ROI defined by the atlas."""
        masker = input_data.NiftiLabelsMasker(labels_img=self.atlas_filename, standardize=True)
        time_series = masker.fit_transform(nifti_image_path)
        return self.labels, time_series

    def extract_connectivity(self, time_series):
        """Computes a correlation matrix from the ROI time-series data."""
        correlation_measure = ConnectivityMeasure(kind='correlation')
        correlation_matrix = correlation_measure.fit_transform([time_series])[0]
        # Fisher's Z-transformation for stabilizing variance
        return np.arctanh(correlation_matrix)

    def save_results(self, connectivity_matrix, labels, csv_path, png_path):
        """Saves the connectivity matrix to a CSV and plots it to a PNG."""
        # Save CSV
        df = pd.DataFrame(connectivity_matrix)
        df.to_csv(csv_path, index=False, header=False)
        
        # Save Plot
        fig = plt.figure(figsize=(11, 10))
        plt.imshow(connectivity_matrix, interpolation='None', cmap='RdYlBu_r')
        plt.yticks(range(len(labels)), labels)
        plt.xticks(range(len(labels)), labels, rotation=90)
        plt.title('Harvard-Oxford Atlas: Connectivity Matrix')
        plt.colorbar()
        plt.tight_layout()
        plt.savefig(png_path)
        plt.close(fig)


class Destrieux_Atlas:
    """
    Performs connectivity analysis using the Destrieux atlas on surface data.
    (For future implementation)
    """
    def __init__(self):
        # This would require surface data, not just volumetric BOLD data
        log.warning("Destrieux Atlas analysis is not fully implemented for volumetric data.")
        pass


# This is Destrieux atlas surface based, while the Harvard atlas in volume based
# from nilearn import surface
# https://nilearn.github.io/auto_examples/01_plotting/plot_surf_stat_map.html#sphx-glr-auto-examples-01-plotting-plot-surf-stat-map-py
#     def extract_correlation_hemi(self, nifti_image, output_file, mesh, hemi='map_left'):
#         """
#         Input params:
#             - hemi (hemisphere) = 'map_left' or 'map_right'
#             - mesh : 'fsaverage.infl_left'
#                     'fsaverage.infl_right'
#                     'fsaverage.pial_left'
#                     'fsaverage.pial_right'
#                     'fsaverage.sulc_left'
#                     'fsaverage.sulc_right'
#         Output param:
#             - correlation matrix and its zFisher values
#             - Save the correlation matrix to csv file
#         """
#         # extract surface data from nifti image ###################
#         surface_data = surface.vol_to_surf(nifti_image, surf_mesh=mesh)
#         timeseries = surface.load_surf_data(surface_data)
#         # fill Nan value with 0 and infinity with large finite numbers
#         timeseries = np.nan_to_num(timeseries)
#         # get destrieux atlas ######################################
#         destrieux_atlas = datasets.fetch_atlas_surf_destrieux()
#         labels = destrieux_atlas['labels']  # get labels
#         parcellation = destrieux_atlas[hemi] # get parcellation

#         # convert timeseries surface to 2D matrix where each column is a ROI
#         rois = []
#         for i in range(len(labels)):
#             pcc_labels = np.where(parcellation == i)[0]
#             # each parcellation to 1D matrix
#             seed_timeseries = np.mean(timeseries[pcc_labels], axis=0)
#             rois.append(np.array(seed_timeseries))
#         rois = np.array(rois).T
#         rois = np.nan_to_num(rois)

#         # extract correlation matrix
#         correlation_measure = ConnectivityMeasure(kind='correlation')
#         corr_rois = correlation_measure.fit_transform([rois])[0]
#         corr_rois_z = np.arctanh(corr_rois) # normalize to z-fisher

#         # save the correlation to csv
#         df = pd.DataFrame(corr_rois_z)
#         df.to_csv(output_file, index=False, header=None)

#         return corr_rois, corr_rois_z

#     def extract_correlation(self, nifti_image, output_loc, output_left, output_right):
#         # getting the mesh for surface mapping #####################
#         fsaverage = datasets.fetch_surf_fsaverage()
#         output_left = os.path.join(output_loc,output_left)
#         output_right = os.path.join(output_loc, output_right)

#         self.extract_correlation_hemi(nifti_image, output_left,
#                                       mesh = fsaverage.infl_left)
#         self.extract_correlation_hemi(nifti_image, output_right,
#                                       hemi='map_right',
#                                       mesh=fsaverage.infl_right)
