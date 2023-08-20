from tkinter import Tk, Text, Label, IntVar, Checkbutton, Button, filedialog, END
from analysis.Dartboard import DartboardGenerator


root = Tk()
root.geometry(str(700) + "x" + str(300))
root.title("Create a dartboard plot")

label_start_time_in_seconds = Label(root, text="Start time in seconds, e.g. 0.0")
label_start_time_in_seconds.grid(row=0, column=0, sticky="W")

text_start_time_in_seconds = Text(root, height=1, width=30)
text_start_time_in_seconds.grid(row=0, column=1, sticky="W")

label_end_time_in_seconds = Label(root, text="End time in seconds, e.g. 5.0")
label_end_time_in_seconds.grid(row=1, column=0, sticky="W")

text_end_time_in_seconds = Text(root, height=1, width=30)
text_end_time_in_seconds.grid(row=1, column=1, sticky="W")

label_frames_per_second = Label(root, text="frames per second in measurement, e.g. 40.0")
label_frames_per_second.grid(row=2, column=0, sticky="W")

text_frames_per_second = Text(root, height=1, width=30)
text_frames_per_second.grid(row=2, column=1, sticky="W")

label_maximum_value_colorbar = Label(root, text="maximum color bar value")
label_maximum_value_colorbar.grid(row=3, column=0, sticky="W")

text_maximum_value_colorbar = Text(root, height=1, width=30)
text_maximum_value_colorbar.grid(row=3, column=1, sticky="W")

label_save_path = Label(root, text="save path")
label_save_path.grid(row=4, column=0, sticky="W")

text_save_path = Text(root, height=1, width=30)
text_save_path.grid(row=4, column=1, sticky="W")

def save_path():
    results_directory = filedialog.askdirectory()
    text_save_path.delete('1.0', END)
    text_save_path.insert(1.0, results_directory)

button_save_path = Button(root, text='Choose save path', command=save_path)
button_save_path.grid(row=4,column=2,sticky="W")

label_data_per_second_or_frame = Label(root, text="Data per second? If not, then per frame:  ")
label_data_per_second_or_frame.grid(row=5, column=0, sticky="W")
data_per_second = IntVar()
check_box_data_per_second = Checkbutton(root,
                                        variable=data_per_second,
                                        onvalue=1,
                                        offvalue=0)
check_box_data_per_second.grid(row=5, column=1, sticky="W")

def create_dartboard():  # RegEx!
    start_time = float(text_start_time_in_seconds.get("1.0", "end-1c"))
    end_time = float(text_end_time_in_seconds.get("1.0", "end-1c"))
    save_path = text_save_path.get("1.0", "end-1c")
    frame_rate = float(text_frames_per_second.get("1.0", "end-1c"))
    experiment_name = ""

    data_per_second_boolean = data_per_second.get() == 1
    dartboard_gen = DartboardGenerator(save_path, frame_rate, experiment_name, experiment_name, save_path)
    dartboard_gen.generate_dartboard(start_time, end_time, data_per_second=data_per_second_boolean, vmax_opt=float(text_maximum_value_colorbar.get("1.0", "end-1c")))
    root.destroy()

create_dartboard_button = Button(root, text='Choose files and create dartboard', command=create_dartboard)
create_dartboard_button.grid(row=6, column=1, sticky="W")

root.mainloop()
quit()



