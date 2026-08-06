#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "SimpleITK",
# ]
# ///


"""  A simple script that uses SimpleITK's Show function to display images
  in Fiji/ImageJ, by default. """

import argparse
import SimpleITK as sitk


def main(argv=None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="sitk-show",
        description="Display one or more images with SimpleITK Show().",
    )
    parser.add_argument("filenames", nargs="+", help="Input image file(s).")
    parser.add_argument(
        "--scale",
        "-s",
        action="store",
        dest="scale",
        type=float,
        default=1.0,
        help="Intensity scale factor.",
    )

    args = parser.parse_args(argv)
    print(args)

    for x in args.filenames:
        print(x)
        img = sitk.ReadImage(x)
        if img.GetNumberOfComponentsPerPixel() == 1:
            img = img * args.scale
        sitk.Show(img, x)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
