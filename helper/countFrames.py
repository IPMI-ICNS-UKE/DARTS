import argparse
import sys
from pathlib import Path

from PIL import Image


def count_frames(path: Path) -> int:
    """Return number of frames/pages in an image (defaults to 1 if absent)."""
    with Image.open(path) as img:
        return getattr(img, "n_frames", 1)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Count frames/pages in an image file.")
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="Path to the image file to inspect.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        frames = count_frames(args.file)
    except FileNotFoundError:
        print(f"File not found: {args.file}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Could not open file {args.file}: {exc}", file=sys.stderr)
        return 1

    print(f"Number of frames: {frames}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
