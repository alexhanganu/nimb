set colscalebarflag 1
set scalebarflag 1
save_tiff /home/kali/Desktop/lucas_nps_mci/project1/fs_glm/results/fdr/g2v1_g1g2.var_3.0_lat.tiff
rotate_brain_y 180
redraw
save_tiff /home/kali/Desktop/lucas_nps_mci/project1/fs_glm/results/fdr/g2v1_g1g2.var_3.0_med.tiff
sclv_set_current_threshold_using_fdr 0.05 0
redraw
save_tiff /home/kali/Desktop/lucas_nps_mci/project1/fs_glm/results/fdr/g2v1_g1g2.var_fdr_med.tiff
rotate_brain_y 180
redraw
save_tiff /home/kali/Desktop/lucas_nps_mci/project1/fs_glm/results/fdr/g2v1_g1g2.var_fdr_lat.tiff
exit
