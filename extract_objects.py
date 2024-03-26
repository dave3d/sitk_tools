#! /usr/bin/env python

import sys
import SimpleITK as sitk


def extract_objects(input_mask, n=1):
    """Given an mask image, seperate out the N largest objects.
    The function returns a list of mask images for these extracted
    objects."""

    objs = sitk.ConnectedComponent(input_mask)
    shape = sitk.LabelShapeStatisticsImageFilter()
    shape.Execute(objs)
    counts = {}

    max_count = 0
    max_id = 0
    for i in range(1, shape.GetNumberOfLabels() + 1):
        counts[i] = shape.GetNumberOfPixels(i)
        if counts[i] > max_count:
            max_count = counts[i]
            max_id = i

    sorted_counts = {
        k: v for k, v in sorted(counts.items(), key=lambda item: item[1], reverse=True)
    }

    ids = list(sorted_counts)
    for i in range(n):

        obj_id = ids[i]
        count = sorted_counts[obj_id]
        print(obj_id, count)

        obj_vol = objs == obj_id
        obj_name = f"mask_{i:02d}.nii.gz"
        print("Writing", obj_name)
        sitk.WriteImage(obj_vol, obj_name)


if __name__ == "__main__":
    mask_name = sys.argv[1]
    mask = sitk.ReadImage(mask_name)
    extract_objects(mask, 1)
