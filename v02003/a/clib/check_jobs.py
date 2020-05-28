# from os import system
# system('squeue -u hanganua > batch_queue')

file = 'batch_queue'

cluster = 'beluga'

import pandas as pd

if cluster == 'beluga':
    df = pd.read_csv(file, sep=' ')

    df.drop(df.iloc[:, 0:8], inplace=True, axis=1)
    df.drop(df.iloc[:, 1:3], inplace=True, axis=1)
    df.drop(df.iloc[:, 1:14], inplace=True, axis=1)

    job_ids = df.iloc[:,0].tolist()
    batch_files = df.iloc[:,1].dropna().tolist()+df.iloc[:,2].dropna().tolist()
	
    start_batch_cmd = 'sbatch '
    cacel_batch_cmd = 'scancel -i '

elif cluster == 'helios':
    df= pd.read_csv(file, sep='\t')
    
    new = df.iloc[:,0].str.split("  ", n = 5, expand = True)
    ls = list()
    for val in new.iloc[:,0]:
        ls.append(val)
    job_ids = ls[3:]
    #data["First Name"]= new[0]  
    #data["Last Name"]= new[1] 
    #data.drop(columns =["Name"], inplace = True)

    start_batch_cmd = 'msub '
    cacel_batch_cmd = 'qdel '

print(job_ids)
print(batch_files)

#for _id in job_ids:
#            print('canceling job: ',_id)
#            system(cacel_batch_cmd+_id)


# from time import sleep
#    sleep(10)
#    for file in batch_files:
#         print('starting job: ',file)
#         system(start_batch_cmd+file)
