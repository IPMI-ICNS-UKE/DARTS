import tkinter

import skimage.io as io
from tkinter import (Tk, ttk, Label, Scale, Listbox, Scrollbar, Frame, Button, LabelFrame,INSERT, OptionMenu,
                     Checkbutton, Radiobutton, IntVar,StringVar, Text, HORIZONTAL, END, Entry, Toplevel, Checkbutton)
import numpy as np
from PIL import Image, ImageTk

from stardist.models import StarDist2D
from csbdeep.utils import normalize

class BeadContactGUI():
    def __init__(self, image, segmentation_labels):
        # self.model = StarDist2D.from_pretrained('2D_versatile_fluo')
        self.image_width = len(image[0][0])
        self.image_height = len(image[0])
        self.GUI_width, self.GUI_height = round(self.image_width*2), round(self.image_height*1.2)
        self.tiff_image_time_series = image  # io.imread("/Users/dejan/Documents/GitHub/T-DARTS/Data/170424 JMP HN1L-KO Beads/170424 HN1L K2 OKT3 Beads/170424 2.tif")
        self.number_of_frames = len(image)
        self.root = Tk()
        self.root.resizable(False, False)
        self.root.geometry(str(self.GUI_width) + "x" + str(self.GUI_height))
        self.root.title("Definition of bead contact sites")
        self.labels_in_each_frame = segmentation_labels
        label_first_frame = self.labels_in_each_frame[0]
        rendered_first_frame = self.return_rendered_image(0,label_first_frame)
        self.bead_contacts = []


        self.label = Label(self.root, image=rendered_first_frame, text="test")
        self.label.image = rendered_first_frame
        self.label.bind("<Button-1>",self.mouse_clicked)
        self.label.place(x=50,y=0)

        self.slider = Scale(self.root, from_=0, to=self.number_of_frames - 1, orient=HORIZONTAL, command=self.update_image)
        self.slider.place(x=self.image_width*0.2,y=self.image_height*1.1)

        self.frame = Frame(self.root)
        self.frame.place(x=650,y=100)

        self.listbox = Listbox(self.frame, width=30, height=30, font=("Helvetica", 12))
        self.listbox.pack(side="left", fill="y")

        scrollbar = Scrollbar(self.frame, orient="vertical")
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")

        self.listbox.config(yscrollcommand=scrollbar.set)


        self.root.mainloop()

    def mouse_clicked(self, event):
        print("clicked at", event.x, event.y)
        frame_number = self.slider.get()
        location = (int(event.x), int(event.y))
        if(self.image_width/2 >= int(event.x)>=0 and self.image_height >= int(event.y) >= 0):
            bead_contact_site = BeadContactSite(location,frame_number)
            self.bead_contacts.append(bead_contact_site)
            self.listbox.insert(END, bead_contact_site.to_string())



    def update_image(self, new_frame):
        label = self.labels_in_each_frame[int(new_frame)-1]
        new_rendered_image = self.return_rendered_image(int(new_frame)-1, label)
        self.label.configure(image=new_rendered_image)
        self.label.image = new_rendered_image

    def return_rendered_image(self, frame, label):
        image_frame = self.tiff_image_time_series[frame]
        image_frame[label > 0] = 0
        converted_image = np.uint8(image_frame)
        converted_image = Image.fromarray(converted_image)
        rendered_image = ImageTk.PhotoImage(converted_image)
        return rendered_image


class BeadContactSite():
    def __init__(self, location, frame_number):
        self.location = location
        self.frame_number = frame_number

    def to_string(self):
        return "x position: " + str(self.location[0]) + "- y position: " + str(self.location[1]) +  "- frame: " + str(self.frame_number)


image = io.imread("/Users/dejan/Documents/GitHub/T-DARTS/Data/170424 JMP HN1L-KO Beads/170424 HN1L K2 OKT3 Beads/170424 2.tif")
image = image[0:10,:,:]
channel1, channel2 = np.split(image, 2, axis=2)

def segment_cells_in_each_frame(image):
    model = StarDist2D.from_pretrained('2D_versatile_fluo')
    labels_list = []
    for frame in range(len(image)):
        img_labels, img_details = model.predict_instances(normalize(image[frame]))
        labels_list.append(img_labels)
    return labels_list

def expand_channel(labels_list):
    width = len(labels_list[0][0])
    height = len(labels_list[0])
    double_sized_list = []
    frame_number = len(labels_list)

    for frame in range(frame_number):
        double_size = np.zeros(shape=(width*2, height))
        double_sized_list.append(double_size)

    for frame in range(frame_number):
        double_sized_list[frame][0:height,0:width] = labels_list[frame]
        double_sized_list[frame][0:height,(width):(2*width)] = labels_list[frame]

    return double_sized_list


labels = segment_cells_in_each_frame(channel2)
double_labels = expand_channel(labels)  # from (500,250) to (500,500)
bead_contact_gui = BeadContactGUI(image, double_labels)






# test