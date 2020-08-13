#!/bin/python
#Alexandru Hanganu, 2018 June 5

from os import listdir, path, mkdir, system, remove
import shutil, datetime, threading
from lib.var import local_maindir
import distribution.lib.local_db

from multiprocessing import cpu_count

from sys import version_info
if version_info[0] >= 3:
    from queue import Queue
else:
    from Queue import Queue


LONGITUDINAL_DEFINITION = ['T2','T3']

dirfssubj=local_maindir+'freesurfer/subjects/'
dirmain=local_maindir+'a/'
dirres=dirmain+'res/'

date=datetime.datetime.now()
dt=str(date.year)+str(date.month)+str(date.day)
dth=str(date.year)+'/'+str(date.month)+'/'+str(date.day)+' '+str(date.hour)+'h'

nr_cpu = cpu_count()
local_ls_cmds = []

def chksubjidinfs(subjid):
    lsallsubjid=listdir(dirfssubj)
    if subjid in lsallsubjid:
        return True
    else:
        return False


def chkIsRunning(subjid):
    lsscripts=listdir(dirfssubj+subjid+'/scripts')
    if any('IsRunning.lh+rh' in i for i in lsscripts):
        return True
    else:
        return False


def chkreconf(subjid):
    if 'recon-all-status.log' in listdir(dirfssubj+subjid+'/scripts/'):
        with open(dirfssubj+subjid+'/scripts/recon-all-status.log','rt') as f:
            for line in f:
                if 'recon-all -s' in line:
                    if 'exited with ERRORS' in line:
                        local_db.Update_status_log('exited with ERRORS line is present')
                        return False
                    elif 'finished without error' in line:
                        return True
                    else:
                        local_db.Update_status_log('neither lines were found')
                        return False
    else:
        return False        


def chk_if_recon_done(subjid):
    if 'wmparc.mgz' in listdir(dirfssubj+subjid+'/mri/'):
        return True
    else:
        return False


def chk_if_qcache_done(subjid):
    if 'rh.w-g.pct.mgh.fsaverage.mgh' in listdir(dirfssubj+subjid+'/surf/'):
        return True
    else:
        return False


def chkhipf(subjid):
    lsscripts=listdir(dirfssubj+subjid+'/scripts/')
    if any('hippocampal-subfields-T1' in i for i in lsscripts):
        with open(dirfssubj+subjid+'/scripts/hippocampal-subfields-T1.log','rt') as readlog:
            for line in readlog:
                line2read=[line]
                if any('Everything done' in i for i in line2read):
                    lsmri=listdir(dirfssubj+subjid+'/mri/')
                    if any('lh.hippoSfVolumes-T1.v10.txt' in i for i in lsmri):
                        if any('rh.hippoSfVolumes-T1.v10.txt' in i for i in lsmri):
                            return True
                    else:
                        return False
    else:
        return False


def chkbrstemf(subjid):
    lsscripts=listdir(dirfssubj+subjid+'/scripts/')
    if any('brainstem-structures' in i for i in lsscripts):
        with open(dirfssubj+subjid+'/scripts/brainstem-structures.log','rt') as readlog:
            for line in readlog:
                line2read=[line]
                if any('Everything done' in i for i in line2read):
                    lsmri=listdir(dirfssubj+subjid+'/mri/')
                    if any('brainstemSsVolumes' in i for i in lsmri):
                        return True
                    else:
                        return False
    else:
        return False 


def chk_lgif(subjid):
    lssstats=listdir(dirfssubj+subjid+'/stats/')
    if any('lh.aparc.pial_lgi.stats' in i for i in lssstats):
        return True
    else:
        return False 

class MyThread(threading.Thread):
    cmd_queues = {}  # Map of uuid -> Queue for all instances of MyThread

    def __init__(self, uuid):
        super(threading.Thread, self).__init__()
        self.cmd_q = Queue()
        self.uuid = uuid
        MyThread.cmd_queues[uuid] = self.cmd_q


def send_to_thread_update():
    for cmd in local_ls_cmds:
        if threading.active_count() < nr_cpu:
            t = MyThread(system(cmd))
            #t.start()        #threading.Thread(target=system(cmd)).start()
            local_ls_cmds.remove(cmd)
            print('STARTED: '+cmd+'\n         '+str(len(local_ls_cmds))+' commands left')
        else:
            time.sleep(600)
            if len(local_ls_cmds)>0:
                send_to_thread_update()


def makesubmitpbs_registration(ls):
    def i4subj(subjid):
        lssubjdir=listdir(local_maindir+"subjects/")
        lsi = {'t1':[],'flair':[]}
        for LONG in LONGITUDINAL_DEFINITION:
            if LONG in subjid:
                longitudinal = True
                longitudinal_name = LONG
                break
            else:
                longitudinal = False
        if longitudinal:
            for DIR in lssubjdir:
                if subjid in DIR and longitudinal_name in DIR:
                        if '_t1' in DIR:
                            lsi['t1'].append(DIR)
                        if '_flair' in DIR:
                            lsi['flair'].append(DIR)
        else:
            for DIR in lssubjdir:
                for LONG in LONGITUDINAL_DEFINITION:
                    if LONG in DIR:
                        DIR_not_Long = False
                        break
                    else:
                        DIR_not_Long = True
                if DIR_not_Long:
                    if subjid in DIR:
                        print(DIR)
                        if '_flair' in DIR:
                            lsi['flair'].append(DIR)
                        elif '_t1' in DIR:
                            lsi['t1'].append(DIR)
                        else:
                            lsi['t1'].append(DIR)
        t=0
        lsrecon = []
        while t<len(lsi['t1']):
            x = [lsi['t1'][t]]
            if path.isdir(local_maindir+'subjects/'+x[0]+'/'):
                pathf=listdir(local_maindir+'subjects/'+x[0]+'/')
                if any('.dcm' in i for i in pathf):
                    PATH_f=(local_maindir+'subjects/'+x[0]+'/'+pathf[0])
            elif any('.nii' | '.nii.gz' in i for i in x):
                PATH_f=(local_maindir+'subjects/'+x[0])        
            elif any('.mnc' | '.mnc.gz' in i for i in x):
                system('mnc2nii '+local_maindir+'subjects/'+x[0]+' '+local_maindir+'subjects/'+subjid+'_t1.nii.gz')
                PATH_f=(local_maindir+'subjects/'+subjid+'_t1.nii.gz')        
            lsrecon.append('-i '+PATH_f)        
            t=t+1
        f=0
        while f<len(lsi['flair']):
            x = [lsi['flair'][f]]
            if path.isdir(local_maindir+'subjects/'+x[0]+'/'):
                pathf=listdir(local_maindir+'subjects/'+x[0]+'/')
                if any('.dcm' in i for i in pathf):
                    PATH_f=(local_maindir+'subjects/'+x[0]+'/'+pathf[0])
            elif any('.nii' | '.nii.gz' in i for i in x):
                PATH_f=(local_maindir+'subjects/'+x[0])        
            elif any('.mnc' | '.mnc.gz' in i for i in lssubjdir):
                system('mnc2nii '+local_maindir+'subjects/'+x[0]+' '+local_maindir+'subjects/'+subjid+'_t1.nii.gz')
                PATH_f=(local_maindir+'subjects/'+subjid+'_t1.nii.gz')        
            lsrecon.append('-FLAIR '+PATH_f)        
            f=f+1
        return(' '.join(lsrecon))

    ls_cmds = []
    for subjid in ls:
        cmd = 'recon-all '+i4subj(subjid)+' -s '+subjid
        ls_cmds.append(cmd)
    if not path.exists(dirres+'/pbs/usedpbs'+dt):
        mkdir(dirres+'pbs/usedpbs'+dt)
    with open(dirres+'pbs/usedpbs'+dt+'/registration.pbs','a') as f:
        for cmd in ls_cmds:
            f.write(cmd+'\n')		
            local_ls_cmds.append(cmd)
            #send_to_thread_update()
            system(cmd)


def runrecon_all(subjid):
    system('recon-all -all -s '+subjid+' -parallel')

def runbrstem(subjid):
    system('recon-all -s '+subjid+' -brainstem-structures -parallel')

def runqcache(subjid):
    system('recon-all -qcache -s '+subjid+' -parallel')

def runhip(subjid):
    system('recon-all -s '+subjid+' -hippocampal-subfields-T1 -parallel')


structure_codes = {'left_hippocampus':17,'right_hippocampus':53,
                    'left_thalamus':10,'right_thalamus':49,'left_caudate':11,'right_caudate':50,
                    'left_putamen':12,'right_putamen':51,'left_pallidum':13,'right_pallidum':52,
                    'left_amygdala':18,'right_amygdala':54,'left_accumbens':26,'right_accumbens':58,
                    'left_hippocampus_CA2':550,'right_hippocampus_CA2':500,
                    'left_hippocampus_CA1':552,'right_hippocampus_CA1':502,
                    'left_hippocampus_CA4':556,'right_hippocampus_CA4':506,
                    'left_hippocampus_fissure':555,'right_hippocampus_fissure':505,
                    'left_amygdala_subiculum':557,'right_amygdala_subiculum':507,
                    'left_amygdala_presubiculum':554,'right_amygdala_presubiculum':504,}	
def run_make_masks(subjid):
    subj_dir = dirfssubj+subjid
    if not path.isdir(subj_dir+'/masks'):
        mkdir(subj_dir+'/masks')
    mask_dir = subj_dir+'/masks/'

    for structure in structure_codes:
        aseg_mgz = subj_dir+'/mri/aseg.mgz'
        orig001_mgz = subj_dir+'/mri/orig/001.mgz'
        mask_mgz = mask_dir+structure+'.mgz'
        mask_nii = mask_dir+structure+'.nii'
        system('mri_binarize --match '+str(structure_codes[structure])+' --i '+aseg_mgz+' --o '+mask_mgz)
        system('mri_convert -rl '+orig001_mgz+' -rt nearest '+mask_mgz+' '+mask_nii)


def chk_masks(subjid):
    if path.isdir(dirfssubj+subjid+'/masks/'):
        for structure in structure_codes:
            if structure+'.nii' not in listdir(dirfssubj+subjid+'/masks/'):
                return False
                break
            else:
                return True
    else:
        return False

files_for_stats = {'mris':{'lh':'_table_lh.txt','rh':'_table_rh.txt',},
    'aparcstats':{
        'lh':{'thickness':'_aparc_stats_thick_lh.txt','meancurv':'_aparc_stats_curv_lh.txt','area':'_aparc_stats_area_lh.txt','volume':'_aparc_stats_volume_lh.txt',},
        'rh':{'thickness':'_aparc_stats_thick_rh.txt','meancurv':'_aparc_stats_curv_rh.txt','area':'_aparc_stats_area_rh.txt','volume':'_aparc_stats_volume_rh.txt',},},
    'aparcstats2009':{
        'lh':{'thickness':'_aparc2009_stats_thick_lh.txt','meancurv':'_aparc2009_stats_curv_lh.txt','area':'_aparc2009_stats_area_lh.txt','volume':'_aparc2009_stats_volume_lh.txt',},
        'rh':{'thickness':'_aparc2009_stats_thick_rh.txt','meancurv':'_aparc2009_stats_curv_rh.txt','area':'_aparc2009_stats_area_rh.txt','volume':'_aparc2009_stats_volume_rh.txt',},},
    'asegstats':'_aseg_stats.txt',
    'brstem_hip':{'brstem':'brainstemSsVolumes.v10.txt','hip_lh':'lh.hippoSfVolumes-T1.v10.txt','hip_rh':'rh.hippoSfVolumes-T1.v10.txt'}}

def stats(subjid):
    if path.isdir(dirres+'stats/'):
        dirstats=dirres+'stats/'
    else:
        mkdir(dirres+'stats')  
        dirstats=dirres+'stats/'
    
    for key in files_for_stats['mris']:
        system('mris_anatomical_stats -a '+dirfssubj+subjid+'/label/'+key+'.aparc.annot -f '+dirstats+subjid+files_for_stats['mris'][key]+' '+subjid+' '+key)
    for key in files_for_stats['aparcstats']:
        for subkey in files_for_stats['aparcstats'][key]:
            system('aparcstats2table --subjects '+subjid+' --hemi '+key+' --meas '+subkey+' --tablefile '+dirstats+subjid+files_for_stats['aparcstats'][key][subkey])
    for key in files_for_stats['aparcstats2009']:
        for subkey in files_for_stats['aparcstats2009'][key]:
            system('aparcstats2table --subjects '+subjid+' --hemi '+key+' --parc aparc.a2009s --meas '+subkey+' --tablefile '+dirstats+subjid+files_for_stats['aparcstats2009'][key][subkey])
    system('asegstats2table --subjects '+subjid+' --meas volume --tablefile '+dirstats+subjid+files_for_stats['asegstats'])
    lsmri=listdir(dirfssubj+subjid+'/mri/')
    for key in files_for_stats['brstem_hip']:
            f=files_for_stats['brstem_hip'][key]
            if any(f in i for i in lsmri):
                shutil.copy(dirfssubj+subjid+'/mri/'+f,dirstats+subjid+"_"+f)
            else:
                with open(dirstats+'logstats.log','a') as logstatslog:
                    logstatslog.write(subjid+' has no file '+f+'\n')
    #system('mri_segstats --annot '+subjid+' lh aparc --i $SUBJECTS_DIR/subjid/suf/lh.pial_lgi --sum lh.aparc.pial_lgi.stats --tablefile '+dirstats+subjid+files_for_stats['asegstats'])


def check_stats(subjid):
    files_check = {'mris':{'lh':'','rh':'',},
    'aparcstats':{
        'lh':{'thickness':'','meancurv':'','area':'','volume':'',},
        'rh':{'thickness':'','meancurv':'','area':'','volume':','},},
    'aparcstats2009':{
        'lh':{'thickness':'','meancurv':'','area':'','volume':'',},
        'rh':{'thickness':'','meancurv':'','area':'','volume':'',},},
    'asegstats':'','brstem_hip':{'brstem':'','hip_lh':'','hip_rh':''},}
    dirstats=dirres+'stats/'
    lsstats=listdir(dirstats)
    lsmiss = []
    for key in files_for_stats['brstem_hip']:
            f= files_for_stats['brstem_hip'][key]
            if subjid+"_"+f in listdir(dirstats):
                files_check['brstem_hip'][key]='y'
            else:
                files_check['brstem_hip'][key]='missing'
                lsmiss.append(subjid+"_"+f)
    for key in files_for_stats['mris']:
        if subjid+files_for_stats['mris'][key] in listdir(dirstats):
            files_check['mris'][key]='y'
        else:
            files_check['mris'][key]='n'
            lsmiss.append(subjid+files_for_stats['mris'][key])
    for key in files_for_stats['aparcstats']:
        for subkey in files_for_stats['aparcstats'][key]:
            if subjid+files_for_stats['aparcstats'][key][subkey] in listdir(dirstats):
                files_check['aparcstats'][key][subkey]='y'
            else:
                files_check['aparcstats'][key][subkey]='n'
                lsmiss.append(subjid+files_for_stats['aparcstats'][key][subkey])
    for key in files_for_stats['aparcstats2009']:
        for subkey in files_for_stats['aparcstats2009'][key]:
            if subjid+files_for_stats['aparcstats2009'][key][subkey] in listdir(dirstats):
                files_check['aparcstats2009'][key][subkey]='y'
            else:
                files_check['aparcstats2009'][key][subkey]='n'
                lsmiss.append(subjid+files_for_stats['aparcstats2009'][key][subkey])
    if subjid+files_for_stats['asegstats'] in listdir(dirstats):
        files_check['asegstats']='y'
    else:
        files_check['asegstats']='n'
        lsmiss.append(subjid+files_for_stats['asegstats'])
    if len(lsmiss)>0:
        return False
    else:
        return True

def remove_all_IsRunning():
    for subDIR in listdir(dirfssubj):
        if path.isdir(dirfssubj+subDIR+'/scripts'):
            if any('IsRunning.lh+rh' in i for i in listdir(dirfssubj+subDIR+'/scripts/')):
                remove(dirfssubj+subDIR+'/scripts/IsRunning.lh+rh')
            else:
                pass
