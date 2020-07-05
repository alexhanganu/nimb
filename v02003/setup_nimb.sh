#!/bin/bash -p

#############################################################################
# Name:    setup_nimb.sh
# Purpose: Setup the environment to run nimb
#
#############################################################################

VERSION='setup_nimb.sh 1.0'

## Print help if --help or -help is specified
if [ $# -gt 1 ]; then
  if [[ "$1" == "--help" || "$1" == "-help" ]]; then
    echo "setup_nimb.sh"
    echo ""
    echo "Purpose: Setup the environment to run nimb"
    echo ""
    echo "Usage:"
    echo ""
    echo "1. Create an environment variable called NIMB_HOME and"
    echo "   set it to the directory in which nimb is installed."
    echo "2. From a sh or bash shell or (.bash_login): "
    echo '       source $NIMB_HOME/seup_nimb.sh'
    return 0;
  fi
fi

## Get the name of the operating system
os=`uname -s`
export OS=$os

## Set this environment variable to suppress the output.
if [ -n "$FS_FREESURFERENV_NO_OUTPUT" ]; then
    output=0
else
    output=1
fi

if [[ -z "$USER" || -z "$PS1" ]]; then
    output=0
fi

## Check if NIMB_HOME variable exists, then check if the actual
## directory exists.
if [ -z "$NIMB_HOME" ]; then
    echo "ERROR: environment variable NIMB_HOME is not defined"
    echo "       Run the command 'export NIMB_HOME <nimb_home>'"
    echo "       where <nimb_home> is the directory where nimb"
    echo "       is installed."
    return 1;
fi

if [ ! -d $NIMB_HOME ]; then
    echo "ERROR: $NIMB_HOME "
    echo "       does not exist. Check that this value is correct.";
    return 1;
fi



## Now we'll set directory locations based on FREESURFER_HOME for use
## by other programs and scripts.

## Set up the path. They should probably already have one, but set a
## basic one just in case they don't. Then add one with all the
## directories we just set.  Additions are made along the way in this
## script.
if [ -z "$PATH" ]; then
    PATH="~/bin:/bin:/usr/bin:/usr/local/bin"
fi


export NIMB_HOME=$NIMB_HOME
export       LOCAL_DIR=$NIMB_HOME/local

if [[ $output == 1 ]]; then
    echo "NIMB_HOME   $NIMB_HOME"
fi


# set NIMB to match NIMB_HOME
export NIMB=$NIMB_HOME

####################################################################
