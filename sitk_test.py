#! /usr/bin/env python


#  A test script that I wrote to exercise SimpleITK a bit
#

import platform
import SimpleITK as sitk

print(platform.python_version())
print(platform.platform())
print(sitk)
print(sitk.Version())

gauss = sitk.GaussianSource(
    sitk.sitkFloat32, [128, 128, 128], [32.0, 32.0, 32.0], [64.0, 64.0, 64.0]
)

deriv = sitk.Derivative(gauss)

result = sitk.RescaleIntensity(deriv, 0.0, 255.0)

result = sitk.Cast(result, sitk.sitkUInt8)

cutslice = result[:, :, 64]

sitk.Show(
    cutslice,
    "python "
    + platform.python_version()
    + "; SimpleITK "
    + sitk.Version_VersionString(),
)
