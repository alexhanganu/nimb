clusters = database._get_Table_Data('Clusters','all')
cname = [*clusters.keys()][0]
    project_folder = clusters[cname]['HOME']
    a_folder = clusters[cname]['App_DIR']
    subjects_folder = clusters[cname]['Subjects_raw_DIR']
    # the json path is getting from mri path,
    mri_path = database._get_Table_Data('Projects',Project)[Project]['mri_dir']
    print(mri_path)
    print("subject json: " + mri_path)
    interface_cluster.copy_subjects_to_cluster(mri_path,subjects_folder, a_folder)
    
    
    var.py
    
    for remote_path in (nimb_dir, dir_new_subjects, SUBJECTS_DIR, processed_SUBJECTS_DIR, nimb_scratch_dir):
    	if not path.isdir(remote_path):
    		makedirs(remote_path)
            
            


MainFolder -- not for now, use to be local folder store the results, local

file = MainFolder+'logs/psftpcpdb_from_cluster.scr' => no need

'HOME': '/home/hvt/projects/def-hanganua/',

App_DIR == nimb dir              ==> ''a'' folder

Subjects_raw_DIR ==> local or remote, local now



Processed_SUBJECTS_DIR ==> copy from this

check status: 


get a list of subjects, get the list of old subjects
search in local process folder/define by the user
it is the MainFolder --> make st about it -- change to process_fs_version
if have FS on local it is Processed_SUBJECTS_DIR

# def cpfromcluster(): ==> check the FS status working