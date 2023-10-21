import tkinter

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import (Tk, Label, Scale, Listbox, Scrollbar, Frame, Button, Radiobutton, IntVar, Text, HORIZONTAL, END)

import math
import skimage.io as io


class BeadContactGUI():
    def __init__(self, file, filepath, bead_contact_dict, parameters):
        self.file = file
        self.image = io.imread(filepath)
        self.number_of_frames, self.image_height, self.image_width = self.image.shape
        self.GUI_width, self.GUI_height = 1200, 800  # round(self.image_width * 2.2), round(self.image_height * 1.2)
        if parameters["properties"]["channel_format"] == "two-in-one":
            self.channel_width = self.image_width*0.5
        elif parameters["properties"]["channel_format"] == "single":
            self.channel_width = self.image_width

        self.bead_contact_dict = bead_contact_dict
        self.root = Tk()
        self.root.resizable(False, False)
        self.root.geometry(str(self.GUI_width) + "x" + str(self.GUI_height))
        self.root.title("Definition of bead contact sites, " + file)

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


        self.label_bead_contact_information = Label(self.input_frame, text="Bead contact information: x, y, t")
        self.label_bead_contact_information.grid(row=1, column=0, sticky="W")
        self.text_bead_contact_information = Text(self.input_frame, height=1, width=30)
        self.text_bead_contact_information.grid(row=2, column=0, sticky="W")

        self.label_position_inside_cell = Label(self.input_frame, text="Position inside cell: x,y")
        self.label_position_inside_cell.grid(row=3, column=0, sticky="W")
        self.text_position_inside_cell = Text(self.input_frame, height=1, width=30)
        self.text_position_inside_cell.grid(row=4, column=0, sticky="W")

        self.add_bead_contact_button = Button(self.input_frame, bg='red', text="ADD bead contact",
                                                 command=self.add_bead_contact)
        self.add_bead_contact_button.grid(row=5, column=0, sticky="W")

        self.mouse_click_input = IntVar()
        self.input_button_1 = Radiobutton(self.input_frame, text='bead contact: x, y, t', value=1,
                                                      variable=self.mouse_click_input)
        self.input_button_2 = Radiobutton(self.input_frame, text='Choose cell by clicking a point inside', value=2,
                                                      variable=self.mouse_click_input)
        self.input_button_1.grid(row=6, column=0, sticky="W")
        self.input_button_2.grid(row=7, column=0, sticky="W")


        self.bead_contact_frame = Frame(self.input_frame)
        self.bead_contact_frame.grid(row=9, column=0, sticky="W")
        self.bead_contact_list_label = Label(self.bead_contact_frame,
                                             text="list of bead contacts (position, frame, position inside cell)")
        self.bead_contact_list_label.grid(row=1, column=0, sticky="W")
        self.listbox_frame = Frame(self.bead_contact_frame)
        self.listbox_frame.grid(row=2, column=0, sticky="W")


        self.bead_contact_list = Listbox(self.listbox_frame, width=60, height=10, font=("Helvetica", 12))
        self.bead_contact_list.pack(side="left", fill="y")
        self.bead_contact_list.bind("<<ListboxSelect>>", self.bead_contact_list_selection_changed)
        scrollbar = Scrollbar(self.listbox_frame, orient="vertical")
        scrollbar.config(command=self.bead_contact_list.yview)
        scrollbar.pack(side="right", fill="y")

        self.bead_contact_list.config(yscrollcommand=scrollbar.set)
        self.bead_contacts = []

        self.remove_bead_contact_button = Button(self.bead_contact_frame, text="Remove bead contact", command=self.remove_bead_contact)
        self.remove_bead_contact_button.grid(row=3, column=0, sticky="W")


        self.close_button = Button(self.input_frame, text="Continue with next image or processing, respectively", command=self.close_gui)
        self.close_button.grid(row=10, column=0, sticky="W")
        self.user_info_given = False

        self.cancel_button = Button(self.input_frame, text='Cancel', command=self.cancel)
        self.cancel_button.grid(row=11, column=0, sticky="W")

    def cancel(self):
        self.root.destroy()
        quit()

    def get_frame_from_selection_in_bead_contact_list(self):
        if self.bead_contact_list.curselection() != ():
            selection = self.bead_contact_list.curselection()[0]
            frame = self.bead_contacts[selection].return_time_of_bead_contact()
            return frame


    def bead_contact_list_selection_changed(self, event):
        if self.bead_contact_list.curselection() != ():
            frame = self.get_frame_from_selection_in_bead_contact_list()
            self.slider.set(frame)
            self.update_image(frame)

    def update_image(self, new_frame):
        new_image = self.image[int(new_frame)]
        self.figure.delaxes(self.figure.axes[0])
        self.subplot_image = self.figure.add_subplot(111)
        self.subplot_image.imshow(new_image)

        # self.subplot_image.set_axis_off()

        self.canvas.draw()
        # self.canvas.get_tk_widget().pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=1)

    def remove_bead_contact(self):
        selected_item = self.bead_contact_list.curselection()
        if(self.bead_contact_list.size()>0 and selected_item!= ()):
            self.bead_contact_list.delete(selected_item[0])
            self.bead_contact_list.selection_set(END, END)
            self.bead_contacts.pop(selected_item[0])

    def add_bead_contact(self):  # idea: RegEx für die Textboxen
        try:
            bead_contact_position = self.text_bead_contact_information.get("1.0", "end-1c").split(",")
            bead_contact_x_position = int(bead_contact_position[0])
            bead_contact_y_position = int(bead_contact_position[1])
            frame = int(bead_contact_position[2])
            bead_contact_position = (bead_contact_x_position, bead_contact_y_position)

            # frame = int(self.text_bead_contact_frame.get("1.0", "end-1c"))

            position_inside_cell = self.text_position_inside_cell.get("1.0", "end-1c").split(",")
            x_position_inside_cell = int(position_inside_cell[0])
            y_position_inside_cell = int(position_inside_cell[1])
            position_inside_cell = (x_position_inside_cell, y_position_inside_cell)

            bead_contact = BeadContact(bead_contact_position, frame, position_inside_cell)
            self.bead_contacts.append(bead_contact)
            self.bead_contact_list.insert(END, bead_contact.to_string())

            self.text_bead_contact_information.delete(1.0, END)
            self.text_position_inside_cell.delete(1.0, END)
            # self.text_bead_contact_frame.delete(1.0, END)
        except Exception as E:
            print(E)


    def mouse_clicked(self, event):
        if event.xdata is not None and event.ydata is not None:
            x_location = round(event.xdata)
            y_location = round(event.ydata)

            if(self.channel_width >= x_location >= 0 and self.image_height >= y_location >= 0):
                if self.mouse_click_input.get() == 1:  # if bead contact position/frame have to be selected
                    frame = self.slider.get()
                    self.text_bead_contact_information.delete(1.0, END)
                    self.text_bead_contact_information.insert(1.0, str(x_location) + ', ' + str(y_location) + ', ' + str(frame))

                elif self.mouse_click_input.get() == 2:  # if position inside cell has to be defined
                    position_inside_cell_text = str(x_location) + "," + str(y_location)
                    self.text_position_inside_cell.delete(1.0, END)
                    self.text_position_inside_cell.insert(1.0, position_inside_cell_text)



    def run_main_loop(self):
        self.root.mainloop()


    """
    def assign_bead_contacts_to_cells(self):
        for bead_contact in self.bead_contacts:
            cell_index = bead_contact.return_cell_index()
            start_frame = bead_contact.return_frame_number()
            location = bead_contact.return_location()
            self.cell_list[cell_index].time_of_bead_contact = start_frame
            self.cell_list[cell_index].bead_contact_site = location
            self.cell_list[cell_index].has_bead_contact = True
    """


    def close_gui(self):
        self.insert_bead_contacts_into_dict()
        self.root.destroy()

    def insert_bead_contacts_into_dict(self):
        self.bead_contact_dict[self.file] = self.bead_contacts

    def return_bead_contact_information(self):
        return self.bead_contacts




class BeadContact():
    def __init__(self, bead_contact_position, time_of_bead_contact, selected_position_inside_cell):
        self.bead_contact_position = bead_contact_position
        self.time_of_bead_contact = time_of_bead_contact
        self.selected_position_inside_cell = selected_position_inside_cell

    def to_string(self):
        return "bead contact position" + str(self.bead_contact_position) + "- frame: " + str(self.time_of_bead_contact) + "- position inside cell: " + str(self.selected_position_inside_cell)

    def return_bead_contact_position(self):
        return self.bead_contact_position

    def return_time_of_bead_contact(self):
        return self.time_of_bead_contact

    def return_selected_position_inside_cell(self):
        return self.selected_position_inside_cell

    def calculate_contact_position(self, contact_site_xpos, contact_site_ypos, cell_centroid_x, cell_centroid_y, number_of_areas):
        angle = self.calculate_contact_site_angle_relative_to_center(contact_site_xpos, contact_site_ypos, cell_centroid_x, cell_centroid_y)
        location_on_clock = self.assign_angle_to_clock(angle, number_of_areas)
        return location_on_clock

    def calculate_contact_site_angle_relative_to_center(self, contact_site_xpos, contact_site_ypos, cell_centroid_x, cell_centroid_y):
        y0 = cell_centroid_y
        x0 = cell_centroid_x
        x = contact_site_xpos
        y = contact_site_ypos
        angle = (math.degrees(math.atan2(y0 - y, x0 - x)) + 180) % 360
        return angle

    def assign_angle_to_clock(self, angle, number_of_sections):
        angle_one_section = 360.0 / number_of_sections
        dartboard_area = int(angle / angle_one_section)
        clock_list = [4,5,6,7,8,9,10,11,12,1,2,3]
        location_on_clock = clock_list[dartboard_area]
        return location_on_clock



