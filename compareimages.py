#! /usr/bin/env python

import sys
import SimpleITK as sitk

# Given a list of images, print out the stats of each image, and then
# compare the first image with each of the others.

def printStats(img, name):
    stats = sitk.StatisticsImageFilter()
    stats.Execute(img)
    print ("\n", name)
    print("    Mean:", stats.GetMean())
    print("    Min:", stats.GetMinimum())
    print("    Max:", stats.GetMaximum())
    print("    Sigma:", stats.GetSigma())
    print("    Sum:", stats.GetSum())


# Compute a difference image between two images, and then print
# the stats of that difference image.
def compareImages(img1, name1, img2, name2):
    print("\nComparing", name1, "and", name2)
    diff_img = img1-img2
    printStats(diff_img, "diff")

names = sys.argv[1:]
print(names)
imgs = []


# Print out the stats of each image
for n in names:
    img = sitk.ReadImage(n)
    imgs.append(img)
    #print(img)

    printStats(img, n)

print("\n")

# Compare the first image with each of the rest
for n, i in zip(names[1:], imgs[1:]):
    compareImages(imgs[0], names[0], i, n)
