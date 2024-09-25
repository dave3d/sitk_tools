#! /usr/bin/env python

""" Script to extract the N largest objects from a binary mask image. """
import argparse
import SimpleITK as sitk


def extract_object(obj_id, vol, kernel_radius, output_name):
    """Extract the object with the given ID from the volume and write it to a file."""
    obj_vol = vol == obj_id

    # clean up the volume
    obj_vol = sitk.BinaryFillhole(obj_vol)
    obj_vol = sitk.BinaryClosingByReconstruction(
        obj_vol, [kernel_radius, kernel_radius, kernel_radius]
    )

    print("Writing", output_name)
    sitk.WriteImage(obj_vol, output_name)


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

    dim2 = [input_mask.GetWidth(), input_mask.GetHeight()]

    for i in range(1, shape.GetNumberOfLabels() + 1):
        counts[i] = shape.GetNumberOfPixels(i)

    # Sort the objects by number of pixels in each object
    sorted_counts = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))

    # Extract the n largest objects
    ids = list(sorted_counts)
    for i in range(n):

        obj_id = ids[i]
        print(obj_id, sorted_counts[obj_id])

        # Check the compactness of the object
        bounds = shape.GetBoundingBox(obj_id)
        print("\nBounds:", bounds)
        comp = [bounds[3] / dim2[0], bounds[4] / dim2[1]]
        print("Compactness:", comp)
        if comp[0] > compactness or comp[1] > compactness:
            print("Skipping object")
            continue

        extract_object(obj_id, objs, kernel_radius, f"{output_name}_{i:02d}.nii.gz")


def parse_args():
    """Parse command line arguments."""
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

    return parser.parse_args()


if __name__ == "__main__":

    args = parse_args()

    mask_name = args.filenames[0]

    if len(args.output) > 0:
        out_name = args.output
    else:
        words = mask_name.split(".")
        out_name = words[0] + ".obj"

    mask = sitk.ReadImage(mask_name)

    extract_objects(mask, out_name, args.n, args.compact, args.radius)
