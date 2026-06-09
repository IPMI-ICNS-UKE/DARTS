#!/usr/bin/env python3
"""Save the first N frames of a TIFF stack into a new file."""

import argparse
import os

import tifffile


def parse_args():
    parser = argparse.ArgumentParser(description="Trim a TIFF stack to the first N frames.")
    parser.add_argument("input", help="Path to input .tif/.tiff file")
    parser.add_argument("output", help="Path to output .tif/.tiff file")
    parser.add_argument("-n", "--frames", type=int, required=True, help="Number of frames to keep")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.frames <= 0:
        raise ValueError("--frames must be a positive integer")

    stack = tifffile.imread(args.input)

    if stack.ndim == 2:
        trimmed = stack
    else:
        trimmed = stack[: args.frames]

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    tifffile.imwrite(args.output, trimmed)


if __name__ == "__main__":
    main()
