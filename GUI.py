import tkinter
from tkinter import (Tk, ttk, Label, Frame, Button, LabelFrame,INSERT, OptionMenu,
                     Checkbutton, Radiobutton, IntVar,StringVar, Text, HORIZONTAL, END, Entry, Toplevel, Checkbutton,
                     DISABLED, NORMAL)
from tkinter import filedialog as fd
from tkcalendar import Calendar
import tomlkit



class TDarts_GUI():

    def __init__(self):

        self.window = Tk()
        width = 800
        height = 900
        # self.window.geometry("500x900")
        self.window.geometry(str(width)+"x"+str(height))
        self.window.title("Welcome to T-DARTS")

        self.frame = Frame(self.window)
        self.frame.pack()

        ########################################################################
        # create config frame to place our grid
        self.image_config_frame = LabelFrame(self.frame, text="Choose an image configuration:", labelanchor="n")
        self.image_config_frame.grid(row=0, column=0, sticky="news", padx=20, pady=20)

        # image config: "single" or "two in one"
        self.selected_image_configuration = IntVar()
        self.image_config_radiobutton_1 = Radiobutton(self.image_config_frame, text='single', value=1,
                                                      variable=self.selected_image_configuration)
        self.image_config_radiobutton_2 = Radiobutton(self.image_config_frame, text='two in one', value=2,
                                                      variable=self.selected_image_configuration)
        self.image_config_radiobutton_1.grid(row=0, column=0, sticky="W")
        self.image_config_radiobutton_2.grid(row=3, column=0, sticky="W")

        # choose files
        self.selection_button = Button(self.image_config_frame, text="Choose file(s)", command=self.select_files)
        self.selection_button.grid(row=5, column=0, sticky="W")

        # path for "single"
        # path to input channel 1
        self.label_single_path_to_input_channel1 = Label(self.image_config_frame, text="path to input channel 1")
        self.label_single_path_to_input_channel1.grid(row=1, column=0, sticky="W")
        self.text_single_path_to_input_channel1 = Text(self.image_config_frame, height=1, width=30)
        self.text_single_path_to_input_channel1.grid(row=1, column=1, sticky="W")
        # path to input channel 2
        self.label_single_path_to_input_channel2 = Label(self.image_config_frame, text="path to input channel 2")
        self.label_single_path_to_input_channel2.grid(row=2, column=0, sticky="W")
        self.text_single_path_to_input_channel2 = Text(self.image_config_frame, height=1, width=30)
        self.text_single_path_to_input_channel2.grid(row=2, column=1, sticky="W")

        # path for "two in one"
        # path to combined
        self.label_path_to_input_combined = Label(self.image_config_frame, text="path to input combined")
        self.label_path_to_input_combined.grid(row=4, column=0, sticky="W")
        self.text_path_to_input_combined = Text(self.image_config_frame, height=1, width=30)
        self.text_path_to_input_combined.grid(row=4, column=1, sticky="W")

        ######################################################################################
        # create config frame to place our grid
        self.image_result_frame = LabelFrame(self.frame, text="Choose a results directory:", labelanchor="n")
        self.image_result_frame.grid(row=1, column=0, sticky="news", padx=20, pady=20)

        # path to result folder
        self.label_results_directory = Label(self.image_result_frame, text="results directory")
        self.label_results_directory.grid(row=0, column=0, sticky="W")
        self.text_results_directory = Text(self.image_result_frame, height=1, width=30)
        self.text_results_directory.grid(row=0, column=1, sticky="W")
        self.choose_results_directory_button = Button(self.image_result_frame, text="Choose a results directory",
                                                      command=self.choose_results_directory_clicked)
        self.choose_results_directory_button.grid(row=1, column=0, sticky="W")

        #####################################################################################

        # create Properties of measurement frame to place our grid
        self.properties_of_measurement_frame = LabelFrame(self.frame, text="Properties of measurement:",
                                                          labelanchor="n")
        self.properties_of_measurement_frame.grid(row=2, column=0, sticky="news", padx=20, pady=20)

        # microscope
        self.label_microscope_name = Label(self.properties_of_measurement_frame, text="Used microscope:  ")
        self.label_microscope_name.grid(row=0, column=0, sticky="W")
        self.text_microscope = Text(self.properties_of_measurement_frame, height=1, width=30)
        self.text_microscope.grid(row=0, column=1, sticky="W")
        # scale
        self.label_scale = Label(self.properties_of_measurement_frame, text="Scale (microns per pixel):  ")
        self.label_scale.grid(row=1, column=0, sticky="W")
        self.text_scale = Text(self.properties_of_measurement_frame, height=1, width=30)
        self.text_scale.insert(INSERT, "0")
        self.text_scale.grid(row=1, column=1, sticky="W")
        # fps
        self.label_fps = Label(self.properties_of_measurement_frame, text="frame rate (fps):  ")
        self.label_fps.grid(row=2, column=0, sticky="W")
        self.text_fps = Text(self.properties_of_measurement_frame, height=1, width=30)
        self.text_fps.insert(INSERT, "3.0")
        self.text_fps.grid(row=2, column=1, sticky="W")
        # resolution
        self.label_resolution = Label(self.properties_of_measurement_frame, text="Spatial resolution in pixels:  ")
        self.label_resolution.grid(row=3, column=0, sticky="W")
        self.text_resolution = Text(self.properties_of_measurement_frame, height=1, width=30)
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
        self.entry_time = Entry(self.properties_of_measurement_frame)
        self.entry_time.grid(row=5, column=1, sticky="W")
        self.entry_time.insert(0, "yyyy/mm/dd")
        self.entry_time.bind("<1>", self.pick_date)

        ###################################################################################

        # create Pipeline frame to place our grid
        self.label_processing_pipeline = LabelFrame(self.frame, text="Processing pipeline:", labelanchor="n")
        self.label_processing_pipeline.grid(row=3, column=0, sticky="news", padx=20, pady=20)

        self.label_channel_alignment = Label(self.label_processing_pipeline, text="Channel alignment (SITK):  ")
        self.label_channel_alignment.grid(column=1, row=12, sticky="W")
        self.channel_alignment_in_pipeline = IntVar(value=0)
        self.check_box_channel_alignment = Checkbutton(self.label_processing_pipeline,
                                                       variable=self.channel_alignment_in_pipeline,
                                                       onvalue=1, offvalue=0, command=self.update_settings_for_registration)
        self.check_box_channel_alignment.grid(column=2, row=12, sticky="W")

        self.label_frame_by_frame_registration = Label(self.label_processing_pipeline,
                                                       text="Frame-by-Frame registration:  ")
        self.label_frame_by_frame_registration.grid(column=3, row=12, sticky="W")
        self.frame_by_frame_registration = IntVar()
        self.check_box_frame_by_frame_registration = Checkbutton(self.label_processing_pipeline,
                                                                 variable=self.frame_by_frame_registration,
                                                                 onvalue=1, offvalue=0, )
        self.check_box_frame_by_frame_registration.grid(column=4, row=12, sticky="W")

        self.label_deconvolution = Label(self.label_processing_pipeline, text="Deconvolution:  ")
        self.label_deconvolution.grid(column=1, row=13, sticky="W")
        self.deconvolution_in_pipeline = IntVar()
        self.check_box_deconvolution_in_pipeline = Checkbutton(self.label_processing_pipeline,
                                                               variable=self.deconvolution_in_pipeline,
                                                               onvalue=1,
                                                               offvalue=0,
                                                               command=self.update_deconvolution)
        self.check_box_deconvolution_in_pipeline.grid(column=2, row=13, sticky="W")

        deconvolution_algorithms = [
            "LR",
            "TDE"
        ]
        self.deconvolution_algorithm = StringVar(self.label_processing_pipeline)
        self.deconvolution_algorithm.set(deconvolution_algorithms[0])
        self.option_menu_deconvolution = OptionMenu(self.label_processing_pipeline, self.deconvolution_algorithm, *deconvolution_algorithms)
        self.option_menu_deconvolution.config(state=DISABLED)
        self.option_menu_deconvolution.grid(column=3, row=13, sticky="W")

        self.label_bleaching_correction = Label(self.label_processing_pipeline, text="Bleaching correction:  ")
        self.label_bleaching_correction.grid(column=1, row=14, sticky="W")
        self.bleaching_correction_in_pipeline = IntVar()
        self.check_box_bleaching_correction = Checkbutton(self.label_processing_pipeline,
                                                          variable=self.bleaching_correction_in_pipeline,
                                                          onvalue=1,
                                                          offvalue=0,
                                                          command=self.update_bleaching_correction)
        self.check_box_bleaching_correction.grid(column=2, row=14, sticky="W")

        bleaching_correction_algorithms = [
            "additiv"
        ]

        self.bleaching_correction_algorithm = StringVar(self.label_processing_pipeline)
        self.bleaching_correction_algorithm.set(bleaching_correction_algorithms[0])
        self.option_menu_bleaching_correction = OptionMenu(self.label_processing_pipeline, self.bleaching_correction_algorithm,
                                                    *bleaching_correction_algorithms)
        self.option_menu_bleaching_correction.config(state=DISABLED)
        self.option_menu_bleaching_correction.grid(column=3, row=14, sticky="W")

        """
        self.label_dartboard_projection = Label(self.label_processing_pipeline, text="Dartboard projection:  ")
        self.label_dartboard_projection.grid(column=1, row=15, sticky="W")
        self.dartboard_projection_in_pipeline = IntVar()
        self.check_box_dartboard_projection = Checkbutton(self.label_processing_pipeline,
                                                          variable=self.dartboard_projection_in_pipeline,
                                                          onvalue=1, offvalue=0, )
        self.check_box_dartboard_projection.grid(column=2, row=15, sticky="W")
        """

        self.label_further_information = Label(self.label_processing_pipeline, text="Further information:  ")
        self.label_further_information.grid(column=1, row=15, sticky="W")

        self.label_user = Label(self.label_processing_pipeline, text="User:  ")
        self.label_user.grid(column=2, row=15, sticky="W")
        self.text_user = Text(self.label_processing_pipeline, height=1, width=30)
        self.text_user.grid(column=3, row=15, sticky="W")

        self.label_experiment_name = Label(self.label_processing_pipeline, text="Name of experiment:  ")
        self.label_experiment_name.grid(column=1, row=16, sticky="W")
        self.text_experiment_name = Text(self.label_processing_pipeline, height=1, width=30)
        self.text_experiment_name.grid(column=2, row=16, sticky="W")

        ##################################################################################

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

        #################################################################################

        # settings from last run
        self.settings_from_last_run = Button(self.window, text="Use settings from last run",
                                             command=self.get_settings_from_last_run)
        self.settings_from_last_run.place(x=0.09 * width, y=0.9 * height)
        # self.settings_from_last_run.grid(row=5, column=0, sticky="W")

        ################################################################################

        # start button
        self.start_button = Button(self.window, text='Start', command=self.start_analysis)
        self.start_button.place(x=0.5 * width, y=0.9 * height)

        self.cancel_button = Button(self.window, text='Cancel', command=self.cancel)
        self.cancel_button.place(x=0.8 * width, y=0.9 * height)

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
                            date_pattern="y/mm/dd")
        calendar.place(x=0, y=0)
        submit_button = Button(date_window, text='submit', command=self.grab_date)
        submit_button.place(x=80, y=190)

    def get_settings_from_last_run(self):
        with open("config.toml", mode="rt", encoding="utf-8") as fp:
            config = tomlkit.load(fp)
            image_config = self.convert_image_config_to_number(config["properties"]["channel_format"])
            self.selected_image_configuration.set(image_config)

            if config["properties"]["channel_format"] == "single":
                channel1_path = config["inputoutput"]["path_to_input_channel1"]
                self.text_single_path_to_input_channel1.delete(1.0, END)
                self.text_single_path_to_input_channel1.insert(1.0, channel1_path)
                channel2_path = config["inputoutput"]["path_to_input_channel2"]
                self.text_single_path_to_input_channel2.delete(1.0, END)
                self.text_single_path_to_input_channel2.insert(1.0, channel2_path)
            elif config["properties"]["channel_format"] == "two-in-one":
                combined_path = config["inputoutput"]["path_to_input_combined"]
                self.text_path_to_input_combined.delete(1.0, END)
                self.text_path_to_input_combined.insert(1.0, combined_path)

            self.text_user.delete(1.0, END)
            self.text_user.insert(1.0, config["inputoutput"]["user"])

            self.text_experiment_name.delete(1.0, END)
            self.text_experiment_name.insert(1.0, config["properties"]["experiment_name"])

            self.text_results_directory.delete(1.0, END)
            self.text_results_directory.insert(1.0, config["inputoutput"]["path_to_output"])

            self.text_microscope.delete(1.0, END)
            self.text_microscope.insert(1.0, config["properties"]["used_microscope"])

            self.text_scale.delete(1.0, END)
            self.text_scale.insert(1.0, config["properties"]["scale_microns_per_pixel"])

            self.text_fps.delete(1.0, END)
            self.text_fps.insert(1.0, config["properties"]["frames_per_second"])

            self.text_resolution.delete(1.0, END)
            self.text_resolution.insert(1.0, config["properties"]["spatial_resolution"])

            if config["properties"]["registration_in_pipeline"]:
                self.check_box_channel_alignment.select()

            if config["properties"]["registration_framebyframe"]:
                self.check_box_frame_by_frame_registration.select()

            if config["deconvolution"]["deconvolution_in_pipeline"]:
                self.check_box_deconvolution_in_pipeline.select()
                self.deconvolution_algorithm.set(config["deconvolution"]["decon"])
                self.option_menu_deconvolution.config(state=NORMAL)

            if config["properties"]["bleaching_correction_in_pipeline"]:
                self.check_box_bleaching_correction.select()
                self.bleaching_correction_algorithm.set(config["properties"]["bleaching_correction_algorithm"])
                self.option_menu_bleaching_correction.config(state=NORMAL)

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

    def select_files(self):
        chosen_image_configuration = self.get_image_configuration()

        if (chosen_image_configuration == "single"):
            filename_channel1 = fd.askopenfilename()
            self.text_single_path_to_input_channel1.insert(1.0, filename_channel1)
            filename_channel2 = fd.askopenfilename()
            self.text_single_path_to_input_channel2.insert(1.0, filename_channel2)
            self.text_path_to_input_combined.delete('1.0', END)

        elif (chosen_image_configuration == "two-in-one"):
            filename_combined = fd.askopenfilename()
            self.text_path_to_input_combined.insert(1.0, filename_combined)
            self.text_single_path_to_input_channel1.delete('1.0', END)
            self.text_single_path_to_input_channel2.delete('1.0', END)

    def enable_text_boxes(self):
        self.text_path_to_input_combined['state'] = 'normal'
        self.text_single_path_to_input_channel1['state'] = 'normal'
        self.text_single_path_to_input_channel2['state'] = 'normal'

    def disable_text_boxes(self):
        self.text_path_to_input_combined['state'] = 'disabled'
        self.text_single_path_to_input_channel1['state'] = 'disabled'
        self.text_single_path_to_input_channel2['state'] = 'disabled'

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

            if self.get_image_configuration() == "single":
                config["inputoutput"]["path_to_input_channel1"] = self.text_single_path_to_input_channel1.get("1.0",
                                                                                                              "end-1c")
                config["inputoutput"]["path_to_input_channel2"] = self.text_single_path_to_input_channel2.get("1.0",
                                                                                                              "end-1c")
            elif self.get_image_configuration() == "two-in-one":
                config["inputoutput"]["path_to_input_combined"] = self.text_path_to_input_combined.get("1.0", "end-1c")

            config["inputoutput"]["path_to_output"] = self.text_results_directory.get("1.0", "end-1c")

            config["inputoutput"]["user"] = str(self.text_user.get("1.0", "end-1c"))
            config["inputoutput"]["experiment_name"] = self.text_experiment_name.get("1.0", "end-1c")

            config["properties"]["used_microscope"] = str(self.text_microscope.get("1.0", "end-1c"))
            config["properties"]["day_of_measurement"] = str(self.entry_time.get())

            config["properties"]["scale_microns_per_pixel"] = float(self.text_scale.get("1.0", END))
            config["properties"]["frames_per_second"] = float(self.text_fps.get("1.0", END))
            config["properties"]["spatial_resolution"] = int(self.text_resolution.get("1.0", END))

            config["properties"]["registration_framebyframe"] = self.frame_by_frame_registration.get() == 1
            config["properties"]["registration_in_pipeline"] = self.channel_alignment_in_pipeline.get() == 1

            config["deconvolution"]["deconvolution_in_pipeline"] = self.deconvolution_in_pipeline.get() == 1
            config["deconvolution"]["decon"] = str(self.deconvolution_algorithm.get())

            config["properties"]["bleaching_correction_algorithm"] = self.bleaching_correction_algorithm.get()
            config["properties"]["bleaching_correction_in_pipeline"] = self.bleaching_correction_in_pipeline.get() == 1

            config["properties"]["cell_type"] = self.cell_type.get()


            # write back
        with open("config.toml", mode="wt", encoding="utf-8") as fp:
            tomlkit.dump(config, fp)

    def add_cell_type_clicked(self):
        pass

    def run_main_loop(self):
        self.window.mainloop()

    def close_window(self):
        self.window.destroy()