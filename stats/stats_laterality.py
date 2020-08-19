'''laterality = ( L - R ) / ( L + R )
'''

import pandas as pd

def run_laterality(db_f, group_col, PATH_save_results):
	df = pd.read_excel(db_f)
	ls_columns = df.columns


	from stats_definitions import all_data, cols_per_measure_per_atlas
	cols2meas2atlas = cols_per_measure_per_atlas(df)
	cols_to_meas = cols2meas2atlas.cols_to_meas_to_atlas

	ls_atlases_laterality = list()
	for atlas in all_data['atlases']:
		if all_data[atlas]['two_hemi']:
			ls_atlases_laterality.append(atlas)


	ls_L = []
	ls_R = []
	for atlas in ls_atlases_laterality:
		df_lat = pd.DataFrame()
		df_lat[group_col] = df[group_col]
		d_mean = dict()

		if atlas == 'HIP':
			for index in cols_to_meas[atlas]['HIPL']:
				ls_L.append(ls_columns[index])
			for index in cols_to_meas[atlas]['HIPR']:
				ls_R.append(ls_columns[index])
			df_L = df[ls_L]
			df_R = df[ls_R]
			for col in df_L:
				df_lat[col.replace('_HIPL','')] = (df_L[col]-df_R[col.replace('HIPL','HIPR')])/(df_L[col]+df_R[col.replace('HIPL','HIPR')])
				d_mean[col.replace('_HIPL','')] = df_lat[col.replace('_HIPL','')].mean()
			df_lat.to_csv(PATH_save_results+atlas+'.csv')
		else:
			for measure in cols_to_meas[atlas]:
					for index in cols_to_meas[atlas][measure]:
						col_name = ls_columns[index]
						if 'L' in col_name[-4]:
							ls_L.append(col_name)
						if 'R' in col_name[-4]:
							ls_R.append(col_name)
						df_L = df[ls_L]
						df_R = df[ls_R]
					for col in df_L:
						df_lat[col.replace(measure+atlas,'')] = (df_L[col]-df_R[col.replace('L','R')])/(df_L[col]+df_R[col.replace('L','R')])
						d_mean[col.replace(measure+atlas,'')] = df_lat[col.replace(measure+atlas,'')].mean()
					df_lat.to_csv(PATH_save_results+atlas+'_'+measure+'.csv')



