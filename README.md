NIMB: NeuroImaging My Brain
NIMB is a comprehensive, automated Python pipeline designed for structural, functional, and diffusion MRI analysis. It streamlines the entire neuroimaging workflow, from data classification and distribution to local or remote servers, to initiating processing with leading software packages like FreeSurfer, Nilearn, and Dipy, and finally extracting and performing statistical analysis.
Table of Contents
Features
Getting Started
Prerequisites
Installation
Initial Setup
Usage
Automated Processing for Public Datasets
General Workflow for Individual Projects
Configuration
Acknowledgments
License
Features
Data Classification: Classifies MRI data into a BIDS (Brain Imaging Data Structure) compliant format.
Automated Processing: Initiates processing pipelines using industry-standard tools like FreeSurfer, Nilearn, and Dipy.
Server Distribution: Seamlessly distributes processing tasks to local or remote servers.
Statistical Analysis: Extracts key statistics and performs general statistical analysis, including FreeSurfer GLM.
Flexible Workflow: Supports a step-by-step workflow for individual projects or a fully automated pipeline for public datasets like ADNI and PPMI.
Getting Started
Prerequisites
Python 3.5 or higher.
FreeSurfer, Nilearn, and Dipy installed on your system.
An environment for job scheduling, such as slurm, if using a remote cluster.
Installation
You can install NIMB directly from the source code. Navigate to the project directory and run:
pip install .


Initial Setup
The first time you run NIMB, it will guide you through an interactive setup process to configure your local environment and define project-specific paths and variables. This will create essential JSON configuration files in a designated credentials directory.
Usage
Automated Processing for Public Datasets
NIMB provides a fully automated pipeline for well-known public neuroimaging databases.
PPMI:
python3 nimb.py -process run -project loni_ppmi


ADNI:
python3 nimb.py -process run -project loni_adni


General Workflow for Individual Projects
For custom projects, follow these steps to process and analyze your data.
Classify Data: Classify your MRI data into a BIDS-compliant format. This will generate a new_subject.json file.
python3 nimb.py -process classify


Run FreeSurfer Processing: Once your new_subject.json file is created, you can start the FreeSurfer processing pipeline.
python3 nimb.py -process freesurfer -project YOUR_PROJECT_NAME


Extract FreeSurfer Stats: After processing is complete, use this command to extract statistics from the processed data.
python3 nimb.py -process fs-get-stats -project YOUR_PROJECT_NAME


Perform FreeSurfer GLM Analysis: If you have provided a group file for your project, you can perform a GLM analysis.
python3 nimb.py -process fs-glm -project YOUR_PROJECT_NAME


Note: The -glm command and its parameters can also be added for more specific analyses:
python3 nimb.py -process fs-glm -project YOUR_PROJECT_NAME -glmcontrast g1 -glmpermutations 1000
Configuration
NIMB uses JSON files to store configuration variables. During the initial setup, these files are created in your credentials directory. You can edit these files directly to customize the pipeline's behavior.
local.json: Defines local system paths, user information, and processing variables.
projects.json: Defines project-specific variables, including source and processed data directories, group files, and statistical analysis parameters.
remoteX.json: Defines connection details and paths for each remote server or cluster used for processing.
For detailed information on each variable, please refer to the comments within the respective JSON files.
Acknowledgments
Data used in preparation of this app were obtained from public sources such as the Global Alzheimer’s Association Interactive Network (GAAIN), the Parkinson's Progression Markers Initiative (PPMI), and the Alzheimer's Disease Neuroimaging Initiative (ADNI). We thank the teams and participants who have made this data available.
License
This project is licensed under the MIT License.
