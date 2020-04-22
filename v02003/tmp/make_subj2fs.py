from os import path, listdir, getcwd, getenv

path_home = getenv('HOME')+'/projects/def-hanganua/'

print(path_home)
SUBJECTS_RAW = path_home+'subjects/'
NIMB_DIR = path_home+'a/'

ls_subjects = list()
for folder in listdir(SUBJECTS_RAW):
    subjid = folder.replace('_t1','').replace('_flair','').replace('_t2','')
    if subjid not in ls_subjects:
        ls_subjects.append(subjid)

with open(NIMB_DIR+'subj2fs','w') as f:
    for subjid in sorted(ls_subjects):
        f.write(subjid+'\n')


