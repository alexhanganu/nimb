# -*- coding: utf-8 -*-
"""
This module handles the first-time interactive setup for the NIMB application.
It creates all necessary configuration files, initializes the database, and can
now also check for, download, and install key dependencies like Miniconda and FreeSurfer.

To run, execute this file directly: python nimb/setup/setup.py
"""
import os
import sys
import shutil
import json
import tarfile
import subprocess
import getpass
import pwd
from os import path
from urllib import request

# --- Default JSON Templates and Installer URLs (consolidated) ---

INSTALLER_URLS = {
    "install_fs7.3.2_centos7": "https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.3.2/freesurfer-linux-centos7_x86_64-7.3.2.tar.gz",
    "install_fs7.2.0_centos7": "https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.2.0/freesurfer-linux-centos7_x86_64-7.2.0.tar.gz",
    "install_fs7.1.1_centos7": "https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.1.1/freesurfer-linux-centos7_x86_64-7.1.1.tar.gz",
    "install_miniconda3": "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
}

DEFAULT_PROJECTS_JSON = { "project1": {}, "LOCATION": ["local", "remote1"] }
DEFAULT_REMOTE_JSON = { "USER": {}, "NIMB_PATHS": {}, "FREESURFER": {} }
DEFAULT_STATS_JSON = { "STATS_PATHS": {} }

# --- Helper Utilities ---

def _get_credentials_home():
    home_dir = os.environ.get('HOME') or os.environ.get('USERPROFILE')
    credentials_home = path.join(home_dir, ".nimb")
    if not path.exists(credentials_home):
        os.makedirs(credentials_home)
    return credentials_home

def _get_current_username():
    try:
        return pwd.getpwuid(os.getuid())[0]
    except (ImportError, KeyError):
        return getpass.getuser()

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

# --- Dependency Installation Logic ---

class DependencyManager:
    """ Handles checking and installing external software dependencies. """
    def __init__(self, config, home_dir):
        self.config = config
        self.home_dir = home_dir
        self.tmp_dir = self.config['NIMB_PATHS'].get('NIMB_tmp', '~/nimb_tmp').replace("~", self.home_dir)
        if not path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

    def run_dependency_check(self):
        """Orchestrates the checking and installation of all dependencies."""
        print("\n--- Checking Miniconda ---")
        self._check_miniconda()

        print("\n--- Checking FreeSurfer ---")
        self._check_freesurfer()

    def _check_miniconda(self):
        conda_home = self.config['NIMB_PATHS']['conda_home'].replace("~", self.home_dir)
        conda_exe = path.join(conda_home, 'bin', 'conda')
        if path.exists(conda_exe):
            print(f"✓ Miniconda found at: {conda_home}")
            return

        print(f"✗ Miniconda not found at the configured path: {conda_home}")
        if self._get_yes_no("Would you like to download and install it now?"):
            self._install_miniconda(conda_home)

    def _install_miniconda(self, install_path):
        """Downloads and runs the Miniconda installer script."""
        installer_url = INSTALLER_URLS['install_miniconda3']
        installer_name = installer_url.split('/')[-1]
        installer_path = path.join(self.tmp_dir, installer_name)

        try:
            print(f"Downloading Miniconda installer to {installer_path}...")
            request.urlretrieve(installer_url, installer_path)
            
            print("Making installer executable...")
            subprocess.run(['chmod', '+x', installer_path], check=True)
            
            print(f"Running Miniconda installer for path: {install_path}")
            subprocess.run([installer_path, '-b', '-p', install_path], check=True)

            print("Updating shell configuration (~/.bashrc) to include conda...")
            bashrc_path = path.join(self.home_dir, '.bashrc')
            with open(bashrc_path, 'a') as f:
                f.write(f'\n# Added by NIMB setup\n')
                f.write(f'export PATH="{install_path}/bin:$PATH"\n')
            
            print("✓ Miniconda installed successfully.")
            print("Please run 'source ~/.bashrc' or restart your terminal to use it.")
        except Exception as e:
            print(f"🔥 ERROR during Miniconda installation: {e}")
        finally:
            if path.exists(installer_path):
                os.remove(installer_path)

    def _check_freesurfer(self):
        fs_home = self.config['FREESURFER']['FREESURFER_HOME'].replace("~", self.home_dir)
        fs_setup_script = path.join(fs_home, 'SetUpFreeSurfer.sh')
        if path.exists(fs_setup_script):
            print(f"✓ FreeSurfer found at: {fs_home}")
            return

        print(f"✗ FreeSurfer not found at the configured path: {fs_home}")
        if self._get_yes_no("Would you like to download and install it now?"):
            self._install_freesurfer(fs_home)

    def _install_freesurfer(self, install_path):
        """Downloads and extracts the FreeSurfer archive."""
        # Simple OS selection for demo; could be auto-detected
        version = self.config['FREESURFER'].get('version', '7.3.2')
        key = f"install_fs{version.replace('.', '')}_centos7"
        installer_url = INSTALLER_URLS.get(key)
        
        if not installer_url:
            print(f"🔥 ERROR: No installer URL found for FreeSurfer version {version}.")
            return

        installer_name = installer_url.split('/')[-1]
        installer_path = path.join(self.tmp_dir, installer_name)
        parent_dir = path.dirname(install_path)
        os.makedirs(parent_dir, exist_ok=True)

        try:
            print(f"Downloading FreeSurfer ({installer_name})... This may take a while.")
            request.urlretrieve(installer_url, installer_path)
            
            print(f"Extracting FreeSurfer archive to {parent_dir}...")
            with tarfile.open(installer_path, "r:gz") as tar:
                tar.extractall(path=parent_dir)
            
            # The extracted folder is named 'freesurfer', rename if target is different
            extracted_dir = path.join(parent_dir, 'freesurfer')
            if extracted_dir != install_path:
                os.rename(extracted_dir, install_path)
            
            self._write_fs_license(install_path)
            print("✓ FreeSurfer installed successfully.")
        except Exception as e:
            print(f"🔥 ERROR during FreeSurfer installation: {e}")
        finally:
            if path.exists(installer_path):
                os.remove(installer_path)

    def _write_fs_license(self, fs_home):
        """Writes the FreeSurfer license from config to the installation directory."""
        license_content = self.config['FREESURFER'].get('freesurfer_license')
        if isinstance(license_content, list) and len(license_content) > 1:
            license_path = path.join(fs_home, 'license.txt')
            print(f"Writing FreeSurfer license to {license_path}...")
            with open(license_path, 'w') as f:
                f.write("\n".join(license_content))
        else:
            print("WARNING: FreeSurfer license not found in config. Please add it manually.")

    def _get_yes_no(self, question):
        while True:
            response = input(f"{question} (y/n): ").lower().strip()
            if response in ['y', 'yes']: return True
            if response in ['n', 'no']: return False
            print("Invalid input.")

# --- Main Interactive Setup Class ---

class SetupManager:
    """ Manages the interactive, one-time setup process for NIMB. """
    def __init__(self):
        self.credentials_home = _get_credentials_home()
        self.home_dir = os.environ.get('HOME') or os.environ.get('USERPROFILE')

    def run_setup(self):
        """ Executes the full interactive setup and dependency installation process. """
        print("--- Welcome to the NIMB Interactive Setup ---")
        self._create_files_if_not_exist()

        # Step 1: Configure all JSON files
        self._configure_local_json()
        self._configure_projects_json()
        self._configure_remote_json()
        self._configure_stats_json()

        # Step 2: Offer to install dependencies based on the configuration
        print("\n--- 🚀 Checking and Installing Dependencies ---")
        if self._get_yes_no("Configuration complete. Check for missing dependencies now?"):
            local_config = self._load_json(path.join(self.credentials_home, 'local.json'))
            dep_manager = DependencyManager(local_config, self.home_dir)
            dep_manager.run_dependency_check()

        print("\n✅ --- NIMB Setup Complete! ---")
        print(f"Your configuration files are stored in: {self.credentials_home}")
        print("To finish, configure your shell: source nimb/setup/setup_env.sh")

    def _create_files_if_not_exist(self):
        print("\nChecking for essential configuration files...")
        files_to_check = { "local.json": DEFAULT_REMOTE_JSON, "projects.json": DEFAULT_PROJECTS_JSON, "remote1.json": DEFAULT_REMOTE_JSON, "stats.json": DEFAULT_STATS_JSON }
        for filename, default_content in files_to_check.items():
            dest_path = path.join(self.credentials_home, filename)
            if not path.exists(dest_path):
                print(f"'{filename}' not found. Creating it with default values.")
                save_json(default_content, dest_path)

    def _configure_local_json(self):
        print("\n--- ⚙️ Configuring Local Machine Settings (local.json) ---")
        file_path, config = self._load_config_file('local.json')
        config['NIMB_PATHS'] = self._configure_simple_paths(config.get('NIMB_PATHS', {}), [("NIMB_HOME", "~/nimb"), ("NIMB_tmp", "~/nimb_tmp"), ("conda_home", "~/miniconda3")])
        config['FREESURFER'] = self._configure_simple_paths(config.get('FREESURFER', {}), [("FREESURFER_HOME", "~/freesurfer")])
        save_json(config, file_path)

    def _configure_projects_json(self):
        print("\n--- 📂 Configuring Your First Project (projects.json) ---")
        file_path, config = self._load_config_file('projects.json')
        project_name = list(config.keys())[0] if "LOCATION" not in list(config.keys())[0] else "project1"
        new_name = input(f"Enter project name [default: {project_name}]: ").strip() or project_name
        if new_name != project_name: config[new_name] = config.pop(project_name); project_name = new_name
        project_config = config.get(project_name, {}); locations = config.get("LOCATION", ["local", "remote1"])
        paths_to_set = [("SOURCE_SUBJECTS_DIR", ["local", f"~/{project_name}/source"]), ("PROCESSED_FS_DIR", ["remote1", f"~/{project_name}/derivatives"])]
        for key, default_val in paths_to_set: project_config[key] = self._ask_for_project_path(key, project_config.get(key, default_val), locations)
        config[project_name] = project_config; save_json(config, file_path)

    def _configure_remote_json(self):
        print("\n--- ☁️ Configuring Remote Server Settings (remote1.json) ---")
        file_path, config = self._load_config_file('remote1.json')
        config['NIMB_PATHS'] = self._configure_simple_paths(config.get('NIMB_PATHS', {}), [("NIMB_HOME", "~/nimb"), ("NIMB_tmp", "~/scratch/nimb_tmp")])
        config['FREESURFER'] = self._configure_simple_paths(config.get('FREESURFER', {}), [("FREESURFER_HOME", "/project/freesurfer")])
        save_json(config, file_path)

    def _configure_stats_json(self):
        print("\n--- 📊 Configuring Statistics Paths (stats.json) ---")
        file_path, config = self._load_config_file('stats.json')
        stats_paths = config.get("STATS_PATHS", {})
        stats_paths['STATS_HOME'] = self._ask_for_path("Main Statistics Home", stats_paths.get('STATS_HOME', "~/nimb_results/stats"))
        if self._get_yes_no("Auto-populate other stats paths as sub-directories?"):
            for key in stats_paths:
                if key != "STATS_HOME": stats_paths[key] = path.join(stats_paths['STATS_HOME'], key.lower().replace('_dir',''))
        config['STATS_PATHS'] = stats_paths; save_json(config, file_path)

    def _load_config_file(self, filename):
        file_path = path.join(self.credentials_home, filename)
        return file_path, self._load_json(file_path)

    def _configure_simple_paths(self, section, paths):
        for key, default in paths: section[key] = self._ask_for_path(key.replace('_', ' '), section.get(key, default))
        return section

    def _ask_for_path(self, name, current):
        prompt = f"\nPath for [{name}] (current: {current})\nEnter to keep, or provide new path: "
        return input(prompt).strip() or current

    def _ask_for_project_path(self, name, current, locations):
        new_path = self._ask_for_path(name, current[1])
        print(f"Where is this path? (current: {current[0]})"); [print(f"  {i}) {loc}") for i, loc in enumerate(locations, 1)]
        while True:
            try: return [locations[int(input(f"Choose [1-{len(locations)}]: ").strip()) - 1], new_path]
            except (ValueError, IndexError): print("Invalid choice.")

    def _get_yes_no(self, question):
        while True:
            resp = input(f"{question} (y/n): ").lower().strip();
            if resp in ['y', 'yes']: return True
            if resp in ['n', 'no']: return False

    def _load_json(self, filepath):
        if path.exists(filepath):
            with open(filepath, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError: return {}
        return {}


if __name__ == '__main__':
    SetupManager().run_setup()