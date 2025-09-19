# -*- coding: utf-8 -*-
"""
ConfigManager is responsible for loading all configurations, paths, and
user-provided parameters for the NIMB application at runtime. Non-interactive.
"""
import os
import sys
import argparse
import getpass
import shlex
import socket
from os import path, environ
from subprocess import check_output
from distutils.version import LooseVersion

# --- Application Version ---
__version__ = "0.1.2"

# --- Helper Utilities ---

def load_json(filepath):
    """Loads and returns a JSON file as a dictionary."""
    if path.exists(filepath):
        with open(filepath, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# --- Main Configuration Class ---

class ConfigManager:
    """ Manages all configuration aspects of the NIMB application at runtime. """
    def __init__(self):
        self.credentials_home = self._get_credentials_home()
        self.username = getpass.getuser()

        # Load core configuration files
        self.projects = self._load_json_file("projects.json")
        self.location_vars = self._get_all_locations_vars()
        self.stats_vars = self._load_json_file("stats.json")

        if not self.projects or not self.location_vars.get('local'):
            print(f"ERROR: Config files missing in {self.credentials_home}. "
                  "Please run the interactive setup: python nimb/setup/setup.py", file=sys.stderr)
            sys.exit(1)
            
        # Parse command-line arguments
        self.params = self._get_parameters()
        
        # Initialize logger (simplified for this example)
        tmp_dir = self.location_vars['local']['NIMB_PATHS']['NIMB_tmp'].replace("~", environ.get('HOME'))
        if not path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        # self.logger = Log(tmp_dir).logger  # Assuming a logger class exists elsewhere

        # Check for new version of NIMB
        self._check_for_updates()

    def _get_credentials_home(self):
        """Determines the application's credentials home directory (~/.nimb)."""
        home_dir = environ.get('HOME') or environ.get('USERPROFILE')
        return path.join(home_dir, ".nimb")

    def _load_json_file(self, filename):
        """Loads a JSON file from the credentials directory."""
        return load_json(path.join(self.credentials_home, filename))

    def _get_all_locations_vars(self):
        """Loads all location variables from local.json and remote*.json files."""
        locations = {'local': self._load_json_file("local.json")}
        for f in os.listdir(self.credentials_home):
            if f.startswith('remote') and f.endswith('.json'):
                remote_name = path.splitext(f)[0]
                locations[remote_name] = self._load_json_file(f)
        return locations
        
    def _get_project_ids(self):
        """Returns a list of project IDs from the projects config."""
        return [k for k in self.projects.keys() if not k.isupper()]

    def _get_parameters(self):
        """Parses and returns command-line arguments."""
        project_ids = self._get_project_ids() or ['default_project']
        parser = argparse.ArgumentParser(
            description=f"NIMB v{__version__}",
            epilog="Documentation at https://github.com/alexhanganu/nimb"
        )
        # Add arguments (simplified for brevity, should match original file)
        parser.add_argument("-process", required=False, default='ready', help="The main process to execute.")
        parser.add_argument("-project", required=False, default=project_ids[0], choices=project_ids, help="Name of the project.")
        return parser.parse_args()
    
    def _check_for_updates(self, repo="alexhanganu/nimb"):
        """Checks GitHub for a newer version of NIMB and warns the user."""
        try:
            # Check for internet
            socket.create_connection(("8.8.8.8", 53), timeout=1)
            
            # Check for curl
            if not shutil.which("curl"):
                return

            url = f"https://github.com/{repo}/releases/latest"
            output = check_output(shlex.split(f"curl --silent -L {url}")).decode()
            latest_version = output.split(f'/releases/tag/')[1].split('"')[0]

            if LooseVersion(latest_version) > LooseVersion(__version__):
                print(f"\nWARNING: A new version of NIMB is available: {latest_version} (you have {__version__})")
                print("Consider running: bash nimb/setup/setup_env.sh update\n")
        except Exception:
            # Silently fail if check is not possible
            pass