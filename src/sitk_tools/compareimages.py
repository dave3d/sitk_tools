#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "SimpleITK",
# ]
# ///

""" Compare two images by computing the difference image and printing out the
stats of the difference image. """

import sys
import SimpleITK as sitk

# Given a list of images, print out the stats of each image, and then
# compare the first image with each of the others.


def printStats(img, name):
    """Print out the stats of the given image."""
    stats = sitk.StatisticsImageFilter()
    stats.Execute(img)
    print("\n", name)
    print("    Mean:", stats.GetMean())
    print("    Min:", stats.GetMinimum())
    print("    Max:", stats.GetMaximum())
    print("    Sigma:", stats.GetSigma())
    print("    Sum:", stats.GetSum())


# Compute a difference image between two images, and then print
# the stats of that difference image.
def compareImages(img1, name1, img2, name2):
    """Compute a difference image between two images, and then print
    the stats of that difference image."""
    print("\nComparing", name1, "and", name2)
    diff_img = img1 - img2
    printStats(diff_img, "diff")


def main(argv=None):
    """CLI entry point."""
    names = argv if argv is not None else sys.argv[1:]
    if len(names) < 2:
        print("Usage: sitk-compareimages <input_image1> <input_image2> [input_image3 ...]")
        return 1

    print(names)
    imgs = []

    # Print out the stats of each image
    for n in names:
        try:
            i = sitk.ReadImage(n)
        except RuntimeError:
            print("Error: unable to read", n)
            continue

        imgs.append(i)
        printStats(i, n)

    if len(imgs) < 2:
        print("Error: need at least two readable images")
        return 1

    print("\n")

    # Compare the first image with each of the rest
    for n, i in zip(names[1:], imgs[1:]):
        compareImages(imgs[0], names[0], i, n)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
