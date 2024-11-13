#! /usr/bin/env python3

""" histo.py: Compute histogram of an image """

import sys
import SimpleITK as sitk
import numpy as np


def histo(img, nbins=50, img_range=None):
    """Compute histogram of an image"""

    if img_range is None:
        stats = sitk.StatisticsImageFilter()
        stats.Execute(img)
        img_range = [stats.GetMinimum(), stats.GetMaximum()]

    np_img = sitk.GetArrayFromImage(img)
    hist, bins = np.histogram(np_img, bins=nbins, range=img_range)

    print("\nHistogram")
    print("   bin_start    bin_count")
    for i in range(nbins):
        # print("{}, {}".format(bin_starts[i], hist[i]))
        print(f"{bins[i]:12.2f}\t{hist[i]}")
    return hist, bins


if __name__ == "__main__":
    in_img = sitk.ReadImage(sys.argv[1])

    # Defaults to standard Hounsfield units range
    r = [-1000.0, 2000.0]
    histo(in_img, 50, r)
