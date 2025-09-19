# -*- coding: utf-8 -*-
"""
This module handles the first-time interactive setup for the NIMB application.
It creates all necessary configuration files (local, projects, remote, stats),
initializes the database, and sets essential paths through a guided process.

To run, execute this file directly: python nimb/setup/setup.py
"""
import os
import sys
import shutil
import json
import sqlite3
import getpass
import pwd
from os import path

# --- Default JSON Templates (for creating new files) ---

DEFAULT_PROJECTS_JSON = {
    "project1": {
        "SOURCE_BIDS_DIR": ["local", "/home/user/datasets/project1/bids"],
        "SOURCE_SUBJECTS_DIR": ["local", "/home/user/datasets/project1/source"],
        "PROCESSED_FS_DIR": ["remote1", "/home/user/datasets/project1/derivatives/freesurfer"],
        "materials_DIR": ["local", "/home/user/projects/project1/materials"]
    },
    "LOCATION": ["local", "remote1"]
}

DEFAULT_REMOTE_JSON = {
    "USER": {"user": "user1"},
    "NIMB_PATHS": {
        "NIMB_HOME": "~/nimb",
        "NIMB_tmp": "~/scratch/nimb_tmp"
    },
    "PROCESSING": {"processing_env": "slurm"},
    "FREESURFER": {"FREESURFER_HOME": "/project/freesurfer"}
}

DEFAULT_STATS_JSON = {
    "STATS_PATHS": {
        "STATS_HOME": "default",
        "FS_GLM_dir": "default",
        "features": "default"
    },
    "STATS_PARAMS": {},
    "STATS_FILES": {}
}

# --- Helper Utilities ---

def _get_credentials_home():
    """Determines and creates the application's config directory (~/.nimb)."""
    home_dir = os.environ.get('HOME') or os.environ.get('USERPROFILE')
    credentials_home = path.join(home_dir, ".nimb")
    if not path.exists(credentials_home):
        print(f"Configuration directory not found. Creating it at: {credentials_home}")
        os.makedirs(credentials_home)
    return credentials_home

def _get_current_username():
    """Finds the current user's username."""
    try:
        return pwd.getpwuid(os.getuid())[0]
    except (ImportError, KeyError):
        return getpass.getuser()

def save_json(data, filepath):
    """Saves a dictionary to a JSON file with nice formatting."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

# --- Main Setup Class ---

class SetupManager:
    """ Manages the interactive, one-time setup process for NIMB. """
    def __init__(self):
        self.credentials_home = _get_credentials_home()
        self.home_dir = os.environ.get('HOME') or os.environ.get('USERPROFILE')

    def run_setup(self):
        """ Executes the full interactive setup process. """
        print("--- Welcome to the NIMB Interactive Setup ---")
        print("This script will help you configure all necessary files.")

        # 1. Create/verify essential config files from templates
        self._create_files_if_not_exist()

        # 2. Interactively configure all JSON files
        self._configure_local_json()
        self._configure_projects_json()
        self._configure_remote_json()
        self._configure_stats_json()

        print("\n✅ --- NIMB Setup Complete! ---")
        print(f"Your configuration files are stored in: {self.credentials_home}")
        print("To configure your shell, remember to run: source nimb/setup/setup_env.sh")

    def _create_files_if_not_exist(self):
        """Ensures all config files exist, creating them from defaults if needed."""
        print("\nChecking for essential configuration files...")
        files_to_check = {
            "local.json": DEFAULT_REMOTE_JSON, # local and remote have similar structures
            "projects.json": DEFAULT_PROJECTS_JSON,
            "remote1.json": DEFAULT_REMOTE_JSON,
            "stats.json": DEFAULT_STATS_JSON
        }
        for filename, default_content in files_to_check.items():
            dest_path = path.join(self.credentials_home, filename)
            if not path.exists(dest_path):
                print(f"'{filename}' not found. Creating it with default values.")
                save_json(default_content, dest_path)
            else:
                print(f"'{filename}' already exists.")

    def _configure_local_json(self):
        """Guides the user through setting paths in local.json."""
        print("\n--- ⚙️ Configuring Local Machine Settings (local.json) ---")
        file_path = path.join(self.credentials_home, 'local.json')
        config = self._load_json(file_path)

        config['NIMB_PATHS'] = self._configure_simple_paths(
            config.get('NIMB_PATHS', {}),
            [("NIMB_HOME", "~/nimb"), ("NIMB_tmp", "~/nimb_tmp"), ("conda_home", "~/miniconda3")]
        )
        config['FREESURFER'] = self._configure_simple_paths(
            config.get('FREESURFER', {}),
            [("FREESURFER_HOME", "~/freesurfer")]
        )
        
        save_json(config, file_path)
        print(f"✓ Local settings saved to {file_path}")

    def _configure_projects_json(self):
        """Guides the user through setting paths for a default project."""
        print("\n--- 📂 Configuring Your First Project (projects.json) ---")
        file_path = path.join(self.credentials_home, 'projects.json')
        config = self._load_json(file_path)
        
        project_name = list(config.keys())[0] if "LOCATION" not in list(config.keys())[0] else "project1"
        new_name = input(f"Enter a name for your project [default: {project_name}]: ").strip() or project_name
        if new_name != project_name:
            config[new_name] = config.pop(project_name)
            project_name = new_name
            
        project_config = config.get(project_name, {})
        locations = config.get("LOCATION", ["local", "remote1"])

        paths_to_set = [
            ("SOURCE_SUBJECTS_DIR", ["local", f"/home/{_get_current_username()}/data/{project_name}/source"]),
            ("SOURCE_BIDS_DIR", ["local", f"/home/{_get_current_username()}/data/{project_name}/bids"]),
            ("PROCESSED_FS_DIR", ["remote1", f"/home/{_get_current_username()}/data/{project_name}/derivatives/freesurfer"]),
            ("materials_DIR", ["local", f"/home/{_get_current_username()}/projects/{project_name}/materials"])
        ]

        for key, default_val in paths_to_set:
            project_config[key] = self._ask_for_project_path(key, project_config.get(key, default_val), locations)
        
        config[project_name] = project_config
        save_json(config, file_path)
        print(f"✓ Project '{project_name}' saved to {file_path}")

    def _configure_remote_json(self):
        """Guides the user through setting remote server paths."""
        print("\n--- ☁️ Configuring Remote Server Settings (remote1.json) ---")
        print("NOTE: These are paths on the remote machine.")
        file_path = path.join(self.credentials_home, 'remote1.json')
        config = self._load_json(file_path)

        config['NIMB_PATHS'] = self._configure_simple_paths(
            config.get('NIMB_PATHS', {}),
            [("NIMB_HOME", "~/nimb"), ("NIMB_tmp", "~/scratch/nimb_tmp")]
        )
        config['FREESURFER'] = self._configure_simple_paths(
            config.get('FREESURFER', {}),
            [("FREESURFER_HOME", "/project/freesurfer")]
        )
        
        save_json(config, file_path)
        print(f"✓ Remote settings saved to {file_path}")

    def _configure_stats_json(self):
        """Guides the user through setting paths for statistics."""
        print("\n--- 📊 Configuring Statistics Paths (stats.json) ---")
        file_path = path.join(self.credentials_home, 'stats.json')
        config = self._load_json(file_path)
        stats_paths = config.get("STATS_PATHS", {})

        # Set the main stats directory
        default_stats_home = f"~/nimb_results/stats"
        stats_paths['STATS_HOME'] = self._ask_for_path("Main Statistics Home", stats_paths.get('STATS_HOME', default_stats_home))
        stats_home_path = stats_paths['STATS_HOME']

        # Ask to auto-populate other paths
        print(f"\nYour main stats directory is: {stats_home_path}")
        if self._get_yes_no("Auto-populate other stats paths as sub-directories? (Recommended)"):
            for key in stats_paths:
                if key != "STATS_HOME":
                    stats_paths[key] = path.join(stats_home_path, key.lower().replace('_dir',''))
            print("Auto-populating paths...")
        
        config['STATS_PATHS'] = stats_paths
        save_json(config, file_path)
        print(f"✓ Statistics settings saved to {file_path}")

    # --- Helper methods for user input ---

    def _configure_simple_paths(self, config_section, paths_to_check):
        for key, default in paths_to_check:
            config_section[key] = self._ask_for_path(key.replace('_', ' '), config_section.get(key, default))
        return config_section
    
    def _ask_for_path(self, name, current_path):
        """Prompts user for a simple path string."""
        expanded_path = current_path.replace("~", self.home_dir)
        prompt = f"\nPath for [{name}] (current: {expanded_path})\nPress ENTER to keep current, or enter new path: "
        user_input = input(prompt).strip()
        return user_input or current_path
    
    def _ask_for_project_path(self, name, current_value, locations):
        """Prompts user for a project path, which includes a location and a path string."""
        current_loc, current_path = current_value
        # 1. Get the path string
        new_path = self._ask_for_path(name, current_path)
        
        # 2. Get the location
        print(f"Where is this path located? (current: {current_loc})")
        for i, loc in enumerate(locations, 1):
            print(f"  {i}) {loc}")
        
        while True:
            choice = input(f"Choose a location number [1-{len(locations)}]: ").strip()
            try:
                new_loc = locations[int(choice) - 1]
                break
            except (ValueError, IndexError):
                print("Invalid choice, please try again.")
        
        return [new_loc, new_path]

    def _get_yes_no(self, question):
        """Prompts the user with a yes/no question."""
        while True:
            response = input(f"{question} (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            if response in ['n', 'no']:
                return False
            print("Invalid input. Please enter 'y' or 'n'.")
            
    def _load_json(self, filepath):
        """Loads a JSON file, returning an empty dict on failure."""
        if path.exists(filepath):
            with open(filepath, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

if __name__ == '__main__':
    SetupManager().run_setup()