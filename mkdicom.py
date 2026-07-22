#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "SimpleITK",
# ]
# ///

"""
mkdicom.py — Convert a 3D image to a DICOM slice series.

Each Z slice of the input volume is written as an individual DICOM file
(slice_000.dcm, slice_001.dcm, …) in the current directory.  The slices
share a common Series Instance UID so they are recognised as one series
by DICOM viewers and tools such as SimpleITK's GetGDCMSeriesIDs().

Usage
-----
    python mkdicom.py [input_image]

The input can be any format that SimpleITK supports (NRRD, NIfTI, MHD, …).
Defaults to teapot.nrrd when no argument is given.
"""

import argparse
import time
import uuid
import SimpleITK as sitk


def main():  # pylint: disable=too-many-locals
    """Parse arguments and convert the input volume to a DICOM slice series."""
    parser = argparse.ArgumentParser(
        description="Convert a 3D image to a DICOM slice series."
    )
    parser.add_argument("input", nargs="?", default="teapot.nrrd",
                        help="Input image file (default: teapot.nrrd)")
    args = parser.parse_args()

    volume = sitk.ReadImage(args.input)

    # Compute window center/width from the volume's intensity range.
    stats = sitk.StatisticsImageFilter()
    stats.Execute(volume)
    window_width = max(1.0, stats.GetMaximum() - stats.GetMinimum())
    window_center = stats.GetMinimum() + window_width / 2.0

    # Slice thickness from the volume's Z spacing.
    z_spacing = volume.GetSpacing()[2]

    # Image Orientation Patient: row cosines (i-axis) then column cosines (j-axis),
    # extracted from the volume's direction matrix (stored row-major in SimpleITK).
    d = volume.GetDirection()
    iop = "\\".join(f"{v:.6f}" for v in [d[0], d[3], d[6], d[1], d[4], d[7]])

    # Generate globally unique UIDs (DICOM root 2.25 is for UUID-derived UIDs).
    study_instance_uid  = "2.25." + str(uuid.uuid4().int)
    series_instance_uid = "2.25." + str(uuid.uuid4().int)

    study_date = time.strftime("%Y%m%d")
    study_time = time.strftime("%H%M%S")

    for z in range(volume.GetDepth()):
        # Extract a single 2-D slice; SimpleITK returns a 2-D image.
        slc = volume[:, :, z]

        # SOP Class UID — CT Image Storage.
        slc.SetMetaData("0008|0016", "1.2.840.10008.5.1.4.1.1.2")
        # SOP Instance UID — must be unique per slice.
        slc.SetMetaData("0008|0018", f"{series_instance_uid}.{z + 1:04d}")
        # Image Type — mark as derived/secondary (not original acquisition data).
        slc.SetMetaData("0008|0008", "DERIVED\\SECONDARY")

        # Study Date / Time
        slc.SetMetaData("0008|0020", study_date)
        slc.SetMetaData("0008|0030", study_time)
        # Instance Creation Date / Time
        slc.SetMetaData("0008|0012", study_date)
        slc.SetMetaData("0008|0013", study_time)

        # Modality — CT preserves slice location and thickness in most viewers.
        slc.SetMetaData("0008|0060", "CT")
        # Series Description — human-readable label shown in viewers.
        slc.SetMetaData("0008|103e", args.input.rsplit("/", 1)[-1].rsplit("\\", 1)[-1])

        # Study Instance UID — groups all series for one patient/session.
        slc.SetMetaData("0020|000d", study_instance_uid)
        # Series Instance UID — shared across all slices so they form one series.
        slc.SetMetaData("0020|000e", series_instance_uid)
        # Series Number
        slc.SetMetaData("0020|0011", "1")
        # Instance Number — 1-based slice index within the series.
        slc.SetMetaData("0020|0013", str(z + 1))

        # Image Position Patient — physical coordinates of the top-left voxel,
        # computed from the volume's origin, spacing, and direction cosines.
        slc.SetMetaData(
            "0020|0032",
            "\\".join(map(str, volume.TransformIndexToPhysicalPoint((0, 0, z)))),
        )
        # Image Orientation Patient — row and column direction cosines.
        slc.SetMetaData("0020|0037", iop)

        # Slice Thickness — Z voxel spacing of the original volume.
        slc.SetMetaData("0018|0050", str(z_spacing))

        # Window Center / Width — default display window from intensity range.
        slc.SetMetaData("0028|1050", str(window_center))
        slc.SetMetaData("0028|1051", str(window_width))

        filename = f"slice_{z:03d}.dcm"
        writer = sitk.ImageFileWriter()
        writer.KeepOriginalImageUIDOn()
        writer.SetFileName(filename)
        writer.Execute(slc)
        print(f"Written: {filename}")


if __name__ == "__main__":
    main()
