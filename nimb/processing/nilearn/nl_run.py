# %%
from nilearn import image
# import matplotlib.pyplot as plt
import os
# %%

class RUNProcessingNL:

    def __init__(self, all_vars):
        self.all_vars = all_vars
        self.project  = all_vars.params.project
        vars_local    = all_vars.location_vars['local']
        self.NIMB_tmp = vars_local['NIMB_PATHS']['NIMB_tmp']
        self.db_nl    = dict()
        # fs_ver = vars_local['FREESURFER']['freesurfer_version']
        # logger = Log(self.NIMB_tmp, fs_ver).logger
        self.get_subjects()
        # self.run_connectivity_analysis()


    def get_subjects(self):
        f_new_subjects = os.path.join(self.NIMB_tmp, DEFAULT.f_subjects2proc)
        f_db_proc = os.path.join(self.NIMB_tmp, DEFAULT.process_db_name)
        ls_subj_nl = list()
        if os.path.isfile(f_db_proc):
            with open(f_db_proc) as f_open:
                db_proc = json.load(f_open)
                ls_subj_nl = list(db_proc[f"PROCESS_NL"].keys())
        if os.path.isfile(f_new_subjects):
            with open(f_new_subjects) as f_open:
                new_subj = json.load(f_open)
        if ls_subj_nl:
            print(ls_subj_nl)
            for subj_id in ls_subj_nl:
                print(subj_id)
                self.db_nl[subj_id] = new_subj[subj_id]
        print(self.db_nl)


    def run_connectivity_analysis(self):
        # #load file

        # im_bold1 = image.load_img("P001_run1_bold.nii.gz")
        # output_loc = "D:/PROGRAMMING/Alex/nilearn/001PD/corr"

        # #%%
        # #initialize
        # harvard = hp.Havard_Atlas()
        # #%%
        # conn = harvard.extract_connectivity_zFisher(im_bold1, output_loc, "connectivity.csv")
        # #%%
        # #extract label for ploting
        # rois_labels = harvard.extract_label_rois(im_bold1)[0]
        # #print(rois_labels[1:])
        # #plot
        # fig = plt.figure(figsize=(11,10))
        # plt.imshow(conn, interpolation='None', cmap='RdYlBu_r')
        # plt.yticks(range(len(rois_labels)), rois_labels[0:]);
        # plt.xticks(range(len(rois_labels)), rois_labels[0:], rotation=90);
        # plt.title('Parcellation correlation matrix')
        # plt.colorbar();
        # img_name = os.path.join(output_loc,"corr_harvard.png")
        # plt.savefig(img_name)

        # #%%
        # destrieux = hp.Destrieux_Atlas()
        # destrieux.extract_correlation(im_bold1, output_loc, 'left_hemi_corr.csv', 'right_hemi_corr.csv')



def get_parameters(projects):
    """get parameters for nimb"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-project", required=False,
        default=projects[0],
        choices = projects,
        help="names of projects located in credentials_path.py/nimb/projects.json -> PROJECTS",
    )


    params = parser.parse_args()
    return params



if __name__ == "__main__":

    import argparse
    import sys
    try:
        from pathlib import Path
    except ImportError as e:
        print('please install pathlib')
        sys.exit(e)

    top = Path(__file__).resolve().parents[2]
    sys.path.append(str(top))

    from setup.get_vars import Get_Vars
    from distribution.logger import Log
    from distribution.utilities import load_json, save_json
    from distribution.distribution_definitions import DEFAULT
    from processing.schedule_helper import Scheduler, get_jobs_status
    from processing.nilearn import nl_helper as hp

    project_ids = Get_Vars().get_projects_ids()
    params      = get_parameters(project_ids)
    project     = params.project
    all_vars    = Get_Vars(params)

    RUNProcessingNL(all_vars)


