#!/bin/python
#Alexandru Hanganu, 2019 november 3

from var import max_walltime

def Get_walltime(process):
    
    suggested_times = {
        'registration':'01:00:00',
        'recon':'30:00:00',
        'recbase':'30:00:00',
        'reclong':'23:00:00',
        'qcache':'03:00:00',
        'brstem':'02:00:00',
        'hip':'02:00:00',
        }
    if suggested_times[process] <= max_walltime:
        walltime = suggested_times[process]
    else:
        walltime = max_walltime

    return walltime
