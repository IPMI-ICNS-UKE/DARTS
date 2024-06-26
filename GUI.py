import tkinter.filedialog
from tkinter import (Tk, Label, Frame, Button, LabelFrame,INSERT, OptionMenu,
                    Radiobutton, IntVar,StringVar, Text, END, Entry, Toplevel, Checkbutton,
                     DISABLED, NORMAL, Listbox, LEFT, BOTH, simpledialog, messagebox)
from tkinter import filedialog as fd
from tkcalendar import Calendar
import tomlkit
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg)
import webbrowser

class TDarts_GUI():

    def __init__(self):

        self.window = Tk()
        # self.window.resizable(False, False)
        width = 1650
        height = 1000
        self.window.geometry(str(width) + "x" + str(height))


        self.window.title("Welcome to DARTS")

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
        self.choose_single = Radiobutton(self.input_output_frame, text="Select File", variable=self.select_mode,
                                         value="file")
        self.choose_single.grid(column=0, row=1, sticky="W")

        self.choose_dir = Radiobutton(self.input_output_frame, text="Select Directory", variable=self.select_mode,
                                      value="dir")
        self.choose_dir.grid(column=1, row=1, sticky="W")

        self.label_path = Label(self.input_output_frame, text="path to input", anchor="e")
        self.label_path.grid(row=2, column=0, sticky="E")
        self.text_path = Text(self.input_output_frame, height=1, width=20)
        self.text_path.grid(row=2, column=1, sticky="W")
        self.selection_button = Button(self.input_output_frame, text="Choose files or directory",
                                       command=self.select_files_or_directory)
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
        self.image_config_radiobutton_2 = Radiobutton(self.input_output_frame, text='both channels in one file',
                                                      value=2,
                                                      variable=self.selected_image_configuration)
        self.image_config_radiobutton_2.grid(row=8, column=0, sticky="W")
        self.label_config2 = Label(self.input_output_frame, text="channels are side-by-side in the same frame or "
                                                                 + "\n" +  "in the channel dimension of bioformats")
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
        self.cell_types = [
            "jurkat",
            "primary",
            "NK"
        ]
        self.cell_type = StringVar(self.properties_of_measurement_frame)
        self.cell_type.set(self.cell_types[0])
        self.option_menu_cell_types = OptionMenu(self.properties_of_measurement_frame, self.cell_type, *self.cell_types)
        self.option_menu_cell_types.grid(row=4, column=1, sticky="W")

        self.manage_cell_types_button = Button(self.properties_of_measurement_frame, text="Manage cell types", command=self.manage_cell_types)
        self.manage_cell_types_button.grid(row=4, column=2, sticky="W")

        self.cell_type_manager = CellTypeManager(self.window, self.cell_types, self.option_menu_cell_types,
                                                 self.cell_type)

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

        # global or local measurement
        self.label_global_or_local = Label(self.properties_of_measurement_frame, text="Imaging intention")
        self.label_global_or_local.grid(column=0, row=8, sticky="W")
        self.local_or_global = StringVar(value="local")
        self.choose_local = Radiobutton(self.properties_of_measurement_frame, text="local imaging (microdomains)", variable=self.local_or_global,
                                         value="local", command=self.set_default_settings_for_local_imaging)
        self.choose_local.grid(column=0, row=9, sticky="W")

        self.choose_global = Radiobutton(self.properties_of_measurement_frame, text="global imaging (ratio)", variable=self.local_or_global,
                                      value="global", command=self.set_default_settings_for_global_imaging)
        self.choose_global.grid(column=1, row=9, sticky="W")

        # Bead contacts involved
        self.label_bead_contact_sites = Label(self.properties_of_measurement_frame, text="Bead contact:  ")
        self.label_bead_contact_sites.grid(column=0, row=10, sticky="W")
        self.bead_contacts_in_pipeline = IntVar()
        self.check_box_bead_contacts = Checkbutton(self.properties_of_measurement_frame,
                                                   variable=self.bead_contacts_in_pipeline,
                                                   onvalue=1,
                                                   offvalue=0,
                                                   command=self.update_bead_contact)
        self.check_box_bead_contacts.grid(column=1, row=10, sticky="W")
        self.check_box_bead_contacts.select()
        # self.check_box_bead_contacts.config(state=DISABLED)

        # duration of measurement before bead contact/starting point
        self.label_duration_before = Label(self.properties_of_measurement_frame, text="Measured seconds before starting" + "\n" +"point, e.g. bead contact:")
        self.label_duration_before.grid(column=0, row=11, sticky="W")
        self.text_duration_before = Text(self.properties_of_measurement_frame, height=1, width=20)
        self.text_duration_before.grid(column=1, row=11, sticky="W")

        # duration of measurement after bead contact/starting point
        self.label_duration_after = Label(self.properties_of_measurement_frame, text="Measured seconds after starting" + "\n" +"point, e.g. bead contact:")
        self.label_duration_after.grid(column=0, row=12, sticky="W")
        self.text_duration_after = Text(self.properties_of_measurement_frame, height=1, width=20)
        self.text_duration_after.grid(column=1, row=12, sticky="W")

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
        # self.check_box_channel_alignment.config(state=DISABLED)

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
        # self.check_box_background_subtraction_in_pipeline.config(state=DISABLED)

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
        # self.check_box_deconvolution_in_pipeline.config(state=DISABLED)

        deconvolution_algorithms = [
            "LR",
            "TDE"
        ]
        self.deconvolution_algorithm = StringVar(self.label_processing_pipeline)
        self.deconvolution_algorithm.set(deconvolution_algorithms[0])
        self.option_menu_deconvolution = OptionMenu(self.label_processing_pipeline, self.deconvolution_algorithm, *deconvolution_algorithms, command=self.decon_selection_changed)
        # self.option_menu_deconvolution.config(state=DISABLED)
        self.option_menu_deconvolution.grid(column=3, row=16, sticky="W")

        self.deconvolution_text_boxes = []

        self.label_TDE_lambda = Label(self.label_processing_pipeline, text="lambda (TDE)")
        self.label_TDE_lambda.grid(column=3, row=17, sticky="W")
        self.text_TDE_lambda = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_TDE_lambda.grid(column=4, row=17, sticky="W")
        self.text_TDE_lambda.config(state=DISABLED)
        self.deconvolution_text_boxes.append(self.text_TDE_lambda)

        self.label_TDE_lambda_t = Label(self.label_processing_pipeline, text="lambda t (TDE)")
        self.label_TDE_lambda_t.grid(column=5, row=17, sticky="W")
        self.text_TDE_lambda_t = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_TDE_lambda_t.grid(column=6, row=17, sticky="W")
        self.text_TDE_lambda_t.config(state=DISABLED)
        self.deconvolution_text_boxes.append(self.text_TDE_lambda_t)

        self.label_psf_type = Label(self.label_processing_pipeline, text="psf: type")
        self.label_psf_type.grid(column=7, row=17, sticky="W")
        self.text_psf_type = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_type.grid(column=8, row=17, sticky="W")
        self.deconvolution_text_boxes.append(self.text_psf_type)


        self.label_psf_lambdaEx_ch1 = Label(self.label_processing_pipeline, text="psf: lambdaEx_ch1")
        self.label_psf_lambdaEx_ch1.grid(column=3, row=18, sticky="W")
        self.text_psf_lambdaEx_ch1 = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_lambdaEx_ch1.grid(column=4, row=18, sticky="W")
        self.deconvolution_text_boxes.append(self.text_psf_lambdaEx_ch1)

        self.label_psf_lambdaEm_ch1 = Label(self.label_processing_pipeline, text="psf: lambdaEm_ch1")
        self.label_psf_lambdaEm_ch1.grid(column=5, row=18, sticky="W")
        self.text_psf_lambdaEm_ch1 = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_lambdaEm_ch1.grid(column=6, row=18, sticky="W")
        self.deconvolution_text_boxes.append(self.text_psf_lambdaEm_ch1)

        self.label_psf_lambdaEx_ch2 = Label(self.label_processing_pipeline, text="psf: lambdaEx_ch2")
        self.label_psf_lambdaEx_ch2.grid(column=7, row=18, sticky="W")
        self.text_psf_lambdaEx_ch2 = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_lambdaEx_ch2.grid(column=8, row=18, sticky="W")
        self.deconvolution_text_boxes.append(self.text_psf_lambdaEx_ch2)

        self.label_psf_lambdaEm_ch2 = Label(self.label_processing_pipeline, text="psf: lambdaEm_ch2")
        self.label_psf_lambdaEm_ch2.grid(column=3, row=19, sticky="W")
        self.text_psf_lambdaEm_ch2 = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_lambdaEm_ch2.grid(column=4, row=19, sticky="W")
        self.deconvolution_text_boxes.append(self.text_psf_lambdaEm_ch2)

        self.label_psf_numAper = Label(self.label_processing_pipeline, text="psf: numAper")
        self.label_psf_numAper.grid(column=5, row=19, sticky="W")
        self.text_psf_numAper= Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_numAper.grid(column=6, row=19, sticky="W")
        self.deconvolution_text_boxes.append(self.text_psf_numAper)

        self.label_psf_magObj = Label(self.label_processing_pipeline, text="psf: magObj")
        self.label_psf_magObj.grid(column=7, row=19, sticky="W")
        self.text_psf_magObj = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_magObj.grid(column=8, row=19, sticky="W")
        self.deconvolution_text_boxes.append(self.text_psf_magObj)

        self.label_psf_rindexObj = Label(self.label_processing_pipeline, text="psf: rindexObj")
        self.label_psf_rindexObj.grid(column=3, row=20, sticky="W")
        self.text_psf_rindexObj = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_rindexObj.grid(column=4, row=20, sticky="W")
        self.deconvolution_text_boxes.append(self.text_psf_rindexObj)

        self.label_psf_rindexSp = Label(self.label_processing_pipeline, text="psf: rindexSp")
        self.label_psf_rindexSp.grid(column=5, row=20, sticky="W")
        self.text_psf_rindexSp = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_rindexSp.grid(column=6, row=20, sticky="W")
        self.deconvolution_text_boxes.append(self.text_psf_rindexSp)

        self.label_psf_ccdSize = Label(self.label_processing_pipeline, text="psf: ccdSize")
        self.label_psf_ccdSize.grid(column=7, row=20, sticky="W")
        self.text_psf_ccdSize = Text(self.label_processing_pipeline, height=1, width=10)
        self.text_psf_ccdSize.grid(column=8, row=20, sticky="W")
        self.deconvolution_text_boxes.append(self.text_psf_ccdSize)

        #

        self.label_bleaching_correction = Label(self.label_processing_pipeline, text="Bleaching correction:  ")
        self.label_bleaching_correction.grid(column=1, row=21, sticky="W")
        self.bleaching_correction_in_pipeline = IntVar()
        self.check_box_bleaching_correction = Checkbutton(self.label_processing_pipeline,
                                                          variable=self.bleaching_correction_in_pipeline,
                                                          onvalue=1,
                                                          offvalue=0,
                                                          command=self.update_bleaching_correction)
        self.check_box_bleaching_correction.grid(column=2, row=21, sticky="W")
        self.check_box_bleaching_correction.select()
        # self.check_box_bleaching_correction.config(state=DISABLED)

        bleaching_correction_algorithms = [
            "additiv no fit",
            "multiplicative simple ratio",
            "biexponential fit additiv"
        ]

        self.bleaching_correction_algorithm = StringVar(self.label_processing_pipeline)
        self.bleaching_correction_algorithm.set(bleaching_correction_algorithms[0])
        self.option_menu_bleaching_correction = OptionMenu(self.label_processing_pipeline, self.bleaching_correction_algorithm,
                                                    *bleaching_correction_algorithms)
        # self.option_menu_bleaching_correction.config(state=DISABLED)
        self.option_menu_bleaching_correction.grid(column=3, row=21, sticky="W")
        #
        self.label_ratio_generation = Label(self.label_processing_pipeline, text="Ratio images:  ")
        self.label_ratio_generation.grid(column=1, row=22, sticky="W")
        self.ratio_generation_in_pipeline = IntVar()
        self.check_box_ratio_generation = Checkbutton(self.label_processing_pipeline,
                                                          variable=self.ratio_generation_in_pipeline,
                                                          onvalue=1,
                                                          offvalue=0,
                                                          command=None)
        self.check_box_ratio_generation.grid(column=2, row=22, sticky="W")
        self.check_box_ratio_generation.select()
        self.check_box_ratio_generation.config(state=DISABLED)

        self.empty_label = Label(self.label_processing_pipeline, text="")
        self.empty_label.grid(column=1, row=23, sticky="W")

        self.label_shape_normalization = Label(self.label_processing_pipeline, text="Shape Normalization")
        self.label_shape_normalization.grid(column=1, row=24, sticky="W")
        self.label_shape_normalization.config(bg='lightgray')


        self.shape_normalization_in_pipeline = IntVar()
        self.check_box_shape_normalization = Checkbutton(self.label_processing_pipeline,
                                                      variable=self.shape_normalization_in_pipeline,
                                                      onvalue=1,
                                                      offvalue=0,
                                                      command=self.update_settings_shape_normalization)
        self.check_box_shape_normalization.grid(column=2, row=24, sticky="W")
        self.check_box_shape_normalization.select()
        # self.check_box_shape_normalization.config(state=DISABLED)

        self.empty_label_2 = Label(self.label_processing_pipeline, text="")
        self.empty_label_2.grid(column=1, row=25, sticky="W")

        self.label_analysis = Label(self.label_processing_pipeline, text="Analysis")
        self.label_analysis.grid(column=1, row=26, sticky="W")
        self.label_analysis.config(bg='lightgray')

        self.label_hotspot_detection = Label(self.label_processing_pipeline, text="Hotspot detection:  ")
        self.label_hotspot_detection.grid(column=1, row=27, sticky="W")
        self.hotspot_detection_in_pipeline = IntVar()
        self.check_box_hotspot_detection = Checkbutton(self.label_processing_pipeline,
                                                      variable=self.hotspot_detection_in_pipeline,
                                                      onvalue=1,
                                                      offvalue=0,
                                                      command=self.update_settings_for_analysis)
        self.check_box_hotspot_detection.grid(column=2, row=27, sticky="W")
        self.check_box_hotspot_detection.select()
        # self.check_box_hotspot_detection.config(state=DISABLED)

        self.label_dartboard_projection = Label(self.label_processing_pipeline, text="Dartboard projection:  ")
        self.label_dartboard_projection.grid(column=1, row=28, sticky="W")
        self.dartboard_projection_in_pipeline = IntVar()
        self.check_box_dartboard_projection = Checkbutton(self.label_processing_pipeline,
                                                       variable=self.dartboard_projection_in_pipeline,
                                                       onvalue=1,
                                                       offvalue=0,
                                                       command=None)
        self.check_box_dartboard_projection.grid(column=2, row=28, sticky="W")
        self.check_box_dartboard_projection.select()
        # self.check_box_dartboard_projection.config(state=DISABLED)

        self.empty_label_3 = Label(self.label_processing_pipeline, text="")
        self.empty_label_3.grid(column=1, row=29, sticky="W")

        self.set_default_settings_for_local_imaging()

        # select all/default settings button
        # self.default_settings_button = Button(self.label_processing_pipeline, text='Default settings', command=self.default_processing_settings)
        # self.default_settings_button.grid(column=1, row=30, sticky="W")

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
        self.save_settings_as_method_button = Button(self.label_control_buttons, text="Save settings on computer",
                                                      command=self.save_settings_as_method)
        self.save_settings_as_method_button.grid(row=0, column=1, sticky="W")

        self.load_settings_from_computer_button = Button(self.label_control_buttons, text="Load settings from computer",
                                                     command=self.load_settings_from_computer)
        self.load_settings_from_computer_button.grid(row=1, column=1, sticky="W")

        ################################################################################


        self.start_button = Button(self.label_control_buttons, text='Start', command=self.start_analysis)
        self.start_button.grid(row=2, column=1, sticky="W")

        # cancel button
        self.cancel_button = Button(self.label_control_buttons, text='Cancel', command=self.cancel)
        self.cancel_button.grid(row=3, column=1, sticky="W")

        # About DARTS button
        self.about_DARTS_button = Button(self.label_control_buttons, text='About DARTS', command=self.open_github_page)
        self.about_DARTS_button.grid(row=4, column=1, sticky="W")

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

    def open_github_page(self):
        website = "https://github.com/IPMI-ICNS-UKE/DARTS"
        webbrowser.open(website)

    def get_parameters(self):
        data = {
            'input_output': {
                'file_or_directory': self.select_mode.get(),
                'image_conf': self.get_image_configuration(),
                'path': self.text_path.get("1.0", "end-1c"),
                # 'path_to_input_1': self.text_single_path_to_input_channel1.get("1.0", "end-1c"),
                # 'path_to_input_2': self.text_single_path_to_input_channel2.get("1.0", "end-1c"),
                # 'path_to_input_combined': self.text_path_to_input_combined.get("1.0", "end-1c"),
                'results_dir': self.text_results_directory.get("1.0", "end-1c"),
                'excel_filename_microdomain_data': "microdomain_data.xlsx"
            },
            'properties_of_measurement': {
                'used_microscope': str(self.text_microscope.get("1.0", "end-1c")),
                'scale': float(self.text_scale.get("1.0", END)),
                'frame_rate': float(self.text_fps.get("1.0", END)),
                'resolution': int(self.text_resolution.get("1.0", END)),
                'cell_type': self.cell_type.get(),
                'cell_types_options': self.cell_types,
                'calibration_parameters_cell_types': self.cell_type_manager.parameters_dict,
                'day_of_measurement': str(self.entry_time.get()),
                'user': str(self.text_user.get("1.0", "end-1c")),
                'experiment_name': str(self.text_experiment_name.get("1.0", "end-1c")),
                'imaging_local_or_global': self.local_or_global.get(),
                'bead_contact': self.bead_contacts_in_pipeline.get() == 1,
                'duration_of_measurement': (float(self.text_duration_before.get("1.0", END)) + float(self.text_duration_after.get("1.0", END)))*float(self.text_fps.get("1.0", END)),
                'wavelength_1': 488,
                'wavelength_2': 561,
                'time_of_measurement_before_starting_point': float(self.text_duration_before.get("1.0", END)),
                'time_of_measurement_after_starting_point': float(self.text_duration_after.get("1.0", END))
            },
            'processing_pipeline': {
                'postprocessing': {
                    'channel_alignment_in_pipeline': self.channel_alignment_in_pipeline.get() == 1,
                    'channel_alignment_each_frame': self.frame_by_frame_registration.get() == 1,
                    'registration_method': 'SITK',
                    'background_sub_in_pipeline': self.background_subtraction_in_pipeline.get() == 1,
                    'cell_segmentation_tracking_in_pipeline': self.segmentation_tracking_in_pipeline.get() == 1,
                    'deconvolution_in_pipeline': self.deconvolution_in_pipeline.get() == 1,
                    'deconvolution_algorithm': str(self.deconvolution_algorithm.get()),
                    'TDE_lambda': self.text_TDE_lambda.get("1.0", "end-1c"),
                    'TDE_lambda_t': self.text_TDE_lambda_t.get("1.0", "end-1c"),
                    'psf': {
                        'type': str(self.text_psf_type.get("1.0", "end-1c")),  # accepted types: "confocal" and "widefield"
                        'lambdaEx_ch1': int(self.text_psf_lambdaEx_ch1.get("1.0", END)),
                        'lambdaEm_ch1': int(self.text_psf_lambdaEm_ch1.get("1.0", END)),
                        'lambdaEx_ch2': int(self.text_psf_lambdaEx_ch2.get("1.0", END)),
                        'lambdaEm_ch2': int(self.text_psf_lambdaEm_ch2.get("1.0", END)),
                        'numAper': float(self.text_psf_numAper.get("1.0", END)),
                        'magObj': int(self.text_psf_magObj.get("1.0", END)),
                        'rindexObj': float(self.text_psf_rindexObj.get("1.0", END)),
                        'ccdSize': int(self.text_psf_ccdSize.get("1.0", END)),
                        'dz': 0,
                        'nslices': 1,
                        'depth': 0,
                        'rindexSp': float(self.text_psf_rindexSp.get("1.0", END)),
                        'nor': 0,
                        'xysize': 150
                    },
                    'bleaching_correction_in_pipeline': self.bleaching_correction_in_pipeline.get() == 1,
                    'bleaching_correction_algorithm': self.bleaching_correction_algorithm.get(),
                    'ratio_images': self.ratio_generation_in_pipeline.get() == 1,
                    'median_filter_kernel': 3
                },
                'shape_normalization': {
                    'shape_normalization': self.shape_normalization_in_pipeline.get() == 1
                },
                'analysis': {
                    'hotspot_detection': self.hotspot_detection_in_pipeline.get() == 1,
                    'dartboard_projection': self.dartboard_projection_in_pipeline.get() == 1
                }
            }
        }
        return data

    def save_settings_as_method(self):
        data = self.get_parameters()
        directory = tkinter.filedialog.askdirectory()
        experiment_name = data['properties_of_measurement']['experiment_name']
        user = data['properties_of_measurement']['user']
        date = data['properties_of_measurement']['day_of_measurement']
        file = open(directory + "/DARTS_settings_" + date + "_" + experiment_name + "_" + user + ".toml", "w")
        tomlkit.dump(data, file)
        file.close()



    def load_settings_from_computer(self):
        config_file_path = tkinter.filedialog.askopenfilename()
        with open(config_file_path, mode="rt", encoding="utf-8") as fp:
            config = tomlkit.load(fp)
            # INPUT OUTPUT
            self.select_mode.set(config["input_output"]["file_or_directory"])
            image_config = self.convert_image_config_to_number(config['input_output']['image_conf'])
            self.selected_image_configuration.set(image_config)
            self.text_path.delete(1.0, END)
            self.text_path.insert(1.0, config["input_output"]["path"])

            self.text_results_directory.delete(1.0, END)
            self.text_results_directory.insert(1.0, config["input_output"]["results_dir"])
            self.excel_filename_microdomain_data = config["input_output"]["excel_filename_microdomain_data"]

            # PROPERTIES OF MEASUREMENT
            self.text_microscope.delete(1.0, END)
            self.text_microscope.insert(1.0, config["properties_of_measurement"]["used_microscope"])
            self.text_scale.delete(1.0, END)
            self.text_scale.insert(1.0, config["properties_of_measurement"]["scale"])
            self.text_fps.delete(1.0, END)
            self.text_fps.insert(1.0, config["properties_of_measurement"]["frame_rate"])
            self.text_resolution.delete(1.0, END)
            self.text_resolution.insert(1.0, config["properties_of_measurement"]["resolution"])
            self.cell_type.set(config["properties_of_measurement"]["cell_type"])
            self.cell_types = list(config["properties_of_measurement"]["cell_types_options"])
            # Clear current menu
            self.option_menu_cell_types['menu'].delete(0, END)

            # Update options in cell type option menu
            for cell_type in self.cell_types:
                self.option_menu_cell_types['menu'].add_command(label=cell_type,
                                                                command=tkinter._setit(self.cell_type,
                                                                                       cell_type))
            self.cell_type_manager.cell_types = self.cell_types

            # calibration parameters for cell type
            self.cell_type_manager.parameters_dict = dict(config["properties_of_measurement"]["calibration_parameters_cell_types"])

            self.entry_time.delete(0, END)
            self.entry_time.insert(0, config["properties_of_measurement"]["day_of_measurement"])
            self.text_user.delete(1.0, END)
            self.text_user.insert(1.0, config["properties_of_measurement"]["user"])
            self.text_experiment_name.delete(1.0, END)
            self.text_experiment_name.insert(1.0, config["properties_of_measurement"]["experiment_name"])
            self.local_or_global.set(config["properties_of_measurement"]["imaging_local_or_global"])

            if config["properties_of_measurement"]["bead_contact"]:
                self.check_box_bead_contacts.select()
            else:
                self.check_box_bead_contacts.deselect()
            self.duration_of_measurement = config["properties_of_measurement"]["duration_of_measurement"]
            self.wavelength_1 = config["properties_of_measurement"]["wavelength_1"]
            self.wavelength_2 = config["properties_of_measurement"]["wavelength_2"]
            self.text_duration_before.delete(1.0, END)
            self.text_duration_before.insert(1.0, config["properties_of_measurement"]["time_of_measurement_before_starting_point"])
            self.text_duration_after.delete(1.0, END)
            self.text_duration_after.insert(1.0, config["properties_of_measurement"]["time_of_measurement_after_starting_point"])

            # PROCESSING PIPELINE
            ## POSTPROCESSING
            if config["processing_pipeline"]["postprocessing"]["channel_alignment_in_pipeline"]:
                self.check_box_channel_alignment.select()
            else:
                self.check_box_channel_alignment.deselect()
            if config["processing_pipeline"]["postprocessing"]["channel_alignment_each_frame"]:
                self.check_box_frame_by_frame_registration.select()
            else:
                self.check_box_frame_by_frame_registration.deselect()
            self.registration_method = config["processing_pipeline"]["postprocessing"]["registration_method"]

            if config["processing_pipeline"]["postprocessing"]["background_sub_in_pipeline"]:
                self.check_box_background_subtraction_in_pipeline.select()
            else:
                self.check_box_background_subtraction_in_pipeline.deselect()
            if config["processing_pipeline"]["postprocessing"]["cell_segmentation_tracking_in_pipeline"]:
                self.check_box_segmentation_tracking_in_pipeline.select()
            else:
                self.check_box_segmentation_tracking_in_pipeline.deselect()
            if config["processing_pipeline"]["postprocessing"]["deconvolution_in_pipeline"]:
                self.check_box_deconvolution_in_pipeline.select()

                self.deconvolution_algorithm.set(config["processing_pipeline"]["postprocessing"]["deconvolution_algorithm"])
                self.option_menu_deconvolution.config(state=NORMAL)
                if self.deconvolution_algorithm.get() == "TDE":
                    self.text_TDE_lambda.config(state=NORMAL)
                    self.text_TDE_lambda_t.config(state=NORMAL)
                    self.text_TDE_lambda.delete(1.0, END)
                    self.text_TDE_lambda.insert(1.0, config["processing_pipeline"]["postprocessing"]["TDE_lambda"])
                    self.text_TDE_lambda_t.delete(1.0, END)
                    self.text_TDE_lambda_t.insert(1.0, config["processing_pipeline"]["postprocessing"]["TDE_lambda_t"])
                self.text_psf_type.delete(1.0, END)
                self.text_psf_type.insert(1.0, config["processing_pipeline"]["postprocessing"]["psf"]["type"])
                self.text_psf_lambdaEx_ch1.delete(1.0, END)
                self.text_psf_lambdaEx_ch1.insert(1.0, config["processing_pipeline"]["postprocessing"]["psf"]["lambdaEx_ch1"])
                self.text_psf_lambdaEm_ch1.delete(1.0, END)
                self.text_psf_lambdaEm_ch1.insert(1.0, config["processing_pipeline"]["postprocessing"]["psf"]["lambdaEm_ch1"])
                self.text_psf_lambdaEx_ch2.delete(1.0, END)
                self.text_psf_lambdaEx_ch2.insert(1.0, config["processing_pipeline"]["postprocessing"]["psf"]["lambdaEx_ch2"])
                self.text_psf_lambdaEm_ch2.delete(1.0, END)
                self.text_psf_lambdaEm_ch2.insert(1.0, config["processing_pipeline"]["postprocessing"]["psf"]["lambdaEm_ch2"])
                self.text_psf_numAper.delete(1.0, END)
                self.text_psf_numAper.insert(1.0, config["processing_pipeline"]["postprocessing"]["psf"]["numAper"])
                self.text_psf_magObj.delete(1.0, END)
                self.text_psf_magObj.insert(1.0, config["processing_pipeline"]["postprocessing"]["psf"]["magObj"])
                self.text_psf_rindexObj.delete(1.0, END)
                self.text_psf_rindexObj.insert(1.0, config["processing_pipeline"]["postprocessing"]["psf"]["rindexObj"])
                self.text_psf_rindexSp.delete(1.0, END)
                self.text_psf_rindexSp.insert(1.0, config["processing_pipeline"]["postprocessing"]["psf"]["rindexSp"])
                self.text_psf_ccdSize.delete(1.0, END)
                self.text_psf_ccdSize.insert(1.0, config["processing_pipeline"]["postprocessing"]["psf"]["ccdSize"])
            else:
                self.check_box_deconvolution_in_pipeline.deselect()
                self.option_menu_deconvolution.config(state=DISABLED)

            if config["processing_pipeline"]["postprocessing"]["bleaching_correction_in_pipeline"]:
                self.check_box_bleaching_correction.select()
                self.bleaching_correction_algorithm.set(config["processing_pipeline"]["postprocessing"]["bleaching_correction_algorithm"])
                self.option_menu_bleaching_correction.config(state=NORMAL)
            else:
                self.check_box_bleaching_correction.deselect()
                self.option_menu_bleaching_correction.config(state=DISABLED)
            if config["processing_pipeline"]["postprocessing"]["ratio_images"]:
                self.check_box_ratio_generation.select()
            else:
                self.check_box_ratio_generation.deselect()
            self.median_filter_kernel = config["processing_pipeline"]["postprocessing"]["median_filter_kernel"]

            ## SHAPE NORMALIZATION
            if config["processing_pipeline"]["shape_normalization"]["shape_normalization"]:
                self.check_box_shape_normalization.config(state=NORMAL)
                self.check_box_shape_normalization.select()
            else:
                self.check_box_shape_normalization.deselect()

            ## ANALYSIS
            if config["processing_pipeline"]["analysis"]["hotspot_detection"]:
                self.check_box_hotspot_detection.select()
                self.check_box_hotspot_detection.config(state=NORMAL)
            else:
                self.check_box_hotspot_detection.deselect()

            if config["processing_pipeline"]["analysis"]["dartboard_projection"]:
                self.check_box_dartboard_projection.select()
                self.check_box_dartboard_projection.config(state=NORMAL)
            else:
                self.check_box_dartboard_projection.deselect()




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

    def update_settings_for_analysis(self):
        if self.hotspot_detection_in_pipeline.get() == 0:
            self.dartboard_projection_in_pipeline.set(0)
            self.check_box_dartboard_projection.config(state=DISABLED)
        elif self.hotspot_detection_in_pipeline.get() == 1 and self.shape_normalization_in_pipeline.get() == 1 and self.bead_contacts_in_pipeline.get()==1:
            self.check_box_dartboard_projection.config(state=NORMAL)
            self.dartboard_projection_in_pipeline.set(1)

    def update_settings_shape_normalization(self):
        if self.shape_normalization_in_pipeline.get() == 0:
            # self.hotspot_detection_in_pipeline.set(0)
            # self.check_box_hotspot_detection.config(state=DISABLED)
            self.dartboard_projection_in_pipeline.set(0)
            self.check_box_dartboard_projection.config(state=DISABLED)
        elif self.shape_normalization_in_pipeline.get() == 1 and self.bead_contacts_in_pipeline.get() == 1:
            self.hotspot_detection_in_pipeline.set(1)
            self.check_box_hotspot_detection.config(state=NORMAL)
            self.dartboard_projection_in_pipeline.set(1)
            self.check_box_dartboard_projection.config(state=NORMAL)

    def update_deconvolution(self):
        if self.deconvolution_in_pipeline.get() == 0:
            self.option_menu_deconvolution.config(state=DISABLED)
            for textbox in self.deconvolution_text_boxes:
                textbox.config(state=DISABLED)
        elif self.deconvolution_in_pipeline.get() == 1:
            self.option_menu_deconvolution.config(state=NORMAL)
            for textbox in self.deconvolution_text_boxes:
                textbox.config(state=NORMAL)

    def update_bleaching_correction(self):
        if self.bleaching_correction_in_pipeline.get() == 0:
            self.option_menu_bleaching_correction.config(state=DISABLED)
        elif self.bleaching_correction_in_pipeline.get() == 1:
            self.option_menu_bleaching_correction.config(state=NORMAL)

    def update_bead_contact(self):
        if self.bead_contacts_in_pipeline.get() == 0:
            self.dartboard_projection_in_pipeline.set(0)
            self.check_box_dartboard_projection.config(state=DISABLED)
        elif self.bead_contacts_in_pipeline.get():
            if self.shape_normalization_in_pipeline.get() == 1 and self.hotspot_detection_in_pipeline.get() == 1:
                self.dartboard_projection_in_pipeline.set(1)
                self.check_box_dartboard_projection.config(state=NORMAL)

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

    def manage_cell_types(self):
        self.cell_type_manager.open_manage_window()


    def set_default_settings_for_global_imaging(self):
        self.check_box_channel_alignment.select()
        self.check_box_frame_by_frame_registration.deselect()
        self.check_box_background_subtraction_in_pipeline.deselect()
        self.check_box_deconvolution_in_pipeline.deselect()
        self.update_deconvolution()
        # self.option_menu_deconvolution.config(state=DISABLED)
        self.check_box_bleaching_correction.deselect()
        self.update_bleaching_correction()
        # self.option_menu_bleaching_correction.config(state=DISABLED)
        self.check_box_shape_normalization.deselect()
        self.update_settings_shape_normalization()
        self.check_box_hotspot_detection.deselect()
        self.check_box_dartboard_projection.deselect()

    def set_default_settings_for_local_imaging(self):
        self.check_box_channel_alignment.select()
        self.check_box_frame_by_frame_registration.deselect()
        self.check_box_background_subtraction_in_pipeline.select()
        self.set_default_decon_parameters()
        self.check_box_bleaching_correction.select()
        self.option_menu_bleaching_correction.config(state=NORMAL)
        self.bleaching_correction_algorithm.set('additiv no fit')
        self.check_box_shape_normalization.select()
        self.update_settings_shape_normalization()
        self.check_box_hotspot_detection.select()
        self.check_box_dartboard_projection.select()
        self.check_box_bead_contacts.select()
        self.update_bead_contact()

    def set_default_decon_parameters(self):
        self.check_box_deconvolution_in_pipeline.select()
        self.option_menu_deconvolution.config(state=NORMAL)
        self.deconvolution_algorithm.set('LR')

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
        file = open("config.toml", "w")
        data = self.get_parameters()
        tomlkit.dump(data, file)
        file.close()

    def add_cell_type_clicked(self):
        pass

    def run_main_loop(self):
        self.window.mainloop()

    def close_window(self):
        self.window.destroy()



class CellTypeManager:
    def __init__(self, root, cell_types, option_menu_cell_types, selected_cell_type):
        self.root = root
        self.cell_types = cell_types
        self.option_menu_cell_types = option_menu_cell_types
        self.selected_cell_type = selected_cell_type
        self.parameters_dict = {"jurkat": {},
                                "NK": {},
                                "primary": {}}

    def open_manage_window(self):
        manage_window = Toplevel(self.root)
        manage_window.title("Manage Cell Types")

        self.listbox = Listbox(manage_window, width=30)
        self.listbox.pack(padx=10, pady=10, side=LEFT, fill=BOTH)

        for cell_type in self.cell_types:
            self.listbox.insert(END, cell_type)

        add_button = Button(manage_window, text="Add Cell Type", command=self.add_cell_type)
        add_button.pack(pady=5)

        delete_button = Button(manage_window, text="Delete Cell Type", command=self.delete_cell_type)
        delete_button.pack(pady=5)

        view_button = Button(manage_window, text="View Parameters", command=self.view_parameters)
        view_button.pack(pady=5)

        plot_button = Button(manage_window, text="Plot calibration curve", command=self.plot_calibration_curve)
        plot_button.pack(pady=5)

        # save_button = Button(manage_window, text="Save", command=self.save_cell_types)
        # save_button.pack(pady=5)

        """
        # Create a Text widget to display parameter explanations
        text = Text(manage_window, height=25, width=40)
        text.pack()

        # Define the explanations
        explanations = {
            "corresponding_Ca_value": "The corresponding calcium value for a given pixel intensity or ratio",
            "threshold_Calcium": "The threshold value for calcium microdomain detection: corresponding_Ca_value + spotHeight",
            "threshold_ratio": "The threshold ratio for the cell type",
            "spotHeight": "Pixels inside a Ca2+ microdomain have to be greater than (mean calcium concentration of a frame + spotHeight)"
        }

        # Insert the explanations into the Text widget
        for parameter, explanation in explanations.items():
            text.insert(END, f"{parameter}: {explanation}\n\n")

        text.config(state=DISABLED)
        """

    def add_cell_type(self):
        cell_type = simpledialog.askstring("Add Cell Type", "Enter the name of the cell type:")
        if cell_type:
            if cell_type not in self.cell_types:
                parameters = self.get_cell_type_parameters(cell_type)
                if parameters:
                    self.cell_types.append(cell_type)
                    self.parameters_dict[cell_type] = parameters
                    self.listbox.insert(END, cell_type)
                else:
                    messagebox.showerror("Error", "Failed to get parameters for the cell type!")
            else:
                messagebox.showwarning("Duplicate Cell Type", "Cell type already exists!")
            self.save_cell_types()

    def delete_cell_type(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_cell_type = self.listbox.get(selected_index)
            self.listbox.delete(selected_index)
            self.cell_types.remove(selected_cell_type)
        self.save_cell_types()

    def get_cell_type_parameters(self, cell_type):
        parameter_values = {}
        parameter_names = ["KD value (of Ca2+ dye) [nM]", "minimum ratio", "maximum ratio", "minimum fluorescence intensity", "maximum fluorescence intensity", "spot Height Ca2+ microdomains"]
        for param in parameter_names:
            value = simpledialog.askfloat(f"Enter {param} value for {cell_type}", f"Enter value for parameter {param}:")
            if value is not None:
                parameter_values[param] = value
            else:
                return None
        return parameter_values

    def view_parameters(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_cell_type = self.listbox.get(selected_index)
            parameters = self.parameters_dict.get(selected_cell_type)
            if parameters:
                view_window = Toplevel(self.root)
                view_window.title(f"{selected_cell_type} Parameters")

                entry_boxes = {}
                for i, (param, value) in enumerate(parameters.items()):
                    label = Label(view_window, text=param)
                    label.grid(row=i, column=0, padx=10, pady=5)

                    entry = Entry(view_window)
                    entry.insert(0, str(value))
                    entry.grid(row=i, column=1, padx=10, pady=5)

                    entry_boxes[param] = entry

                def save_changes():
                    for param, entry in entry_boxes.items():
                        try:
                            parameters[param] = float(entry.get())
                        except ValueError:
                            messagebox.showerror("Error", f"Invalid value for {param}!")

                save_button = Button(view_window, text="Save Changes", command=save_changes)
                save_button.grid(row=len(parameters), columnspan=2, padx=10, pady=10)

            else:
                messagebox.showerror("Error", "Parameters not available for this cell type!")

    def plot_calibration_curve(self):
        selected_index = self.listbox.curselection()
        selected_cell_type = self.listbox.get(selected_index)
        params_for_cell_type = self.parameters_dict[selected_cell_type]
        parameter_names = ["KD value (of Ca2+ dye) [nM]", "minimum ratio", "maximum ratio", "minimum fluorescence intensity",
                           "maximum fluorescence intensity", "spot Height Ca2+ microdomains"]

        # Convert parameter values to float
        kd_value = float(params_for_cell_type["KD value (of Ca2+ dye) [nM]"])
        min_ratio = float(params_for_cell_type["minimum ratio"])
        max_ratio = float(params_for_cell_type["maximum ratio"])
        min_intensity = float(params_for_cell_type["minimum fluorescence intensity"])
        max_intensity = float(params_for_cell_type["maximum fluorescence intensity"])

        # Generate ratio values
        ratio_values = np.linspace(min_ratio, max_ratio, num=100, endpoint=False)

        # Calculate corresponding Ca2+ values
        corresponding_Ca_values = [
            kd_value * ((ratio - min_ratio) / (max_ratio - ratio)) * (min_intensity / max_intensity) for ratio in
            ratio_values]

        # Create a new Tkinter window
        plot_window = tk.Toplevel(self.root)
        plot_window.title("Calibration Curve")

        # Create a Matplotlib figure and plot the calibration curve
        fig, ax = plt.subplots()
        ax.plot(ratio_values, corresponding_Ca_values)
        ax.set_xlabel('Ratio Value')
        ax.set_ylabel('Corresponding Ca2+ Value (nM)')

        # Embed the Matplotlib plot within the Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def save_cell_types(self):
        # Clear current menu
        self.option_menu_cell_types['menu'].delete(0, END)

        # Update options
        for cell_type in self.cell_types:
            self.option_menu_cell_types['menu'].add_command(label=cell_type, command=tkinter._setit(self.selected_cell_type, cell_type))

        # Set default value to the first option in the new list
        self.selected_cell_type.set(self.cell_types[0])







