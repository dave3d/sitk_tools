#! /usr/bin/env python

import sys
import argparse
import SimpleITK as sitk


def extract_objects(
    input_mask, output_name="mask", n=1, compactness=1.0, kernel_radius=5
):
    """Given an mask image, seperate out the N largest objects.
    The function returns a list of mask images for these extracted
    objects."""

    objs = sitk.ConnectedComponent(input_mask)
    shape = sitk.LabelShapeStatisticsImageFilter()
    shape.Execute(objs)
    counts = {}

    xdim = input_mask.GetWidth()
    ydim = input_mask.GetHeight()

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

        bounds = shape.GetBoundingBox(obj_id)
        print("\nBounds:", bounds)
        xc = bounds[3] / xdim
        yc = bounds[4] / ydim
        print("Compactness:", xc, yc)
        if xc > compactness or yc > compactness:
            print("Skipping object")
            continue

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


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("filenames", nargs="*")

    parser.add_argument(
        "--num",
        "-n",
        action="store",
        dest="n",
        type=int,
        default=1,
        help="number of largest objects to extract",
    )

    parser.add_argument(
        "--compact",
        "-c",
        action="store",
        dest="compact",
        type=float,
        default=1.0,
        help="compactness factor",
    )

    parser.add_argument(
        "--output",
        "-o",
        action="store",
        dest="output",
        default="",
        help="output name",
    )

    parser.add_argument(
        "--radius",
        "-r",
        action="store",
        dest="radius",
        type=int,
        default=5,
        help="radius for binary fill hole filter",
    )

    args = parser.parse_args()
    return args


if __name__ == "__main__":

    args = parse_args()

    mask_name = args.filenames[0]

    if len(args.output) > 0:
        output_name = args.output
    else:
        words = mask_name.split(".")
        output_name = words[0] + ".obj"

    mask = sitk.ReadImage(mask_name)

    extract_objects(mask, output_name, args.n, args.compact, args.radius)
