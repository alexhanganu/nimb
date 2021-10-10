from nilearn import image
import os

class RUNProcessingNL:

    def __init__(self, all_vars):
        app = "nilearn"
        self.all_vars   = all_vars
        self.project    = all_vars.params.project
        vars_local      = all_vars.location_vars['local']
        self.NIMB_tmp   = vars_local['NIMB_PATHS']['NIMB_tmp']
        self.output_loc = vars_local['NIMB_PATHS']['NIMB_PROCESSED_NILEARN']

        self.db_nl    = dict()
        # nl_ver = vars_local['FREESURFER']['freesurfer_version']
        # logger = Log(self.NIMB_tmp, fs_ver).logger
        self.get_subjects()
        # self.run_connectivity_analysis()


    def get_subjects(self):
        f_new_subjects = os.path.join(self.NIMB_tmp, DEFAULT.app_files[app]["new_subjects"])
        f_db = os.path.join(self.NIMB_tmp, DEFAULT.app_files[app]["db"])
        ls_subj_nl = list()
        if os.path.isfile(f_db_proc):
            print('    reading processing database')
            db_proc = load_json(f_db_proc)
            ls_subj_nl = list(db_proc["PROCESS_NL"].keys())
        else:
            print(f'    database file for app: {app} is missing')

        if os.path.isfile(f_new_subjects):
            print('    reading new subjects to process')
            new_subj = load_json(f_new_subjects)
        if ls_subj_nl:
            print(ls_subj_nl)
            for subj_id in ls_subj_nl:
                print(subj_id)
                self.db_nl[subj_id] = new_subj[subj_id]["func"]
        print(self.db_nl)


    def run_connectivity_analysis(self):
        # #initialize
        harvard   = nl_helper.Havard_Atlas()
        destrieux = nl_helper.Destrieux_Atlas()

        #load file
        for subj_id in self.db_nl:
            if "rsfmri" in self.db_nl[subj_id]:
                rs_img = self.db_nl[subj_id]["rsfmri"][0] #!!! might include multiple files
                im_bold1 = image.load_img(rs_img)#"run1_bold.nii.gz"

                # conn_h = harvard.extract_connectivity_zFisher(im_bold1, self.output_loc, "connectivity.csv")
                # rois_labels = harvard.extract_label_rois(im_bold1)[0] #extract label for ploting
                # conn_d = destrieux.extract_correlation(im_bold1, self.output_loc, 'left_hemi_corr.csv', 'right_hemi_corr.csv')
                # self.plot_connectivity(conn_h, rois_labels)


    def plot_connectivity(self, connectivity, rois_labels):
        #plot
        print(rois_labels[1:])
        import matplotlib.pyplot as plt

        fig = plt.figure(figsize=(11,10))
        plt.imshow(connectivity, interpolation='None', cmap='RdYlBu_r')
        plt.yticks(range(len(rois_labels)), rois_labels[0:]);
        plt.xticks(range(len(rois_labels)), rois_labels[0:], rotation=90);
        plt.title('Parcellation correlation matrix')
        plt.colorbar();
        img_name = os.path.join(self.output_loc,"corr_harvard.png")
        plt.savefig(img_name)




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
    from processing.nilearn import nl_helper

    project_ids = Get_Vars().get_projects_ids()
    params      = get_parameters(project_ids)
    project     = params.project
    all_vars    = Get_Vars(params)

    RUNProcessingNL(all_vars)
