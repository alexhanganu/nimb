# %%
import processing.nilearn.nl_helper as hp
from nilearn import image
import matplotlib.pyplot as plt
from sys import platform
# %%
#load file
if platform == "linux" or platform == "darwin":
    im_bold1 = image.load_img("/home/hanganua/projects/def-hanganua/nilearn/001PD/P001_run1_bold.nii.gz")
if platform == "win32" or platform == "win64":
    im_bold1 = image.load_img("D:/PROGRAMMING/Alex/nilearn/001PD/P001_run1_bold.nii.gz")

#%%
#initialize
ex = hp.Havard_Atlas()
#%%
conn = ex.extract_connectivity_zFisher(im_bold1, "connectivity.csv")
#%%
#extract label for ploting
rois_labels = ex.extract_label_rois(im_bold1)[0]
print(rois_labels[1:])
#plot
fig = plt.figure(figsize=(11,10))
plt.imshow(conn, interpolation='None', cmap='RdYlBu_r')
plt.yticks(range(len(rois_labels)), rois_labels[0:]);
plt.xticks(range(len(rois_labels)), rois_labels[0:], rotation=90);
plt.title('Parcellation correlation matrix')
plt.colorbar();
plt.savefig("graph.png")

#%%

