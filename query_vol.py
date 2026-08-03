#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "SimpleITK",
#   "numpy",
# ]
# ///

""" query_vol.py: Query volume information """

import sys
import argparse
import SimpleITK as sitk
import histo


def compute_corners(img):
    """Compute the physical coordinates of the corners of the volume"""
    sz = img.GetSize()
    corners = []
    pt_corners = []
    for z in (0, 1):
        zc = (sz[2] - 1) * z
        for y in (0, 1):
            yc = (sz[1] - 1) * y
            for x in (0, 1):
                xc = (sz[0] - 1) * x
                c = [xc, yc, zc]
                corners.append(c)
    for c in corners:
        pt = img.TransformIndexToPhysicalPoint(c)
        pt_corners.append(pt)

    return pt_corners


def compute_bounds(img):
    """Compute the physical bounds of the volume"""
    corners = compute_corners(img)
    mins = [1e9, 1e9, 1e9]
    maxs = [-1e9, -1e9, -1e9]
    for pt in corners:
        for i in range(3):
            mins[i] = min(mins[i], pt[i])
            maxs[i] = max(maxs[i], pt[i])

    print("Bounds:", mins, maxs)


def query_vol(img, histoFlag=False, nbins=50, img_range=None, chart_width=60):
    """Query volume information"""
    print()
    print("Pixel type:", img.GetPixelIDTypeAsString())
    print("Size:      ", img.GetSize())
    print("Spacing:   ", img.GetSpacing())
    print("Origin:    ", img.GetOrigin())
    print("Direction: ", img.GetDirection())
    print()
    stats = sitk.StatisticsImageFilter()
    stats.Execute(img)
    print("Range:", stats.GetMinimum(), stats.GetMaximum())
    print("Mean:", stats.GetMean())
    print("StdDev:", stats.GetSigma())
    print()
    compute_bounds(img)

    if histoFlag:
        histo.histo(img, nbins=nbins, img_range=img_range, chart_width=chart_width)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Query volume information and display histogram."
    )
    parser.add_argument(
        "input",
        help="Input image file"
    )
    parser.add_argument(
        "-b", "--bins",
        type=int,
        default=25,
        help="Number of bins in histogram (default: 25)"
    )
    parser.add_argument(
        "--no-histogram",
        action="store_true",
        help="Skip histogram display"
    )
    parser.add_argument(
        "-r", "--range",
        type=float,
        nargs=2,
        metavar=("MIN", "MAX"),
        help="Custom range for histogram (e.g., -1000 2000)"
    )
    parser.add_argument(
        "-w", "--chart-width",
        type=int,
        default=60,
        help="Width of histogram chart in characters (default: 60)"
    )
    args = parser.parse_args()

    if args.bins <= 0:
        parser.error("--bins must be a positive integer")
    if args.chart_width <= 0:
        parser.error("--chart-width must be a positive integer")
    if args.range is not None and args.range[0] >= args.range[1]:
        parser.error("--range MIN must be less than MAX")

    try:
        in_img = sitk.ReadImage(args.input)
    except RuntimeError:
        print("Error: unable to read", args.input)
        sys.exit(1)


    print()
    print("File:      ", args.input)
    query_vol(
        in_img,
        not args.no_histogram,
        nbins=args.bins,
        img_range=args.range,
        chart_width=args.chart_width,
    )
