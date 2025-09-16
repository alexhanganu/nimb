NIMB: NeuroImaging My Brain
NIMB is a comprehensive, automated Python pipeline for structural, functional, and diffusion MRI analysis. It streamlines the entire neuroimaging workflow, from data classification and distribution to local or remote servers, to initiating processing with leading software packages like FreeSurfer, Nilearn, and DIPY, and finally extracting and performing statistical analysis.

# Table of Contents
1. Core Concepts
2. Key Features
3. Getting Started
	- Prerequisites
	- Installation
	- Initial Setup
4. Usage Workflow
	- Step 1: Check Environment Readiness
	- Step 2: Classify Source Data to BIDS
	- Step 3: Find New Subjects & Queue for Processing
	- Step 4: Start the Processing Daemon
	- Step 5: Post-Processing & Statistical Analysis
5. Configuration
6. Acknowledgments
7. License

# Core Concepts
NIMB operates on a powerful daemon-and-runner architecture, making it ideal for scalable, automated processing on high-performance computing (HPC) clusters.
The Daemon (processing_run.py): This is the master orchestrator. You submit this single script to your scheduler (e.g., Slurm). It runs continuously, monitoring the processing queue, launching application-specific runners for new subjects, and handling the final archiving of completed results.

# The Runners
(freesurfer_runner.py, nilearn_runner.py, dipy_runner.py): These are independent, specialized scripts that the daemon launches. Each runner is responsible for managing the entire processing queue for a single application (e.g., freesurfer_runner.py handles all recon-all stages for all queued subjects).

# The Controller
(nimb.py): This is the user's main entry point. You use it to issue high-level commands like "classify my data," "find new subjects," or "start the main daemon." It communicates with the daemon and runners via a shared file-based database.

# Key Features
=> BIDS Classification: Intelligently scans source directories and converts MRI data into a BIDS (Brain Imaging Data Structure) compliant format.

=> Automated Multi-Modal Processing: Manages parallel processing pipelines using industry-standard tools:
* FreeSurfer for structural analysis.
* Nilearn for functional connectivity analysis.
* DIPY for diffusion imaging and tractography.

=> HPC-Ready: Designed for job schedulers like Slurm or tmux, enabling massive parallel processing on local or remote servers.

=> Statistical Analysis: Extracts key statistics from processed data and prepares files for group-level General Linear Model (GLM) analysis with FreeSurfer.

=> Flexible Workflow: Supports both a fully automated pipeline for large datasets and a step-by-step workflow for individual research projects.

# Getting Started
=> Prerequisites

=> Python 3.6+

=> An environment for job scheduling (e.g., Slurm, tmux).

=> The core neuroimaging packages should be installed and accessible in the environment where the runners will execute:

=> FreeSurfer

=> Nilearn

=> DIPY

# Installation
Clone the repository and install the required Python packages:
```
git clone https://github.com/alexhanganu/nimb.git

cd nimb

pip install -r requirements.txt
```

# Initial Setup
The first time you run NIMB, it will guide you through an interactive setup to configure your environment. This creates essential JSON configuration files in ~/.nimb/.
```
python3 nimb/setup/setup.py
```

This will prompt you for paths to your NIMB home, temporary directories, and software installations (like FreeSurfer).
Usage Workflow

The following is a typical step-by-step workflow for a new project.

# Step 1: Check Environment Readiness
Before starting, verify that all paths and dependencies are correctly configured.
```
python3 nimb.py -project YourProjectName -process ready
```

# Step 2: Classify Source Data to BIDS
Scan your source data directory and convert it to BIDS format. This is a user-initiated, one-time step for new data.
```
python3 nimb.py -project YourProjectName -process classify-bids
```

# Step 3: Find New Subjects & Queue for Processing
This command scans your BIDS directory, compares it against the project's processed data, and adds any new, unprocessed subjects to the processing queue.
```
python3 nimb.py -project YourProjectName -process run
```

# Step 4: Start the Processing Daemon
Submit the main processing daemon to your scheduler. This daemon will find the queued subjects from the previous step and start launching the appropriate application runners (FreeSurfer, Nilearn, etc.).
```
python3 nimb.py -project YourProjectName -process process
```

# Step 5: Post-Processing & Statistical Analysis
Once subjects have been processed by the daemon, you can perform post-processing tasks. These are also submitted as independent jobs.

# Extract FreeSurfer Statistics
Aggregate .stats files from all processed subjects into comprehensive Excel tables.

```
python3 nimb.py -project YourProjectName -process fs-stats-get
```

# A. Run Statistical analysis
Run standard statistical analysis on all data.

```python3 nimb.py -project YourProjectName -process run-stats```

# B. Prepare and Run FreeSurfer GLM Analysis
Prepare the necessary files (.fsgd, .mtx) and then run the GLM analysis.

# 1. Prepare GLM files

```python3 nimb.py -project YourProjectName -process fs-glm-prep```

# 2. Run the GLM analysis

```python3 nimb.py -project YourProjectName -process fs-glm```


# 3. Extract GLM Result Images
Generate statistical map images (.tiff) from the completed GLM analysis for visualization and publication.

```python3 nimb.py -project YourProjectName -process fs-glm-images```


# Configuration
NIMB is configured via simple JSON files located in ~/.nimb/.

- local.json: Defines paths and settings for your local machine, including software locations (FREESURFER_HOME), temporary directories, and scheduler settings.

- projects.json: Defines all project-specific information, such as paths to source BIDS and processed derivative data, the name of your subject/group information file, and variables for statistical analysis.

- remoteX.json: (Optional) Defines connection details and paths for remote servers or clusters.

# Acknowledgments
This tool was developed to streamline neuroimaging research. Data used in the development and testing of this app were obtained from public sources, including the Global Alzheimer’s Association Interactive Network (GAAIN), the Parkinson's Progression Markers Initiative (PPMI), and the Alzheimer's Disease Neuroimaging Initiative (ADNI). We thank the teams and participants who have made this data available.

# License
This project is licensed under the MIT License. See the LICENSE file for details.
