#! /usr/bin/env python

"""  Simple script to dump out an image's meta-data dictionary """

import sys
import SimpleITK as sitk


fnames = sys.argv[1:]


for f in fnames:
    img = sitk.ReadImage(f)

    print("\nFile: ", f)

    keys = img.GetMetaDataKeys()

    for k in keys:
        v = img.GetMetaData(k)
        print(k, ": ", v)
