#!/usr/bin/env python3
"""
Small helper script to count "red" pixels in an image (e.g., tracks_overlay_frame*.png).

Definition of red: channel R is strictly greater than both G and B (optionally with a margin).
"""

import argparse
import sys

import imageio.v2 as iio
import numpy as np


def count_red_pixels(path: str, margin: int = 0) -> int:
    """
    Count pixels where R > G + margin and R > B + margin.
    """
    img = iio.imread(path)
    if img.ndim < 3 or img.shape[2] < 3:
        raise ValueError("Image does not have at least 3 channels.")
    r = img[..., 0].astype(np.int32)
    g = img[..., 1].astype(np.int32)
    b = img[..., 2].astype(np.int32)
    red_mask = (r > g + margin) & (r > b + margin)
    return int(red_mask.sum())


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Count red pixels in an image.")
    parser.add_argument("image", help="Path to PNG/JPEG/etc. image")
    parser.add_argument("--margin", type=int, default=0,
                        help="Minimum margin by which R must exceed G and B (default: 0)")
    args = parser.parse_args(argv)

    try:
        total = count_red_pixels(args.image, args.margin)
    except Exception as exc:  # pragma: no cover - simple CLI helper
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Red pixels: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
