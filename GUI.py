from tkinter import (Tk, Label, Frame, Button, LabelFrame,INSERT, OptionMenu,
                    Radiobutton, IntVar,StringVar, Text, END, Entry, Toplevel, Checkbutton,
                     DISABLED, NORMAL)
from tkinter import filedialog as fd
from tkcalendar import Calendar
import tomlkit



class TDarts_GUI():

    def __init__(self):

        self.window = Tk()
        # self.window.resizable(False, False)
        width = 1300
        height = 900
        self.window.geometry(str(width) + "x" + str(height))


        self.window.title("Welcome to C-DARTS")

        self.frame = Frame(self.window)
        self.frame.pack()


        ########################################################################
        # create config frame to place our grid
        self.input_output_frame = LabelFrame(self.frame, text="Input/Output:", labelanchor="n")
        self.input_output_frame.grid(row=0, column=0, sticky="news", padx=20, pady=20)

        # batch or single processing

        self.label_batch = Label(self.input_output_frame, text="Batch or single processing")
        self.label_batch.grid(column=0, row=0, sticky="W")
        self.select_mode = StringVar(value="file")
        self.choose_single = Radiobutton(self.input_output_frame, text="Select File", variable=self.select_mode, value="file")
        self.choose_single.grid(column=0, row=1, sticky="W")

        self.choose_dir = Radiobutton(self.input_output_frame, text="Select Directory", variable=self.select_mode, value="dir")
        self.choose_dir.grid(column=1, row=1, sticky="W")

        self.label_path = Label(self.input_output_frame, text="path to input", anchor="e")
        self.label_path.grid(row=2, column=0, sticky="E")
        self.text_path = Text(self.input_output_frame, height=1, width=20)
        self.text_path.grid(row=2, column=1, sticky="W")
        self.selection_button = Button(self.input_output_frame, text="Choose files or directory", command=self.select_files_or_directory)
        self.selection_button.grid(row=3, column=0, sticky="W")

        self.empty_label_fd = Label(self.input_output_frame, text="")
        self.empty_label_fd.grid(row=4, column=0, sticky="W")
        # image config: "single" or "two in one"
        self.label_image_configuration = Label(self.input_output_frame, text="Image configuration")
        self.label_image_configuration.grid(column=0, row=5, sticky="W")
        self.label_image_configuration.config(bg='lightgray')

        self.empty_label_cf = Label(self.input_output_frame, text="")
        self.empty_label_cf.grid(row=6, column=0, sticky="W")

        self.selected_image_configuration = IntVar(value=2)

        self.image_config_radiobutton_1 = Radiobutton(self.input_output_frame, text='one file per channel', value=1,
                                                      variable=self.selected_image_configuration)
        self.image_config_radiobutton_1.grid(row=7, column=0, sticky="W")
        self.label_config1 = Label(self.input_output_frame, text="each channel is a separate file")
        self.label_config1.grid(column=1, row=7, sticky="W")
        self.image_config_radiobutton_2 = Radiobutton(self.input_output_frame, text='both channels in one file', value=2,
                                                      variable=self.selected_image_configuration)
        self.image_config_radiobutton_2.grid(row=8, column=0, sticky="W")
        self.label_config2 = Label(self.input_output_frame, text="channels are side-by-side in the same frame or "
                                                                 + "in the channel dimension of bioformats")
        self.label_config2.grid(column=1, row=8, sticky="W")


        self.empty_label_3 = Label(self.input_output_frame, text="")
        self.empty_label_3.grid(row=9, column=0, sticky="W")


        # path to result folder
        self.label_results_directory = Label(self.input_output_frame, text="results directory")
        self.label_results_directory.grid(row=10, column=0, sticky="W")
        self.label_results_directory.config(bg='lightgray')
        self.text_results_directory = Text(self.input_output_frame, height=1, width=20)
        self.text_results_directory.grid(row=11, column=0, sticky="W")
        self.choose_results_directory_button = Button(self.input_output_frame, text="Choose a results directory",
                                                      command=self.choose_results_directory_clicked)
        self.choose_results_directory_button.grid(row=12, column=0, sticky="W")

        #####################################################################################

        # create Properties of measurement frame to place our grid
        self.properties_of_measurement_frame = LabelFrame(self.frame, text="Properties of measurement:",
                                                          labelanchor="n")
        self.properties_of_measurement_frame.grid(row=1, column=0, sticky="news", padx=20, pady=20)

        # microscope
        self.label_microscope_name = Label(self.properties_of_measurement_frame, text="Used microscope:  ")
        self.label_microscope_name.grid(row=0, column=0, sticky="W")
        self.text_microscope = Text(self.properties_of_measurement_frame, height=1, width=20)
        self.text_microscope.grid(row=0, column=1, sticky="W")
        # scale
        self.label_scale = Label(self.properties_of_measurement_frame, text="Scale (Pixels per micron):  ")
        self.label_scale.grid(row=1, column=0, sticky="W")
        self.text_scale = Text(self.properties_of_measurement_frame, height=1, width=20)
        self.text_scale.insert(INSERT, "0")
        self.text_scale.grid(row=1, column=1, sticky="W")
        # fps
        self.label_fps = Label(self.properties_of_measurement_frame, text="frame rate (fps):  ")
        self.label_fps.grid(row=2, column=0, sticky="W")
        self.text_fps = Text(self.properties_of_measurement_frame, height=1, width=20)
        self.text_fps.insert(INSERT, "3.0")
        self.text_fps.grid(row=2, column=1, sticky="W")
        # resolution
        self.label_resolution = Label(self.properties_of_measurement_frame, text="Spatial resolution in pixels:  ")
        self.label_resolution.grid(row=3, column=0, sticky="W")
        self.text_resolution = Text(self.properties_of_measurement_frame, height=1, width=20)
        self.text_resolution.insert(INSERT, "3")
        self.text_resolution.grid(row=3, column=1, sticky="W")

        # cell types
        self.label_cell_type = Label(self.properties_of_measurement_frame, text="Cell type:  ")
        self.label_cell_type.grid(row=4, column=0, sticky="W")
        cell_types = [
            "jurkat",
            "primary",
            "NK"
        ]
        self.cell_type = StringVar(self.properties_of_measurement_frame)
        self.cell_type.set(cell_types[0])
        self.option_menu_cell_types = OptionMenu(self.properties_of_measurement_frame, self.cell_type, *cell_types)
        self.option_menu_cell_types.grid(row=4, column=1, sticky="W")

        # time
        self.label_time = Label(self.properties_of_measurement_frame, text="day of measurement :  ")
        self.label_time.grid(row=5, column=0, sticky="W")
        self.entry_time = Entry(self.properties_of_measurement_frame, width=10)
        self.entry_time.grid(row=5, column=1, sticky="W")
        self.entry_time.insert(0, "yyyy-mm-dd")
        self.entry_time.bind("<1>", self.pick_date)

        # user
        self.label_user = Label(self.properties_of_measurement_frame, text="User:  ")
        self.label_user.grid(column=0, row=6, sticky="W")
        self.text_user = Text(self.properties_of_measurement_frame, height=1, width=20)
        self.text_user.grid(column=1, row=6, sticky="W")

        # name of experiment
        self.label_experiment_name = Label(self.properties_of_measurement_frame, text="Name of experiment:  ")
        self.label_experiment_name.grid(column=0, row=7, sticky="W")
        self.text_experiment_name = Text(self.properties_of_measurement_frame, height=1, width=20)
        self.text_experiment_name.grid(column=1, row=7, sticky="W")

        ###################################################################################

        # create Pipeline frame to place our grid
        self.label_processing_pipeline = LabelFrame(self.frame, text="Processing pipeline:", labelanchor="n")
        self.label_processing_pipeline.grid(row=0, column=1, sticky="news", padx=20, pady=20)

        self.label_postprocessing = Label(self.label_processing_pipeline, text="Postprocessing")
        self.label_postprocessing.grid(column=1, row=12, sticky="W")
        self.label_postprocessing.config(bg='lightgray')

        self.label_channel_alignment = Label(self.label_processing_pipeline, text="Channel alignment (SITK):  ")
        self.label_channel_alignment.grid(column=1, row=13, sticky="W")
        self.channel_alignment_in_pipeline = IntVar(value=0)
        self.check_box_channel_alignment = Checkbutton(self.label_processing_pipeline,
                                                       variable=self.channel_alignment_in_pipeline,
                                                       onvalue=1, offvalue=0, command=self.update_settings_for_registration)
        self.check_box_channel_alignment.grid(column=2, row=13, sticky="W")
        self.check_box_channel_alignment.select()
        self.check_box_channel_alignment.config(state=DISABLED)

        self.label_frame_by_frame_registration = Label(self.label_processing_pipeline,
                                                       text="align each frame?:  ")
        self.label_frame_by_frame_registration.grid(column=3, row=13, sticky="W")
        self.frame_by_frame_registration = IntVar()
        self.check_box_frame_by_frame_registration = Checkbutton(self.label_processing_pipeline,
                                                                 variable=self.frame_by_frame_registration,
                                                                 onvalue=1, offvalue=0, )
        self.check_box_frame_by_frame_registration.grid(column=4, row=13, sticky="W")

        #
        self.label_background_subtraction = Label(self.label_processing_pipeline, text="Background subtraction:  ")
        self.label_background_subtraction.grid(column=1, row=14, sticky="W")
        self.background_subtraction_in_pipeline = IntVar()
        self.check_box_background_subtraction_in_pipeline = Checkbutton(self.label_processing_pipeline,
                                                               variable=self.background_subtraction_in_pipeline,
                                                               onvalue=1,
                                                               offvalue=0,
                                                               command=None)
        self.check_box_background_subtraction_in_pipeline.grid(column=2, row=14, sticky="W")
        self.check_box_background_subtraction_in_pipeline.select()
        self.check_box_background_subtraction_in_pipeline.config(state=DISABLED)

        #
        self.label_segmentation_tracking = Label(self.label_processing_pipeline, text="Cell segmentation/Tracking:  ")
        self.label_segmentation_tracking.grid(column=1, row=15, sticky="W")
        self.segmentation_tracking_in_pipeline = IntVar()
        self.check_box_segmentation_tracking_in_pipeline = Checkbutton(self.label_processing_pipeline,
                                                                        variable=self.segmentation_tracking_in_pipeline,
                                                                        onvalue=1,
                                                                        offvalue=0,
                                                                        command=None)
        self.check_box_segmentation_tracking_in_pipeline.grid(column=2, row=15, sticky="W")
        self.check_box_segmentation_tracking_in_pipeline.select()
        self.check_box_segmentation_tracking_in_pipeline.config(state=DISABLED)
        #
        self.label_deconvolution = Label(self.label_processing_pipeline, text="Deconvolution:  ")
        self.label_deconvolution.grid(column=1, row=16, sticky="W")
        self.deconvolution_in_pipeline = IntVar()
        self.check_box_deconvolution_in_pipeline = Checkbutton(self.label_processing_pipeline,
                                                               variable=self.deconvolution_in_pipeline,
                                                               onvalue=1,
                                                               offvalue=0,
                                                               command=self.update_deconvolution)
        self.check_box_deconvolution_in_pipeline.grid(column=2, row=16, sticky="W")
        self.check_box_deconvolution_in_pipeline.select()
        self.check_box_deconvolution_in_pipeline.config(state=DISABLED)

        deconvolution_algorithms = [
            "LR",
            "TDE"
        ]
        self.deconvolution_algorithm = StringVar(self.label_processing_pipeline)
        self.deconvolution_algorithm.set(deconvolution_algorithms[0])
        self.option_menu_deconvolution = OptionMenu(self.label_processing_pipeline, self.deconvolution_algorithm, *deconvolution_algorithms, command=self.decon_selection_changed)
        # self.option_menu_deconvolution.config(state=DISABLED)
        self.option_menu_deconvolution.grid(column=3, row=16, sticky="W")

        self.label_TDE_lambda = Label(self.label_processing_pipeline, text="lambda (TDE)")
        self.label_TDE_lambda.grid(column=3, row=17, sticky="W")
        self.text_TDE_lambda = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_TDE_lambda.grid(column=4, row=17, sticky="W")
        self.text_TDE_lambda.config(state=DISABLED)

        self.label_TDE_lambda_t = Label(self.label_processing_pipeline, text="lambda t (TDE)")
        self.label_TDE_lambda_t.grid(column=5, row=17, sticky="W")
        self.text_TDE_lambda_t = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_TDE_lambda_t.grid(column=6, row=17, sticky="W")
        self.text_TDE_lambda_t.config(state=DISABLED)

        self.label_psf_type = Label(self.label_processing_pipeline, text="psf: type")
        self.label_psf_type.grid(column=7, row=17, sticky="W")
        self.text_psf_type = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_type.grid(column=8, row=17, sticky="W")


        self.label_psf_lambdaEx_ch1 = Label(self.label_processing_pipeline, text="psf: lambdaEx_ch1")
        self.label_psf_lambdaEx_ch1.grid(column=3, row=18, sticky="W")
        self.text_psf_lambdaEx_ch1 = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_lambdaEx_ch1.grid(column=4, row=18, sticky="W")

        self.label_psf_lambdaEm_ch1 = Label(self.label_processing_pipeline, text="psf: lambdaEm_ch1")
        self.label_psf_lambdaEm_ch1.grid(column=5, row=18, sticky="W")
        self.text_psf_lambdaEm_ch1 = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_lambdaEm_ch1.grid(column=6, row=18, sticky="W")

        self.label_psf_lambdaEx_ch2 = Label(self.label_processing_pipeline, text="psf: lambdaEx_ch2")
        self.label_psf_lambdaEx_ch2.grid(column=7, row=18, sticky="W")
        self.text_psf_lambdaEx_ch2 = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_lambdaEx_ch2.grid(column=8, row=18, sticky="W")

        self.label_psf_lambdaEm_ch2 = Label(self.label_processing_pipeline, text="psf: lambdaEm_ch2")
        self.label_psf_lambdaEm_ch2.grid(column=3, row=19, sticky="W")
        self.text_psf_lambdaEm_ch2 = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_lambdaEm_ch2.grid(column=4, row=19, sticky="W")


        self.label_psf_numAper = Label(self.label_processing_pipeline, text="psf: numAper")
        self.label_psf_numAper.grid(column=5, row=19, sticky="W")
        self.text_psf_numAper= Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_numAper.grid(column=6, row=19, sticky="W")

        self.label_psf_magObj = Label(self.label_processing_pipeline, text="psf: magObj")
        self.label_psf_magObj.grid(column=7, row=19, sticky="W")
        self.text_psf_magObj = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_magObj.grid(column=8, row=19, sticky="W")

        self.label_psf_rindexObj = Label(self.label_processing_pipeline, text="psf: rindexObj")
        self.label_psf_rindexObj.grid(column=3, row=20, sticky="W")
        self.text_psf_rindexObj = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_rindexObj.grid(column=4, row=20, sticky="W")

        self.label_psf_rindexSp = Label(self.label_processing_pipeline, text="psf: rindexSp")
        self.label_psf_rindexSp.grid(column=5, row=20, sticky="W")
        self.text_psf_rindexSp = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_rindexSp.grid(column=6, row=20, sticky="W")

        self.label_psf_ccdSize = Label(self.label_processing_pipeline, text="psf: ccdSize")
        self.label_psf_ccdSize.grid(column=7, row=20, sticky="W")
        self.text_psf_ccdSize = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_ccdSize.grid(column=8, row=20, sticky="W")



        #
        self.label_bead_contact_sites = Label(self.label_processing_pipeline, text="Bead contact:  ")
        self.label_bead_contact_sites.grid(column=1, row=21, sticky="W")
        self.bead_contacts_in_pipeline = IntVar()
        self.check_box_bead_contacts = Checkbutton(self.label_processing_pipeline,
                                                          variable=self.bead_contacts_in_pipeline,
                                                          onvalue=1,
                                                          offvalue=0,
                                                          command=None)
        self.check_box_bead_contacts.grid(column=2, row=21, sticky="W")
        self.check_box_bead_contacts.select()
        self.check_box_bead_contacts.config(state=DISABLED)
        #

        self.label_bleaching_correction = Label(self.label_processing_pipeline, text="Bleaching correction:  ")
        self.label_bleaching_correction.grid(column=1, row=22, sticky="W")
        self.bleaching_correction_in_pipeline = IntVar()
        self.check_box_bleaching_correction = Checkbutton(self.label_processing_pipeline,
                                                          variable=self.bleaching_correction_in_pipeline,
                                                          onvalue=1,
                                                          offvalue=0,
                                                          command=self.update_bleaching_correction)
        self.check_box_bleaching_correction.grid(column=2, row=22, sticky="W")
        self.check_box_bleaching_correction.select()
        self.check_box_bleaching_correction.config(state=DISABLED)

        bleaching_correction_algorithms = [
            "additiv no fit"
        ]

        self.bleaching_correction_algorithm = StringVar(self.label_processing_pipeline)
        self.bleaching_correction_algorithm.set(bleaching_correction_algorithms[0])
        self.option_menu_bleaching_correction = OptionMenu(self.label_processing_pipeline, self.bleaching_correction_algorithm,
                                                    *bleaching_correction_algorithms)
        # self.option_menu_bleaching_correction.config(state=DISABLED)
        self.option_menu_bleaching_correction.grid(column=3, row=22, sticky="W")
        #
        self.label_ratio_generation = Label(self.label_processing_pipeline, text="Ratio images:  ")
        self.label_ratio_generation.grid(column=1, row=23, sticky="W")
        self.ratio_generation_in_pipeline = IntVar()
        self.check_box_ratio_generation = Checkbutton(self.label_processing_pipeline,
                                                          variable=self.ratio_generation_in_pipeline,
                                                          onvalue=1,
                                                          offvalue=0,
                                                          command=None)
        self.check_box_ratio_generation.grid(column=2, row=23, sticky="W")
        self.check_box_ratio_generation.select()
        self.check_box_ratio_generation.config(state=DISABLED)

        self.empty_label = Label(self.label_processing_pipeline, text="")
        self.empty_label.grid(column=1, row=24, sticky="W")

        self.label_shape_normalization = Label(self.label_processing_pipeline, text="Shape Normalization")
        self.label_shape_normalization.grid(column=1, row=25, sticky="W")
        self.label_shape_normalization.config(bg='lightgray')


        self.shape_normalization_in_pipeline = IntVar()
        self.check_box_shape_normalization = Checkbutton(self.label_processing_pipeline,
                                                      variable=self.shape_normalization_in_pipeline,
                                                      onvalue=1,
                                                      offvalue=0,
                                                      command=None)
        self.check_box_shape_normalization.grid(column=2, row=25, sticky="W")
        self.check_box_shape_normalization.select()
        self.check_box_shape_normalization.config(state=DISABLED)

        self.empty_label_2 = Label(self.label_processing_pipeline, text="")
        self.empty_label_2.grid(column=1, row=26, sticky="W")

        self.label_analysis = Label(self.label_processing_pipeline, text="Analysis")
        self.label_analysis.grid(column=1, row=27, sticky="W")
        self.label_analysis.config(bg='lightgray')

        self.label_hotspot_detection = Label(self.label_processing_pipeline, text="Hotspot detection:  ")
        self.label_hotspot_detection.grid(column=1, row=28, sticky="W")
        self.hotspot_detection_in_pipeline = IntVar()
        self.check_box_hotspot_detection= Checkbutton(self.label_processing_pipeline,
                                                      variable=self.hotspot_detection_in_pipeline,
                                                      onvalue=1,
                                                      offvalue=0,
                                                      command=None)
        self.check_box_hotspot_detection.grid(column=2, row=28, sticky="W")
        self.check_box_hotspot_detection.select()
        self.check_box_hotspot_detection.config(state=DISABLED)

        self.label_dartboard_projection = Label(self.label_processing_pipeline, text="Dartboard projection:  ")
        self.label_dartboard_projection.grid(column=1, row=29, sticky="W")
        self.dartboard_projection_in_pipeline = IntVar()
        self.check_box_dartboard_projection = Checkbutton(self.label_processing_pipeline,
                                                       variable=self.dartboard_projection_in_pipeline,
                                                       onvalue=1,
                                                       offvalue=0,
                                                       command=None)
        self.check_box_dartboard_projection.grid(column=2, row=29, sticky="W")
        self.check_box_dartboard_projection.select()
        self.check_box_dartboard_projection.config(state=DISABLED)

        self.empty_label_3 = Label(self.label_processing_pipeline, text="")
        self.empty_label_3.grid(column=1, row=30, sticky="W")

        # select all/default settings button
        self.default_settings_button = Button(self.label_processing_pipeline, text='Default settings', command=self.default_processing_settings)
        self.default_settings_button.grid(column=1, row=31, sticky="W")

        ##################################################################################
        """
        # create Properties of measurement frame to place our grid
        self.processing_mode_frame = LabelFrame(self.frame, text="Choose a processing mode:", labelanchor="n")
        self.processing_mode_frame.grid(row=4, column=0, sticky="news", padx=20, pady=20)
        self.processing_mode = IntVar()
        self.processing_mode_radiobutton_1 = Radiobutton(self.processing_mode_frame, text='single measurement', value=1,
                                                         variable=self.processing_mode)
        self.processing_mode_radiobutton_2 = Radiobutton(self.processing_mode_frame, text='batch processing', value=2,
                                                         variable=self.processing_mode)
        self.processing_mode_radiobutton_1.grid(row=0, column=0, sticky="W")
        self.processing_mode_radiobutton_2.grid(row=1, column=0, sticky="W")
        """
        #################################################################################
        # create Pipeline frame to place our grid
        self.label_control_buttons = LabelFrame(self.frame, text="Control buttons:", labelanchor="n")
        self.label_control_buttons.grid(row=1, column=1, sticky="news", padx=20, pady=20)

        # settings from last run
        self.settings_from_last_run = Button(self.label_control_buttons, text="Use settings from last run",
                                             command=self.get_settings_from_last_run)

        self.settings_from_last_run.grid(column=1, row=0, sticky="W")



        ################################################################################


        self.start_button = Button(self.label_control_buttons, text='Start', command=self.start_analysis)
        self.start_button.grid(column=1, row=1, sticky="W")

        # cancel button
        self.cancel_button = Button(self.label_control_buttons, text='Cancel', command=self.cancel)
        self.cancel_button.grid(column=1, row=2, sticky="W")

        # cancel button
        self.reinit_button = Button(self.label_control_buttons, text='Reinitialize', command=None)
        self.reinit_button.grid(column=1, row=3, sticky="W")

    def pick_date(self, event):
        global calendar, date_window

        date_window = Toplevel()
        date_window.grab_set()
        date_window.title("Choose date of measurement")
        date_window.geometry('270x220+590+370')
        calendar = Calendar(date_window,
                            selectmode="day",
                            background="black",
                            foreground="gray",
                            normalbackground="black",
                            selectedbackground="gray",
                            date_pattern="y-mm-dd")
        calendar.place(x=0, y=0)
        submit_button = Button(date_window, text='submit', command=self.grab_date)
        submit_button.place(x=80, y=190)

    def get_settings_from_last_run(self):
        with open("config.toml", mode="rt", encoding="utf-8") as fp:
            config = tomlkit.load(fp)
            image_config = self.convert_image_config_to_number(config["properties"]["channel_format"])
            self.selected_image_configuration.set(image_config)

            self.text_path.insert(1.0, config["inputoutput"]["input_path"])

            #if config["properties"]["channel_format"] == "single":
            #    channel1_path = config["inputoutput"]["path_to_input_channel1"]
            #    self.text_single_path_to_input_channel1.delete(1.0, END)
            #    self.text_single_path_to_input_channel1.insert(1.0, channel1_path)
            #    channel2_path = config["inputoutput"]["path_to_input_channel2"]
            #    self.text_single_path_to_input_channel2.delete(1.0, END)
            #    self.text_single_path_to_input_channel2.insert(1.0, channel2_path)
            #elif config["properties"]["channel_format"] == "two-in-one":
            #    combined_path = config["inputoutput"]["path_to_input_combined"]
            #    self.text_path_to_input_combined.delete(1.0, END)
            #    self.text_path_to_input_combined.insert(1.0, combined_path)

            self.text_user.delete(1.0, END)
            self.text_user.insert(1.0, config["inputoutput"]["user"])

            self.text_experiment_name.delete(1.0, END)
            self.text_experiment_name.insert(1.0, config["inputoutput"]["experiment_name"])

            self.text_results_directory.delete(1.0, END)
            self.text_results_directory.insert(1.0, config["inputoutput"]["path_to_output"])

            self.text_microscope.delete(1.0, END)
            self.text_microscope.insert(1.0, config["properties"]["used_microscope"])

            self.text_scale.delete(1.0, END)
            self.text_scale.insert(1.0, config["properties"]["scale_pixels_per_micron"])

            self.text_fps.delete(1.0, END)
            self.text_fps.insert(1.0, config["properties"]["frames_per_second"])

            self.text_resolution.delete(1.0, END)
            self.text_resolution.insert(1.0, config["properties"]["spatial_resolution"])

            if config["properties"]["registration_in_pipeline"]:
                self.check_box_channel_alignment.select()
            else:
                self.check_box_channel_alignment.deselect()

            if config["properties"]["registration_framebyframe"]:
                self.check_box_frame_by_frame_registration.select()
            else:
                self.check_box_frame_by_frame_registration.deselect()

            if config["deconvolution"]["deconvolution_in_pipeline"]:
                self.check_box_deconvolution_in_pipeline.select()
                self.deconvolution_algorithm.set(config["deconvolution"]["decon"])
                self.option_menu_deconvolution.config(state=NORMAL)
                if self.deconvolution_algorithm.get() == "TDE":
                    self.text_TDE_lambda.config(state=NORMAL)
                    self.text_TDE_lambda_t.config(state=NORMAL)
                    self.text_TDE_lambda.delete(1.0, END)
                    self.text_TDE_lambda.insert(1.0, config["deconvolution"]["lambda"])
                    self.text_TDE_lambda_t.delete(1.0, END)
                    self.text_TDE_lambda_t.insert(1.0, config["deconvolution"]["lambda_t"])
                self.text_psf_type.delete(1.0, END)
                self.text_psf_type.insert(1.0, config["psf"]["type"])
                self.text_psf_lambdaEx_ch1.delete(1.0, END)
                self.text_psf_lambdaEx_ch1.insert(1.0, config["psf"]["lambdaEx_ch1"])
                self.text_psf_lambdaEm_ch1.delete(1.0, END)
                self.text_psf_lambdaEm_ch1.insert(1.0, config["psf"]["lambdaEm_ch1"])
                self.text_psf_lambdaEx_ch2.delete(1.0, END)
                self.text_psf_lambdaEx_ch2.insert(1.0, config["psf"]["lambdaEx_ch2"])
                self.text_psf_lambdaEm_ch2.delete(1.0, END)
                self.text_psf_lambdaEm_ch2.insert(1.0, config["psf"]["lambdaEm_ch2"])
                self.text_psf_numAper.delete(1.0, END)
                self.text_psf_numAper.insert(1.0, config["psf"]["numAper"])
                self.text_psf_magObj.delete(1.0, END)
                self.text_psf_magObj.insert(1.0, config["psf"]["magObj"])
                self.text_psf_rindexObj.delete(1.0, END)
                self.text_psf_rindexObj.insert(1.0, config["psf"]["rindexObj"])
                self.text_psf_rindexSp.delete(1.0, END)
                self.text_psf_rindexSp.insert(1.0, config["psf"]["rindexSp"])
                self.text_psf_ccdSize.delete(1.0, END)
                self.text_psf_ccdSize.insert(1.0, config["psf"]["ccdSize"])




            else:
                self.check_box_deconvolution_in_pipeline.deselect()

            if config["properties"]["bleaching_correction_in_pipeline"]:
                self.check_box_bleaching_correction.select()
                self.bleaching_correction_algorithm.set(config["properties"]["bleaching_correction_algorithm"])
                self.option_menu_bleaching_correction.config(state=NORMAL)
            else:
                self.check_box_bleaching_correction.deselect()

            self.cell_type.set(config["properties"]["cell_type"])
            self.entry_time.delete(0, END)
            self.entry_time.insert(0, config["properties"]["day_of_measurement"])





    def grab_date(self):
        self.entry_time.delete(0, END)
        self.entry_time.insert(0, calendar.get_date())
        date_window.destroy()

    def start_analysis(self):
        self.write_input_to_config_file()
        self.close_window()

    def cancel(self):
        self.window.destroy()
        quit()


    def update_settings_for_registration(self):
        if self.channel_alignment_in_pipeline.get() == 0:
            self.frame_by_frame_registration.set(0)
            self.check_box_frame_by_frame_registration.config(state=DISABLED)
        elif self.channel_alignment_in_pipeline.get() == 1:
            self.check_box_frame_by_frame_registration.config(state=NORMAL)

    def update_deconvolution(self):
        if self.deconvolution_in_pipeline.get() == 0:
            self.option_menu_deconvolution.config(state=DISABLED)
        elif self.deconvolution_in_pipeline.get() == 1:
            self.option_menu_deconvolution.config(state=NORMAL)

    def update_bleaching_correction(self):
        if self.bleaching_correction_in_pipeline.get() == 0:
            self.option_menu_bleaching_correction.config(state=DISABLED)
        elif self.bleaching_correction_in_pipeline.get() == 1:
            self.option_menu_bleaching_correction.config(state=NORMAL)

    def get_image_configuration(self):
        if self.selected_image_configuration.get() == 1:
            return "single"
        if self.selected_image_configuration.get() == 2:
            return "two-in-one"
        else:
            return "no configuration chosen"

    def convert_image_config_to_number(self, image_config):
        if image_config == "single":
            return 1
        elif image_config == "two-in-one":
            return 2
        else:
            return None

    def decon_selection_changed(self, event):
        chosen_decon_algorithm = self.deconvolution_algorithm.get()
        if chosen_decon_algorithm == "TDE":
            self.text_TDE_lambda.config(state=NORMAL)
            self.text_TDE_lambda_t.config(state=NORMAL)
        elif chosen_decon_algorithm =="LR":
            self.text_TDE_lambda.delete(1.0, END)
            self.text_TDE_lambda.config(state=DISABLED)
            self.text_TDE_lambda_t.delete(1.0, END)
            self.text_TDE_lambda_t.config(state=DISABLED)

    #def select_directory(self):
    #    chosen_image_configuration = self.get_image_configuration()

    #    if (chosen_image_configuration == "single"):
    #        #filename_channel1 = fd.askdirectory()
    #        filename_channel1 = fd.askopenfilename(title="Select a File or Directory",
    #                                  filetypes=[("All files and directories", "*.*")])
    #        #self.text_single_path_to_input_channel1.delete('1.0', END)
    #        self.text_single_path_to_input_channel1.insert(1.0, filename_channel1)
    #        filename_channel2 = fd.askopenfilename(title="Select a File or Directory",
    #                                               filetypes=[("All files and directories", "*.*")])
    #        #self.text_single_path_to_input_channel2.delete('1.0', END)
    #        self.text_single_path_to_input_channel2.insert(1.0, filename_channel2)
    #        #self.text_path_to_input_combined.delete('1.0', END)

    #    elif (chosen_image_configuration == "two-in-one"):
    #        #filename_combined = fd.askopenfilename(title="Select a File or Directory",
    #        #                                       filetypes=[("All files and directories", "*.*")])
    #        filename_combined = fd.askopenfilenames()
    #        #filename_combined = fd.askdirectory()
    #        self.text_path_to_input_combined.delete('1.0', END)
    #        self.text_path_to_input_combined.insert(1.0, filename_combined)
    #        self.text_single_path_to_input_channel1.delete('1.0', END)
    #        self.text_single_path_to_input_channel2.delete('1.0', END)

    def select_files_or_directory(self):
        if self.select_mode.get() == "file":
            paths = fd.askopenfilename(title="Select File")
        else:
            paths = fd.askdirectory(title="Select Directory")

        self.text_path.delete('1.0', END)
        self.text_path.insert(1.0, paths)

    #def enable_text_boxes(self):
    #    self.text_path_to_input_combined['state'] = 'normal'
    #    self.text_single_path_to_input_channel1['state'] = 'normal'
    #    self.text_single_path_to_input_channel2['state'] = 'normal'

    #def disable_text_boxes(self):
    #    self.text_path_to_input_combined['state'] = 'disabled'
    #    self.text_single_path_to_input_channel1['state'] = 'disabled'
    #    self.text_single_path_to_input_channel2['state'] = 'disabled'

    def default_processing_settings(self):
        self.check_box_frame_by_frame_registration.deselect()
        self.deconvolution_algorithm.set('LR')
        self.bleaching_correction_algorithm.set('additiv no fit')


        self.text_psf_type.delete(1.0, END)
        self.text_psf_type.insert(1.0, "confocal")
        self.text_psf_lambdaEx_ch1.delete(1.0, END)
        self.text_psf_lambdaEx_ch1.insert(1.0, "488")
        self.text_psf_lambdaEm_ch1.delete(1.0, END)
        self.text_psf_lambdaEm_ch1.insert(1.0, "520")
        self.text_psf_lambdaEx_ch2.delete(1.0, END)
        self.text_psf_lambdaEx_ch2.insert(1.0, "488")
        self.text_psf_lambdaEm_ch2.delete(1.0, END)
        self.text_psf_lambdaEm_ch2.insert(1.0, "600")
        self.text_psf_numAper.delete(1.0, END)
        self.text_psf_numAper.insert(1.0, "1.4")
        self.text_psf_magObj.delete(1.0, END)
        self.text_psf_magObj.insert(1.0, "100")
        self.text_psf_rindexObj.delete(1.0, END)
        self.text_psf_rindexObj.insert(1.0, "1.518")
        self.text_psf_rindexSp.delete(1.0, END)
        self.text_psf_rindexSp.insert(1.0, "1.518")
        self.text_psf_ccdSize.delete(1.0, END)
        self.text_psf_ccdSize.insert(1.0, "6450")


    def choose_results_directory_clicked(self):
        self.select_results_directory()

    def select_results_directory(self):
        results_directory = fd.askdirectory()
        self.text_results_directory.delete('1.0', END)
        self.text_results_directory.insert(1.0, results_directory)

    def write_input_to_config_file(self):
        with open("config.toml", mode="rt", encoding="utf-8") as fp:
            config = tomlkit.load(fp)

            config["properties"]["channel_format"] = self.get_image_configuration()
            config["inputoutput"]["input_path"] = self.text_path.get("1.0", "end-1c")

            #if self.get_image_configuration() == "single":
            #    config["inputoutput"]["path_to_input_channel1"] = self.text_single_path_to_input_channel1.get("1.0",
            #                                                                                                  "end-1c")
            #    config["inputoutput"]["path_to_input_channel2"] = self.text_single_path_to_input_channel2.get("1.0",
            #                                                                                                  "end-1c")
            #elif self.get_image_configuration() == "two-in-one":
            #    config["inputoutput"]["path_to_input_combined"] = self.text_path_to_input_combined.get("1.0", "end-1c")

            config["inputoutput"]["path_to_output"] = self.text_results_directory.get("1.0", "end-1c")

            config["inputoutput"]["user"] = str(self.text_user.get("1.0", "end-1c"))
            config["inputoutput"]["experiment_name"] = str(self.text_experiment_name.get("1.0", "end-1c"))

            config["properties"]["used_microscope"] = str(self.text_microscope.get("1.0", "end-1c"))
            config["properties"]["day_of_measurement"] = str(self.entry_time.get())

            config["properties"]["scale_pixels_per_micron"] = float(self.text_scale.get("1.0", END))
            config["properties"]["frames_per_second"] = float(self.text_fps.get("1.0", END))
            config["properties"]["spatial_resolution"] = int(self.text_resolution.get("1.0", END))

            config["properties"]["registration_framebyframe"] = self.frame_by_frame_registration.get() == 1
            config["properties"]["registration_in_pipeline"] = self.channel_alignment_in_pipeline.get() == 1

            config["deconvolution"]["deconvolution_in_pipeline"] = self.deconvolution_in_pipeline.get() == 1
            config["deconvolution"]["decon"] = str(self.deconvolution_algorithm.get())
            if self.deconvolution_algorithm.get() == "TDE":
                config["deconvolution"]["lambda"] = self.text_TDE_lambda.get("1.0", "end-1c")
                config["deconvolution"]["lambda_t"] = self.text_TDE_lambda_t.get("1.0", "end-1c")

            config["properties"]["bleaching_correction_algorithm"] = self.bleaching_correction_algorithm.get()
            config["properties"]["bleaching_correction_in_pipeline"] = self.bleaching_correction_in_pipeline.get() == 1

            config["properties"]["cell_type"] = self.cell_type.get()

            config["psf"]["type"] = str(self.text_psf_type.get("1.0", "end-1c"))
            config["psf"]["lambdaEx_ch1"] = int(self.text_psf_lambdaEx_ch1.get("1.0", END))
            config["psf"]["lambdaEm_ch1"] = int(self.text_psf_lambdaEm_ch1.get("1.0", END))
            config["psf"]["lambdaEx_ch2"] = int(self.text_psf_lambdaEx_ch2.get("1.0", END))
            config["psf"]["lambdaEm_ch2"] = int(self.text_psf_lambdaEm_ch2.get("1.0", END))
            config["psf"]["numAper"] = float(self.text_psf_numAper.get("1.0", END))
            config["psf"]["magObj"] = int(self.text_psf_magObj.get("1.0", END))
            config["psf"]["rindexObj"] = float(self.text_psf_rindexObj.get("1.0", END))
            config["psf"]["rindexSp"] = float(self.text_psf_rindexSp.get("1.0", END))
            config["psf"]["ccdSize"] = int(self.text_psf_ccdSize.get("1.0", END))


            # write back
        with open("config.toml", mode="wt", encoding="utf-8") as fp:
            tomlkit.dump(config, fp)

    def add_cell_type_clicked(self):
        pass

    def run_main_loop(self):
        self.window.mainloop()

    def close_window(self):
        self.window.destroy()