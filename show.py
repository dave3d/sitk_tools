#! /usr/bin/env python


"""  A simple script that uses SimpleITK's Show function to display images
  in Fiji/ImageJ, by default. """

import argparse
import SimpleITK as sitk

parser = argparse.ArgumentParser()
parser.add_argument("filenames", nargs="*")
parser.add_argument(
    "--scale",
    "-s",
    action="store",
    dest="scale",
    type=float,
    default=1.0,
    help="Scale intensity",
)

args = parser.parse_args()
print(args)

for x in args.filenames:
    print(x)
    img = sitk.ReadImage(x)
    if img.GetNumberOfComponentsPerPixel() == 1:
        img = img * args.scale
    sitk.Show(img, x)
