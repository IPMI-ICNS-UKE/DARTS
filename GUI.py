import tkinter
from tkinter import (Tk, ttk, Label, Frame, Button,
    Checkbutton, Radiobutton, IntVar, Text, HORIZONTAL, END, Entry, Toplevel, Checkbutton)
from tkinter import filedialog as fd
from tkcalendar import Calendar

class  SimpleGUI():

    def __init__(self):
        self.window = Tk()
        self.window.geometry("1000x500")
        self.window.title("Welcome to T-DARTS")

        self.label_image_configuration = Label(self.window, text="Choose an image configuration:  ")
        self.label_image_configuration.grid(column=0, row=0, sticky="W")
        self.selected_image_configuration = IntVar()
        self.image_config_radiobutton_1 = Radiobutton(self.window, text='single', value=1, variable=self.selected_image_configuration)
        self.image_config_radiobutton_2 = Radiobutton(self.window, text='two in one', value=2, variable=self.selected_image_configuration)
        self.image_config_radiobutton_1.grid(column=1, row=0, sticky="W")
        self.image_config_radiobutton_2.grid(column=2, row=0, sticky="W")

        self.selection_button = Button(self.window, text="Choose file(s)", command=self.choose_file_clicked)
        self.selection_button.grid(column=3, row=0, sticky="W")

        self.label_single_path_to_input_channel1 = Label(self.window, text="path to input channel 1")
        self.label_single_path_to_input_channel1.grid(column=1, row=1, sticky="W")
        self.text_single_path_to_input_channel1 = Text(self.window, height=1, width=30)
        self.text_single_path_to_input_channel1.grid(column=2, row=1, sticky="W")

        self.label_single_path_to_input_channel2 = Label(self.window, text="path to input channel 2")
        self.label_single_path_to_input_channel2.grid(column=1, row=2, sticky="W")
        self.text_single_path_to_input_channel2 = Text(self.window, height=1, width=30)
        self.text_single_path_to_input_channel2.grid(column=2, row=2, sticky="W")

        self.label_path_to_input_combined = Label(self.window, text="path to input combined")
        self.label_path_to_input_combined.grid(column=1, row=3, sticky="W")
        self.text_path_to_input_combined = Text(self.window, height=1, width=30)
        self.text_path_to_input_combined.grid(column=2, row=3, sticky="W")

        self.label_choose_results_directory = Label(self.window, text="Choose a results directory:  ")
        self.label_choose_results_directory.grid(column=0, row=4, sticky="W")
        self.label_results_directory= Label(self.window, text="results directory")
        self.label_results_directory.grid(column=1, row=4, sticky="W")
        self.text_results_directory = Text(self.window, height=1, width=30)
        self.text_results_directory.grid(column=2, row=4, sticky="W")
        self.choose_results_directory_button = Button(self.window, text="Choose a results directory", command=self.choose_results_directory_clicked)
        self.choose_results_directory_button.grid(column=3, row=4, sticky="W")

        self.label_image_configuration = Label(self.window, text="Choose a processing mode:  ")
        self.label_image_configuration.grid(column=0, row=5, sticky="W")
        self.selected_image_configuration = IntVar()
        self.processing_mode_radiobutton_1 = Radiobutton(self.window, text='single measurement', value=1, variable=self.selected_image_configuration)
        self.processing_mode_radiobutton_2 = Radiobutton(self.window, text='batch processing', value=2, variable=self.selected_image_configuration)
        self.processing_mode_radiobutton_1.grid(column=1, row=5, sticky="W")
        self.processing_mode_radiobutton_2.grid(column=2, row=5, sticky="W")

        self.label_measurement_properties = Label(self.window, text="Properties of measurement:  ")
        self.label_measurement_properties.grid(column=0, row=7, sticky="W")
        self.label_microscope_name = Label(self.window, text="Used microscope:  ")
        self.label_microscope_name.grid(column=1, row=7, sticky="W")
        self.text_microscope= Text(self.window, height=1, width=30)
        self.text_microscope.grid(column=2, row=7, sticky="W")
        self.label_scale = Label(self.window, text="Scale (microns per pixel):  ")
        self.label_scale.grid(column=1, row=8, sticky="W")
        self.text_scale = Text(self.window, height=1, width=30)
        self.text_scale.grid(column=2, row=8, sticky="W")
        self.label_fps = Label(self.window, text="frame rate (fps):  ")
        self.label_fps.grid(column=1, row=9, sticky="W")
        self.text_fps = Text(self.window, height=1, width=30)
        self.text_fps.grid(column=2, row=9, sticky="W")
        self.label_resolution = Label(self.window, text="Spatial resolution in pixels:  ")
        self.label_resolution.grid(column=1, row=10, sticky="W")
        self.text_resolution = Text(self.window, height=1, width=30)
        self.text_resolution.grid(column=2, row=10, sticky="W")
        self.label_time = Label(self.window, text="day of measurement :  ")
        self.label_time.grid(column=1, row=11, sticky="W")
        self.entry_time = Entry(self.window)
        self.entry_time.grid(column=2, row=11, sticky="W")
        self.entry_time.insert(0, "dd/mm/yyyy")
        self.entry_time.bind("<1>", self.pick_date)

        self.label_processing_pipeline = Label(self.window, text="Processing pipeline:  ")
        self.label_processing_pipeline.grid(column=0, row=12, sticky="W")
        self.label_channel_alignment = Label(self.window, text="Channel alignment:  ")
        self.label_channel_alignment.grid(column=1, row=12, sticky="W")
        self.channel_alignment_in_pipeline = IntVar()
        self.check_button_channel_alignment = Checkbutton(self.window, variable=self.channel_alignment_in_pipeline, onvalue=1, offvalue=0,)
        self.check_button_channel_alignment.grid(column=2, row=12, sticky="W")

        self.label_deconvolution = Label(self.window, text="Deconvolution:  ")
        self.label_deconvolution.grid(column=1, row=13, sticky="W")
        self.deconvolution_in_pipeline = IntVar()
        self.check_box_deconvolution_in_pipeline = Checkbutton(self.window, variable=self.deconvolution_in_pipeline,
                                                          onvalue=1, offvalue=0, )
        self.check_box_deconvolution_in_pipeline.grid(column=2, row=13, sticky="W")

        self.label_bleaching_correction = Label(self.window, text="Bleaching correction:  ")
        self.label_bleaching_correction.grid(column=1, row=14, sticky="W")
        self.bleaching_correction_in_pipeline = IntVar()
        self.check_box_bleaching_correction = Checkbutton(self.window, variable=self.bleaching_correction_in_pipeline,
                                                          onvalue=1, offvalue=0, )
        self.check_box_bleaching_correction.grid(column=2, row=14, sticky="W")

        self.label_dartboard_projection = Label(self.window, text="Dartboard projection:  ")
        self.label_dartboard_projection.grid(column=1, row=15, sticky="W")
        self.dartboard_projection_in_pipeline = IntVar()
        self.check_box_dartboard_projection = Checkbutton(self.window, variable=self.dartboard_projection_in_pipeline,
                                                          onvalue=1, offvalue=0, )
        self.check_box_dartboard_projection.grid(column=2, row=15, sticky="W")

        self.start_button = Button(self.window, text='Start', command=None)
        self.start_button.place(x=200,y=450)

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
                            date_pattern="dd/mm/y")
        calendar.place(x=0, y=0)
        submit_button = Button(date_window, text='submit', command=self.grab_date)
        submit_button.place(x=80, y=190)

    def grab_date(self):
        self.entry_time.delete(0, END)
        self.entry_time.insert(0, calendar.get_date())
        date_window.destroy()

    def choose_file_clicked(self):
        self.select_files()

    def get_image_configuration(self):
        if self.selected_image_configuration.get() == 1:
            return "single"
        if self.selected_image_configuration.get() == 2:
            return "two-in-one"
        else:
            return "no configuration chosen"

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


    def run_main_loop(self):
        self.window.mainloop()

    def close_window(self):
        self.window.destroy()

simple_gui = SimpleGUI()
simple_gui.run_main_loop()
