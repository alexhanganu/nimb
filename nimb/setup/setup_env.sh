#!/bin/bash
#
# Name:    setup_env.sh
# Purpose: A utility script to configure the shell environment for NIMB
#          and to update the application from GitHub.
#
# --- Usage ---
#
# 1. To configure your current shell session (add this to ~/.bashrc or ~/.zshrc):
#    source /path/to/nimb/setup/setup_env.sh
#
# 2. To check for and apply updates to key files:
#    bash /path/to/nimb/setup/setup_env.sh update
#

# --- Main Functions ---

# Function to set up the shell environment
setup_environment() {
    # Set NIMB_HOME to the root of the repo if it's not already set.
    if [ -z "$NIMB_HOME" ]; then
        # Resolve the directory two levels above this script's location
        export NIMB_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
        echo "NIMB_HOME was not set. Defaulting to: $NIMB_HOME"
    fi

    # Check if the NIMB_HOME directory exists
    if [ ! -d "$NIMB_HOME" ]; then
        echo "ERROR: NIMB_HOME directory does not exist: $NIMB_HOME"
        return 1;
    fi

    # Add the main NIMB executable directory to the PATH
    NIMB_EXECUTABLE_PATH="$NIMB_HOME/nimb"
    if [[ ":$PATH:" != *":$NIMB_EXECUTABLE_PATH:"* ]]; then
        export PATH="$NIMB_EXECUTABLE_PATH:$PATH"
        echo "Added NIMB to your PATH."
    fi

    # Add a convenient alias for running the main script
    alias nimb="python3 $NIMB_HOME/nimb/nimb.py"

    echo "NIMB environment is configured. You can now use the 'nimb' command."
}

# Function to update key files from GitHub
update_nimb() {
    echo "Checking for NIMB updates..."
    
    # List of key files to keep updated from the main branch
    declare -a FILES=(
        "https://raw.githubusercontent.com/alexhanganu/nimb/main/nimb/nimb.py"
        "https://raw.githubusercontent.com/alexhanganu/nimb/main/nimb/setup/config_manager.py"
        "https://raw.githubusercontent.com/alexhanganu/nimb/main/nimb/distribution/distribution_manager.py"
    )

    local nimb_root_dir
    nimb_root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    local updated_flag=false

    for file_url in "${FILES[@]}"; do
        local filename
        filename=$(basename "$file_url")
        # Determine the relative path from the repo root
        local relative_path
        relative_path=$(echo "$file_url" | sed -n 's|.*nimb/main/\(.*\)|/\1|p')
        local local_file_path="${nimb_root_dir}${relative_path}"

        echo -n "Checking ${filename}... "

        # Download the latest version to a temporary file
        local temp_file
        temp_file=$(mktemp)
        if ! curl -sL "$file_url" -o "$temp_file"; then
            echo "Failed to download."
            rm -f "$temp_file"
            continue
        fi

        if [ ! -f "$local_file_path" ]; then
            echo "Local file not found. Installing."
            mv "$temp_file" "$local_file_path"
            updated_flag=true
        elif ! diff --quiet "$temp_file" "$local_file_path"; then
            echo "Update found. Overwriting local file."
            mv "$temp_file" "$local_file_path"
            updated_flag=true
        else
            echo "Already up to date."
            rm -f "$temp_file"
        fi
    done

    if [ "$updated_flag" = true ]; then
        echo "Update process finished. Some files were updated."
    else
        echo "All files are up to date."
    fi
}

# --- Script Logic ---

# Check if an argument is provided (e.g., "update")
if [[ -n "$1" ]]; then
    if [[ "$1" == "update" ]]; then
        update_nimb
    else
        echo "Unknown command: $1. Use 'update' or source the script without arguments."
    fi
else
    # If sourced, run the setup function.
    # The BASH_SOURCE check prevents execution when sourced.
    if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
         echo "This script is meant to be sourced to set up your environment."
         echo "Usage: source ${BASH_SOURCE[0]}"
         exit 1
    fi
    setup_environment
fi