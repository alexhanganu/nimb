#!/bin/sh
#SBATCH --account=def-hanganua
#SBATCH --mem=8G
#SBATCH --time=03:00:00
#SBATCH --output=/scratch/$USER/a_tmp/running_output_20200714.out

module load python/3.8.2
cd /home/$USER/projects/def-hanganua/a/
python crun.py
