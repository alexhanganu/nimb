#!/bin/sh
# script for execution of deployed applications
#
# Sets up the MCR environment for the current $ARCH and executes 
# the specified command.
#

exe_name=$0
exe_dir=`dirname "$0"`

echo "------------------------------------------"
if [ "x$1" = "x" ]; then
  echo Usage:
  echo    $0 \<deployedMCRroot\> args
else
  echo Setting up environment variables
  MCRROOT="$1"
  echo ---
  
  MCRJRE=${MCRROOT}/sys/java/jre/glnxa64/jre/lib/amd64 ;

  export XAPPLRESDIR=${MCRROOT}/X11/app-defaults ;
  unset JAVA_TOOL_OPTIONS

  ORIG_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
  export  LD_LIBRARY_PATH_MCR_SNAPSHOT=$ORIG_LD_LIBRARY_PATH

  MCR_LD_LIBRARY_PATH=${MCRROOT}/runtime/glnxa64:${MCRROOT}/bin/glnxa64:${MCRROOT}/sys/os/glnxa64:${MCRJRE}/native_threads:${MCRJRE}/server:${MCRJRE}/client:${MCRJRE}

  # since we're going to call fs binaries from matlab, we want them to link to the system libstdc++ and not the matlab version
  libstdpath="$(/sbin/ldconfig -p | grep libstdc++.so | sed -n 1p | awk '{ print $NF }')"
  if [ -z "$libstdpath" ]; then echo "error: can't find libstdc++.so" && exit 1; fi
  libstddir="$(dirname $libstdpath)"

  export LD_LIBRARY_PATH=.:${libstddir}:${MCR_LD_LIBRARY_PATH}:${ORIG_LD_LIBRARY_PATH}

  if [ -x "$(command -v ldd)" ] && [ -n "$(ldd ${exe_dir}/SegmentThalamicNuclei 2>&1 | grep 'not found')" ]; then
    echo "INFO: error loading libraries in default configuration, trying with MCR libraries only"
    export LD_LIBRARY_PATH=.:${MCR_LD_LIBRARY_PATH}:${ORIG_LD_LIBRARY_PATH}
  fi

  echo LD_LIBRARY_PATH is ${LD_LIBRARY_PATH};

  shift 1
  args=
  while [ $# -gt 0 ]; do
      token=$1
      args="${args} ${token}" 
      shift
  done

  RANDOMNUMBER=$(od -vAn -N4 -tu4 < /dev/urandom) ;
  MCR_CACHE_ROOT=$( echo "/tmp/MCR_${RANDOMNUMBER}/" | tr -d ' ' ) ;
  export MCR_CACHE_ROOT;

  cmd="${exe_dir}/SegmentThalamicNuclei $args"
  eval ${cmd}
  returnVal=$?
  rm -rf $MCR_CACHE_ROOT 

fi

exit $returnVal
