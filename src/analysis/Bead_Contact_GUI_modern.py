from __future__ import annotations

import math
import sys

import numpy as np
import skimage.io as io
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class _Window(QMainWindow):
    def __init__(self, controller: "BeadContactGUI"):
        super().__init__()
        self.controller = controller

    def closeEvent(self, event):  # noqa: N802
        # X button: close without saving, same as cancel
        super().closeEvent(event)


class BeadContactGUI:
    def __init__(self, file: str, filepath: str, bead_contact_dict: dict, parameters: dict):
        self.file = file
        self.channel_format = parameters["input_output"]["image_conf"]
        self.image_raw = io.imread(filepath)
        self.image = self._prepare_display_image(self.image_raw, self.channel_format)
        self.number_of_frames, self.image_height, self.image_width = self.image.shape
        if self.channel_format == "two-in-one":
            self.channel_width = self.image_width * 0.5
        elif self.channel_format == "single":
            self.channel_width = self.image_width

        self.bead_contact_dict = bead_contact_dict
        self.bead_contacts: list[BeadContact] = []

        existing_app = QApplication.instance()
        self._owns_app = existing_app is None
        self.app = existing_app if existing_app is not None else QApplication(sys.argv)

        self.window = _Window(self)
        self.window.setWindowTitle("Definition of bead contact sites, " + file)
        self.window.resize(1200, 800)
        self.window.setMinimumSize(1000, 700)
        self.window.setStyleSheet(self._build_stylesheet())

        self._build_ui()

    # ------------------------------------------------------------------
    # Theming
    # ------------------------------------------------------------------

    def _is_dark_mode(self) -> bool:
        palette = self.app.palette()
        window_color = palette.color(QPalette.ColorRole.Window)
        return window_color.lightness() < 128

    def _build_stylesheet(self) -> str:
        if self._is_dark_mode():
            colors = {
                "text": "#e6edf3",
                "muted_text": "#9aa6b2",
                "window_bg": "#2b2f36",
                "group_bg": "#353a43",
                "group_border": "#7a7f87",
                "field_bg": "#262b33",
                "field_border": "#8a8f98",
                "button_bg": "#464c56",
                "button_border": "#8a8f98",
                "button_hover": "#555c68",
                "start_bg": "#1c98ff",
                "start_hover": "#0f8ef8",
                "start_border": "#1c98ff",
            }
        else:
            colors = {
                "text": "#1b2733",
                "muted_text": "#4e5a67",
                "window_bg": "#f3f6fb",
                "group_bg": "#fcfcfd",
                "group_border": "#d7dbe0",
                "field_bg": "#ffffff",
                "field_border": "#c7ced8",
                "button_bg": "#f6f8fb",
                "button_border": "#c7ced8",
                "button_hover": "#edf2f8",
                "start_bg": "#0b84ff",
                "start_hover": "#0876e4",
                "start_border": "#0b84ff",
            }

        return f"""
            QWidget {{
                font-size: 13px;
                color: {colors["text"]};
            }}
            QMainWindow, QWidget#centralwidget {{
                background: {colors["window_bg"]};
            }}
            QGroupBox {{
                font-weight: 600;
                border: 1px solid {colors["group_border"]};
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px 10px 8px 10px;
                background: {colors["group_bg"]};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }}
            QLabel {{
                color: {colors["text"]};
            }}
            QLineEdit {{
                min-height: 34px;
                padding: 4px 8px;
                border: 1px solid {colors["field_border"]};
                border-radius: 6px;
                background: {colors["field_bg"]};
                color: {colors["text"]};
            }}
            QListWidget {{
                border: 1px solid {colors["field_border"]};
                border-radius: 6px;
                background: {colors["field_bg"]};
                color: {colors["text"]};
            }}
            QPushButton {{
                padding: 6px 12px;
                border: 1px solid {colors["button_border"]};
                border-radius: 6px;
                background: {colors["button_bg"]};
                color: {colors["text"]};
            }}
            QPushButton:hover {{
                background: {colors["button_hover"]};
            }}
            QPushButton#StartButton {{
                background: {colors["start_bg"]};
                color: white;
                border: 1px solid {colors["start_border"]};
                font-weight: 600;
            }}
            QPushButton#StartButton:hover {{
                background: {colors["start_hover"]};
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: {colors["group_border"]};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
                background: {colors["start_bg"]};
            }}
        """

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("centralwidget")
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # --- Matplotlib canvas ---
        self.figure = Figure()
        self.figure.patch.set_facecolor("white")
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("white")
        self.ax.imshow(self.image[0])
        self.ax.axis("off")
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.mpl_connect("button_press_event", self.mouse_clicked)

        # --- Frame slider ---
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, self.number_of_frames - 1)
        self.slider.setValue(0)
        self.slider.setToolTip("Drag to browse through image frames.")
        self.slider.valueChanged.connect(self.update_image)

        canvas_col = QVBoxLayout()
        canvas_col.setSpacing(6)
        canvas_col.addWidget(self.canvas, stretch=1)
        canvas_col.addWidget(self.slider)

        # --- Right panel ---
        controls_col = QVBoxLayout()
        controls_col.setSpacing(8)
        controls_col.setContentsMargins(0, 0, 0, 0)

        # Click mode group
        mode_group = QGroupBox("Click mode")
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(6)

        self._click_mode_group = QButtonGroup(self.window)
        self.input_button_1 = QRadioButton("Bead contact: x, y, t")
        self.input_button_1.setChecked(True)
        self.input_button_1.setToolTip(
            "Click on the image to record a bead-cell contact site. The current frame is used as the time point."
        )
        self.input_button_2 = QRadioButton("Point inside cell")
        self.input_button_2.setToolTip(
            "Click on the image to mark a point inside the cell. Used to define the cell center."
        )
        self._click_mode_group.addButton(self.input_button_1, 1)
        self._click_mode_group.addButton(self.input_button_2, 2)
        mode_layout.addWidget(self.input_button_1)
        mode_layout.addWidget(self.input_button_2)
        controls_col.addWidget(mode_group)

        # Contact info group
        info_group = QGroupBox("Contact information")
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(6)

        info_layout.addWidget(QLabel("Bead contact: x, y, t"))
        self.text_bead_contact_information = QLineEdit()
        self.text_bead_contact_information.setToolTip(
            "Filled automatically by clicking the image. You can also type or paste coordinates manually (format: x, y, frame)."
        )
        info_layout.addWidget(self.text_bead_contact_information)

        info_layout.addWidget(QLabel("Position inside cell: x, y"))
        self.text_position_inside_cell = QLineEdit()
        self.text_position_inside_cell.setToolTip(
            "Filled automatically by clicking the image. You can also type or paste coordinates manually (format: x, y)."
        )
        info_layout.addWidget(self.text_position_inside_cell)

        self.add_bead_contact_button = QPushButton("ADD bead contact")
        self.add_bead_contact_button.setObjectName("StartButton")
        self.add_bead_contact_button.setToolTip(
            "Add the current bead contact and cell position to the list below."
        )
        self.add_bead_contact_button.clicked.connect(self.add_bead_contact)
        info_layout.addWidget(self.add_bead_contact_button)
        controls_col.addWidget(info_group)

        # Contact list group
        list_group = QGroupBox("Bead contacts (position, frame, cell position)")
        list_layout = QVBoxLayout(list_group)
        list_layout.setSpacing(6)

        self.bead_contact_list = QListWidget()
        self.bead_contact_list.setMinimumHeight(160)
        self.bead_contact_list.setMinimumWidth(420)
        self.bead_contact_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.bead_contact_list.setToolTip("All recorded bead contacts for this image.")
        self.bead_contact_list.currentRowChanged.connect(self.bead_contact_list_selection_changed)
        list_layout.addWidget(self.bead_contact_list)

        self.remove_bead_contact_button = QPushButton("Remove selected")
        self.remove_bead_contact_button.setToolTip("Remove the selected contact from the list.")
        self.remove_bead_contact_button.clicked.connect(self.remove_bead_contact)
        list_layout.addWidget(self.remove_bead_contact_button)
        controls_col.addWidget(list_group)

        controls_col.addStretch(1)

        # Content row
        content_row = QHBoxLayout()
        content_row.setSpacing(12)
        content_row.addLayout(canvas_col, stretch=1)
        content_row.addLayout(controls_col)

        main_layout.addLayout(content_row, stretch=1)

        # --- Bottom action bar ---
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setToolTip("Cancel and exit the program.")
        self.cancel_button.clicked.connect(self.cancel)

        self.continue_button = QPushButton("Continue")
        self.continue_button.setObjectName("StartButton")
        self.continue_button.setMinimumWidth(160)
        self.continue_button.setMinimumHeight(36)
        self.continue_button.setToolTip(
            "Save the recorded bead contacts and continue to the next image or processing step."
        )
        self.continue_button.clicked.connect(self.close_gui)

        action_row.addWidget(self.cancel_button)
        action_row.addStretch(1)
        action_row.addWidget(self.continue_button)

        main_layout.addLayout(action_row)

        self.window.setCentralWidget(central)

    # ------------------------------------------------------------------
    # Image helpers (unchanged logic from original)
    # ------------------------------------------------------------------

    def _prepare_display_image(self, image, channel_format):
        """Return a 3-D (T, H, W) stack for GUI display only; keep raw data intact."""
        if image.ndim == 3:
            return image
        if image.ndim == 4:
            if image.shape[-1] in (2, 3):
                return image[..., 0]
            if image.shape[0] in (2, 3):
                return image[0]
            if image.shape[1] in (2, 3):
                return image[:, 0, ...]
        squeezed = np.squeeze(image)
        if squeezed.ndim == 3:
            return squeezed
        raise ValueError(f"Unsupported image shape for GUI display: {image.shape}")

    # ------------------------------------------------------------------
    # Event handlers (unchanged logic from original)
    # ------------------------------------------------------------------

    def update_image(self, new_frame: int):
        new_image = self.image[int(new_frame)]
        self.ax.clear()
        self.ax.set_facecolor("white")
        self.ax.imshow(new_image)
        self.ax.axis("off")
        self.canvas.draw()

    def mouse_clicked(self, event):
        if event.xdata is not None and event.ydata is not None:
            x_location = round(event.xdata)
            y_location = round(event.ydata)
            if self.channel_width >= x_location >= 0 and self.image_height >= y_location >= 0:
                mode = self._click_mode_group.checkedId()
                if mode == 1:
                    frame = self.slider.value()
                    self.text_bead_contact_information.setText(
                        f"{x_location}, {y_location}, {frame}"
                    )
                elif mode == 2:
                    self.text_position_inside_cell.setText(f"{x_location},{y_location}")

    def get_frame_from_selection_in_bead_contact_list(self):
        row = self.bead_contact_list.currentRow()
        if row >= 0:
            return self.bead_contacts[row].return_time_of_bead_contact()
        return None

    def bead_contact_list_selection_changed(self, row: int):
        if row >= 0:
            frame = self.get_frame_from_selection_in_bead_contact_list()
            if frame is not None:
                self.slider.setValue(frame)
                self.update_image(frame)

    def add_bead_contact(self):
        try:
            bead_contact_position = self.text_bead_contact_information.text().split(",")
            bead_contact_x_position = int(bead_contact_position[0])
            bead_contact_y_position = int(bead_contact_position[1])
            frame = int(bead_contact_position[2])
            bead_contact_position = (bead_contact_x_position, bead_contact_y_position)

            position_inside_cell = self.text_position_inside_cell.text().split(",")
            x_position_inside_cell = int(position_inside_cell[0])
            y_position_inside_cell = int(position_inside_cell[1])
            position_inside_cell = (x_position_inside_cell, y_position_inside_cell)

            bead_contact = BeadContact(bead_contact_position, frame, position_inside_cell)
            self.bead_contacts.append(bead_contact)
            self.bead_contact_list.addItem(bead_contact.to_string())

            self.text_bead_contact_information.clear()
            self.text_position_inside_cell.clear()
        except Exception as e:
            print(e)

    def remove_bead_contact(self):
        row = self.bead_contact_list.currentRow()
        if self.bead_contact_list.count() > 0 and row >= 0:
            self.bead_contact_list.takeItem(row)
            self.bead_contacts.pop(row)
            new_count = self.bead_contact_list.count()
            if new_count > 0:
                self.bead_contact_list.setCurrentRow(new_count - 1)

    # ------------------------------------------------------------------
    # Public API (unchanged from original)
    # ------------------------------------------------------------------

    def run_main_loop(self):
        self.window.show()
        self.app.exec()

    def close_gui(self):
        self.insert_bead_contacts_into_dict()
        self.window.close()  # safe — closeEvent no longer calls back into close_gui

    def insert_bead_contacts_into_dict(self):
        self.bead_contact_dict[self.file] = self.bead_contacts

    def return_bead_contact_information(self) -> list:
        return self.bead_contacts

    def cancel(self):
        self.window.close()
        sys.exit(0)


# ---------------------------------------------------------------------------
# BeadContact helper class — unchanged from original
# ---------------------------------------------------------------------------

class BeadContact:
    def __init__(self, bead_contact_position, time_of_bead_contact, selected_position_inside_cell):
        self.bead_contact_position = bead_contact_position
        self.time_of_bead_contact = time_of_bead_contact
        self.selected_position_inside_cell = selected_position_inside_cell

    def to_string(self):
        return (
            "bead contact position"
            + str(self.bead_contact_position)
            + "- frame: "
            + str(self.time_of_bead_contact)
            + "- position inside cell: "
            + str(self.selected_position_inside_cell)
        )

    def return_bead_contact_position(self):
        return self.bead_contact_position

    def return_time_of_bead_contact(self):
        return self.time_of_bead_contact

    def return_selected_position_inside_cell(self):
        return self.selected_position_inside_cell

    def calculate_contact_position(self, contact_site_xpos, contact_site_ypos,
                                   cell_centroid_x, cell_centroid_y, number_of_areas):
        angle = self.calculate_contact_site_angle_relative_to_center(
            contact_site_xpos, contact_site_ypos, cell_centroid_x, cell_centroid_y
        )
        location_on_clock = self.assign_angle_to_clock(angle, number_of_areas)
        return location_on_clock

    def calculate_contact_site_angle_relative_to_center(self, contact_site_xpos, contact_site_ypos,
                                                         cell_centroid_x, cell_centroid_y):
        angle = (math.degrees(math.atan2(cell_centroid_y - contact_site_ypos,
                                          cell_centroid_x - contact_site_xpos)) + 180) % 360
        return angle

    def assign_angle_to_clock(self, angle, number_of_sections):
        angle_one_section = 360.0 / number_of_sections
        dartboard_area = int(angle / angle_one_section)
        clock_list = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]
        location_on_clock = clock_list[dartboard_area]
        return location_on_clock
