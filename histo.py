#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "SimpleITK",
#   "numpy",
# ]
# ///

""" histo.py: Compute histogram of an image """

import sys
import SimpleITK as sitk
import numpy as np


def histo(img, nbins=50, img_range=None, chart_width=60):
    """Compute histogram of an image"""

    if img_range is None:
        stats = sitk.StatisticsImageFilter()
        stats.Execute(img)
        img_range = [stats.GetMinimum(), stats.GetMaximum()]

    np_img = sitk.GetArrayFromImage(img)
    hist, bins = np.histogram(np_img, bins=nbins, range=img_range)

    print("\nHistogram")
    _draw_histogram(hist, bins, nbins, width=chart_width)
    return hist, bins


def _draw_histogram(hist, bins, nbins, width=60):
    """Draw a text-based histogram chart"""
    if len(hist) == 0:
        return

    max_count = max(hist)
    if max_count == 0:
        return

    print(f"{'Bin Start':>12} | Count        | Chart")
    print("-" * (12 + 1 + 12 + 1 + width))

    for i in range(nbins):
        bin_start = bins[i]
        count = hist[i]
        bar_width = int((count / max_count) * width) if max_count > 0 else 0
        histogram_bar = "█" * bar_width
        print(f"{bin_start:12.2f} | {count:11d} | {histogram_bar}")


if __name__ == "__main__":
    in_img = sitk.ReadImage(sys.argv[1])

    # Defaults to standard Hounsfield units range
    r = [-1000.0, 2000.0]
    histo(in_img, 50, r)
