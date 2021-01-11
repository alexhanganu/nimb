'''laterality = ( L - R ) / ( L + R )
'''

import pandas as pd
from os import path
from processing.freesurfer.fs_definitions import (get_structure_measurement,
                                     			get_names_of_measurements,
                                     			get_names_of_structures)
ls_meas = get_names_of_measurements()
ls_struct = get_names_of_structures()

class RReplace():

	def __init__(self, features):
		self.add_contralateral_features(features)
		self.contralateral_features = self.lhrh_features

	def add_contralateral_features(self, features):
		self.lhrh_features = {}
		for feat in features:
			meas, struct = get_structure_measurement(feat, ls_meas, ls_struct)
			if meas != 'VolSeg':
				new_struct, hemi = self.get_contralateral_meas(meas)
				contra_feat = struct+'_'+new_struct
			else:
				new_struct, hemi = self.get_contralateral_meas(struct)
				contra_feat = new_struct+'_'+meas
			if 'none' not in new_struct:
				if hemi == 'L':
					self.lhrh_features[contra_feat] = feat
				else:
					self.lhrh_features[feat] = contra_feat
		self.lhrh_features

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



class LateralityAnalysis():

    def __init__(self, df, lhrh_feat_d, group, PATH_save_results):

        self.df          = df
        self.lhrh_feat_d = lhrh_feat_d
        self.group       = group
        self.PATH_save   = PATH_save_results

    def run(self):
        df_lat = pd.DataFrame()
        for feat in self.lhrh_feat_d:
            meas, struct = get_structure_measurement(feat, ls_meas, ls_struct)
            contra_feat = self.lhrh_feat_d[feat]
            df_lat[feat.replace('_'+meas,'')] = (self.df[feat]-self.df[contra_feat]) / (self.df[feat] + self.df[contra_feat])
        df_lat.to_csv(path.join(self.PATH_save, self.group+'.csv'))


