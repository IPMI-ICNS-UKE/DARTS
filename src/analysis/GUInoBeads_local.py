import tkinter

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import (Tk, Label, Scale, Listbox, Scrollbar, Frame, Button, Radiobutton, IntVar, Text, HORIZONTAL, END)
import skimage.io as io
import math
from src.general.load_data import load_data


class GUInoBeads_local():
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
        self.root.title("GUI no beads local, " + file)

        self.figure = Figure()
        self.subplot_image = self.figure.add_subplot(111)
        self.subplot_image.imshow(self.image[0])
        # self.subplot_image.set_axis_off()
        self.canvas_frame = Frame(self.root, width=600, height=600)
        self.canvas_frame.place(x=10, y=10)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=1)
        self.canvas.mpl_connect('button_press_event', self.mouse_clicked)
        self.start_frame = 0
        self.end_frame = len(self.image)-1

        self.slider = Scale(self.root, from_=self.start_frame, to=self.end_frame, orient=HORIZONTAL,
                           command=self.update_image, length=500)

        self.slider.place(x=self.GUI_width * 0.1, y=self.GUI_height * 0.65)


        self.input_frame = Frame(self.root)
        self.input_frame.place(x=750, y=50)


        self.label_position_inside_cell = Label(self.input_frame, text="Position inside cell: x,y")
        self.label_position_inside_cell.grid(row=1, column=0, sticky="W")
        self.text_position_inside_cell = Text(self.input_frame, height=1, width=30)
        self.text_position_inside_cell.grid(row=2, column=0, sticky="W")

        self.add_cell_button = Button(self.input_frame, bg='red', text="ADD cell",
                                                 command=self.add_cell)
        self.add_cell_button.grid(row=3, column=0, sticky="W")



        self.cell_frame = Frame(self.input_frame)
        self.cell_frame.grid(row=5, column=0, sticky="W")
        self.cell_list_label = Label(self.cell_frame,
                                             text="list of cells")
        self.cell_list_label.grid(row=1, column=0, sticky="W")
        self.listbox_frame = Frame(self.cell_frame)
        self.listbox_frame.grid(row=2, column=0, sticky="W")


        self.cell_position_list = Listbox(self.listbox_frame, width=60, height=10, font=("Helvetica", 12))
        self.cell_position_list.pack(side="left", fill="y")
        # self.cell_position_list.bind("<<ListboxSelect>>", self.cell_position_list_selection_changed)
        scrollbar = Scrollbar(self.listbox_frame, orient="vertical")
        scrollbar.config(command=self.cell_position_list.yview)
        scrollbar.pack(side="right", fill="y")

        self.cell_position_list.config(yscrollcommand=scrollbar.set)
        self.cells = []

        self.remove_cell_button = Button(self.cell_frame, text="Remove cell", command=self.remove_cell)
        self.remove_cell_button.grid(row=3, column=0, sticky="W")


        self.close_button = Button(self.input_frame, text="Continue with next image or processing, respectively", command=self.close_gui)
        self.close_button.grid(row=10, column=0, sticky="W")
        self.user_info_given = False

        self.cancel_button = Button(self.input_frame, text='Cancel', command=self.cancel)
        self.cancel_button.grid(row=11, column=0, sticky="W")

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

    def remove_cell(self):
        selected_item = self.cell_position_list.curselection()
        if(self.cell_position_list.size()>0 and selected_item!= ()):
            self.cell_position_list.delete(selected_item[0])
            self.cell_position_list.selection_set(END, END)
            self.cells.pop(selected_item[0])

    def add_cell(self):  # idea: RegEx für die Textboxen
        try:
            position_inside_cell = self.text_position_inside_cell.get("1.0", "end-1c").split(",")
            x_position_inside_cell = int(position_inside_cell[0])
            y_position_inside_cell = int(position_inside_cell[1])
            position_inside_cell = (x_position_inside_cell, y_position_inside_cell)

            self.cells.append(position_inside_cell)
            self.cell_position_list.insert(END, str(position_inside_cell))

            self.text_position_inside_cell.delete(1.0, END)
        except Exception as E:
            print(E)


    def mouse_clicked(self, event):
        if event.xdata is not None and event.ydata is not None:
            x_location = round(event.xdata)
            y_location = round(event.ydata)

            if(self.channel_width >= x_location >= 0 and self.image_height >= y_location >= 0):
                position_inside_cell_text = str(x_location) + "," + str(y_location)
                self.text_position_inside_cell.delete(1.0, END)
                self.text_position_inside_cell.insert(1.0, position_inside_cell_text)



    def run_main_loop(self):
        self.root.mainloop()

    def get_cell_positions(self):
        return self.cells

    def close_gui(self):
        self.root.destroy()




