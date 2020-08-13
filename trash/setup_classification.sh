#!/usr/bin/env bash
echo -e "\e[1;31m clear db and status.log in scratch \e[0m"
mv -v /scratch/hiver85/a_tmp/db /scratch/hiver85/a_tmp/db_bk
mv -v /scratch/hiver85/a_tmp/status.log /scratch/hiver85/a_tmp/status_bk.log
module load python/3.7.4
echo -e "\e[1;31m Create json \e[0m"
python get_MRIs_ppmi_v2.py
#verify if json exist
if [ -e new_subjects.json ];then
	echo -e "\e[1;31m new_subjects.json ok \e[0m"
	echo -e "\e[1;31m start pipeline \e[0m"
    python crun.py
else
    echo "new_subjects.json doesn't exist"
fi
echo -e "\e[1;31m finish pipeline \e[0m";