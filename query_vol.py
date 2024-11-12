#! /usr/bin/env python

""" query_vol.py: Query volume information """

import sys
import SimpleITK as sitk
import histo


def compute_corners(img):
    """ Compute the physical coordinates of the corners of the volume """
    sz = img.GetSize()
    corners = []
    pt_corners = []
    for z in (0, 1):
        zc = (sz[2]-1) * z
        for y in (0, 1):
            yc = (sz[1]-1) * y
            for x in (0, 1):
                xc = (sz[0]-1) * x
                c = [xc, yc, zc]
                corners.append(c)
    for c in corners:
        pt = img.TransformIndexToPhysicalPoint(c)
        pt_corners.append(pt)

    return pt_corners


def compute_bounds(img):
    """ Compute the physical bounds of the volume """
    corners = compute_corners(img)
    mins = [1e9, 1e9, 1e9]
    maxs = [-1e9, -1e9, -1e9]
    for pt in corners:
        for i in range(3):
            mins[i] = min(mins[i], pt[i])
            maxs[i] = max(maxs[i], pt[i])

    print("Bounds:", mins, maxs)


def query_vol(img, histoFlag=False):
    """ Query volume information """
    print()
    print("File:      ", sys.argv[1])
    print("Pixel type:", img.GetPixelIDTypeAsString())
    print("Size:      ", img.GetSize())
    print("Spacing:   ", img.GetSpacing())
    print("Origin:    ", img.GetOrigin())
    print("Direction: ", img.GetDirection())
    print()
    stats = sitk.StatisticsImageFilter()
    stats.Execute(img)
    print("Range:", stats.GetMinimum(), stats.GetMaximum())
    print()
    compute_bounds(img)

    if histoFlag:
        histo.histo(img)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ", sys.argv[0], " <input>")
    img = sitk.ReadImage(sys.argv[1])

    query_vol(img, True)
