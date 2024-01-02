import tkinter

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import (Tk, Label, Scale, Listbox, Scrollbar, Frame, Button, Radiobutton, IntVar, Text, HORIZONTAL, END, StringVar, Entry)
import skimage.io as io


class GUInoBeads():
    def __init__(self, file, filepath, parameters):
        self.file = file
        self.channel_format = parameters["input_output"]["image_conf"]
        self.image = io.imread(filepath)

        self.number_of_frames, self.image_height, self.image_width = self.image.shape
        self.GUI_width, self.GUI_height = 1200, 800  # round(self.image_width * 2.2), round(self.image_height * 1.2)
        if self.channel_format == "two-in-one":
            self.channel_width = self.image_width*0.5
        elif self.channel_format == "single":
            self.channel_width = self.image_width

        self.root = Tk()
        self.root.resizable(False, False)
        self.root.geometry(str(self.GUI_width) + "x" + str(self.GUI_height))
        self.root.title("Global measurement, no bead contacts: Definition of time of addition, " + file)

        self.figure = Figure()
        self.subplot_image = self.figure.add_subplot(111)
        self.subplot_image.imshow(self.image[0])
        # self.subplot_image.set_axis_off()
        self.canvas_frame = Frame(self.root, width=600, height=600)
        self.canvas_frame.place(x=10, y=10)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=1)
        self.start_frame = 0
        self.end_frame = len(self.image)-1

        self.slider = Scale(self.root, from_=self.start_frame, to=self.end_frame, orient=HORIZONTAL,
                           command=self.update_image, length=500)

        self.slider.place(x=self.GUI_width * 0.1, y=self.GUI_height * 0.65)


        self.input_frame = Frame(self.root)
        self.input_frame.place(x=750, y=50)

        self.time_label = Label(self.input_frame, text="Time of Addition (frame)")
        self.time_label.grid(row=1, column=0, sticky="W")

        self.entry_var = StringVar()
        self.entry = Entry(self.input_frame, textvariable=self.entry_var)
        self.entry.grid(row=2, column=0, sticky="W")

        self.close_button = Button(self.input_frame, text="Continue with next image or processing, respectively", command=self.close_gui)
        self.close_button.grid(row=3, column=0, sticky="W")


        self.cancel_button = Button(self.input_frame, text='Cancel', command=self.cancel)
        self.cancel_button.grid(row=4, column=0, sticky="W")

    def cancel(self):
        self.root.destroy()
        quit()


    def update_image(self, new_frame):
        new_image = self.image[int(new_frame)]
        self.figure.delaxes(self.figure.axes[0])
        self.subplot_image = self.figure.add_subplot(111)
        self.subplot_image.imshow(new_image)

        # self.subplot_image.set_axis_off()

        self.canvas.draw()
        # self.canvas.get_tk_widget().pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=1)

    def get_time_of_addition(self):
        try:
            frame_number = int(self.entry_var.get())
            return frame_number
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

    def run_main_loop(self):
        self.root.mainloop()


    def close_gui(self):
        self.root.destroy()



