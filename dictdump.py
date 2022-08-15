#! /usr/bin/env python

import SimpleITK as sitk

import sys

fnames = sys.argv[1:]


for f in fnames:
    img = sitk.ReadImage(f)

    print("\nFile: ", f)

    keys = img.GetMetaDataKeys()

    for k in keys:
        v = img.GetMetaData(k)
        print(k, ": ", v)
