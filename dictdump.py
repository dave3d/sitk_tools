#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "SimpleITK",
# ]
# ///

"""  Simple script to dump out an image's meta-data dictionary """

import sys
import SimpleITK as sitk


fnames = sys.argv[1:]


for f in fnames:
    try:
        img = sitk.ReadImage(f)
    except RuntimeError:
        print("Error: unable to read", f)
        continue
    print("\nFile: ", f)

    keys = img.GetMetaDataKeys()

    for k in keys:
        v = img.GetMetaData(k)
        print(k, ": ", v)
