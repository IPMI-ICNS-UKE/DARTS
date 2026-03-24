from __future__ import annotations

import sys

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
    QMainWindow,
    QPushButton,
    QRadioButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from src.general.RatioToConcentrationConverter import RatioConverter


class _Window(QMainWindow):
    def __init__(self, controller: "GUInoBeads_local"):
        super().__init__()
        self.controller = controller

    def closeEvent(self, event):  # noqa: N802
        self.controller.close_gui()
        super().closeEvent(event)


class GUInoBeads_local:
    # Class variable to remember the last chosen method across all instances
    _last_method_choice = 1  # Default to original method

    def __init__(self, cell, cell_index, parameters, ratioconverter, processor=None):
        self.channel_format = parameters["input_output"]["image_conf"]
        self.image = cell.ratio
        self.mean_ratio_list = cell.mean_ratio_list
        self.calcium_c = []
        self.starting_point_auto = cell.starting_point_auto
        self.cell_denied_flag = False
        self.cell_type = parameters["properties_of_measurement"]["cell_type"]
        self.processor = processor
        self.cell = cell
        self.starting_frame = None

        self.spotHeight = None
        if self.cell_type == "primary":
            self.spotHeight = 112.5
        elif self.cell_type == "jurkat":
            self.spotHeight = 72
        elif self.cell_type == "NK":
            self.spotHeight = 72
        elif self.cell_type == "NK_human":
            self.spotHeight = 72

        self.ratio_converter = ratioconverter
        self.number_of_frames, self.image_height, self.image_width = self.image.shape

        # Concentration conversion
        for ip in self.mean_ratio_list:
            c, _, _ = self.ratio_converter.calcium_calibration(ip, self.cell_type, self.spotHeight)
            self.calcium_c.append(c)

        existing_app = QApplication.instance()
        self._owns_app = existing_app is None
        self.app = existing_app if existing_app is not None else QApplication(sys.argv)

        self.window = _Window(self)
        self.window.setWindowTitle("GUI no beads local, cell number: " + str(cell_index))
        self.window.resize(1200, 900)
        self.window.setMinimumSize(1000, 700)
        self.window.setStyleSheet(self._build_stylesheet())

        self._build_ui()

        # Restore last remembered method choice
        if GUInoBeads_local._last_method_choice == 2:
            self.method_radio2.setChecked(True)
        else:
            self.method_radio1.setChecked(True)

        self.update_auto_method()

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

        # --- Matplotlib figure with two subplots ---
        self.figure = Figure(figsize=(10, 5))
        self.figure.patch.set_facecolor("white")
        self.figure.subplots_adjust(wspace=0.6)

        self.subplot_image = self.figure.add_subplot(121)
        self.subplot_image.set_facecolor("white")
        im = self.subplot_image.imshow(
            self.image[0], cmap="nipy_spectral", vmin=0.1, vmax=1.0
        )
        self.colorbar = self.figure.colorbar(
            im, ax=self.subplot_image, orientation="vertical", fraction=0.046, pad=0.04
        )
        self.colorbar.set_label("Ratio")
        # Keep colorbar tick/label colors black for readability
        self.colorbar.ax.yaxis.set_tick_params(color="black")
        self.colorbar.ax.yaxis.label.set_color("black")

        self.global_signal_subplot = self.figure.add_subplot(122)
        self.global_signal_subplot.set_facecolor("white")
        self.global_signal_subplot.plot(self.calcium_c, color="blue")
        self.global_signal_subplot.set_title("Global Ca concentration", color="black")
        self.global_signal_subplot.set_xlabel("Frame", color="black")
        self.global_signal_subplot.set_ylabel("Mean Intensity", color="black")
        self.global_signal_subplot.tick_params(colors="black")
        self.global_signal_subplot.set_ylim(0, max(self.calcium_c))
        self.vertical_line = self.global_signal_subplot.axvline(
            x=self.starting_point_auto, color="red", linestyle="--"
        )

        self.canvas = FigureCanvasQTAgg(self.figure)

        # --- Frame slider ---
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, self.number_of_frames - 1)
        self.slider.setValue(self.starting_point_auto)
        self.slider.setToolTip("Drag to browse through image frames.")
        self.slider.valueChanged.connect(self.update_image)

        canvas_col = QVBoxLayout()
        canvas_col.setSpacing(6)
        canvas_col.addWidget(self.canvas, stretch=1)
        canvas_col.addWidget(self.slider)

        main_layout.addLayout(canvas_col, stretch=1)

        # --- Starting point controls ---
        sp_group = QGroupBox("Starting Point")
        sp_layout = QVBoxLayout(sp_group)
        sp_layout.setSpacing(8)

        self.starting_frame_label = QLabel(
            f"Current Starting Frame: {self.starting_point_auto}, automatically set"
        )
        sp_layout.addWidget(self.starting_frame_label)

        method_row = QHBoxLayout()
        method_row.setSpacing(16)
        method_label = QLabel("Method:")
        method_row.addWidget(method_label)

        self._method_group = QButtonGroup(self.window)
        self.method_radio1 = QRadioButton("Original Method")
        self.method_radio1.setChecked(True)
        self.method_radio1.setToolTip(
            "Use the original automatic algorithm to detect the stimulation starting point."
        )
        self.method_radio2 = QRadioButton("Exponential Method")
        self.method_radio2.setToolTip(
            "Use an exponential-fit algorithm to detect the stimulation starting point."
        )
        self._method_group.addButton(self.method_radio1, 1)
        self._method_group.addButton(self.method_radio2, 2)
        self.method_radio1.toggled.connect(self.update_auto_method)
        self.method_radio2.toggled.connect(self.update_auto_method)
        method_row.addWidget(self.method_radio1)
        method_row.addWidget(self.method_radio2)
        method_row.addStretch(1)
        sp_layout.addLayout(method_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.set_manually_button = QPushButton("Set manually")
        self.set_manually_button.setToolTip(
            "Use the current slider position as the starting frame."
        )
        self.set_manually_button.clicked.connect(self.set_manually)
        self.set_automatically_button = QPushButton("Set automatically")
        self.set_automatically_button.setToolTip(
            "Let the selected algorithm determine the starting frame automatically."
        )
        self.set_automatically_button.clicked.connect(self.set_automatically)
        btn_row.addWidget(self.set_manually_button)
        btn_row.addWidget(self.set_automatically_button)
        btn_row.addStretch(1)
        sp_layout.addLayout(btn_row)

        main_layout.addWidget(sp_group)

        # --- Bottom action bar ---
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setToolTip("Cancel and exit the program.")
        self.cancel_button.clicked.connect(self.cancel)

        self.deny_button = QPushButton("Deny cell")
        self.deny_button.setToolTip("Exclude this cell from the analysis and continue.")
        self.deny_button.clicked.connect(self.deny_cell)

        self.accept_button = QPushButton("Accept && Continue")
        self.accept_button.setObjectName("StartButton")
        self.accept_button.setMinimumWidth(160)
        self.accept_button.setMinimumHeight(36)
        self.accept_button.setToolTip(
            "Accept the current starting frame and continue to the next cell."
        )
        self.accept_button.clicked.connect(self.close_and_continue_gui)

        action_row.addWidget(self.cancel_button)
        action_row.addStretch(1)
        action_row.addWidget(self.deny_button)
        action_row.addWidget(self.accept_button)

        main_layout.addLayout(action_row)

        self.window.setCentralWidget(central)

    # ------------------------------------------------------------------
    # Event handlers (unchanged logic from original)
    # ------------------------------------------------------------------

    def update_image(self, new_frame: int):
        new_frame = int(new_frame)
        new_image = self.image[new_frame]
        self.subplot_image.clear()
        self.subplot_image.set_facecolor("white")
        im = self.subplot_image.imshow(new_image, cmap="nipy_spectral", vmin=0.1, vmax=1.0)
        self.colorbar.update_normal(im)
        self.vertical_line.set_xdata([new_frame])
        self.canvas.draw()

    def set_manually(self):
        try:
            frame = self.slider.value()
            if 0 <= frame <= self.number_of_frames - 1:
                self.starting_frame = frame
                print(f"Starting frame set to: {frame}")
                self.starting_frame_label.setText(
                    f"Current Starting Frame: {frame}, manually set"
                )
            else:
                print("Invalid frame. Please enter a value within the valid range.")
        except ValueError:
            print("Invalid input. Please enter an integer.")

    def set_automatically(self):
        self.starting_frame = self.starting_point_auto
        if self.starting_point_auto > 0:
            self.starting_frame_label.setText(
                f"Current Starting Frame: {self.starting_frame}, automatically set"
            )
            self.update_image(self.starting_point_auto)
            self.slider.setValue(self.starting_point_auto)
        else:
            method_name = "Original" if self._method_group.checkedId() == 1 else "Exponential"
            self.starting_frame_label.setText(
                f"No starting point found, {method_name} method (set to -1)"
            )
            print(
                f"Warning: No valid starting point found by {method_name} method. "
                "Manual selection may be required."
            )

    def save_method_choice(self):
        GUInoBeads_local._last_method_choice = self._method_group.checkedId()

    def update_auto_method(self):
        if self.processor is not None:
            method_id = self._method_group.checkedId()
            if method_id == 1:
                self.starting_point_auto = self.processor.automated_starting_point(self.cell)
            elif method_id == 2:
                self.starting_point_auto = self.processor.find_exp_start(self.cell)
                if self.starting_point_auto == -1:
                    if hasattr(self.cell, "exp_start_diagnostics"):
                        reason = self.cell.exp_start_diagnostics.get("reason", "unknown")
                        print(f"Exponential method could not find a starting point. Reason: {reason}")
                    else:
                        print("Exponential method could not find a starting point.")

            self.cell.starting_point_auto = self.starting_point_auto

            if self.starting_point_auto > 0:
                self.vertical_line.set_xdata([self.starting_point_auto])
                self.canvas.draw()
            else:
                self.vertical_line.set_xdata([0])
                self.canvas.draw()

            method_name = "Original" if self._method_group.checkedId() == 1 else "Exponential"
            if self.starting_point_auto > 0:
                self.starting_frame_label.setText(
                    f"Current Starting Frame: {self.starting_point_auto}, {method_name} method"
                )
            else:
                self.starting_frame_label.setText(
                    f"No starting point found, {method_name} method (set to -1)"
                )

    def deny_cell(self):
        print("Cell denied.")
        self.cell_denied_flag = True
        self.save_method_choice()
        self.close_gui()

    def close_and_continue_gui(self):
        if self.starting_frame is None:
            print("No starting frame defined.")
        else:
            print(f"Starting frame: {self.starting_frame}")
        self.save_method_choice()
        self.window.close()

    # ------------------------------------------------------------------
    # Public API (unchanged from original)
    # ------------------------------------------------------------------

    def run_main_loop(self):
        self.window.show()
        self.app.exec()

    def close_gui(self):
        self.save_method_choice()
        self.window.close()

    def cancel(self):
        self.save_method_choice()
        self.window.close()
        QApplication.quit()
        quit()
