from nilearn import input_data, datasets
from nilearn.connectome import ConnectivityMeasure
import numpy as np

class Extractions():

    def extract_atlas_rois(self,image):
        #Extract the 2D ROIs from 4D BOLD image using atlas labels get from nilearn
        atlas = datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm')
        atlas_filename = atlas.maps
        # Create a masker object that we can use to select ROIs
        masker = input_data.NiftiLabelsMasker(labels_img=atlas_filename)
        # Apply our atlas to the Nifti object so we can pull out data from single parcels/ROIs
        rois = masker.fit_transform(image)

        return atlas.labels, rois


    def extract_zFisher_connectivity(self, image):
        """Compute correlations across multiple brain regions from 4D BOLD image """

        # Extract the 2D ROIs from 4D BOLD image using atlas labels get from nilearn
        rois = self.extract_atlas_rois(image)[1]

        # Calculate the correlation of each parcel with every other parcel
        correlation_measure = ConnectivityMeasure(kind='correlation')
        corr_ROIs_brain = correlation_measure.fit_transform([rois])[0]

        # Calculate the correlation fisher_z
        corr_ROIs_brain_fisher_z = np.arctanh(corr_ROIs_brain)

        return corr_ROIs_brain_fisher_z


    def extract_seed_time_series(self, coords, image):
        """Extract the time_series from 1 seed of 3 coords (x,y,z) """
        seed_masker = input_data.NiftiSpheresMasker(
            coords, radius=8,
            detrend=True, standardize=True,
            low_pass=0.1, high_pass=0.01, t_r=2,
            memory='nilearn_cache', memory_level=1, verbose=0)

        seed_time_series = seed_masker.fit_transform(image)

        return seed_time_series


    def extract_zFisher_1_region(self, coords, image):
        """Extract Fisher score a seed of 3 coords (x,y,z) and 4D BOLD image """

        #Extract the time_series from 4D BOLD image
        brain_masker = input_data.NiftiMasker(smoothing_fwhm=6,
                                              detrend=True, standardize=True,
                                              low_pass=0.1, high_pass=0.01, t_r=2,
                                              memory='nilearn_cache', memory_level=1, verbose=0)
        brain_time_series = brain_masker.fit_transform(image)

        # extract time series of 1 region
        seed_time_series = self.extract_seed_time_series(coords, image)

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
        print("pcc_coords: %.3f" % coords)
        # print("Seed-to-voxel correlation shape: (%s, %s)" %seed_to_voxel_correlations.shape)
        print("Seed-to-voxel correlation: min = %.3f; max = %.3f" % (
            seed_to_voxel_correlations.min(), seed_to_voxel_correlations.max()))
        print("Seed-to-voxel correlation Fisher-z transformed: min = %.3f; max = %.3f"
              % (seed_to_voxel_correlations_fisher_z.min(),
                 seed_to_voxel_correlations_fisher_z.max()))

        return seed_to_voxel_correlations, seed_to_voxel_correlations_fisher_z


    def seed_correlation(self, seed_coords, bold):
        """Compute the correlation between a seed voxel vs. other voxels of 2D array BOLD
        Parameters
        ----------
        bold [2d array]: n_stimuli x n_voxels
        seed_coords [2d arra]: n_stimuli x 1 voxel

        Return
        ----------
        seed_corr [2d array]: n_stimuli x 1
        seed_corr_fishZ [2d array]: n_stimuli x 1
        """
        seed_to_voxel_correlations = (np.dot(bold.T, seed_coords) /
                                      seed_coords.shape[0])
        # Transfrom the correlation values to Fisher z-scores
        seed_to_voxel_correlations_fisher_z = np.arctanh(seed_to_voxel_correlations)

        return seed_to_voxel_correlations, seed_to_voxel_correlations_fisher_z

