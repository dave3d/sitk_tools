#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "SimpleITK",
#   "numpy",
# ]
# ///

"""
Extract a radial series of 2-D reformatted images from a 3-D volume.

Cutting planes rotate around the physical Z axis through the image centre.
Angles run from 0° up to (but not including) 180°; the opposite half of the
circle produces identical planes, so only a half-rotation is needed.

Usage
-----
    radial_slices.py [options] input_volume output_dir

Options
-------
    -n, --nslices INT     Number of evenly-spaced angles to extract (default: 36)
    -s, --spacing FLOAT   Output pixel spacing in mm (default: finest input spacing)
    -f, --format EXT      Output file extension, e.g. .nrrd .mhd .nii.gz (default: .nrrd)
    -w, --window          Rescale intensities to uint16 before writing (needed for PNG/TIFF)
    -v, --verbose         Print progress
    -h, --help            Show this help
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import SimpleITK as sitk


def physical_corners(img: sitk.Image) -> np.ndarray:
    """Return the 8 physical-space corner coordinates of a 3-D image."""
    sz = img.GetSize()
    return np.array([
        img.TransformIndexToPhysicalPoint([i, j, k])
        for i in (0, sz[0] - 1)
        for j in (0, sz[1] - 1)
        for k in (0, sz[2] - 1)
    ])


# pylint: disable=too-many-locals
def extract_radial_slice(
    img: sitk.Image,
    angle_rad: float,
    out_spacing: float,
) -> sitk.Image:
    """
    Extract a 2-D reformat of *img* on the vertical plane that passes through
    the image centre at *angle_rad* rotation around the Z axis.

    The output is a 3-D slab of size (nu, nv, 1) with the correct 3-D origin,
    direction cosines, and spacing, so it can be placed accurately in world space.
    The image axes are:
      - axis 0 (i): radial direction (cos θ, sin θ, 0)
      - axis 1 (j): axial direction  (0, 0, 1)
      - axis 2 (k): plane normal     (-sin θ, cos θ, 0)  — 1 voxel thick

    Parameters
    ----------
    img         : 3-D input SimpleITK image
    angle_rad   : rotation angle around Z in radians (0 = XZ plane)
    out_spacing : pixel spacing for both output axes in mm

    Returns
    -------
    3-D SimpleITK image of size (nu, nv, 1) with full world-space metadata
    """
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    # Orthonormal basis for the cutting plane and its normal.
    u = np.array([ cos_a, sin_a, 0.0])  # radial  (horizontal in output)
    v = np.array([ 0.0,   0.0,   1.0])  # axial   (vertical in output)
    n = np.array([ sin_a,-cos_a, 0.0])  # normal = u × v (right-handed, required for DICOM)

    # Physical centre of the volume.
    sz = img.GetSize()
    centre = np.array(
        img.TransformContinuousIndexToPhysicalPoint([(s - 1) / 2.0 for s in sz])
    )

    # Project all 8 bounding-box corners onto u and v to find the full extent.
    corners = physical_corners(img)
    u_coords = corners @ u
    v_coords = corners @ v
    u_min, u_max = float(u_coords.min()), float(u_coords.max())
    v_min, v_max = float(v_coords.min()), float(v_coords.max())

    # Output grid size.
    nu = max(1, round((u_max - u_min) / out_spacing) + 1)
    nv = max(1, round((v_max - v_min) / out_spacing) + 1)

    # Physical origin of the output slab:
    #   – radially at the minimum u projection of the bounding box
    #   – axially  at the minimum v projection
    #   – along the normal: pinned to the centre of the volume so the
    #     plane passes through the image centre.
    n_coord = float(centre @ n)
    origin = (u_min * u + v_min * v + n_coord * n).tolist()

    # Direction matrix stored row-major in SimpleITK: column i gives the
    # physical direction of image axis i.
    direction = (
        u[0], v[0], n[0],
        u[1], v[1], n[1],
        u[2], v[2], n[2],
    )

    # Resample the 3-D volume onto a 1-voxel-thick slab aligned with the plane.
    # The slab retains its full 3-D origin, direction cosines, and spacing so
    # that viewers (3D Slicer, ITK-SNAP, …) can place it correctly in world space.
    return sitk.Resample(
        img,
        [nu, nv, 1],
        sitk.Transform(),
        sitk.sitkLinear,
        origin,
        [out_spacing, out_spacing, 1.0],
        direction,
        0.0,
        img.GetPixelID(),
    )


# pylint: enable=too-many-locals


def rescale_to_uint16(img: sitk.Image) -> sitk.Image:
    """Linearly rescale intensities to [0, 65535] and cast to uint16."""
    img_f = sitk.Cast(img, sitk.sitkFloat32)
    stats = sitk.StatisticsImageFilter()
    stats.Execute(img_f)
    mn, mx = stats.GetMinimum(), stats.GetMaximum()
    if mx > mn:
        img_f = (img_f - mn) * (65535.0 / (mx - mn))
    return sitk.Cast(img_f, sitk.sitkUInt16)


def main(argv=None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="sitk-radial-slices",
        description="Extract a radial series of 2-D reformats from a 3-D volume.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", help="Input 3-D image file.")
    parser.add_argument("output_dir", help="Directory to write 2-D slices into.")
    parser.add_argument("-n", "--nslices", type=int, default=36, metavar="N",
                        help="Number of angles to extract (default: 36).")
    parser.add_argument("-s", "--spacing", type=float, default=None, metavar="MM",
                        help="Output pixel spacing in mm (default: finest input spacing).")
    parser.add_argument("-f", "--format", default=".nrrd", dest="fmt", metavar="EXT",
                        help="Output file extension (default: .nrrd). Use a 3-D format "
                             "(.nrrd, .mhd, .nii.gz) to preserve spatial metadata.")
    parser.add_argument("-w", "--window", action="store_true",
                        help="Rescale intensities to uint16 before writing.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Print progress information.")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.nslices < 1:
        print("Error: --nslices must be >= 1.")
        return 1

    fmt = args.fmt if args.fmt.startswith(".") else "." + args.fmt
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.verbose:
        print(f"Loading {args.input} …")
    img = sitk.ReadImage(args.input)
    if img.GetDimension() != 3:
        print("Error: input must be a 3-D image.")
        return 1

    out_spacing = args.spacing if args.spacing is not None else min(img.GetSpacing())

    if args.verbose:
        print(f"Input size:    {img.GetSize()}")
        print(f"Input spacing: {img.GetSpacing()} mm")
        print(f"Output spacing: {out_spacing} mm,  {args.nslices} slices")

    for idx in range(args.nslices):
        angle_rad = math.pi * idx / args.nslices
        deg = math.degrees(angle_rad)

        if args.verbose:
            print(f"  [{idx + 1:3d}/{args.nslices}]  {deg:7.3f}°")

        sl = extract_radial_slice(img, angle_rad, out_spacing)

        if args.window:
            sl = rescale_to_uint16(sl)

        out_path = str(out_dir / f"radial_{deg:07.3f}deg{fmt}")
        sitk.WriteImage(sl, out_path)

    if args.verbose:
        print(f"Done. Wrote {args.nslices} slices to {out_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
