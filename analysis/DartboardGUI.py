import tkinter
from analysis.Dartboard import DartboardGenerator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import (Tk, Label, Scale, Listbox, Scrollbar, Frame, Button, Radiobutton, IntVar, Text, HORIZONTAL, END)

import math
import skimage.io as io
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors

class DartboardGUI:
    def __init__(self,parameters, selected_dartboard_areas_for_timeline):
        self.root = Tk()
        # self.root.resizable(False, False)
        self.root.geometry(str(700) + "x" + str(650))
        self.root.title("dartboard timelines")
        self.root.bind('<Button-1>', self.mouse_clicked)
        self.dartboard_number_of_sections = parameters["properties"]["dartboard_number_of_sections"]
        self.dartboard_number_of_areas_per_section = parameters["properties"]["dartboard_number_of_areas_per_section"]
        self.dartboard_data = np.zeros(
            shape=(self.dartboard_number_of_areas_per_section, self.dartboard_number_of_sections))
        self.dartboard_generator = DartboardGenerator(None, None, None, None, None)
        self.selected_dartboard_areas_for_timeline = selected_dartboard_areas_for_timeline

        self.figure = self.create_dartboard()
        self.centroid_coords = (203, 239)  # measured with mouse... (x,y)

        self.canvas_frame = Frame(self.root, width=600, height=600)
        self.canvas_frame.place(x=10, y=10)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=1)

        self.save_and_close_button = Button(self.root, text="Save and close", command=self.save_and_close)
        self.save_and_close_button.place(x=30,y=500)

    def mouse_clicked(self, event):
        x = event.x
        y = event.y
        # print("Pointer is currently at %d, %d" % (x, y))
        dartboard_section, dartboard_area_number_within_section = self.dartboard_generator.assign_signal_to_dartboard_area((x,y), self.centroid_coords, self.dartboard_number_of_sections, self.dartboard_number_of_areas_per_section, 139)
        # print(str(dartboard_section))
        # print(str(dartboard_area_number_within_section))
        if dartboard_area_number_within_section is not None and dartboard_area_number_within_section > 4:  # if not bull's eye
            self.dartboard_data[dartboard_area_number_within_section][dartboard_section] = 1 - self.dartboard_data[dartboard_area_number_within_section][dartboard_section]

        """
        if dartboard_area_number_within_section > 4:  # not bull's eye
            if (self.dartboard_data[dartboard_area_number_within_section][dartboard_section]) == 0:  # toggle from 0 to 1
                self.dartboard_data[dartboard_area_number_within_section][dartboard_section] = 1
            else:
                self.dartboard_data[dartboard_area_number_within_section][dartboard_section] = 0
        else:
            self.toggle_bulls_eye()
        """

        # self.figure = self.create_dartboard()
        plt.close(self.canvas.figure)
        self.canvas.figure = self.create_dartboard()
        self.canvas.draw()

    def toggle_bulls_eye(self):
        for i in range(5):
            for n, col in enumerate(self.dartboard_data[i]):
                self.dartboard_data[i][n] = 1 - self.dartboard_data[i][n]

    def save_and_close(self):  # better use list comprehension
        for row in range(5, len(self.dartboard_data)):
            for col in range(len(self.dartboard_data[row])):
                if self.dartboard_data[row][col] == 1:
                    # col, row = self.calculate_corresponding_dartboard_field((col,row))
                    self.selected_dartboard_areas_for_timeline.append((col, row))
        self.root.destroy()

    def calculate_corresponding_dartboard_field(self, selected_area):
        dartboard_section = selected_area[0]
        # list = [3,2,1,12,11,10,9,8,7,6,5,4]
        # dartboard_section = list[dartboard_section]
        area_within_section = selected_area[1]
        return (dartboard_section, area_within_section)

    def create_dartboard(self):
        vmin = 0
        vmax = 1.0
        # red_sequential_cmap = plt.get_cmap("Reds")
        normalized_color = colors.Normalize(vmin=vmin, vmax=vmax)
        white_to_red_cmap = colors.LinearSegmentedColormap.from_list("", ["white", "red"])

        fig = plt.figure()
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)

        angle_per_section = 360.0 / self.dartboard_number_of_sections

        height_of_annuli = [0, 0, 0, 0, 0, 2, 1.544,
                            1.3049]  # manually calculated, so that the areas of the dartboard areas all have the area 2pi
        bottom_list = [0, 0, 0, 0, 0, 5, 7, 8.544, 9.8489]
        area_of_one_dartboard_area = (7 ** 2 * math.pi - 5 ** 2 * math.pi) * angle_per_section / 360.0
        area_of_bulls_eye = 5 ** 2 * math.pi
        area_ratio_bulls_eye_dartboard_area = area_of_bulls_eye / area_of_one_dartboard_area

        # create bull's eye
        number_of_signals_in_bulls_eye = 0
        for i in range(5):
            number_of_signals_in_bulls_eye += np.sum(self.dartboard_data[i])
        normalized_number_of_signals = number_of_signals_in_bulls_eye / area_ratio_bulls_eye_dartboard_area

        color = white_to_red_cmap(normalized_color(normalized_number_of_signals))

        ax.bar(x=0, height=5, width=2 * np.pi,
               bottom=0,
               color=color)

        # create dartboard areas outside of bull's eye
        for i in range(self.dartboard_number_of_sections):
            center_angle = math.radians((i * angle_per_section + angle_per_section / 2) % 360.0)

            for dartboard_area in range(self.dartboard_number_of_areas_per_section):
                if (dartboard_area > 4):
                    number_of_signals_in_current_dartboard_area = self.dartboard_data[dartboard_area][i]

                    color = white_to_red_cmap(normalized_color(number_of_signals_in_current_dartboard_area))

                    ax.bar(x=center_angle, height=height_of_annuli[dartboard_area],
                           width=2 * np.pi / (self.dartboard_number_of_sections), bottom=bottom_list[dartboard_area],
                           color=color, edgecolor='lightgray')

        plt.ylim(0, 9.85)

        ax.grid(False)  # test

        ax.set_yticks([])
        ax.axis("on")  # test
        ax.set_xticks((np.pi / 180.) * np.linspace(165, -195, 12, endpoint=False))
        ax.set_xticklabels(['10', '11', '12', '1', '2', '3', '4', '5', '6', '7', '8', '9'])
        ax.set_thetalim(-np.pi, np.pi)
        # ax.set_xticks(np.pi / 180. * np.linspace(180, -180, 12, endpoint=False))

        # ax.set_xticks([])

        plt.title('Click on the areas for single area timelines', x=0.5, y=1.15)

        sm = plt.cm.ScalarMappable(cmap=white_to_red_cmap, norm=normalized_color)
        sm.set_clim(vmin=vmin, vmax=vmax)
        plt.colorbar(sm, pad=0.3, label="")

        ax.annotate('Bead contact',
                    xy=(math.radians(45), 9.85),  # theta, radius
                    xytext=(0.6, 0.85),  # fraction, fraction
                    textcoords='figure fraction',
                    arrowprops=dict(facecolor='black', shrink=0.05, width=0.5),
                    horizontalalignment='left',
                    verticalalignment='bottom',
                    )

        return fig



    def run_main_loop(self):
        self.root.mainloop()

    def close_window(self):
        self.root.destroy()
