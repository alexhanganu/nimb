#!/bin/python
# 2021.11.02

file_FSLabels   = "nimb/processing/atlases/FreeSurferColorLUT.txt"
file_DipyLabels = "nimb/processing/atlases/label_info.txt"

import os

hemi2 = ['lh','rh']
hemi3 = {'lh':'lh.', 'rh':'rh.', 'lhrh':''}

def get_freesurfer_labels():
    d1 = dict()
    with open(file_FSLabels, "r") as f:
        for line in f:
            if "#" not in line:
                vals = line.split(" ")
                vals = [i for i in vals if i]
                if vals and "\n" not in vals[0]:
                    d1[vals[1]] = vals[0]
    return d1


def get():#_dipy_labels:
    d1 = dict()
    with open(file_DipyLabels, "r") as f:
        for line in f:
            vals = line.split(",")
            vals = [i.replace(" ","").replace("\n","").replace('\"','') for i in vals]
            if "newlabel" in vals[0]:
                vals[0] = "dipy_label"
            if len(vals) > 1:
                d1[vals[2]] = vals[0]
    return d1


def stats_f(fsver, atlas, _dir = "stats", hemi='lhrh'):
    mri_key = ""
    fs_key = "fs"
    if fsver < "7" and "fs6_stats_f" in atlas_data[atlas]:
        fs_key = "fs6"
    if _dir == "mri" and "fs_stats_f_inmridir" in atlas_data[atlas]:
        mri_key = "_inmridir"
    key = f"{fs_key}_stats_f{mri_key}"
    file = atlas_data[atlas][key]

    hemi_dot = hemi3[hemi]
    if 'lh.' in file and hemi_dot not in file:
        file = file.replace("lh.", hemi_dot)
    return os.path.join(_dir, file)


BS_Hip_Tha_stats_f = {
    'Brainstem':('mri/brainstemSsVolumes.v10.txt','stats/brainstem.v12.stats','stats/aseg.brainstem.volume.stats'),
    'HIPL'     :('mri/hippoSfVolumes-T1.v10.txt','stats/lh.hipposubfields.T1.v21.stats','stats/aseg.hippo.lh.volume.stats'),
    'HIPR'     :('mri/hippoSfVolumes-T1.v10.txt','stats/rh.hipposubfields.T1.v21.stats','stats/aseg.hippo.rh.volume.stats'),
    'AMYL'     :('stats/amygdalar-nuclei.lh.T1.v21.stats',),
    'AMYR'     :('stats/amygdalar-nuclei.rh.T1.v21.stats',),
    'THAL'     :('stats/thalamic-nuclei.lh.v12.T1.stats',),
    'THAR'     :('stats/thalamic-nuclei.rh.v12.T1.stats',)}
'''this is used in fs_stats2table to add columns to specific sheets'''
aparc_file_extra_measures = {
    'SurfArea': 'Cortex_WhiteSurfArea',
    'ThickAvg': 'Cortex_MeanThickness',
    'GrayVol' : 'Cortex_CortexVol',
    'NumVert' : 'Cortex_NumVert',}
parc_DS_f2rd ={'L':'lh.aparc.a2009s.stats','R':'rh.aparc.a2009s.stats'}
parc_DK_f2rd ={'L':'lh.aparc.stats','R':'rh.aparc.stats'}

atlas_data = {
    'SubCtx':{
        'atlas_name' :'Subcortical segmentations',
        'hemi' : ['lhrh'],
        'parameters' : {'Volume_mm3':'Vol',         'NVoxels'   :'VolVoxNum',
                        'normMean'  :'VolMeanNorm', 'normStdDev':'VolStdNorm',
                        'normMin'   :'VolMinNorm',  'normMax'   :'VolMaxNorm',
                        'normRange' :'VolRangeNorm'},
        'header':['Left-Thalamus-Proper', 'Right-Thalamus-Proper', 'Left-Thalamus', 'Right-Thalamus', 'Left-Caudate',
                'Right-Caudate', 'Left-Putamen', 'Right-Putamen', 'Left-Pallidum', 'Right-Pallidum', 'Left-Hippocampus',
                'Right-Hippocampus', 'Left-Amygdala', 'Right-Amygdala', 'Left-Accumbens-area',
                'Right-Accumbens-area', 'Left-Lateral-Ventricle', 'Right-Lateral-Ventricle',
                'Left-Inf-Lat-Vent', 'Right-Inf-Lat-Vent', 'Left-Cerebellum-White-Matter',
                'Right-Cerebellum-White-Matter', 'Left-Cerebellum-Cortex', 'Right-Cerebellum-Cortex',
                'Left-VentralDC', 'Right-VentralDC', 'Left-vessel', 'Right-vessel', 'Left-choroid-plexus',
                'Right-choroid-plexus', 'Left-WM-hypointensities', 'Right-WM-hypointensities', 'Left-non-WM-hypointensities',
                'Right-non-WM-hypointensities', 'lhCortexVol', 'rhCortexVol', 'lhCerebralWhiteMatterVol',
                'rhCerebralWhiteMatterVol', 'lhSurfaceHoles', 'rhSurfaceHoles', '3rd-Ventricle',
                '4th-Ventricle', '5th-Ventricle', 'VentricleChoroidVol', 'Brain-Stem', 'CSF', 'Optic-Chiasm',
                'CC_Posterior', 'CC_Mid_Posterior', 'CC_Central', 'CC_Mid_Anterior', 'CC_Anterior', 'CortexVol',
                'SubCortGrayVol', 'TotalGrayVol', 'BrainSegVol', 'BrainSegVolNotVent', 'BrainSegVolNotVentSurf',
                'BrainSegVol-to-eTIV', 'CerebralWhiteMatterVol', 'SupraTentorialVol', 'SupraTentorialVolNotVent',
                'SupraTentorialVolNotVentVox', 'WM-hypointensities', 'non-WM-hypointensities', 'SurfaceHoles',
                'MaskVol', 'MaskVol-to-eTIV', 'eTIV'],
        "fs_stats_f":"aseg.stats",
                },
    'CtxDK':{
        'atlas_name' :'Desikan segmentations',
        'hemi' : ['lh','rh'],
        'parameters' : {
                'GrayVol' :'Vol',
                'ThickAvg':'Thick',
                'SurfArea':'Area',
                'NumVert' :'VertexNum',
                'ThickStd':'ThickStd', 
                'FoldInd' :'FoldInd',
                'MeanCurv':'Curv',
                'GausCurv':'CurvGaus',
                'CurvInd' :'CurvInd'},
        'header':['bankssts', 'caudalanteriorcingulate', 'caudalmiddlefrontal', 'cuneus', 'entorhinal', 'fusiform',
                'inferiorparietal', 'inferiortemporal', 'isthmuscingulate', 'lateraloccipital', 'lateralorbitofrontal',
                'lingual', 'medialorbitofrontal', 'middletemporal', 'parahippocampal', 'paracentral', 'parsopercularis',
                'parsorbitalis', 'parstriangularis', 'pericalcarine', 'postcentral', 'posteriorcingulate', 'precentral',
                'precuneus', 'rostralanteriorcingulate', 'rostralmiddlefrontal', 'superiorfrontal', 'superiorparietal',
                'superiortemporal', 'supramarginal', 'frontalpole', 'temporalpole', 'transversetemporal', 'insula',
                'Cortex_MeanThickness', 'Cortex_WhiteSurfArea', 'Cortex_CortexVol', 'Cortex_NumVert', 'UnsegmentedWhiteMatter'],
        "fs_stats_f":"lh.aparc.stats",
                },
    'CtxDKT':{
        'atlas_name' :'Desikan-Tournoix segmentations',
        'hemi' : ['lh','rh'],
        'parameters' : {
                'GrayVol' :'Vol',
                'ThickAvg':'Thick',
                'SurfArea':'Area',
                'NumVert' :'VertexNum',
                'ThickStd':'ThickStd', 
                'FoldInd' :'FoldInd',
                'MeanCurv':'Curv',
                'GausCurv':'CurvGaus',
                'CurvInd' :'CurvInd'},
        'header':['caudalanteriorcingulate', 'caudalmiddlefrontal', 'cuneus', 'entorhinal', 'fusiform', 'inferiorparietal',
                'inferiortemporal', 'isthmuscingulate', 'lateraloccipital', 'lateralorbitofrontal', 'lingual', 'medialorbitofrontal',
                'middletemporal', 'parahippocampal', 'paracentral', 'parsopercularis', 'parsorbitalis', 'parstriangularis',
                'pericalcarine', 'postcentral', 'posteriorcingulate', 'precentral', 'precuneus', 'rostralanteriorcingulate',
                'rostralmiddlefrontal', 'superiorfrontal', 'superiorparietal', 'superiortemporal', 'supramarginal',
                'transversetemporal', 'insula', 'Cortex_MeanThickness', 'Cortex_WhiteSurfArea', 'Cortex_CortexVol',
                'Cortex_NumVert', 'UnsegmentedWhiteMatter'],
        "fs_stats_f":"lh.aparc.DKTatlas.stats",
                },
    'CtxDS':{
        'atlas_name' :'Destrieux segmentations',
        'hemi' : ['lh','rh'],
        'parameters' : {
                'GrayVol' :'Vol',
                'ThickAvg':'Thick',
                'SurfArea':'Area',
                'NumVert' :'VertexNum',
                'ThickStd':'ThickStd', 
                'FoldInd' :'FoldInd',
                'MeanCurv':'Curv',
                'GausCurv':'CurvGaus',
                'CurvInd' :'CurvInd'},
        'header':['G&S_frontomargin', 'G_and_S_frontomargin', 'G&S_occipital_inf', 'G_and_S_occipital_inf', 'G&S_paracentral',
                'G_and_S_paracentral', 'G&S_subcentral', 'G_and_S_subcentral', 'G&S_transv_frontopol', 'G_and_S_transv_frontopol',
                'G&S_cingul-Ant', 'G_and_S_cingul-Ant', 'G&S_cingul-Mid-Ant', 'G_and_S_cingul-Mid-Ant', 'G&S_cingul-Mid-Post',
                'G_and_S_cingul-Mid-Post', 'G_cingul-Post-dorsal', 'G_cingul-Post-ventral', 'G_cuneus', 'G_front_inf-Opercular',
                'G_front_inf-Orbital', 'G_front_inf-Triangul', 'G_front_middle', 'G_front_sup', 'G_Ins_lg_and_S_cent_ins',
                'G_insular_short', 'G_occipital_middle', 'G_occipital_sup', 'G_oc-temp_lat-fusifor', 'G_oc-temp_med-Lingual',
                'G_oc-temp_med-Parahip', 'G_orbital', 'G_pariet_inf-Angular', 'G_pariet_inf-Supramar', 'G_parietal_sup',
                'G_postcentral', 'G_precentral', 'G_precuneus', 'G_rectus', 'G_subcallosal', 'G_temp_sup-G_T_transv',
                'G_temp_sup-Lateral', 'G_temp_sup-Plan_polar', 'G_temp_sup-Plan_tempo', 'G_temporal_inf', 'G_temporal_middle',
                'Lat_Fis-ant-Horizont', 'Lat_Fis-ant-Vertical', 'Lat_Fis-post', 'Pole_occipital', 'Pole_temporal', 'S_calcarine',
                'S_central', 'S_cingul-Marginalis', 'S_circular_insula_ant', 'S_circular_insula_inf', 'S_circular_insula_sup',
                'S_collat_transv_ant', 'S_collat_transv_post', 'S_front_inf', 'S_front_middle', 'S_front_sup', 'S_interm_prim-Jensen',
                'S_intrapariet_and_P_trans', 'S_oc_middle_and_Lunatus', 'S_oc_sup_and_transversal', 'S_occipital_ant', 'S_oc-temp_lat',
                'S_oc-temp_med_and_Lingual', 'S_orbital_lateral', 'S_orbital_med-olfact', 'S_orbital-H_Shaped', 'S_parieto_occipital',
                'S_pericallosal', 'S_postcentral', 'S_precentral-inf-part', 'S_precentral-sup-part', 'S_suborbital', 'S_subparietal',
                'S_temporal_inf', 'S_temporal_sup', 'S_temporal_transverse', 'Cortex_MeanThickness', 'Cortex_WhiteSurfArea',
                'Cortex_CortexVol', 'Cortex_NumVert', 'UnsegmentedWhiteMatter'],
        "fs_stats_f":"lh.aparc.a2009s.stats",
                },
    'WMDK':{
        'atlas_name' :'White Matter subcortical segmentations based on Desikan atlas',
        'hemi' : ['lhrh'],
        'parameters' : {'Volume_mm3':'Vol',         'NVoxels'   :'VolVoxNum',
                        'normMean'  :'VolMeanNorm', 'normStdDev':'VolStdNorm',
                        'normMin'   :'VolMinNorm',  'normMax'   :'VolMaxNorm',
                        'normRange' :'VolRangeNorm'},
        'header':['wm-lh-bankssts', 'wm-lh-caudalanteriorcingulate', 'wm-lh-caudalmiddlefrontal', 'wm-lh-cuneus',
                'wm-lh-entorhinal', 'wm-lh-fusiform', 'wm-lh-inferiorparietal', 'wm-lh-inferiortemporal',
                'wm-lh-isthmuscingulate', 'wm-lh-lateraloccipital', 'wm-lh-lateralorbitofrontal', 'wm-lh-lingual',
                'wm-lh-medialorbitofrontal', 'wm-lh-middletemporal', 'wm-lh-parahippocampal', 'wm-lh-paracentral',
                'wm-lh-parsopercularis', 'wm-lh-parsorbitalis', 'wm-lh-parstriangularis', 'wm-lh-pericalcarine',
                'wm-lh-postcentral', 'wm-lh-posteriorcingulate', 'wm-lh-precentral', 'wm-lh-precuneus',
                'wm-lh-rostralanteriorcingulate', 'wm-lh-rostralmiddlefrontal', 'wm-lh-superiorfrontal',
                'wm-lh-superiorparietal', 'wm-lh-superiortemporal', 'wm-lh-supramarginal', 'wm-lh-frontalpole',
                'wm-lh-temporalpole', 'wm-lh-transversetemporal', 'wm-lh-insula', 'wm-rh-bankssts',
                'wm-rh-caudalanteriorcingulate', 'wm-rh-caudalmiddlefrontal', 'wm-rh-cuneus', 'wm-rh-entorhinal',
                'wm-rh-fusiform', 'wm-rh-inferiorparietal', 'wm-rh-inferiortemporal', 'wm-rh-isthmuscingulate',
                'wm-rh-lateraloccipital', 'wm-rh-lateralorbitofrontal', 'wm-rh-lingual', 'wm-rh-medialorbitofrontal',
                'wm-rh-middletemporal', 'wm-rh-parahippocampal', 'wm-rh-paracentral', 'wm-rh-parsopercularis',
                'wm-rh-parsorbitalis', 'wm-rh-parstriangularis', 'wm-rh-pericalcarine', 'wm-rh-postcentral',
                'wm-rh-posteriorcingulate', 'wm-rh-precentral', 'wm-rh-precuneus', 'wm-rh-rostralanteriorcingulate',
                'wm-rh-rostralmiddlefrontal', 'wm-rh-superiorfrontal', 'wm-rh-superiorparietal', 'wm-rh-superiortemporal',
                'wm-rh-supramarginal', 'wm-rh-frontalpole', 'wm-rh-temporalpole', 'wm-rh-transversetemporal',
                'wm-rh-insula', 'Left-UnsegmentedWhiteMatter', 'Right-UnsegmentedWhiteMatter'],
        "fs_stats_f":"wmparc.stats",
                },
    'BS':{
        'atlas_name' :'Brainstem segmentations',
        'hemi' : ['lhrh'],
        'parameters' : {'Vol':'Vol'},
        'header':['Medulla','Pons','SCP','Midbrain','Whole_brainstem',],
        'fs_stats_files' :{'fs7':'brainstem.v12.stats',
                        'fs6':'brainstem.v10.stats',},
        "fs_stats_f":"brainstem.v12.stats",
        "fs6_stats_f":"brainstem.v10.stats",
        "fs_stats_f_inmridir":"brainstemSsVolumes.v12.txt",
        "fs6_stats_f_inmridir":"brainstemSsVolumes.v10",
        },
    'HIP':{
        'atlas_name' :'Hippocampus segmentations',
        'hemi' : ['lh','rh'],
        'parameters' : {'Vol':'Vol'},
        'header':['Hippocampal_tail','subiculum', 'subiculum-body', 'subiculum-head', 'CA1',
                'CA1-body', 'CA1-head', 'hippocampal-fissure',
                'presubiculum','presubiculum-body','presubiculum-head','parasubiculum','molecular_layer_HP',
                'molecular_layer_HP-head','molecular_layer_HP-body','GC-ML-DG','GC-ML-DG-body', 'GC-ML-DG-head'
                'CA3', 'CA3-body', 'CA3-head', 'CA4', 'CA4-body', 'CA4-head', 'fimbria','HATA','Whole_hippocampus',
                'Whole_hippocampal_body', 'Whole_hippocampal_head'],
        "fs_stats_f":"hipposubfields.lh.T1.v21.stats",
        "fs6_stats_f":"hipposubfields.lh.T1.v10.stats",
        "fs_stats_f_inmridir":"lh.hippoSfVolumes-T1.v21.txt",
        "fs6_stats_f_inmridir":"lh.hippoSfVolumes-T1.v10.txt",
                },
    'AMY':{
        'atlas_name' :'Amygdala segmentations',
        'hemi' : ['lh','rh'],
        'parameters' : {'Vol':'Vol'},
        'header': ['Lateral-nucleus', 'Basal-nucleus', 'Accessory-Basal-nucleus', 'Anterior-amygdaloid-area-AAA',
                    'Central-nucleus', 'Medial-nucleus', 'Cortical-nucleus', 'Corticoamygdaloid-transitio',
                    'Paralaminar-nucleus', 'Whole_amygdala'],
        "fs_stats_f":"amygdalar-nuclei.lh.T1.v21.stats",
        "fs_stats_f_inmridir":"lh.amygNucVolumes-T1.v21.txt",
                    },
    'THA':{
        'atlas_name' :'Thalamus segmentations',
        'hemi' : ['lh','rh'],
        'parameters' : {'Vol':'Vol'},
        'header': ['AV', 'CeM', 'CL', 'CM', 'LD', 'LGN', 'LP', 'L-Sg', 'MDl', 'MDm', 'MGN', 'MV(Re)', 'Pc', 'Pf', 'Pt',
                    'PuA', 'PuI', 'PuL', 'PuM', 'VA', 'VAmc', 'VLa', 'VLp', 'VM', 'VPL', 'Whole_thalamus'],
        "fs_stats_f":"thalamic-nuclei.lh.v12.T1.stats",
        "fs_stats_f_inmridir":"ThalamicNuclei.v12.T1.volumes.txt",
                    },
    'HypoTHA':{
        'atlas_name' :'HypoThalamus segmentations',
        'hemi' : ['lh','rh'],
        'parameters' : {'Vol':'Vol'},
        'header': ['SON', 'PVN', 'TMN'],
        "fs_stats_f":"lh.hypothalamic_subunits_volumes.v1.stats",
                    },
}


header_fs2nimb = {'Medulla':'medulla','Pons':'pons','SCP':'scp','Midbrain':'midbrain',
                'Whole_brainstem':'wholeBrainstem',
                'Hippocampal_tail':'hippocampal-tail',
                'subiculum':'subiculum','subiculum-body':'subiculum-body','subiculum-head':'subiculum-head',
                'CA1':'ca1','CA1-body':'ca1-body','CA1-head':'ca1-head','hippocampal-fissure':'fissureHippocampal',
                'presubiculum':'presubiculum','presubiculum-body':'presubiculum-body','presubiculum-head':'presubiculum-head',
                'parasubiculum':'parasubiculum',
                'molecular_layer_HP':'molecularLayerHP','molecular_layer_HP-head':'molecularLayerHP-head',
                'molecular_layer_HP-body':'molecularLayerHP-body',
                'GC-ML-DG':'gcmldg','GC-ML-DG-body':'gcmldg-body','GC-ML-DG-head':'gcmldg-head',
                'CA3':'ca3','CA3-body':'ca3-body','CA3-head':'ca3-head',
                'CA4':'ca4','CA4-body':'ca4-body','CA4-head':'ca4-head',
                'fimbria':'fimbria','HATA':'hata','Whole_hippocampal_body':'wholeHippocampus-body',
                'Whole_hippocampal_head':'wholeHippocampus-head',
                'Whole_hippocampus':'wholeHippocampus',
                'Lateral-nucleus': 'Lateral-nucleus', 'Basal-nucleus': 'Basal-nucleus', 'Accessory-Basal-nucleus': 'Accessory-Basal-nucleus',
                'Anterior-amygdaloid-area-AAA': 'Anterior-amygdaloid-area-AAA', 'Central-nucleus': 'Central-nucleus',
                'Medial-nucleus': 'Medial-nucleus', 'Cortical-nucleus': 'Cortical-nucleus',
                'Corticoamygdaloid-transitio': 'Corticoamygdaloid-transitio', 'Paralaminar-nucleus': 'Paralaminar-nucleus',
                'Whole_amygdala': 'WholeAmygdala',
                'AV': 'AV', 'CeM': 'CeM', 'CL': 'CL', 'CM': 'CM', 'LD': 'LD', 'LGN': 'LGN', 'LP': 'LP', 'L-Sg': 'L-Sg',
                'MDl':'MDl', 'MDm': 'MDm', 'MGN': 'MGN', 'MV(Re)': 'MV(Re)', 'Pc': 'Pc', 'Pf': 'Pf', 'Pt': 'Pt', 'PuA': 'PuA',
                'PuI':'PuI', 'PuL': 'PuL', 'PuM': 'PuM', 'VA': 'VA', 'VAmc': 'VAmc', 'VLa': 'VLa', 'VLp': 'VLp', 'VM': 'VM',
                'VPL':'VPL', 'Whole_thalamus': 'WholeThalamus',
                'Left-Thalamus-Proper'        :'thalamusProper_lh',        'Right-Thalamus-Proper'        :'thalamusProper_rh',
                'Left-Thalamus'               :'thalamusL',                'Right-Thalamus'               :'thalamusR',
                'Left-Caudate'                :'caudate_lh',               'Right-Caudate'                :'caudate_rh',
                'Left-Putamen'                :'putamen_lh',               'Right-Putamen'                :'putamen_rh',
                'Left-Pallidum'               :'pallidum_lh',              'Right-Pallidum'               :'pallidum_rh',
                'Left-Hippocampus'            :'hippocampus_lh',           'Right-Hippocampus'            :'hippocampus_rh',
                'Left-Amygdala'               :'amygdala_lh',              'Right-Amygdala'               :'amygdala_rh',
                'Left-Accumbens-area'         :'accumbensArea_lh',         'Right-Accumbens-area'         :'accumbensArea_rh',
                'Left-Lateral-Ventricle'      :'ventricleLateral_lh',      'Right-Lateral-Ventricle'      :'ventricleLateral_rh',
                'Left-Inf-Lat-Vent'           :'ventricleInfLateral_lh',   'Right-Inf-Lat-Vent'           :'ventricleInfLateral_rh',
                'Left-Cerebellum-White-Matter':'cerebellumWhiteMatter_lh', 'Right-Cerebellum-White-Matter':'cerebellumWhiteMatter_rh',
                'Left-Cerebellum-Cortex'      :'cerebellumCortex_lh',      'Right-Cerebellum-Cortex'      :'cerebellumCortex_rh',
                'Left-VentralDC'              :'ventralDC_lh',             'Right-VentralDC'              :'ventralDC_rh',
                'Left-vessel'                 :'vessel_lh',                'Right-vessel'                 :'vessel_rh',
                'Left-choroid-plexus'         :'choroidPlexus_lh',         'Right-choroid-plexus'         :'choroidPlexus_rh',
                'Left-WM-hypointensities'     :'wm_hypointensities_lh',    'Right-WM-hypointensities'     :'WMhypointensities_rh',
                'Left-non-WM-hypointensities' :'nonWMhypointensities_lh',  'Right-non-WM-hypointensities' :'nonWMhypointensities_rh',                
                'lhCortexVol'                 :'volCortex_lh',             'rhCortexVol'                  :'volCortex_rh',
                'lhCerebralWhiteMatterVol'    :'volCerebralWhiteMatter_lh','rhCerebralWhiteMatterVol'     :'volCerebralWhiteMatter_rh',
                'lhSurfaceHoles'              :'surfaceHoles_lh',          'rhSurfaceHoles'               :'surfaceHoles_rh',
                '3rd-Ventricle':'ventricle_3rd',
                '4th-Ventricle':'ventricle_4th',
                '5th-Ventricle':'ventricle_5th',
                'VentricleChoroidVol':'volVentricleChoroid',
                'Brain-Stem':'brainstem', 'CSF':'csf', 'Optic-Chiasm':'opticChiasm',
                'CC_Posterior':'ccPosterior','CC_Mid_Posterior':'ccMidPosterior',
                'CC_Central':'ccCentral',    'CC_Mid_Anterior':'ccMidAnterior',  'CC_Anterior':'ccAnterior',
                'CortexVol'                  :'volCortex',
                'SubCortGrayVol'             :'volSubCortGray',
                'TotalGrayVol'               :'volTotalGray',
                'BrainSegVol'                :'volBrainSeg',
                'BrainSegVolNotVent'         :'volBrainSegNotVent',
                'BrainSegVolNotVentSurf'     :'volBrainSegNotVentSurf',
                'BrainSegVol-to-eTIV'        :'volBrainSegtoeTIV',
                'CerebralWhiteMatterVol'     :'volCerebralWhiteMatter',
                'SupraTentorialVol'          :'volSupraTentorial',
                'SupraTentorialVolNotVent'   :'volSupraTentorialNotVent',
                'SupraTentorialVolNotVentVox':'volSupraTentorialNotVentVox',
                'WM-hypointensities'         :'wm_hypointensities',
                'non-WM-hypointensities'     :'nonWMhypointensities',
                'SurfaceHoles'               :'surfaceHoles',
                'MaskVol'                    :'volMask',
                'MaskVol-to-eTIV'            :'volMasktoeTIV',
                'eTIV'                       :'eTIV',
                'bankssts':'temporal_superior_sulcus_bank',
                'caudalanteriorcingulate':'cingulate_anterior_caudal',
                'caudalmiddlefrontal':'frontal_middle_caudal',
                'cuneus':'occipital_cuneus',
                'entorhinal':'temporal_entorhinal',
                'fusiform':'temporal_fusiform',
                'inferiorparietal':'parietal_inferior',
                'inferiortemporal':'temporal_inferior',
                'isthmuscingulate':'cingulate_isthmus',
                'lateraloccipital':'occipital_lateral',
                'lateralorbitofrontal':'frontal_orbitolateral',
                'lingual':'occipital_lingual',
                'medialorbitofrontal':'frontal_orbitomedial',
                'middletemporal':'temporal_middle',
                'parahippocampal':'temporal_parahippocampal',
                'paracentral':'frontal_paracentral',
                'parsopercularis':'frontal_parsopercularis',
                'parsorbitalis':'frontal_parsorbitalis',
                'parstriangularis':'frontal_parstriangularis',
                'pericalcarine':'occipital_pericalcarine',
                'postcentral':'parietal_postcentral',
                'posteriorcingulate':'cingulate_posterior',
                'precentral':'frontal_precentral',
                'precuneus':'parietal_precuneus',
                'rostralanteriorcingulate':'cingulate_anterior_rostral',
                'rostralmiddlefrontal':'frontal_middle_rostral',
                'superiorfrontal':'frontal_superior',
                'superiorparietal':'parietal_superior',
                'superiortemporal':'temporal_superior',
                'supramarginal':'parietal_supramarginal',
                'frontalpole':'frontal_pole',
                'temporalpole':'temporal_pole',
                'transversetemporal':'temporal_transverse',
                'insula':'insula',
                'Cortex_MeanThickness':'cortex_thickness',
                'Cortex_WhiteSurfArea':'cortex_area',
                'Cortex_CortexVol':'cortex_vol',
                'Cortex_NumVert':'cortex_numvert',
                'UnsegmentedWhiteMatter':'WMUnsegmented',
                'G&S_frontomargin': 'frontal_margin_GS',
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
    '''extract the nimb names of FreeSurfer structures
    '''
    nimb_names = list()
    for atlas in atlas_data:
        header = atlas_data[atlas]["header"]
        for fs_roi in header:
            name_structures.append(header_fs2nimb[fs_roi])
    return nimb_names


def get_names_of_measurements():
    measurements = []

    for atlas in atlas_data:
        for meas in list(atlas_data[atlas]['parameters'].values()):
            for hemi in atlas_data[atlas]['hemi']:
                measurements.append(meas+hemi+atlas)

    return measurements


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


class GetFSStructureMeasurement:
    def __init__(self):
        self.ls_meas   = get_names_of_measurements()
        self.ls_struct = get_names_of_structures()

    def get(self, name, ls_err = list()):
        meas_try1   = name[name.rfind('_')+1:]
        struct_try1 = name.replace(f'_{meas_try1}','')
        if struct_try1 in self.ls_struct and meas_try1 in self.ls_meas:
            return meas_try1, struct_try1, ls_err
        elif name == 'eTIV':
            return 'eTIV', 'eTIV', ls_err
        else:
            measurement = name
            structure = name
            i = 0
            while structure not in self.ls_struct and i<5:
                if measurement not in self.ls_meas:
                    for meas in self.ls_meas:
                        if meas in name:
                            measurement = meas
                            break
                else:
                    self.ls_meas = self.ls_meas[self.ls_meas.index(measurement)+1:]
                    for meas in self.ls_meas:
                        if meas in name:
                            measurement = meas
                            break
                structure = name.replace('_'+measurement,'')
                i += 1
            if f'{structure}_{measurement}' != name:
                    ls_err.append(name)
            return measurement, structure, ls_err


class RReplace():
    '''written for NIMB ROIs
        created based on  Desikan/ Destrieux atlases + FreeSurfer measurement (thickness, area, etc.), + Hemisphere
        e.g.: frontal_middle_caudal_ThickL_DK, where DK stands for Desikan and DS stands for Destrieux
        extracts roi name and measurement
        combines roi with contralateral roi
    Args: feature to
    Return: {'feature_name':('Left-corresponding-feature', 'Right-corresponding-feature')}
    '''

    def __init__(self, features):
        self.add_contralateral_features(features)
        self.contralateral_features = self.lhrh

    def add_contralateral_features(self, features):
        self.lhrh = {}
        for feat in features:
            meas, struct, _ = GetFSStructureMeasurement().get(feat)
            lr_feature = feat.replace(f'_{meas}','')
            if lr_feature not in self.lhrh:
                self.lhrh[lr_feature] = ''
            if meas != 'VolSeg':
                new_struct, hemi = self.get_contralateral_meas(meas)
                contra_feat = f'{struct}_{new_struct}'
            else:
                new_struct, hemi = self.get_contralateral_meas(struct)
                contra_feat = f'{new_struct}_{meas}'
            if 'none' not in new_struct:
                if hemi == 'L':
                    self.lhrh[lr_feature] = (contra_feat, feat)
                else:
                    self.lhrh[lr_feature] = (feat, contra_feat)
        # self.lhrh

    def get_contralateral_meas(self, param):
        if "L" in param:
            return self.rreplace(param, "L", "R", 1), "R"
        elif "R" in param:
            return self.rreplace(param, "R", "L", 1), "L"
        else:
            # print('    no laterality in : {}'.format(param))
            return 'none', 'none'

    def rreplace(self, s, old, new, occurence):
        li = s.rsplit(old, 1)
        return new.join(li)


def get_fs_rois_lateralized(atlas, meas = None):
    '''
    create a dictionary with atlas-based FreeSurfer ROIs, with hemisphere based classification
    available atlas are based on all_data
    if atlas defined:
        Return: {roi':('Left-roi', 'Right-roi')}
    else:
        Return: {atlas: {measure: {roi':('roi_lh', 'roi_rh')}}}
    '''
    def get_measures(meas, atlas):
        if not meas:
            return all_data[atlas]['parameters'].values()
        else:
            return [meas]

    def get_subcort_lat():
        subcort_twohemi_rois = list()
        for i in all_data['SubCort']['header'].values():
            if i.endswith(f'_{hemi[0]}') or i.endswith(f'_{hemi[1]}'):
                roi = i.strip(f'_{hemi[0]}').strip(f'_{hemi[1]}')
                if roi not in subcort_twohemi_rois:
                    subcort_twohemi_rois.append(roi)
        return subcort_twohemi_rois

    def get_rois(atlas):
        if atlas != 'SubCort':
            return all_data[atlas]['header'].values()
        else:
            return get_subcort_lat()

    def populate_lateralized(meas_user, ls_atlases):
        lateralized = {atlas:{} for atlas in ls_atlases}
        for atlas in lateralized:
            measures = get_measures(meas_user, atlas)
            headers  = get_rois(atlas)
            for meas in measures:
                lateralized[atlas] = {meas:{header: {} for header in headers}}
                for header in lateralized[atlas][meas]:
                    lateralized[atlas][meas][header] = (f'{header}_{meas}_{hemi[0]}_{atlas}',
                                                    f'{header}_{meas}_{hemi[1]}_{atlas}')
        return lateralized


    if atlas == 'SubCort' or atlas in all_data['atlases'] and all_data[atlas]['two_hemi']:
        return populate_lateralized(meas, [atlas])
    else:
        ls_atlases = [atlas for atlas in all_data['atlases'] if all_data[atlas]['two_hemi']] + ['SubCort']
        print(f'{atlas}\
            is ill-defined or not lateralized. Please use one of the following names:\
            {ls_atlases}. Returning all lateralized atlases')
        return populate_lateralized(meas, ls_atlases)


name_structures  = get_names_of_structures()
name_measurement = get_names_of_measurements()