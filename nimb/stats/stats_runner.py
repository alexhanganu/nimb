# -*- coding: utf-8 -*-
"""
This module contains the StatsRunner, an independent, schedulable script for
performing all statistical analyses for a NIMB project.
"""

import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, PowerTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score

# Add project root to path to allow imports
try:
    from pathlib import Path
    top = Path(__file__).resolve().parents[1]
    sys.path.append(str(top))
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from setup.config_manager import ConfigManager
from distribution.utilities import save_json

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class PandasManager:
    """A lightweight helper for pandas operations."""
    def get_df(self, f_path, index_col=None):
        """Reads a CSV or Excel file into a DataFrame."""
        if not os.path.exists(f_path):
            log.error(f"File not found: {f_path}")
            return pd.DataFrame()
        if f_path.endswith('.csv'):
            return pd.read_csv(f_path, index_col=index_col)
        elif f_path.endswith(('.xlsx', '.xls')):
            return pd.read_excel(f_path, engine='openpyxl', index_col=index_col)
        return pd.DataFrame()

    def save_df(self, df, f_path, sheet_name='Sheet1'):
        """Saves a DataFrame to a CSV or Excel file."""
        dir_name = os.path.dirname(f_path)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        if f_path.endswith('.csv'):
            df.to_csv(f_path)
        else:
            df.to_excel(f_path, sheet_name=sheet_name, engine='openpyxl')
        log.info(f"Saved DataFrame to {f_path}")

class GridBuilder:
    """Builds the final data grid for statistical analysis."""
    def __init__(self, project_vars, stats_vars):
        self.project_vars = project_vars
        self.stats_vars = stats_vars
        self.stats_home = project_vars["STATS_PATHS"]["STATS_HOME"]
        self.id_col = project_vars.get('id_col', 'subject_id')
        self.group_col = project_vars.get('group_col', 'group')
        self.pm = PandasManager()

    def build(self):
        """Main method to construct and preprocess the grid."""
        log.info("Building statistical analysis grid...")
        
        # 1. Load clinical/group data
        groups_file = os.path.join(self.stats_home, self.project_vars["fname_groups"])
        df_clinical = self.pm.get_df(groups_file, index_col=self.id_col)
        if df_clinical.empty:
            log.error("Clinical/group data file is empty or not found. Cannot proceed.")
            return None, None, None, None

        # 2. Load and merge imaging data files
        imaging_files = self._get_imaging_stats_files()
        df_imaging = self._merge_files(imaging_files, self.id_col)
        
        # 3. Join clinical and imaging data
        df_final = df_clinical.join(df_imaging, how='inner')
        log.info(f"Final grid created with {df_final.shape[0]} subjects and {df_final.shape[1]} variables.")

        # 4. Preprocess: Handle outliers and missing data
        df_final = self._preprocess_grid(df_final)

        # Save the final grid
        final_grid_path = os.path.join(self.stats_home, "final_analysis_grid.csv")
        self.pm.save_df(df_final, final_grid_path)

        groups = df_final[self.group_col].unique().tolist()
        imaging_cols = [col for col in df_imaging.columns if col in df_final.columns]
        
        return df_clinical, df_final, df_final[imaging_cols], imaging_cols, groups

    def _get_imaging_stats_files(self):
        """Identifies paths to all imaging stats files to be merged."""
        files_to_load = []
        stats_files_config = self.stats_vars.get("STATS_FILES", {})
        file_keys = ["fname_fs_all_stats", "fname_func_all_stats", "fname_diff_all_stats"]
        for key in file_keys:
            fname = self.project_vars.get(key)
            if not fname or fname == 'default':
                fname = stats_files_config.get(key)
            
            if fname:
                file_path = os.path.join(self.stats_home, f"{fname}.{stats_files_config.get('file_type', 'csv')}")
                if os.path.exists(file_path):
                    files_to_load.append(file_path)
        return files_to_load

    def _merge_files(self, file_paths, index_col):
        """Merges multiple DataFrames on their index."""
        if not file_paths:
            return pd.DataFrame()
        
        df_list = [self.pm.get_df(f, index_col=index_col) for f in file_paths]
        
        # Start with the first DataFrame and join the rest
        merged_df = df_list[0]
        for df in df_list[1:]:
            merged_df = merged_df.join(df, how='outer')
        return merged_df

    def _preprocess_grid(self, df):
        """Handles outlier detection and missing value imputation."""
        log.info("Preprocessing grid: checking for outliers and NaNs.")
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        
        # Simple outlier detection (values > 3 std dev from mean)
        for col in numeric_cols:
            mean, std = df[col].mean(), df[col].std()
            cut_off = std * 3
            lower, upper = mean - cut_off, mean + cut_off
            outliers = df[(df[col] < lower) | (df[col] > upper)]
            if not outliers.empty:
                log.warning(f"Outliers detected in column '{col}'. Replacing with NaN.")
                df.loc[outliers.index, col] = np.nan
        
        # Impute NaNs with the mean of the column
        for col in numeric_cols:
            if df[col].isnull().any():
                mean_val = df[col].mean()
                df[col].fillna(mean_val, inplace=True)
                log.info(f"Imputed {df[col].isnull().sum()} NaN values in '{col}' with mean ({mean_val:.2f}).")
                
        return df

class AnalysisHelper:
    """Contains methods for running statistical analyses."""
    def __init__(self, final_grid, group_col, groups, imaging_cols, stats_home):
        self.df = final_grid
        self.group_col = group_col
        self.groups = groups
        self.imaging_cols = imaging_cols
        self.stats_home = stats_home
        self.pm = PandasManager()

    def run_ttests(self):
        """Performs t-tests between groups for all imaging variables."""
        log.info("Running two-sample t-tests...")
        from scipy.stats import ttest_ind
        
        results = []
        group1_df = self.df[self.df[self.group_col] == self.groups[0]]
        group2_df = self.df[self.df[self.group_col] == self.groups[1]]

        for col in self.imaging_cols:
            stat, p_val = ttest_ind(group1_df[col], group2_df[col], nan_policy='omit')
            results.append({'variable': col, 't_stat': stat, 'p_value': p_val})
        
        results_df = pd.DataFrame(results).sort_values('p_value')
        save_path = os.path.join(self.stats_home, "t_test_results.csv")
        self.pm.save_df(results_df, save_path)
        return results_df

    def run_prediction(self, features_to_use):
        """Runs a Random Forest prediction model."""
        log.info("Running prediction analysis with Random Forest...")
        X = self.df[features_to_use].values
        
        le = LabelEncoder()
        y = le.fit_transform(self.df[self.group_col])
        
        # Scale features
        scaler = PowerTransformer()
        X_scaled = scaler.fit_transform(X)

        # Cross-validation and model fitting
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        accuracies = []
        for train_idx, test_idx in cv.split(X_scaled, y):
            X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            accuracies.append(accuracy_score(y_test, preds))

        avg_accuracy = np.mean(accuracies)
        log.info(f"Prediction complete. Average accuracy: {avg_accuracy:.3f}")
        return avg_accuracy

class StatsRunner:
    """
    Main class for the stats runner. Loads config, prepares data,
    and executes the requested statistical analyses.
    """
    def __init__(self, all_vars):
        self.all_vars = all_vars
        self.project_vars = all_vars.projects[all_vars.params.project]
        self.stats_vars = all_vars.stats_vars
        self.stats_home = self.project_vars["STATS_PATHS"]["STATS_HOME"]
        self.step_to_run = all_vars.params.step

    def run(self):
        """Main entry point to run the statistical pipeline."""
        log.info(f"Starting statistical analysis for project: {self.all_vars.params.project}")
        log.info(f"Analysis step to run: {self.step_to_run}")

        builder = GridBuilder(self.project_vars, self.stats_vars)
        df_clinical, df_final, df_imaging, imaging_cols, groups = builder.build()

        if df_final is None:
            log.error("Grid building failed. Aborting analysis.")
            return

        analyzer = AnalysisHelper(df_final, self.project_vars['group_col'], groups, imaging_cols, self.stats_home)
        
        # Dispatch to the correct analysis step
        if self.step_to_run == 'all' or self.step_to_run == 'ttest':
            analyzer.run_ttests()
        
        if self.step_to_run == 'all' or self.step_to_run == 'predskf':
            # For simplicity, we'll use all imaging columns for prediction
            # A feature selection step (like RFE or PCA) could be added here
            analyzer.run_prediction(features_to_use=imaging_cols)
        
        # Add other steps (anova, linregmod, etc.) here as needed...

        log.info("Statistical analysis run is complete.")

def get_parameters():
    """Parses command-line arguments for the stats runner."""
    # This function is duplicated from the original stats_helper.py
    # for standalone execution capability.
    parser = argparse.ArgumentParser(description="NIMB Statistics Runner")
    parser.add_argument("-project", required=True, help="Name of the project to analyze.")
    parser.add_argument("-step", required=False, default='all',
                        choices=['all', 'ttest', 'predskf'], # Add more choices as implemented
                        help="Specific statistical analysis step to run.")
    return parser.parse_args()

if __name__ == "__main__":
    # This allows the script to be run independently
    params = get_parameters()
    
    # We need to manually create the `all_vars` object that nimb.py would normally provide
    class MockAllVars:
        def __init__(self, project, step):
            # A full implementation would load from JSON files
            # For this runner, we primarily need the params
            self.params = argparse.Namespace(project=project, step=step)
            # A real ConfigManager would populate these
            self.projects = {} 
            self.stats_vars = {}
            # This is a simplification; a full ConfigManager would be better
            # For now, let's assume `ConfigManager` can work with just params
            # for the purpose of this script.
            try:
                cm = ConfigManager(init_params=False)
                cm.params = self.params
                self.projects = cm.projects
                self.stats_vars = cm.stats_vars
            except Exception as e:
                log.error(f"Could not fully initialize ConfigManager for standalone run: {e}")
                log.error("Please ensure your setup/config files are correct.")
                sys.exit(1)


    all_vars = MockAllVars(params.project, params.step)
    
    # We have to patch ConfigManager to accept pre-parsed args for standalone mode
    original_get_parameters = ConfigManager._get_parameters
    ConfigManager._get_parameters = lambda self: params
    
    try:
        all_vars = ConfigManager()
        runner = StatsRunner(all_vars)
        runner.run()
    finally:
        # Restore original method
        ConfigManager._get_parameters = original_get_parameters

