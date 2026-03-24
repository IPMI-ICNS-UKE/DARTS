from __future__ import annotations

import sys

import skimage.io as io
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class _Window(QMainWindow):
    def __init__(self, controller: "GUInoBeads"):
        super().__init__()
        self.controller = controller

    def closeEvent(self, event):  # noqa: N802
        self.controller.close_gui()
        super().closeEvent(event)


class GUInoBeads:
    def __init__(self, file: str, filepath: str, parameters: dict):
        self.file = file
        self.channel_format = parameters["input_output"]["image_conf"]
        self.image = io.imread(filepath)
        self.number_of_frames, self.image_height, self.image_width = self.image.shape
        if self.channel_format == "two-in-one":
            self.channel_width = self.image_width * 0.5
        elif self.channel_format == "single":
            self.channel_width = self.image_width

        existing_app = QApplication.instance()
        self._owns_app = existing_app is None
        self.app = existing_app if existing_app is not None else QApplication(sys.argv)

        self.window = _Window(self)
        self.window.setWindowTitle(
            "Global measurement, no bead contacts: Definition of time of addition, " + file
        )
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
            QSpinBox {{
                min-height: 34px;
                padding: 4px 8px;
                border: 1px solid {colors["field_border"]};
                border-radius: 6px;
                background: {colors["field_bg"]};
                color: {colors["text"]};
            }}
            QSpinBox::up-button {{
                width: 22px;
                subcontrol-origin: border;
                subcontrol-position: top right;
            }}
            QSpinBox::down-button {{
                width: 22px;
                subcontrol-origin: border;
                subcontrol-position: bottom right;
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

        # Matplotlib canvas
        self.figure = Figure()
        self.figure.patch.set_facecolor("white")
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("white")
        self.ax.imshow(self.image[0])
        self.ax.axis("off")
        self.canvas = FigureCanvasQTAgg(self.figure)

        # Frame slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, self.number_of_frames - 1)
        self.slider.setValue(0)
        self.slider.setToolTip("Drag to browse through image frames.")
        self.slider.valueChanged.connect(self.update_image)

        canvas_col = QVBoxLayout()
        canvas_col.setSpacing(6)
        canvas_col.addWidget(self.canvas, stretch=1)
        canvas_col.addWidget(self.slider)

        # Right-side controls
        controls_group = QGroupBox("Time of Addition")
        form = QFormLayout(controls_group)
        form.setSpacing(10)

        self.frame_spinbox = QSpinBox()
        self.frame_spinbox.setRange(0, self.number_of_frames - 1)
        self.frame_spinbox.setValue(0)
        self.frame_spinbox.setFixedWidth(160)
        self.frame_spinbox.setToolTip(
            "Enter or select the frame number at which the reagent was added to the cells."
        )
        form.addRow(QLabel("Frame number:"), self.frame_spinbox)

        controls_col = QVBoxLayout()
        controls_col.setSpacing(8)
        controls_col.addWidget(controls_group)
        controls_col.addStretch(1)

        # Content row
        content_row = QHBoxLayout()
        content_row.setSpacing(12)
        content_row.addLayout(canvas_col, stretch=1)
        content_row.addLayout(controls_col)

        main_layout.addLayout(content_row, stretch=1)

        # Bottom action bar
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setToolTip("Cancel and exit the program.")
        self.cancel_button.clicked.connect(self.cancel)

        self.continue_button = QPushButton("Continue")
        self.continue_button.setObjectName("StartButton")
        self.continue_button.setMinimumWidth(160)
        self.continue_button.setMinimumHeight(36)
        self.continue_button.setToolTip("Confirm the selected frame and continue to the next step.")
        self.continue_button.clicked.connect(self.close_gui)

        action_row.addWidget(self.cancel_button)
        action_row.addStretch(1)
        action_row.addWidget(self.continue_button)

        main_layout.addLayout(action_row)

        self.window.setCentralWidget(central)

    # ------------------------------------------------------------------
    # Public API (unchanged from original)
    # ------------------------------------------------------------------

    def update_image(self, new_frame: int):
        new_image = self.image[int(new_frame)]
        self.ax.clear()
        self.ax.set_facecolor("white")
        self.ax.imshow(new_image)
        self.ax.axis("off")
        self.canvas.draw()

    def get_time_of_addition(self) -> int | None:
        try:
            return int(self.frame_spinbox.value())
        except ValueError:
            print("Invalid input. Please enter a valid integer.")
            return None

    def run_main_loop(self):
        self.window.show()
        self.app.exec()

    def close_gui(self):
        self.window.close()

    def cancel(self):
        self.window.close()
        QApplication.quit()
        quit()
