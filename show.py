#! /usr/bin/env python

import sys
import SimpleITK as sitk

for x in sys.argv[1:]:
  print(x)
  img = sitk.ReadImage(x)
  sitk.Show(img)
