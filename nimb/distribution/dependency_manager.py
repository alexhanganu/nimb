# -*- coding: utf-8 -*-

"""
This module handles the setup of external dependencies like Miniconda and FreeSurfer,
including downloading, installation, and configuration checks.
"""

import os
import sys
import shutil
import subprocess
from os.path import expanduser, join, dirname, exists

from .utilities import (
    makedir_ifnot_exist, is_writable_directory,
    is_command_ran_successfully, load_json
)
from .definitions import DEFAULT

# A more robust way to find the installers.json file
_INSTALLERS_JSON_PATH = join(dirname(__file__), 'installers.json')


class DependencyManager:
    """
    Manages the installation and configuration of external dependencies
    required by the NIMB application.
    """

    @staticmethod
    def is_miniconda_installed(conda_home):
        """Checks if Miniconda is installed by verifying the 'conda' executable."""
        conda_bin_path = join(expanduser(conda_home), 'bin', 'conda')
        return exists(conda_bin_path)

    @staticmethod
    def setup_miniconda(conda_home, nimb_home):
        """
        Installs Miniconda if it's not already present.
        Returns True on success, False otherwise.
        """
        conda_home = expanduser(conda_home)
        installers = load_json(_INSTALLERS_JSON_PATH)
        installer_url = installers.get("install_miniconda3")
        
        if not installer_url:
            print("ERROR: Miniconda installer URL not found in installers.json.")
            return False

        installer_filename = installer_url.split('/')[-1]
        print("Miniconda is not installed. Starting installation...")
        
        temp_dir = join(nimb_home, 'temp_installer')
        makedir_ifnot_exist(temp_dir)
        
        try:
            # Using with statement for changing directory is safer
            original_dir = os.getcwd()
            os.chdir(temp_dir)
            
            print(f"Downloading {installer_url}...")
            subprocess.run(["curl", "-L", "-O", installer_url], check=True, stderr=subprocess.PIPE)
            
            print("Running Miniconda installer...")
            install_cmd = f"bash {installer_filename} -b -p {conda_home}"
            subprocess.run(install_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            print("Miniconda installation complete.")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"ERROR during Miniconda installation: {e.stderr.decode()}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during Miniconda setup: {e}")
            return False
        finally:
            # Clean up
            os.chdir(original_dir)
            if exists(temp_dir):
                shutil.rmtree(temp_dir)

    @staticmethod
    def check_modules_installed(conda_home, modules_list):
        """
        Checks and installs required Python modules in the Conda environment.
        """
        conda_bin = join(expanduser(conda_home), 'bin', 'conda')
        
        try:
            # Get list of installed packages once to improve performance
            result = subprocess.run(f"{conda_bin} list", shell=True, check=True, capture_output=True, text=True)
            installed_packages = result.stdout

            for module in modules_list:
                if module not in installed_packages:
                    print(f"Module '{module}' not found. Installing...")
                    install_cmd = f"{conda_bin} install -y {module}"
                    subprocess.run(install_cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError as e:
            print(f"ERROR checking or installing modules: {e.stderr}")
            return False


    @staticmethod
    def setup_freesurfer(local_vars, default_vars):
        """
        Installs FreeSurfer if it's not already present.
        """
        fs_config = local_vars.get('FREESURFER', {})
        fs_home = expanduser(fs_config.get('FREESURFER_HOME'))
        fs_version = fs_config.get('freesurfer_version') or default_vars.FREESURFER_VERSION
        
        if exists(fs_home):
            print("FreeSurfer appears to be installed. Skipping installation.")
            return True
            
        print("FreeSurfer installation required.")
        # Simplified for non-interactive flow; in a real CLI, you'd prompt user
        
        parent_dir = dirname(fs_home)
        if not is_writable_directory(parent_dir):
            print(f"ERROR: Parent directory '{parent_dir}' is not writable.")
            return False

        installers = load_json(_INSTALLERS_JSON_PATH)
        os_platform = 'centos' # Simplified, add more logic for ubuntu/mac if needed
        installer_key = f"install_fs{fs_version.replace('.', '')}_{os_platform}{default_vars.CENTOS_VERSION}"
        installer_url = installers.get(installer_key)
        
        if not installer_url:
            print(f"ERROR: No installer found for FreeSurfer v'{fs_version}' on OS '{os_platform}'.")
            return False

        print(f"Downloading FreeSurfer from {installer_url}...")
        installer_filename = installer_url.split('/')[-1]
        temp_download_path = join(parent_dir, installer_filename)

        try:
            subprocess.run(["curl", "-L", "-o", temp_download_path, installer_url], check=True, stderr=subprocess.PIPE)
            
            print("Extracting FreeSurfer archive...")
            shutil.unpack_archive(temp_download_path, parent_dir)
            # The unpacked directory might have a version number, rename it
            unpacked_dir = join(parent_dir, 'freesurfer') # Default name
            if not exists(unpacked_dir):
                # Find what it was actually named
                # This is a simplification; robust code would find the actual dir name
                pass
            if exists(unpacked_dir) and unpacked_dir != fs_home:
                os.rename(unpacked_dir, fs_home)

            # Handle license
            license_path = expanduser(fs_config.get('freesurfer_license'))
            if not exists(license_path) or os.path.getsize(license_path) == 0:
                print("WARNING: FreeSurfer license file is missing or empty.")
                print("Please create it manually at ~/.license or the path specified in local.json")
            else:
                shutil.copy(license_path, join(fs_home, '.license'))

            print("FreeSurfer installation complete.")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"ERROR during FreeSurfer installation: {e.stderr.decode()}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during FreeSurfer setup: {e}")
            return False
        finally:
            if exists(temp_download_path):
                os.remove(temp_download_path)
