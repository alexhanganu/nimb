# -*- coding: utf-8 -*-

"""
ConfigManager class
Responsible for loading all configurations,
paths, and user-provided parameters for the NIMB application
at runtime.
Non-interactive.
"""

import os
import sys
import argparse
import getpass
from os import path, environ

try:
    from ..distribution.utilities import load_json
    from ..distribution.logger import Log
    from .version import __version__
except ImportError:
    # Fallback for different execution contexts
    sys.path.append(path.abspath(path.join(path.dirname(__file__), '..')))
    from distribution.utilities import load_json
    from distribution.logger import Log
    from setup.version import __version__


class ConfigManager:
    """
    Manages all configuration aspects of the NIMB application at runtime,
    including loading JSON files and parsing command-line arguments.
    """
    def __init__(self):
        self.credentials_home = self._get_credentials_home()
        self.username = getpass.getuser()

        # Load core configuration files
        self.projects = self._load_json_file("projects.json")
        if not self.projects:
            print(f"ERROR: 'projects.json' not found in {self.credentials_home}. "
                  "Please run the interactive setup first.", file=sys.stderr)
            sys.exit(1)
            
        self.location_vars = self._get_all_locations_vars()
        self.stats_vars = self._load_json_file("stats.json")

        # Parse command-line arguments
        self.params = self._get_parameters()
        
        # Initialize logger
        tmp_dir_template = self.location_vars.get('local', {}).get('NIMB_PATHS', {}).get('NIMB_tmp', '/tmp/nimb')
        home_dir = environ.get('HOME') or environ.get('USERPROFILE')
        tmp_dir = tmp_dir_template.replace("~", home_dir)

        if not path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        self.logger = Log(tmp_dir).logger

    def _get_credentials_home(self):
        """Determines the application's credentials home directory (~/.nimb)."""
        home_dir = environ.get('HOME') or environ.get('USERPROFILE')
        return path.join(home_dir, ".nimb")

    def _load_json_file(self, filename):
        """Loads a JSON file from the credentials directory."""
        file_path = path.join(self.credentials_home, filename)
        if not path.exists(file_path):
            print(f"WARNING: Configuration file not found: {file_path}", file=sys.stderr)
            return {}
        return load_json(file_path)

    def _get_all_locations_vars(self):
        """Loads all location variables from local.json and remote*.json files."""
        locations = {'local': self._load_json_file("local.json")}
        if not locations['local']:
            print(f"ERROR: 'local.json' not found in {self.credentials_home} or is empty. "
                  "Please run the interactive setup.", file=sys.stderr)
            sys.exit(1)

        for f in os.listdir(self.credentials_home):
            if f.startswith('remote') and f.endswith('.json'):
                remote_name = path.splitext(f)[0]
                locations[remote_name] = self._load_json_file(f)
        return locations
        
    def _get_project_ids(self):
        """Returns a list of project IDs from the projects config."""
        # Exclude special keys like "LOCATION" and "EXPLANATION"
        return [k for k in self.projects.keys() if k.isupper() is False]

    def _get_parameters(self):
        """Parses and returns command-line arguments."""
        project_ids = self._get_project_ids()
        if not project_ids:
             print(f"ERROR: No projects found in {path.join(self.credentials_home, 'projects.json')}", file=sys.stderr)
             sys.exit(1)

        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=f"NIMB v{__version__}",
            epilog="Documentation at https://github.com/alexhanganu/nimb"
        )
        
        # Add arguments...
        parser.add_argument(
            "-process", required=False, default='ready',
            choices=['ready', 'run', 'classify', 'classify2bids', 'fs-get-stats', 
                     'fs-glm', 'fs-glm-image', 'run-stats'],
            help="The main process to execute."
        )
        parser.add_argument(
            "-project", required=False, default=project_ids[0], choices=project_ids,
            help="Name of the project to run."
        )
        # ... (rest of the arguments are the same as your original file)
        parser.add_argument(
            "-do", required=False, default='all',
            choices=['all', 'check-new', 'classify', 'classify2bids', 'process', 
                     'fs-get-masks', 'fs-get-stats', 'fs-glm', 'fs-glm-image', 'run-stats'],
            help="Sub-task for the 'run' process."
        )
        parser.add_argument(
            "-fix-spaces", required=False, action='store_true',
            help="Replace spaces with underscores in paths during classification."
        )
        parser.add_argument(
            "-step", required=False, default='all',
            choices=['all', 'groups', 'ttest', 'anova', 'simplinreg', 'logreg', 
                     'predskf', 'predloo', 'linregmod', 'laterality'],
            help="Specific step for statistical analysis."
        )
        parser.add_argument(
            "-test", required=False, action='store_true',
            help="Run in test mode on a small subset of participants."
        )
        parser.add_argument(
            "-glmcontrast", required=False, nargs="+", default=["g"],
            choices=["g", "g1", "g2", "g3", "g1v0", "g1v1", 'g2v0', "g2v1", 'g3v0', "g3v1"],
            help="Define GLM contrasts to be used."
        )
        parser.add_argument(
            "-glmcorrected", required=False, action='store_true',
            help="Run only the corrected GLM contrasts."
        )
        parser.add_argument(
            "-glmpermutations", required=False, type=int, default=1000,
            help="Number of permutations for GLM analysis."
        )

        return parser.parse_args()

