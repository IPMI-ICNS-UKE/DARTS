---
layout: default
title: Frame Index Mismatch Fix Spec
parent: Getting Started
nav_order: 99
---

# Frame Index Mismatch Fix Spec

## Goal
Fix crashes and wrong bead-contact-to-cell assignments caused by mixing:
- global frame indices (original TIFF timeline, used in bead-contact GUI), and
- local frame indices (per-track reindexed timeline, used for ROI arrays).

This spec implements only:
1. crash guard in bead-contact assignment
2. explicit support for both global and local frame indices

## Problem Summary
Current pipeline behavior:
- Bead contact time (`starting_point`) is selected in global TIFF frame coordinates.
- During ROI extraction, track frames are reindexed from original sparse/global values to local `0..N-1`.
- Later, bead contact assignment looks up `dataframe['frame'] == starting_point`.
- For cells where local `frame` does not contain the global frame value, lookup is empty and code still indexes `[0]`, causing:
  - `IndexError: list index out of range`

Observed failing location:
- `src/general/processing.py` in `assign_bead_contacts_to_cells()`

Contributing reindex location:
- `src/postprocessing/CellTracker_ROI.py` in `give_rois()` where `particle_dataframe_subset['frame']` is overwritten.

## Scope
### In scope
- Add robust empty-check handling before indexing track rows.
- Preserve original/global frame index in each cell dataframe.
- Keep local reindexed frame for ROI processing.
- Use global frame for bead-contact assignment.

### Out of scope
- Nearest-frame fallback logic.
- Changes to GUI behavior.
- Changes to tracking thresholds/search range policy.

## Design
### Data model
Each per-cell dataframe must carry both:
- `frame_global`: original frame index from tracking results / TIFF timeline.
- `frame`: local contiguous index (`0..N-1`) used by ROI-aligned arrays.

### Matching rule in bead-contact assignment
- `starting_point` must be matched against `frame_global` (not `frame`).
- If no row exists for `starting_point`, the current cell is skipped for that bead contact.

## Required Code Changes

### 1) Preserve global frame before reindex
File:
- `src/postprocessing/CellTracker_ROI.py`

Function:
- `give_rois(...)`

Current behavior:
- Resets `particle_dataframe_subset['frame']` to local indices.

Required behavior:
- Before overwriting `frame`, copy it into `frame_global`.
- Then write local indices into `frame`.

Expected pattern:
- `frame_global = old frame list`
- `frame = range(len(track))`

### 2) Guard against empty frame lookup
File:
- `src/general/processing.py`

Function:
- `assign_bead_contacts_to_cells(self)`

Current behavior:
- Logs empty lookup but still executes:
  - `cell_data_for_frame['bbox'].values.tolist()[0]`

Required behavior:
- If lookup is empty, log and `continue` for this cell.
- Never index `[0]` on empty selection.

### 3) Use global frame in bead-contact lookup
File:
- `src/general/processing.py`

Function:
- `assign_bead_contacts_to_cells(self)`

Required behavior:
- Lookup row by `frame_global == starting_point`.
- Backward compatibility: if `frame_global` column is absent (legacy checkpoint/object), fall back to existing `frame` lookup.

Suggested lookup logic:
- if `'frame_global' in dataframe.columns`: use `frame_global`
- else: use `frame`

## Acceptance Criteria
1. No crash on missing frame:
- Run that previously failed at `IndexError` now completes assignment stage without exception.

2. Correct frame-domain mapping:
- For a bead contact at frame `T`, assignment attempts match in `frame_global == T`.
- Local `frame` remains contiguous `0..N-1` for ROI-based processing.

3. Logging behavior:
- Missing tracked frame prints a clear message and skips that cell/contact pair.
- Processing continues for remaining cells/files.

4. Regression safety:
- Runs without bead contacts are unaffected.
- Existing ROI generation still works with local frame indexing.

## Test Plan
### Test A: Reproduce original failing dataset
- Input: dataset that previously logged
  - `No tracked frame 602 for this cell; available frames: [0..540]`
- Expected:
  - no `IndexError`
  - warning emitted
  - run continues

### Test B: Positive assignment path
- Use cell track containing selected bead-contact frame in global timeline.
- Expected:
  - cell gets `has_bead_contact = True`
  - `starting_point` set correctly
  - bead-contact site assigned

### Test C: Mixed-cell scenario
- In one run, some cells contain selected global frame, others do not.
- Expected:
  - only valid cells assigned
  - invalid cells skipped without crash

## Risks and Mitigations
- Risk: downstream code may implicitly assume `frame` is global.
  - Mitigation: keep `frame` local as before, add `frame_global` as additive field.
- Risk: legacy dataframes/checkpoints without `frame_global`.
  - Mitigation: explicit fallback to `frame`.

## Rollback
If needed, rollback can be limited to:
- removing `frame_global` addition
- restoring old lookup in `assign_bead_contacts_to_cells`

This rollback is not recommended because it reintroduces the crash condition.
