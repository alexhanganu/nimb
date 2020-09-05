# %%
import processing.nilearn.nl_helper as hp
from nilearn import image
import matplotlib.pyplot as plt
from sys import platform
import os
# %%
#load file
if platform == "linux" or platform == "darwin":
    im_bold1 = image.load_img("/home/hanganua/projects/def-hanganua/nilearn/001PD/P001_run1_bold.nii.gz")
if platform == "win32" or platform == "win64":
    im_bold1 = image.load_img("D:/PROGRAMMING/Alex/nilearn/001PD/P001_run1_bold.nii.gz")
    output_loc = "D:/PROGRAMMING/Alex/nilearn/001PD/corr"

#%%
#initialize
harvard = hp.Havard_Atlas()
#%%
conn = harvard.extract_connectivity_zFisher(im_bold1, output_loc, "connectivity.csv")
#%%
#extract label for ploting
rois_labels = harvard.extract_label_rois(im_bold1)[0]
#print(rois_labels[1:])
#plot
fig = plt.figure(figsize=(11,10))
plt.imshow(conn, interpolation='None', cmap='RdYlBu_r')
plt.yticks(range(len(rois_labels)), rois_labels[0:]);
plt.xticks(range(len(rois_labels)), rois_labels[0:], rotation=90);
plt.title('Parcellation correlation matrix')
plt.colorbar();
img_name = os.path.join(output_loc,"corr_harvard.png")
plt.savefig(img_name)

#%%
destrieux = hp.Destrieux_Atlas()
destrieux.extract_correlation(im_bold1, output_loc, 'left_hemi_corr.csv', 'right_hemi_corr.csv')

