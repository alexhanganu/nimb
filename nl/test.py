# %%
import nl.nl_helper as hp
from nilearn import image
import matplotlib.pyplot as plt
# %%
#load file
im_bold1 = image.load_img("D:/PROGRAMMING/Alex/nilearn/001PD/P001_run1_bold.nii.gz")

#%%
#initialize
ex = hp.Extractions()

#extract info
rois_labels = ex.extract_atlas_rois(im_bold1)[0]
print(rois_labels[1:])
#%%
conn = ex.extract_zFisher_connectivity(im_bold1)
#%%
#plot
fig = plt.figure(figsize=(11,10))
plt.imshow(conn, interpolation='None', cmap='RdYlBu_r')
plt.yticks(range(len(rois_labels)), rois_labels[0:]);
plt.xticks(range(len(rois_labels)), rois_labels[0:], rotation=90);
plt.title('Parcellation correlation matrix')
plt.colorbar();
plt.savefig("graph.png")

#%%
