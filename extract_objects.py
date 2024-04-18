#! /usr/bin/env python

import sys
import SimpleITK as sitk


def extract_objects(input_mask, output_name="mask", n=1, kernel_radius=5):
    """Given an mask image, seperate out the N largest objects.
    The function returns a list of mask images for these extracted
    objects."""

    objs = sitk.ConnectedComponent(input_mask)
    shape = sitk.LabelShapeStatisticsImageFilter()
    shape.Execute(objs)
    counts = {}

    for i in range(1, shape.GetNumberOfLabels() + 1):
        counts[i] = shape.GetNumberOfPixels(i)

    # Sort the objects by number of pixels in each object
    sorted_counts = {
        k: v for k, v in sorted(counts.items(), key=lambda item: item[1], reverse=True)
    }

    # Extract the n largest objects
    ids = list(sorted_counts)
    for i in range(n):

        obj_id = ids[i]
        count = sorted_counts[obj_id]
        print(obj_id, count)

        # select out the object's voxels
        obj_vol = objs == obj_id

        # clean up the volume
        obj_vol = sitk.BinaryFillhole(obj_vol)
        obj_vol = sitk.BinaryClosingByReconstruction(
            obj_vol, [kernel_radius, kernel_radius, kernel_radius]
        )

        obj_name = f"{output_name}_{i:02d}.nii.gz"
        print("Writing", obj_name)
        sitk.WriteImage(obj_vol, obj_name)


if __name__ == "__main__":

    mask_name = sys.argv[1]

    output_name = "mask"
    if len(sys.argv) > 2:
        output_name = sys.argv[2]

    mask = sitk.ReadImage(mask_name)
    extract_objects(mask, output_name, 1)
