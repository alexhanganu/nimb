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

class DestrieuxAtlas:
    """
    Performs connectivity analysis using the Destrieux atlas on surface data.
    (Placeholder for future implementation if needed)
    """
    def __init__(self):
        # This would require surface data, not just volumetric BOLD data
        log.warning("Destrieux Atlas analysis is not fully implemented for volumetric data.")
        pass
