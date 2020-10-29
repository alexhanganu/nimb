# !/usr/bin/env python
# coding: utf-8
# last update: 2020-06-23

# script to do the logging and other small adjustments


from os import path, makedirs
from shutil import copyfile
from stats import db_processing


def get_dir(path_dir):
    if not path.exists(path_dir):
        makedirs(path_dir)
        print('creating folder: ',path_dir)
    return path_dir



def get_subjects_per_group(df, group_col):
    subjects_per_group = {}
    for group in groups:
        subjects_per_group[group] = []
        for _id in df.index.tolist():
            if df.at[_id, group_col] == group:
                subjects_per_group[group].append(_id)
    return subjects_per_group



def get_region(val):

    for end in ('_DK','_DS','_VolR','_VolL','_VolSeg','_ThickL','_ThickR','_AreaL','_AreaR','_ThickStdL','_ThickStdR',
        '_FoldIndL','_FoldIndR','_CurvIndL','_CurvIndR',):
        if end in val:
            val = val.replace(end,'')
    return val



brain_structures = {
    'frontal':('frontal_','front_','rectus_'),
    'cingulate':('cingulate_','cingul_',),
    'corpus_callosum':('cc_','ccMidPosterior','ccPosterior','ccCentral'),
    'parietal':('pariet_','parietal_','parieto_','interm_','intrapariet_'),
    'temporal':('temporal_','temp_',),
    'occipital':('occipital_','collat_'),
    'insula':('insula_','insular_'),
    'wm':('wm_','surfaceHoles','vessel','ventricle','opticChiasm','choroid','ventralDC','volCerebralWhiteMatter','csf'),
    'cortex':('cortex_','volTotalGray'),
    'basal_ganglia':('thalamus','caudate','putamen','pallidum','accumbens'),
    'hippocampus':('_HIP',),
    'brainstem':('_Brainstem',),
    'cerebellum':('cerebellum_',),
}

def get_brain_structure(region):

    structure = ''
    defined = False

    for struct in brain_structures:
        for val in brain_structures[struct]:
            if val in region[:region.find('_')+1] or val in region[region.rfind('_'):]:
                defined = True
                structure = struct
                short_region = val
                break
            elif 'lat_Fis_' in region:
                defined = True
                structure = 'temporal'
                short_region = ''
                break
            elif '_' not in region and val in region:
                defined = True
                structure = struct
                short_region = ''
                break
        if defined:
            break
    if not defined:
        print(region, 'no struct')
    # print(region, structure, short_region)

    return structure, short_region, defined


def extract_regions(dic, path_save_results, atlas):

    regions = dict()
    cols = ['explained_variance',]

    for feat in dic:
        defined = False
        region = get_region(feat)
        struct, short_region, defined = get_brain_structure(region)
        if defined:
            if struct not in regions:
                regions[struct] = list()
                regions[struct].append(dic[feat])
            else:
                regions[struct][0] = regions[struct][0] + dic[feat]
            sub_region= region.replace(short_region,'')
            if region not in regions[struct]:
                # print(region, '->',sub_region)
                regions[struct].append('{:.6}'.format(str(dic[feat]))+'_'+sub_region)
        else:
            print(region, 'not defined')


    n_vals = 0
    for key in regions:
        regions[key][0] = '{:.4}'.format(regions[key][0])
        regions[key] = [regions[key][0]]+sorted(regions[key][1:], reverse=True)
#        print(regions[key])

        if len(regions[key])> n_vals:
            n_vals = len(regions[key])

    for key in regions:
        to_add = n_vals - len(regions[key])
        for i in range(to_add):
            regions[key].append('0')
    for i in range(n_vals-1):
        cols.append('region'+str(i+1))

    import pandas as pd
    df_feat = pd.DataFrame.from_dict(regions, orient='index', columns=cols)
    df_feat.sort_values(by=['explained_variance'], inplace=True, ascending=False)

    db_processing.save_df_tocsv(df_feat, path.join(path_save_results,'regions_from_pca_features_'+atlas+'.csv'))

