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
    p = pathlib.Path(input_path)
    # Strip .nii or .nii.gz suffix
    if p.suffix == ".gz":
        p = p.with_suffix("")
    if p.suffix == ".nii":
        p = p.with_suffix("")
    return str(p) + ".vti"


def nifti_to_vti(input_path: str, output_path: str) -> None:
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input.nii[.gz]> [input2.nii[.gz] ...]")
        sys.exit(1)

    for input_path in sys.argv[1:]:
        nifti_to_vti(input_path, derive_output_path(input_path))
