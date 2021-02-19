import os
import db_processing


class LateralityAnalysis():
	'''creates a pandas.DataFrame with laterality analysis using the formula:
		laterality = ( feature - contralateral_feature ) / ( feature + contralateral_feature )
	Args: df: pandas.DataFrame to be used for columns
			lhrh_feat_d: {'common_feature_name':('feature', 'contralateral_feature')}
			file_name: name of the file.csv
			PATH_save_results: abspath to save the file.csv
	Return: pandas.DataFrame csv file with results
	'''

    def __init__(self, df, lhrh_feat_d, file_name, PATH_save_results):

        self.df          = df
        self.lhrh_feat_d = lhrh_feat_d
        self.file_name   = file_name
        self.PATH_save   = PATH_save_results
        self.run()

    def run(self):

        df_lat = db_processing.Table().get_clean_df()
        for common_feature_name in self.lhrh_feat_d:
            feat = self.lhrh_feat_d[common_feature_name][0]
            contra_feat = self.lhrh_feat_d[common_feature_name][1]
            df_lat[common_feature_name] = (self.df[feat]-self.df[contra_feat]) / (self.df[feat] + self.df[contra_feat])
        df_lat.to_csv(os.path.join(self.PATH_save, f'{self.file_name}.csv'))

