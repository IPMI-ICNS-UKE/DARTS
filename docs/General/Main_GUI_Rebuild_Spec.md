# Main GUI Rebuild Specification (Codex-Ready)

## 1. Objective
Rebuild the **main DARTS GUI** with a sleek, clean, highly user-friendly design while preserving existing behavior.

Core user intent:
- The GUI must feel direct and responsive.
- Spacing/layout must be clearly improved.
- All currently editable parameters must remain editable.
- No analysis functionality or parameter semantics may change.

## 2. Scope
In scope:
- Full visual redesign of the main GUI.
- Improved layout/spacing/information hierarchy.
- Faster-feeling interactions and immediate UI feedback.
- Optional step-by-step flow (wizard-like) as a UI pattern.
- Framework switch is allowed.
- Keep save/load settings easy.

Out of scope:
- Any change to analysis logic.
- Any change to parameter meaning/semantics.
- Removal of any currently editable parameter.
- Rebuild of secondary GUIs (bead/no-bead dialogs) in this phase.

## 3. Target Platforms
Must support:
- macOS
- Windows
- Linux

## 4. Workflow Constraints (Must Preserve)
The current end-to-end workflow must stay equivalent:
1. Open main GUI.
2. Configure input/output, measurement metadata, and pipeline settings.
3. Save settings and/or load settings from TOML.
4. Start run (writes `config.toml` and exits main GUI).
5. Downstream execution remains unchanged (`main.py` flow and post-main dialogs).

## 5. Functional Parity Requirements
All fields currently represented in `TDarts_GUI.get_parameters()` must remain available and editable in the new main GUI.

Required configuration coverage:
- `input_output`
  - `file_or_directory`
  - `image_conf`
  - `path`
  - `results_dir`
  - `excel_filename_microdomain_data`
- `properties_of_measurement`
  - `used_microscope`
  - `scale`
  - `frame_rate`
  - `resolution`
  - `cell_type`
  - `cell_types_options`
  - `calibration_parameters_cell_types`
  - `day_of_measurement`
  - `user`
  - `experiment_name`
  - `imaging_local_or_global`
  - `bead_contact`
  - `duration_of_measurement`
  - `wavelength_1`
  - `wavelength_2`
  - `time_of_measurement_before_starting_point`
  - `time_of_measurement_after_starting_point`
- `processing_pipeline.postprocessing`
  - `channel_alignment_in_pipeline`
  - `channel_alignment_each_frame`
  - `registration_method`
  - `upsampling_in_pipeline`
  - `upsampling_algorithm`
  - `denoising_in_pipeline`
  - `denoising_algorithm`
  - `background_sub_in_pipeline`
  - `background_subtractor_algorithm`
  - `wavelet_algorithm`
  - `cell_segmentation_tracking_in_pipeline`
  - `deconvolution_in_pipeline`
  - `deconvolution_algorithm`
  - `decon_iter`
  - `TDE_lambda`
  - `TDE_lambda_t`
  - `psf.type`
  - `psf.lambdaEx_ch1`
  - `psf.lambdaEm_ch1`
  - `psf.lambdaEx_ch2`
  - `psf.lambdaEm_ch2`
  - `psf.numAper`
  - `psf.magObj`
  - `psf.rindexObj`
  - `psf.ccdSize`
  - `psf.dz`
  - `psf.nslices`
  - `psf.depth`
  - `psf.rindexSp`
  - `psf.nor`
  - `psf.xysize`
  - `bleaching_correction_in_pipeline`
  - `bleaching_correction_algorithm`
  - `ratio_images`
  - `median_filter_kernel`
- `processing_pipeline.shape_normalization`
  - `shape_normalization`
- `processing_pipeline.analysis`
  - `hotspot_detection`
  - `dartboard_projection`
- `processing_pipeline.checkpoints`
  - `save_pre_start`
  - `load_pre_start`
  - `source_dir`

## 6. Backward Compatibility (Required)
Settings I/O must keep compatibility with existing TOML files.

The new GUI must continue to read these legacy alias keys:
- `background_subtraction_algorithm` <-> `background_subtractor_algorithm`
- `wavelet_background` <-> `wavelet_algorithm`
- `iterations` <-> `decon_iter`

Behavioral requirement:
- Loading old settings must produce equivalent effective state in UI.
- Saving from the new GUI must remain consumable by current `main.py` pipeline.

## 7. Responsiveness and Perceived Performance
The app should feel immediate after user actions.

Recommended practical targets (desktop UX baselines):
- Control feedback (button highlight/toggle/selection): <= 100 ms
- Simple panel/step switch: <= 150 ms
- Opening native file dialog: trigger immediately (no app-side delay before OS dialog)
- Loading settings file and reflecting values in UI: <= 300 ms for typical files
- Pressing `Start` should provide visible acknowledgement immediately (<= 100 ms), then perform write/close flow

Software-style references (for intuition):
- VS Code side panel toggle feels instant around ~50-120 ms.
- Slack/Discord channel switch usually feels immediate around ~100-200 ms.
- Native desktop setting dialogs generally feel instant when below ~150 ms response.

Implementation requirement:
- No avoidable synchronous heavy work on the UI thread during interaction.

## 8. UX / Layout Requirements
- Clear grouping with stronger visual hierarchy than current dense grid.
- Increased spacing and readable alignment.
- Preserve all options but reduce cognitive load by grouping and progressive disclosure.
- Keep primary actions clear: `Load Settings`, `Save Settings`, `Start`, `Cancel`.
- Keep path selection and settings file loading straightforward (same or fewer clicks than current flow).

Optional pattern:
- Step-by-step wizard is allowed but not mandatory.

## 9. State and Dependency Rules
Existing dependency logic must remain equivalent:
- Channel alignment off => frame-by-frame registration disabled.
- Hotspot off => dartboard disabled.
- Shape normalization off => dartboard disabled.
- Bead contact off => dartboard disabled.
- Deconvolution off => decon fields disabled.
- TDE selected => `TDE_lambda`, `TDE_lambda_t` enabled.
- LW selected => `decon_iter` enabled.
- Background subtraction off => background algorithm and wavelet controls disabled.
- Wavelet controls enabled only when background method is Wavelet.
- Imaging presets (`local`/`global`) must preserve current default toggling behavior.

## 10. Recommended Technical Direction
Preferred:
- Rebuild main GUI in `PySide6` (or `PyQt6`) for better layout system and cross-platform consistency.

Architecture guardrails:
- Separate view state model from widget construction.
- Centralized config serialization/deserialization layer.
- Keep output schema identical to current `config.toml` expectations.
- Add lightweight validation with inline messages (without changing semantics).

## 11. Acceptance Criteria
The rebuild is done when all conditions below pass:
1. Main GUI launches on macOS/Windows/Linux.
2. Every currently editable parameter is present and editable.
3. Current workflow remains equivalent from user perspective.
4. Existing settings TOML files load successfully (including alias keys).
5. New saved TOML works with current pipeline execution (`python main.py`).
6. Interaction latency targets are met in normal local runs.
7. No analysis behavior changes are introduced.

## 12. Test Checklist (Manual)
- Launch app and verify main window.
- Toggle each pipeline checkbox and verify dependent controls.
- Test both `local` and `global` presets.
- Test `file`, `dir`, and `checkpoint` input modes.
- Load historical TOML variants and verify all mapped fields.
- Save settings, diff keys/values vs expected schema.
- Press `Start`, confirm `config.toml` is written and flow continues as before.

## 13. Implementation Notes for Codex
- Phase 1 only: main GUI replacement.
- Keep old GUI available behind a temporary fallback switch until parity is confirmed.
- Do not modify analysis modules unless strictly required for wiring.
- If any parity conflict appears, preserve existing behavior over visual preference.
