#!/bin/bash
#
# Name:    setup_nimb.sh
# Purpose: Sets up the shell environment to run the NIMB command-line tool.
#
# Usage:
#   This script must be 'sourced' to affect your current shell session.
#   From a bash or sh shell, run:
#   source /path/to/your/nimb/setup/setup_nimb.sh
#
#   It is recommended to add this line to your shell profile (e.g., ~/.bashrc or ~/.zshrc)
#   so the environment is configured automatically when you open a new terminal.

# Set NIMB_HOME to the directory containing this script, if it's not already set.
if [ -z "$NIMB_HOME" ]; then
    # Resolve the directory where this script lives
    export NIMB_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    echo "NIMB_HOME was not set. Defaulting to: $NIMB_HOME"
fi

# Check if the NIMB_HOME directory exists
if [ ! -d "$NIMB_HOME" ]; then
    echo "ERROR: NIMB_HOME directory does not exist: $NIMB_HOME"
    return 1;
fi

# Add the main NIMB directory to the PATH so you can run 'nimb.py' from anywhere.
# This assumes your main executable is in 'nimb/nimb/'.
NIMB_EXECUTABLE_PATH="$NIMB_HOME/nimb"
if [[ ":$PATH:" != *":$NIMB_EXECUTABLE_PATH:"* ]]; then
    export PATH="$NIMB_EXECUTABLE_PATH:$PATH"
    echo "Added NIMB to your PATH."
fi

# Add an alias for convenience
alias nimb="python $NIMB_HOME/nimb/nimb.py"

echo "NIMB environment is configured. You can now use the 'nimb' command."
