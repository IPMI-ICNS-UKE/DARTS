import pandas as pd
import math


class FrameRange:
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path
        self.bead_contact_KO_table = pd.read_excel(excel_file_path, sheet_name="HN1L KO", usecols="A:E",
                                              skiprows=[0, 1])
        self.bead_contact_KO_table = self.bead_contact_KO_table.dropna()
        self.file_names_KO = self.bead_contact_KO_table['Dateiname'].values.tolist()
        self.start_frames_KO = self.bead_contact_KO_table['Start-Frame Analyse'].values.tolist()
        self.end_frames_KO = self.bead_contact_KO_table['End-Frame Analyse'].values.tolist()

        self.bead_contact_WT_table = pd.read_excel(excel_file_path, sheet_name="HN1L WT", usecols="A:E",
                                              skiprows=[0, 1])
        self.bead_contact_WT_table = self.bead_contact_WT_table.dropna()
        self.file_names_WT = self.bead_contact_WT_table['Dateiname'].values.tolist()
        self.start_frames_WT = self.bead_contact_WT_table['Start-Frame Analyse'].values.tolist()
        self.end_frames_WT = self.bead_contact_WT_table['End-Frame Analyse'].values.tolist()

        self.KO_file_bead_contact_dict = {}
        for i, filename in enumerate(self.file_names_KO):
            start_frame = int(self.start_frames_KO[i])
            end_frame = int(self.end_frames_KO[i])
            self.KO_file_bead_contact_dict[filename] = (start_frame, end_frame)

        self.WT_file_bead_contact_dict = {}
        for i, filename in enumerate(self.file_names_WT):
            start_frame = int(self.start_frames_WT[i])
            end_frame = int(self.end_frames_WT[i])
            self.WT_file_bead_contact_dict[filename] = (start_frame, end_frame)

    def give_KO_file_bead_contact_dict(self):
        return self.KO_file_bead_contact_dict

    def give_WT_file_bead_contact_dict(self):
        return self.WT_file_bead_contact_dict



