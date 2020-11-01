'''
script will run correlations for the provided dataframe
per group
'''

from scipy import stats

    '''creating files with descriptions and correlations of each sheet (groups, df, group_col, GLM_dir)'''
class Correlations_Run():
    def __init__(self, df, cor_methods, cor_level_chosen, PATH2save_res):
        self.df = df
        self.cor_methods = cor_methods
        self.cor_level_chosen = cor_level_chosen
        self.lvl_thresh = {'STRONG': {'minim':0.7,'maxim':1},
                           'MODERATE': {'minim':0.5,'maxim':0.7},
                           'WEAK': {'minim':0.3, 'maxim':0.5}
        print('writing correlation sheet, group: ',group)
        self.make_correlations_per_group()
        print('FINISHED creating correlation file for group:', group)

    def make_correlations_per_group(self):
        frame = [{'Correlation':'0', 'Region1':'0', 'Region2':'0', 'Value':'0'}]
        results_df = pd.DataFrame(frame)

        for cor in self.cor_methods:
            writer = pd.ExcelWriter(PATH2save_res+'cor_'+group+'_'+cor+'.xlsx', engine='xlsxwriter')
            df_cor = self.df.corr(method=cor)
            df_cor.to_excel(writer, 'correlation')
            df_cor05 = self.df.corr(method=cor)>0.5
            df_cor05.to_excel(writer, 'correlation_r07')
            df_cor07 = self.df.corr(method=cor)>0.7
            df_cor07.to_excel(writer, 'correlation_r08')
            writer.save()
            nr_row_2_start = 0
            df_row = 0
            for cor_level in self.cor_level_chosen:
                cor_thresholds = self.lvl_thresh[cor_level]
                for nr_col in range(0, len(df_cor.columns)+1):
                    for nr_row in range(nr_row_2_start, len(df_cor.iloc[nr_col])):
                        if df_cor.iloc[nr_col, nr_row] > cor_thresholds['minim'] and df_cor.iloc[nr_col, nr_row]< cor_thresholds[>
                            cor_type = cor_level+' POSITIVE'
                        elif df_cor.iloc[nr_col, nr_row] < -cor_thresholds['minim'] and df_cor.iloc[nr_col, nr_row]> -cor_thresho>
                            cor_type = cor_level+' NEGATIVE '
                        else:
                            cor_type = 0
                        if cor_type != 0:
                            results_df.at[df_row, 'Correlation'] = cor_type
                            results_df.at[df_row, 'Region1'] = df_cor.columns[nr_col]
                            results_df.at[df_row, 'Region2'] = df_cor.index[nr_row]
                            results_df.at[df_row, 'Value'] = str(df_cor.iloc[nr_col, nr_row])
                            df_row += 1
                    nr_row_2_start += 1
                results_df = results_df.sort_values(by=['Region1'])#or 'Correlation'
                results_df.to_csv(PATH2save_res+'cor_res_'+group+'_'+cor+'_'+cor_level+'.csv', encoding='utf-8', index=F>

	def RUN_CORRELATIONS_with_stats_stats_pearsonr(self):
		groups = _GET_Groups(study)
		ls_cols, first_clin_col_index, last_clin_col_index, first_struct_col_index, last_struct_col_index = _GET_df_Parameters(st>
		df_main =_GET_df(study)
		group_col = _get_definitions(study, 'group_col')
		data_cor =df_main.copy()
		name_file_all = 'v1res_cor_all_'
		name_file_group = 'v1res_cor_'

		frame = [{'Clinical_Variable':'0', 'structure':'0',}]
		results_df = pd.DataFrame(frame)
		results_df_all = results_df

		f_per_group = {}
		for group in groups:
			f_per_group[group] = []
		f_per_group['all'] = []

		for col_x in ls_cols[first_clin_col_index+1:last_clin_col_index+1]:
			d_groups_2_analyze = {}
			for group in groups:
					x = np.array(df_main[df_main[group_col] == group][col_x])
					for val in x:
						if val != 0:
							d_groups_2_analyze[group] = True
							break
						else:
							d_groups_2_analyze[group] = False
			d_groups_2_analyze['all'] = True
			for group in d_groups_2_analyze:
				if d_groups_2_analyze[group] == False:
					d_groups_2_analyze['all'] = False
					break
			if d_groups_2_analyze['all'] == True:
				x = np.array(data_cor[col_x])
				df_row = 0
				for col_y in ls_cols[first_struct_col_index:last_struct_col_index+1]:
					y = np.array(data_cor[col_y])
					res_correlate = RUN_Correlate(x,y)
					if res_correlate['p'] <0.05:
						#measurement, structure = get_structure_measurement(col_y)
						#results_df_all = update_dataframe(results_df_all,res_correlate,col_x,measurement, structure)
						#results_df_all.at[df_row, 'Correlation'] = res_correlate['Correlation']
						results_df_all.at[df_row, 'Clinical_Variable'] = col_x
						results_df_all.at[df_row, 'structure'] = col_y
						results_df_all.at[df_row, 'r'] = str(res_correlate['r'])
						results_df_all.at[df_row, 'p'] = str(res_correlate['p'])
						df_row += 1
				results_df_all = results_df_all.sort_values(by=['Clinical_Variable'])
				results_df_all.to_csv(PATH2save_fig+name_file_all+col_x.replace('/','-')+'.csv', encoding='utf-8', index=False)
				f_per_group['all'].append(PATH2save_fig+name_file_all+col_x.replace('/','-')+'.csv')
			else:
				pass

			for group in groups:
				if d_groups_2_analyze[group] == True:
					results_df_group = results_df.copy(deep=True)
					x = np.array(data_cor[data_cor[group_col] == group][col_x])
					df_row = 0
					for col_y in ls_cols[first_struct_col_index:last_struct_col_index+1]:
						y = np.array(data_cor[data_cor[group_col] == group][col_y])
						res_correlate = RUN_Correlate(x,y)
						if res_correlate['p'] <0.05:
							#measurement, structure = get_structure_measurement(col_y)
							#results_df_group = update_dataframe(results_df_group,res_correlate,col_x,measurement, structure)
							#results_df_group.at[df_row, 'Correlation'] = res_correlate['Correlation']
							results_df_group.at[df_row, 'Clinical_Variable'] = col_x
							results_df_group.at[df_row, 'structure'] = col_y
							results_df_group.at[df_row, 'r'] = str(res_correlate['r'])
							results_df_group.at[df_row, 'p'] = str(res_correlate['p'])
							df_row += 1
					if len(results_df_group.iloc[0]['Clinical_Variable']) > 1:
						results_df_group = results_df_group.sort_values(by=['Clinical_Variable'])
						results_df_group = results_df_group.sort_values(by=['structure'])
						results_df_group.to_csv(PATH2save_fig+name_file_group+group+'_'+col_x.replace('/','-')+'.csv', encoding='>
						f_per_group[group].append(PATH2save_fig+name_file_group+group+'_'+col_x.replace('/','-')+'.csv')

		for group in f_per_group:
			if len(f_per_group[group])>0:
				writer = pd.ExcelWriter(PATH2save_fig+'res_'+group+'.xlsx', engine='xlsxwriter')
				df_concat = pd.read_csv(f_per_group[group][0])
				for file in f_per_group[group][1:]:
					df2 = pd.read_csv(file)
					frames = (df_concat, df2)
					df_concat = pd.concat(frames, axis=0)
				df_concat = df_concat.sort_values(by=['Clinical_Variable','structure'])
				#for file in f_per_group[group]:
				#    remove(file)

			df_concat.to_excel(writer, 'correlations')
			writer.save()
		print('DONE')


    def check_correl_sig(self, x, y):
        res = {}
        cor = stats.stats.pearsonr(x,y)
        if cor[1] <0.05:
            if cor[0] > 0:
                cor_type = 'pos'
            else:
                cor_type = 'neg'
            res['correlation'] = cor_type
        res['r'] = cor[0]
        res['p'] = cor[1]
        return res

    def update_dataframe(self, df, res_correlate, col_x, measurement, structure):
        ls = df['structure'].tolist()
        if structure in ls:
            df_row = ls.index(structure)
            #df.at[df_row, measurement] = measurement
            #df.at[df_row, 'cor_'+measurement] = res_correlate['correlation']
            #df.at[df_row, 'r_'+measurement] = str(res_correlate['r'])
            df.at[df_row, measurement+'_p'] = str(res_correlate['p'])
        else:
            if len(df.iloc[0]['Clinical_Variable']) == 1:
                df_row = 0
            else:
                df_row = len(ls)+1
            df.at[df_row, 'Clinical_Variable'] = col_x
            df.at[df_row, 'structure'] = structure
            #df.at[df_row, measurement] = measurement
            #df.at[df_row, 'cor_'+measurement] = res_correlate['correlation']
            #df.at[df_row, 'r_'+measurement] = str(res_correlate['r'])
            df.at[df_row, measurement+'_p'] = str(res_correlate['p'])
        return df

