#!/bin/bash
#
# Name:    updateFiles.sh
# Purpose: A utility script to download the latest versions of key NIMB files
#          directly from the official GitHub repository.
#
# This helps in applying patches or updates without a full re-installation.
#
# Note: This script uses `wget` and ignores SSL certificate checks for simplicity.

# Array of files to check and update.
# Modify this list to control which files are managed by the script.
declare -a FILES=(
    "https://raw.githubusercontent.com/alexhanganu/nimb/main/nimb/nimb/nimb.py"
    "https://raw.githubusercontent.com/alexhanganu/nimb/main/nimb/nimb/setup/config_manager.py"
    "https://raw.githubusercontent.com/alexhanganu/nimb/main/nimb/nimb/distribution/distribution_manager.py"
    # Add other key files here as needed
)

UPDATED=false
# The root directory of the NIMB installation
NIMB_ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Checking for updates..."

# Create a temporary directory for downloads
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Loop through each file, download it, and compare with the local version.
for file_url in "${FILES[@]}"; do
    filename=$(basename "$file_url")
    # Determine the relative path within the project structure
    relative_path=$(echo "$file_url" | sed -n 's|.*nimb/main/\(.*\)|/\1|p')
    local_file_path="${NIMB_ROOT_DIR}${relative_path}"

    echo -n "Checking ${filename}... "

    # Download the latest version quietly
    wget --quiet --no-check-certificate "$file_url" -O "$filename.latest"

    if [ ! -f "$local_file_path" ]; then
        echo "Local file not found. Installing."
        mv "$filename.latest" "$local_file_path"
        UPDATED=true
    # Compare the downloaded file with the local one
    elif ! diff --quiet "$filename.latest" "$local_file_path"; then
        echo "Update found. Replacing local file."
        mv "$filename.latest" "$local_file_path"
        UPDATED=true
    else
        echo "Already up to date."
        rm "$filename.latest"
    fi
done

# Cleanup the temporary directory
cd ..
rm -rf "$TEMP_DIR"

if [ "$UPDATED" = true ]; then
    echo "Update process finished. Some files were updated."
    exit 1
else
    echo "All files are up to date."
    exit 0
fi
