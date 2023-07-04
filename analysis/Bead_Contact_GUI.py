import tkinter

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import (Tk, ttk, Label, Scale, Listbox, Scrollbar, Frame, Button, LabelFrame,INSERT, OptionMenu,
                     Checkbutton, Radiobutton, IntVar,StringVar, Text, HORIZONTAL, END, Entry, Toplevel, Checkbutton)

import matplotlib.patches as mpatches
import math
import time

class BeadContactGUI():
    def __init__(self, image, cell_list, number_of_areas_dartboard, file_name, start_frame, end_frame):
        self.cell_list = cell_list
        self.bboxes_list_each_cell = self.give_bbox_list_for_each_cell(cell_list)
        self.coords_list_each_cell = self.give_coords_list_for_each_cell(cell_list)
        self.number_of_areas = number_of_areas_dartboard
        self.image = image
        self.image_width = len(image[0][0])
        self.image_height = len(image[0])
        self.GUI_width, self.GUI_height = round(self.image_width * 2.2), round(self.image_height * 1.2)

        self.number_of_frames = len(image)

        self.root = Tk()
        self.root.resizable(False, False)
        self.root.geometry(str(self.GUI_width) + "x" + str(self.GUI_height))
        self.root.title("Definition of bead contact sites, " + file_name)

        self.figure = Figure()
        self.subplot_image = self.figure.add_subplot(111)
        self.subplot_image.imshow(image[0])

        self.subplot_image.set_axis_off()
        self.canvas_frame = Frame(self.root)
        self.canvas_frame.place(x=10, y=10)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=1)
        self.canvas.mpl_connect('button_press_event', self.mouse_clicked)
        self.start_frame = start_frame
        self.end_frame = end_frame

        self.slider = Scale(self.root, from_=start_frame, to=end_frame-1, orient=HORIZONTAL,

                           command=self.update_image)

        self.slider.place(x=self.image_width * 0.2, y=self.image_height * 1.1)


        self.input_frame = Frame(self.root)
        self.input_frame.place(x=750, y=50)
        self.cell_list_label = Label(self.input_frame, text="cells")
        self.cell_list_label.grid(row=0, column=0, sticky="W")

        self.frame_cell_list = Frame(self.input_frame)
        self.frame_cell_list.grid(row=1, column=0, sticky="W")


        self.cell_listbox = Listbox(self.frame_cell_list, width=30, height=10, font=("Helvetica", 12))
        self.cell_listbox.pack(side="left", fill="y")
        self.cell_listbox.bind("<<ListboxSelect>>", self.cell_selection_changed)
        scrollbar = Scrollbar(self.frame_cell_list, orient="vertical")
        scrollbar.config(command=self.cell_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.cell_listbox.config(yscrollcommand=scrollbar.set)


        for cell_index in range(len(cell_list)):
            self.cell_listbox.insert(END, "cell : " + str(cell_index))


        self.bead_contact_list_label = Label(self.input_frame, text="list of bead contacts (location, frame, cell index)")
        self.bead_contact_list_label.grid(row=2, column=0, sticky="W")

        self.bead_contact_frame = Frame(self.input_frame)
        self.bead_contact_frame.grid(row=3, column=0, sticky="W")

        self.bead_contact_list = Listbox(self.bead_contact_frame, width=30, height=10, font=("Helvetica", 12))
        self.bead_contact_list.pack(side="left", fill="y")
        self.bead_contact_list.bind("<<ListboxSelect>>", self.bead_contact_list_selection_changed)
        scrollbar = Scrollbar(self.bead_contact_frame, orient="vertical")
        scrollbar.config(command=self.bead_contact_list.yview)
        scrollbar.pack(side="right", fill="y")

        self.bead_contact_list.config(yscrollcommand=scrollbar.set)
        self.bead_contacts = []


        self.remove_bead_contact_button = Button(self.input_frame, text="Remove bead contact", command=self.remove_bead_contact)
        self.remove_bead_contact_button.grid(row=4, column=0, sticky="W")

        self.manual_input_frame = Frame(self.input_frame)
        self.manual_input_frame.grid(row=5, column=0, sticky='W')


        self.label_manual_input = Label(self.manual_input_frame, text="Manual input")
        self.label_manual_input.grid(row=0, column=0, sticky="W")
        self.label_manual_input.config(bg='lightgray')
        self.label_frame_input = Label(self.manual_input_frame, text="Frame")
        self.label_frame_input.grid(row=1, column=0, sticky="W")
        self.text_frame = Text(self.manual_input_frame, height=1, width=10)
        self.text_frame.grid(row=1, column=1, sticky="W")
        self.label_clock_input = Label(self.manual_input_frame, text="clock")
        self.label_clock_input.grid(row=2, column=0, sticky="W")
        self.text_time_on_clock = Text(self.manual_input_frame, height=1, width=10)
        self.text_time_on_clock.grid(row=2, column=1, sticky="W")

        self.add_bead_contact_button = Button(self.manual_input_frame, text="add bead contact", command=self.manual_bead_contact_input)
        self.add_bead_contact_button.grid(row=3, column=1, sticky="W")



        self.close_button = Button(self.root, text="Continue analysis", command=self.close_gui)
        self.close_button.place(x=950, y=550)





    def give_bbox_list_for_each_cell(self, cell_list):
        bbox_list_all_cells = []
        for cell in cell_list:
            bbox_list_cell_channel_1 = cell.return_bbox_list_channel_1()
            bbox_list_cell_channel_2 = cell.return_bbox_list_channel_2()
            bbox_list_all_cells.append((bbox_list_cell_channel_1, bbox_list_cell_channel_2))

        return bbox_list_all_cells

    def give_coords_list_for_each_cell(self, cell_list):
        coords_list_all_cells = []
        for cell in cell_list:
            coords_list_cell_channel_2 = cell.return_coords_list_channel_2()
            coords_list_all_cells.append(coords_list_cell_channel_2)
        return coords_list_all_cells

    def manual_bead_contact_input(self):
        if self.cell_listbox.curselection() != ():
            location_on_clock = int(self.text_time_on_clock.get("1.0","end-1c"))
            frame = int(self.text_frame.get("1.0","end-1c"))
            cell_index = int(self.cell_listbox.curselection()[0])
            if frame in range(self.number_of_frames) and location_on_clock in range(1,13):
                bead_contact = BeadContact(location_on_clock, frame, cell_index)
                self.bead_contacts.append(bead_contact)
                self.bead_contact_list.insert(END, bead_contact.to_string())
                self.text_frame.delete(1.0, END)
                self.text_time_on_clock.delete(1.0, END)
                self.update_image(frame, cell_index)



    def bboxes_for_cell(self, frame, cell_index = None):
        if self.cell_listbox.curselection() != () or self.bead_contact_list.curselection() != ():
            bboxes = []
            relevant_frame = frame
            if self.cell_listbox.size() > 0:

                if self.cell_listbox.curselection() != ():
                    index_selected_cell = self.cell_listbox.curselection()[0]
                    self.cell_listbox.selection_clear(0, END)
                    self.cell_listbox.selection_set(index_selected_cell, index_selected_cell)
                else:
                    relevant_frame = self.get_frame_from_selection_in_bead_contact_list()
                    index_selected_cell = self.get_cell_index_from_selection_in_bead_contact_list()

                cell_frame_bbox_channel_1 = self.bboxes_list_each_cell[index_selected_cell][0]
                cell_frame_bbox_channel_2 = self.bboxes_list_each_cell[index_selected_cell][1]
                bboxes.append(cell_frame_bbox_channel_1[relevant_frame])
                bboxes.append(cell_frame_bbox_channel_2[relevant_frame])
                return bboxes
        else:
            return None

    def cell_selection_changed(self, event):
        self.update_image(self.slider.get())

    def get_frame_from_selection_in_bead_contact_list(self):
        if self.bead_contact_list.curselection() != ():
            selection = self.bead_contact_list.curselection()[0]
            frame = self.bead_contacts[selection].return_frame_number()
            return frame

    def get_cell_index_from_selection_in_bead_contact_list(self):
        if self.bead_contact_list.curselection() != ():
            selection = self.bead_contact_list.curselection()[0]
            cell_index = self.bead_contacts[selection].return_cell_index()
            return cell_index


    def bead_contact_list_selection_changed(self, event):
        if self.bead_contact_list.curselection() != ():
            frame = self.get_frame_from_selection_in_bead_contact_list()
            cell_index = self.get_cell_index_from_selection_in_bead_contact_list()
            self.slider.set(frame)
            self.update_image(frame, cell_index)

    def update_image(self, new_frame, cell_index = None):
        new_frame_in_short_image = int(new_frame) - self.start_frame
        new_image = self.image[int(new_frame_in_short_image)]

        self.figure.delaxes(self.figure.axes[0])
        self.subplot_image = self.figure.add_subplot(111)
        self.subplot_image.imshow(new_image)

        bboxes_for_frame_and_cell = self.bboxes_for_cell(int(new_frame_in_short_image), cell_index)
        if bboxes_for_frame_and_cell is not None:
            for bbox in bboxes_for_frame_and_cell:
                minr, minc, maxr, maxc = bbox
                rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                                          fill=False, edgecolor='red', linewidth=1)
                self.subplot_image.add_patch(rect)

        self.subplot_image.set_axis_off()

        self.canvas.draw()
        # self.canvas.get_tk_widget().pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=1)

    def remove_bead_contact(self):
        selected_item = self.bead_contact_list.curselection()
        if(self.bead_contact_list.size()>0 and selected_item!= ()):
            self.bead_contact_list.delete(selected_item[0])
            self.bead_contact_list.selection_set(END,END)

            self.bead_contacts.pop(selected_item[0])




    def mouse_clicked(self, event):
        if event.xdata is not None and event.ydata is not None:
            x_location = round(event.xdata)
            y_location = round(event.ydata)
            cell_listbox_selection = self.cell_listbox.curselection()

            if(self.image_width*0.5 >= x_location >= 0 and self.image_height >= y_location >= 0 and self.cell_listbox.size()>0 and cell_listbox_selection != ()):
                # print("im richtigen Bereich")
                frame = self.slider.get()
                cell_index = self.cell_listbox.curselection()[0]
                if (not self.cell_already_in_bead_contact_list(cell_index)):

                    centroid_coord_x_cell_frame = self.coords_list_each_cell[cell_index][frame][0]
                    centroid_coord_y_cell_frame = self.coords_list_each_cell[cell_index][frame][1]
                    location_on_clock = self.calculate_contact_position(x_location, y_location, centroid_coord_x_cell_frame, centroid_coord_y_cell_frame, self.number_of_areas)

                    bead_contact = BeadContact(location_on_clock, frame, int(cell_index))
                    self.bead_contacts.append(bead_contact)
                    self.bead_contact_list.insert(END, bead_contact.to_string())

    def cell_already_in_bead_contact_list(self, cell_index):
        cell_index_string = "cell: " + str(cell_index)
        bead_contacts_as_list = self.bead_contact_list.get(0, END)
        for string in bead_contacts_as_list:
            if cell_index_string in string:
                return True
        return False

    def run_main_loop(self):
        self.root.mainloop()

    def assign_bead_contacts_to_cells(self):
        for bead_contact in self.bead_contacts:
            cell_index = bead_contact.return_cell_index()
            start_frame = bead_contact.return_frame_number()
            location = bead_contact.return_location()
            self.cell_list[cell_index].time_of_bead_contact = start_frame
            self.cell_list[cell_index].bead_contact_site = location
            self.cell_list[cell_index].has_bead_contact = True



    def close_gui(self):

        self.assign_bead_contacts_to_cells()

        self.root.destroy()

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

    def return_bead_contact_information(self):
        return self.bead_contacts



class BeadContact():
    def __init__(self, location, frame_number, cell_index):
        self.location = location
        self.frame_number = frame_number
        self.cell_index = cell_index

    def to_string(self):
        return "location on clock" + str(self.location) + "- frame: " + str(self.frame_number) + "- cell: " + str(self.cell_index)

    def return_location(self):
        return self.location

    def return_frame_number(self):
        return self.frame_number

    def return_cell_index(self):
        return self.cell_index

