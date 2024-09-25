#! /usr/bin/env python

""" Script to extract subimages from a color image.
We assume the background is black. """


import re
import argparse
from pathlib import Path
from string import digits
import SimpleITK as sitk


def extract_subimages(img, root_name, file_num, min_size=20000):
    """Extract sub-images from an image."""

    print(f"\nExtracting subimages from {root_name}")

    if img.GetNumberOfComponentsPerPixel() == 3:
        # max of RGB channels
        max_img = sitk.Maximum(
            sitk.VectorIndexSelectionCast(img, 0), sitk.VectorIndexSelectionCast(img, 1)
        )
        max_img = sitk.Maximum(max_img, sitk.VectorIndexSelectionCast(img, 2))
    else:
        max_img = img

    mask = max_img > 50
    cc = sitk.ConnectedComponent(mask)

    stats = sitk.LabelShapeStatisticsImageFilter()
    stats.Execute(cc)

    count = file_num

    for l in stats.GetLabels():
        n = stats.GetNumberOfPixels(l)
        if n > min_size:
            print(f"\nBlock {l} has size {n}")
            bbox = stats.GetBoundingBox(l)
            print(bbox)

            sub_img = img[bbox[0] : bbox[0] + bbox[2], bbox[1] : bbox[1] + bbox[3]]
            new_name = root_name + f"{count}.jpeg"
            sitk.WriteImage(sub_img, new_name)
            print(new_name)
            count = count + 1


def parse_args():
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description="Extract subimages from an image.")
    parser.add_argument("filenames", help="Input images", nargs="+")
    parser.add_argument(
        "--min_size", type=int, default=20000, help="Minimum size of subimage"
    )
    parser.add_argument("--output_dir", default="", help="Output directory")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    print(args)

    for filename in args.filenames:
        print(f"\nProcessing {filename}")
        path = Path(filename)
        if len(args.output_dir) == 0:
            args.output_dir = str(path.parent)
        name = path.stem.rstrip(digits)
        print(path.stem)

        try:
            num = int(re.search(r"\d+$", path.stem).group()) + 1
        except AttributeError:
            num = 1

        print(name, num)

        input_image = sitk.ReadImage(filename)
        extract_subimages(input_image, args.output_dir + "/" + name, num)
