#! /usr/bin/env python


import sys
import SimpleITK as sitk


def bound_obj(img, threshold=1.0):
    img2 = img >= threshold
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


if __name__ == "__main__":

    img_name = sys.argv[1]
    threshold = 1.0
    if len(sys.argv) > 2:
        threshold = float(sys.argv[2])

    img = sitk.ReadImage(img_name)
    bound_obj(img, threshold)
