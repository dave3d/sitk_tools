#! /usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "vtk",
# ]
# ///

""" nifti2vti.py: Convert one or more NIfTI 3D images to compressed VTI files """

import sys
import pathlib
import vtk


def derive_output_path(input_path: str) -> str:
    """Return the output .vti path derived from a NIfTI input path."""
    p = pathlib.Path(input_path)
    # Strip .nii or .nii.gz suffix
    if p.suffix == ".gz":
        p = p.with_suffix("")
    if p.suffix == ".nii":
        p = p.with_suffix("")
    return str(p) + ".vti"


def nifti_to_vti(input_path: str, output_path: str) -> None:
    """Read a NIfTI file and write it as a compressed VTK XML image (.vti)."""
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(input_path)
    reader.Update()

    writer = vtk.vtkXMLImageDataWriter()
    writer.SetFileName(output_path)
    writer.SetInputConnection(reader.GetOutputPort())
    writer.SetCompressorTypeToZLib()
    writer.SetDataModeToBinary()
    writer.Write()

    print(f"Written: {output_path}")


def main(argv=None):
    """CLI entry point."""
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 1:
        print("Usage: sitk-nifti2vti <input1.nii[.gz]> [input2.nii[.gz] ...]")
        return 1

    for src in args:
        nifti_to_vti(src, derive_output_path(src))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
