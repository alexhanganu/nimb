# Usage

## Introduction

nimb aims to perform automatic freesurfer analysis, dwi roi extraction with dipy and rsfmri roi z-values extraction with nilearn.
extract the roi-stats to a csv file
performs general statistical analysis of the file per groups.

## CLI

It works on cedar at the moment. Should work on tmux as well, but wasn't tested.
unzip on cedar in ../projects
cd nimb
python3 nimb.py

this will add all required folders.

to perform freesurfer analysis, nimb has to receive the folder of files to be analysed. The example is located in:
nimb/tmp/examples/new_subjects.json

this file is created with:
python3 nimb.py -process classify

The classifier was constructed on adni, nacc and ppmi data. It has to be adjusted on the data.
In the future we will switch to the dcm2bids app (github.com/cbedetti/dcm2bids.git)

after the new_subjects.json file is provided, do:

cd ../nimb
python3 nimb.py -process freesurfer

It will start sending all subjects to the scheduler and run the analysis.

Be sure to change:
~/nimb/local.json:
freesurfer_instal to be 1 instead of 0. This means that freesurfer is installed on cedar or, will be installed.
Also, in the local.json file - be sure to put the freesurfer license.

after the freesurfer analysis is done, you can perform freesurfer glm:
python3 nimb.py -process fs-glm

after that you should copy the glm results to your local linux or mac and can extract the images with the command:
python3 nimb.py -process fs-glm-image

if you provide a csv file with data (see nimb/tmp/examles/example_table.csv), you can perform general stats;
python3 nimb.py -process run-stats

## Output

processed subjects are located in the path provided in :
~/nimb/local.json -> NIMB_PROCESSED_FS

## Tools

MRIs
csv file with groups.

