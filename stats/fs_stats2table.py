#!/bin/python
#Alexandru Hanganu, 2020 06 13


import time
date = str(time.strftime('%Y%m%d', time.localtime()))


#Names of the final files with statistical data:
file_with_all_sheets = 'data_FreeSurfer_'+date+'.xlsx'
file_with_only_subcortical_volumes = 'data_FreeSurfer_subcortical_volumes_'+date+'.xlsx'
file_with_all_data_one_sheet = 'data_FreeSurfer_one_sheet_'+date+'.xlsx'



from os import path, listdir
try:
        import pandas as pd
except ImportError:
        print('Install pandas module. Type in the terminal: pip3 install pandas')
try:
        import numpy as np
except ImportError:
        print('Install numpy module. Type in the terminal: pip3 install numpy')
try:
        import xlsxwriter, xlrd
except ImportError:
        print('Install xlsxwriter and xlrd modules (pip3 install xlsxwriter, xlrd)')


def stats2table_oldversion(PATHstats, SUBJECTS_DIR, data_only_volumes=True):

    dataf = path.join(PATHstats,file_with_all_sheets)
    data_subcortical_volumes = path.join(PATHstats,file_with_only_subcortical_volumes)
    data_big = path.join(PATHstats,file_with_all_data_one_sheet)

    '''
    extracts the data from the data files of each subject and creates the dataf file
    '''
    #writing Headers for all sheets
    print('Writing Headers for all sheets')

    from stats.stats_definitions import (BrStem_Hip_f2rd_stats, BrStem_Hip_f2rd,
                                                              brstem_hip_header,
                                                              segmentation_parameters,
                                                              segmentations_header, parc_parameters,
                                                              parc_DK_f2rd,
                                                              parc_DK_header, parc_DS_f2rd, parc_DS_header)


    def get_ending(str):
        if str == 'wm-lh':
            ending = 'L'
        elif str == 'wm-rh':
            ending = 'R'
        elif str == 'Left-':
            ending = 'L'
        elif str == 'Right':
            ending = 'R'

        return ending

    writer=pd.ExcelWriter(dataf, engine='xlsxwriter')
    sheetnames = list()
    row=1
    print('Writing stats for subjects')

    for _SUBJECT in listdir(SUBJECTS_DIR)[:1]:
        '''Running Brainstem and Hippocampus'''
        print(_SUBJECT,'\n    Brainstem and Hippocampus running')
        for sheet in BrStem_Hip_f2rd:
            f_exists = False
            if path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'mri',BrStem_Hip_f2rd[sheet])):
                file = path.join(SUBJECTS_DIR,_SUBJECT,'mri',BrStem_Hip_f2rd[sheet])
                f_exists = True
                print('\n    file present '+BrStem_Hip_f2rd[sheet]+'\n')
            elif path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',BrStem_Hip_f2rd[sheet])):
                file = path.join(SUBJECTS_DIR,_SUBJECT,'stats',BrStem_Hip_f2rd[sheet])
                f_exists = True
            else:
                print('    ERROR '+BrStem_Hip_f2rd_stats[sheet]+' file is missing'+'\n')
            if f_exists:
                df=pd.read_table(file)
                df.loc[-1]=df.columns.values
                df.index=df.index+1
                df=df.sort_index()
                df.columns=['col']
                df['col'],df[_SUBJECT]=df['col'].str.split(' ',1).str
                df.index=df['col']
                del df['col']
                df=df.transpose()
            else:
                index_df = brstem_hip_header[sheet]
                len_df = len(index_df)
                df=pd.DataFrame(np.repeat('nan',len_df), columns=[_SUBJECT], index=index_df)
                df=df.T
            if sheet in sheetnames:
                    df.to_excel(writer,sheet_name=sheet,startcol=0, startrow=row, header=False, index=True)
            else:
                    df.rename(columns=lambda ROI: brstem_hip_header['all'][ROI], inplace=True)
                    df.to_excel(writer,sheet_name=sheet,startcol=0, startrow=0, header=True, index=True)
                    sheetnames.append(sheet)
        print('                              DONE')


        '''Running SEGMENTATIONS'''
        print('    Segmentations running')
        file_with_stats = 'aseg.stats'
        f_exists = False
        if path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)):
            file = path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)
            f_exists = True
        else:
            print('    ERROR '+file_with_stats+' file is missing\n')
        if f_exists:
            lines = list(open(file,'r'))
            volumes_general_structures = [x.split()[3].strip(',') for x in lines if 'Measure' in x]
            volumes_general_values = [x.split()[-2].strip(',') for x in lines if 'Measure' in x]
            segmentations = lines[lines.index([x for x in lines if 'ColHeaders' in x][0]):]
            seg_measurements = [segmentations[0].split()[4:]]
            for line in segmentations[1:]:
                seg_measurements.append(line.split()[2:])
            df = pd.DataFrame(seg_measurements[1:], columns=seg_measurements[0])

            for parameter in segmentation_parameters:
                sheetName = 'VolSeg'+parameter.replace('Volume_mm3','')
                df2 = pd.DataFrame()
                df2[_SUBJECT] = df[parameter]
                df2.index = df['StructName']
                df2 = df2.transpose()
                if parameter == 'Volume_mm3':
                    for ROI in volumes_general_structures:
                        df2[ROI] = volumes_general_values[volumes_general_structures.index(ROI)]
                if sheetName in sheetnames:
                    df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=row, header=False, index=True)
                else:
                    df2.rename(columns=lambda ROI: segmentations_header[ROI], inplace=True)
                    df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=0, header=True, index=True)
                    sheetnames.append(sheetName)
        print('                  DONE')



        '''Running PARCELLATIONS Desikan'''
        print('    Parcellations Desikan running')
        atlas = '_DK'
        for hemisphere in parc_DK_f2rd:
            file_with_stats = parc_DK_f2rd[hemisphere]
            f_exists = False
            if path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)):
                file = path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)
                f_exists = True
            else:
                print('    ERROR '+file_with_stats+' file is missing\n')
            if f_exists:
                lines = list(open(file,'r'))
                volumes_general_structures = [x.split()[2].strip(',')+'_'+x.split()[3].strip(',') for x in lines if 'Measure' in x and 'Cortex' in x]
                volumes_general_values = [x.split()[-2].strip(',') for x in lines if 'Measure' in x and 'Cortex' in x]
                segmentations = lines[lines.index([x for x in lines if 'ColHeaders' in x][0]):]
                seg_measurements = [segmentations[0].split()[2:]]
                for line in segmentations[1:]:
                    seg_measurements.append(line.split())
                df = pd.DataFrame(seg_measurements[1:], columns=seg_measurements[0])

                for parameter in parc_parameters:
                    sheetName = parc_parameters[parameter]+hemisphere+atlas
                    df2 = pd.DataFrame()
                    df2[_SUBJECT] = df[parameter]
                    df2.index = df['StructName']
                    df2 = df2.transpose()
                    if parameter == 'SurfArea':
                        df2['Cortex_WhiteSurfArea'] = volumes_general_values[volumes_general_structures.index('Cortex_WhiteSurfArea')]
                    elif parameter == 'ThickAvg':
                        df2['Cortex_MeanThickness'] = volumes_general_values[volumes_general_structures.index('Cortex_MeanThickness')]
                    elif parameter == 'GrayVol':
                        df2['Cortex_CortexVol'] = volumes_general_values[volumes_general_structures.index('Cortex_CortexVol')]
                    elif parameter == 'NumVert':
                        df2['Cortex_NumVert'] = volumes_general_values[volumes_general_structures.index('Cortex_NumVert')]
                    if sheetName in sheetnames:
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=row, header=False, index=True)
                    else:
                        df2.rename(columns=lambda ROI: parc_DK_header[ROI], inplace=True)
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=0, header=True, index=True)
                        sheetnames.append(sheetName)
        print('                          DONE')
		


        '''Running PARCELLATIONS Destrieux'''
        print('    Parcellations Destrieux running')
        atlas = '_DS'
        for hemisphere in parc_DS_f2rd:
            file_with_stats = parc_DS_f2rd[hemisphere]
            f_exists = False
            if path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)):
                file = path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)
                f_exists = True
            else:
                print('    ERROR '+file_with_stats+' file is missing\n')
            if f_exists:
                lines = list(open(file,'r'))
                segmentations = lines[lines.index([x for x in lines if 'ColHeaders' in x][0]):]
                seg_measurements = [segmentations[0].split()[2:]]
                for line in segmentations[1:]:
                    seg_measurements.append(line.split())
                df = pd.DataFrame(seg_measurements[1:], columns=seg_measurements[0])

                for parameter in parc_parameters:
                    sheetName = parc_parameters[parameter]+hemisphere+atlas
                    df2 = pd.DataFrame()
                    df2[_SUBJECT] = df[parameter]
                    df2.index = df['StructName']
                    df2 = df2.transpose()
                    if sheetName in sheetnames:
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=row, header=False, index=True)
                    else:
                        df2.rename(columns=lambda ROI: parc_DS_header[ROI], inplace=True)
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=0, header=True, index=True)
                        sheetnames.append(sheetName)
        print('                            DONE')
		


        '''Running PARCELLATIONS Desikan WhiteMatter'''
        print('    Parcellations WhiteMatter running')
        atlas = '_DK'
        file_with_stats = 'wmparc.stats'
        f_exists = False
        if path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)):
            file = path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)
            f_exists = True
        else:
            print('    ERROR '+file_with_stats+' file is missing\n')
        if f_exists:
                lines = list(open(file,'r'))
                segmentations = lines[lines.index([x for x in lines if 'ColHeaders' in x][0]):]
                seg_measurements = [segmentations[0].split()[4:]]
                for line in segmentations[1:]:
                    seg_measurements.append(line.split()[2:])
                df = pd.DataFrame(seg_measurements[1:], columns=seg_measurements[0])

                for parameter in segmentation_parameters:
                    sheetName = 'VolSegWM'+parameter.replace('Volume_mm3','')+atlas
                    df2 = pd.DataFrame()
                    df2[_SUBJECT] = df[parameter]
                    df2.index = df['StructName']
                    df2 = df2.transpose()

                    if sheetName in sheetnames:
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=row, header=False, index=True)
                    else:
                        df2.rename(columns=lambda ROI: parc_DK_header[ROI.replace('wm-lh-','').replace('wm-rh-','').replace('Left-','').replace('Right-','')]+get_ending(ROI[:5]), inplace=True)
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=0, header=True, index=True)
                        sheetnames.append(sheetName)
        print('                             DONE')

        row += 1
    writer.save()



    '''CREATING file with Subcortical Volumes and ONE BIG STATS FILE'''
    print('CREATING file with Subcortical Volumes')
    columns_2_remove = ['ventricle_5th','wm_hypointensities_L',
                        'wm_hypointensities_R','non_wm_hypointensities',
                        'non_wm_hypointensities_L','non_wm_hypointensities_R',
                        'eTIV', 'volBrainSegNotVent']
    
    def change_column_name(df, sheet):
        ls = df.columns.tolist()
        columns_2_drop = []
        for col in columns_2_remove:
            if col in ls:
                columns_2_drop.append(col)
                ls.remove(col)
            
        if len(columns_2_drop)>0:
            df.drop(columns=columns_2_drop, inplace=True)
        for col in ls:
            ls[ls.index(col)] = col+'_'+sheet
        df.columns = ls
        return df


    df_segmentations = pd.read_excel(dataf, sheet_name='VolSeg')
    df_final = df_segmentations['eTIV']

    df_concat = pd.read_excel(dataf, sheet_name=sheetnames[0])
    df_concat = change_column_name(df_concat, sheetnames[0])

    for sheet in sheetnames[1:5]:
        df2 = pd.read_excel(dataf, sheet_name=sheet)
        df2 = change_column_name(df2, sheet)
        frames = (df_concat, df2)
        df_concat = pd.concat(frames, axis=1, sort=True)

    frame_final = (df_concat, df_final)
    df_concat = pd.concat(frame_final,axis=1, sort=True)
	
    if data_only_volumes:
        writer = pd.ExcelWriter(data_subcortical_volumes, engine='xlsxwriter')
        df_concat.to_excel(writer, 'stats')
        writer.save()
    print('FINISHED creating file with Subcortical Volumes')


    print('CREATING One file with all statistics')

    df_concat = pd.read_excel(dataf, sheet_name=sheetnames[0])
    df_concat = change_column_name(df_concat, sheetnames[0])

    for sheet in sheetnames[1:]:
        df2 = pd.read_excel(dataf, sheet_name=sheet)
        df2 = change_column_name(df2, sheet)
        frames = (df_concat, df2)
        df_concat = pd.concat(frames, axis=1, sort=True)

    frame_final = (df_concat, df_final)
    df_concat = pd.concat(frame_final,axis=1, sort=True)
	
    writer = pd.ExcelWriter(data_big, engine='xlsxwriter')
    df_concat.to_excel(writer, 'stats')
    writer.save()
    print('FINISHED creating One file with all statistics')





def chk_if_subjects_ready(PATHstats, SUBJECTS_DIR):
    ''' this checks if all subjects have all stats files'''

    import json
    from stats.stats_definitions import (BS_Hip_Tha_stats_f, parc_DK_f2rd, parc_DS_f2rd)

    miss = dict()

    def add_to_miss(miss, _SUBJECT, sheet):
        if _SUBJECT not in miss:
            miss[_SUBJECT] = list()
        if sheet:
            miss[_SUBJECT].append(sheet)
        return miss

    subjects = sorted(listdir(SUBJECTS_DIR))
    for _SUBJECT in subjects:
        print('reading: ', _SUBJECT, '; left: ', len(subjects[subjects.index(_SUBJECT):]))
        for sheet in BS_Hip_Tha_stats_f:
            try:
                file_with_stats = [i for i in BS_Hip_Tha_stats_f[sheet] if path.exists(path.join(SUBJECTS_DIR,_SUBJECT,i))][0]
                if not file_with_stats:
                    print('missing: ', sheet)
                    miss = add_to_miss(miss, _SUBJECT, sheet)
            except Exception as e:
                print(e)
                miss = add_to_miss(miss, _SUBJECT, sheet)                
        if not path.exists(path.join(SUBJECTS_DIR,_SUBJECT, 'stats', 'aseg.stats')):
                print('missing: ', 'aseg.stats')
                miss = add_to_miss(miss, _SUBJECT, 'VolSeg')
        for hemisphere in parc_DK_f2rd:
            file_with_stats = parc_DK_f2rd[hemisphere]
            if not path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)):
                print('missing: ', file_with_stats)
                miss = add_to_miss(miss, _SUBJECT, file_with_stats)
        for hemisphere in parc_DS_f2rd:
            file_with_stats = parc_DS_f2rd[hemisphere]
            if not path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)):
                print('missing: ', file_with_stats)
                miss = add_to_miss(miss, _SUBJECT, file_with_stats)
        file_with_stats = 'wmparc.stats'
        if not path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)):
                miss = add_to_miss(miss, _SUBJECT, file_with_stats)
                print('missing: ', file_with_stats)

    if miss:
        print('ERROR: some subjects are missing the required files')
        with open(path.join(PATHstats, 'subjects_missing.json'), 'w') as j:
            json.dump(miss, j, indent=4)





# works on stats of FreeSurfer 7.1, needs to be confirmed on stats from FreeSurfer <7
def stats2table_v7(PATHstats, SUBJECTS_DIR, data_only_volumes=True):

    dataf = path.join(PATHstats,file_with_all_sheets)
    data_subcortical_volumes = path.join(PATHstats,file_with_only_subcortical_volumes)
    data_big = path.join(PATHstats,file_with_all_data_one_sheet)

    '''
    extracts the data from the data files of each subject and creates the dataf file
    '''
    #writing Headers for all sheets
    print('Writing Headers for all sheets')

    from stats.stats_definitions import (BS_Hip_Tha_stats_f, brstem_hip_header,
                                                              segmentation_parameters,
                                                              segmentations_header, parc_parameters,
                                                              parc_DK_f2rd,
                                                              parc_DK_header, parc_DS_f2rd, parc_DS_header)


    def read_BS_HIP_AMY_THA_v12_v21(file, _SUBJECT):
        content=open(file,'r').readlines()
        if 'hipposubfields' in file:
            dict1 = {i.split(' ')[-2]:i.split(' ')[-1].strip('\n') for i in content}
        else:
            dict1 = {i.split(' ')[-1].strip('\n'):i.split(' ')[-2] for i in content[1:]}
        return pd.DataFrame(dict1, index=[_SUBJECT])

    def read_BS_HIP_v10(file, _SUBJECT):
        df=pd.read_table(file)
        df.loc[-1]=df.columns.values
        df.index=df.index+1
        df=df.sort_index()
        df.columns=['col']
        df['col'],df[_SUBJECT]=df['col'].str.split(' ',1).str
        df.index=df['col']
        del df['col']
        return df.transpose()

    def get_ending(str):
        if str == 'wm-lh':
            ending = 'L'
        elif str == 'wm-rh':
            ending = 'R'
        elif str == 'Left-':
            ending = 'L'
        elif str == 'Right':
            ending = 'R'

        return ending


    writer=pd.ExcelWriter(dataf, engine='xlsxwriter')
    sheetnames = list()
    row=1
    print('Writing stats for subjects')

    for _SUBJECT in listdir(SUBJECTS_DIR):
        print(_SUBJECT)
        '''Extracting Brainstem,  Hippocampus, Amygdala, Thalamus'''
        print('    Brainstem,  Hippocampus, Amygdala, Thalamus running')
        for sheet in BS_Hip_Tha_stats_f:
            file_with_stats = [i for i in BS_Hip_Tha_stats_f[sheet] if path.exists(path.join(SUBJECTS_DIR,_SUBJECT,i))][0]
            if file_with_stats:
                if '.v12' in file_with_stats or '.v21' in file_with_stats:
                    df = read_BS_HIP_AMY_THA_v12_v21(path.join(SUBJECTS_DIR,_SUBJECT,file_with_stats),_SUBJECT)
                else:
                    df = read_BS_HIP_v10(path.join(SUBJECTS_DIR,_SUBJECT,file_with_stats),_SUBJECT)
            else:
                print('    ERROR, '+sheet+' stats file is missing\n')
                index_df = brstem_hip_header[sheet]
                df=pd.DataFrame(np.repeat('nan',len(index_df)), columns=[_SUBJECT], index=index_df)
                df=df.T
            if sheet in sheetnames:
                df.to_excel(writer,sheet_name=sheet,startcol=0, startrow=row, header=False, index=True)
            else:
                df.rename(columns=lambda ROI: brstem_hip_header['all'][ROI], inplace=True)
                df.to_excel(writer,sheet_name=sheet,startcol=0, startrow=0, header=True, index=True)
                sheetnames.append(sheet)


        '''Extracting SEGMENTATIONS'''
        print('    Segmentations ')
        sheet = 'VolSeg'
        file = 'aseg.stats'
        file_with_stats = path.join(SUBJECTS_DIR,_SUBJECT,'stats',file)
        if file_with_stats:
            lines = list(open(file_with_stats,'r'))
            dict_vol_general = {x.split()[3].strip(','):x.split()[-2].strip(',') for x in lines if 'Measure' in x}
            # volumes_general_structures = [x.split()[3].strip(',') for x in lines if 'Measure' in x]
            # volumes_general_values = [x.split()[-2].strip(',') for x in lines if 'Measure' in x]
            segmentations = lines[lines.index([x for x in lines if 'ColHeaders' in x][0]):]
            seg_measurements = [segmentations[0].split()[4:]]
            for line in segmentations[1:]:
                seg_measurements.append(line.split()[2:])
            df = pd.DataFrame(seg_measurements[1:], columns=seg_measurements[0])

            for parameter in segmentation_parameters:
                sheetName = 'VolSeg'+parameter.replace('Volume_mm3','')
                df2 = pd.DataFrame()
                df2[_SUBJECT] = df[parameter]
                df2.index = df['StructName']
                df2 = df2.transpose()
                if parameter == 'Volume_mm3':
                    for ROI in dict_vol_general:
                        df2[ROI] = dict_vol_general[ROI]
                    # for ROI in volumes_general_structures:
                    #     df2[ROI] = volumes_general_values[volumes_general_structures.index(ROI)]
                if sheetName in sheetnames:
                    df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=row, header=False, index=True)
                else:
                    df2.rename(columns=lambda ROI: segmentations_header[ROI], inplace=True)
                    df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=0, header=True, index=True)
                    sheetnames.append(sheetName)
        else:
            print('    ERROR '+file_with_stats+' is missing\n')



        '''Extracting PARCELLATIONS Desikan'''
        print('    Cortical Parcellations:\n        Desikan')
        atlas = '_DK'
        for hemisphere in parc_DK_f2rd:
            file_with_stats = parc_DK_f2rd[hemisphere]
            f_exists = False
            if path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)):
                file = path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)
                f_exists = True
            else:
                print('    ERROR '+file_with_stats+' file is missing\n')
            if f_exists:
                lines = list(open(file,'r'))
                dict_vol_general = {x.split()[2].strip(',')+'_'+x.split()[3].strip(','):x.split()[-2].strip(',') for x in lines if 'Measure' in x}
                # volumes_general_structures = [x.split()[2].strip(',')+'_'+x.split()[3].strip(',') for x in lines if 'Measure' in x and 'Cortex' in x]
                # volumes_general_values = [x.split()[-2].strip(',') for x in lines if 'Measure' in x and 'Cortex' in x]
                segmentations = lines[lines.index([x for x in lines if 'ColHeaders' in x][0]):]
                seg_measurements = [segmentations[0].split()[2:]]
                for line in segmentations[1:]:
                    seg_measurements.append(line.split())
                df = pd.DataFrame(seg_measurements[1:], columns=seg_measurements[0])

                for parameter in parc_parameters:
                    sheetName = parc_parameters[parameter]+hemisphere+atlas
                    df2 = pd.DataFrame()
                    df2[_SUBJECT] = df[parameter]
                    df2.index = df['StructName']
                    df2 = df2.transpose()
                    if parameter == 'SurfArea':
                        df2['Cortex_WhiteSurfArea'] = dict_vol_general['Cortex_WhiteSurfArea']
                        # df2['Cortex_WhiteSurfArea'] = volumes_general_values[volumes_general_structures.index('Cortex_WhiteSurfArea')]
                    elif parameter == 'ThickAvg':
                        df2['Cortex_MeanThickness'] = dict_vol_general['Cortex_MeanThickness']
                        # df2['Cortex_MeanThickness'] = volumes_general_values[volumes_general_structures.index('Cortex_MeanThickness')]
                    elif parameter == 'GrayVol':
                        if 'Cortex_CortexVol' in dict_vol_general:
                            df2['Cortex_CortexVol'] = dict_vol_general['Cortex_CortexVol']
                            # df2['Cortex_CortexVol'] = volumes_general_values[volumes_general_structures.index('Cortex_CortexVol')]
                        else:
                            df2['Cortex_CortexVol'] = 'nan'
                    elif parameter == 'NumVert':
                        df2['Cortex_NumVert'] = dict_vol_general['Cortex_NumVert']
                        # df2['Cortex_NumVert'] = volumes_general_values[volumes_general_structures.index('Cortex_NumVert')]
                    if sheetName in sheetnames:
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=row, header=False, index=True)
                    else:
                        df2.rename(columns=lambda ROI: parc_DK_header[ROI], inplace=True)
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=0, header=True, index=True)
                        sheetnames.append(sheetName)
        


        '''Extracting PARCELLATIONS Destrieux'''
        print('        Destrieux')
        atlas = '_DS'
        for hemisphere in parc_DS_f2rd:
            file_with_stats = parc_DS_f2rd[hemisphere]
            f_exists = False
            if path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)):
                file = path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)
                f_exists = True
            else:
                print('    ERROR '+file_with_stats+' file is missing\n')
            if f_exists:
                lines = list(open(file,'r'))
                segmentations = lines[lines.index([x for x in lines if 'ColHeaders' in x][0]):]
                seg_measurements = [segmentations[0].split()[2:]]
                for line in segmentations[1:]:
                    seg_measurements.append(line.split())
                df = pd.DataFrame(seg_measurements[1:], columns=seg_measurements[0])

                for parameter in parc_parameters:
                    sheetName = parc_parameters[parameter]+hemisphere+atlas
                    df2 = pd.DataFrame()
                    df2[_SUBJECT] = df[parameter]
                    df2.index = df['StructName']
                    df2 = df2.transpose()
                    if sheetName in sheetnames:
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=row, header=False, index=True)
                    else:
                        df2.rename(columns=lambda ROI: parc_DS_header[ROI], inplace=True)
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=0, header=True, index=True)
                        sheetnames.append(sheetName)
        


        '''Extracting PARCELLATIONS Desikan WhiteMatter'''
        print('        WhiteMatter')
        atlas = '_DK'
        file_with_stats = 'wmparc.stats'
        f_exists = False
        if path.isfile(path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)):
            file = path.join(SUBJECTS_DIR,_SUBJECT,'stats',file_with_stats)
            f_exists = True
        else:
            print('    ERROR '+file_with_stats+' file is missing\n')
        if f_exists:
                lines = list(open(file,'r'))
                segmentations = lines[lines.index([x for x in lines if 'ColHeaders' in x][0]):]
                seg_measurements = [segmentations[0].split()[4:]]
                for line in segmentations[1:]:
                    seg_measurements.append(line.split()[2:])
                df = pd.DataFrame(seg_measurements[1:], columns=seg_measurements[0])

                for parameter in segmentation_parameters:
                    sheetName = 'VolSegWM'+parameter.replace('Volume_mm3','')+atlas
                    df2 = pd.DataFrame()
                    df2[_SUBJECT] = df[parameter]
                    df2.index = df['StructName']
                    df2 = df2.transpose()

                    if sheetName in sheetnames:
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=row, header=False, index=True)
                    else:
                        df2.rename(columns=lambda ROI: parc_DK_header[ROI.replace('wm-lh-','').replace('wm-rh-','').replace('Left-','').replace('Right-','')]+get_ending(ROI[:5]), inplace=True)
                        df2.to_excel(writer,sheet_name=sheetName,startcol=0, startrow=0, header=True, index=True)
                        sheetnames.append(sheetName)

        row += 1
    writer.save()



    '''CREATING file with Subcortical Volumes and ONE BIG STATS FILE'''
    print('CREATING file with Subcortical Volumes')
    columns_2_remove = ['ventricle_5th','wm_hypointensities_L',
                        'wm_hypointensities_R','non_wm_hypointensities',
                        'non_wm_hypointensities_L','non_wm_hypointensities_R',
                        'eTIV', 'volBrainSegNotVent']
    
    def change_column_name(df, sheet):
        ls = df.columns.tolist()
        columns_2_drop = []
        for col in columns_2_remove:
            if col in ls:
                columns_2_drop.append(col)
                ls.remove(col)
            
        if len(columns_2_drop)>0:
            df.drop(columns=columns_2_drop, inplace=True)
        for col in ls:
            ls[ls.index(col)] = col+'_'+sheet
        df.columns = ls
        return df


    df_segmentations = pd.read_excel(dataf, sheet_name='VolSeg')
    df_final = df_segmentations['eTIV']

    df_concat = pd.read_excel(dataf, sheet_name=sheetnames[0])
    df_concat = change_column_name(df_concat, sheetnames[0])

    for sheet in sheetnames[1:5]:
        df2 = pd.read_excel(dataf, sheet_name=sheet)
        df2 = change_column_name(df2, sheet)
        frames = (df_concat, df2)
        df_concat = pd.concat(frames, axis=1, sort=True)

    frame_final = (df_concat, df_final)
    df_concat = pd.concat(frame_final,axis=1, sort=True)
    
    if data_only_volumes:
        writer = pd.ExcelWriter(data_subcortical_volumes, engine='xlsxwriter')
        df_concat.to_excel(writer, 'stats')
        writer.save()
    print('FINISHED creating file with Subcortical Volumes')


    print('CREATING One file with all statistics')

    df_concat = pd.read_excel(dataf, sheet_name=sheetnames[0])
    df_concat = change_column_name(df_concat, sheetnames[0])

    for sheet in sheetnames[1:]:
        df2 = pd.read_excel(dataf, sheet_name=sheet)
        df2 = change_column_name(df2, sheet)
        frames = (df_concat, df2)
        df_concat = pd.concat(frames, axis=1, sort=True)

    frame_final = (df_concat, df_final)
    df_concat = pd.concat(frame_final,axis=1, sort=True)
    
    writer = pd.ExcelWriter(data_big, engine='xlsxwriter')
    df_concat.to_excel(writer, 'stats')
    writer.save()
    print('FINISHED creating One file with all statistics')
