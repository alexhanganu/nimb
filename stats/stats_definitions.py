#!/bin/python
# 2020 06 13

BS_Hip_Tha_stats_f = {
    'Brainstem':('mri/brainstemSsVolumes.v10.txt','stats/brainstem.v12.stats','stats/aseg.brainstem.volume.stats'),
    'HIPL':('mri/hippoSfVolumes-T1.v10.txt','stats/lh.hipposubfields.T1.v21.stats','stats/aseg.hippo.lh.volume.stats'),
    'HIPR':('mri/hippoSfVolumes-T1.v10.txt','stats/rh.hipposubfields.T1.v21.stats','stats/aseg.hippo.rh.volume.stats'),
    'AMYL':('stats/amygdalar-nuclei.lh.T1.v21.stats',),
    'AMYR':('stats/amygdalar-nuclei.rh.T1.v21.stats',),
    'THAL':('stats/thalamic-nuclei.lh.v12.T1.stats',),
    'THAR':('stats/thalamic-nuclei.rh.v12.T1.stats',)}


BrStem_Hip_f2rd_stats={'Brainstem':'aseg.brainstem.volume.stats','HIPL':'aseg.hippo.lh.volume.stats',
                 'HIPR':'aseg.hippo.rh.volume.stats'}
BrStem_Hip_f2rd={'Brainstem':'brainstemSsVolumes.v10.txt','HIPL':'lh.hippoSfVolumes-T1.v10.txt',
                 'HIPR':'rh.hippoSfVolumes-T1.v10.txt'}
parc_DK_f2rd ={'L':'lh.aparc.stats','R':'rh.aparc.stats'}
parc_DS_f2rd ={'L':'lh.aparc.a2009s.stats','R':'rh.aparc.a2009s.stats'}

all_data = {
    'atlases':['Brainstem','HIP','Vol','ParcDK','ParcDS'],
    'atlas_ending':{'Brainstem':'','HIP':'','Vol':'','ParcDK':'_DK','ParcDS':'_DS'},
    'Brainstem':{
        'two_hemi':False,
        'files':{'Brainstem_stats':('aseg.brainstem.volume.stats',),
                 'Brainstem_mri':('brainstemSsVolumes.v10.txt',)},
        'parameters' : {'Brainstem':'Brainstem',},
        'header':{'Medulla':'medulla','Pons':'pons','SCP':'scp','Midbrain':'midbrain',
                'Whole_brainstem':'wholeBrainstem',}},
    'HIP':{
        'two_hemi':True,
        'files':{'HIPL_stats':('aseg.hippo.lh.volume.stats',),
                 'HIPL_mri':('rh.hippoSfVolumes-T1.v10.txt',),
                 'HIPR_stats':('aseg.hippo.rh.volume.stats',),
                 'HIPR_mri':('rh.hippoSfVolumes-T1.v10.txt',)},
        'parameters' : {'HIPL':'HIPL','HIPR':'HIPR',},
        'header':{'Hippocampal_tail':'hippocampal_tail',
                'subiculum':'subiculum','CA1':'ca1','hippocampal-fissure':'fissureHIP',
            'presubiculum':'presubiculum','parasubiculum':'parasubiculum','molecular_layer_HP':'molecularLayerHP',
            'GC-ML-DG':'gcmldg','CA3':'ca3','CA4':'ca4','fimbria':'fimbria','HATA':'hata',
            'Whole_hippocampus':'wholeHippocampus'}},
    'Vol':{
        'two_hemi':True,
        'files':{'Vol_stats':('aseg.parc.stats',),},
        'parameters' : {'Volume_mm3':'VolSeg','NVoxels':'VolSegNVoxels',
                        'normMean':'VolSegnormMean','normStdDev':'VolSegnormStdDev',
                        'normMin':'VolSegnormMin','normMax':'VolSegnormMax','normRange':'VolSegnormRange'},
        'header':{'Left-Lateral-Ventricle':'ventricleLateralL','Left-Inf-Lat-Vent':'ventricleInfLateralL',
                'Left-Cerebellum-White-Matter':'cerebellumWhiteMatterL','Left-Cerebellum-Cortex':'cerebellumCortexL',
                'Left-Thalamus-Proper':'thalamusProperL','Left-Caudate':'caudateL','Left-Putamen':'putamenL',
                'Left-Pallidum':'pallidumL','3rd-Ventricle':'ventricle_3rd','4th-Ventricle':'ventricle_4th',
                'Brain-Stem':'brainstem','Left-Hippocampus':'hippocampusL','Left-Amygdala':'amygdalaL',
                'CSF':'csf','Left-Accumbens-area':'accumbensAreaL','Left-VentralDC':'ventralDCL',
                'Left-vessel':'vesselL','Left-choroid-plexus':'choroidPlexusL','Right-Lateral-Ventricle':'ventricleLateralR',
                'Right-Inf-Lat-Vent':'ventricleInfLateralR','Right-Cerebellum-White-Matter':'cerebellumWhiteMatterR',
                'Right-Cerebellum-Cortex':'cerebellumCortexR','Right-Thalamus-Proper':'thalamusProperR',
                'Right-Caudate':'caudateR','Right-Putamen':'putamenR','Right-Pallidum':'pallidumR',
                'Right-Hippocampus':'hippocampusR','Right-Amygdala':'amygdalaR','Right-Accumbens-area':'accumbensAreaR',
                'Right-VentralDC':'ventralDCR','Right-vessel':'vesselR','Right-choroid-plexus':'choroidPlexusR',
                '5th-Ventricle':'ventricle_5th','WM-hypointensities':'wm_hypointensities','Left-WM-hypointensities':'wm_hypointensitiesL',
                'Right-WM-hypointensities':'WMhypointensitiesR','non-WM-hypointensities':'nonWMhypointensities',
                'Left-non-WM-hypointensities':'nonWMhypointensitiesL','Right-non-WM-hypointensities':'nonWMhypointensitiesR',
                'Optic-Chiasm':'opticChiasm','CC_Posterior':'ccPosterior','CC_Mid_Posterior':'ccMidPosterior',
                'CC_Central':'ccCentral','CC_Mid_Anterior':'ccMidAnterior','CC_Anterior':'ccAnterior','BrainSegVol':'volBrainSeg',
                'BrainSegVolNotVent':'volBrainSegNotVent','BrainSegVolNotVentSurf':'volBrainSegNotVentSurf',
                'VentricleChoroidVol':'volVentricleChoroid','lhCortexVol':'volCortexL',
                'rhCortexVol':'volCortexR','CortexVol':'volCortex','lhCerebralWhiteMatterVol':'volCerebralWhiteMatterL',
                'rhCerebralWhiteMatterVol':'volCerebralWhiteMatterR','CerebralWhiteMatterVol':'volCerebralWhiteMatter',
                'SubCortGrayVol':'volSubCortGray','TotalGrayVol':'volTotalGray','SupraTentorialVol':'volSupraTentorial',
                'SupraTentorialVolNotVent':'volSupraTentorialNotVent','SupraTentorialVolNotVentVox':'volSupraTentorialNotVentVox',
                'MaskVol':'volMask','BrainSegVol-to-eTIV':'volBrainSegtoeTIV','MaskVol-to-eTIV':'volMasktoeTIV',
                'lhSurfaceHoles':'surfaceHolesL','rhSurfaceHoles':'surfaceHolesR','SurfaceHoles':'surfaceHoles','eTIV':'eTIV'}},
    'ParcDK':{
        'two_hemi':True,
        'files':{'L':('lh.aparc.stats',),'R':('rh.aparc.stats',),},
        'parameters' : {'ThickAvg':'Thick','SurfArea':'Area',
                  'GrayVol':'Vol','MeanCurv':'Curv',
                  'NumVert':'NumVert','ThickStd':'ThickStd',
                  'GausCurv':'CurvGaus','CurvInd':'CurvInd',
                  'FoldInd':'FoldInd'},
        'header':{'bankssts':'temporal_superior_sulcus_bank','caudalanteriorcingulate':'cingulate_anterior_caudal','caudalmiddlefrontal':'frontal_middle_caudal',
            'cuneus':'occipital_cuneus','entorhinal':'temporal_entorhinal','fusiform':'temporal_fusiform','inferiorparietal':'parietal_inferior',
            'inferiortemporal':'temporal_inferior','isthmuscingulate':'cingulate_isthmus','lateraloccipital':'occipital_lateral',
            'lateralorbitofrontal':'frontal_orbitolateral','lingual':'occipital_lingual','medialorbitofrontal':'frontal_orbitomedial',
            'middletemporal':'temporal_middle','parahippocampal':'temporal_parahippocampal','paracentral':'frontal_paracentral',
            'parsopercularis':'frontal_parsopercularis','parsorbitalis':'frontal_parsorbitalis','parstriangularis':'frontal_parstriangularis',
            'pericalcarine':'occipital_pericalcarine','postcentral':'parietal_postcentral','posteriorcingulate':'cingulate_posterior',
            'precentral':'frontal_precentral','precuneus':'parietal_precuneus','rostralanteriorcingulate':'cingulate_anterior_rostral',
            'rostralmiddlefrontal':'frontal_middle_rostral','superiorfrontal':'frontal_superior','superiorparietal':'parietal_superior',
            'superiortemporal':'temporal_superior','supramarginal':'parietal_supramarginal',
            'frontalpole':'frontal_pole',
            'temporalpole':'temporal_pole','transversetemporal':'temporal_transverse','insula':'insula','Cortex_MeanThickness':'cortex_thickness',
            'Cortex_WhiteSurfArea':'cortex_area','Cortex_CortexVol':'cortex_vol',
            'Cortex_NumVert':'cortex_numvert',
            'UnsegmentedWhiteMatter':'WMUnsegmented',}},
    'ParcDS':{
        'two_hemi':True,
        'files':{'L':('lh.aparc.a2009s.stats',),'R':('rh.aparc.a2009s.stats',),},
        'parameters' : {'ThickAvg':'Thick','SurfArea':'Area',
                  'GrayVol':'Vol','MeanCurv':'Curv',
                  'NumVert':'NumVert','ThickStd':'ThickStd',
                  'GausCurv':'CurvGaus','CurvInd':'CurvInd',
                  'FoldInd':'FoldInd'},
        'header':{'G&S_frontomargin': 'frontal_margin_GS',
                'G&S_occipital_inf': 'occipital_inf_GS',
                'G&S_paracentral': 'frontal_paracentral_GS',
                'G&S_subcentral': 'frontal_subcentral_GS',
                'G&S_transv_frontopol': 'frontal_pol_transv_GS',
                'G&S_cingul-Ant': 'cingul_ant_GS',
                'G&S_cingul-Mid-Ant': 'cingul_ant_mid_GS',
                'G&S_cingul-Mid-Post': 'cingul_Mid_Post_GS',
                'G_cingul-Post-dorsal': 'cingul_Post_dorsal_Gyr',
                'G_cingul-Post-ventral': 'cingul_Post_ventral_Gyr',
                'G_cuneus': 'occipital_cuneus_Gyr',
                'G_front_inf-Opercular': 'frontal_inf_Opercular_Gyr',
                'G_front_inf-Orbital': 'frontal_inf_Orbital_Gyr',
                'G_front_inf-Triangul': 'frontal_inf_Triangul_Gyr',
                'G_front_middle': 'frontal_middle_Gyr',
                'G_front_sup': 'frontal_sup_Gyr',
                'G_Ins_lg&S_cent_ins': 'insula_lg_S_cent_ins_Gyr',
                'G_insular_short': 'insular_short_Gyr',
                'G_occipital_middle': 'occipital_middle_Gyr',
                'G_occipital_sup': 'occipital_sup_Gyr',
                'G_oc-temp_lat-fusifor': 'temporal_lat_fusifor_Gyr',
                'G_oc-temp_med-Lingual': 'temporal_med_Lingual_Gyr',
                'G_oc-temp_med-Parahip': 'temporal_med_Parahip_Gyr',
                'G_orbital': 'frontal_orbital_Gyr',
                'G_pariet_inf-Angular': 'pariet_inf_Angular_Gyr',
                'G_pariet_inf-Supramar': 'pariet_inf_Supramar_Gyr',
                'G_parietal_sup': 'parietal_sup_Gyr',
                'G_postcentral': 'parietal_postcentral_Gyr',
                'G_precentral': 'frontal_precentral_Gyr',
                'G_precuneus': 'parietal_precuneus_Gyr',
                'G_rectus': 'rectus_Gyr',
                'G_subcallosal': 'cc_subcallosal_Gyr',
                'G_temp_sup-G_T_transv': 'temp_sup_G_T_transv_Gyr',
                'G_temp_sup-Lateral': 'temp_sup_Lateral_Gyr',
                'G_temp_sup-Plan_polar': 'temp_sup_Plan_polar_Gyr',
                'G_temp_sup-Plan_tempo': 'temp_sup_Plan_tempo_Gyr',
                'G_temporal_inf': 'temporal_inf_Gyr',
                'G_temporal_middle': 'temporal_middle_Gyr',
                'Lat_Fis-ant-Horizont': 'lat_Fis_ant_Horizont',
                'Lat_Fis-ant-Vertical': 'lat_Fis_ant_Vertical',
                'Lat_Fis-post': 'lat_Fis_post',
                'Pole_occipital': 'occipital_Pole',
                'Pole_temporal': 'temporal_pole',
                'S_calcarine': 'occipital_calcarine_Sulc',
                'S_central': 'frontal_central_Sulc',
                'S_cingul-Marginalis': 'cingul_Marginalis_Sulc',
                'S_circular_insula_ant': 'insula_circular_ant_Sulc',
                'S_circular_insula_inf': 'insula_circular_inf_Sulc',
                'S_circular_insula_sup': 'insula__circular_sup_Sulc',
                'S_collat_transv_ant': 'collat_transv_ant_Sulc',
                'S_collat_transv_post': 'collat_transv_post_Sulc',
                'S_front_inf': 'front_inf_Sulc',
                'S_front_middle': 'front_middle_Sulc',
                'S_front_sup': 'front_sup_Sulc',
                'S_interm_prim-Jensen': 'interm_prim_Jensen_Sulc',
                'S_intrapariet&P_trans': 'intrapariet_P_trans_Sulc',
                'S_oc_middle&Lunatus': 'occipital_middle_Lunatus_Sulc',
                'S_oc_sup&transversal': 'occipital_sup_transversal_Sulc',
                'S_occipital_ant': 'occipital_ant_Sulc',
                'S_oc-temp_lat': 'occipital_temp_lat_Sulc',
                'S_oc-temp_med&Lingual': 'occipital_temp_med_Lingual_Sulc',
                'S_orbital_lateral': 'frontal_orbital_lateral_Sulc',
                'S_orbital_med-olfact': 'frontal_orbital_med_olfact_Sulc',
                'S_orbital-H_Shaped': 'frontal_orbital_H_Shaped_Sulc',
                'S_parieto_occipital': 'parieto_occipital_Sulc',
                'S_pericallosal': 'cc_pericallosal_Sulc',
                'S_postcentral': 'parietal_postcentral_Sulc',
                'S_precentral-inf-part': 'frontal_precentral_inf_part_Sulc',
                'S_precentral-sup-part': 'frontal_precentral_sup_part_Sulc',
                'S_suborbital': 'frontal_suborbital_Sulc',
                'S_subparietal': 'parietal_subparietal_Sulc',
                'S_temporal_inf': 'temporal_inf_Sulc',
                'S_temporal_sup': 'temporal_sup_Sulc',
                'S_temporal_transverse': 'temporal_transverse_Sulc'}},
}


brstem_hip_header = {
    'all':{'Medulla':'medulla','Pons':'pons','SCP':'scp','Midbrain':'midbrain',
            'Whole_brainstem':'wholeBrainstem','Hippocampal_tail':'hippocampal-tail',
            'subiculum':'subiculum','subiculum-body':'subiculum-body','subiculum-head':'subiculum-head',
            'CA1':'ca1','CA1-body':'ca1-body','CA1-head':'ca1-head','hippocampal-fissure':'hippocampal-fissure',
            'presubiculum':'presubiculum','presubiculum-body':'presubiculum-body','presubiculum-head':'presubiculum-head',
            'parasubiculum':'parasubiculum',
            'molecular_layer_HP':'molecularLayerHP','molecular_layer_HP-head':'molecularLayerHP-head','molecular_layer_HP-body':'molecularLayerHP-body',
            'GC-ML-DG':'gcmldg','GC-ML-DG-body':'gcmldg-body','GC-ML-DG-head':'gcmldg-head',
            'CA3':'ca3','CA3-body':'ca3-body','CA3-head':'ca3-head',
            'CA4':'ca4','CA4-body':'ca4-body','CA4-head':'ca4-head',
            'fimbria':'fimbria','HATA':'hata','Whole_hippocampal_body':'wholeHippocampus-body','Whole_hippocampal_head':'wholeHippocampus-head',
            'Whole_hippocampus':'wholeHippocampus',
            'Lateral-nucleus': 'Lateral-nucleus', 'Basal-nucleus': 'Basal-nucleus', 'Accessory-Basal-nucleus': 'Accessory-Basal-nucleus',
            'Anterior-amygdaloid-area-AAA': 'Anterior-amygdaloid-area-AAA', 'Central-nucleus': 'Central-nucleus',
            'Medial-nucleus': 'Medial-nucleus', 'Cortical-nucleus': 'Cortical-nucleus',
            'Corticoamygdaloid-transitio': 'Corticoamygdaloid-transitio', 'Paralaminar-nucleus': 'Paralaminar-nucleus',
            'Whole_amygdala': 'WholeAmygdala',
            'AV': 'AV', 'CeM': 'CeM', 'CL': 'CL', 'CM': 'CM', 'LD': 'LD', 'LGN': 'LGN', 'LP': 'LP', 'L-Sg': 'L-Sg',
            'MDl': 'MDl', 'MDm': 'MDm', 'MGN': 'MGN', 'MV(Re)': 'MV(Re)', 'Pc': 'Pc', 'Pf': 'Pf', 'Pt': 'Pt', 'PuA': 'PuA',
            'PuI': 'PuI', 'PuL': 'PuL', 'PuM': 'PuM', 'VA': 'VA', 'VAmc': 'VAmc', 'VLa': 'VLa', 'VLp': 'VLp', 'VM': 'VM',
            'VPL': 'VPL', 'Whole_thalamus': 'WholeThalamus'},
    'Brainstem':['Medulla','Pons','SCP','Midbrain','Whole_brainstem',],
    'HIPL':['Hippocampal_tail','subiculum','CA1','hippocampal-fissure',
            'presubiculum','parasubiculum','molecular_layer_HP','GC-ML-DG',
            'CA3','CA4','fimbria','HATA','Whole_hippocampus'],
    'HIPR':['Hippocampal_tail','subiculum','CA1','hippocampal-fissure',
            'presubiculum','parasubiculum','molecular_layer_HP','GC-ML-DG',
            'CA3','CA4','fimbria','HATA','Whole_hippocampus'],}

segmentation_parameters = ('Volume_mm3','NVoxels','normMean','normStdDev','normMin','normMax','normRange')
segmentations_header = {'Left-Lateral-Ventricle':'ventricleLateralL','Left-Inf-Lat-Vent':'ventricleInfLateralL',
                        'Left-Cerebellum-White-Matter':'cerebellumWhiteMatterL','Left-Cerebellum-Cortex':'cerebellumCortexL',
                        'Left-Thalamus':'thalamusL','Left-Thalamus-Proper':'thalamusProperL','Left-Caudate':'caudateL','Left-Putamen':'putamenL',
                        'Left-Pallidum':'pallidumL','3rd-Ventricle':'ventricle_3rd','4th-Ventricle':'ventricle_4th',
                        'Brain-Stem':'brainstem','Left-Hippocampus':'hippocampusL','Left-Amygdala':'amygdalaL',
                        'CSF':'csf','Left-Accumbens-area':'accumbensAreaL','Left-VentralDC':'ventralDCL',
                        'Left-vessel':'vesselL','Left-choroid-plexus':'choroidPlexusL','Right-Lateral-Ventricle':'ventricleLateralR',
                            'Right-Inf-Lat-Vent':'ventricleInfLateralR','Right-Cerebellum-White-Matter':'cerebellumWhiteMatterR',
                            'Right-Cerebellum-Cortex':'cerebellumCortexR','Right-Thalamus-Proper':'thalamusProperR','Right-Thalamus':'thalamusR',
                            'Right-Caudate':'caudateR','Right-Putamen':'putamenR','Right-Pallidum':'pallidumR',
                            'Right-Hippocampus':'hippocampusR','Right-Amygdala':'amygdalaR','Right-Accumbens-area':'accumbensAreaR',
                            'Right-VentralDC':'ventralDCR','Right-vessel':'vesselR','Right-choroid-plexus':'choroidPlexusR',
                            '5th-Ventricle':'ventricle_5th','WM-hypointensities':'wm_hypointensities','Left-WM-hypointensities':'wm_hypointensitiesL',
                            'Right-WM-hypointensities':'WMhypointensitiesR','non-WM-hypointensities':'nonWMhypointensities',
                            'Left-non-WM-hypointensities':'nonWMhypointensitiesL','Right-non-WM-hypointensities':'nonWMhypointensitiesR',
                            'Optic-Chiasm':'opticChiasm','CC_Posterior':'ccPosterior','CC_Mid_Posterior':'ccMidPosterior',
                            'CC_Central':'ccCentral','CC_Mid_Anterior':'ccMidAnterior','CC_Anterior':'ccAnterior','BrainSegVol':'volBrainSeg',
                            'BrainSegVolNotVent':'volBrainSegNotVent','BrainSegVolNotVentSurf':'volBrainSegNotVentSurf',
                            'VentricleChoroidVol':'volVentricleChoroid','lhCortexVol':'volCortexL',
                            'rhCortexVol':'volCortexR','CortexVol':'volCortex','lhCerebralWhiteMatterVol':'volCerebralWhiteMatterL',
                            'rhCerebralWhiteMatterVol':'volCerebralWhiteMatterR','CerebralWhiteMatterVol':'volCerebralWhiteMatter',
                            'SubCortGrayVol':'volSubCortGray','TotalGrayVol':'volTotalGray','SupraTentorialVol':'volSupraTentorial',
                            'SupraTentorialVolNotVent':'volSupraTentorialNotVent','SupraTentorialVolNotVentVox':'volSupraTentorialNotVentVox',
                            'MaskVol':'volMask','BrainSegVol-to-eTIV':'volBrainSegtoeTIV','MaskVol-to-eTIV':'volMasktoeTIV',
                            'lhSurfaceHoles':'surfaceHolesL','rhSurfaceHoles':'surfaceHolesR','SurfaceHoles':'surfaceHoles','eTIV':'eTIV'}


parc_parameters= {'ThickAvg':'Thick','SurfArea':'Area',
                  'GrayVol':'Vol','MeanCurv':'Curv',
                  'NumVert':'NumVert','ThickStd':'ThickStd',
                  'GausCurv':'CurvGaus','CurvInd':'CurvInd',
                  'FoldInd':'FoldInd'}
parc_DK_header={'bankssts':'temporal_superior_sulcus_bank','caudalanteriorcingulate':'cingulate_anterior_caudal','caudalmiddlefrontal':'frontal_middle_caudal',
            'cuneus':'occipital_cuneus','entorhinal':'temporal_entorhinal','fusiform':'temporal_fusiform','inferiorparietal':'parietal_inferior',
            'inferiortemporal':'temporal_inferior','isthmuscingulate':'cingulate_isthmus','lateraloccipital':'occipital_lateral',
            'lateralorbitofrontal':'frontal_orbitolateral','lingual':'occipital_lingual','medialorbitofrontal':'frontal_orbitomedial',
            'middletemporal':'temporal_middle','parahippocampal':'temporal_parahippocampal','paracentral':'frontal_paracentral',
            'parsopercularis':'frontal_parsopercularis','parsorbitalis':'frontal_parsorbitalis','parstriangularis':'frontal_parstriangularis',
            'pericalcarine':'occipital_pericalcarine','postcentral':'parietal_postcentral','posteriorcingulate':'cingulate_posterior',
            'precentral':'frontal_precentral','precuneus':'parietal_precuneus','rostralanteriorcingulate':'cingulate_anterior_rostral',
            'rostralmiddlefrontal':'frontal_middle_rostral','superiorfrontal':'frontal_superior','superiorparietal':'parietal_superior',
            'superiortemporal':'temporal_superior','supramarginal':'parietal_supramarginal',
            'frontalpole':'frontal_pole',
            'temporalpole':'temporal_pole','transversetemporal':'temporal_transverse','insula':'insula','Cortex_MeanThickness':'cortex_thickness',
            'Cortex_WhiteSurfArea':'cortex_area','Cortex_CortexVol':'cortex_vol',
            'Cortex_NumVert':'cortex_numvert',
            'UnsegmentedWhiteMatter':'WMUnsegmented',}
parc_DS_header={'G&S_frontomargin': 'frontal_margin_GS',
                'G_and_S_frontomargin': 'frontal_margin_GS',
                'G&S_occipital_inf': 'occipital_inf_GS',
                'G_and_S_occipital_inf': 'occipital_inf_GS',
                'G&S_paracentral': 'frontal_paracentral_GS',
                'G_and_S_paracentral': 'frontal_paracentral_GS',
                'G&S_subcentral': 'frontal_subcentral_GS',
                'G_and_S_subcentral': 'frontal_subcentral_GS',
                'G&S_transv_frontopol': 'frontal_pol_transv_GS',
                'G_and_S_transv_frontopol': 'frontal_pol_transv_GS',
                'G&S_cingul-Ant': 'cingul_ant_GS',
                'G_and_S_cingul-Ant': 'cingul_ant_GS',
                'G&S_cingul-Mid-Ant': 'cingul_ant_mid_GS',
                'G_and_S_cingul-Mid-Ant': 'cingul_ant_mid_GS',
                'G&S_cingul-Mid-Post': 'cingul_Mid_Post_GS',
                'G_and_S_cingul-Mid-Post': 'cingul_Mid_Post_GS',
                'G_cingul-Post-dorsal': 'cingul_Post_dorsal_Gyr',
                'G_cingul-Post-ventral': 'cingul_Post_ventral_Gyr',
                'G_cuneus': 'occipital_cuneus_Gyr',
                'G_front_inf-Opercular': 'frontal_inf_Opercular_Gyr',
                'G_front_inf-Orbital': 'frontal_inf_Orbital_Gyr',
                'G_front_inf-Triangul': 'frontal_inf_Triangul_Gyr',
                'G_front_middle': 'frontal_middle_Gyr',
                'G_front_sup': 'frontal_sup_Gyr',
                'G_Ins_lg_and_S_cent_ins': 'insula_lg_S_cent_ins_Gyr',
                'G_insular_short': 'insular_short_Gyr',
                'G_occipital_middle': 'occipital_middle_Gyr',
                'G_occipital_sup': 'occipital_sup_Gyr',
                'G_oc-temp_lat-fusifor': 'temporal_lat_fusifor_Gyr',
                'G_oc-temp_med-Lingual': 'temporal_med_Lingual_Gyr',
                'G_oc-temp_med-Parahip': 'temporal_med_Parahip_Gyr',
                'G_orbital': 'frontal_orbital_Gyr',
                'G_pariet_inf-Angular': 'pariet_inf_Angular_Gyr',
                'G_pariet_inf-Supramar': 'pariet_inf_Supramar_Gyr',
                'G_parietal_sup': 'parietal_sup_Gyr',
                'G_postcentral': 'parietal_postcentral_Gyr',
                'G_precentral': 'frontal_precentral_Gyr',
                'G_precuneus': 'parietal_precuneus_Gyr',
                'G_rectus': 'rectus_Gyr',
                'G_subcallosal': 'cc_subcallosal_Gyr',
                'G_temp_sup-G_T_transv': 'temp_sup_G_T_transv_Gyr',
                'G_temp_sup-Lateral': 'temp_sup_Lateral_Gyr',
                'G_temp_sup-Plan_polar': 'temp_sup_Plan_polar_Gyr',
                'G_temp_sup-Plan_tempo': 'temp_sup_Plan_tempo_Gyr',
                'G_temporal_inf': 'temporal_inf_Gyr',
                'G_temporal_middle': 'temporal_middle_Gyr',
                'Lat_Fis-ant-Horizont': 'lat_Fis_ant_Horizont',
                'Lat_Fis-ant-Vertical': 'lat_Fis_ant_Vertical',
                'Lat_Fis-post': 'lat_Fis_post',
                'Pole_occipital': 'occipital_Pole',
                'Pole_temporal': 'temporal_pole',
                'S_calcarine': 'occipital_calcarine_Sulc',
                'S_central': 'frontal_central_Sulc',
                'S_cingul-Marginalis': 'cingul_Marginalis_Sulc',
                'S_circular_insula_ant': 'insula_circular_ant_Sulc',
                'S_circular_insula_inf': 'insula_circular_inf_Sulc',
                'S_circular_insula_sup': 'insula__circular_sup_Sulc',
                'S_collat_transv_ant': 'collat_transv_ant_Sulc',
                'S_collat_transv_post': 'collat_transv_post_Sulc',
                'S_front_inf': 'front_inf_Sulc',
                'S_front_middle': 'front_middle_Sulc',
                'S_front_sup': 'front_sup_Sulc',
                'S_interm_prim-Jensen': 'interm_prim_Jensen_Sulc',
                'S_intrapariet_and_P_trans': 'intrapariet_P_trans_Sulc',
                'S_oc_middle_and_Lunatus': 'occipital_middle_Lunatus_Sulc',
                'S_oc_sup_and_transversal': 'occipital_sup_transversal_Sulc',
                'S_occipital_ant': 'occipital_ant_Sulc',
                'S_oc-temp_lat': 'occipital_temp_lat_Sulc',
                'S_oc-temp_med_and_Lingual': 'occipital_temp_med_Lingual_Sulc',
                'S_orbital_lateral': 'frontal_orbital_lateral_Sulc',
                'S_orbital_med-olfact': 'frontal_orbital_med_olfact_Sulc',
                'S_orbital-H_Shaped': 'frontal_orbital_H_Shaped_Sulc',
                'S_parieto_occipital': 'parieto_occipital_Sulc',
                'S_pericallosal': 'cc_pericallosal_Sulc',
                'S_postcentral': 'parietal_postcentral_Sulc',
                'S_precentral-inf-part': 'frontal_precentral_inf_part_Sulc',
                'S_precentral-sup-part': 'frontal_precentral_sup_part_Sulc',
                'S_suborbital': 'frontal_suborbital_Sulc',
                'S_subparietal': 'parietal_subparietal_Sulc',
                'S_temporal_inf': 'temporal_inf_Sulc',
                'S_temporal_sup': 'temporal_sup_Sulc',
                'S_temporal_transverse': 'temporal_transverse_Sulc'}


def get_names_of_structures():
    name_structures = list()

    for val in segmentations_header:
        name_structures.append(segmentations_header[val])
    for val in parc_DK_header:
        name_structures.append(parc_DK_header[val])	
    for val in brstem_hip_header['all']:
        name_structures.append(brstem_hip_header['all'][val])
    for val in parc_DS_header:
        name_structures.append(parc_DS_header[val])

    return name_structures

name_structures = get_names_of_structures()



def get_names_of_measurements():
    name_measurement = ['Brainstem','HIPL','HIPR',]

    for val in segmentation_parameters:
        name_measurement.append('VolSeg'+val.replace('Volume_mm3',''))
        name_measurement.append('VolSegWM'+val.replace('Volume_mm3','')+'_DK')

    for hemi in ('L','R',):
        for atlas in ('_DK','_DS',):
            for meas in parc_parameters:
                name_measurement.append(parc_parameters[meas]+hemi+atlas)

    return name_measurement

name_measurement = get_names_of_measurements()


class cols_per_measure_per_atlas():

    def __init__(self, ls_columns):
        self.ls_columns = ls_columns
        self.cols_to_meas_to_atlas = self.get_columns()

    def get_columns(self):
        result = dict()

        for atlas in all_data['atlases']:
            result[atlas] = dict()
            for meas in all_data[atlas]['parameters']:
                result[atlas][meas] = list()

        for col in self.ls_columns:
            for atlas in all_data['atlases']:
                for meas in all_data[atlas]['parameters']:
                    if all_data[atlas]['parameters'][meas] in col and all_data['atlas_ending'][atlas] in col:
                        result[atlas][meas].append(self.ls_columns.index(col))
        return result

def get_structure_measurement(name, ls_meas, ls_struct):
    if name == 'eTIV':
        measurement = 'eTIV'
        structure = 'eTIV'
    else:
        measurement = ''
        structure = ''
        i = 0
        while structure not in ls_struct and i<5:
            if measurement not in ls_meas:
                for meas in ls_meas:
                    if meas in name:
                        measurement = meas
                        break
            else:
                ls_meas = ls_meas[ls_meas.index(measurement)+1:]
                for meas in ls_meas:
                    if meas in name:
                        measurement = meas
                        break

            structure = name.replace('_'+measurement,'')
            i += 1
    if structure != 'eTIV' and structure+'_'+measurement != name:
            print('ERROR in get_structure_measurement')
    return measurement, structure


def get_atlas_measurements():
    measurements = {}
    for meas in parc_parameters:
        measurements[parc_parameters[meas]] = list()
        for atlas in ('_DK','_DS',):
            measurements[parc_parameters[meas]].append(parc_parameters[meas]+'L'+atlas)
            measurements[parc_parameters[meas]].append(parc_parameters[meas]+'R'+atlas)
    return measurements

def change_column_name(df, sheet):
        columns_2_remove = ['ventricle_5th','wm_hypointensities_L',
                        'wm_hypointensities_R','non_wm_hypointensities',
                        'non_wm_hypointensities_L','non_wm_hypointensities_R',
                        'eTIV', 'volBrainSegNotVent','lhSurfaceHoles',
                        'rhSurfaceHoles','SurfaceHoles',]
        ls = df.columns.tolist()
        columns_2_drop = []
        for col in columns_2_remove:
            if col in ls:
                columns_2_drop.append(col)
                ls.remove(col)

        if len(columns_2_drop)>0:
            df.drop(columns=columns_2_drop, inplace=True)
        for col in ls:
            ls[ls.index(col)] = col+'_'+sheet
        df.columns = ls
        return df
