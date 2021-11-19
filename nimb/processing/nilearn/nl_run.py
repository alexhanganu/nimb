from nilearn import image
import os

class RUNProcessingNL:

    def __init__(self, all_vars):
        self.app        = "nilearn"
        self.all_vars   = all_vars
        self.project    = all_vars.params.project
        vars_local      = all_vars.location_vars['local']
        self.NIMB_tmp   = vars_local['NIMB_PATHS']['NIMB_tmp']
        vars_app        = vars_local["NILEARN"]
        self.output_loc = vars_app['NIMB_PROCESSED']
        process_order   = ['connectivity',]

        self.db_nl      = dict()
        # self.db_nl    = app_db.DBManage(self.app,
        #                             vars_local,
        #                             vars_app,
        #                             process_order
        #                             DEFAULT,
        #                             atlas_definitions)
        # nl_ver = vars_local['FREESURFER']['nilearn_version']
        # logger = Log(self.NIMB_tmp, fs_ver).logger
        self.get_subjects()
        self.run_connectivity_analysis()
        # self.output_loc = vars_local['NIMB_PATHS']['NIMB_PROCESSED_NILEARN']


    def get_subjects(self):
        # subjects = self.db_nl.get_db()
        new_subjects_f_name = DEFAULT.app_files[self.app]["new_subjects"]
        new_subjects_f_path = os.path.join(self.NIMB_tmp, new_subjects_f_name)
        if os.path.isfile(new_subjects_f_path):
            print('    reading new subjects to process')
            new_subj = load_json(new_subjects_f_path)
            self.db_nl = new_subj

        # ls_subj_nl = list()
        # f_db = os.path.join(self.NIMB_tmp, DEFAULT.app_files[self.app]["db"])
        # if os.path.isfile(f_db):
        #     print('    reading processing database')
        #     db_proc = load_json(f_db)
        #     ls_subj_nl = list(db_proc["PROCESS_NL"].keys())
        # else:
        #     print(f'    database file for app: {self.app} is missing')

        # if ls_subj_nl:
        #     print(ls_subj_nl)
        #     for subj_id in ls_subj_nl:
        #         print(subj_id)
        #         self.db_nl[subj_id] = new_subj[subj_id]["func"]


    def run_connectivity_analysis(self):
        #initialize
        print(f"performing connectivity analysis with harvard atlas")
        harvard   = nl_helper.Havard_Atlas()
        for subj_id in self.db_nl:
            print(f"    for subject: {subj_id}")
            rs_img = self.db_nl[subj_id]["func"]["bold"][0]
            im_bold1 = image.load_img(rs_img)#"run1_bold.nii.gz"
            conn_h = harvard.extract_connectivity_zFisher(im_bold1,
                                                            self.output_loc,
                                                            f"{subj_id}_connectivity_harvard.csv")
            rois_labels_h = harvard.extract_label_rois(im_bold1)[0] #extract label for ploting
            self.plot_connectivity(conn_h, rois_labels_h, f"{subj_id}_corr_harvard.png")

        # print(f"performing connectivity analysis with destrieux atlas")
        # destrieux = nl_helper.Destrieux_Atlas()
        # for subj_id in self.db_nl:
        #     print(f"    for subject: {subj_id}")
        #     conn_d = destrieux.extract_correlation(im_bold1,
        #                                             self.output_loc,
        #                                             f'{subj_id}_correlation_destrieux_left.csv',
        #                                             f'{subj_id}_correlation_destrieux_right.csv')
        #     rois_labels_d = destrieux.extract_label_rois(im_bold1)[0] #extract label for ploting
        #     self.plot_connectivity(conn_d, rois_labels_d, f"{subj_id}_corr_destrieux.png")


    def plot_connectivity(self, connectivity, rois_labels, f_name):
        #plot
        print("    saving image and roi file")
        import matplotlib.pyplot as plt

        fig = plt.figure(figsize=(11,10))
        plt.imshow(connectivity, interpolation='None', cmap='RdYlBu_r')
        plt.yticks(range(len(rois_labels)), rois_labels[0:]);
        plt.xticks(range(len(rois_labels)), rois_labels[0:], rotation=90);
        plt.title(f'Parcellation correlation matrix')
        plt.colorbar();
        img_name = os.path.join(self.output_loc, f_name)
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
    from processing.atlases import atlas_definitions
    from processing import nl_helper, app_db

    project_ids = Get_Vars().get_projects_ids()
    params      = get_parameters(project_ids)
    project     = params.project
    all_vars    = Get_Vars(params)

    RUNProcessingNL(all_vars)
