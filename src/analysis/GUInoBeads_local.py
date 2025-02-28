import tkinter
from tkinter import (Tk, Scale, Frame, Button, Toplevel, Label, Entry, IntVar, Radiobutton, HORIZONTAL)

from fontTools.misc.arrayTools import calcIntBounds
from fontTools.misc.sstruct import calcsize
from ipykernel.pickleutil import cell_type
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import skimage.io as io
import math

from tensorflow.python.keras.utils.metrics_utils import update_confusion_matrix_variables
from tifffile.tifffile import rational

from src.general.RatioToConcentrationConverter import RatioConverter
from src.general.load_data import load_data


class GUInoBeads_local:
    def __init__(self, cell, cell_index, parameters, ratioconverter):
        self.channel_format = parameters["input_output"]["image_conf"]
        self.image = cell.ratio
        self.mean_ratio_list = cell.mean_ratio_list  # Using mean_ratio_list for the global signal
        self.calcium_c = [] # empty list for calcium values, filled below
        self.starting_point_auto = cell.starting_point_auto
        self.cell_denied_flag = False
        self.cell_type = parameters["properties_of_measurement"]["cell_type"]
        self.spotHeight = None
        if self.cell_type == 'primary':
            self.spotHeight = 112.5  # [Ca2+] = 112.5 nM
        elif self.cell_type == 'jurkat':
            self.spotHeight = 72
        elif self.cell_type == 'NK':
            self.spotHeight = 72  # needs to be checked
        self.ratio_converter = ratioconverter
        self.number_of_frames, self.image_height, self.image_width = self.image.shape
        self.GUI_width, self.GUI_height = 1200, 800
        self.root = Tk()
        self.root.resizable(False, False)
        self.root.geometry(f"{self.GUI_width}x{self.GUI_height}")
        self.root.title("GUI no beads local, cell number: " + str(cell_index))

        # concentration conversion
        for i, ip in enumerate(self.mean_ratio_list):
            c,_,_ = self.ratio_converter.calcium_calibration(ip,
                                                                             self.cell_type,
                                                                             self.spotHeight)
            self.calcium_c.append(c)

        # Set up the figure with increased spacing between subplots
        self.figure = Figure(figsize=(10, 5))
        self.figure.subplots_adjust(wspace=0.6)  # Increase horizontal space between subplots

        # Image display subplot with color bar
        self.subplot_image = self.figure.add_subplot(121)
        im = self.subplot_image.imshow(self.image[0], cmap='viridis', vmin=0.1, vmax=2.0)
        self.colorbar = self.figure.colorbar(im, ax=self.subplot_image, orientation='vertical', fraction=0.046,
                                             pad=0.04)
        self.colorbar.set_label("Ratio")
        # Global signal subplot on the right
        self.global_signal_subplot = self.figure.add_subplot(122)
        #self.global_signal_subplot.plot(self.mean_ratio_list, color='blue')
        self.global_signal_subplot.plot(self.calcium_c, color='blue')
        #self.global_signal_subplot.set_title("Global Signal")
        self.global_signal_subplot.set_title("Global Ca concentration")
        self.global_signal_subplot.set_xlabel("Frame")
        self.global_signal_subplot.set_ylabel("Mean Intensity")
        self.global_signal_subplot.set_ylim(0, max(self.calcium_c))

        # Add a vertical line to indicate the current frame
        self.vertical_line = self.global_signal_subplot.axvline(x=self.starting_point_auto, color='red', linestyle='--')

        # Set up canvas to display figure in Tkinter
        self.canvas_frame = Frame(self.root, width=600, height=600)
        self.canvas_frame.place(x=10, y=10)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=1)

        # Slider for frame selection
        self.start_frame = 0
        self.end_frame = len(self.image) - 1
        self.slider = Scale(self.root, from_=self.start_frame, to=self.end_frame, orient=HORIZONTAL,
                            command=self.update_image, length=500)
        self.slider.place(x=self.GUI_width * 0.1, y=self.GUI_height * 0.65)
        self.slider.set(self.starting_point_auto)

        # initialize choice
        self.determination_choice = IntVar()

        # Text field for showing current starting frame
        self.starting_frame_label = Label(self.root, text=f"Current Starting Frame: {self.starting_point_auto}, automatically set", width=30,
                                          anchor='w')
        self.starting_frame_label.place(x=self.GUI_width * 0.1, y=self.GUI_height * 0.7)

        # Set manually Button
        self.accept_button = Button(self.root, text="set manually", command=self.set_manually)
        self.accept_button.place(x=self.GUI_width * 0.3, y=self.GUI_height * 0.7)

        # Set automatically Button
        self.accept_button = Button(self.root, text="set automatically", command=self.set_automatically)
        self.accept_button.place(x=self.GUI_width * 0.3, y=self.GUI_height * 0.75)

        # Set Deny Button
        self.deny_button = Button(self.root, text="Deny cell", command=self.deny_cell)
        self.deny_button.place(x=self.GUI_width * 0.50, y=self.GUI_height * 0.8)

        # Close button to finalize the selection and close GUI
        self.close_button = Button(self.root, text="Accept & Continue", command=self.close_and_continue_gui)
        self.close_button.place(x=self.GUI_width * 0.4, y=self.GUI_height * 0.8)

        self.cancel_button = Button(self.root, text='Cancel', command=self.cancel)
        self.cancel_button.place(x=self.GUI_width * 0.4, y=self.GUI_height * 0.9)

        # Initialize starting frame to None (default value if not set manually)
        self.starting_frame = None

    def cancel(self):
        self.root.destroy()
        quit()

    def update_image(self, new_frame):
        # Update the displayed image
        new_frame = int(new_frame)
        new_image = self.image[new_frame]
        self.subplot_image.clear()
        im = self.subplot_image.imshow(new_image, cmap='viridis', vmin=0.1, vmax=2.0)
        self.colorbar.update_normal(im)

        # Move the vertical line to the new frame position
        self.vertical_line.set_xdata([new_frame])

        # Refresh both subplots on the canvas
        self.canvas.draw()

    def set_manually(self):
        self.determination_choice.set(1)
        if self.determination_choice.get() == 1:  # Manual
            try:
                # Retrieve frame from slider
                frame = self.slider.get()
                if 0 <= frame <= self.number_of_frames - 1:
                    self.starting_frame = frame  # Store the valid frame number
                    print(f"Starting frame set to: {frame}")
                    # Update the starting frame label
                    self.starting_frame_label.config(text=f"Current Starting Frame: {frame}, manually set")
                else:
                    print("Invalid frame. Please enter a value within the valid range.")
            except ValueError:
                print("Invalid input. Please enter an integer.")

    def set_automatically(self):
        self.determination_choice.set(2)
        if self.determination_choice.get() == 2:  # Automatic
            print("Automatic starting point determination selected.")
            self.starting_frame = self.starting_point_auto
            self.starting_frame_label.config(text=f"Current Starting Frame: {self.starting_frame}, automatically set")
            self.update_image(self.starting_point_auto)
            self.slider.set(self.starting_point_auto)

    def deny_cell(self):
        print("Cell denied.")
        self.cell_denied_flag = True
        self.close_gui()

    def close_and_continue_gui(self):
        if self.starting_frame is None:
            print("No starting frame defined.")
        else:
            print(f"Starting frame: {self.starting_frame}")
        self.root.destroy()

    def run_main_loop(self):
        self.root.mainloop()

    def close_gui(self):
        self.root.quit()
        self.root.destroy()
