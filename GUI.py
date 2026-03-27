from __future__ import annotations

import re
import sys
import webbrowser
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import tomlkit

from PySide6.QtCore import QDate, Qt, QTimer
from PySide6.QtGui import QDoubleValidator, QIntValidator, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QDoubleSpinBox,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class _MainWindow(QMainWindow):
    def __init__(self, controller: "TDarts_GUI"):
        super().__init__()
        self.controller = controller

    def closeEvent(self, event):  # noqa: N802 (Qt API)
        if not self.controller.started:
            self.controller.cancelled = True
        super().closeEvent(event)


class TDarts_GUI:
    """Modern main GUI implementation with functional parity to legacy Tk GUI."""

    def __init__(self):
        existing_app = QApplication.instance()
        self._owns_app = existing_app is None
        self.app = existing_app if existing_app is not None else QApplication(sys.argv)

        self.started = False
        self.cancelled = False
        self._loading = False
        self._suspend_presets = False

        self.last_input_mode = "file"
        self.input_path_value = ""
        self.checkpoint_path_value = ""
        self.form_label_width = 260

        self.cell_types = ["jurkat", "primary", "NK", "NK_human"]
        self.parameters_dict = {
            "jurkat": {},
            "primary": {},
            "NK": {},
            "NK_human": {},
        }

        self.window = _MainWindow(self)
        self.window.setWindowTitle("DARTS - Main Configuration")
        self.window.resize(1400, 980)
        self.window.setMinimumSize(1200, 860)
        self._status_hide_timer = QTimer(self.window)
        self._status_hide_timer.setSingleShot(True)

        self._build_ui()
        self._connect_signals()
        self._status_hide_timer.timeout.connect(lambda: self._set_status(""))
        self.set_default_settings_for_local_imaging()
        self._refresh_start_state()

    def _build_ui(self):
        self.window.setStyleSheet(self._build_stylesheet())

        central = QWidget(self.window)
        central.setObjectName("centralwidget")
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        title = QLabel("DARTS - Analysis Setup")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        subtitle = QLabel("Configure your analysis in three steps: set your data paths, describe your experiment, then choose the processing pipeline.")
        subtitle.setObjectName("SubtitleLabel")

        title_wrap = QVBoxLayout()
        title_wrap.setSpacing(0)
        title_wrap.addWidget(title)
        title_wrap.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_input_output_tab(), "1. Input / Output")
        self.tabs.addTab(self._build_measurement_tab(), "2. Measurement")
        self.tabs.addTab(self._build_pipeline_tab(), "3. Pipeline")

        self.status_label = QLabel()
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setFrameShape(QFrame.Shape.StyledPanel)
        self.status_label.setStyleSheet("padding: 6px;")
        self.status_label.hide()

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        self.save_settings_button = QPushButton("&Save settings")
        self.load_settings_button = QPushButton("&Load settings")
        self.about_button = QPushButton("&About DARTS")

        self.start_button = QPushButton("&Start")
        self.start_button.setObjectName("StartButton")
        self.start_button.setMinimumWidth(170)
        self.start_button.setMinimumHeight(40)
        self.cancel_button = QPushButton("&Cancel")
        self.cancel_button.setMinimumWidth(120)

        self.validation_label = QLabel()
        self.validation_label.setObjectName("ValidationLabel")
        self.validation_label.setWordWrap(True)

        actions_layout.addWidget(self.save_settings_button)
        actions_layout.addWidget(self.load_settings_button)
        actions_layout.addWidget(self.about_button)
        actions_layout.addStretch(1)
        actions_layout.addWidget(self.validation_label, stretch=1)
        actions_layout.addWidget(self.cancel_button)
        actions_layout.addWidget(self.start_button)
        self._apply_accessibility_labels()

        main_layout.addLayout(title_wrap)
        main_layout.addWidget(self.tabs, stretch=1)
        main_layout.addWidget(self.status_label)
        main_layout.addLayout(actions_layout)

        self.window.setCentralWidget(central)

    def _apply_accessibility_labels(self):
        widgets = {
            self.path_edit: "Input path",
            self.results_dir_edit: "Results directory path",
            self.microscope_edit: "Used microscope",
            self.scale_spin: "Scale pixels per micron",
            self.fps_spin: "Frame rate",
            self.resolution_spin: "Spatial resolution",
            self.cell_type_combo: "Cell type",
            self.day_edit: "Day of measurement",
            self.user_edit: "User",
            self.experiment_name_edit: "Experiment name",
            self.background_algorithm_combo: "Background algorithm",
            self.wavelet_algorithm_combo: "Wavelet algorithm",
            self.deconvolution_algorithm_combo: "Deconvolution algorithm",
            self.start_button: "Start analysis",
        }
        for widget, name in widgets.items():
            widget.setAccessibleName(name)

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
                "tab_bg": "#3f4550",
                "tab_selected_bg": "#4a5160",
                "status_bg": "#2f343d",
                "status_border": "#7a7f87",
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
                "tab_bg": "#eef2f7",
                "tab_selected_bg": "#ffffff",
                "status_bg": "#edf3f9",
                "status_border": "#c7ced8",
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
            QWidget#ContentCard {{
                background: {colors["group_bg"]};
                border: 1px solid {colors["group_border"]};
                border-radius: 10px;
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
            QLabel#SubtitleLabel {{
                color: {colors["muted_text"]};
            }}
            QLabel#TabSectionTitle {{
                font-size: 16px;
                font-weight: 700;
            }}
            QLabel#TabSectionSubtitle {{
                color: {colors["muted_text"]};
            }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
                min-height: 34px;
                padding: 4px 8px;
                border: 1px solid {colors["field_border"]};
                border-radius: 6px;
                background: {colors["field_bg"]};
                color: {colors["text"]};
            }}
            QComboBox::drop-down {{
                width: 30px;
                border-left: 1px solid {colors["field_border"]};
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button {{
                width: 22px;
                subcontrol-origin: border;
                subcontrol-position: top right;
            }}
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                width: 22px;
                subcontrol-origin: border;
                subcontrol-position: bottom right;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
            QTabWidget::pane {{
                border: 1px solid {colors["group_border"]};
                border-radius: 8px;
                top: -1px;
                background: {colors["group_bg"]};
            }}
            QTabBar::tab {{
                padding: 8px 14px;
                background: {colors["tab_bg"]};
                border: 1px solid {colors["group_border"]};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {colors["tab_selected_bg"]};
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
            QPushButton:disabled {{
                color: {colors["muted_text"]};
            }}
            QToolButton {{
                padding: 6px 12px;
                border: 1px solid {colors["button_border"]};
                border-radius: 6px;
                background: {colors["button_bg"]};
                color: {colors["text"]};
            }}
            QToolButton:hover {{
                background: {colors["button_hover"]};
            }}
            QLabel#StatusLabel {{
                background: {colors["status_bg"]};
                border: 1px solid {colors["status_border"]};
                border-radius: 6px;
            }}
            QLabel#ValidationLabel {{
                color: {colors["muted_text"]};
                padding: 0 8px;
            }}
            QLabel#ValidationLabel[invalid=\"true\"] {{
                color: #d94848;
                font-weight: 600;
            }}
        """

    def _build_input_output_tab(self) -> QWidget:
        tab, card_layout = self._create_tab_scaffold(
            "Input and Output",
            "Select input mode, choose data paths, and configure checkpoint behavior.",
            next_tab=1,
            next_label="Next: Measurement",
        )

        self.mode_file_radio = QRadioButton("Select File")
        self.mode_file_radio.setToolTip("Analyze a single image file.")
        self.mode_dir_radio = QRadioButton("Select Directory")
        self.mode_dir_radio.setToolTip("Analyze all image files found in a folder.")
        self.mode_cp_radio = QRadioButton("Select Checkpoint")
        self.mode_cp_radio.setToolTip("Resume a previously saved analysis without repeating preprocessing.")
        self.mode_file_radio.setChecked(True)

        self.mode_group_buttons = QButtonGroup(self.window)
        self.mode_group_buttons.addButton(self.mode_file_radio)
        self.mode_group_buttons.addButton(self.mode_dir_radio)
        self.mode_group_buttons.addButton(self.mode_cp_radio)

        mode_widget = QWidget()
        mode_layout = QHBoxLayout(mode_widget)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(18)
        mode_layout.addWidget(self.mode_file_radio)
        mode_layout.addWidget(self.mode_dir_radio)
        mode_layout.addWidget(self.mode_cp_radio)
        mode_layout.addStretch(1)

        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.select_path_button = QPushButton("Select path")
        self.select_path_button.setFixedWidth(180)
        path_widget = QWidget()
        path_layout = QHBoxLayout(path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(10)
        path_layout.addWidget(self.path_edit, stretch=1)
        path_layout.addWidget(self.select_path_button)

        self.image_single_radio = QRadioButton("one file per channel")
        self.image_single_radio.setToolTip("Each fluorescence channel is stored in a separate image file.")
        self.image_two_in_one_radio = QRadioButton("both channels in one file")
        self.image_two_in_one_radio.setToolTip("Both fluorescence channels are stored together in one multi-channel file (e.g. multi-channel TIFF).")
        self.image_two_in_one_radio.setChecked(True)
        image_widget = QWidget()
        image_layout = QHBoxLayout(image_widget)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(18)
        image_layout.addWidget(self.image_single_radio)
        image_layout.addWidget(self.image_two_in_one_radio)
        image_layout.addStretch(1)

        self.results_dir_edit = QLineEdit()
        self.choose_results_dir_button = QPushButton("Choose results directory")
        self.choose_results_dir_button.setFixedWidth(180)
        results_widget = QWidget()
        results_layout = QHBoxLayout(results_widget)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(10)
        results_layout.addWidget(self.results_dir_edit, stretch=1)
        results_layout.addWidget(self.choose_results_dir_button)

        self.checkpoint_save_checkbox = QCheckBox("Save after preprocessing")
        self.checkpoint_save_checkbox.setToolTip("Save the preprocessed data to disk so you can reload and resume the analysis later without repeating the preprocessing step.")
        checkpoint_widget = QWidget()
        checkpoint_layout = QHBoxLayout(checkpoint_widget)
        checkpoint_layout.setContentsMargins(0, 0, 0, 0)
        checkpoint_layout.addWidget(self.checkpoint_save_checkbox)
        checkpoint_layout.addStretch(1)

        grid = self._new_form_grid()
        self._add_form_row(grid, 0, "Input mode", mode_widget)
        self._add_form_row(grid, 1, "Selected path", path_widget)
        self._add_form_row(grid, 2, "Image configuration", image_widget)
        self._add_form_row(grid, 3, "Results directory", results_widget)
        self._add_form_row(grid, 4, "Checkpoint", checkpoint_widget)
        card_layout.addLayout(grid)

        return tab

    def _build_measurement_tab(self) -> QWidget:
        tab, card_layout = self._create_tab_scaffold(
            "Measurement Metadata",
            "Describe your microscopy setup and experiment. These settings are used to correctly interpret your imaging data.",
            prev_tab=0,
            prev_label="Back: Input",
            next_tab=2,
            next_label="Next: Pipeline",
        )

        self.microscope_edit = QLineEdit()
        self.microscope_edit.setMaximumWidth(480)

        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setDecimals(6)
        self.scale_spin.setRange(0.0, 1000000.0)
        self.scale_spin.setValue(0.0)
        self.scale_spin.setMaximumWidth(240)
        self.scale_spin.setToolTip("Number of pixels per micron. Find this value in your microscope acquisition software.")

        self.fps_spin = QDoubleSpinBox()
        self.fps_spin.setDecimals(3)
        self.fps_spin.setRange(0.0, 100000.0)
        self.fps_spin.setValue(3.0)
        self.fps_spin.setMaximumWidth(240)
        self.fps_spin.setToolTip("Number of image frames acquired per second during the time-lapse recording.")

        self.resolution_spin = QSpinBox()
        self.resolution_spin.setRange(1, 100000)
        self.resolution_spin.setValue(3)
        self.resolution_spin.setMaximumWidth(240)
        self.resolution_spin.setToolTip("Spatial resolution in pixels used for cell segmentation and normalization.")

        self.cell_type_combo = QComboBox()
        self.cell_type_combo.addItems(self.cell_types)
        self.cell_type_combo.setMaximumWidth(240)
        self.manage_cell_types_button = QPushButton("Manage cell types")
        self.manage_cell_types_button.setFixedWidth(170)
        cell_widget = QWidget()
        cell_layout = QHBoxLayout(cell_widget)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        cell_layout.setSpacing(10)
        cell_layout.addWidget(self.cell_type_combo)
        cell_layout.addWidget(self.manage_cell_types_button)
        cell_layout.addStretch(1)

        self.day_edit = QDateEdit()
        self.day_edit.setDisplayFormat("yyyy-MM-dd")
        self.day_edit.setDate(QDate.currentDate())
        self.day_edit.setCalendarPopup(True)
        self.day_edit.setMaximumWidth(220)

        self.user_edit = QLineEdit()
        self.user_edit.setMaximumWidth(380)
        self.experiment_name_edit = QLineEdit()
        self.experiment_name_edit.setMaximumWidth(520)

        self.local_radio = QRadioButton("local imaging (microdomains)")
        self.local_radio.setToolTip("Detect discrete calcium hotspots at the cell membrane (microdomain analysis).")
        self.global_radio = QRadioButton("global imaging (ratio)")
        self.global_radio.setToolTip("Measure the average calcium ratio across the entire cell (whole-cell analysis).")
        self.local_radio.setChecked(True)
        imaging_widget = QWidget()
        imaging_layout = QHBoxLayout(imaging_widget)
        imaging_layout.setContentsMargins(0, 0, 0, 0)
        imaging_layout.setSpacing(18)
        imaging_layout.addWidget(self.local_radio)
        imaging_layout.addWidget(self.global_radio)
        imaging_layout.addStretch(1)

        self.bead_checkbox = QCheckBox()
        self.bead_checkbox.setChecked(True)
        self.bead_checkbox.setToolTip("Enable if cells were stimulated using beads. The bead contact point is used to define the start of stimulation.")

        self.duration_before_spin = QDoubleSpinBox()
        self.duration_before_spin.setDecimals(3)
        self.duration_before_spin.setRange(0.0, 100000.0)
        self.duration_before_spin.setValue(1.0)
        self.duration_before_spin.setMaximumWidth(240)
        self.duration_before_spin.setToolTip("How many seconds of recording to include before the stimulation point.")

        self.duration_after_spin = QDoubleSpinBox()
        self.duration_after_spin.setDecimals(3)
        self.duration_after_spin.setRange(0.0, 100000.0)
        self.duration_after_spin.setValue(15.0)
        self.duration_after_spin.setMaximumWidth(240)
        self.duration_after_spin.setToolTip("How many seconds of recording to include after the stimulation point.")

        grid = self._new_form_grid()
        self._add_form_row(grid, 0, "Used microscope", self.microscope_edit)
        self._add_form_row(grid, 1, "Scale (pixels per micron)", self.scale_spin)
        self._add_form_row(grid, 2, "Frame rate (fps)", self.fps_spin)
        self._add_form_row(grid, 3, "Spatial resolution in pixels", self.resolution_spin)
        self._add_form_row(grid, 4, "Cell type", cell_widget)
        self._add_form_row(grid, 5, "Day of measurement", self.day_edit)
        self._add_form_row(grid, 6, "User", self.user_edit)
        self._add_form_row(grid, 7, "Name of experiment", self.experiment_name_edit)
        self._add_form_row(grid, 8, "Imaging intention", imaging_widget)
        self._add_form_row(grid, 9, "Bead contact", self.bead_checkbox)
        self._add_form_row(grid, 10, "Seconds before starting point", self.duration_before_spin)
        self._add_form_row(grid, 11, "Seconds after starting point", self.duration_after_spin)
        card_layout.addLayout(grid)

        return tab

    def _build_pipeline_tab(self) -> QWidget:
        tab, card_layout = self._create_tab_scaffold(
            "Pipeline Configuration",
            "Enable or disable processing steps for your pipeline. Each module can be individually toggled and configured.",
            use_scroll=False,
            prev_tab=1,
            prev_label="Back: Measurement",
        )

        core_group, core_grid = self._make_module_section("Core Postprocessing")
        self.channel_alignment_checkbox = QCheckBox()
        self.channel_alignment_checkbox.setChecked(True)
        self.channel_alignment_checkbox.setToolTip("Correct for any spatial offset between the two fluorescence channels caused by the optical setup.")
        self.frame_by_frame_checkbox = QCheckBox("Align each frame")
        self.frame_by_frame_checkbox.setToolTip("Apply channel alignment independently to every time frame. Useful if there is mechanical drift during the recording.")
        self._add_module_row(
            core_grid,
            0,
            "Channel alignment (SITK)",
            self.channel_alignment_checkbox,
            secondary=self.frame_by_frame_checkbox,
        )

        self.background_checkbox = QCheckBox()
        self.background_checkbox.setChecked(True)
        self.background_checkbox.setToolTip("Remove background fluorescence that is not from the cell itself.")
        self.background_algorithm_combo = QComboBox()
        self.background_algorithm_combo.addItems(["Masked", "Wavelet"])
        self.background_algorithm_combo.setMinimumWidth(220)
        self.background_algorithm_combo.setToolTip("Masked: estimates background using regions outside the cell mask.\nWavelet: removes background using frequency-domain filtering.")
        self.wavelet_algorithm_combo = QComboBox()
        self.wavelet_algorithm_combo.addItems(["No", "Weak-HI", "Strong-HI", "Weak-LI", "Strong-LI"])
        self.wavelet_algorithm_combo.setMinimumWidth(220)
        self.wavelet_algorithm_combo.setToolTip("Strength of wavelet background removal.\nHI = high-intensity images, LI = low-intensity images.\nWeak/Strong controls how aggressively background is removed.")
        self._add_module_row(
            core_grid,
            1,
            "Background subtraction",
            self.background_checkbox,
            primary=self.background_algorithm_combo,
            secondary=self.wavelet_algorithm_combo,
        )

        self.upsampling_checkbox = QCheckBox()
        self.upsampling_checkbox.setToolTip("Increase the image resolution for improved spatial precision in downstream analysis.")
        self.upsampling_algorithm_combo = QComboBox()
        self.upsampling_algorithm_combo.addItems(["Fourier", "Spatial"])
        self.upsampling_algorithm_combo.setMinimumWidth(220)
        self.upsampling_algorithm_combo.setToolTip("Fourier: upsamples in frequency space (better for periodic structures).\nSpatial: upsamples using interpolation in image space.")
        self._add_module_row(
            core_grid,
            2,
            "Upsampling",
            self.upsampling_checkbox,
            primary=self.upsampling_algorithm_combo,
        )

        self.segmentation_checkbox = QCheckBox()
        self.segmentation_checkbox.setChecked(True)
        self.segmentation_checkbox.setEnabled(False)
        segmentation_note = QLabel("Always enabled")
        self._add_module_row(
            core_grid,
            3,
            "Cell segmentation/tracking",
            self.segmentation_checkbox,
            primary=segmentation_note,
        )

        self.denoising_checkbox = QCheckBox()
        self.denoising_checkbox.setToolTip("Reduce image noise while preserving cell structures and signal features.")
        self.denoising_algorithm_combo = QComboBox()
        self.denoising_algorithm_combo.addItems(["SparseHessian"])
        self.denoising_algorithm_combo.setMinimumWidth(220)
        self.denoising_algorithm_combo.setToolTip("SparseHessian: denoising algorithm that preserves edges and fine structures using second-order image derivatives.")
        self._add_module_row(
            core_grid,
            4,
            "Denoising",
            self.denoising_checkbox,
            primary=self.denoising_algorithm_combo,
        )

        self.bleaching_checkbox = QCheckBox()
        self.bleaching_checkbox.setChecked(True)
        self.bleaching_checkbox.setToolTip("Correct for the gradual loss of fluorescence signal over time caused by photobleaching.")
        self.bleaching_algorithm_combo = QComboBox()
        self.bleaching_algorithm_combo.addItems(
            [
                "additiv no fit",
                "multiplicative simple ratio",
                "biexponential fit additiv",
            ]
        )
        self.bleaching_algorithm_combo.setMinimumWidth(220)
        self.bleaching_algorithm_combo.setToolTip(
            "additiv no fit: subtracts a simple additive bleaching estimate without curve fitting.\n"
            "multiplicative simple ratio: scales the signal using the ratio of baseline to current intensity.\n"
            "biexponential fit additiv: fits a double-exponential decay curve to model and remove bleaching."
        )
        self._add_module_row(
            core_grid,
            5,
            "Bleaching correction",
            self.bleaching_checkbox,
            primary=self.bleaching_algorithm_combo,
        )

        self.ratio_checkbox = QCheckBox()
        self.ratio_checkbox.setChecked(True)
        self.ratio_checkbox.setEnabled(False)
        ratio_note = QLabel("Always enabled")
        self._add_module_row(
            core_grid,
            6,
            "Ratio images",
            self.ratio_checkbox,
            primary=ratio_note,
        )

        decon_group, decon_grid = self._make_module_section("Deconvolution")
        self.deconvolution_checkbox = QCheckBox()
        self.deconvolution_checkbox.setChecked(True)
        self.deconvolution_checkbox.setToolTip("Improve image sharpness by computationally reversing the blurring caused by the microscope's point spread function (PSF).")
        self.deconvolution_algorithm_combo = QComboBox()
        self.deconvolution_algorithm_combo.addItems(["LR", "TDE", "LW"])
        self.deconvolution_algorithm_combo.setMinimumWidth(220)
        self.deconvolution_algorithm_combo.setToolTip(
            "LR: Lucy-Richardson — classic iterative deconvolution, robust and widely used.\n"
            "TDE: Time-Dependent Entropy — regularized method suited for time-lapse data.\n"
            "LW: Landweber — linear iterative method, fast and stable."
        )

        self.decon_advanced_toggle = QToolButton()
        self.decon_advanced_toggle.setCheckable(True)
        self.decon_advanced_toggle.setChecked(False)
        self.decon_advanced_toggle.setText("Show advanced fields")
        self._add_module_row(
            decon_grid,
            0,
            "Deconvolution module",
            self.deconvolution_checkbox,
            primary=self.deconvolution_algorithm_combo,
            secondary=self.decon_advanced_toggle,
        )

        self.text_TDE_lambda = self._make_float_line(allow_empty=True)
        self.text_TDE_lambda_t = self._make_float_line(allow_empty=True)
        self.text_iterations = self._make_int_line(allow_empty=True)
        self.text_psf_type = QLineEdit("confocal")
        self.text_psf_lambdaEx_ch1 = self._make_int_line("488")
        self.text_psf_lambdaEm_ch1 = self._make_int_line("520")
        self.text_psf_lambdaEx_ch2 = self._make_int_line("488")
        self.text_psf_lambdaEm_ch2 = self._make_int_line("600")
        self.text_psf_numAper = self._make_float_line("1.4")
        self.text_psf_magObj = self._make_int_line("100")
        self.text_psf_rindexObj = self._make_float_line("1.518")
        self.text_psf_rindexSp = self._make_float_line("1.518")
        self.text_psf_ccdSize = self._make_int_line("6450")

        self.decon_advanced_panel = QWidget()
        advanced_grid = QGridLayout(self.decon_advanced_panel)
        advanced_grid.setContentsMargins(8, 6, 8, 6)
        advanced_grid.setHorizontalSpacing(12)
        advanced_grid.setVerticalSpacing(10)

        advanced_grid.addWidget(QLabel("lambda (TDE)"), 0, 0)
        advanced_grid.addWidget(self.text_TDE_lambda, 0, 1)
        advanced_grid.addWidget(QLabel("lambda t (TDE)"), 0, 2)
        advanced_grid.addWidget(self.text_TDE_lambda_t, 0, 3)
        advanced_grid.addWidget(QLabel("iterations (LW)"), 1, 0)
        advanced_grid.addWidget(self.text_iterations, 1, 1)
        advanced_grid.addWidget(QLabel("psf type"), 1, 2)
        advanced_grid.addWidget(self.text_psf_type, 1, 3)
        advanced_grid.addWidget(QLabel("psf lambdaEx_ch1"), 2, 0)
        advanced_grid.addWidget(self.text_psf_lambdaEx_ch1, 2, 1)
        advanced_grid.addWidget(QLabel("psf lambdaEm_ch1"), 2, 2)
        advanced_grid.addWidget(self.text_psf_lambdaEm_ch1, 2, 3)
        advanced_grid.addWidget(QLabel("psf lambdaEx_ch2"), 3, 0)
        advanced_grid.addWidget(self.text_psf_lambdaEx_ch2, 3, 1)
        advanced_grid.addWidget(QLabel("psf lambdaEm_ch2"), 3, 2)
        advanced_grid.addWidget(self.text_psf_lambdaEm_ch2, 3, 3)
        advanced_grid.addWidget(QLabel("psf numAper"), 4, 0)
        advanced_grid.addWidget(self.text_psf_numAper, 4, 1)
        advanced_grid.addWidget(QLabel("psf magObj"), 4, 2)
        advanced_grid.addWidget(self.text_psf_magObj, 4, 3)
        advanced_grid.addWidget(QLabel("psf rindexObj"), 5, 0)
        advanced_grid.addWidget(self.text_psf_rindexObj, 5, 1)
        advanced_grid.addWidget(QLabel("psf rindexSp"), 5, 2)
        advanced_grid.addWidget(self.text_psf_rindexSp, 5, 3)
        advanced_grid.addWidget(QLabel("psf ccdSize"), 6, 0)
        advanced_grid.addWidget(self.text_psf_ccdSize, 6, 1)

        decon_grid.addWidget(self.decon_advanced_panel, 1, 0, 1, 4)
        self.decon_advanced_panel.setVisible(False)

        self.decon_base_fields = [
            self.text_psf_type,
            self.text_psf_lambdaEx_ch1,
            self.text_psf_lambdaEm_ch1,
            self.text_psf_lambdaEx_ch2,
            self.text_psf_lambdaEm_ch2,
            self.text_psf_numAper,
            self.text_psf_magObj,
            self.text_psf_rindexObj,
            self.text_psf_rindexSp,
            self.text_psf_ccdSize,
            self.text_TDE_lambda,
            self.text_TDE_lambda_t,
            self.text_iterations,
        ]

        analysis_group, analysis_grid = self._make_module_section("Analysis Dependencies")
        self.shape_normalization_checkbox = QCheckBox()
        self.shape_normalization_checkbox.setChecked(True)
        self.shape_normalization_checkbox.setToolTip("Normalize all cell shapes to a common template, enabling direct comparison of signals across different cells.")
        self._add_module_row(
            analysis_grid,
            0,
            "Shape normalization",
            self.shape_normalization_checkbox,
        )

        self.hotspot_checkbox = QCheckBox()
        self.hotspot_checkbox.setChecked(True)
        self.hotspot_checkbox.setToolTip("Automatically detect and quantify discrete calcium microdomain events at the cell membrane.")
        self._add_module_row(
            analysis_grid,
            1,
            "Hotspot detection",
            self.hotspot_checkbox,
        )

        self.dartboard_checkbox = QCheckBox()
        self.dartboard_checkbox.setChecked(True)
        self.dartboard_checkbox.setToolTip("Map the spatial distribution of calcium signals onto a concentric-ring diagram (dartboard) showing signal intensity by location on the cell.")
        self._add_module_row(
            analysis_grid,
            2,
            "Dartboard projection",
            self.dartboard_checkbox,
        )

        pipeline_tabs = QTabWidget()
        pipeline_tabs.addTab(self._wrap_in_tab_page(core_group), "Core")
        pipeline_tabs.addTab(self._wrap_in_tab_page(decon_group), "Deconvolution")
        pipeline_tabs.addTab(self._wrap_in_tab_page(analysis_group), "Analysis")
        card_layout.addWidget(pipeline_tabs)

        return tab

    def _create_tab_scaffold(
        self,
        title_text: str,
        subtitle_text: str,
        use_scroll: bool = True,
        prev_tab: int | None = None,
        prev_label: str = "Back",
        next_tab: int | None = None,
        next_label: str = "Next",
    ):
        tab = QWidget()
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(8)

        title = QLabel(title_text)
        title.setObjectName("TabSectionTitle")
        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("TabSectionSubtitle")
        subtitle.setWordWrap(True)
        outer.addWidget(title)
        outer.addWidget(subtitle)

        card = QWidget()
        card.setObjectName("ContentCard")
        card_shell_layout = QVBoxLayout(card)
        card_shell_layout.setContentsMargins(16, 16, 16, 16)
        card_shell_layout.setSpacing(14)

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(14)
        card_shell_layout.addLayout(card_layout, stretch=1)

        if use_scroll:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)

            content = QWidget()
            content_layout = QVBoxLayout(content)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(10)
            content_layout.addWidget(card)
            content_layout.addStretch(1)
            scroll.setWidget(content)
            outer.addWidget(scroll, stretch=1)
        else:
            outer.addWidget(card, stretch=1)

        outer.addLayout(
            self._tab_nav_layout(
                prev_tab=prev_tab,
                prev_label=prev_label,
                next_tab=next_tab,
                next_label=next_label,
            )
        )

        return tab, card_layout

    @staticmethod
    def _wrap_in_tab_page(widget: QWidget):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(4, 6, 4, 6)
        layout.setSpacing(8)
        layout.addWidget(widget)
        layout.addStretch(1)
        return page

    def _new_form_grid(self):
        grid = QGridLayout()
        grid.setColumnMinimumWidth(0, self.form_label_width)
        grid.setColumnStretch(1, 1)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)
        return grid

    def _add_form_row(self, grid: QGridLayout, row: int, label_text: str, field_widget: QWidget):
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        label.setFixedWidth(self.form_label_width)
        grid.addWidget(label, row, 0)
        grid.addWidget(field_widget, row, 1)

    def _make_module_section(self, title: str):
        group = QGroupBox(title)
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 280)
        grid.setColumnMinimumWidth(1, 90)
        grid.setColumnMinimumWidth(2, 220)
        grid.setColumnStretch(3, 1)
        return group, grid

    def _add_module_row(
        self,
        grid: QGridLayout,
        row: int,
        name: str,
        toggle: QWidget | None,
        primary: QWidget | None = None,
        secondary: QWidget | None = None,
    ):
        label = QLabel(name)
        grid.addWidget(label, row, 0)
        if toggle is not None:
            grid.addWidget(toggle, row, 1, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if primary is not None:
            grid.addWidget(primary, row, 2)
        if secondary is not None:
            grid.addWidget(secondary, row, 3)

    def _tab_nav_layout(
        self,
        prev_tab: int | None = None,
        prev_label: str = "Back",
        next_tab: int | None = None,
        next_label: str = "Next",
    ):
        row = QHBoxLayout()
        row.setContentsMargins(0, 8, 0, 0)
        row.setSpacing(8)

        if prev_tab is not None:
            prev_btn = QPushButton(prev_label)
            prev_btn.setFixedWidth(150)
            prev_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(prev_tab))
            row.addWidget(prev_btn)

        row.addStretch(1)

        if next_tab is not None:
            next_btn = QPushButton(next_label)
            next_btn.setFixedWidth(170)
            next_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(next_tab))
            row.addWidget(next_btn)

        return row

    def _make_int_line(self, default: str = "", allow_empty: bool = False) -> QLineEdit:
        edit = QLineEdit(default)
        if not allow_empty:
            edit.setPlaceholderText("required")
        validator = QIntValidator(0, 2_000_000_000, self.window)
        edit.setValidator(validator)
        return edit

    def _make_float_line(self, default: str = "", allow_empty: bool = False) -> QLineEdit:
        edit = QLineEdit(default)
        if not allow_empty:
            edit.setPlaceholderText("required")
        validator = QDoubleValidator(0.0, 2_000_000_000.0, 10, self.window)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        edit.setValidator(validator)
        return edit

    def _connect_signals(self):
        self.mode_file_radio.toggled.connect(self.on_select_mode_change)
        self.mode_dir_radio.toggled.connect(self.on_select_mode_change)
        self.mode_cp_radio.toggled.connect(self.on_select_mode_change)

        self.select_path_button.clicked.connect(self.select_files_or_directory)
        self.choose_results_dir_button.clicked.connect(self.select_results_directory)

        self.local_radio.toggled.connect(self._imaging_mode_changed)
        self.global_radio.toggled.connect(self._imaging_mode_changed)

        self.channel_alignment_checkbox.toggled.connect(self.update_settings_for_registration)
        self.background_checkbox.toggled.connect(self.update_background)
        self.background_algorithm_combo.currentTextChanged.connect(self.update_wavelet)
        self.upsampling_checkbox.toggled.connect(self.update_upsampling)
        self.denoising_checkbox.toggled.connect(self.update_denoising)
        self.deconvolution_checkbox.toggled.connect(self.update_deconvolution)
        self.deconvolution_algorithm_combo.currentTextChanged.connect(self.decon_selection_changed)
        self.decon_advanced_toggle.toggled.connect(self._toggle_decon_advanced_panel)
        self.bleaching_checkbox.toggled.connect(self.update_bleaching_correction)

        self.hotspot_checkbox.toggled.connect(lambda _: self.update_settings_for_analysis())
        self.shape_normalization_checkbox.toggled.connect(lambda _: self.update_settings_shape_normalization())
        self.bead_checkbox.toggled.connect(lambda _: self.update_bead_contact())

        self.manage_cell_types_button.clicked.connect(self.manage_cell_types)

        self.save_settings_button.clicked.connect(self.save_settings_as_method)
        self.load_settings_button.clicked.connect(self.load_settings_from_computer)
        self.about_button.clicked.connect(self.open_github_page)
        self.start_button.clicked.connect(self.start_analysis)
        self.cancel_button.clicked.connect(self.cancel)

        validation_triggers = [
            self.path_edit.textChanged,
            self.results_dir_edit.textChanged,
            self.text_TDE_lambda.textChanged,
            self.text_TDE_lambda_t.textChanged,
            self.text_iterations.textChanged,
            self.text_psf_type.textChanged,
            self.text_psf_lambdaEx_ch1.textChanged,
            self.text_psf_lambdaEm_ch1.textChanged,
            self.text_psf_lambdaEx_ch2.textChanged,
            self.text_psf_lambdaEm_ch2.textChanged,
            self.text_psf_numAper.textChanged,
            self.text_psf_magObj.textChanged,
            self.text_psf_rindexObj.textChanged,
            self.text_psf_rindexSp.textChanged,
            self.text_psf_ccdSize.textChanged,
            self.mode_file_radio.toggled,
            self.mode_dir_radio.toggled,
            self.mode_cp_radio.toggled,
            self.deconvolution_checkbox.toggled,
            self.deconvolution_algorithm_combo.currentTextChanged,
        ]
        for sig in validation_triggers:
            sig.connect(lambda *_: self._refresh_start_state())

    def _imaging_mode_changed(self):
        if self._suspend_presets or self._loading:
            return
        if self.global_radio.isChecked():
            self.set_default_settings_for_global_imaging()
        elif self.local_radio.isChecked():
            self.set_default_settings_for_local_imaging()

    def _set_status(self, text: str):
        if not text:
            self._status_hide_timer.stop()
            self.status_label.clear()
            self.status_label.hide()
            return
        self.status_label.setText(text)
        self.status_label.show()
        self._status_hide_timer.stop()
        self._status_hide_timer.start(3500)

    def _toggle_decon_advanced_panel(self, checked: bool):
        self.decon_advanced_panel.setVisible(checked and self.deconvolution_checkbox.isChecked())
        self.decon_advanced_toggle.setText("Hide advanced fields" if checked else "Show advanced fields")

    def _validate_start_conditions(self):
        mode = self._current_mode()
        display_path = self.path_edit.text().strip()
        if mode in ("file", "dir"):
            if not display_path:
                return False, "Select an input file or directory."
        else:
            if not display_path:
                return False, "Select a checkpoint directory."

        if not self.results_dir_edit.text().strip():
            return False, "Select a results directory."

        if self.deconvolution_checkbox.isChecked():
            required_fields = [
                self.text_psf_type.text().strip(),
                self.text_psf_lambdaEx_ch1.text().strip(),
                self.text_psf_lambdaEm_ch1.text().strip(),
                self.text_psf_lambdaEx_ch2.text().strip(),
                self.text_psf_lambdaEm_ch2.text().strip(),
                self.text_psf_numAper.text().strip(),
                self.text_psf_magObj.text().strip(),
                self.text_psf_rindexObj.text().strip(),
                self.text_psf_rindexSp.text().strip(),
                self.text_psf_ccdSize.text().strip(),
            ]
            if any(v == "" for v in required_fields):
                return False, "Fill all required deconvolution fields or disable deconvolution."

        return True, "Ready to start analysis."

    def _refresh_start_state(self):
        valid, msg = self._validate_start_conditions()
        self.start_button.setEnabled(valid)
        self.validation_label.setText(msg)
        self.validation_label.setProperty("invalid", "false" if valid else "true")
        self.validation_label.style().unpolish(self.validation_label)
        self.validation_label.style().polish(self.validation_label)

    def _current_mode(self) -> str:
        if self.mode_cp_radio.isChecked():
            return "cp"
        if self.mode_dir_radio.isChecked():
            return "dir"
        return "file"

    def _set_mode(self, mode: str):
        if mode == "cp":
            self.mode_cp_radio.setChecked(True)
        elif mode == "dir":
            self.mode_dir_radio.setChecked(True)
        else:
            self.mode_file_radio.setChecked(True)

    def run_main_loop(self):
        self.window.show()
        self.app.exec()
        return self.started and not self.cancelled

    def open_github_page(self):
        webbrowser.open("https://github.com/IPMI-ICNS-UKE/DARTS")

    def get_parameters(self):
        mode = self._current_mode()
        if mode in ("file", "dir"):
            self.input_path_value = self.path_edit.text().strip()
        else:
            self.checkpoint_path_value = self.path_edit.text().strip()

        load_pre_start = mode == "cp" and bool(self.checkpoint_path_value)

        data = {
            "input_output": {
                "file_or_directory": self.last_input_mode,
                "image_conf": self.get_image_configuration(),
                "path": self.input_path_value,
                "results_dir": self.results_dir_edit.text().strip(),
                "excel_filename_microdomain_data": "microdomain_data.xlsx",
            },
            "properties_of_measurement": {
                "used_microscope": self.microscope_edit.text().strip(),
                "scale": float(self.scale_spin.value()),
                "frame_rate": float(self.fps_spin.value()),
                "resolution": int(self.resolution_spin.value()),
                "cell_type": self.cell_type_combo.currentText(),
                "cell_types_options": list(self.cell_types),
                "calibration_parameters_cell_types": dict(self.parameters_dict),
                "day_of_measurement": self.day_edit.date().toString("yyyy-MM-dd"),
                "user": self.user_edit.text().strip(),
                "experiment_name": self.experiment_name_edit.text().strip(),
                "imaging_local_or_global": "global" if self.global_radio.isChecked() else "local",
                "bead_contact": self.bead_checkbox.isChecked(),
                "duration_of_measurement": (
                    (float(self.duration_before_spin.value()) + float(self.duration_after_spin.value()))
                    * float(self.fps_spin.value())
                ),
                "wavelength_1": 488,
                "wavelength_2": 561,
                "time_of_measurement_before_starting_point": float(self.duration_before_spin.value()),
                "time_of_measurement_after_starting_point": float(self.duration_after_spin.value()),
            },
            "processing_pipeline": {
                "postprocessing": {
                    "channel_alignment_in_pipeline": self.channel_alignment_checkbox.isChecked(),
                    "channel_alignment_each_frame": self.frame_by_frame_checkbox.isChecked(),
                    "registration_method": "SITK",
                    "upsampling_in_pipeline": self.upsampling_checkbox.isChecked(),
                    "upsampling_algorithm": self.upsampling_algorithm_combo.currentText(),
                    "denoising_in_pipeline": self.denoising_checkbox.isChecked(),
                    "denoising_algorithm": self.denoising_algorithm_combo.currentText(),
                    "background_sub_in_pipeline": self.background_checkbox.isChecked(),
                    "background_subtractor_algorithm": self.background_algorithm_combo.currentText(),
                    "wavelet_algorithm": self.wavelet_algorithm_combo.currentText(),
                    "cell_segmentation_tracking_in_pipeline": self.segmentation_checkbox.isChecked(),
                    "deconvolution_in_pipeline": self.deconvolution_checkbox.isChecked(),
                    "deconvolution_algorithm": self.deconvolution_algorithm_combo.currentText(),
                    "decon_iter": self.text_iterations.text().strip(),
                    "TDE_lambda": self._float_from_optional_lineedit(self.text_TDE_lambda),
                    "TDE_lambda_t": self._float_from_optional_lineedit(self.text_TDE_lambda_t),
                    "psf": {
                        "type": self.text_psf_type.text().strip(),
                        "lambdaEx_ch1": self._required_int(self.text_psf_lambdaEx_ch1, "psf.lambdaEx_ch1"),
                        "lambdaEm_ch1": self._required_int(self.text_psf_lambdaEm_ch1, "psf.lambdaEm_ch1"),
                        "lambdaEx_ch2": self._required_int(self.text_psf_lambdaEx_ch2, "psf.lambdaEx_ch2"),
                        "lambdaEm_ch2": self._required_int(self.text_psf_lambdaEm_ch2, "psf.lambdaEm_ch2"),
                        "numAper": self._required_float(self.text_psf_numAper, "psf.numAper"),
                        "magObj": self._required_int(self.text_psf_magObj, "psf.magObj"),
                        "rindexObj": self._required_float(self.text_psf_rindexObj, "psf.rindexObj"),
                        "ccdSize": self._required_int(self.text_psf_ccdSize, "psf.ccdSize"),
                        "dz": 0,
                        "nslices": 1,
                        "depth": 0,
                        "rindexSp": self._required_float(self.text_psf_rindexSp, "psf.rindexSp"),
                        "nor": 0,
                        "xysize": 150,
                    },
                    "bleaching_correction_in_pipeline": self.bleaching_checkbox.isChecked(),
                    "bleaching_correction_algorithm": self.bleaching_algorithm_combo.currentText(),
                    "ratio_images": self.ratio_checkbox.isChecked(),
                    "median_filter_kernel": 3,
                },
                "shape_normalization": {
                    "shape_normalization": self.shape_normalization_checkbox.isChecked(),
                },
                "analysis": {
                    "hotspot_detection": self.hotspot_checkbox.isChecked(),
                    "dartboard_projection": self.dartboard_checkbox.isChecked(),
                },
                "checkpoints": {
                    "save_pre_start": self.checkpoint_save_checkbox.isChecked(),
                    "load_pre_start": load_pre_start,
                    "source_dir": self.checkpoint_path_value,
                },
            },
        }
        return data

    @staticmethod
    def _float_from_optional_lineedit(widget: QLineEdit):
        value = widget.text().strip()
        if not value:
            return ""
        try:
            return float(value)
        except ValueError:
            return ""

    @staticmethod
    def _required_int(widget: QLineEdit, label: str) -> int:
        text = widget.text().strip()
        if not text:
            raise ValueError(f"{label} is required")
        return int(text)

    @staticmethod
    def _required_float(widget: QLineEdit, label: str) -> float:
        text = widget.text().strip()
        if not text:
            raise ValueError(f"{label} is required")
        return float(text)

    def save_settings_as_method(self):
        directory = QFileDialog.getExistingDirectory(self.window, "Choose target directory")
        if not directory:
            return

        try:
            data = self.get_parameters()
        except Exception as exc:
            QMessageBox.critical(self.window, "Invalid parameters", str(exc))
            return

        experiment_name = data["properties_of_measurement"]["experiment_name"].strip()
        user = data["properties_of_measurement"]["user"].strip()
        date = data["properties_of_measurement"]["day_of_measurement"].strip()

        safe_experiment = self._safe_filename_part(experiment_name or "experiment")
        safe_user = self._safe_filename_part(user or "user")
        safe_date = self._safe_filename_part(date or "date")

        output_path = Path(directory) / f"DARTS_settings_{safe_date}_{safe_experiment}_{safe_user}.toml"
        with output_path.open("w", encoding="utf-8") as fp:
            tomlkit.dump(data, fp)

        self._set_status(f"Saved settings: {output_path}")

    @staticmethod
    def _safe_filename_part(text: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9._-]+", "_", text)
        normalized = normalized.strip("_")
        return normalized or "value"

    def load_settings_from_computer(self):
        path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Choose settings file",
            "",
            "TOML files (*.toml);;All files (*)",
        )
        if not path:
            return

        try:
            with open(path, mode="rt", encoding="utf-8") as fp:
                config = tomlkit.load(fp)
            self._apply_loaded_settings(config)
            self._set_status(f"Loaded settings: {path}")
        except Exception as exc:
            QMessageBox.critical(self.window, "Load error", f"Could not load settings:\n{exc}")

    def _apply_loaded_settings(self, config):
        self._loading = True
        self._suspend_presets = True

        input_cfg = config.get("input_output", {})
        post_cfg = config.get("processing_pipeline", {}).get("postprocessing", {})
        checkpoint_cfg = config.get("processing_pipeline", {}).get("checkpoints", {})
        prop_cfg = config.get("properties_of_measurement", {})

        self.last_input_mode = str(input_cfg.get("file_or_directory", "file"))
        image_cfg = str(input_cfg.get("image_conf", "two-in-one"))
        if image_cfg == "single":
            self.image_single_radio.setChecked(True)
        else:
            self.image_two_in_one_radio.setChecked(True)

        self.input_path_value = str(input_cfg.get("path", ""))
        self.results_dir_edit.setText(str(input_cfg.get("results_dir", "")))

        self.checkpoint_save_checkbox.setChecked(bool(checkpoint_cfg.get("save_pre_start", False)))
        self.checkpoint_path_value = str(checkpoint_cfg.get("source_dir", ""))

        load_pre_start = bool(checkpoint_cfg.get("load_pre_start", False))
        if load_pre_start and self.checkpoint_path_value:
            self._set_mode("cp")
        else:
            self._set_mode(self.last_input_mode)

        self.microscope_edit.setText(str(prop_cfg.get("used_microscope", "")))
        self.scale_spin.setValue(float(prop_cfg.get("scale", 0.0)))
        self.fps_spin.setValue(float(prop_cfg.get("frame_rate", 3.0)))
        self.resolution_spin.setValue(int(prop_cfg.get("resolution", 3)))

        loaded_cell_types = prop_cfg.get("cell_types_options", self.cell_types)
        if loaded_cell_types:
            self.cell_types = [str(v) for v in loaded_cell_types]

        self.parameters_dict = {
            str(k): dict(v)
            for k, v in dict(prop_cfg.get("calibration_parameters_cell_types", self.parameters_dict)).items()
        }

        for cell_type in self.cell_types:
            self.parameters_dict.setdefault(cell_type, {})

        self._refresh_cell_type_combo()
        loaded_cell_type = str(prop_cfg.get("cell_type", self.cell_type_combo.currentText()))
        if loaded_cell_type not in self.cell_types:
            self.cell_types.append(loaded_cell_type)
            self.parameters_dict.setdefault(loaded_cell_type, {})
            self._refresh_cell_type_combo()
        self.cell_type_combo.setCurrentText(loaded_cell_type)

        date_text = str(prop_cfg.get("day_of_measurement", ""))
        date_value = QDate.fromString(date_text, "yyyy-MM-dd")
        if date_value.isValid():
            self.day_edit.setDate(date_value)

        self.user_edit.setText(str(prop_cfg.get("user", "")))
        self.experiment_name_edit.setText(str(prop_cfg.get("experiment_name", "")))

        imaging_mode = str(prop_cfg.get("imaging_local_or_global", "local"))
        self.local_radio.setChecked(imaging_mode != "global")
        self.global_radio.setChecked(imaging_mode == "global")

        self.bead_checkbox.setChecked(bool(prop_cfg.get("bead_contact", True)))
        self.duration_before_spin.setValue(float(prop_cfg.get("time_of_measurement_before_starting_point", 1.0)))
        self.duration_after_spin.setValue(float(prop_cfg.get("time_of_measurement_after_starting_point", 15.0)))

        self.channel_alignment_checkbox.setChecked(bool(post_cfg.get("channel_alignment_in_pipeline", False)))
        self.frame_by_frame_checkbox.setChecked(bool(post_cfg.get("channel_alignment_each_frame", False)))

        self.background_checkbox.setChecked(bool(post_cfg.get("background_sub_in_pipeline", False)))

        background_algorithm = post_cfg.get("background_subtractor_algorithm")
        if background_algorithm is None:
            background_algorithm = post_cfg.get("background_subtraction_algorithm", "Masked")
        self._set_combo_value(self.background_algorithm_combo, str(background_algorithm))

        wavelet_algorithm = post_cfg.get("wavelet_algorithm")
        if wavelet_algorithm is None:
            wavelet_algorithm = post_cfg.get("wavelet_background", "No")
        self._set_combo_value(self.wavelet_algorithm_combo, str(wavelet_algorithm))

        self.upsampling_checkbox.setChecked(bool(post_cfg.get("upsampling_in_pipeline", False)))
        self._set_combo_value(self.upsampling_algorithm_combo, str(post_cfg.get("upsampling_algorithm", "Fourier")))

        self.denoising_checkbox.setChecked(bool(post_cfg.get("denoising_in_pipeline", False)))
        self._set_combo_value(self.denoising_algorithm_combo, str(post_cfg.get("denoising_algorithm", "SparseHessian")))

        self.segmentation_checkbox.setChecked(bool(post_cfg.get("cell_segmentation_tracking_in_pipeline", True)))

        self.deconvolution_checkbox.setChecked(bool(post_cfg.get("deconvolution_in_pipeline", False)))
        self._set_combo_value(self.deconvolution_algorithm_combo, str(post_cfg.get("deconvolution_algorithm", "LR")))

        decon_iter = post_cfg.get("decon_iter")
        if decon_iter is None:
            decon_iter = post_cfg.get("iterations", "")
        self.text_iterations.setText("" if decon_iter is None else str(decon_iter))

        tde_lambda = post_cfg.get("TDE_lambda", "")
        self.text_TDE_lambda.setText("" if tde_lambda is None else str(tde_lambda))

        tde_lambda_t = post_cfg.get("TDE_lambda_t", "")
        self.text_TDE_lambda_t.setText("" if tde_lambda_t is None else str(tde_lambda_t))

        psf_cfg = post_cfg.get("psf", {})
        self.text_psf_type.setText(str(psf_cfg.get("type", "confocal")))
        self.text_psf_lambdaEx_ch1.setText(str(psf_cfg.get("lambdaEx_ch1", "488")))
        self.text_psf_lambdaEm_ch1.setText(str(psf_cfg.get("lambdaEm_ch1", "520")))
        self.text_psf_lambdaEx_ch2.setText(str(psf_cfg.get("lambdaEx_ch2", "488")))
        self.text_psf_lambdaEm_ch2.setText(str(psf_cfg.get("lambdaEm_ch2", "600")))
        self.text_psf_numAper.setText(str(psf_cfg.get("numAper", "1.4")))
        self.text_psf_magObj.setText(str(psf_cfg.get("magObj", "100")))
        self.text_psf_rindexObj.setText(str(psf_cfg.get("rindexObj", "1.518")))
        self.text_psf_rindexSp.setText(str(psf_cfg.get("rindexSp", "1.518")))
        self.text_psf_ccdSize.setText(str(psf_cfg.get("ccdSize", "6450")))

        self.bleaching_checkbox.setChecked(bool(post_cfg.get("bleaching_correction_in_pipeline", False)))
        self._set_combo_value(
            self.bleaching_algorithm_combo,
            str(post_cfg.get("bleaching_correction_algorithm", "additiv no fit")),
        )

        self.ratio_checkbox.setChecked(bool(post_cfg.get("ratio_images", True)))

        shape_cfg = config.get("processing_pipeline", {}).get("shape_normalization", {})
        analysis_cfg = config.get("processing_pipeline", {}).get("analysis", {})

        self.shape_normalization_checkbox.setChecked(bool(shape_cfg.get("shape_normalization", True)))
        self.hotspot_checkbox.setChecked(bool(analysis_cfg.get("hotspot_detection", True)))
        self.dartboard_checkbox.setChecked(bool(analysis_cfg.get("dartboard_projection", True)))

        self.on_select_mode_change()

        self._loading = False
        self._suspend_presets = False
        self.refresh_control_states(auto_select=False)

    @staticmethod
    def _set_combo_value(combo: QComboBox, value: str):
        idx = combo.findText(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def start_analysis(self):
        valid, msg = self._validate_start_conditions()
        if not valid:
            QMessageBox.warning(self.window, "Missing required input", msg)
            self._refresh_start_state()
            return

        try:
            self.write_input_to_config_file()
        except Exception as exc:
            QMessageBox.critical(self.window, "Invalid parameters", str(exc))
            return

        self.started = True
        self.cancelled = False
        self._set_status("Config written. Starting analysis...")
        self.window.close()

    def cancel(self):
        self.cancelled = True
        self.started = False
        self.window.close()

    def update_settings_for_registration(self):
        enabled = self.channel_alignment_checkbox.isChecked()
        self.frame_by_frame_checkbox.setEnabled(enabled)
        if not enabled:
            self.frame_by_frame_checkbox.setChecked(False)

    def update_settings_for_analysis(self, auto_select: bool | None = None):
        if auto_select is None:
            auto_select = not self._loading

        if not self.hotspot_checkbox.isChecked():
            self.dartboard_checkbox.setChecked(False)
            self.dartboard_checkbox.setEnabled(False)
            return

        can_enable = self.shape_normalization_checkbox.isChecked() and self.bead_checkbox.isChecked()
        self.dartboard_checkbox.setEnabled(can_enable)
        if can_enable and auto_select:
            self.dartboard_checkbox.setChecked(True)
        elif not can_enable:
            self.dartboard_checkbox.setChecked(False)

    def update_settings_shape_normalization(self, auto_select: bool | None = None):
        if auto_select is None:
            auto_select = not self._loading

        if not self.shape_normalization_checkbox.isChecked():
            self.dartboard_checkbox.setChecked(False)
            self.dartboard_checkbox.setEnabled(False)
            return

        self.hotspot_checkbox.setEnabled(True)
        if self.bead_checkbox.isChecked() and auto_select:
            self.hotspot_checkbox.setChecked(True)

        if self.bead_checkbox.isChecked() and self.hotspot_checkbox.isChecked():
            self.dartboard_checkbox.setEnabled(True)
            if auto_select:
                self.dartboard_checkbox.setChecked(True)

    def update_background(self):
        enabled = self.background_checkbox.isChecked()
        self.background_algorithm_combo.setEnabled(enabled)
        if not enabled:
            self.wavelet_algorithm_combo.setEnabled(False)
            return
        self.update_wavelet()

    def update_wavelet(self):
        enabled = self.background_checkbox.isChecked() and self.background_algorithm_combo.currentText() == "Wavelet"
        self.wavelet_algorithm_combo.setEnabled(enabled)

    def update_upsampling(self):
        self.upsampling_algorithm_combo.setEnabled(self.upsampling_checkbox.isChecked())

    def update_denoising(self):
        self.denoising_algorithm_combo.setEnabled(self.denoising_checkbox.isChecked())

    def update_deconvolution(self):
        enabled = self.deconvolution_checkbox.isChecked()
        self.deconvolution_algorithm_combo.setEnabled(enabled)
        self.decon_advanced_toggle.setEnabled(enabled)
        for widget in self.decon_base_fields:
            widget.setEnabled(enabled)

        if not enabled:
            self.decon_advanced_panel.setVisible(False)
        else:
            self.decon_advanced_panel.setVisible(self.decon_advanced_toggle.isChecked())

        if enabled:
            self.decon_selection_changed()

    def update_bleaching_correction(self):
        self.bleaching_algorithm_combo.setEnabled(self.bleaching_checkbox.isChecked())

    def update_bead_contact(self, auto_select: bool | None = None):
        if auto_select is None:
            auto_select = not self._loading

        if not self.bead_checkbox.isChecked():
            self.dartboard_checkbox.setChecked(False)
            self.dartboard_checkbox.setEnabled(False)
            return

        can_enable = self.shape_normalization_checkbox.isChecked() and self.hotspot_checkbox.isChecked()
        self.dartboard_checkbox.setEnabled(can_enable)
        if can_enable and auto_select:
            self.dartboard_checkbox.setChecked(True)

    def get_image_configuration(self):
        if self.image_single_radio.isChecked():
            return "single"
        return "two-in-one"

    def decon_selection_changed(self):
        chosen = self.deconvolution_algorithm_combo.currentText()
        if not self.deconvolution_checkbox.isChecked():
            self.text_TDE_lambda.setEnabled(False)
            self.text_TDE_lambda_t.setEnabled(False)
            self.text_iterations.setEnabled(False)
            return

        tde_enabled = chosen == "TDE"
        self.text_TDE_lambda.setEnabled(tde_enabled)
        self.text_TDE_lambda_t.setEnabled(tde_enabled)
        if not tde_enabled and not self._loading:
            self.text_TDE_lambda.clear()
            self.text_TDE_lambda_t.clear()

        iter_enabled = chosen == "LW"
        self.text_iterations.setEnabled(iter_enabled)
        if not iter_enabled and not self._loading:
            self.text_iterations.clear()

    def select_files_or_directory(self):
        mode = self._current_mode()
        selected_path = ""

        if mode == "file":
            selected_path, _ = QFileDialog.getOpenFileName(self.window, "Select file")
        elif mode == "dir":
            selected_path = QFileDialog.getExistingDirectory(self.window, "Select directory")
        else:
            selected_path = QFileDialog.getExistingDirectory(self.window, "Select checkpoint directory")

        if not selected_path:
            return

        if mode in ("file", "dir"):
            self.input_path_value = selected_path
            self.update_path_display(self.input_path_value)
        else:
            self.set_checkpoint_path_value(selected_path)

    def update_path_display(self, value: str):
        self.path_edit.setText(value or "")
        self._refresh_start_state()

    def on_select_mode_change(self):
        mode = self._current_mode()
        if mode in ("file", "dir"):
            self.last_input_mode = mode
            self.update_path_display(self.input_path_value)
        elif mode == "cp":
            self.update_path_display(self.checkpoint_path_value)
        else:
            self.update_path_display("")
        self._refresh_start_state()

    def set_checkpoint_path_value(self, value: str):
        self.checkpoint_path_value = value
        if self._current_mode() == "cp":
            self.update_path_display(self.checkpoint_path_value)
        self._refresh_start_state()

    def refresh_control_states(self, auto_select: bool = True):
        self.update_settings_for_registration()
        self.update_background()
        self.update_upsampling()
        self.update_denoising()
        self.update_deconvolution()
        self.update_bleaching_correction()
        self.update_settings_shape_normalization(auto_select=auto_select)
        self.update_settings_for_analysis(auto_select=auto_select)
        self.update_bead_contact(auto_select=auto_select)
        self._refresh_start_state()

    def set_default_settings_for_global_imaging(self):
        self.channel_alignment_checkbox.setChecked(True)
        self.frame_by_frame_checkbox.setChecked(False)
        self.background_checkbox.setChecked(False)
        self.deconvolution_checkbox.setChecked(False)
        self.bleaching_checkbox.setChecked(False)
        self.shape_normalization_checkbox.setChecked(False)
        self.hotspot_checkbox.setChecked(False)
        self.dartboard_checkbox.setChecked(False)
        self.refresh_control_states(auto_select=True)

    def set_default_settings_for_local_imaging(self):
        self.channel_alignment_checkbox.setChecked(True)
        self.frame_by_frame_checkbox.setChecked(False)
        self.background_checkbox.setChecked(True)

        self.set_default_decon_parameters()

        self.bleaching_checkbox.setChecked(True)
        self._set_combo_value(self.bleaching_algorithm_combo, "additiv no fit")

        self.shape_normalization_checkbox.setChecked(True)
        self.hotspot_checkbox.setChecked(True)
        self.dartboard_checkbox.setChecked(True)
        self.bead_checkbox.setChecked(True)

        self.refresh_control_states(auto_select=True)

    def set_default_decon_parameters(self):
        self.deconvolution_checkbox.setChecked(True)
        self._set_combo_value(self.deconvolution_algorithm_combo, "LR")

        self.text_psf_type.setText("confocal")
        self.text_psf_lambdaEx_ch1.setText("488")
        self.text_psf_lambdaEm_ch1.setText("520")
        self.text_psf_lambdaEx_ch2.setText("488")
        self.text_psf_lambdaEm_ch2.setText("600")
        self.text_psf_numAper.setText("1.4")
        self.text_psf_magObj.setText("100")
        self.text_psf_rindexObj.setText("1.518")
        self.text_psf_rindexSp.setText("1.518")
        self.text_psf_ccdSize.setText("6450")

        self.text_TDE_lambda.clear()
        self.text_TDE_lambda_t.clear()
        self.text_iterations.clear()

        self.decon_selection_changed()

    def choose_results_directory_clicked(self):
        self.select_results_directory()

    def select_results_directory(self):
        path = QFileDialog.getExistingDirectory(self.window, "Select results directory")
        if not path:
            return
        self.results_dir_edit.setText(path)
        self._refresh_start_state()

    def write_input_to_config_file(self):
        data = self.get_parameters()
        with open("config.toml", "w", encoding="utf-8") as file:
            tomlkit.dump(data, file)

    def manage_cell_types(self):
        dialog = QDialog(self.window)
        dialog.setWindowTitle("Manage Cell Types")
        dialog.resize(640, 420)

        layout = QHBoxLayout(dialog)
        list_widget = QListWidget()
        list_widget.addItems(self.cell_types)

        buttons_layout = QVBoxLayout()
        add_btn = QPushButton("Add Cell Type")
        delete_btn = QPushButton("Delete Cell Type")
        view_btn = QPushButton("View Parameters")
        plot_btn = QPushButton("Plot calibration curve")
        close_btn = QPushButton("Close")

        for btn in (add_btn, delete_btn, view_btn, plot_btn):
            buttons_layout.addWidget(btn)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(close_btn)

        layout.addWidget(list_widget, stretch=1)
        layout.addLayout(buttons_layout)

        def refresh_list():
            list_widget.clear()
            list_widget.addItems(self.cell_types)
            self._refresh_cell_type_combo()

        def get_selected_cell_type() -> str | None:
            item = list_widget.currentItem()
            return item.text() if item is not None else None

        def add_cell_type():
            name, ok = QInputDialog.getText(dialog, "Add Cell Type", "Enter the name of the cell type:")
            name = name.strip()
            if not ok or not name:
                return
            if name in self.cell_types:
                QMessageBox.warning(dialog, "Duplicate", "Cell type already exists.")
                return

            params = self._prompt_cell_type_parameters(dialog, name)
            if params is None:
                return

            self.cell_types.append(name)
            self.parameters_dict[name] = params
            refresh_list()

        def delete_cell_type():
            selected = get_selected_cell_type()
            if selected is None:
                return
            if selected in self.cell_types:
                self.cell_types.remove(selected)
            self.parameters_dict.pop(selected, None)
            if not self.cell_types:
                self.cell_types = ["jurkat"]
                self.parameters_dict.setdefault("jurkat", {})
            refresh_list()

        def view_parameters():
            selected = get_selected_cell_type()
            if selected is None:
                QMessageBox.warning(dialog, "No selection", "Please select a cell type.")
                return

            params = dict(self.parameters_dict.get(selected, {}))
            if not params:
                QMessageBox.warning(dialog, "No parameters", "No parameters found for this cell type.")
                return

            editor = QDialog(dialog)
            editor.setWindowTitle(f"{selected} Parameters")
            editor_layout = QVBoxLayout(editor)
            form = QFormLayout()

            edits: dict[str, QLineEdit] = {}
            for param_name in params.keys():
                edit = QLineEdit(str(params[param_name]))
                edit.setValidator(QDoubleValidator(-1_000_000_000.0, 1_000_000_000.0, 10, editor))
                edits[param_name] = edit
                form.addRow(param_name, edit)

            save_btn = QPushButton("Save Changes")
            editor_layout.addLayout(form)
            editor_layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

            def save_changes():
                updated = {}
                try:
                    for key, edit in edits.items():
                        updated[key] = float(edit.text())
                except ValueError:
                    QMessageBox.critical(editor, "Invalid input", "All parameter values must be numeric.")
                    return
                self.parameters_dict[selected] = updated
                editor.accept()

            save_btn.clicked.connect(save_changes)
            editor.exec()

        def plot_calibration_curve():
            selected = get_selected_cell_type()
            if selected is None:
                QMessageBox.warning(dialog, "No selection", "Please select a cell type.")
                return

            params = dict(self.parameters_dict.get(selected, {}))
            if not params:
                QMessageBox.warning(dialog, "No parameters", "No parameters found for this cell type.")
                return

            kd_key = "KD value (of Ca2+ dye) [nM]"
            kd_alt_key = "KD value (of Ca2+ dye)"
            kd_value = params.get(kd_key, params.get(kd_alt_key))

            required = {
                "minimum ratio": params.get("minimum ratio"),
                "maximum ratio": params.get("maximum ratio"),
                "minimum fluorescence intensity": params.get("minimum fluorescence intensity"),
                "maximum fluorescence intensity": params.get("maximum fluorescence intensity"),
            }

            if kd_value is None or any(v is None for v in required.values()):
                QMessageBox.warning(dialog, "Missing parameters", "Calibration parameters are incomplete.")
                return

            kd_value = float(kd_value)
            min_ratio = float(required["minimum ratio"])
            max_ratio = float(required["maximum ratio"])
            min_intensity = float(required["minimum fluorescence intensity"])
            max_intensity = float(required["maximum fluorescence intensity"])

            if max_ratio <= min_ratio:
                QMessageBox.warning(dialog, "Invalid range", "maximum ratio must be greater than minimum ratio.")
                return

            ratio_values = np.linspace(min_ratio, max_ratio, num=100, endpoint=False)
            corresponding_ca_values = [
                kd_value * ((ratio - min_ratio) / (max_ratio - ratio)) * (min_intensity / max_intensity)
                for ratio in ratio_values
            ]

            plt.figure(figsize=(7, 4))
            plt.plot(ratio_values, corresponding_ca_values)
            plt.title(f"Calibration Curve - {selected}")
            plt.xlabel("Ratio Value")
            plt.ylabel("Corresponding Ca2+ Value (nM)")
            plt.tight_layout()
            plt.show(block=False)

        add_btn.clicked.connect(add_cell_type)
        delete_btn.clicked.connect(delete_cell_type)
        view_btn.clicked.connect(view_parameters)
        plot_btn.clicked.connect(plot_calibration_curve)
        close_btn.clicked.connect(dialog.accept)

        dialog.exec()

    def _prompt_cell_type_parameters(self, parent: QWidget, cell_type: str):
        parameter_names = [
            "KD value (of Ca2+ dye) [nM]",
            "minimum ratio",
            "maximum ratio",
            "minimum fluorescence intensity",
            "maximum fluorescence intensity",
            "spot Height Ca2+ microdomains",
        ]
        values = {}
        for param in parameter_names:
            value, ok = QInputDialog.getDouble(
                parent,
                f"Enter {param}",
                f"Enter value for {param} ({cell_type})",
                decimals=6,
            )
            if not ok:
                return None
            values[param] = float(value)
        return values

    def _refresh_cell_type_combo(self):
        current = self.cell_type_combo.currentText()
        self.cell_type_combo.blockSignals(True)
        self.cell_type_combo.clear()
        self.cell_type_combo.addItems(self.cell_types)
        if current in self.cell_types:
            self.cell_type_combo.setCurrentText(current)
        elif self.cell_types:
            self.cell_type_combo.setCurrentText(self.cell_types[0])
        self.cell_type_combo.blockSignals(False)
