#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "SimpleITK",
# ]
# ///

"""Script to find the bounding box of an object in a binary image."""

import sys
import SimpleITK as sitk


def bound_obj(input_image, threshold=1.0):
    """Find the bounding box of an object in a binary image."""

    img2 = input_image >= threshold
    stats = sitk.LabelShapeStatisticsImageFilter()
    stats.Execute(img2)

    n = stats.GetNumberOfLabels()
    if n == 0:
        print("Error:  No labels")
        return

    b = stats.GetBoundingBox(1)
    print("X range:", b[0], b[0] + b[3] - 1)
    print("Y range:", b[1], b[1] + b[4] - 1)
    print("Z range:", b[2], b[2] + b[5] - 1)


def main(argv=None):
    """CLI entry point."""
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("Usage: sitk-bound-obj <input_image> [threshold]")
        return 1

    img_name = args[0]
    threshold = 1.0
    if len(args) > 1:
        threshold = float(args[1])

    img = sitk.ReadImage(img_name)
    bound_obj(img, threshold)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
