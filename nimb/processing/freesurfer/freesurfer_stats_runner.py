# -*- coding: utf-8 -*-
"""
This module contains the FS_StatsRunner, a consolidated and independent script
for extracting statistical data from processed FreeSurfer subject directories.

It scans a directory of subjects, reads the various .stats files for each one,
and aggregates the data into comprehensive Excel spreadsheets. It is designed
to be submitted as a job to a scheduler.
"""

import os
import sys
import argparse
import logging
import json
import pandas as pd
from pathlib import Path

# Adjust path to import other NIMB modules
try:
    top = Path(__file__).resolve().parents[2]
    sys.path.append(str(top))
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from setup.config_manager import ConfigManager
from ..atlases import atlas_definitions
from .fs_utils import FS_Utils

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


class StatsReader:
    """
    Handles the parsing of various FreeSurfer .stats text files.
    """
    def __init__(self, atlas_data, fs_version):
        self.atlas_data = atlas_data
        self.fs_version = fs_version
        self.nuclei_atlases = [i for i in self.atlas_data if "nuclei" in self.atlas_data[i]["group"]]

    def get_values(self, atlas_name, file_path, subject_id):
        """
        Reads a .stats file and returns a pandas DataFrame and extra measures.
        """
        if not os.path.isfile(file_path):
            log.warning(f"Stats file missing for {subject_id}: {file_path}")
            return pd.DataFrame(), {}

        with open(file_path, 'r') as f:
            content = f.readlines()
        
        if not content:
            log.warning(f"Stats file is empty for {subject_id}: {file_path}")
            return pd.DataFrame(), {}
            
        extra_measures = self._get_extra_measures(atlas_name, content)

        if atlas_name in self.nuclei_atlases:
            df = self._parse_nuclei_stats(content, subject_id)
        else:
            df = self._parse_standard_stats(content, subject_id)

        return df, extra_measures

    def _parse_standard_stats(self, content, subject_id):
        """Parses standard aparc/aseg.stats files."""
        header_line_index = -1
        for i, line in enumerate(content):
            if line.startswith('# ColHeaders'):
                header_line_index = i
                break
        
        if header_line_index == -1:
            return pd.DataFrame()

        headers = content[header_line_index].split()[2:]
        data_lines = [line.split() for line in content[header_line_index+1:]]
        
        df = pd.DataFrame(data_lines, columns=headers)
        return df

    def _parse_nuclei_stats(self, content, subject_id):
        """Parses stats files from brainstem, hippocampus, etc."""
        values = {}
        for line in content[1:]: # Skip header
            parts = line.strip().split()
            if len(parts) >= 2:
                # Format: 'StructureName 123.45'
                structure_name = parts[0]
                try:
                    stat_value = float(parts[1])
                    values[structure_name] = stat_value
                except ValueError:
                    continue
        
        df = pd.DataFrame(values, index=[subject_id])
        return df

    def _get_extra_measures(self, atlas, content):
        """Extracts 'Measure' lines (e.g., eTIV, BrainSegVol) from stats files."""
        measures = {}
        for line in content:
            if line.strip().startswith('# Measure'):
                parts = line.split(',')
                try:
                    key = parts[1].strip()
                    value = float(parts[2].strip())
                    measures[key] = value
                except (IndexError, ValueError):
                    continue
        return measures


class ExcelWriter:
    """
    Manages the creation and writing of stats data to Excel files.
    """
    def __init__(self, output_filepath):
        self.writer = pd.ExcelWriter(output_filepath, engine='xlsxwriter')
        self.sheets = {}

    def add_subject_data(self, sheet_name, subject_id, data_series):
        """Adds a subject's data (a pandas Series) to a sheet."""
        if sheet_name not in self.sheets:
            self.sheets[sheet_name] = pd.DataFrame()
        
        self.sheets[sheet_name] = pd.concat([self.sheets[sheet_name], data_series.to_frame(subject_id).T])

    def save_and_close(self):
        """Writes all accumulated data to the Excel file and saves it."""
        for sheet_name, df in self.sheets.items():
            df.to_excel(self.writer, sheet_name=sheet_name, index=True)
        self.writer.close()

    def create_single_sheet_file(self, output_filepath, id_col_name):
        """Combines all sheets into a single DataFrame and saves it."""
        if not self.sheets:
            log.warning("No data to write to single-sheet file.")
            return

        all_dfs = []
        for sheet_name, df in self.sheets.items():
            # Add a prefix to column names to avoid duplicates
            df_renamed = df.rename(columns=lambda x: f"{sheet_name}_{x}")
            all_dfs.append(df_renamed)
        
        combined_df = pd.concat(all_dfs, axis=1)
        combined_df.index.name = id_col_name
        combined_df.to_excel(output_filepath)
        log.info(f"Successfully created single-sheet stats file: {output_filepath}")


class FS_StatsRunner:
    """
    Main class to orchestrate the extraction of FreeSurfer stats.
    """
    def __init__(self, all_vars):
        self.params = all_vars.params
        self.project_vars = all_vars.projects[self.params.project]
        self.fs_vars = all_vars.location_vars['local']['FREESURFER']

        # --- Paths ---
        self.stats_dir = self.params.stats_dir
        self.subjects_dir = self.params.dir_fs_stats
        
        # --- Config ---
        self.fs_utils = FS_Utils(self.fs_vars['FREESURFER_HOME'], self.fs_vars.get('version'))
        self.atlas_data = atlas_definitions.atlas_data
        self.stats_reader = StatsReader(self.atlas_data, self.fs_utils.fs_version)
        
        # --- File Naming ---
        self.output_per_param_file = os.path.join(self.stats_dir, "fs_stats_per_parameter.xlsx")
        self.output_all_stats_file = os.path.join(self.stats_dir, "fs_stats_all.xlsx")

    def run(self):
        """
        Executes the full stats extraction pipeline.
        """
        log.info(f"Starting FreeSurfer stats extraction from: {self.subjects_dir}")
        os.makedirs(self.stats_dir, exist_ok=True)

        subjects_to_process = os.listdir(self.subjects_dir)
        excel_writer = ExcelWriter(self.output_per_param_file)
        
        for subject_id in subjects_to_process:
            subject_path = os.path.join(self.subjects_dir, subject_id)
            if not os.path.isdir(subject_path):
                continue
            
            log.info(f"Processing subject: {subject_id}")
            self._process_single_subject(subject_id, subject_path, excel_writer)

        log.info(f"Saving multi-sheet Excel file to: {self.output_per_param_file}")
        excel_writer.save_and_close()

        log.info("Creating consolidated single-sheet Excel file...")
        excel_writer.create_single_sheet_file(self.output_all_stats_file, self.project_vars.get("id_col", "subject_id"))
        
        log.info("Stats extraction complete.")

    def _process_single_subject(self, subject_id, subject_path, writer):
        """Extracts all stats for one subject and adds them to the writer."""
        for atlas_name, atlas_info in self.atlas_data.items():
            for hemi in atlas_info.get('hemi', ['']):
                stats_filename = self.fs_utils.get_stats_filename(atlas_name, hemi)
                stats_filepath = os.path.join(subject_path, 'stats', stats_filename)
                
                df, extra_measures = self.stats_reader.get_values(atlas_name, stats_filepath, subject_id)

                if df.empty:
                    continue

                # Handle different dataframe structures
                if "StructName" in df.columns: # Standard aparc/aseg style
                    df.set_index("StructName", inplace=True)
                    for param in df.columns:
                        sheet_name = f"{atlas_name}_{param}_{hemi}" if hemi else f"{atlas_name}_{param}"
                        writer.add_subject_data(sheet_name, subject_id, df[param].astype(float))
                else: # Nuclei style (already one row per subject)
                     for param, value in df.iloc[0].items():
                        sheet_name = f"{atlas_name}_{param}_{hemi}" if hemi else f"{atlas_name}_{param}"
                        writer.add_subject_data(sheet_name, subject_id, pd.Series([value], index=[param]))
                
                # Add extra measures
                for measure_name, value in extra_measures.items():
                     sheet_name = f"ExtraMeasures"
                     writer.add_subject_data(sheet_name, subject_id, pd.Series([value], index=[measure_name]))


def main():
    """Main entry point for the independent stats runner script."""
    parser = argparse.ArgumentParser(description="NIMB FreeSurfer Stats Extraction Runner")
    # ConfigManager will use these, but we define them here for clarity
    parser.add_argument("-project", required=True, help="Name of the project.")
    parser.add_argument("-stats_dir", required=True, help="Directory to save the output stats files.")
    parser.add_argument("-dir_fs_stats", required=True, help="Directory containing the processed FreeSurfer subjects.")
    
    try:
        all_vars = ConfigManager()
        runner = FS_StatsRunner(all_vars)
        runner.run()
    except Exception as e:
        log.error("A fatal error occurred in the stats runner.", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
