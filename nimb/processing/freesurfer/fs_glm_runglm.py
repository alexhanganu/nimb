#!/bin/python
# last update: 20230304

# testing the sending the scheduler method
send_2scheduler = True

import os
import sys
import linecache
import shutil
import time

try:
    from processing.freesurfer import fs_definitions
except ImportError:
    import fs_definitions


class PerformGLM():

    def __init__(self,
                all_vars,
                params,
                Log,
                sig_fdr_thresh = 3.0):
        '''
        sig_fdr_thresh at 3.0 corresponds to p = 0.001;
        for p=0.05 use value 1.3,
        but it should be used ONLY for visualisation.
        '''
        self.vars_local            = all_vars.location_vars['local']
        vars_fs                    = self.vars_local["FREESURFER"]
        self.FREESURFER_HOME       = vars_fs["FREESURFER_HOME"]
        self.SUBJECTS_DIR          = vars_fs["SUBJECTS_DIR"]
        self.measurements          = vars_fs["GLM_measurements"]
        self.thresholds            = vars_fs["GLM_thresholds"]
        self.cache_thresh          = vars_fs["GLM_MCz_cache"]
        self.PATHglm               = params.glm_dir
        self.contrast_choice       = params.contrast
        self.corrected             = params.corrected
        self.permutations          = params.permutations
        print("number of permutations is:", params.permutations)
        self.cluster_thresh        = 0.05
        self.glm_sim_thresh        = 1.3
        param                      = fs_definitions.FSGLMParams(self.PATHglm)
        self.schedule              = Scheduler(self.vars_local)
        self.log                   = Log(self.vars_local['NIMB_PATHS']['NIMB_tmp']).logger

        self.sig_fdr_thresh        = sig_fdr_thresh

        self.PATHglm_glm           = param.PATHglm_glm
        self.PATH_img              = param.PATH_img
        self.PATHglm_results       = param.PATHglm_results
        self.sig_fdr_json          = param.sig_fdr_json
        self.sig_mc_json           = param.sig_mc_json
        self.err_mris_preproc_file = param.err_mris_preproc_file
        self.mcz_sim_direction     = param.mcz_sim_direction
        self.hemispheres           = fs_definitions.hemi
        self.GLM_sim_fwhm4csd      = param.GLM_sim_fwhm4csd
        self.GLM_MCz_meas_codes    = param.GLM_MCz_meas_codes
        self.cluster_stats         = param.cluster_stats
        self.cluster_stats_2csv    = param.cluster_stats_2csv
        self.sig_contrasts         = param.sig_contrasts
        self.db                    = {'RUNNING_JOBS':dict()}
        self.nr_cmds_2combine      = 10
        self.pcc_r_filename       = "pcc.r.dat"
        self.cohensd_sum_filename = "cohensd.sum.dat"
        self.files_glm, RUN        = self.files_f4glm_get(param)


        if RUN:
            self.err_preproc   = list()
            self.sig_fdr_data  = dict()
            self.sig_mc_data   = dict()
            self.loop_run()

            if self.err_preproc:
                save_json(self.err_preproc, self.err_mris_preproc_file)
            if self.sig_fdr_data:
                save_json(self.sig_fdr_data, self.sig_fdr_json)
            if self.sig_mc_data:
                save_json(self.sig_mc_data, self.sig_mc_json)
            if os.path.exists(self.cluster_stats):
                ClusterFile2CSV(self.cluster_stats,
                                self.cluster_stats_2csv,
                                self.log)
            self.log.info('\n\nGLM DONE')
        else:
            sys.exit('some ERRORS were found. Cannot perform FreeSurfer GLM')


    def loop_run(self):
        """initiate loop running for GLM analysis
        """
        if self.check_active_tasks():
            self.preproc_run()
        if self.check_active_tasks():
            self.glmfit_run()
        if self.check_active_tasks():
            self.monte_carlo_correction_run()
        if self.check_active_tasks():
            self.results_monte_carlo_get()


    def db_update(self):
        """will check status of each job
            from the list of all running jobs
        """
        tup_keys = tuple(self.db['RUNNING_JOBS'].keys())
        for key in tup_keys:
            self.db['RUNNING_JOBS'], status, _ = self.get_status_for_subjid_in_queue(self.db['RUNNING_JOBS'],
                                                                                    key)
            self.log.info(f"        job: {key} has status: {status}")
            if status == 'none':
                self.db['RUNNING_JOBS'].pop(key, None)
        return len(self.db['RUNNING_JOBS'].keys())


    def check_active_tasks(self):
        """will initiate a waiting loop that will wait until all batched are finished
        """
        run = True
        active_subjects = self.db_update()
        while active_subjects >0:
            time_to_sleep = 300 # 5 minutes
            self.log.info(f'\n                 active subjects: {str(active_subjects)}')
            self.log.info('\n\nWAITING. \nNext run at: '+str(time.strftime("%H:%M",time.localtime(time.time()+time_to_sleep))))
            time.sleep(time_to_sleep)
            active_subjects = self.db_update()
        return run


    def preproc_run(self):
        """do preprocessing using mris_preproc, before running GLM
        """
        self.log.info('\n\n    PREPROCESSING performing using mris_preproc')
        process = "glm_preproc"
        self.submit_cmds = dict()
        dirs_present = list()

        for fsgd_type in self.files_glm:
            self.files_glm[fsgd_type]["glm"] = dict()
            for fsgd_file in self.files_glm[fsgd_type]['fsgd']:
                    fsgd_file_name = fsgd_file.split("/")[-1].replace('.fsgd','')
                    fsgd_f_unix = os.path.join(self.PATHglm,'fsgd',fsgd_file_name+'_unix.fsgd')
                    for hemi in self.hemispheres:
                        for meas in self.measurements:
                            for thresh in self.thresholds:
                                glm_analysis = f'{meas}.{hemi}.fwhm{str(thresh)}'
                                analysis_name = f'{fsgd_file_name}.{glm_analysis}'
                                submit_key = analysis_name
                                glmdir   = os.path.join(self.PATHglm_glm, analysis_name)
                                mgh_f    = os.path.join(glmdir, f'{glm_analysis}.y.mgh')
                                f_cache  = f'{meas}.fwhm{str(thresh)}.fsaverage'
                                cmd_tail = f' --target fsaverage --hemi {hemi} --out {mgh_f}'
                                cmd      = f'mris_preproc --fsgd {fsgd_f_unix} --cache-in {f_cache}{cmd_tail}'
                                self.files_glm[fsgd_type]["glm"][analysis_name] = {"mgh_f": mgh_f,
                                                                                   "fsgd_f_unix": fsgd_f_unix,
                                                                                   "hemi": hemi,
                                                                                   "meas": meas}
                                if not os.path.exists(glmdir) or not os.path.exists(mgh_f):
                                    self.submit_cmds[submit_key] = cmd
                                else:
                                    dirs_present.append(glmdir)
        if dirs_present:
            self.log.info(f"        DONE: {len(dirs_present)} glm folders are present and mgh file was created")

        if self.submit_cmds:
            self.log.info(f'PREPROC: must create: {len(list(self.submit_cmds.keys()))} folders')
            tmp_ls_keys =  list(self.submit_cmds.keys())[:self.nr_cmds_2combine]
            new_data = self.submit_cmds.copy()
            while len(tmp_ls_keys) > 0:
                tmp_data = {i:self.submit_cmds[i] for i in tmp_ls_keys}
                key      = list(tmp_data.keys())[0]
                cmd      = "\n".join(list(tmp_data.values()))
                self.schedule_send(key, cmd, process)
                new_data    = {i:new_data[i] for i in new_data.keys() if i not in tmp_ls_keys}
                tmp_ls_keys =  list(new_data.keys())[:self.nr_cmds_2combine]


    def glmfit_run(self):
        """do GLM using mri_glmfit
            flags:
                --skew: to compute skew and p-value for skew, will create files skew.mgh and skew.sig.mgh
                --kurtosis: to compute kurtosis and p-value for kurtosis, will create files kurtosis mgh and kurtosis.sig.mgh
                --pca: perform pca/svd analysis on residual, will create folder pca-eres
                --save-yhat: save signal estimate, will create the file yhat.mgh
            to run mri_glmfit only for ROIs use command:
                mri_glmfit --label or
                mri_glmfit --table (instead of --y)
                    the table must be created with the first column being subject name
                    and first row being clustername (Cluter 1, Cluster 2)
                    col = 1, row = 1 can by dummy string (e.g., "dummy")
        """
        self.log.info('\n\n    GLM analysis performing using mri_glmfit')
        process = "glmfit"
        self.submit_cmds = dict()
        dirs_present = list()
        dirs_error = list()

        for fsgd_type in self.files_glm:
            for analysis_name in self.files_glm[fsgd_type]["glm"]:
                glmdir      = os.path.join(self.PATHglm_glm, analysis_name)
                mgh_f       = self.files_glm[fsgd_type]["glm"][analysis_name]["mgh_f"]
                fsgd_f_unix = self.files_glm[fsgd_type]["glm"][analysis_name]["fsgd_f_unix"]
                hemi        = self.files_glm[fsgd_type]["glm"][analysis_name]["hemi"]
                self.files_glm[fsgd_type]["glm"][analysis_name]["contrasts"] = dict()
                if os.path.exists(glmdir) and os.path.exists(mgh_f):
                    for contrast_file in self.files_glm[fsgd_type]['mtx']:
                        glm_contrast_dir = contrast_file.replace(".mtx","")
                        for gd2mtx in self.files_glm[fsgd_type]['gd2mtx']:
                            submit_key   = analysis_name+"_"+glm_contrast_dir
                            cmd_header   = f'mri_glmfit --y {mgh_f} --fsgd {fsgd_f_unix} {gd2mtx}'
                            glmdir_cmd   = f'--glmdir {glmdir}'
                            path_2label  = os.path.join(self.SUBJECTS_DIR, 'fsaverage', 'label', f'{hemi}.aparc.label')
                            surf_label   = f'--surf fsaverage {hemi} --label {path_2label}'
                            contrast_cmd = f'--C {os.path.join(self.PATHglm, "contrasts", contrast_file)}'
                            cmd_tail     = f'--skew --kurtosis --pca --save-yhat'
                            cmd          = f'{cmd_header} {glmdir_cmd} {surf_label} {contrast_cmd} {cmd_tail}'
                            glm_folder   = os.path.join(glmdir, glm_contrast_dir)
                            self.files_glm[fsgd_type]["glm"][analysis_name]["contrasts"][glm_contrast_dir] = {"":list()}
                            if not os.path.exists(glm_folder):
                                self.submit_cmds[submit_key] = cmd
                            else:
                                dirs_present.append(glmdir)
                                if not os.path.exists(os.path.join(glm_folder, "sig.mgh")):
                                    self.log.info(f"        ERROR!!!! sig.mgh file is ABSENT for folder: {glm_folder}")
                                    dirs_error.append(glm_folder)
                else:
                    self.log.info(f'ERR: folder {glmdir} is missing or mgh file: {mgh_f} is missing')
                if not os.path.exists(mgh_f):
                    self.err_preproc.append(mgh_f)

        if dirs_present:
            self.log.info(f"        DONE: {len(dirs_present)} glm analysis were done and sig files were created")
        if dirs_error:
            self.log.info(f"        ERROR: {len(dirs_present)} glm analysis have missing sig.mgh files")

        if self.submit_cmds:
            self.log.info(f'GLM commands total: {len(list(self.submit_cmds.keys()))}')
            tmp_ls_keys =  list(self.submit_cmds.keys())[:self.nr_cmds_2combine]
            new_data = self.submit_cmds.copy()
            while len(tmp_ls_keys) > 0:
                tmp_data = {i:self.submit_cmds[i] for i in tmp_ls_keys}
                key      = list(tmp_data.keys())[0]
                cmd      = "\n".join(list(tmp_data.values()))
                self.schedule_send(key, cmd, process)
                new_data    = {i:new_data[i] for i in new_data.keys() if i not in tmp_ls_keys}
                tmp_ls_keys =  list(new_data.keys())[:self.nr_cmds_2combine]


    def simulations_run(self):
        """run simulations using mri_glmfit-sim
            https://surfer.nmr.mgh.harvard.edu/fswiki/FsTutorial/MultipleComparisonsV6.0Perm
            --glmdir: Specify the same GLM directory
            --perm: Run a permuation simulation 
            Vertex-wise/cluster-forming threshold of (1.3 = p < .05, 2 = p < .01).
            direction: the sign of analysis ("neg" for negative, "pos" for positive, or "abs" for absolute/unsigned)
            --cwp 0.05 : Keep clusters that have cluster-wise p-values < 0.05. To see all clusters, set to .999
            --2spaces : adjust p-values for two hemispheres
        """
        self.log.info('\n\n    SIMULATIONs and permutations performing using mri_glmfit-sim')
        process  = "glmfit-sim"
        self.submit_cmds = dict()
        dirs_present = list()

        for fsgd_type in self.files_glm:
            for analysis_name in self.files_glm[fsgd_type]["glm"]:
                glmdir   = os.path.join(self.PATHglm_glm, analysis_name)
                hemi     = self.files_glm[fsgd_type]["glm"][analysis_name]["hemi"]
                meas     = self.files_glm[fsgd_type]["glm"][analysis_name]["meas"]
                mcz_meas = self.GLM_MCz_meas_codes[meas]
                for glm_contrast_dir in self.files_glm[fsgd_type]["glm"][analysis_name]["contrasts"]:
                    glm_folder   = os.path.join(glmdir, glm_contrast_dir)
                    sig_f         = os.path.join(glm_folder,'sig.mgh')
                    maxvox_file   = os.path.join(glm_folder, 'maxvox.dat')
                    contrast       = glm_contrast_dir.replace(fsgd_type+'_','')
                    contrast_f_ix  = self.files_glm[fsgd_type]['mtx'].index(glm_contrast_dir + ".mtx")
                    explanation    = self.files_glm[fsgd_type]['mtx_explanation'][contrast_f_ix]
                    if os.path.exists(maxvox_file):
                        if self.check_maxvox(maxvox_file):
                            # populate log file with significant results
                            with open(self.sig_contrasts, 'a') as f:
                                f.write(f'{analysis_name}/{glm_contrast_dir}\n')
                            self.prepare_for_image_extraction_fdr(hemi, glmdir, analysis_name,
                                                                  glm_contrast_dir)

                            self.files_glm[fsgd_type]["glm"][analysis_name]["contrasts"][glm_contrast_dir] = {"csd": list()}
                            for direction in self.mcz_sim_direction:
                                submit_key = f"mcz_{analysis_name}_{glm_contrast_dir}_{direction}"
                                cwsig_mc_f, _, sum_mc_f, ocn_mc_f, oannot_mc_f, _, _, _ = self.mcz_files_get(direction, mcz_meas, glm_folder)
                                if not os.path.exists(sum_mc_f):
                                    fwhm = f'fwhm{self.GLM_sim_fwhm4csd[meas][hemi]}'
                                    th   = f'th{str(self.cache_thresh)}'
                                    path_2fsavg = os.path.join(self.FREESURFER_HOME, 'average', 'mult-comp-cor', 'fsaverage')
                                    csd_mc_f = os.path.join(path_2fsavg, hemi, 'cortex', fwhm, direction, th, 'mc-z.csd')
                                    cmd_header_curv = f'mri_glmfit-sim --glmdir {glm_folder}'
                                    cmd_perm_curv   = f'--sim perm {self.permutations} {self.glm_sim_thresh} {direction}'
                                    cmd_tail_curve   = f'--cwp {self.cluster_thresh} --2spaces'
                                    self.files_glm[fsgd_type]["glm"][analysis_name]["contrasts"][glm_contrast_dir]["csd"].append(direction)
                                    run_permut = f'{cmd_header_curv} {cmd_perm_curv} {cmd_tail_curve}'
                                    if meas != "curv":
                                        cmd = run_permut
                                    else:
                                        cmd_cache_curv  = f'--cache {str(self.cache_thresh)} {direction}'
                                        run_cache  = f'{cmd_header_curv} {cmd_cache_curv} {cmd_tail_curve}'
                                        cmd = "\n".join([run_cache, run_permut])
                                    self.submit_cmds[submit_key] = cmd
                                else:
                                    dirs_present.append(submit_key)
        if dirs_present:
            self.log.info(f"        DONE: {len(dirs_present)} folder has all permutations")

        if self.submit_cmds:
            self.log.info(f'SIMULATION submitting')
            self.log.info(f'SIMULATION commands total: {len(list(self.submit_cmds.keys()))}')
            tmp_ls_keys =  list(self.submit_cmds.keys())[:self.nr_cmds_2combine]
            new_data = self.submit_cmds.copy()
            while len(tmp_ls_keys) > 0:
                tmp_data = {i:self.submit_cmds[i] for i in tmp_ls_keys}
                key      = list(tmp_data.keys())[0]
                cmd      = "\n".join(list(tmp_data.values()))
                self.schedule_send(key, cmd, process)
                new_data    = {i:new_data[i] for i in new_data.keys() if i not in tmp_ls_keys}
                tmp_ls_keys =  list(new_data.keys())[:self.nr_cmds_2combine]


    def monte_carlo_correction_run(self):
        """run Monte-Carlo correction using mri_surfcluster
        """
        self.log.info('\n\n    MONTE_CARLO correction performing using mri_surfcluster')
        process  = "glm_montecarlo"
        self.submit_cmds = dict()
        dirs_present = list()

        for fsgd_type in self.files_glm:
            for analysis_name in self.files_glm[fsgd_type]["glm"]:
                glmdir   = os.path.join(self.PATHglm_glm, analysis_name)
                hemi     = self.files_glm[fsgd_type]["glm"][analysis_name]["hemi"]
                meas     = self.files_glm[fsgd_type]["glm"][analysis_name]["meas"]
                mcz_meas = self.GLM_MCz_meas_codes[meas]
                for glm_contrast_dir in self.files_glm[fsgd_type]["glm"][analysis_name]["contrasts"]:
                    glm_folder   = os.path.join(glmdir, glm_contrast_dir)
                    sig_f         = os.path.join(glm_folder,'sig.mgh')
                    maxvox_file   = os.path.join(glm_folder, 'maxvox.dat')
                    contrast       = glm_contrast_dir.replace(fsgd_type+'_','')
                    contrast_f_ix  = self.files_glm[fsgd_type]['mtx'].index(glm_contrast_dir + ".mtx")
                    explanation    = self.files_glm[fsgd_type]['mtx_explanation'][contrast_f_ix]
                    if os.path.exists(maxvox_file):
                        if self.check_maxvox(maxvox_file):
                            # populate log file with significant results
                            with open(self.sig_contrasts, 'a') as f:
                                f.write(f'{analysis_name}/{glm_contrast_dir}\n')
                            self.prepare_for_image_extraction_fdr(hemi, glmdir, analysis_name,
                                                                  glm_contrast_dir)

                            self.files_glm[fsgd_type]["glm"][analysis_name]["contrasts"][glm_contrast_dir] = {"mcz": list()}
                            for direction in self.mcz_sim_direction:
                                submit_key = f"mcz_{analysis_name}_{glm_contrast_dir}_{direction}"
                                cwsig_mc_f, _, sum_mc_f, ocn_mc_f, oannot_mc_f, _, _, _ = self.mcz_files_get(direction, mcz_meas, glm_folder)
                                if not os.path.exists(sum_mc_f):
                                    fwhm = f'fwhm{self.GLM_sim_fwhm4csd[meas][hemi]}'
                                    th   = f'th{str(self.cache_thresh)}'
                                    path_2fsavg = os.path.join(self.FREESURFER_HOME, 'average', 'mult-comp-cor', 'fsaverage')
                                    csd_mc_f = os.path.join(path_2fsavg, hemi, 'cortex', fwhm, direction, th, 'mc-z.csd')
                                    header_cmd = f'mri_surfcluster --in {sig_f} --csd {csd_mc_f}'
                                    mask_cmd   = f'--mask {os.path.join(glmdir,"mask.mgh")}'
                                    params_cmd = self.mcz_commands_get(direction, mcz_meas, glm_folder)
                                    tail_cmd   = f'--annot aparc --cwpvalthresh {self.cluster_thresh} --surf white'
                                    cmd        = f'{header_cmd} {mask_cmd} {params_cmd} {tail_cmd}'
                                    self.files_glm[fsgd_type]["glm"][analysis_name]["contrasts"][glm_contrast_dir]["mcz"].append(direction)
                                    self.submit_cmds[submit_key] = cmd
                                else:
                                    dirs_present.append(submit_key)
        if dirs_present:
            self.log.info(f"        DONE: {len(dirs_present)} folder have all Monte-Carlo correction performed")

        if self.submit_cmds:
            self.log.info(f'MCZ submitting')
            self.log.info(f'MCZ commands total: {len(list(self.submit_cmds.keys()))}')
            tmp_ls_keys =  list(self.submit_cmds.keys())[:self.nr_cmds_2combine]
            new_data = self.submit_cmds.copy()
            while len(tmp_ls_keys) > 0:
                tmp_data = {i:self.submit_cmds[i] for i in tmp_ls_keys}
                key      = list(tmp_data.keys())[0]
                cmd      = "\n".join(list(tmp_data.values()))
                self.schedule_send(key, cmd, process)
                new_data    = {i:new_data[i] for i in new_data.keys() if i not in tmp_ls_keys}
                tmp_ls_keys =  list(new_data.keys())[:self.nr_cmds_2combine]


    def results_monte_carlo_get(self):
        """extracting significant results after Monte-Carlo correction
        """
        self.log.info('\n\n    RESULTS extracting for Monte-Carlo analysis')

        for fsgd_type in self.files_glm:
            for analysis_name in self.files_glm[fsgd_type]["glm"]:
                glmdir   = os.path.join(self.PATHglm_glm, analysis_name)
                hemi     = self.files_glm[fsgd_type]["glm"][analysis_name]["hemi"]
                meas     = self.files_glm[fsgd_type]["glm"][analysis_name]["meas"]
                mcz_meas = self.GLM_MCz_meas_codes[meas]
                for glm_contrast_dir in self.files_glm[fsgd_type]["glm"][analysis_name]["contrasts"]:
                    glm_folder   = os.path.join(glmdir, glm_contrast_dir)
                    contrast       = glm_contrast_dir.replace(fsgd_type+'_','')
                    contrast_f_ix  = self.files_glm[fsgd_type]['mtx'].index(glm_contrast_dir + ".mtx")
                    explanation    = self.files_glm[fsgd_type]['mtx_explanation'][contrast_f_ix]
                    if "mcz" in self.files_glm[fsgd_type]["glm"][analysis_name]["contrasts"][glm_contrast_dir]:
                        for direction in self.mcz_sim_direction:
                            cwsig_mc_f, _, sum_mc_f, ocn_mc_f, oannot_mc_f, _, pcc, cohensd_sum = self.mcz_files_get(direction, mcz_meas, glm_folder)
                            if self.check_mcz_summary(sum_mc_f):
                                self.pcc_cohensd_get(glm_folder, ocn_mc_f)
                                self.cluster_stats_to_file(analysis_name,
                                                            sum_mc_f,
                                                            pcc,
                                                            cohensd_sum,
                                                            contrast,
                                                            direction,
                                                            explanation)
                                self.prepare_for_image_extraction_mc(hemi, analysis_name, glm_folder,
                                                                    glm_contrast_dir, contrast, direction,
                                                                    cwsig_mc_f, oannot_mc_f)


    def pcc_cohensd_get(self,
                        glm_folder,
                        ocn_mc_f):
        """extract the Mean value per contrast
            that represents the effect size
            as per: https://www.mail-archive.com/freesurfer@nmr.mgh.harvard.edu/msg52144.html
                    https://www.mail-archive.com/freesurfer@nmr.mgh.harvard.edu/msg57316.html
                    the Mean is the value needed for extraction
                    The mean in .dat file is the Cohen's D mean
                                    or the Mean R Partial Correlation Coefficient (pcc) or effect size
        extract F-value with:
            mri_segstats --seg mc-z.pos.ar13.sig.vertex.mgh --i F.mgh --sum Fstats_g1g2_g3.txt
            os.system(f'mri_seg_stats --i F.mgh --seg {vwsig_mc_f} --sum Fstats.txt')
        """
        os.chdir(glm_folder)
        self.log.info(f"{'='*20}")
        if os.path.exists(os.path.join(os.getcwd(), "pcc.mgh")):
            self.log.info(f'        PCC R: extracting partial correlation coefficient R from pcc.mgh')
            self.log.info(f"            in folder: {os.getcwd()}")
            if not os.path.exists(os.path.join(os.getcwd(), self.pcc_r_filename)):
                os.system(f'mri_segstats --i pcc.mgh --seg {ocn_mc_f} --exclude 0 --o {self.pcc_r_filename}')
            else:
                self.log.info("            results are present")
        else:
            self.log.info(f'        PCC R: CANNOT extract partial correlation coefficient R from pcc.mgh, file is MISSING')

        if os.path.exists(os.path.join(os.getcwd(), "gamma.mgh")):
            self.log.info(f'        COHENSD: extracting cohensd correlation coefficient')
            self.log.info(f"            in folder: {os.getcwd()}")
            if not os.path.exists(os.path.join(os.getcwd(), self.cohensd_sum_filename)):
                os.system('fscalc gamma.mgh div ../rstd.mgh -o cohensd.mgh')
                os.system(f'mri_segstats --i cohensd.mgh --seg {ocn_mc_f} --exclude 0 --o {self.cohensd_sum_filename}')
            else:
                self.log.info("            results are present")
        else:
            self.log.info(f'        COHENSD: CANNOT extract cohensd correlation coefficient from gamma.mgh, file is MISSING')


    def mcz_files_get(self,
                      direction,
                      mcz_meas,
                      glm_folder):
        mcz_header  = f'mc-z.{direction}.{mcz_meas}{str(self.cache_thresh)}'
        cwsig_mc_f  = os.path.join(glm_folder,f'{mcz_header}.sig.cluster.mgh')
        vwsig_mc_f  = os.path.join(glm_folder,f'{mcz_header}.sig.vertex.mgh')
        sum_mc_f    = os.path.join(glm_folder,f'{mcz_header}.sig.cluster.summary')
        ocn_mc_f    = os.path.join(glm_folder,f'{mcz_header}.sig.ocn.mgh')
        oannot_mc_f = os.path.join(glm_folder,f'{mcz_header}.sig.ocn.annot')
        csdpdf_mc_f = os.path.join(glm_folder,f'{mcz_header}.pdf.dat')
        pcc         = os.path.join(glm_folder, self.cohensd_sum_filename)
        cohensd_sum = os.path.join(glm_folder, self.cohensd_sum_filename)
        return cwsig_mc_f, vwsig_mc_f, sum_mc_f, ocn_mc_f, oannot_mc_f, csdpdf_mc_f, pcc, cohensd_sum


    def mcz_commands_get(self,
                      direction,
                      mcz_meas,
                      glm_folder):
        cwsig_mc_f, vwsig_mc_f, sum_mc_f, ocn_mc_f, oannot_mc_f, csdpdf_mc_f, _, _ = self.mcz_files_get(direction, mcz_meas, glm_folder)
        cmd_sig_fs  = f'--cwsig {cwsig_mc_f} --vwsig {vwsig_mc_f}'
        cmd_params  = f'--sum {sum_mc_f} --ocn {ocn_mc_f} --oannot {oannot_mc_f} --csdpdf {csdpdf_mc_f}'
        return f'{cmd_sig_fs} {cmd_params}'


    def check_maxvox(self, maxvox_file):
        res = False
        val = [i.strip() for i in open(maxvox_file).readlines()][0].split()[0]
        if float(val) > self.sig_fdr_thresh or float(val) < -self.sig_fdr_thresh:
            res = True
        return res


    def check_mcz_summary(self, file):
        if len(linecache.getline(file, 42).strip('\n')) > 0:
            return True
        else:
            return False


    def cluster_stats_to_file(self,
                              analysis_name,
                              sum_mc_f,
                              pcc,
                              cohensd_sum,
                              contrast,
                              direction,
                              explanation):
        if not os.path.isfile(self.cluster_stats):
            open(self.cluster_stats,'w').close()
        pcc_cont = list()
        cohens_cont = list()

        sum_mc_cont = [i.rstrip() for i in open(sum_mc_f).readlines()[41:]]
        if os.path.exists(pcc):
            cont = open(pcc, "r").readlines()
            ix_pcc  = cont.index([i for i in cont if "# ColHeaders" in i][0])
            pcc_cont = [i.rstrip() for i in cont[ix_pcc:]]
        if os.path.exists(cohensd_sum):
            cont = open(cohensd_sum, "r").readlines()
            ix_cohensd  = cont.index([i for i in cont if "# ColHeaders" in i][0])
            cohens_cont = [i.rstrip() for i in cont[ix_cohensd:]]

        with open(self.cluster_stats, 'a') as f:
            f.write('{}_{}_{}\n'.format(analysis_name, contrast, direction))
            f.write(explanation+'\n')
            for value in sum_mc_cont:
                f.write(value+'\n')
            f.write('\n')
            if pcc_cont:
                f.write('PCC R:\n')
                for value in pcc_cont:
                    f.write(value+'\n')
            if cohens_cont:
                f.write('Cohens D:\n')
                for value in cohens_cont:
                    f.write(value+'\n')


    def prepare_for_image_extraction_fdr(self, hemi, glmdir, analysis_name, fsgd_type_contrast):
        '''copying sig.mgh file from the contrasts to the image/contrast folder
            populating dict with significant fdr data, that contains the data to access the sig.mgh file
        Args:
            hemi: hemisphere
            glmdir: dir for the analysis = self.PATHglm_glm + analysis_name
            analysis_name: name of the folder for glm analysis
            fsgd_type_contrast: name of the folder for the specific contrast used
        Return:
            none
            creates corresponding folder in the self.PATH_img folder
            populates the sig_fdr_data dictionary
        '''
        glm_image_dir = os.path.join(self.PATH_img, analysis_name, fsgd_type_contrast)
        if not os.path.exists(glm_image_dir):
            os.makedirs(glm_image_dir)
        sig_file = 'sig.mgh'
        shutil.copy(os.path.join(glmdir, fsgd_type_contrast, sig_file), glm_image_dir)

        sig_count = len(self.sig_fdr_data.keys())+1
        self.sig_fdr_data[sig_count] = {
                                'hemi'         : hemi,
                                'analysis_name': analysis_name,
                                'fsgd_type_contrast': fsgd_type_contrast,
                                'sig_thresh'   : self.sig_fdr_thresh}


    def prepare_for_image_extraction_mc(self, hemi, analysis_name, glm_folder,
                                            fsgd_type_contrast, contrast, direction,
                                            cwsig_mc_f, oannot_mc_f):
        '''copying MCz significancy files file from the contrasts to the image/analysis_name/fsgd_type_contrast folder
            populating dict with significant MCz data, in order to extract the images
        Args:
            hemi: hemisphere
            analysis_name: as previous defined
            glm_folder: folder where the post FS-GLM files are stores
            fsgd_type_contrast: specific folder in the glm_folder
            contrast: name of the contrast used
            direction: direction of the MCz analysis
            cwsig_mc_f: file with significant MCz results
            oannot_mc_f: file with significant MCz annotations
        Return:
            none
            creates corresponding folder in the self.PATH_img folder
            populates the sig_mc_data dictionary
        '''
        glm_image_dir = os.path.join(self.PATH_img, analysis_name, fsgd_type_contrast)
        if not os.path.exists(glm_image_dir):
            os.makedirs(glm_image_dir)
        shutil.copy(cwsig_mc_f, glm_image_dir)
        shutil.copy(oannot_mc_f, glm_image_dir)
        cwsig_mc_f_copy  = os.path.join(analysis_name, fsgd_type_contrast, cwsig_mc_f.replace(glm_folder+'/', ''))
        oannot_mc_f_copy = os.path.join(analysis_name, fsgd_type_contrast, oannot_mc_f.replace(glm_folder+'/', ''))

        sig_mc_count = len(self.sig_mc_data.keys())+1
        self.sig_mc_data[sig_mc_count] = {
                                'hemi'              : hemi,
                                'analysis_name'     : analysis_name,
                                'contrast'          : contrast,
                                'direction'         : direction,
                                'cwsig_mc_f'        : cwsig_mc_f_copy,
                                'oannot_mc_f'       : oannot_mc_f_copy}


    def files_f4glm_get(self,
                        param):
        # get files_glm.
        files_glm = dict()
        RUN = True

        # get file with subjects per group
        try:
            subjects_per_group = load_json(param.subjects_per_group)
            self.log.info(f'    successfully uploaded file: {param.subjects_per_group}')
            # checking that all subjects are present
            self.log.info(f'    subjects are located in: {self.SUBJECTS_DIR}')
            for group in subjects_per_group:
                for subject in subjects_per_group[group]:
                    if subject not in os.listdir(self.SUBJECTS_DIR):
                        self.log.info(f' subject is missing from FreeSurfer Subjects folder: {subject}')
                        RUN = False
                        break
        except Exception as e:
            self.log.info(e)
            self.log.info(f'    file {param.subjects_per_group} is missing')
            RUN = False

        if RUN:
            try:
                files_glm = load_json(param.files_for_glm)
                self.log.info(f'    successfully uploaded file: {param.files_for_glm}')
                data = dict()
                for contrast_chosen in self.contrast_choice:
                    for i in files_glm.keys():
                        if contrast_chosen in i:
                            data[i] = files_glm[i]
                if self.corrected:
                    data = {i: data[i] for i in data.keys() if "cor" in i}
                self.log.info(f"list of contrasts is: {list(data.keys())}")

                for subdir in (self.PATHglm_glm, self.PATHglm_results, self.PATH_img):
                    if not os.path.isdir(subdir): os.makedirs(subdir)
                if not os.path.isfile(self.sig_contrasts):
                    open(self.sig_contrasts,'w').close()
            except ImportError as e:
                self.log.info(e)
                self.log.info(f'    file {param.files_for_glm} is missing')
                RUN = False

        return data, RUN


    def schedule_send(self,
                      key,
                      cmd,
                      process):
        """Send to scheduler
        Args:
            cmd: str() to send to scheduler
        """
        if send_2scheduler:
            job_id = '0'
            self.log.info(f"sending to scheduler command: {cmd}")
            job_id = self.schedule.submit_4_processing(cmd, key, process,
                                                       activate_fs = True)
            try:
                self.log.info(f'        submited id: {str(job_id)}')
            except Exception as e:
                self.log.info(f'        err in do: {str(e)}')
            self.db['RUNNING_JOBS'][key] = job_id
        else:
            self.log.info(f"sending to system for run command: {cmd}")
            os.system(cmd)


    def get_status_for_subjid_in_queue(self, running_jobs, key):
        scheduler_jobs = self.schedule.get_jobs_status(self.vars_local["USER"]["user"],
                                                        self.db['RUNNING_JOBS'])
        if key in running_jobs:
            job_id = str(running_jobs[key])
            if job_id in scheduler_jobs:
               status = scheduler_jobs[job_id][1]
            else:
               status = 'none'
        else:
            running_jobs, status = self.try_to_infer_jobid(running_jobs, key, scheduler_jobs)
            job_id = '0'
        return running_jobs, status, job_id


    def try_to_infer_jobid(self, running_jobs, key, scheduler_jobs):
        probable_jobids = [i for i in scheduler_jobs if scheduler_jobs[i][0] in key]
        if probable_jobids:
            self.log.info(f'            job_id for subject {key} inferred, probable jobids: {str(probable_jobids[0])}')
            if len(probable_jobids)>1:
                running_jobs[key] = 0
            else:
                running_jobs[key] = probable_jobids[0]
            return running_jobs, 'PD'
        else:
            return running_jobs, 'none'



class ClusterFile2CSV():

    def __init__(self,
                file_abspath,
                result_abspath,
                log):
        from stats.db_processing import Table
        self.contrasts = fs_definitions.GLMcontrasts['contrasts']
        self.get_explanations()

        self.col_4constrasts = "Contrast"
        self.header = ("ClusterNo",
                      "Max", "VtxMax", "Size(mm^2)", 
                      "TalX", "TalY", "TalZ",
                      "CWP", "CWPLow", "CWPHi",
                      "NVtxs", "WghtVtx",
                      "Annot", self.col_4constrasts, "Explanation")
        self.length_matrix = len(self.header)
        self.content = open(file_abspath, 'r').readlines()
        self.result_abspath = result_abspath
        self.tab = Table()
        self.log = log
        self.ls_vals_2chk = self.contrasts.keys()
        self.run()

    def run(self):
        self.log.info('\n\n    CLUSTER FILE: creating the tabular version of statistical file')
        d = dict()
        i = 0
        line_length = 15

        while i < len(self.content):
            line = self.content[i].replace('\n','')
            if self.chk_if_vals_in_line(line):
                expl = self.content[i+1].replace('\n','').replace(';','.')
                ls_vide = list(" "*(line_length - 2))
                d[i] = ls_vide + [line, expl,]
                i += 2
            else:
                line = self.clean_nans_from_list(line.split(' '))
                i += 1
                if len(line) != 0:
                    if len(line) < line_length:
                        ls_vide = list(" " *(line_length - len(line)))
                        line = line + ls_vide
                    d[i] = line
        self.save_2table(d)

    def save_2table(self, d):
        df = self.tab.create_df_from_dict(d).T
        column_names = {i[0]:i[1] for i in list(zip(df.columns, self.header))}
        df = df.rename(columns = column_names)
        df = df.set_index(df[self.col_4constrasts])
        df = df.drop(columns = [self.col_4constrasts])
        self.tab.save_df(df, self.result_abspath)

    def chk_if_vals_in_line(self, line):
        '''will use each value from self.ls_vals_2chk
            if present in the line:
            will return True and break
            else: return False
        '''
        exists     = False

        for val_2chk in self.ls_vals_2chk:
            if val_2chk in line:
                exists = True
                break
        return exists

    def clean_nans_from_list(self, ls):
        for i in ls[::-1]:
            if i == '':
                ls.remove(i)
        return ls

    def get_explanations(self):
        self.explanations = list()
        for key in self.contrasts:
            for file_name in self.contrasts[key]:
                self.explanations.append(self.contrasts[key][file_name][1])


def get_parameters(projects, FS_GLM_DIR):
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

    parser.add_argument(
        "-glm_dir", required=False,
        default=FS_GLM_DIR,
        help="path to GLM folder",
    )

    parser.add_argument(
        "-contrast", required=False, nargs = "+",
        default="g",
        choices = ["g1v0", "g1v1", 'g2v0', "g2v1", 'g3v0', "g3v1"],
        help="path to GLM folder",
    )

    parser.add_argument(
    "-corrected", required=False,
    action = 'store_true',
    help   = "when used, will run only the corrected contrasts",
    )

    parser.add_argument(
        "-permutations", required=False,
        default=1000,
        help="choose number of permutations. default is 1000. usually up to 10000 is chosen. this can increase the computation time up to 10 hours",
    )

    params = parser.parse_args()
    return params


def initiate_fs_from_sh(vars_local):
    """
    FreeSurfer needs to be initiated with source and export
    this functions tries to automate this
    """
    sh_file = os.path.join(vars_local["NIMB_PATHS"]["NIMB_tmp"], 'source_fs.sh')
    with open(sh_file, 'w') as f:
        f.write(vars_local["FREESURFER"]["export_FreeSurfer_cmd"]+'\n')
        f.write("export SUBJECTS_DIR="+vars_local["FREESURFER"]["SUBJECTS_DIR"]+'\n')
        f.write(vars_local["FREESURFER"]["source_FreeSurfer_cmd"]+'\n')
    os.system("chmod +x {}".format(sh_file))
    return ("source {}".format(sh_file))


if __name__ == "__main__":

    import argparse
    try:
        from pathlib import Path
    except ImportError as e:
        print('please install pathlib')
        sys.exit(e)

    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[2]
    sys.path.append(str(top))

    import subprocess
    from distribution.logger import Log
    from distribution.utilities import load_json, save_json
    from setup.get_vars import Get_Vars, SetProject
    from stats.db_processing import Table
    from processing.freesurfer import fs_definitions
    from processing.schedule_helper import Scheduler

    all_vars     = Get_Vars()
    projects     = all_vars.projects
    project_ids  = all_vars.project_ids

    NIMB_tmp     = all_vars.location_vars['local']['NIMB_PATHS']['NIMB_tmp']
    stats_vars   = SetProject(NIMB_tmp,
                                all_vars.stats_vars,
                                project_ids[0],
                                projects).stats

    params       = get_parameters(project_ids,
                                 stats_vars["STATS_PATHS"]["FS_GLM_dir"])

    fs_start_cmd = initiate_fs_from_sh(all_vars.location_vars['local'])
    run_ok = True

    try:
        subprocess.run(['mri_info'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    except Exception as e:
        print(e)
        print(f'ERROR: please initiate freesurfer using the command: \n    {fs_start_cmd}')
        run_ok = False

    if run_ok:
        PerformGLM(all_vars, params, Log, sig_fdr_thresh = 3.0)
