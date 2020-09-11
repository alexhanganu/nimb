'''laterality = ( L - R ) / ( L + R )
'''

import pandas as pd
from stats.stats_definitions import (get_structure_measurement,
                                     get_names_of_measurements,
                                     get_names_of_structures)
ls_meas = get_names_of_measurements()
ls_struct = get_names_of_structures()

class RReplace():

	def __init__(self, features):
		self.contralateral_features = self.add_contralateral_features(features)

	def add_contralateral_features(self, features):
		for feat in features:
			meas, struct = get_structure_measurement(feat, ls_meas, ls_struct)
			if meas != 'VolSeg':
				new_struct = struct+'_'+ self.get_contralateral_meas(meas)
			else:
				new_struct = self.get_contralateral_meas(struct)+'_'+meas
			if new_struct not in features:
				features.append(new_struct)
		return features

	def get_contralateral_meas(self, param):
		if "L" in param:
			return self.rreplace(param, "L", "R", 1)
		elif "R" in param:
			return self.rreplace(param, "R", "L", 1)
		else:
			print('no laterality in : {}'.format(param))
			return param

	def rreplace(self, s, old, new, occurence):
		li = s.rsplit(old, 1)
		return new.join(li)



class LateralityAnalysis():

    def __init__(self, df, groups_col, PATH_save_results):

        self.ls_columns = df.columns.tolist()
        self.group_col = groups_col
        self.PATH_save_results = PATH_save_results
        self.df = df
        self.feat_L = ''
        self.feat_R = ''
#        self.get_atlases_lat()

#    def get_atlases_lat(self):
#        from stats.stats_definitions import all_data, cols_per_measure_per_atlas
#        self.cols_to_meas = cols_per_measure_per_atlas(self.ls_columns).cols_to_meas_to_atlas
#        self.ls_atlases_laterality = list()
#        for atlas in all_data['atlases']:
#            if all_data[atlas]['two_hemi']:
#                self.ls_atlases_laterality.append(atlas)
#        self.ls_atlases_laterality

    def get_LR_features(self, feat):
        meas, struct = get_structure_measurement(feat, ls_meas, ls_struct)
        if meas != 'VolSeg':
            self.attrib_LR_feat(feat, meas)
        else:
            self.attrib_LR_feat(feat, struct)

    def attrib_LR_feat(self, feat, param):
        if 'L' in param:
           self.feat_L = feat
        elif 'R' in param:
           self.feat_R = feat
        else:
           self.feat_L = 'none'
           self.feat_R = 'none'

    def run(self):
        for feat in self.ls_columns:
            self.get_LR_features(feat)



    def run2(self):
        ls_L = []
        ls_R = []
        for atlas in self.ls_atlases_laterality:
            df_lat = pd.DataFrame()
            df_lat[self.group_col] = self.df[self.group_col]
            d_mean = dict()
            if atlas == 'HIP':
                for index in self.cols_to_meas[atlas]['HIPL']:
                    ls_L.append(self.ls_columns[index])
                for index in self.cols_to_meas[atlas]['HIPR']:
                    ls_R.append(self.ls_columns[index])
                df_L = self.df[ls_L]
                df_R = self.df[ls_R]
                for col in df_L:
                    df_lat[col.replace('_HIPL','')] = (df_L[col]-df_R[col.replace('HIPL','HIPR')])/(df_L[col]+df_R[col.replace('HIPL','HIPR')])
                    d_mean[col.replace('_HIPL','')] = df_lat[col.replace('_HIPL','')].mean()
                df_lat.to_csv(self.PATH_save_results+atlas+'.csv')
            else:
                for measure in self.cols_to_meas[atlas]:
                    for index in self.cols_to_meas[atlas][measure]:
                        col_name = self.ls_columns[index]
                        if 'L' in col_name[-4]:
                            ls_L.append(col_name)
                        if 'R' in col_name[-4]:
                            ls_R.append(col_name)
                        df_L = self.df[ls_L]
                        df_R = self.df[ls_R]
                    for col in df_L:
                        df_lat[col.replace(measure+atlas,'')] = (df_L[col]-df_R[col.replace('L','R')])/(df_L[col]+df_R[col.replace('L','R')])
                        d_mean[col.replace(measure+atlas,'')] = df_lat[col.replace(measure+atlas,'')].mean()
                    df_lat.to_csv(self.PATH_save_results+atlas+'_'+measure+'.csv')



