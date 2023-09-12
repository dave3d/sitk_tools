#! /usr/bin/env python


#  A test script that I wrote to exercise SimpleITK a bit
#

import SimpleITK as sitk

print (sitk)

print (sitk.Version())

gauss = sitk.GaussianSource( sitk.sitkFloat32, [128,128,128], [32., 32., 32.], [64., 64., 64.] )


deriv = sitk.Derivative(gauss)

result = sitk.RescaleIntensity(deriv, 0., 255.)

result = sitk.Cast(result, sitk.sitkUInt8)

cutslice = result[:,:,64]


sitk.Show(cutslice)
