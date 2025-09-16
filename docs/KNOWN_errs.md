FreeSurfer:
Error: missing Tcl_Init
Solve: export TCL_LIBRARY=../freesurfer/lib/tktools/tcl8.4

Error: missing libjpeg.so.62
Solve: sudo apt-get install libjpeg62-dev

MATLAB: Notes: 
On the target computer, append the following to your LD_LIBRARY_PATH environment variable:
/tmp/tmp.KMkjZfw9YN/install-target/v84/runtime/glnxa64:/tmp/tmp.KMkjZfw9YN/install-target/v84/bin/glnxa64:/tmp/tmp.KMkjZfw9YN/install-target/v84/sys/os/glnxa64:

Next, set the XAPPLRESDIR environment variable to the following value:
/tmp/tmp.KMkjZfw9YN/install-target/v84/X11/app-defaults