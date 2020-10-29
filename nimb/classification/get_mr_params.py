#!/bin/python
# 2020.08.13

from os import path, remove, system, chdir
from pathlib import Path
import logging

def verify_vox_size_values(vox_size):
    vox = True
    if type(vox_size) == list:
        if len(vox_size) == 3:
            for val in vox_size:
                if '.' not in val:
                    vox=False
                    break
        else:
            vox=False
    else:
        vox=False
    return vox


def get_MR_file_params(subjid, NIMB_tmp, file):
	tmp_f = path.join(NIMB_tmp, 'tmp_mriinfo')
	vox_size = 'none'
	chdir(Path(__file__).resolve().parent)
    try:
    	system('./mri_info '+file+' >> '+tmp_f)
    except Exception as e:
        print(e)
	if path.isfile(tmp_f):
		lines = list(open(tmp_f, 'r'))
		file_mrparams = path.join(NIMB_tmp, 'mriparams', subjid+'_mrparams')
		if not path.isfile(file_mrparams):
			open(file_mrparams,'w').close()
		with open(file_mrparams, 'a') as f:
			f.write(file+'\n')
			try:
				vox_size = [x.strip('\n') for x in lines if 'voxel sizes' in x][0].split(' ')[-3:]
				vox_size = [x.replace(',','') for x in vox_size]
				f.write('voxel \t'+str(vox_size)+'\n')
			except IndexError as e:
				print(e)
			try:
				TR_TE_TI = [x.strip('\n') for x in lines if 'TR' in x][0].split(',')
				TR = TR_TE_TI[0].split(' ')[-2]
				TE = TR_TE_TI[1].split(' ')[-2]
				TI = TR_TE_TI[2].split(' ')[-2]
				flip_angle = TR_TE_TI[3].split(' ')[-2]
				f.write('TR \t'+str(TR)+'\n')
				f.write('TE \t'+str(TE)+'\n')
				f.write('TI \t'+str(TI)+'\n')
				f.write('flip angle \t'+str(flip_angle)+'\n')
			except IndexError as e:
				print(e)
			try:
				field_strength = [x.strip('\n') for x in lines if 'FieldStrength' in x][0].split(',')[0].replace('       FieldStrength: ','')
				f.write('field strength \t'+str(field_strength)+'\n')
			except IndexError as e:
				print(e)
			try:
				matrix = [x.strip('\n') for x in lines if 'dimensions' in x][0].split(',')[0].replace('    dimensions: ','')
				f.write('matrix \t'+str(matrix)+'\n')
			except IndexError as e:
				print(e)
			try:
				fov = [x.strip('\n') for x in lines if 'fov' in x][0].split(',')[0].replace('           fov: ','')
				f.write('fov \t'+str(fov)+'\n')
			except IndexError as e:
				print(e)
		remove(tmp_f)
	return vox_size


def keep_files_similar_params(subjid, NIMB_tmp, t1_ls_f, flair_ls_f, t2_ls_f):
    grouped_by_voxsize = {}
    for file in t1_ls_f:
        # log.info(NIMB_tmp, '        reading MR data for T1 file: '+file)
        vox_size = get_MR_file_params(subjid, NIMB_tmp, file)
        if vox_size:
            if verify_vox_size_values(vox_size):
                if str(vox_size) not in grouped_by_voxsize:
                    grouped_by_voxsize[str(vox_size)] = {'t1':[file]}
                else:
                    grouped_by_voxsize[str(vox_size)]['t1'].append(file)
            try:
                vox_size_used = min(grouped_by_voxsize.keys())
            # log.info(NIMB_tmp, '        voxel size used: '+str(vox_size_used))
                t1_ls_f = grouped_by_voxsize[vox_size_used]['t1']
            except Exception as e:
                print(e)
                t1_ls_f = t1_ls_f[:1]
        else:
            t1_ls_f = t1_ls_f[:1]
            vox_size_used = ''
            # log.info(NIMB_tmp, '        voxel size not detected, the first T1 is used')
    if vox_size_used:
        if flair_ls_f != 'none':
            for file in flair_ls_f:
                # log.info(NIMB_tmp, '        reading MR data for FLAIR file: '+file)
                vox_size = get_MR_file_params(subjid, NIMB_tmp, file)
                if str(vox_size) == str(vox_size_used):
                    if 'flair' not in grouped_by_size[str(vox_size)]:
                        grouped_by_voxsize[str(vox_size)]['flair'] = [file]
                    else:
                        grouped_by_voxsize[str(vox_size)]['flair'].append(file)
                    flair_ls_f = grouped_by_voxsize[vox_size_used]['flair']
        if t2_ls_f != 'none':
            for file in t2_ls_f:
                # log.info(NIMB_tmp, '        reading MR data for T2 file: '+file)
                vox_size = get_MR_file_params(subjid, NIMB_tmp, file)
                if str(vox_size) == vox_size_used:
                    if 'flair' not in grouped_by_voxsize[str(vox_size)]:
                        if 't2' not in grouped_by_voxsize[str(vox_size)]:
                            grouped_by_voxsize[str(vox_size)]['t2'] = [file]
                        else:
                            grouped_by_voxsize[str(vox_size)]['t2'].append(file)
                        t2_ls_f = grouped_by_voxsize[vox_size_used]['t2']
    # log.info(NIMB_tmp, '        files used: '+str(t1_ls_f)+' '+str(flair_ls_f)+'_'+str(t2_ls_f))
    return t1_ls_f, flair_ls_f, t2_ls_f


def verify_MRIs_for_similarity(d_subjects, NIMB_tmp, flair_t2_add):
        # log.info(NIMB_tmp, '    '+subjid+' reading registration files')
        for subject in d_subjects:
            for session in d_subjects[subject]:
                subjid = subject+'_'+session
                t1_ls_f = d_subjects[subject][session]['anat']['t1']
                flair_ls_f = 'none'
                t2_ls_f = 'none'
                if 'flair' in d_subjects[subject][session]['anat'] and flair_t2_add == 1:
                    if d_subjects[subject][session]['anat']['flair']:
                        flair_ls_f = d_subjects[subject][session]['anat']['flair']
                if 't2' in d_subjects[subject][session]['anat'] and flair_t2_add == 1:
                    if d_subjects[subject][session]['anat']['t2'] and flair_ls_f == 'none':
                        t2_ls_f = d_subjects[subject][session]['anat']['t2']
                # log.info(NIMB_tmp, '        from db[\'REGISTRATION\']')
                t1_ls_f, flair_ls_f, t2_ls_f = keep_files_similar_params(subjid, NIMB_tmp, t1_ls_f, flair_ls_f, t2_ls_f)
                d_subjects[subject][session]['anat']['t1'] = t1_ls_f
                d_subjects[subject][session]['anat']['flair'] = flair_ls_f
                d_subjects[subject][session]['anat']['t2'] = t2_ls_f
        return d_subjects
