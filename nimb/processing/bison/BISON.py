# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 12:43:32 2019
######################################################################################################################################
Copyright (c)  2019 Mahsa Dadar, Louis Collins
Developed and validated using Python 2.7.13 :: Anaconda 2.5.0 (64-bit)
Other necessary Installations: https://github.com/BIC-MNI/pyezminc, minc-toolkit-v2 

Script for Tissue Segmentation from T1-w images
This version of the pipeline has the option to perform its own preprocessing and works with .nii images.
The pipeline provides the option of using other classifiers, but is has been tested and validated with random forests 
Input arguments:
BISON.py -c <Classifier (Default: RF)> -i <Input CSV File> 
 -m <Template Mask File>  -f <Number of Folds in K-fold Cross Validation (Default=10)>
 -o <Output Path> -t <Temp Files Path> -e <Classification Mode> -n <New Data CSV File> 
 -p <Pre-trained Classifiers Path> -d  <Do Preprocessing> -l < The Number of Classes>

CSV File Column Headers: Subjects, XFMs, T1s, T2s, PDs, FLAIRs, Labels, Masks
Subjects:   Subject ID
T1s:        Path to preprocessed T1 image, coregistered with primary modality (mandatory)
T2s:        Path to preprocessed T2 image, coregistered with primary modality (if exists)
PD:         Path to preprocessed PD image, coregistered with primary modality (if exists)
FLAIR:      Path to preprocessed FLAIR image, coregistered with primary modality (if exists)
XFMs:       Nonlinear transformation from primary modality image to template
Masks:      Brain mask or mask of region of interest
Labels:     Labels (For Training, not necessary if using pre-trained classifiers)

Preprocessing Options: 
 Y:   Perform Preprocessing 

Classification Mode Options: 
 CV:   Cross Validation (On The Same Dataset) 
 TT:   Train-Test Model (Training on Input CSV Data, Segment New Data, Needs an extra CSV file)
 PT:   Using Pre-trained Classifiers  

Classifier Options:
 NB:   Naive Bayes
 LDA:  Linear Discriminant Analysis
 QDA:  Quadratic Discriminant Analysis
 LR:   Logistic Regression
 KNN:  K Nearest Neighbors 
 RF:   Random Forest 
 SVM:  Support Vector Machines 
 Tree: Decision Tree
 Bagging
 AdaBoost
#####################################################################################################################################
@author: mdadar
"""
def doPreprocessing(path_nlin_mask,path_Temp, ID_Test, Label_Files_Test , Label, T1_Files_Test , t1 , T2_Files_Test , t2 , PD_Files_Test , pd , FLAIR_Files_Test , flair ,  path_av_t1 , path_av_t2 , path_av_pd , path_av_flair):
    import os
    nlmf = 'Y'
    nuf = 'Y'
    volpolf = 'Y'
    if '.nii' in T1_Files_Test[0]: 
        fileFormat = 'nii'
    else:
        fileFormat = 'mnc'
    preprocessed_list = {}
    str_t1_proc = ''
    str_t2_proc = ''
    str_pd_proc = ''
    str_flair_proc = ''
    preprocessed_list_address=path_Temp+'Preprocessed.csv'
    print('Preprocessing Images')
    for i in range(0 , len(T1_Files_Test)):
        if (t1 != ''):
            str_File_t1 = str(T1_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
            if (fileFormat == 'nii'):
                new_command = 'nii2mnc ' + str_File_t1 + ' ' + path_Temp + str(ID_Test[i]) + '_T1.mnc'      
            else:
                new_command = 'cp ' + str_File_t1 + ' ' + path_Temp + str(ID_Test[i]) + '_T1.mnc'
            os.system(new_command)
            new_command = 'bestlinreg_s2 ' +  path_Temp + str(ID_Test[i]) + '_T1.mnc ' +  path_av_t1 + ' ' +  path_Temp + str(ID_Test[i]) + '_T1toTemplate.xfm'
            os.system(new_command)
            new_command = 'mincresample ' +  path_nlin_mask + ' -transform ' +  path_Temp + str(ID_Test[i]) + '_T1toTemplate.xfm' + ' ' +  path_Temp + str(ID_Test[i]) + '_T1_Mask.mnc -invert_transform -like ' + path_Temp + str(ID_Test[i]) + '_T1.mnc -nearest -clobber'
            os.system(new_command)
            str_t1_proc = path_Temp + str(ID_Test[i]) + '_T1.mnc'
            str_main_modality = str_t1_proc
            if (nlmf == 'Y'):
                new_command = 'mincnlm -clobber -mt 1 ' + path_Temp + str(ID_Test[i]) + '_T1.mnc ' + path_Temp + str(ID_Test[i]) + '_T1_NLM.mnc -beta 0.7 -clobber'
                os.system(new_command)
                str_t1_proc = path_Temp + str(ID_Test[i]) + '_T1_NLM.mnc'
            if (nuf == 'Y'):
                new_command = 'nu_correct ' + path_Temp + str(ID_Test[i]) + '_T1_NLM.mnc '  + path_Temp + str(ID_Test[i]) + '_T1_N3.mnc -mask '+ path_Temp + str(ID_Test[i]) + '_T1_Mask.mnc  -iter 200 -distance 50 -clobber'
                os.system(new_command)
                str_t1_proc = path_Temp + str(ID_Test[i]) + '_T1_N3.mnc'
            if (volpolf == 'Y'):
                new_command = 'volume_pol ' + path_Temp + str(ID_Test[i]) + '_T1_N3.mnc '  + path_av_t1 + ' --order 1 --noclamp --expfile ' + path_Temp + str(ID_Test[i]) + '_T1_norm --clobber'
                os.system(new_command)
                new_command = 'minccalc -expfile ' + path_Temp + str(ID_Test[i]) + '_T1_norm '  + path_Temp + str(ID_Test[i]) + '_T1_N3.mnc ' + path_Temp + str(ID_Test[i]) + '_T1_VP.mnc ' 
                os.system(new_command)
                str_t1_proc = path_Temp + str(ID_Test[i]) + '_T1_VP.mnc'
                
            new_command = 'bestlinreg_s2 ' +  str_t1_proc + ' ' +  path_av_t1 + ' ' +  path_Temp + str(ID_Test[i]) + '_T1toTemplate_pp_lin.xfm'
            os.system(new_command)
            new_command = 'mincresample ' +  str_t1_proc + ' -transform ' +  path_Temp + str(ID_Test[i]) + '_T1toTemplate_pp_lin.xfm' + ' ' +  path_Temp + str(ID_Test[i]) + '_T1_lin.mnc -like ' + path_av_t1 + ' -clobber'
            os.system(new_command)
            new_command = 'nlfit_s ' + path_Temp + str(ID_Test[i]) + '_T1_lin.mnc ' +  path_av_t1 + ' ' +  path_Temp + str(ID_Test[i]) + '_T1toTemplate_pp_nlin.xfm -level 2 -clobber'
            os.system(new_command)
            new_command = 'xfmconcat ' + path_Temp + str(ID_Test[i]) + '_T1toTemplate_pp_lin.xfm ' + path_Temp + str(ID_Test[i]) + '_T1toTemplate_pp_nlin.xfm '+ path_Temp + str(ID_Test[i]) + '_T1toTemplate_pp_both.xfm'
            os.system(new_command)

        if (t2 != ''):
            str_File_t2 = str(T2_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
            if (fileFormat == 'nii'):                
                new_command = 'nii2mnc ' + str_File_t2 + ' ' + path_Temp + str(ID_Test[i]) + '_T2.mnc'      
            else:
                new_command = 'cp ' + str_File_t2 + ' ' + path_Temp + str(ID_Test[i]) + '_T2.mnc'
            os.system(new_command)
            new_command = 'bestlinreg_s2 -lsq6 ' +  path_Temp + str(ID_Test[i]) + '_T2.mnc '  +  path_Temp + str(ID_Test[i]) + '_T1.mnc ' + ' ' +  path_Temp + str(ID_Test[i]) + '_T2toT1.xfm -mi -close'
            os.system(new_command)
            str_t2_proc = path_Temp + str(ID_Test[i]) + '_T2.mnc'
            if (nlmf == 'Y'):
                new_command = 'mincnlm -clobber -mt 1 ' + path_Temp + str(ID_Test[i]) + '_T2.mnc ' + path_Temp + str(ID_Test[i]) + '_T2_NLM.mnc -beta 0.7 -clobber'
                os.system(new_command)
                str_t2_proc = path_Temp + str(ID_Test[i]) + '_T2_NLM.mnc'
            if (nuf == 'Y'):
                new_command = 'nu_correct ' + path_Temp + str(ID_Test[i]) + '_T2_NLM.mnc '  + path_Temp + str(ID_Test[i]) + '_T2_N3.mnc -mask '+ path_Temp + str(ID_Test[i]) + '_T2_Mask.mnc  -iter 200 -distance 50 -clobber'
                os.system(new_command)
                str_t2_proc = path_Temp + str(ID_Test[i]) + '_N3.mnc'
            if (volpolf == 'Y'):
                new_command = 'volume_pol ' + path_Temp + str(ID_Test[i]) + '_T2_N3.mnc '  + path_av_t2 + ' --order 1 --noclamp --expfile ' + path_Temp + str(ID_Test[i]) + '_T2_norm --clobber'
                os.system(new_command)
                new_command = 'minccalc -expfile ' + path_Temp + str(ID_Test[i]) + '_T2_norm '  + path_Temp + str(ID_Test[i]) + '_T2_N3.mnc ' + path_Temp + str(ID_Test[i]) + '_T2_VP.mnc ' 
                os.system(new_command)
                str_t2_proc = path_Temp + str(ID_Test[i]) + '_T2_VP.mnc'                         
            
        if (pd != ''):
            str_File_pd = str(PD_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
            if (fileFormat == 'nii'):                
                new_command = 'nii2mnc ' + str_File_pd + ' ' + path_Temp + str(ID_Test[i]) + '_PD.mnc'    
            else:
                new_command = 'cp ' + str_File_pd + ' ' + path_Temp + str(ID_Test[i]) + '_PD.mnc'    
            os.system(new_command)
            new_command = 'bestlinreg_s2 -lsq6 ' +  path_Temp + str(ID_Test[i]) + '_PD.mnc '  +  path_Temp + str(ID_Test[i]) + '_T1.mnc ' + ' ' +  path_Temp + str(ID_Test[i]) + '_PDtoT1.xfm -mi -close'
            os.system(new_command)
            str_pd_proc = path_Temp + str(ID_Test[i]) + '_PD.mnc'
            if (nlmf == 'Y'):
                new_command = 'mincnlm -clobber -mt 1 ' + path_Temp + str(ID_Test[i]) + '_PD.mnc ' + path_Temp + str(ID_Test[i]) + '_PD_NLM.mnc -beta 0.7 -clobber'
                os.system(new_command)
                str_pd_proc = path_Temp + str(ID_Test[i]) + '_PD_NLM.mnc'
            if (nuf == 'Y'):
                new_command = 'nu_correct ' + path_Temp + str(ID_Test[i]) + '_PD_NLM.mnc '  + path_Temp + str(ID_Test[i]) + '_PD_N3.mnc -mask '+ path_Temp + str(ID_Test[i]) + '_PD_Mask.mnc  -iter 200 -distance 50 -clobber'
                os.system(new_command)
                str_pd_proc = path_Temp + str(ID_Test[i]) + '_PD_N3.mnc'
            if (volpolf == 'Y'):
                new_command = 'volume_pol ' + path_Temp + str(ID_Test[i]) + '_PD_N3.mnc '  + path_av_pd + ' --order 1 --noclamp --expfile ' + path_Temp + str(ID_Test[i]) + '_PD_norm --clobber'
                os.system(new_command)
                new_command = 'minccalc -expfile ' + path_Temp + str(ID_Test[i]) + '_PD_norm '  + path_Temp + str(ID_Test[i]) + '_PD_N3.mnc ' + path_Temp + str(ID_Test[i]) + '_PD_VP.mnc ' 
                os.system(new_command)
                str_pd_proc = path_Temp + str(ID_Test[i]) + '_PD_VP.mnc'
                
        if (flair != ''):
            str_File_flair = str(FLAIR_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
            if (fileFormat == 'nii'):                
                new_command = 'nii2mnc ' + str_File_flair + ' ' + path_Temp + str(ID_Test[i]) + '_FLAIR.mnc'   
            else:
                new_command = 'cp ' + str_File_flair + ' ' + path_Temp + str(ID_Test[i]) + '_FLAIR.mnc' 
            os.system(new_command)
            new_command = 'bestlinreg_s2 -lsq6 ' +  path_Temp + str(ID_Test[i]) + '_FLAIR.mnc '  +  path_Temp + str(ID_Test[i]) + '_T1.mnc ' + ' ' +  path_Temp + str(ID_Test[i]) + '_FLAIRtoT1.xfm -mi -close'
            os.system(new_command)
            str_flair_proc = path_Temp + str(ID_Test[i]) + '_FLAIR.mnc'
            if (nlmf == 'Y'):
                new_command = 'mincnlm -clobber -mt 1 ' + path_Temp + str(ID_Test[i]) + '_FLAIR.mnc ' + path_Temp + str(ID_Test[i]) + '_FLAIR_NLM.mnc -beta 0.7 -clobber'
                os.system(new_command)
                str_flair_proc = path_Temp + str(ID_Test[i]) + '_FLAIR_NLM.mnc'
            if (nuf == 'Y'):
                new_command = 'nu_correct ' + path_Temp + str(ID_Test[i]) + '_FLAIR_NLM.mnc '  + path_Temp + str(ID_Test[i]) + '_FLAIR_N3.mnc -mask '+ path_Temp + str(ID_Test[i]) + '_FLAIR_Mask.mnc  -iter 200 -distance 50 -clobber'
                os.system(new_command)
                str_flair_proc = path_Temp + str(ID_Test[i]) + '_FLAIR_N3.mnc'
            if (volpolf == 'Y'):
                new_command = 'volume_pol ' + path_Temp + str(ID_Test[i]) + '_FLAIR_N3.mnc '  + path_av_flair + ' --order 1 --noclamp --expfile ' + path_Temp + str(ID_Test[i]) + '_FLAIR_norm --clobber'
                os.system(new_command)
                new_command = 'minccalc -expfile ' + path_Temp + str(ID_Test[i]) + '_FLAIR_norm '  + path_Temp + str(ID_Test[i]) + '_FLAIR_N3.mnc ' + path_Temp + str(ID_Test[i]) + '_FLAIR_VP.mnc ' 
                os.system(new_command)
                str_flair_proc = path_Temp + str(ID_Test[i]) + '_FLAIR_VP.mnc'
        if (Label != ''):
            str_File_Label = str(Label_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
            if (fileFormat == 'nii'):   
                new_command = 'nii2mnc ' + str_File_Label + ' ' + path_Temp + str(ID_Test[i]) + '_Label.mnc' 
            else:
                new_command = 'cp ' + str_File_Label + ' ' + path_Temp + str(ID_Test[i]) + '_Label.mnc'
            os.system(new_command)
            str_File_Label = path_Temp + str(ID_Test[i]) + '_Label.mnc' 
        
        if (flair != ''):
            new_command = 'bestlinreg_s2 -lsq6 ' +  str_flair_proc + ' '  +  str_main_modality + ' ' +  path_Temp + str(ID_Test[i]) + '_FLAIRtoMain.xfm  -mi -close -clobber'
            os.system(new_command)
            new_command = 'mincresample ' +  str_flair_proc + ' -transform ' +  path_Temp + str(ID_Test[i]) + '_FLAIRtoMain.xfm' + ' ' +  path_Temp + str(ID_Test[i]) + '_FLAIR_CR.mnc -like ' + str_main_modality + ' -clobber'
            os.system(new_command)
            str_t1_proc =  path_Temp + str(ID_Test[i]) + '_T1_CR.mnc'        
                                   
        if (t2 != ''):
            new_command = 'bestlinreg_s2 -lsq6 ' +  str_t2_proc + ' '  +  str_main_modality + ' ' +  path_Temp + str(ID_Test[i]) + '_T2toMain.xfm -mi -close'
            os.system(new_command)
            new_command = 'mincresample ' +  str_t2_proc + ' -transform ' +  path_Temp + str(ID_Test[i]) + '_T2toMain.xfm' + ' ' +  path_Temp + str(ID_Test[i]) + '_T2_CR.mnc -like ' + str_main_modality + ' -clobber'
            os.system(new_command)
            str_t1_proc =  path_Temp + str(ID_Test[i]) + '_T2_CR.mnc'
        
        if (pd != ''):    
            new_command = 'bestlinreg_s2 -lsq6 ' +  str_pd_proc + ' '  +  str_main_modality + ' ' +  path_Temp + str(ID_Test[i]) + '_PDtoMain.xfm -mi -close'
            os.system(new_command)
            new_command = 'mincresample ' +  str_pd_proc + ' -transform ' +  path_Temp + str(ID_Test[i]) + '_PDtoMain.xfm' + ' ' +  path_Temp + str(ID_Test[i]) + '_PD_CR.mnc -like ' + str_main_modality + ' -clobber'
            os.system(new_command)
            str_pd_proc =  path_Temp + str(ID_Test[i]) + '_PD_CR.mnc'

        new_command = 'mincresample ' +  path_nlin_mask + ' -transform ' + path_Temp + str(ID_Test[i]) + '_T1toTemplate_pp_both.xfm' + ' ' +  path_Temp + str(ID_Test[i]) + '_Mask_nl.mnc -like ' + str_main_modality + ' -invert_transformation -nearest -clobber'
        os.system(new_command) 
        str_Mask = path_Temp + str(ID_Test[i]) + '_Mask_nl.mnc'
        nl_xfm = path_Temp + str(ID_Test[i]) + '_T1toTemplate_pp_both.xfm'
            
        print('.'),
        preprocessed_list[0,0]= 'Subjects,T1s,Masks,XFMs'
        preprocessed_list[i+1,0]= str(ID_Test[i]) + ',' + str_t1_proc + ',' + str_Mask + ',' + nl_xfm
        if (t2 != ''):
            preprocessed_list[0,0]=  preprocessed_list[0,0] + ',T2s'
            preprocessed_list[i+1,0]=  preprocessed_list[i+1,0] + ',' + str_t2_proc
        if (pd != ''):
            preprocessed_list[0,0]=  preprocessed_list[0,0] + ',PDs'
            preprocessed_list[i+1,0]=  preprocessed_list[i+1,0] + ',' + str_pd_proc
        if (flair != ''):
            preprocessed_list[0,0]=  preprocessed_list[0,0] + ',FLAIRs'
            preprocessed_list[i+1,0]=  preprocessed_list[i+1,0] + ',' + str_flair_proc
        if (Label != ''):
            preprocessed_list[0,0]=  preprocessed_list[0,0] + ',Labels'
            preprocessed_list[i+1,0]=  preprocessed_list[i+1,0] + ',' + str_File_Label
            
    outfile = open( preprocessed_list_address, 'w' )
    for key, value in sorted( preprocessed_list.items() ):
        outfile.write(  str(value) + '\n' )
    outfile = open( preprocessed_list_address, 'w' )
    for key, value in sorted( preprocessed_list.items() ):
        outfile.write(  str(value) + '\n' )
    return [preprocessed_list_address]
###########################################################################################################################################################################
def Calculate_Tissue_Histogram(Files_Train , Masks_Train , Label_Files_Train , image_range , n_labels):
    import minc
    import numpy as np
    PDF_Label = np.zeros(shape = (image_range , n_labels)).astype(float)
    print('Calculating Histograms of Tissues: .'),
    for i in range(0 , len(Files_Train)):
        print('.'),
        str_File = str(Files_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
        str_Mask = str(Masks_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
        str_Label = str(Label_Files_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
        manual_segmentation = minc.Image(str_Label).data
        image_vol = minc.Image(str_File).data
        brain_mask = minc.Image(str_Mask).data
        image_vol = np.round(image_vol)
        for nl in range(0 , n_labels):
            for j in range(1 , image_range):
                PDF_Label[j,nl] = PDF_Label[j,nl] + np.sum((image_vol * (manual_segmentation==(nl+1)) * brain_mask) == j)
    
        PDF_Label[:,nl] = PDF_Label[:,nl] / np.sum(PDF_Label[:,nl])
    print(' Done.')
    return PDF_Label
###########################################################################################################################################################################
def load_csv(csv_file):
    import csv
    data = {}
    with open(csv_file , 'r') as f:
        for r in csv.DictReader(f):
            for k in r.iterkeys():
                try:
                    data[k].append(r[k])
                except KeyError:
                    data[k] = [r[k]]
    return data
###########################################################################################################################################################################
def get_Train_Test(Indices_G , K , IDs):
    import numpy as np
    i_train = 0
    i_test = 0
    ID_Train = np.empty(shape = (np.sum(Indices_G != K) , 1) , dtype = list , order = 'C')
    ID_Test = np.empty(shape = (np.sum(Indices_G == K) , 1) , dtype = list , order = 'C')        
    for i in range(0 , len(Indices_G)):
        if (Indices_G[i] != K):
            ID_Train[i_train] = IDs[i]
            i_train = i_train + 1
        if (Indices_G[i] == K):
            ID_Test[i_test] = IDs[i]
            i_test = i_test + 1
    return [ID_Train , ID_Test]
###########################################################################################################################################################################
def get_addressess(TestList):
    InputListInfo_Test = load_csv(TestList)    
    ID_Test = InputListInfo_Test['Subjects']
    if 'XFMs' in InputListInfo_Test:    
        XFM_Files_Test = InputListInfo_Test['XFMs']
        xfmf = 'exists'
    else:
        xfmf = ''
        XFM_Files_Test = ''
    if 'Masks' in InputListInfo_Test:    
        Mask_Files_Test = InputListInfo_Test['Masks']
        maskf = 'exists'
    else:
        maskf = ''
        Mask_Files_Test = ''
    if 'T1s' in InputListInfo_Test:    
        T1_Files_Test = InputListInfo_Test['T1s']
        t1 = 'exists'
    else:
        t1 =''
        T1_Files_Test = ''
    if 'T2s' in InputListInfo_Test:    
        T2_Files_Test = InputListInfo_Test['T2s']
        t2 = 'exists'
    else:
        t2 =''
        T2_Files_Test = ''
    if 'PDs' in InputListInfo_Test:    
        PD_Files_Test = InputListInfo_Test['PDs']
        pd = 'exists'
    else:
        pd = ''
        PD_Files_Test = ''
    if 'FLAIRs' in InputListInfo_Test:    
        FLAIR_Files_Test = InputListInfo_Test['FLAIRs']
        flair = 'exists'
    else:
        flair = ''
        FLAIR_Files_Test = ''
    if 'Labels' in InputListInfo_Test:    
        Label_Files_Test = InputListInfo_Test['Labels']
        Label = 'exists'
    else:
        Label = ''
        Label_Files_Test = ''
    if 'cls' in InputListInfo_Test:    
        cls_Files_Test = InputListInfo_Test['cls']
        clsf = 'exists'
    else:
        clsf = ''
        cls_Files_Test = ''
    return [ID_Test, XFM_Files_Test, xfmf, Mask_Files_Test, maskf, T1_Files_Test, t1, T2_Files_Test, t2, PD_Files_Test, pd, FLAIR_Files_Test, flair, Label_Files_Test, Label,cls_Files_Test, clsf]
###########################################################################################################################################################################
import sys,getopt
def main(argv):   
    import minc
    import numpy as np
    import os
    #from joblib import Parallel
    #import multiprocessing
# Default Values    
    n_folds=10
    image_range = 256
    subject = 0
    Classifier='RF'    
    InputList=''
    doPreprocessingf='N'
    path_trained_classifiers=''
    InputList=''
    TestList=''
    path_Temp=''
    path_nlin_files = ''
    ClassificationMode = ''
    path_output = ''
    TestList = ''
    n_labels = 0

    try:
        opts, args = getopt.getopt(argv,"hc:i:m:o:t:e:n:f:p:d:l:",["cfile=","ifile=","mfile=","ofile=","tfile=","efile=","nfile=","ffile=","pfile=","dfile=","lfile="])
    except getopt.GetoptError:
        print 'BISON.py -c <Classifier (Default: LDA)> -i <Input CSV File> \n -m <Template Mask File> -f <Number of Folds in K-fold Cross Validation (Default=10)>'
        print' -o <Output Path> -t <Temp Files Path> -e <Classification Mode> -n <New Data CSV File> -p <Pre-trained Classifiers Path> -d  <Do Preprocessing> -l < The Number of Classes> \n'
        print 'CSV File Column Headers: Subjects, XFMs, T1s, T2s, PDs, FLAIRs, Labels, cls, Masks\n'
        print 'Preprocessing Options: \n Y:   Perform Preprocessing \n '
        print 'Classification Mode Options: \n CV:   Cross Validation (On The Same Dataset) \n TT:   Train-Test Model (Training on Input CSV Data, Segment New Data, Needs an extra CSV file)\n'
        print ' PT:   Using Pre-trained Classifiers \n'                  
        print 'Classifier Options:\n NB:   Naive Bayes\n LDA:  Linear Discriminant Analysis\n QDA:  Quadratic Discriminant Analysis\n LR:   Logistic Regression'
        print ' KNN:  K Nearest Neighbors \n RF:   Random Forest \n SVM:  Support Vector Machines \n Tree: Decision Tree\n Bagging\n AdaBoost'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'Label_Segmentation_Pipeline.py -c <Classifier (Default: LDA)> -i <Input CSV File> \n -m <Template Mask File>  -f <Number of Folds in K-fold Cross Validation (Default=10)>'
            print' -o <Output Path> -t <Temp Files Path> -e <Classification Mode> -n <New Data CSV File> -p <Pre-trained Classifiers Path> -d  <Do Preprocessing> -l < The Number of Classes> \n'            
            print 'CSV File Column Headers: Subjects, XFMs, T1s, T2s, PDs, FLAIRs, Labels, cls, Masks\n'            
            print 'Preprocessing Options: \n Y:   Perform Preprocessing \n'            
            print 'Classification Mode Options: \n CV:   Cross Validation (On The Same Dataset) \n TT:   Train-Test Model (Training on Input CSV Data, Segment New Data, Needs an extra CSV file)'
            print ' PT:   Using Pre-trained Classifiers \n'            
            print 'Classifier Options:\n NB:   Naive Bayes\n LDA:  Linear Discriminant Analysis\n QDA:  Quadratic Discriminant Analysis\n LR:   Logistic Regression'
            print ' KNN:  K Nearest Neighbors \n RF:   Random Forest \n SVM:  Support Vector Machines \n Tree: Decision Tree\n Bagging\n AdaBoost'
            sys.exit()
        elif opt in ("-c", "--cfile"):
            Classifier = arg
        elif opt in ("-i", "--ifile"):
            InputList = arg
        elif opt in ("-m", "--mfile"):
            path_nlin_files = arg
        elif opt in ("-o", "--ofile"):
            path_output = arg
        elif opt in ("-t", "--tfile"):
            path_Temp = arg+str(np.random.randint(1000000, size=1)).replace("[",'').replace("]",'').replace(" ",'').replace(" ",'')+'_'
        elif opt in ("-e", "--efile"):
            ClassificationMode = arg
        elif opt in ("-n", "--nfile"):
            TestList = arg
        elif opt in ("-f", "--ffile"):
            n_folds = int(arg)
        elif opt in ("-p", "--pfile"):
            path_trained_classifiers = arg
        elif opt in ("-d", "--dfile"):
            doPreprocessingf = arg    
        elif opt in ("-l", "--lfile"):
            n_labels = int(arg)

    print 'The Selected Input CSV File is ', InputList
    print 'The Selected Classifier is ', Classifier
    print 'The Classification Mode is ', ClassificationMode
    print 'The Selected Template Mask is ', path_nlin_files
    print 'The Selected Output Path is ', path_output    
    print 'The Assigned Temp Files Path is ', path_Temp
    if (doPreprocessingf == 'Y'):
        print 'Preprocessing:  Yes'
    
    if (Classifier == 'NB'):
        # Naive Bayes
        from sklearn.naive_bayes import GaussianNB
        clf = GaussianNB()        
    elif (Classifier == 'LDA'):      
        # Linear Discriminant Analysis
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
        clf = LinearDiscriminantAnalysis(solver = "svd" , store_covariance = True)  
    elif (Classifier == 'QDA'):
        # Quadratic Discriminant Analysis
        from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
        clf = QuadraticDiscriminantAnalysis(priors = None, reg_param = 0.0 , store_covariances = False , tol = 0.0001)
    elif (Classifier == 'LR'):
        # Logistic Regression
        from sklearn.linear_model import LogisticRegression
        clf = LogisticRegression(C = 200 , penalty = 'l2', tol = 0.01)
    elif (Classifier == 'KNN'):
        # K Nearest Neighbors
        from sklearn.neighbors import KNeighborsClassifier
        clf = KNeighborsClassifier(n_neighbors = 10)
    elif (Classifier == 'Bagging'):
        # Bagging
        from sklearn.ensemble import BaggingClassifier
        from sklearn.neighbors import KNeighborsClassifier
        clf = BaggingClassifier(KNeighborsClassifier() , max_samples = 0.5 , max_features = 0.5)        
    elif (Classifier == 'AdaBoost'):
        # AdaBoost
        from sklearn.ensemble import AdaBoostClassifier
        clf = AdaBoostClassifier(n_estimators = 100)        
    elif (Classifier == 'RF'):
        # Random Forest
        from sklearn.ensemble import RandomForestClassifier
        clf = RandomForestClassifier(n_estimators = 100)
    elif (Classifier == 'SVM'):
        # Support Vector Machines
        from sklearn import svm
        clf = svm.LinearSVC()
    elif (Classifier == 'Tree'):
        # Decision Tree
        from sklearn import tree
        clf = tree.DecisionTreeClassifier()   
    else:
        print 'The Selected Classifier Was Not Recongnized'
        sys.exit()
    if (InputList != ''):
    	[IDs, XFM_Files, xfmf, Mask_Files, maskf, T1_Files, t1, T2_Files, t2, PD_Files, pd, FLAIR_Files, flair, Label_Files, Label,cls_Files, clsf] = get_addressess(InputList)
####################### Preprocessing ####################################################################################################################################
    if (path_nlin_files == ''):
	print 'No path has been defined for the template files'
	sys.exit()
    if (path_nlin_files != ''):
    	path_nlin_mask = path_nlin_files+'Mask.mnc'
    	path_av_t1 = path_nlin_files + 'Av_T1.mnc'
    	path_av_t2 = path_nlin_files + 'Av_T2.mnc'
    	path_av_pd = path_nlin_files + 'Av_PD.mnc'
    	path_av_flair = path_nlin_files + 'Av_FLAIR.mnc'

    if ((path_trained_classifiers == '') & (ClassificationMode == 'PT')):
	print 'No path has been defined for the pretrained classifiers'
	sys.exit()
    if (path_trained_classifiers != ''):    
        path_av_t1 = path_trained_classifiers + 'Av_T1.mnc'
        path_av_t2 = path_trained_classifiers + 'Av_T2.mnc'
        path_av_pd = path_trained_classifiers + 'Av_PD.mnc'
        path_av_flair = path_trained_classifiers + 'Av_FLAIR.mnc'   

    if (n_labels == 0):
	print 'The number of classes has not been determined'
	sys.exit()

    if (ClassificationMode == ''):
	print 'The classification mode has not been determined'
	sys.exit()
###########################################################################################################################################################################
    if ClassificationMode == 'CV':
        if (doPreprocessingf == 'Y'):
            preprocessed_list_address=doPreprocessing(path_nlin_mask,path_Temp, IDs, Label_Files , Label, T1_Files , t1 , T2_Files , t2 , PD_Files , pd , FLAIR_Files, flair ,  path_av_t1 , path_av_t2 , path_av_pd , path_av_flair)
            [IDs, XFM_Files, xfmf, Mask_Files, maskf, T1_Files, t1, T2_Files, t2, PD_Files, pd, FLAIR_Files, flair, Label_Files, Label,cls_Files, clsf] = get_addressess(path_Temp+'Preprocessed.csv')

        if Label == '':    
            print 'No Labels to Train on'
            sys.exit()
        Indices_G = np.random.permutation(len(IDs)) * n_folds / len(IDs)
        Kappa = np.zeros(shape = (len(IDs) , n_labels))
        ID_Subject = np.empty(shape = (len(IDs),1) , dtype = list, order = 'C')       

        for K in range(0 , n_folds):
            [ID_Train , ID_Test] = get_Train_Test(Indices_G , K , IDs)    
            [XFM_Files_Train , XFM_Files_Test] = get_Train_Test(Indices_G , K , XFM_Files)    
            [Label_Files_Train , Label_Files_Test] = get_Train_Test(Indices_G , K , Label_Files)    
            [Mask_Files_Train , Mask_Files_Test] = get_Train_Test(Indices_G , K , Mask_Files)    
            
            n_features=n_labels           
            if (t1 != ''):        
                [T1_Files_Train , T1_Files_Test] = get_Train_Test(Indices_G , K , T1_Files)    
                T1_PDF_Label = Calculate_Tissue_Histogram(T1_Files_Train , Mask_Files_Train , Label_Files_Train , image_range , n_labels)
                n_features = n_features + n_labels + 2
                
            if (t2 != ''):
                [T2_Files_Train , T2_Files_Test] = get_Train_Test(Indices_G , K , T2_Files)    
                T2_PDF_Label = Calculate_Tissue_Histogram(T2_Files_Train , Mask_Files_Train , Label_Files_Train , image_range , n_labels)
                n_features = n_features + n_labels + 2
                
            if (pd != ''):
                [PD_Files_Train , PD_Files_Test] = get_Train_Test(Indices_G , K , PD_Files)    
                PD_PDF_Label = Calculate_Tissue_Histogram(PD_Files_Train , Mask_Files_Train , Label_Files_Train , image_range , n_labels)
                n_features = n_features + n_labels + 2
                
            if (flair != ''):
                [FLAIR_Files_Train , FLAIR_Files_Test] = get_Train_Test(Indices_G , K , FLAIR_Files)    
                FLAIR_PDF_Label = Calculate_Tissue_Histogram(FLAIR_Files_Train , Mask_Files_Train , Label_Files_Train , image_range , n_labels)
                n_features = n_features + n_labels + 2
            
            path_sp = path_nlin_files + 'SP_'
            
            X_All = np.empty(shape = (0 , n_features) , dtype = float , order = 'C')
            Y_All = np.empty(shape = (0 , ) , dtype = float , order = 'C')
            
            for i in range(0 , len(ID_Train)):
                str_Train = str(ID_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                print('Extracting The Features: Subject: ID = ' + str_Train)
                
                str_Mask = str(Mask_Files_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                Mask = minc.Image(str_Mask).data
                ind_WM = (Mask > 0)
                N=int(np.sum(Mask))
                Label = str(Label_Files_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'') 
                WMT = minc.Image(Label).data
                
                nl_xfm = str(XFM_Files_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                spatial_priors = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                for nl in range(0 , n_labels):
                    new_command = 'mincresample ' + path_sp + str(nl+1) + '.mnc -like  ' + Label + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_sp.mnc -clobber'
                    os.system(new_command)
                    spatial_prior = minc.Image(path_Temp + str(K) + '_tmp_sp.mnc').data
                    spatial_priors[0:N,nl] = spatial_prior[ind_WM]
                
                if (t1 != ''):
                    str_T1 = str(T1_Files_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                    T1 = minc.Image(str_T1).data
                    new_command = 'mincresample ' + path_av_t1 + ' -like ' + Label + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_t1.mnc -clobber'
                    os.system(new_command)
                    av_T1 = minc.Image(path_Temp + str(K) + '_tmp_t1.mnc').data
                    T1[T1 < 1] = 1
                    T1[T1 > (image_range - 1)] = (image_range - 1)
                    T1_Label_probability = np.empty(shape = (N, n_labels) , dtype = float , order = 'C')
                    for nl in range(0 , n_labels):
                        T1_Label_probability[:,nl] = T1_PDF_Label[np.round(T1[ind_WM]).astype(int),nl]
                    X_t1 = np.zeros(shape = (N , 2))
                    X_t1[0 : N , 0] = T1[ind_WM]
                    X_t1[0 : N , 1] = av_T1[ind_WM]
                    X_t1 = np.concatenate((X_t1 , T1_Label_probability) , axis = 1)
    
                if (t2 != ''):                
                    str_T2 = str(T2_Files_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                    T2 = minc.Image(str_T2).data
                    new_command = 'mincresample ' + path_av_t2 + ' -like ' + Label + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_t2.mnc -clobber'
                    os.system(new_command)
                    av_T2 = minc.Image(path_Temp + str(K) + '_tmp_t2.mnc').data
                    T2[T2 < 1] = 1
                    T2[T2 > (image_range - 1)] = (image_range - 1)
                    T2_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                    for nl in range(0 , n_labels):
                        T2_Label_probability[:,nl] = T2_PDF_Label[np.round(T2[ind_WM]).astype(int),nl]
                    if (t1 == ''):
                        X_t2 = np.zeros(shape = (N , 2))
                        X_t2[0 : N , 0] = T2[ind_WM]
                        X_t2[0 : N , 1] = av_T2[ind_WM]
                    if (t1 != ''):
                        X_t2 = np.zeros(shape = (N , 3))
                        X_t2[0 : N , 0] = T2[ind_WM]
                        X_t2[0 : N , 1] = av_T2[ind_WM]    
                        X_t2[0 : N , 2] = T2[ind_WM] / T1[ind_WM]   
                    X_t2 = np.concatenate((X_t2 , T2_Label_probability) , axis = 1)
                    
                if (pd != ''):
                    str_PD = str(PD_Files_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                    PD = minc.Image(str_PD).data
                    new_command = 'mincresample ' + path_av_pd + ' -like ' + Label + ' -transform ' + nl_xfm + ' -invert_transform '+ path_Temp + str(K) + '_tmp_pd.mnc -clobber'
                    os.system(new_command)
                    av_PD = minc.Image(path_Temp + str(K) + '_tmp_pd.mnc').data
                    PD[PD < 1] = 1
                    PD[PD > (image_range - 1)] = (image_range - 1)
                    PD_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                    for nl in range(0 , n_labels):
                        PD_Label_probability[:,nl] = PD_PDF_Label[np.round(PD[ind_WM]).astype(int),nl]
                    if (t1 == ''):
                        X_pd = np.zeros(shape = (N , 2))
                        X_pd[0 : N , 0] = PD[ind_WM]
                        X_pd[0 : N , 1] = av_PD[ind_WM]
                    if (t1 != ''):
                        X_pd = np.zeros(shape = (N , 3))
                        X_pd[0 : N , 0] = PD[ind_WM]
                        X_pd[0 : N , 1] = av_PD[ind_WM]                        
                        X_pd[0 : N , 2] = PD[ind_WM] / T1[ind_WM]      
                    X_pd = np.concatenate((X_pd , PD_Label_probability ) , axis = 1)                
                    
                if (flair != ''):
                    str_FLAIR = str(FLAIR_Files_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                    FLAIR = minc.Image(str_FLAIR).data
                    new_command = 'mincresample ' + path_av_flair + ' -like ' + Label + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_flair.mnc -clobber'
                    os.system(new_command)
                    av_FLAIR = minc.Image(path_Temp + str(K) + '_tmp_flair.mnc').data
                    FLAIR[FLAIR < 1] = 1
                    FLAIR[FLAIR > (image_range - 1)] = (image_range - 1)
                    FLAIR_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                    for nl in range(0 , n_labels):
                        FLAIR_Label_probability[:,nl] = FLAIR_PDF_Label[np.round(FLAIR[ind_WM]).astype(int),nl]
                    if (t1 == ''):
                        X_flair = np.zeros(shape = (N , 3))
                        X_flair[0 : N , 0] = FLAIR[ind_WM]
                        X_flair[0 : N , 1] = av_FLAIR[ind_WM]
                    if (t1 != ''):
                        X_flair = np.zeros(shape = (N , 4))
                        X_flair[0 : N , 0] = FLAIR[ind_WM]
                        X_flair[0 : N , 1] = av_FLAIR[ind_WM]
                        X_flair[0 : N , 2] = FLAIR[ind_WM] / T1[ind_WM]       
                    X_flair = np.concatenate((X_flair , FLAIR_Label_probability ) , axis = 1)
                
                else:
                    X = np.zeros(shape = (N , 0))
                    X = np.concatenate((X , spatial_priors) , axis = 1)  
                if (t1 != ''):
                    X = np.concatenate((X , X_t1) , axis = 1)
                if (t2 != ''):
                    X = np.concatenate((X , X_t2) , axis = 1)
                if (pd != ''):
                    X = np.concatenate((X , X_pd) , axis = 1)
                if (flair != ''):
                    X = np.concatenate((X , X_flair) , axis = 1)
                
                X_All = np.concatenate((X_All , X) , axis = 0)
                Y = np.zeros(shape = (N , ))
                Y[0 : N , ] = (WMT[ind_WM])    
                Y_All = np.concatenate((Y_All , Y) , axis = 0)
            
            # Training the Classifier
            clf = clf.fit(X_All , Y_All)
    
            for i in range(0 , len(ID_Test)):
                str_Test = str(ID_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                print('Segmenting Volumes: Subject: ID = ' + str_Test)
                Label = str(Label_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                WMT = minc.Image(Label).data                  
                str_Mask = str(Mask_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                Mask = minc.Image(str_Mask).data
                ind_WM = (Mask > 0)
                N=int(np.sum(Mask))
                nl_xfm = str(XFM_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                spatial_priors = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                for nl in range(0 , n_labels):
                    new_command = 'mincresample ' + path_sp + str(nl+1) + '.mnc -like  ' + Label + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_sp.mnc -clobber'
                    os.system(new_command)
                    spatial_prior = minc.Image(path_Temp + str(K) + '_tmp_sp.mnc').data
                    spatial_priors[0:N,nl] = spatial_prior[ind_WM]                
                               
                if (t1 != ''):
                    str_T1 = str(T1_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                    T1 = minc.Image(str_T1).data
                    new_command = 'mincresample ' + path_av_t1 + ' -like ' + Label + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_t1.mnc -clobber'
                    os.system(new_command)
                    av_T1 = minc.Image(path_Temp + str(K) + '_tmp_t1.mnc').data
                    T1[T1 < 1] = 1
                    T1[T1 > (image_range - 1)] = (image_range - 1)
                    T1_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                    for nl in range(0 , n_labels):
                        T1_Label_probability[:,nl] = T1_PDF_Label[np.round(T1[ind_WM]).astype(int),nl]
                    N = len(T1_Label_probability)
                    X_t1 = np.zeros(shape = (N , 2))
                    X_t1[0 : N , 0] = T1[ind_WM]
                    X_t1[0 : N , 1] = av_T1[ind_WM]
                    X_t1 = np.concatenate((X_t1 , T1_Label_probability) , axis = 1)
    
                if (t2 != ''):                
                    str_T2 = str(T2_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                    T2 = minc.Image(str_T2).data
                    new_command = 'mincresample ' + path_av_t2 + ' -like ' + Label + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_t2.mnc -clobber'
                    os.system(new_command)
                    av_T2 = minc.Image(path_Temp + str(K) + '_tmp_t2.mnc').data
                    T2[T2 < 1] = 1
                    T2[T2 > (image_range - 1)] = (image_range - 1)
                    T2_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                    for nl in range(0 , n_labels):
                        T2_Label_probability[:,nl] = T2_PDF_Label[np.round(T2[ind_WM]).astype(int),nl]
                    N = len(T2_Label_probability)
                    if (t1 == ''):
                        X_t2 = np.zeros(shape = (N , 2))
                        X_t2[0 : N , 0] = T2[ind_WM]
                        X_t2[0 : N , 1] = av_T2[ind_WM]
                    if (t1 != ''):
                        X_t2 = np.zeros(shape = (N , 3))
                        X_t2[0 : N , 0] = T2[ind_WM]
                        X_t2[0 : N , 1] = av_T2[ind_WM]    
                        X_t2[0 : N , 2] = T2[ind_WM] / T1[ind_WM]  
                    X_t2 = np.concatenate((X_t2 , T2_Label_probability) , axis = 1)
                    
                if (pd != ''):
                    str_PD = str(PD_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                    PD = minc.Image(str_PD).data
                    new_command = 'mincresample ' + path_av_pd + ' -like ' + Label + ' -transform ' + nl_xfm + ' -invert_transform '+ path_Temp + str(K) + '_tmp_pd.mnc -clobber'
                    os.system(new_command)
                    av_PD = minc.Image(path_Temp + str(K) + '_tmp_pd.mnc').data
                    PD[PD < 1] = 1
                    PD[PD > (image_range - 1)] = (image_range - 1)
                    PD_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                    for nl in range(0 , n_labels):
                        PD_Label_probability[:,nl] = PD_PDF_Label[np.round(PD[ind_WM]).astype(int),nl]
                    N = len(PD_Label_probability)
                    if (t1 == ''):
                        X_pd = np.zeros(shape = (N , 2))
                        X_pd[0 : N , 0] = PD[ind_WM]
                        X_pd[0 : N , 1] = av_PD[ind_WM]
                    if (t1 != ''):
                        X_pd = np.zeros(shape = (N , 3))
                        X_pd[0 : N , 0] = PD[ind_WM]
                        X_pd[0 : N , 1] = av_PD[ind_WM]                        
                        X_pd[0 : N , 2] = PD[ind_WM] / T1[ind_WM]
                    X_pd = np.concatenate((X_pd , PD_Label_probability ) , axis = 1)                
                    
                if (flair != ''):
                    str_FLAIR = str(FLAIR_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                    FLAIR = minc.Image(str_FLAIR).data
                    new_command = 'mincresample ' + path_av_flair + ' -like ' + Label + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_flair.mnc -clobber'
                    os.system(new_command)
                    av_FLAIR = minc.Image(path_Temp + str(K) + '_tmp_flair.mnc').data
                    FLAIR[FLAIR < 1] = 1
                    FLAIR[FLAIR > (image_range - 1)] = (image_range - 1)
                    FLAIR_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                    for nl in range(0 , n_labels):
                        FLAIR_Label_probability[:,nl] = FLAIR_PDF_Label[np.round(FLAIR[ind_WM]).astype(int),nl]
                    N = len(FLAIR_Label_probability)
                    if (t1 == ''):
                        X_flair = np.zeros(shape = (N , 3))
                        X_flair[0 : N , 0] = FLAIR[ind_WM]
                        X_flair[0 : N , 1] = av_FLAIR[ind_WM]
                    if (t1 != ''):
                        X_flair = np.zeros(shape = (N , 4))
                        X_flair[0 : N , 0] = FLAIR[ind_WM]
                        X_flair[0 : N , 1] = av_FLAIR[ind_WM]
                        X_flair[0 : N , 2] = FLAIR[ind_WM] / T1[ind_WM]
                    X_flair = np.concatenate((X_flair , FLAIR_Label_probability ) , axis = 1)
                
                else:
                    X = np.zeros(shape = (N , 0))
                    X = np.concatenate((X , spatial_priors) , axis = 1)    
                if (t1 != ''):
                    X = np.concatenate((X , X_t1) , axis = 1)
                if (t2 != ''):
                    X = np.concatenate((X , X_t2) , axis = 1)
                if (pd != ''):
                    X = np.concatenate((X , X_pd) , axis = 1)
                if (flair != ''):
                    X = np.concatenate((X , X_flair) , axis = 1)
                        
                Y = np.zeros(shape = (N , ))
                Y[0 : N] = WMT[ind_WM]
                Binary_Output = clf.predict(X)
                for nl in range(0 , n_labels):
                    Kappa[subject,nl] = 2 * np.sum((Y==(nl+1)) * (Binary_Output==(nl+1))) / (np.sum(Y==(nl+1)) + np.sum(Binary_Output==(nl+1)))
                    ID_Subject[subject] = ID_Test[i]
                if (np.sum(Y) + np.sum(Binary_Output)) == 0:
                    Kappa[subject] = 1
                print Kappa[subject]
                subject = subject + 1
                        
                WMT_auto = np.zeros(shape = (len(Mask) , len(Mask[0,:]) , len(Mask[0 , 0 , :])))
                WMT_auto[ind_WM] = Binary_Output[0 : N]
                out = minc.Image(data = WMT_auto)
                out.save(name = path_output + Classifier + '_' + str_Test + '_Label.mnc', imitate = str_Mask)
        
        print 'Cross Validation Successfully Completed. \nKappa Values:\n'        
        print Kappa
        print 'Indices'
        print Indices_G 
        print('Mean Kappa: ' + str(np.mean(Kappa)) + ' - STD Kappa: ' + str(np.std(Kappa)))  
###########################################################################################################################################################################    
    if ClassificationMode == 'TT':          
        K=0
        Indices_G=np.ones(shape = (len(IDs) , 1))
        ID_Train = IDs
        XFM_Files_Train = XFM_Files    
        Label_Files_Train = Label_Files   
        Mask_Files_Train = Mask_Files  
        if (t1 != ''):
            T1_Files_Train = T1_Files
        if (t2 != ''):        
            T2_Files_Train = T2_Files
        if (pd != ''):
            PD_Files_Train = PD_Files
        if (flair != ''):
            FLAIR_Files_Train = FLAIR_Files
        if (doPreprocessingf == 'Y'):
            preprocessed_list_address=doPreprocessing(path_nlin_mask,path_Temp, IDs, Label_Files , Label, T1_Files , t1 , T2_Files , t2 , PD_Files , pd , FLAIR_Files, flair ,  path_av_t1 , path_av_t2 , path_av_pd , path_av_flair)
            [IDs, XFM_Files, xfmf, Mask_Files, maskf, T1_Files, t1, T2_Files, t2, PD_Files, pd, FLAIR_Files, flair, Label_Files, Label,cls_Files, clsf] = get_addressess(path_Temp+'Preprocessed.csv')

        [ID_Test, XFM_Files_Test, xfmf, Mask_Files_Test, maskf, T1_Files_Test, t1, T2_Files_Test, t2, PD_Files_Test, pd, FLAIR_Files_Test, flair, Label_Files_Test, Label,cls_Files_Test, clsf] = get_addressess(TestList)

        n_features=n_labels           
        if (t1 != ''):        
            [T1_Files_Train , tmp] = get_Train_Test(Indices_G , K , T1_Files)    
            T1_PDF_Label = Calculate_Tissue_Histogram(T1_Files_Train , Mask_Files_Train , Label_Files_Train , image_range , n_labels)
            n_features = n_features + n_labels + 2
                
        if (t2 != ''):
            [T2_Files_Train , tmp] = get_Train_Test(Indices_G , K , T2_Files)    
            T2_PDF_Label = Calculate_Tissue_Histogram(T2_Files_Train , Mask_Files_Train , Label_Files_Train , image_range , n_labels)
            n_features = n_features + n_labels + 2
                
        if (pd != ''):
            [PD_Files_Train , tmp] = get_Train_Test(Indices_G , K , PD_Files)    
            PD_PDF_Label = Calculate_Tissue_Histogram(PD_Files_Train , Mask_Files_Train , Label_Files_Train , image_range , n_labels)
            n_features = n_features + n_labels + 2
                
        if (flair != ''):
            [FLAIR_Files_Train , tmp] = get_Train_Test(Indices_G , K , FLAIR_Files)    
            FLAIR_PDF_Label = Calculate_Tissue_Histogram(FLAIR_Files_Train , Mask_Files_Train , Label_Files_Train , image_range , n_labels)
            n_features = n_features + n_labels + 2            
                       
        path_sp = path_nlin_files + 'SP_'
            
        X_All = np.empty(shape = (0 , n_features ) , dtype = float , order = 'C')
        Y_All = np.empty(shape = (0 , ) , dtype = float , order = 'C')
    
        for i in range(0 , len(ID_Train)):
            str_Train = str(ID_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
            print('Extracting The Features: Subject: ID = ' + str_Train)
                
            str_Mask = str(Mask_Files_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
            Mask = minc.Image(str_Mask).data
            ind_WM = (Mask > 0)
            N=int(np.sum(Mask))
            Label = str(Label_Files_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'') 
            WMT = minc.Image(Label).data
                
            nl_xfm = str(XFM_Files_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
            spatial_priors = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
            for nl in range(0 , n_labels):
                new_command = 'mincresample ' + path_sp + str(nl+1) + '.mnc -like  ' + Label + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_sp.mnc -clobber'
                os.system(new_command)
                spatial_prior = minc.Image(path_Temp + str(K) + '_tmp_sp.mnc').data
                spatial_priors[0:N,nl] = spatial_prior[ind_WM]
                
            if (t1 != ''):
                str_T1 = str(T1_Files_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                T1 = minc.Image(str_T1).data
                new_command = 'mincresample ' + path_av_t1 + ' -like ' + Label + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_t1.mnc -clobber'
                os.system(new_command)
                av_T1 = minc.Image(path_Temp + str(K) + '_tmp_t1.mnc').data
                T1[T1 < 1] = 1
                T1[T1 > (image_range - 1)] = (image_range - 1)
                T1_Label_probability = np.empty(shape = (N, n_labels) , dtype = float , order = 'C')
                for nl in range(0 , n_labels):
                    T1_Label_probability[:,nl] = T1_PDF_Label[np.round(T1[ind_WM]).astype(int),nl]
                X_t1 = np.zeros(shape = (N , 2))
                X_t1[0 : N , 0] = T1[ind_WM]
                X_t1[0 : N , 1] = av_T1[ind_WM]
                X_t1 = np.concatenate((X_t1 , T1_Label_probability) , axis = 1)
    
            if (t2 != ''):                
                str_T2 = str(T2_Files_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                T2 = minc.Image(str_T2).data
                new_command = 'mincresample ' + path_av_t2 + ' -like ' + Label + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_t2.mnc -clobber'
                os.system(new_command)
                av_T2 = minc.Image(path_Temp + str(K) + '_tmp_t2.mnc').data
                T2[T2 < 1] = 1
                T2[T2 > (image_range - 1)] = (image_range - 1)
                T2_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                for nl in range(0 , n_labels):
                    T2_Label_probability[:,nl] = T2_PDF_Label[np.round(T2[ind_WM]).astype(int),nl]
                if (t1 == ''):
                    X_t2 = np.zeros(shape = (N , 2))
                    X_t2[0 : N , 0] = T2[ind_WM]
                    X_t2[0 : N , 1] = av_T2[ind_WM]
                if (t1 != ''):
                    X_t2 = np.zeros(shape = (N , 3))
                    X_t2[0 : N , 0] = T2[ind_WM]
                    X_t2[0 : N , 1] = av_T2[ind_WM]    
                    X_t2[0 : N , 2] = T2[ind_WM] / T1[ind_WM]
                        
                X_t2 = np.concatenate((X_t2 , T2_Label_probability) , axis = 1)
                    
            if (pd != ''):
                str_PD = str(PD_Files_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                PD = minc.Image(str_PD).data
                new_command = 'mincresample ' + path_av_pd + ' -like ' + Label + ' -transform ' + nl_xfm + ' -invert_transform '+ path_Temp + str(K) + '_tmp_pd.mnc -clobber'
                os.system(new_command)
                av_PD = minc.Image(path_Temp + str(K) + '_tmp_pd.mnc').data
                PD[PD < 1] = 1
                PD[PD > (image_range - 1)] = (image_range - 1)
                PD_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                for nl in range(0 , n_labels):
                    PD_Label_probability[:,nl] = PD_PDF_Label[np.round(PD[ind_WM]).astype(int),nl]
                if (t1 == ''):
                    X_pd = np.zeros(shape = (N , 2))
                    X_pd[0 : N , 0] = PD[ind_WM]
                    X_pd[0 : N , 1] = av_PD[ind_WM]
                if (t1 != ''):
                    X_pd = np.zeros(shape = (N , 3))
                    X_pd[0 : N , 0] = PD[ind_WM]
                    X_pd[0 : N , 1] = av_PD[ind_WM]                        
                    X_pd[0 : N , 2] = PD[ind_WM] / T1[ind_WM]
                        
                X_pd = np.concatenate((X_pd , PD_Label_probability ) , axis = 1)                
                    
            if (flair != ''):
                str_FLAIR = str(FLAIR_Files_Train[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                FLAIR = minc.Image(str_FLAIR).data
                new_command = 'mincresample ' + path_av_flair + ' -like ' + Label + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_flair.mnc -clobber'
                os.system(new_command)
                av_FLAIR = minc.Image(path_Temp + str(K) + '_tmp_flair.mnc').data
                FLAIR[FLAIR < 1] = 1
                FLAIR[FLAIR > (image_range - 1)] = (image_range - 1)
                FLAIR_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                for nl in range(0 , n_labels):
                    FLAIR_Label_probability[:,nl] = FLAIR_PDF_Label[np.round(FLAIR[ind_WM]).astype(int),nl]
                if (t1 == ''):
                    X_flair = np.zeros(shape = (N , 3))
                    X_flair[0 : N , 0] = FLAIR[ind_WM]
                    X_flair[0 : N , 1] = av_FLAIR[ind_WM]
                if (t1 != ''):
                    X_flair = np.zeros(shape = (N , 4))
                    X_flair[0 : N , 0] = FLAIR[ind_WM]
                    X_flair[0 : N , 1] = av_FLAIR[ind_WM]
                    X_flair[0 : N , 2] = FLAIR[ind_WM] / T1[ind_WM]
                        
                X_flair = np.concatenate((X_flair , FLAIR_Label_probability ) , axis = 1)
                
            else:
                X = np.zeros(shape = (N , 0))
                X = np.concatenate((X , spatial_priors) , axis = 1)  
            if (t1 != ''):
                X = np.concatenate((X , X_t1) , axis = 1)
            if (t2 != ''):
                X = np.concatenate((X , X_t2) , axis = 1)
            if (pd != ''):
                X = np.concatenate((X , X_pd) , axis = 1)
            if (flair != ''):
                X = np.concatenate((X , X_flair) , axis = 1)
                
            X_All = np.concatenate((X_All , X) , axis = 0)
            Y = np.zeros(shape = (N , ))
            Y[0 : N , ] = (WMT[ind_WM])    
            Y_All = np.concatenate((Y_All , Y) , axis = 0)
            
        # Training the Classifier
        clf = clf.fit(X_All , Y_All)

        saveFlag=0
        if saveFlag == 1:
            from sklearn.externals import joblib
            path_trained_classifiers='/data/ipl/ipl12/Mahsa/Neuromorphometrics/Trained_Classifiers/'
            path_save_classifier=path_trained_classifiers+Classifier+'_CLS'+clsf+'_T1'+t1+'_T2'+t2+'_PD'+pd+'_FLAIR'+flair+'.pkl'    
            joblib.dump(clf,path_save_classifier)
            if (t1 != ''):
                joblib.dump(T1_PDF_Label,path_trained_classifiers+'T1_Label.pkl')
            if (t2 != ''):
                joblib.dump(T2_PDF_Label,path_trained_classifiers+'T2_Label.pkl')
            if (pd != ''):
                joblib.dump(PD_PDF_Label,path_trained_classifiers+'PD_Label.pkl')
            if (flair != ''):
                joblib.dump(FLAIR_PDF_Label,path_trained_classifiers+'FLAIR_Label.pkl')
            sys.exit()
            
        for i in range(0 , len(ID_Test)):
            str_Test = str(ID_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
            print('Segmenting Volumes: Subject: ID = ' + str_Test)
            str_Mask = str(Mask_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'') .replace(" ",'')
            Mask = minc.Image(str_Mask).data
            ind_WM = (Mask > 0)
            nl_xfm = str(XFM_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
            N=int(np.sum(Mask))
              
            if (t1 != ''):
		
                str_T1 = str(T1_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                spatial_priors = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                for nl in range(0 , n_labels):
                    new_command = 'mincresample ' + path_sp + str(nl+1) + '.mnc -like  ' + str_T1 + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_sp.mnc -clobber'
                    os.system(new_command)
                    spatial_prior = minc.Image(path_Temp + str(K) + '_tmp_sp.mnc').data
                    spatial_priors[0:N,nl] = spatial_prior[ind_WM]
                
                T1 = minc.Image(str_T1).data
                new_command = 'mincresample ' + path_av_t1 + ' -like ' + str_T1 + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_t1.mnc -clobber'
                os.system(new_command)
                av_T1 = minc.Image(path_Temp + str(K) + '_tmp_t1.mnc').data
                T1[T1 < 1] = 1
                T1[T1 > (image_range - 1)] = (image_range - 1)
                T1_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                for nl in range(0 , n_labels):
                    T1_Label_probability[:,nl] = T1_PDF_Label[np.round(T1[ind_WM]).astype(int),nl]
                N = len(T1_Label_probability)
                X_t1 = np.zeros(shape = (N , 2))
                X_t1[0 : N , 0] = T1[ind_WM]
                X_t1[0 : N , 1] = av_T1[ind_WM]
                X_t1 = np.concatenate((X_t1 , T1_Label_probability) , axis = 1)
    
            if (t2 != ''):                
                str_T2 = str(T2_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                T2 = minc.Image(str_T2).data
                new_command = 'mincresample ' + path_av_t2 + ' -like ' + str_T2 + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_t2.mnc -clobber'
                os.system(new_command)
                av_T2 = minc.Image(path_Temp + str(K) + '_tmp_t2.mnc').data
                T2[T2 < 1] = 1
                T2[T2 > (image_range - 1)] = (image_range - 1)
                T2_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                for nl in range(0 , n_labels):
                    T2_Label_probability[:,nl] = T2_PDF_Label[np.round(T2[ind_WM]).astype(int),nl]
                N = len(T2_Label_probability)
                if (t1 == ''):
                    X_t2 = np.zeros(shape = (N , 2))
                    X_t2[0 : N , 0] = T2[ind_WM]
                    X_t2[0 : N , 1] = av_T2[ind_WM]
                if (t1 != ''):
                    X_t2 = np.zeros(shape = (N , 3))
                    X_t2[0 : N , 0] = T2[ind_WM]
                    X_t2[0 : N , 1] = av_T2[ind_WM]    
                    X_t2[0 : N , 2] = T2[ind_WM] / T1[ind_WM]                 
                X_t2 = np.concatenate((X_t2 , T2_Label_probability) , axis = 1)
                    
            if (pd != ''):
                str_PD = str(PD_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                PD = minc.Image(str_PD).data
                new_command = 'mincresample ' + path_av_pd + ' -like ' + str_PD + ' -transform ' + nl_xfm + ' -invert_transform '+ path_Temp + str(K) + '_tmp_pd.mnc -clobber'
                os.system(new_command)
                av_PD = minc.Image(path_Temp + str(K) + '_tmp_pd.mnc').data
                PD[PD < 1] = 1
                PD[PD > (image_range - 1)] = (image_range - 1)
                PD_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                for nl in range(0 , n_labels):
                    PD_Label_probability[:,nl] = PD_PDF_Label[np.round(PD[ind_WM]).astype(int),nl]
                N = len(PD_Label_probability)
                if (t1 == ''):
                    X_pd = np.zeros(shape = (N , 2))
                    X_pd[0 : N , 0] = PD[ind_WM]
                    X_pd[0 : N , 1] = av_PD[ind_WM]
                if (t1 != ''):
                    X_pd = np.zeros(shape = (N , 3))
                    X_pd[0 : N , 0] = PD[ind_WM]
                    X_pd[0 : N , 1] = av_PD[ind_WM]                        
                    X_pd[0 : N , 2] = PD[ind_WM] / T1[ind_WM]  
                X_pd = np.concatenate((X_pd , PD_Label_probability ) , axis = 1)                
                    
            if (flair != ''):
                str_FLAIR = str(FLAIR_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                FLAIR = minc.Image(str_FLAIR).data
                new_command = 'mincresample ' + path_av_flair + ' -like ' + str_FLAIR + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_flair.mnc -clobber'
                os.system(new_command)
                av_FLAIR = minc.Image(path_Temp + str(K) + '_tmp_flair.mnc').data
                FLAIR[FLAIR < 1] = 1
                FLAIR[FLAIR > (image_range - 1)] = (image_range - 1)
                FLAIR_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                for nl in range(0 , n_labels):
                    FLAIR_Label_probability[:,nl] = FLAIR_PDF_Label[np.round(FLAIR[ind_WM]).astype(int),nl]
                N = len(FLAIR_Label_probability)
                if (t1 == ''):
                    X_flair = np.zeros(shape = (N , 3))
                    X_flair[0 : N , 0] = FLAIR[ind_WM]
                    X_flair[0 : N , 1] = av_FLAIR[ind_WM]
                if (t1 != ''):
                    X_flair = np.zeros(shape = (N , 4))
                    X_flair[0 : N , 0] = FLAIR[ind_WM]
                    X_flair[0 : N , 1] = av_FLAIR[ind_WM]
                    X_flair[0 : N , 2] = FLAIR[ind_WM] / T1[ind_WM]     
                X_flair = np.concatenate((X_flair , FLAIR_Label_probability ) , axis = 1)
                
            else:
                X = np.zeros(shape = (N , 0))
                X = np.concatenate((X , spatial_priors) , axis = 1)  
            if (t1 != ''):
                X = np.concatenate((X , X_t1) , axis = 1)
            if (t2 != ''):
                X = np.concatenate((X , X_t2) , axis = 1)
            if (pd != ''):
                X = np.concatenate((X , X_pd) , axis = 1)
            if (flair != ''):
                X = np.concatenate((X , X_flair) , axis = 1)                 
   
            Y = np.zeros(shape = (N , ))
            Binary_Output = clf.predict(X)       
            Prob_Output=clf.predict_proba(X)            
            #### Saving results #########################################################################################################################            
            WMT_auto = np.zeros(shape = (len(Mask) , len(Mask[0 , :]) , len(Mask[0 , 0 , :])))
            WMT_auto[ind_WM] = Binary_Output[0 : N]
            out = minc.Image(data = WMT_auto)
            str_Labelo= path_output + Classifier + '_' + str_Test
            out.save(name = str_Labelo + '_Label.mnc', imitate = str_Mask)
            
            Prob_auto = np.zeros(shape = (len(Mask) , len(Mask[0 , :]) , len(Mask[0 , 0 , :])))
            Prob_auto[ind_WM] = Prob_Output[0 : N,1]
            out = minc.Image(data = Prob_auto)
            out.save(name = str_Labelo + '_P.mnc', imitate = str_Mask)
            
            if (t1 != ''):            
                new_command = 'minc_qc.pl ' + str_T1 + ' --mask ' + str_Labelo + '_Label.mnc ' + str_Labelo + '_Label.jpg --big --clobber --spectral-mask  --image-range 0 200 --mask-range 0 ' + str(n_labels)
                os.system(new_command)
            if (t2 != ''): 
                new_command = 'minc_qc.pl ' + str_T2  +' '+ str_Labelo + '_T2.jpg --big --clobber  --image-range 0 200 --mask-range 0 ' + str(n_labels)
                os.system(new_command)
            if (pd != ''): 
                new_command = 'minc_qc.pl ' + str_PD +' '+ str_Labelo + '_PD.jpg --big --clobber  --image-range 0 200 --mask-range 0 ' + str(n_labels)
                os.system(new_command)
            if (flair != ''): 
                new_command = 'minc_qc.pl ' + str_FLAIR+' '+ str_Labelo + '_FLAIR.jpg --big --clobber  --image-range 0 200 --mask-range 0 ' + str(n_labels)
                os.system(new_command)
###########################################################################################################################################################################    
    #path_trained_classifiers='/data/ipl/ipl12/Mahsa/Neuromorphometrics/Trained_Classifiers/'
    path_sp=path_trained_classifiers+'SP_'
    path_av_t1=path_trained_classifiers+'Av_T1.mnc'
    path_av_t2=path_trained_classifiers+'Av_T2.mnc'
    path_av_pd=path_trained_classifiers+'Av_PD.mnc'
    path_av_flair=path_trained_classifiers+'Av_FLAIR.mnc'
    if ClassificationMode == 'PT':       
        from sklearn.externals import joblib            
        
        [ID_Test, XFM_Files_Test, xfmf, Mask_Files_Test, maskf, T1_Files_Test, t1, T2_Files_Test, t2, PD_Files_Test, pd, FLAIR_Files_Test, flair, Label_Files_Test, Label,cls_Files_Test, clsf] = get_addressess(TestList)            
	path_saved_classifier=path_trained_classifiers+Classifier+'_CLS'+clsf+'_T1'+t1+'_T2'+t2+'_PD'+pd+'_FLAIR'+flair+'.pkl'
############## Preprocessing ####################################################################################################################################
        if (doPreprocessingf == 'Y'):
            preprocessed_list_address=doPreprocessing(path_nlin_mask,path_Temp, ID_Test, Label_Files_Test , Label, T1_Files_Test , t1 , T2_Files_Test , t2 , PD_Files_Test , pd , FLAIR_Files_Test , flair ,  path_av_t1 , path_av_t2 , path_av_pd , path_av_flair)
            [ID_Test, XFM_Files_Test, xfmf, Mask_Files_Test, maskf, T1_Files_Test, t1, T2_Files_Test, t2, PD_Files_Test, pd, FLAIR_Files_Test, flair, Label_Files_Test, Label,cls_Files_Test, clsf] = get_addressess(path_Temp+'Preprocessed.csv')
########## Loading Trained Classifier ##########################################################################################################################            
        clf=joblib.load(path_saved_classifier)
        K=0
        if (t1 != ''):
            T1_PDF_Label=joblib.load(path_trained_classifiers+'T1_Label.pkl')
        if (t2 != ''):
            T2_PDF_Label=joblib.load(path_trained_classifiers+'T2_Label.pkl')
        if (pd != ''):
            PD_PDF_Label=joblib.load(path_trained_classifiers+'PD_Label.pkl')
        if (flair != ''):
            FLAIR_PDF_Label=joblib.load(path_trained_classifiers+'FLAIR_Label.pkl')
        for i in range(0 , len(ID_Test)):
            str_Test = str(ID_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
            print('Segmenting Volumes: Subject: ID = ' + str_Test)
            str_Mask = str(Mask_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'') .replace(" ",'')
            Mask = minc.Image(str_Mask).data
            ind_WM = (Mask > 0)
            nl_xfm = str(XFM_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
            N=int(np.sum(Mask))
               
                
            if (t1 != ''):
                str_T1 = str(T1_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                spatial_priors = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                for nl in range(0 , n_labels):
                    new_command = 'mincresample ' + path_sp + str(nl+1) + '.mnc -like  ' + str_T1 + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_sp.mnc -clobber'
                                  
                    os.system(new_command)
                    spatial_prior = minc.Image(path_Temp + str(K) + '_tmp_sp.mnc').data
                    spatial_priors[0:N,nl] = spatial_prior[ind_WM]
                
                
                T1 = minc.Image(str_T1).data
                new_command = 'mincresample ' + path_av_t1 + ' -like ' + str_T1 + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_t1.mnc -clobber'
                os.system(new_command)
                av_T1 = minc.Image(path_Temp + str(K) + '_tmp_t1.mnc').data
                T1[T1 < 1] = 1
                T1[T1 > (image_range - 1)] = (image_range - 1)
                T1_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                for nl in range(0 , n_labels):
                    T1_Label_probability[:,nl] = T1_PDF_Label[np.round(T1[ind_WM]).astype(int),nl]
                N = len(T1_Label_probability)
                X_t1 = np.zeros(shape = (N , 2))
                X_t1[0 : N , 0] = T1[ind_WM]
                X_t1[0 : N , 1] = av_T1[ind_WM]
                X_t1 = np.concatenate((X_t1 , T1_Label_probability) , axis = 1)
    
            if (t2 != ''):                
                str_T2 = str(T2_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                T2 = minc.Image(str_T2).data
                new_command = 'mincresample ' + path_av_t2 + ' -like ' + str_T2 + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_t2.mnc -clobber'
                os.system(new_command)
                av_T2 = minc.Image(path_Temp + str(K) + '_tmp_t2.mnc').data
                T2[T2 < 1] = 1
                T2[T2 > (image_range - 1)] = (image_range - 1)
                T2_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                for nl in range(0 , n_labels):
                    T2_Label_probability[:,nl] = T2_PDF_Label[np.round(T2[ind_WM]).astype(int),nl]
                N = len(T2_Label_probability)
                if (t1 == ''):
                    X_t2 = np.zeros(shape = (N , 2))
                    X_t2[0 : N , 0] = T2[ind_WM]
                    X_t2[0 : N , 1] = av_T2[ind_WM]
                if (t1 != ''):
                    X_t2 = np.zeros(shape = (N , 3))
                    X_t2[0 : N , 0] = T2[ind_WM]
                    X_t2[0 : N , 1] = av_T2[ind_WM]    
                    X_t2[0 : N , 2] = T2[ind_WM] / T1[ind_WM] 
                X_t2 = np.concatenate((X_t2 , T2_Label_probability) , axis = 1)
                    
            if (pd != ''):
                str_PD = str(PD_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                PD = minc.Image(str_PD).data
                new_command = 'mincresample ' + path_av_pd + ' -like ' + str_PD + ' -transform ' + nl_xfm + ' -invert_transform '+ path_Temp + str(K) + '_tmp_pd.mnc -clobber'
                os.system(new_command)
                av_PD = minc.Image(path_Temp + str(K) + '_tmp_pd.mnc').data
                PD[PD < 1] = 1
                PD[PD > (image_range - 1)] = (image_range - 1)
                PD_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                for nl in range(0 , n_labels):
                    PD_Label_probability[:,nl] = PD_PDF_Label[np.round(PD[ind_WM]).astype(int),nl]
                N = len(PD_Label_probability)
                if (t1 == ''):
                    X_pd = np.zeros(shape = (N , 2))
                    X_pd[0 : N , 0] = PD[ind_WM]
                    X_pd[0 : N , 1] = av_PD[ind_WM]
                if (t1 != ''):
                    X_pd = np.zeros(shape = (N , 3))
                    X_pd[0 : N , 0] = PD[ind_WM]
                    X_pd[0 : N , 1] = av_PD[ind_WM]                        
                    X_pd[0 : N , 2] = PD[ind_WM] / T1[ind_WM]    
                X_pd = np.concatenate((X_pd , PD_Label_probability ) , axis = 1)                
                    
            if (flair != ''):
                str_FLAIR = str(FLAIR_Files_Test[i]).replace("[",'').replace("]",'').replace("'",'').replace(" ",'')
                FLAIR = minc.Image(str_FLAIR).data
                new_command = 'mincresample ' + path_av_flair + ' -like ' + str_FLAIR + ' -transform ' + nl_xfm + ' -invert_transform ' + path_Temp + str(K) + '_tmp_flair.mnc -clobber'
                os.system(new_command)
                av_FLAIR = minc.Image(path_Temp + str(K) + '_tmp_flair.mnc').data
                FLAIR[FLAIR < 1] = 1
                FLAIR[FLAIR > (image_range - 1)] = (image_range - 1)
                FLAIR_Label_probability = np.empty(shape = (N , n_labels) , dtype = float , order = 'C')
                for nl in range(0 , n_labels):
                    FLAIR_Label_probability[:,nl] = FLAIR_PDF_Label[np.round(FLAIR[ind_WM]).astype(int),nl]
                N = len(FLAIR_Label_probability)
                if (t1 == ''):
                    X_flair = np.zeros(shape = (N , 3))
                    X_flair[0 : N , 0] = FLAIR[ind_WM]
                    X_flair[0 : N , 1] = av_FLAIR[ind_WM]
                if (t1 != ''):
                    X_flair = np.zeros(shape = (N , 4))
                    X_flair[0 : N , 0] = FLAIR[ind_WM]
                    X_flair[0 : N , 1] = av_FLAIR[ind_WM]
                    X_flair[0 : N , 2] = FLAIR[ind_WM] / T1[ind_WM]  
                X_flair = np.concatenate((X_flair , FLAIR_Label_probability ) , axis = 1)
                
            else:
                X = np.zeros(shape = (N , 0))
                X = np.concatenate((X , spatial_priors) , axis = 1)    
            if (t1 != ''):
                X = np.concatenate((X , X_t1) , axis = 1)
            if (t2 != ''):
                X = np.concatenate((X , X_t2) , axis = 1)
            if (pd != ''):
                X = np.concatenate((X , X_pd) , axis = 1)
            if (flair != ''):
                X = np.concatenate((X , X_flair) , axis = 1)      
                X = np.concatenate((X,X_flair) , axis = 1)
    
            Y = np.zeros(shape = (N , ))
            Binary_Output = clf.predict(X)       
            #### Saving results #########################################################################################################################            
            WMT_auto = np.zeros(shape = (len(Mask) , len(Mask[0 , :]) , len(Mask[0 , 0 , :])))
            WMT_auto[ind_WM] = Binary_Output[0 : N]
            out = minc.Image(data = WMT_auto)
            str_Labelo= path_output + Classifier + '_' + str_Test
            out.save(name = str_Labelo + '_Label.mnc', imitate = str_Mask)
            
            new_command= 'mnc2nii ' + str_Labelo + '_Label.mnc ' + str_Labelo + '_Label.nii'
            os.system(new_command)
            
            if (t1 != ''):            
                new_command = 'minc_qc.pl ' + str_T1 + ' --mask ' + str_Labelo + '_Label.mnc ' + str_Labelo + '_Label.jpg --big --clobber --spectral-mask  --image-range 0 200 --mask-range 0 ' + str(n_labels)
                os.system(new_command)
            if (t2 != ''): 
                new_command = 'minc_qc.pl ' + str_T2  +' '+ str_Labelo + '_T2.jpg --big --clobber  --image-range 0 200 --mask-range 0 ' + str(n_labels)
                os.system(new_command)
            if (pd != ''): 
                new_command = 'minc_qc.pl ' + str_PD +' '+ str_Labelo + '_PD.jpg --big --clobber  --image-range 0 200 --mask-range 0 ' + str(n_labels)
                os.system(new_command)
            if (flair != ''): 
                new_command = 'minc_qc.pl ' + str_FLAIR+' '+ str_Labelo + '_FLAIR.jpg --big --clobber  --image-range 0 200 --mask-range 0 ' + str(n_labels)
                os.system(new_command)

    print 'Segmentation Successfully Completed. '
if __name__ == "__main__":
   main(sys.argv[1:])   

