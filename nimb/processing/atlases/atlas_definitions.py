#!/bin/python
# 2022.07.02

import os

file_FSLabels   = "nimb/processing/atlases/FreeSurferColorLUT.txt"
file_DipyLabels = "nimb/processing/atlases/label_info.txt"

'''this is used in fs_stats2table to add columns to specific sheets'''
aparc_file_extra_measures = {
    'SurfArea': 'Cortex_WhiteSurfArea',
    'ThickAvg': 'Cortex_MeanThickness',
    'GrayVol' : 'Cortex_CortexVol',
    'NumVert' : 'Cortex_NumVert',}

hemis = ['lh','rh']
hemis_long = {"Left": "lh",
              "Right": "rh",}
params_vols = {'Volume_mm3':'Vol',
              'NVoxels'    :'VolVoxNum',
              'normMean'   :'VolMeanNorm',
              'normStdDev' :'VolStdNorm',
              'normMin'    :'VolMinNorm',
              'normMax'    :'VolMaxNorm',
              'normRange'  :'VolRangeNorm',}
params_ctx = {'GrayVol' :'Vol',
              'ThickAvg':'Thick',
              'SurfArea':'Area',
              'NumVert' :'NumVert',
              'ThickStd':'ThickStd', 
              'FoldInd' :'FoldInd',
              'MeanCurv':'Curv',
              'GausCurv':'CurvGaus',
              'CurvInd' :'CurvInd'}

atlas_data = {
    'SubCtx':{'atlas_name' :'Subcortical',
            'short_name': 'Subcortical',
            'group':'subcortical',
            'hemi' : ["".join(hemis)],
            'parameters' : params_vols,
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
            'header_suppl':[],
            "fs_stats_f":"aseg.stats",},
    'CtxDK':{'atlas_name' :'Desikan-Killiany',
            'short_name': 'DesikanKilliany',
            'group':'cortical',
            'hemi' : hemis,
            'parameters' : params_ctx,
            'header':['bankssts', 'caudalanteriorcingulate', 'caudalmiddlefrontal', 'cuneus', 'entorhinal', 'fusiform',
                    'inferiorparietal', 'inferiortemporal', 'isthmuscingulate', 'lateraloccipital', 'lateralorbitofrontal',
                    'lingual', 'medialorbitofrontal', 'middletemporal', 'parahippocampal', 'paracentral', 'parsopercularis',
                    'parsorbitalis', 'parstriangularis', 'pericalcarine', 'postcentral', 'posteriorcingulate', 'precentral',
                    'precuneus', 'rostralanteriorcingulate', 'rostralmiddlefrontal', 'superiorfrontal', 'superiorparietal',
                    'superiortemporal', 'supramarginal', 'frontalpole', 'temporalpole', 'transversetemporal', 'insula',],
            'header_suppl':['Cortex_MeanThickness', 'Cortex_WhiteSurfArea', 'Cortex_CortexVol',
                    'Cortex_NumVert', 'UnsegmentedWhiteMatter'],
            "fs_stats_f":"lh.aparc.stats",},
    'CtxDKT':{'atlas_name' :'Desikan-Killiany-Tourville',
            'short_name': 'DesikanKillianyTourville',
            'group':'cortical',
            'hemi' : hemis,
            'parameters' : params_ctx,
            'header':['caudalanteriorcingulate', 'caudalmiddlefrontal', 'cuneus', 'entorhinal', 'fusiform', 'inferiorparietal',
                    'inferiortemporal', 'isthmuscingulate', 'lateraloccipital', 'lateralorbitofrontal', 'lingual', 'medialorbitofrontal',
                    'middletemporal', 'parahippocampal', 'paracentral', 'parsopercularis', 'parsorbitalis', 'parstriangularis',
                    'pericalcarine', 'postcentral', 'posteriorcingulate', 'precentral', 'precuneus', 'rostralanteriorcingulate',
                    'rostralmiddlefrontal', 'superiorfrontal', 'superiorparietal', 'superiortemporal', 'supramarginal',
                    'transversetemporal', 'insula', ],
            'header_suppl':['Cortex_MeanThickness', 'Cortex_WhiteSurfArea', 'Cortex_CortexVol',
                    'Cortex_NumVert', 'UnsegmentedWhiteMatter'],
            "fs_stats_f":"lh.aparc.DKTatlas.stats",},
    'CtxDS':{'atlas_name' :'Destrieux',
            'short_name': 'Destrieux',
            'group':'cortical',
            'hemi' : hemis,
            'parameters' : params_ctx,
            'header':['G_and_S_frontomargin', 'G_and_S_occipital_inf', 'G_and_S_paracentral', 'G_and_S_subcentral',
                      'G_and_S_transv_frontopol', 'G_and_S_cingul-Ant', 'G_and_S_cingul-Mid-Ant', 'G_and_S_cingul-Mid-Post',
                      'G_cingul-Post-dorsal', 'G_cingul-Post-ventral', 'G_cuneus', 'G_front_inf-Opercular', 'G_front_inf-Orbital',
                      'G_front_inf-Triangul', 'G_front_middle', 'G_front_sup', 'G_Ins_lg_and_S_cent_ins', 'G_insular_short',
                      'G_occipital_middle', 'G_occipital_sup', 'G_oc-temp_lat-fusifor', 'G_oc-temp_med-Lingual', 'G_oc-temp_med-Parahip',
                      'G_orbital', 'G_pariet_inf-Angular', 'G_pariet_inf-Supramar', 'G_parietal_sup', 'G_postcentral', 'G_precentral',
                      'G_precuneus', 'G_rectus', 'G_subcallosal', 'G_temp_sup-G_T_transv', 'G_temp_sup-Lateral', 'G_temp_sup-Plan_polar', 
                      'G_temp_sup-Plan_tempo', 'G_temporal_inf', 'G_temporal_middle', 'Lat_Fis-ant-Horizont', 'Lat_Fis-ant-Vertical',
                      'Lat_Fis-post', 'Pole_occipital', 'Pole_temporal', 'S_calcarine', 'S_central', 'S_cingul-Marginalis',
                      'S_circular_insula_ant', 'S_circular_insula_inf', 'S_circular_insula_sup', 'S_collat_transv_ant',
                      'S_collat_transv_post', 'S_front_inf', 'S_front_middle', 'S_front_sup', 'S_interm_prim-Jensen',
                      'S_intrapariet_and_P_trans', 'S_oc_middle_and_Lunatus', 'S_oc_sup_and_transversal', 'S_occipital_ant',
                      'S_oc-temp_lat', 'S_oc-temp_med_and_Lingual', 'S_orbital_lateral', 'S_orbital_med-olfact', 'S_orbital-H_Shaped',
                      'S_parieto_occipital', 'S_pericallosal', 'S_postcentral', 'S_precentral-inf-part', 'S_precentral-sup-part',
                      'S_suborbital', 'S_subparietal', 'S_temporal_inf', 'S_temporal_sup', 'S_temporal_transverse',],
            'header_suppl':['Cortex_MeanThickness', 'Cortex_WhiteSurfArea', 'Cortex_CortexVol',
                    'Cortex_NumVert', 'UnsegmentedWhiteMatter'],
            "fs_stats_f":"lh.aparc.a2009s.stats",},
    'WMDK':{'atlas_name' :'White-Matter-Desikan',
            'short_name': 'WhiteMatterDesikan',
            'group':'cortical',
            'hemi' : ["".join(hemis)],
            'parameters' : params_vols,
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
            'header_suppl':[],
            "fs_stats_f":"wmparc.stats",},
    'BS':{'atlas_name' :'Brainstem',
            'short_name': 'Brainstem',
            'group':'nuclei',
            'hemi' : ["".join(hemis)],
            'parameters' : {'Vol':'Vol'},
            'header':['Medulla','Pons','SCP','Midbrain','Whole_brainstem',],
            'header_suppl':[],
            'fs_stats_files' :{'fs7':'brainstem.v12.stats',
                            'fs6':'brainstem.v10.stats',},
            "fs_stats_f":"brainstem.v12.stats",
            "fs6_stats_f":"brainstem.v10.stats",
            "fs_stats_f_inmridir":"brainstemSsVolumes.v12.txt",
            "fs6_stats_f_inmridir":"brainstemSsVolumes.v10",},
    'HIP':{'atlas_name' :'Hippocampus',
            'short_name': 'Hippocampus',
            'group':'nuclei',
            'hemi' : hemis,
            'parameters' : {'Vol':'Vol'},
            'header':['Hippocampal_tail','subiculum', 'subiculum-body', 'subiculum-head', 'CA1',
                    'CA1-body', 'CA1-head', 'hippocampal-fissure',
                    'presubiculum','presubiculum-body','presubiculum-head','parasubiculum','molecular_layer_HP',
                    'molecular_layer_HP-head','molecular_layer_HP-body','GC-ML-DG','GC-ML-DG-body', 'GC-ML-DG-head',
                    'CA3', 'CA3-body', 'CA3-head', 'CA4', 'CA4-body', 'CA4-head', 'fimbria','HATA','Whole_hippocampus',
                    'Whole_hippocampal_body', 'Whole_hippocampal_head'],
            'header_suppl':[],
            "fs_stats_f":"hipposubfields.lh.T1.v21.stats",
            "fs6_stats_f":"hipposubfields.lh.T1.v10.stats",
            "fs_stats_f_inmridir":"lh.hippoSfVolumes-T1.v21.txt",
            "fs6_stats_f_inmridir":"lh.hippoSfVolumes-T1.v10.txt",},
    'AMY':{'atlas_name' :'Amygdala',
            'short_name': 'Amygdala',
            'group':'nuclei',
            'hemi' : hemis,
            'parameters' : {'Vol':'Vol'},
            'header': ['Lateral-nucleus', 'Basal-nucleus', 'Accessory-Basal-nucleus', 'Anterior-amygdaloid-area-AAA',
                        'Central-nucleus', 'Medial-nucleus', 'Cortical-nucleus', 'Corticoamygdaloid-transitio',
                        'Paralaminar-nucleus', 'Whole_amygdala'],
            'header_suppl':[],
            "fs_stats_f":"amygdalar-nuclei.lh.T1.v21.stats",
            "fs_stats_f_inmridir":"lh.amygNucVolumes-T1.v21.txt",},
    'THA':{'atlas_name' :'Thalamus',
            'short_name': 'Thalamus',
            'group':'nuclei',
            'hemi' : hemis,
            'parameters' : {'Vol':'Vol'},
            'header': ['AV', 'CeM', 'CL', 'CM', 'LD', 'LGN', 'LP', 'L-Sg', 'MDl', 'MDm', 'MGN', 'MV(Re)', 'Pc', 'Pf', 'Pt',
                        'PuA', 'PuI', 'PuL', 'PuM', 'VA', 'VAmc', 'VLa', 'VLp', 'VM', 'VPL', 'Whole_thalamus'],
            'header_suppl':[],
            "fs_stats_f":"thalamic-nuclei.lh.v12.T1.stats",
            "fs_stats_f_inmridir":"ThalamicNuclei.v12.T1.volumes.txt",},
    'HypoTHA':{'atlas_name' :'HypoThalamus',
            'short_name': 'Hypothalamus',
            'group':'nuclei',
            'hemi' : ["".join(hemis)],
            'parameters' : {'Vol':'Vol'},
            'header': ['Left-Anterior-Inferior', 'Left-Anterior-Superior',
                       'Left-Posterior', 'Left-Tubular-Inferior',
                       'Left-Tubular-Superior',
                       'Right-Anterior-Inferior', 'Right-Anterior-Ssuperior',
                       'Right-Posterior', 'Right-Tubular-Inferior',
                       'Right-Tubular-Superior',
                       'Whole-Left', 'Whole-Right'],
            'header_suppl':[],
            "fs_stats_f":"hypothalamic_subunits_volumes.v1.stats",},}


def params_atlas2nimb(atlas_param):
    parameters = {'Volume_mm3':'Vol',
                  'NVoxels'   :'VolVoxNum',
                  'normMean'  :'VolMeanNorm',
                  'normStdDev':'VolStdNorm',
                  'normMin'   :'VolMinNorm',
                  'normMax'   :'VolMaxNorm',
                  'normRange' :'VolRangeNorm',
                  'Vol'       :'Vol',
                  'GrayVol'   :'Vol',
                  'ThickAvg'  :'Thick',
                  'ThickStd'  :'ThickStd', 
                  'SurfArea'  :'Area',
                  'NumVert'   :'VertexNum',
                  'FoldInd'   :'FoldInd',
                  'MeanCurv'  :'Curv',
                  'GausCurv'  :'CurvGaus',
                  'CurvInd'   :'CurvInd'}
    return parameters[atlas_param]

lobes =    {"frontal"  :["precentral","paracentral","parsopercularis",
                         "parsorbitalis","parstriangularis","subcentral",
                         "orbital","rectus"],
            "parietal" :["postcentral","precuneus","supramarginal"],
            "temporal" :["bankssts","entorhinal","parahippocampal"],
            "occipital":["cuneus","fusiform","lingual","pericalcarine","calcarine"],
            "cingulate":["subcallosal",],
            "insula"   :["insular",]}

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


def header_atlas2nimb():
    """transforms the ROIs of all atlases
        in a nimb format
        aiming to use the same names and formats for all ROIs
    Return: dict(atlas_roi: nimb_roi)
    """
    # defining lobes, abbreviations and corresponding regions
    lobes_define ={"frontal"  :["fronto","front"],
                   "parietal" :["parieto","pariet",],
                   "temporal" :["temp",],
                   "occipital":["oc-","oc_"],
                   "cingulate":["CC_","cingul"],
                   "insula"   :["Ins_",],}
    rois      ={"WhiteMatter" :"_wm",
                "White-Matter":"_wm",
                "_wmVol"      :"_Vol_wm",
                "insular_"    :"insula",
                "VentralDC"   : "Ventral_dincephalon"} #    "fusifor"     :"fusiform",
    lobes_abbrev = [i for k in lobes_define.values() for i in k]

    # roi adjusting start
    header_nimb = dict()
    for atlas in atlas_data:
        header = atlas_data[atlas]["header"]
        if "header_suppl" in atlas_data[atlas]:
            header = header + atlas_data[atlas]["header_suppl"]

        for atlas_roi in header:
            nimb_roi = atlas_roi

            # adjusting names for the WMDK atlas,
            # moving wm abbreviation and hemi to the end
            for hemi in hemis:
                if hemi in nimb_roi[:5]:
                    if "wm-"+hemi in nimb_roi[:5]:
                        nimb_roi = nimb_roi[5:]+"_wm_"+hemi
                    else:
                        nimb_roi = nimb_roi[2:]+"_"+hemi

            # renaming some ROIs for similarity
            for roi in rois:
                if roi in nimb_roi:
                    nimb_roi = nimb_roi.replace(roi, rois[roi])
            if "Ventricle" in nimb_roi or "Lat-Vent" in nimb_roi:
                nimb_roi = "Ventricle_"+nimb_roi.replace("Ventricle","").replace("Vent","")

            # move hemisphere abbreviation to the end
            for hemi_long in hemis_long:
                if hemi_long in nimb_roi:
                    nimb_roi = nimb_roi.replace(hemi_long, "")+"_"+hemis_long[hemi_long]

            # move Destrieux G and S abbreviations to the end
            if "G_and_S_" in nimb_roi:
                nimb_roi = nimb_roi.replace("G_and_S_","")+"_G_and_S"
            for GS in ("G_", "S_"):
                if GS in nimb_roi[:2]:
                    nimb_roi = nimb_roi.replace(GS,"")+"_"+GS.replace("_","")

            # cuneus and precuneus regions seems to interfer; couldn't include otherwise
            if "cuneus" in nimb_roi:
                if "precuneus" in nimb_roi:
                    lobe =[i for i in lobes if "precuneus" in lobes[i]][0]
                    nimb_roi = lobe+"_"+nimb_roi
                else:
                    lobe =[i for i in lobes if "cuneus" in lobes[i]][0]
                    nimb_roi = lobe+"_"+nimb_roi
            if "oc-temp" in nimb_roi:
                nimb_roi = "occipital_temporal"+nimb_roi.replace("oc-temp","")

            # adjusting lobes based on lobe names, their abbreviations and regions
            for abbrev in lobes_abbrev:
                lobe =[i for i in lobes_define if abbrev in lobes_define[i]][0]
                if abbrev in nimb_roi and lobe not in nimb_roi:
                    nimb_roi = nimb_roi.replace(abbrev, lobe)
                    break
            for lobe in lobes:
                if lobe in nimb_roi:
                    nimb_roi = lobe+"_"+nimb_roi.replace(lobe, "")
                elif "cuneus" not in nimb_roi:
                    for lobe_roi in lobes[lobe]:
                        if lobe_roi in nimb_roi.lower() and not nimb_roi.startswith(lobe):
                            nimb_roi = lobe+"_"+nimb_roi

            # couldn't find another method to change this ROI
            if "central" in nimb_roi:
                lobed = False
                for lobe in lobes:
                    if lobe in nimb_roi:
                        lobed = True
                        break
                if not lobed:
                    nimb_roi = "frontal_"+nimb_roi

            # final adjustments for underscores, minuses and ending
            if "-" in nimb_roi:
                nimb_roi = nimb_roi.replace("-","")
            if "__" in nimb_roi:
                nimb_roi = nimb_roi.replace("___","_").replace("__","_")
            if nimb_roi[-1] == "_":
                nimb_roi = nimb_roi[:-1]
            header_nimb[atlas_roi] = nimb_roi
    return header_nimb


header_fs2nimb = header_atlas2nimb()


def atlas_roi_hemi_meas(atlas,
                        hemi,
                        meas = "",
                        meas_add = True,
                        hemi_underscored = True,
                        hemi_last = True):
    """creates the FS_nimb-ROI structure
    Args:
        atlas: atlas name as per atlas_data
        hemi: hemisphere as per atlas_data[atlas]["hemi"]
        meas: parameters as per atlas_data[atlas]["parameters"]
        meas_add: True will add the meas in the name
        hemi_underscored: True will add an underscore before the hemi
        hemi_last: True will put hemi in the last position, else: atlas is last
    """
    _hemi = f"_{hemi}"
    if not hemi_underscored:
        _hemi = hemi
    if not meas_add:
        meas = ""

    ending = f"{meas}{_hemi}_{atlas}"
    if hemi_last:
        ending = f"{meas}_{atlas}{_hemi}"
    if ending[0] == "_":
        ending = ending[1:]
    return ending


def get_names_of_structures(name_type = "nimb"):
    '''extract the nimb names of FreeSurfer structures
    '''
    struct_names = list()
    for atlas in atlas_data:
        header = atlas_data[atlas]["header"]
        for atlas_roi in header:
            if name_type == "nimb" and atlas_roi in header_fs2nimb:
                struct_names.append(header_fs2nimb[atlas_roi])
            else:
                struct_names.append(atlas_roi)
                print(atlas_roi, "not in header_fs2nimb")
    return struct_names


def get_names_of_measurements(name_type = "nimb"):
    measurements = []
    for atlas in atlas_data:
        for meas in list(atlas_data[atlas]['parameters'].keys()):
            if name_type == "nimb":
                meas = params_atlas2nimb(meas)
            for hemi in atlas_data[atlas]['hemi']:
                measurements.append(atlas_roi_hemi_meas(atlas, hemi, meas))
    return measurements

name_structures  = get_names_of_structures()
name_measurement = get_names_of_measurements()


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


class cols_per_measure_per_atlas():

    def __init__(self, ls_columns):
        self.ls_columns = ls_columns
        self.cols_to_meas_to_atlas = self.get_columns()

    def get_columns(self):
        result = dict()
        for atlas in atlas_data['atlases']:
            result[atlas] = dict()
            for meas in atlas_data[atlas]['parameters']:
                result[atlas][meas] = list()

        for col in self.ls_columns:
            for atlas in atlas_data['atlases']:
                for meas in atlas_data[atlas]['parameters']:
                    nimb_meas = atlas_data[atlas]['parameters'][meas]
                    if nimb_meas in col and atlas in col:
                        result[atlas][meas].append(self.ls_columns.index(col))
        return result


def get_rois_freesurfer(atlas_name = '',
                        atlas_group = '',
                        meas = "",
                        hemi_abbrev = '',
                        hemi_underscored = True,
                        hemi_last = True,
                        roi_nimb = True):
    """extracts the FS-nimb-ROI names of subcortical nuclei
        as per FreeSurfer-nimb nuclei atlases:
        an FS-nimb-ROI has the structure:
            <freesurfer_nuclei_roi>_<atlas_abbreviation><_hemisphere_abbreviation>
            where:
            atlas_abbreviation can be: atlas_data from "nuclei" group
                specifically: brainstem, hippocampus, amygdala, thalamus, hypothalamus
    Args:
        atlas_name: name of the atlas to extract ROIs. Can be only 1 name;
            choices: atlas_data[i]["atlas_name"]
        atlas_group: type of atlas to be used to extract ROI;
            choices: "" is for all atlases
                     "nuclei" (for atlas_data[i]["group"] == "nuclei")
                     "cortical"  (for atlas_data[i]["group"] == "cortical")
                     "subcortical"  (for atlas_data[i]["group"] == "subcortical")
        meas: extract for a specified measure. If None - will extract all measures
            choices: "ThickAvg", "SurfArea", "NumVert", etc (atlas_data[i][parameters])
        hemi_abbrev: "capital" will change lh to L, rh to R and lhrh to None
        hemi_underscored: if True will add an underscore before the hemi
        hemi_last: if True will put hemi in the last position, else: atlas is last
        roi_nimb: True will change the ROI names to the nimb abbreviation type
    Return:
        feats: {atlas_name: [FS-nimb-ROIs],}
    """
    # creating dict() with atlases and hemisphere
    # as per parameters requested
    if hemi_abbrev == "capital":
        hemi_ending = {"lh":"L", "rh": "R", "lhrh": ""}
    if roi_nimb:
        rois_nimb = header_atlas2nimb()

    atlases = [i for i in atlas_data if atlas_data[i]]
    if atlas_group:
        atlases = [i for i in atlas_data if atlas_data[i]["group"] == atlas_group]
    if atlas_name:
        atlases = [i for i in atlas_data if atlas_data[i]["atlas_name"] == atlas_name]

    atlases_params = {}
    for atlas in atlases:
        hemi_grp = atlas_data[atlas]['hemi']
        atlases_params[atlas] = {"hemis":hemi_grp,
                                "atlas_end": atlas}
        if hemi_abbrev == "capital":
            ls_hemis_cap = list()
            for _hemi in atlases_params[atlas]['hemis']:
                ls_hemis_cap.append(hemi_ending[_hemi])
            atlases_params[atlas]['hemis'] = ls_hemis_cap
        meas_2add = []
        if meas:
            meas_2add = [meas,]
        else:
            for fs_param in atlas_data[atlas]['parameters']:
                meas = atlas_data[atlas]['parameters'][fs_param]
                meas_2add.append(meas)
        atlases_params[atlas]['measurements'] = meas_2add


    # populating feats with correct feature names
    feats = dict()
    for atlas in list(atlases_params.keys()):
        feats[atlas] = list()
        rois = atlas_data[atlas]['header']

        if roi_nimb:
            rois_nimb_changed = list()
            for ROI in rois:
                rois_nimb_changed.append(rois_nimb[ROI])
            rois = rois_nimb_changed
        for _hemi in atlases_params[atlas]["hemis"]:
            rois_end_hemi = list()
            for meas in atlases_params[atlas]['measurements']:
                ending = atlas_roi_hemi_meas(atlases_params[atlas]["atlas_end"],
                                            _hemi,
                                            meas = meas,
                                            hemi_underscored = hemi_underscored,
                                            hemi_last = hemi_last)
                rois_end_hemi = [f"{roi}_{ending}" for roi in rois]
                feats[atlas] = feats[atlas] + rois_end_hemi
    return feats


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


def stats_f(fsver, atlas, _dir = "stats", hemi="".join(hemis)):
    mri_key = ""
    fs_key = "fs"
    if fsver < "7" and "fs6_stats_f" in atlas_data[atlas]:
        fs_key = "fs6"
    if _dir == "mri" and "fs_stats_f_inmridir" in atlas_data[atlas]:
        mri_key = "_inmridir"
    key = f"{fs_key}_stats_f{mri_key}"
    file = atlas_data[atlas][key]

    hemi_dot = ""
    if hemi in hemis:
        hemi_dot = f"{hemi}."
    if f"{hemis[0]}." in file and hemi_dot not in file:
        file = file.replace(f"{hemis[0]}.", hemi_dot)
    return os.path.join(_dir, file)


def all_stats_files(fsver):
    """extracts all statistical files for each atlas
    Args:
        None
    Return:
        {atlas: [stats/lh.stats, stats/rh.stats],}
    """
    def get_files(atlas, hemi):
        if fsver < "7" and "fs6_stats_f" in atlas_data[atlas]:
            files = files + [stats_f("6", atlas, hemi = hemi)]
        else:
            files = [stats_f("7", atlas, hemi = hemi)]
        return files

    stats_files = dict()
    for atlas in atlas_data:
        stats_files[atlas] = []
        if len(atlas_data[atlas]["hemi"]) > 1:
            for hemi in atlas_data[atlas]["hemi"]:
                files = get_files(atlas, hemi)
                stats_files[atlas] += files
        else:
            files = get_files(atlas, hemi = "".join(hemis))
            stats_files[atlas] = files
    return stats_files


def get_fs_rois_lateralized(atlas, roi = [], meas = None):
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
            return atlas_data[atlas]['parameters'].values()
        else:
            return [meas]

    def get_rois(atlas):
        if atlas != 'SubCtx':
            return atlas_data[atlas]['header'].values()
        else:
            return get_subcort_lat()

    def get_subcort_lat():
        subcort_twohemi_rois = list()
        for i in atlas_data['SubCtx']['header'].values():
            if i.endswith(f'_{hemis[0]}') or i.endswith(f'_{hemis[1]}'):
                roi = i.strip(f'_{hemis[0]}').strip(f'_{hemis[1]}')
                if roi not in subcort_twohemi_rois:
                    subcort_twohemi_rois.append(roi)
        return subcort_twohemi_rois


    def populate_lateralized(meas_user, ls_atlases):
        lateralized = {atlas:{} for atlas in ls_atlases}
        for atlas in lateralized:
            measures = get_measures(meas_user, atlas)
            headers  = get_rois(atlas)
            for meas in measures:
                lateralized[atlas] = {meas:{header: {} for header in headers}}
                for header in lateralized[atlas][meas]:
                    lateralized[atlas][meas][header] = (f'{header}_{meas}_{hemis[0]}_{atlas}',
                                                    f'{header}_{meas}_{hemis[1]}_{atlas}')
        return lateralized


    if atlas == 'SubCtx' or atlas in atlas_data['atlases'] and atlas_data[atlas]['two_hemi']:
        return populate_lateralized(meas, [atlas])
    else:
        ls_atlases = [atlas for atlas in atlas_data['atlases'] if atlas_data[atlas]['two_hemi']] + ['SubCtx']
        print(f'{atlas}\
            is ill-defined or not lateralized. Please use one of the following names:\
            {ls_atlases}. Returning all lateralized atlases')
        return populate_lateralized(meas, ls_atlases)


def get_lateralized_feats_for_freesurfer():
    '''create dict() with lateralized data for freesurfer atlases
    Return: {atlas: {measure: {roi: (left_roi, right_roi)}}}
    '''
    lateralized = dict()
    for atlas in atlases_hemi:
        lateralized[atlas] = dict()
        for meas in measures[atlas]:
            lateralized[atlas][meas] = dict()

    for roi_atlas in cols_X:
        for atlas in atlases_hemi:
            atlas_hemi = atlases_hemi[atlas]
            if atlas_hemi in roi_atlas:
                roi = roi_atlas.replace(f'_{atlas_hemi}','')
                contralat_atlas_hemi = atlas_hemi.replace("L", 'R')
                if atlas in subcort_atlases:
                    meas = measures[atlas][0]
                    lateralized[atlas][meas][roi] = (roi_atlas, roi_atlas.replace(atlas_hemi, contralat_atlas_hemi))
                elif atlas_hemi == 'L_VolSeg':
                    if roi_atlas.endswith(atlas_hemi):
                        meas = measures[atlas][0]
                        lateralized[atlas][meas][roi] = (roi_atlas, roi_atlas.replace(atlas_hemi, contralat_atlas_hemi))
                else:
                    for meas in measures[atlas]:
                        if f'{meas}{atlas_hemi}' in roi_atlas:
                            lateralized[atlas][meas][roi] = (roi_atlas, roi_atlas.replace(atlas_hemi, contralat_atlas_hemi))
    return lateralized


# moved to upper def: get_fs_rois_lateralized
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


def feats_2nimb(atlas_group,
                atlas_abbrev,
                atlas_nimb,
                all_feats,
                feats_2change,
                laterality_vals,
                change_2old_nimb = False):
    """transforms feats from nimb based on user defined parameters
    Args:
        atlas_abbrev: str() of atlas abbreviation to search
        atlas_nimb:   str() of atlas abbreviation from nimb, to be searched and changed
        all_feats:    list() of all feats to be checked for
        feats_2change: list() of feats to be changed
        laterality_vals: [str(laterality_param1), str(laterality_param2)]
        change_2old_nimb: if True, will change the feature to the version of old nimb ROIs
    """
    rois_2change = {
        "Cortex_": "cortex_",
        "cingulate_caudalanterior": "cingulate_anterior_caudal",
        "cingulate_rostralanterior": "cingulate_anterior_rostral",
        "cortex_MeanThickness": "cortex_thickness",
        "_medialorbito": "_orbitomedial",
        "_rostralmiddle": "_middle_rostral",
        "_caudalmiddle": "_middle_caudal",
        "_lateralorbito": "_orbitolateral",
        "_fusiformm": "_fusiform",
        "_bankssts": "_superior_sulcus_bank",
        "occipital_fusiform": "temporal_fusiform",
        "accumbensarea": "accumbensArea",
        "brainStem": "brainstem",
        "cingulate_Anterior": "ccAnterior",
        "cingulate_Central": "ccCentral",
        "cingulate_Mid_Anterior": "ccMidAnterior",
        "cingulate_Mid_Posterior": "ccMidPosterior",
        "cingulate_Posterior": "ccPosterior",
        "cerebellumcortex": "cerebellumCortex",
        "cerebellum_wm": "cerebellumWhiteMatter",
        "choroidplexus": "choroidPlexus",
        "cSF": "csf",
        "ventral_dincephalon": "ventralDC",
        "ventricle_InfLat": "ventricleInfLateral",
        "ventricle_Lateral": "ventricleLateral",
        "brainSegVol": "volBrainSeg",
        "brainSegVolNotVent": "volBrainSegNotVent",
        "brainSegVoltoeTIV": "volBrainSegtoeTIV",
        "cerebral_Vol_wm": "volCerebralWhiteMatter",
        "cortexVol": "volCortex",
        "maskVol": "volMask",
        "maskVoltoeTIV": "volMasktoeTIV",
        "subCortGrayVol": "volSubCortGray",
        "supraTentorialVol": "volSupraTentorial",
        "supraTentorialVolNotVent": "volSupraTentorialNotVent",
        "totalGrayVol": "volTotalGray",
        "ventricle_Choroidvol": "volVentricleChoroid",
        "wm_hypointensitiesR": "WMhypointensitiesR",
        "WMhypointensitiesL": "wm_hypointensitiesL",
        "wMhypointensities": "wm_hypointensities",
        "nonwm_hypointensities": "nonWMhypointensities",
    }
    rois_2rm = ['Unsegmented_wm',
                'cortex_thickness','cortex_NumVert',
               'cortex_WhiteSurfArea', 'cortex_CortexVol']

    for roi in feats_2change[::-1]:
        ix_atlas      = roi.rfind("_")
        ix_meas_hemi  = roi[:ix_atlas].rfind("_")
        feat_fs       = roi[:ix_meas_hemi]
        if feat_fs in rois_2rm:
            feats_2change.remove(roi)
        else:
            meas_hemi     = roi[ix_meas_hemi+1:ix_atlas]
            atlas         = roi[ix_atlas+1:]
            ix_roi2change = feats_2change.index(roi)
            hemi = ""
            if change_2old_nimb:
                if feat_fs in old_header_fs2nimb:
                    feat_fs = old_header_fs2nimb[feat_fs]
            for roi2change in rois_2change:
                if roi2change in feat_fs:
                    feat_fs = feat_fs.replace(roi2change, rois_2change[roi2change])

            if atlas_group == 'cortical':
                if laterality_vals[0] in meas_hemi or laterality_vals[1] in meas_hemi:
                    hemi = meas_hemi[-1]
                    meas = meas_hemi[:-1]
                roi_adapted = feat_fs + "_" +meas+ hemi

            elif atlas_group == "nuclei":
                if laterality_vals[0] in atlas[-1:] or laterality_vals[1] in atlas[-1:]:
                    hemi = atlas[-1:]
                    atlas = atlas[:-1]
                atlas_abbrev = atlas+hemi
                if "BS" in atlas:
                    atlas_abbrev = 'Brainstem'
                roi_adapted = feat_fs+ "_"

            elif atlas_group == 'subcortical':
                feat_fs = feat_fs.replace(feat_fs[0], feat_fs[0].lower())
                if "lh" in feat_fs or "rh" in feat_fs:
                    hemi = feat_fs[-2:]
                    feat_fs = feat_fs.replace(hemi, '')[:-1]
                    if "lh" in hemi:
                        hemi = laterality_vals[0]
                    else:
                        hemi = laterality_vals[1]
                roi_adapted = feat_fs + hemi
            feats_2change[ix_roi2change] = roi_adapted+ atlas_abbrev

    # removing ROIs that are not present in the database
    ls_remove = [i for i in feats_2change if i not in all_feats]
    for roi_atlashemi in feats_2change[::-1]:
        if roi_atlashemi in ls_remove:
            # print("REMOVING roi: ",roi_atlashemi)
            feats_2change.remove(roi_atlashemi)
    return feats_2change


old_header_fs2nimb = {'Medulla':'medulla','Pons':'pons','SCP':'scp','Midbrain':'midbrain',
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
