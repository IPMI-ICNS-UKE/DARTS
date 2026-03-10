#!/usr/bin/env python3
"""Export a specific frame/page from a TIFF file to PNG."""

import argparse
import sys
from pathlib import Path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export one TIFF frame/page as a PNG.")
    parser.add_argument("file", type=Path, help="Path to input .tif/.tiff file")
    parser.add_argument("frame", type=int, help="Zero-based frame/page index")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output PNG path (default: <input_stem>_frame_<index>.png)",
    )
    return parser.parse_args(argv)


def default_output_path(input_path: Path, frame: int) -> Path:
    return input_path.with_name(f"{input_path.stem}_frame_{frame}.png")


def load_frame_with_tifffile(path: Path, frame: int):
    try:
        import tifffile
    except ModuleNotFoundError:
        return None, None, "tifffile_not_installed"

    try:
        data = tifffile.imread(path)
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise OSError(f"Could not read TIFF file {path}: {exc}") from exc

    if data.ndim == 2:
        frame_count = 1
        frame_data = data
    elif data.ndim == 3 and data.shape[-1] in (3, 4):
        # Likely a single RGB/RGBA image.
        frame_count = 1
        frame_data = data
    else:
        frame_count = data.shape[0]
        if frame >= frame_count:
            return None, frame_count, "out_of_range"
        frame_data = data[frame]

    if frame >= frame_count:
        return None, frame_count, "out_of_range"
    return frame_data, frame_count, None


def load_frame_with_pillow(path: Path, frame: int):
    try:
        from PIL import Image
    except ModuleNotFoundError:
        return None, None, "pillow_not_installed"

    try:
        with Image.open(path) as img:
            frame_count = getattr(img, "n_frames", 1)
            if frame >= frame_count:
                return None, frame_count, "out_of_range"
            img.seek(frame)
            return img.copy(), frame_count, None
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise OSError(f"Could not read TIFF file {path}: {exc}") from exc


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if args.frame < 0:
        print("Frame index must be >= 0.", file=sys.stderr)
        return 1

    try:
        frame_data, frame_count, error = load_frame_with_tifffile(args.file, args.frame)
        if error == "out_of_range":
            print(
                f"Frame index out of range: {args.frame} (available 0..{frame_count - 1})",
                file=sys.stderr,
            )
            return 1

        if error == "tifffile_not_installed":
            frame_data, frame_count, error = load_frame_with_pillow(args.file, args.frame)
            if error == "pillow_not_installed":
                print(
                    "Missing dependencies. Install one of: `pip install tifffile` or `pip install pillow`.",
                    file=sys.stderr,
                )
                return 1
            if error == "out_of_range":
                print(
                    f"Frame index out of range: {args.frame} (available 0..{frame_count - 1})",
                    file=sys.stderr,
                )
                return 1
    except FileNotFoundError:
        print(f"File not found: {args.file}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        from PIL import Image
    except ModuleNotFoundError:
        print("Missing dependency: Pillow. Install it with `pip install pillow`.", file=sys.stderr)
        return 1

    if isinstance(frame_data, Image.Image):
        frame_image = frame_data
    else:
        try:
            frame_image = Image.fromarray(frame_data)
        except Exception as exc:  # Pillow raises different exception types by dtype/mode.
            print(f"Could not convert frame to image: {exc}", file=sys.stderr)
            return 1

    output_path = args.output if args.output is not None else default_output_path(args.file, args.frame)
    output_path = output_path.with_suffix(".png")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        frame_image.save(output_path, format="PNG")
    except OSError as exc:
        print(f"Could not write PNG file {output_path}: {exc}", file=sys.stderr)
        return 1

    print(f"Saved PNG: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
