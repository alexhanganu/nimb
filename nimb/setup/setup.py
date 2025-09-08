# -*- coding: utf-8 -*-
"""
This module handles the first-time interactive setup for the NIMB application.
It guides the user through creating configuration files, setting essential paths,
and configuring remote credentials.

To run the setup, execute this file directly: `python setup.py`
"""
import os
import sys
import getpass
import shutil
import json
from os import path

# Assume utilities are in the parent's sibling directory `distribution`
# This relative import works when nimb is treated as a package
try:
    from ..distribution.utilities import save_json, load_json
except ImportError:
    # Fallback for running the script directly from the setup folder
    sys.path.append(path.abspath(path.join(path.dirname(__file__), '..')))
    from distribution.utilities import save_json, load_json

class SetupManager:
    """
    Manages the interactive, one-time setup process for NIMB.
    """
    def __init__(self):
        self.home_dir = os.environ.get('HOME') or os.environ.get('USERPROFILE')
        self.credentials_home = path.join(self.home_dir, ".nimb")
        self.source_dir = path.dirname(__file__) # The directory this script is in

    def run_setup(self):
        """
        Executes the full interactive setup process.
        """
        print("--- Welcome to NIMB Setup ---")
        
        # 1. Create credentials directory
        self._create_credentials_dir()

        # 2. Copy template config files
        self._copy_template_files()

        # 3. Interactively configure local.json
        self._configure_local_json()

        print("\n--- NIMB Setup Complete! ---")
        print(f"Your configuration files are stored in: {self.credentials_home}")
        print("You can now run the main 'nimb.py' application.")

    def _create_credentials_dir(self):
        """Ensures the ~/.nimb configuration directory exists."""
        print(f"\nChecking for configuration directory at: {self.credentials_home}")
        if not path.exists(self.credentials_home):
            print("Configuration directory not found. Creating it.")
            os.makedirs(self.credentials_home)
        else:
            print("Configuration directory already exists.")

    def _copy_template_files(self):
        """
        Copies template JSON files from the setup folder to the ~/.nimb directory
        if they don't already exist.
        """
        print("\nChecking for essential configuration files...")
        template_files = ['local.json', 'projects.json', 'stats.json', 'remote1.json']
        for filename in template_files:
            source_path = path.join(self.source_dir, filename)
            dest_path = path.join(self.credentials_home, filename)

            if not path.exists(dest_path):
                if path.exists(source_path):
                    print(f"'{filename}' not found. Copying template...")
                    shutil.copy(source_path, dest_path)
                else:
                    print(f"WARNING: Template file '{filename}' not found in setup directory.")
            else:
                print(f"'{filename}' already exists.")

    def _configure_local_json(self):
        """
        Walks the user through setting the most important paths in local.json.
        """
        print("\n--- Configuring Essential Paths ---")
        print("Let's set up the main paths for your local machine.")
        print("You can always edit the JSON files manually later.")

        local_json_path = path.join(self.credentials_home, 'local.json')
        config = load_json(local_json_path)

        if not config:
            print(f"ERROR: Could not load {local_json_path}. Skipping interactive config.")
            return

        # Configure NIMB_HOME
        nimb_paths = config.get("NIMB_PATHS", {})
        nimb_paths["NIMB_HOME"] = self._ask_for_path(
            "NIMB Application Home",
            nimb_paths.get("NIMB_HOME", "~/nimb"),
            must_exist=True
        )
        nimb_paths["NIMB_tmp"] = self._ask_for_path(
            "NIMB Temporary Directory",
            nimb_paths.get("NIMB_tmp", "~/nimb_tmp"),
            create_if_not_exist=True
        )
        nimb_paths["conda_home"] = self._ask_for_path(
            "Miniconda/Anaconda Home",
            nimb_paths.get("conda_home", "~/miniconda3"),
            must_exist=True
        )
        config["NIMB_PATHS"] = nimb_paths

        # Configure FREESURFER_HOME
        fs_paths = config.get("FREESURFER", {})
        fs_paths["FREESURFER_HOME"] = self._ask_for_path(
            "FreeSurfer Home",
            fs_paths.get("FREESURFER_HOME", "~/freesurfer"),
            must_exist=True
        )
        fs_paths["SUBJECTS_DIR"] = self._ask_for_path(
            "FreeSurfer SUBJECTS_DIR",
            fs_paths.get("SUBJECTS_DIR", path.join(fs_paths["FREESURFER_HOME"], "subjects")),
            create_if_not_exist=True
        )
        config["FREESURFER"] = fs_paths
        
        # Save updated config
        save_json(config, local_json_path)
        print(f"\nUpdated configuration saved to {local_json_path}")

    def _ask_for_path(self, name, current_path, must_exist=False, create_if_not_exist=False):
        """
        Helper function to prompt the user for a directory path.
        """
        print(f"\n[{name}]")
        
        # Expand ~ to the user's home directory for display
        current_path_expanded = current_path.replace("~", self.home_dir)
        
        print(f"Current path is: {current_path_expanded}")
        if self._get_yes_no("Do you want to keep this path?"):
            return current_path
        
        while True:
            new_path_str = input(f"Please provide the full path for '{name}': ").strip()
            
            # Allow user to use ~
            new_path_expanded = new_path_str.replace("~", self.home_dir)
            
            if must_exist and not path.isdir(new_path_expanded):
                print(f"ERROR: Path does not exist or is not a directory: {new_path_expanded}")
                continue

            if create_if_not_exist and not path.exists(new_path_expanded):
                 if self._get_yes_no(f"Path does not exist. Create '{new_path_expanded}'?"):
                    try:
                        os.makedirs(new_path_expanded)
                        print("Directory created.")
                    except OSError as e:
                        print(f"ERROR: Could not create directory: {e}")
                        continue
                 else:
                    continue

            # Return the path with '~' if it was used, for cleaner JSON files
            return new_path_str

    def _get_yes_no(self, question):
        """Prompts the user with a yes/no question and returns a boolean."""
        while True:
            response = input(f"{question} (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            if response in ['n', 'no']:
                return False
            print("Invalid input. Please enter 'y' or 'n'.")


if __name__ == '__main__':
    setup = SetupManager()
    setup.run_setup()
