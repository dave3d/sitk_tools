#! /usr/bin/env python
# /// script
# dependencies = [
#   "vtk",
#   "numpy",
#   "SimpleITK",
#   "SimpleITKUtilities",
# ]
# ///

"""Convert between VTI and SimpleITK images using VTK and SimpleITK utilities."""

import sys
import vtk
import SimpleITK as sitk
from SimpleITK.utilities import vtk as sitk_vtk
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk


def vti_to_sitk(vti_path: str) -> sitk.Image:
    """Read a VTI image and convert it to a SimpleITK image."""
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(vti_path)
    reader.Update()

    image_data = reader.GetOutput()

    dims = image_data.GetDimensions()
    spacing = image_data.GetSpacing()
    origin = image_data.GetOrigin()
    direction = image_data.GetDirectionMatrix()

    point_data = image_data.GetPointData()
    vtk_array = point_data.GetScalars()
    if vtk_array is None and point_data.GetNumberOfArrays() > 0:
        vtk_array = point_data.GetArray(0)

    if vtk_array is None:
        raise ValueError("No point-data array found in the VTI file.")

    np_array = vtk_to_numpy(vtk_array)
    num_components = vtk_array.GetNumberOfComponents()

    if num_components == 1:
        np_array = np_array.reshape(dims[2], dims[1], dims[0])  # z, y, x
        sitk_image = sitk.GetImageFromArray(np_array)
    else:
        np_array = np_array.reshape(dims[2], dims[1], dims[0], num_components)
        sitk_image = sitk.GetImageFromArray(np_array, isVector=True)

    sitk_image.SetSpacing(spacing)
    sitk_image.SetOrigin(origin)
    sitk_image.SetDirection(
        (
            direction.GetElement(0, 0), direction.GetElement(0, 1), direction.GetElement(0, 2),
            direction.GetElement(1, 0), direction.GetElement(1, 1), direction.GetElement(1, 2),
            direction.GetElement(2, 0), direction.GetElement(2, 1), direction.GetElement(2, 2),
        )
    )

    return sitk_image


def sitk_to_vti(image: sitk.Image, vti_path: str, array_name: str = "ImageScalars") -> None:
    """Convert a SimpleITK image to VTI and write it to disk."""
    # Convert SimpleITK -> NumPy
    arr = sitk.GetArrayFromImage(image)

    # SimpleITK uses (z, y, x) for scalar images and (z, y, x, c) for vector images
    is_vector = image.GetNumberOfComponentsPerPixel() > 1

    vtk_array = numpy_to_vtk(
        num_array=arr.reshape(-1, arr.shape[-1] if is_vector else 1),
        deep=True,
    )

    if is_vector:
        vtk_array.SetNumberOfComponents(image.GetNumberOfComponentsPerPixel())
    else:
        vtk_array.SetNumberOfComponents(1)

    vtk_array.SetName(array_name)

    # Build vtkImageData
    vti = vtk.vtkImageData()
    vti.SetDimensions(image.GetSize())  # (x, y, z)
    vti.SetSpacing(image.GetSpacing())
    vti.SetOrigin(image.GetOrigin())

    # Direction matrix
    d = image.GetDirection()
    direction = vtk.vtkMatrix3x3()
    direction.DeepCopy(
        (
            d[0], d[1], d[2],
            d[3], d[4], d[5],
            d[6], d[7], d[8],
        )
    )
    vti.SetDirectionMatrix(direction)

    # VTK expects point data in a flat array
    vti.GetPointData().SetScalars(vtk_array)

    writer = vtk.vtkXMLImageDataWriter()
    writer.SetFileName(vti_path)
    writer.SetInputData(vti)
    if writer.Write() != 1:
        raise IOError(f"Failed to write VTI file: {vti_path}")


def read_vti_image(file_path: str) -> vtk.vtkImageData:
    """
    Read a VTI (VTK XML ImageData) file and return vtkImageData.

    Parameters
    ----------
    file_path : str
        Path to the .vti file.

    Returns
    -------
    vtk.vtkImageData
        The loaded image data.
    """
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(file_path)
    reader.Update()

    image = reader.GetOutput()
    if image is None or image.GetPointData() is None:
        raise RuntimeError(f"Failed to read VTI file: {file_path}")

    return image

def write_vti_image(image: vtk.vtkImageData, file_path: str) -> None:
    """
    Write a vtkImageData object to a VTI (VTK XML ImageData) file.

    Parameters
    ----------
    image : vtk.vtkImageData
        The image data to write.
    file_path : str
        Output path ending in .vti.
    """
    if image is None:
        raise ValueError("image must not be None")

    writer = vtk.vtkXMLImageDataWriter()
    writer.SetFileName(file_path)
    writer.SetInputData(image)

    # Optional: use binary or ASCII
    writer.SetDataModeToBinary()

    if writer.Write() != 1:
        raise RuntimeError(f"Failed to write VTI file: {file_path}")


# Example usage
def main(argv=None):
    """CLI entry point."""
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 2:
        print("Usage: sitk-vti-sitk <input_image> <output_image>")
        return 1

    inname = args[0]
    outname = args[1]

    if inname.endswith("vti"):
        print("Reading VTI image", inname)
        vti_img = read_vti_image(inname)
        sitk_img = sitk_vtk.vtk2sitk(vti_img)
        print("Writing SimpleITK image", outname)
        sitk.WriteImage(sitk_img, outname)
    else:
        print("Reading SimpleITK image", inname)
        sitk_img = sitk.ReadImage(inname)
        print("Writing VTI image", outname)
        vti_img = sitk_vtk.sitk2vtk(sitk_img)
        write_vti_image(vti_img, outname)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
