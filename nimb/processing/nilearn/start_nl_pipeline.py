# %%
import processing.nilearn.nl_helper as hp
from nilearn import image
import matplotlib.pyplot as plt
from sys import platform
import os
# %%

class RUNProcessingNL:

    def __init__(self, all_vars):
        self.all_vars = all_vars

        pass


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

    all_vars     = Get_Vars()
    projects     = all_vars.projects
    project_ids  = all_vars.project_ids
    params       = get_parameters(project_ids)

    # vars_local = all_vars.location_vars['local']
    # NIMB_tmp   = vars_local['NIMB_PATHS']['NIMB_tmp']
    # logger = Log(NIMB_tmp,
    #             vars_local['FREESURFER']['freesurfer_version']).logger
    RUNProcessingNL(all_vars)#, logger)


