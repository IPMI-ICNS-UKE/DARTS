#!/usr/bin/env python3
"""Convert a 4D 2-channel TIFF into a 3D two-in-one stack (channels side-by-side)."""

import argparse
import os

import numpy as np
import tifffile


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert a 4D 2-channel TIFF to a 3D two-in-one stack (T,H,2W)."
    )
    parser.add_argument("input", help="Path to input .tif/.tiff file")
    parser.add_argument("output", help="Path to output .tif/.tiff file")
    parser.add_argument(
        "--channel-axis",
        type=int,
        default=None,
        help="Channel axis index if known (e.g., -1 for last, 0 for first).",
    )
    return parser.parse_args()


def infer_channel_axis(arr):
    if arr.ndim != 4:
        raise ValueError(f"Expected 4D array, got shape {arr.shape}")
    # Common layouts: (T,H,W,C) or (C,T,H,W)
    if arr.shape[-1] == 2:
        return -1
    if arr.shape[0] == 2:
        return 0
    if arr.shape[1] == 2:
        return 1
    if arr.shape[2] == 2:
        return 2
    raise ValueError(f"Could not infer channel axis for shape {arr.shape}")


def move_channels_to_last(arr, axis):
    if axis < 0:
        axis = arr.ndim + axis
    if axis == arr.ndim - 1:
        return arr
    return np.moveaxis(arr, axis, -1)


def main():
    args = parse_args()
    data = tifffile.imread(args.input)

    if data.ndim == 3:
        raise ValueError("Input is already 3D; no conversion needed.")

    if data.ndim != 4:
        raise ValueError(f"Unsupported input shape {data.shape}; expected 4D.")

    axis = args.channel_axis if args.channel_axis is not None else infer_channel_axis(data)
    data = move_channels_to_last(data, axis)

    if data.shape[-1] != 2:
        raise ValueError(f"Expected 2 channels after reordering, got {data.shape[-1]}")

    ch1 = data[..., 0]
    ch2 = data[..., 1]

    if ch1.shape != ch2.shape:
        raise ValueError("Channel shapes do not match; cannot concatenate.")

    # Concatenate along width (axis=2 for (T,H,W))
    two_in_one = np.concatenate([ch1, ch2], axis=2)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    tifffile.imwrite(args.output, two_in_one)


if __name__ == "__main__":
    main()
