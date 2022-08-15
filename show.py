#! /usr/bin/env python


#  A simple script that uses SimpleITK's Show function to display images
#  in Fiji/ImageJ, be default.
#
import sys
import SimpleITK as sitk

for x in sys.argv[1:]:
    print(x)
    img = sitk.ReadImage(x)
    sitk.Show(img, x)
