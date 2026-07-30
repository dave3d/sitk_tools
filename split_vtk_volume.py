#! /usr/bin/env python
# /// script
# dependencies = [
#   "vtk",
# ]
# ///

"""Split a 3D image into a grid of .vti pieces and a matching .pvti master."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import xml.etree.ElementTree as ET

import vtk


@dataclass(frozen=True)
class ImageGeometry:
    """Metadata needed to describe the source image in a PVTI header."""

    global_extent: list[int]
    origin: list[float]
    spacing: list[float]
    point_data: object
    cell_data: object


def calculate_splits(min_val: int, max_val: int, num_splits: int) -> list[tuple[int, int]]:
    """Split an extent axis into contiguous inclusive intervals.

    VTK image extents are point-index extents, so the number of cells along an
    axis is max_val - min_val.
    """
    if num_splits <= 0:
        raise ValueError(f"num_splits must be positive, got {num_splits}")

    total_cells = max_val - min_val
    if total_cells <= 0:
        raise ValueError(
            f"Invalid extent axis [{min_val}, {max_val}]; expected max_val > min_val"
        )

    if num_splits > total_cells:
        raise ValueError(
            f"Cannot split {total_cells} cells into {num_splits} parts along one axis; "
            "each part must contain at least one cell."
        )

    base_size = total_cells // num_splits
    remainder = total_cells % num_splits

    intervals: list[tuple[int, int]] = []
    current_start = min_val

    for i in range(num_splits):
        current_size = base_size + (1 if i < remainder else 0)
        current_end = current_start + current_size
        intervals.append((current_start, current_end))
        current_start = current_end

    return intervals


def _xml_type_name(vtk_type_name: str) -> str:
    """Convert a VTK data-type string into the XML type name used by .pvti."""
    normalized = vtk_type_name.strip().lower()
    mapping = {
        "bit": "Bit",
        "unsigned char": "UInt8",
        "signed char": "Int8",
        "char": "Int8",
        "unsigned short": "UInt16",
        "short": "Int16",
        "unsigned int": "UInt32",
        "int": "Int32",
        "unsigned long": "UInt64",
        "long": "Int64",
        "unsigned long long": "UInt64",
        "long long": "Int64",
        "float": "Float32",
        "double": "Float64",
        "id type": "Int64",
        "vtk id type": "Int64",
    }
    return mapping.get(normalized, vtk_type_name)


def _array_metadata(array) -> dict[str, str]:
    """Return XML-friendly metadata for a VTK data array."""
    name = array.GetName() if array.GetName() else "Array"
    type_name = _xml_type_name(array.GetDataTypeAsString())
    metadata = {"type": type_name, "Name": name}
    if array.GetNumberOfComponents() > 1:
        metadata["NumberOfComponents"] = str(array.GetNumberOfComponents())
    return metadata


def _build_data_section(parent, data_obj, section_tag: str) -> None:
    """Populate a PPointData/PCellData section with array descriptors."""
    section = ET.SubElement(parent, section_tag)
    arrays = data_obj.GetNumberOfArrays()
    for idx in range(arrays):
        array = data_obj.GetArray(idx)
        if array is None:
            continue
        ET.SubElement(section, "PDataArray", _array_metadata(array))


def write_pvti_header(
    pvti_filename: str,
    geometry: ImageGeometry,
    piece_extents: list[list[int]],
    base_name: str,
) -> None:
    """Create the master .pvti file that references each .vti piece."""
    root = ET.Element(
        "VTKFile",
        {
            "type": "PImageData",
            "version": "0.1",
            "byte_order": "LittleEndian",
            "header_type": "UInt64",
        },
    )

    p_image = ET.SubElement(
        root,
        "PImageData",
        {
            "WholeExtent": " ".join(map(str, geometry.global_extent)),
            "Origin": " ".join(map(str, geometry.origin)),
            "Spacing": " ".join(map(str, geometry.spacing)),
            "GhostLevel": "0",
        },
    )

    _build_data_section(p_image, geometry.point_data, "PPointData")
    _build_data_section(p_image, geometry.cell_data, "PCellData")

    for i, extent in enumerate(piece_extents):
        ET.SubElement(
            p_image,
            "Piece",
            {
                "Extent": " ".join(map(str, extent)),
                "Source": f"{base_name}_{i}.vti",
            },
        )

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(pvti_filename, encoding="utf-8", xml_declaration=True)


def _validate_source_data(source_data, input_file: str) -> None:
    if source_data is None:
        raise RuntimeError(f"Failed to read input image: {input_file}")

    if source_data.GetDataDimension() != 3:
        raise ValueError("This script expects a 3D vtkImageData dataset.")

    extent = source_data.GetExtent()
    if extent[1] <= extent[0] or extent[3] <= extent[2] or extent[5] <= extent[4]:
        raise ValueError(f"Invalid image extent: {extent}")


def _set_reader_filename(reader, input_file: str) -> bool:
    """Set the input file path on a VTK reader, handling API differences."""
    set_file_name = getattr(reader, "SetFileName", None)
    if callable(set_file_name):
        set_file_name(input_file)
        return True

    set_file_names = getattr(reader, "SetFileNames", None)
    if callable(set_file_names):
        string_array = vtk.vtkStringArray()
        string_array.InsertNextValue(input_file)
        set_file_names(string_array)
        return True

    return False


def _build_image_reader(input_file: str):
    """Create a reader for any 3D image format supported by this VTK build."""
    if os.path.isdir(input_file):
        dicom_reader = getattr(vtk, "vtkDICOMImageReader", None)
        if dicom_reader is None:
            raise ValueError(
                "Input is a directory, but vtkDICOMImageReader is not available "
                "in this VTK build."
            )

        reader = dicom_reader()
        reader.SetDirectoryName(input_file)
        return reader

    factory = vtk.vtkImageReader2Factory()
    reader = factory.CreateImageReader2(input_file)
    if reader is not None:
        if not _set_reader_filename(reader, input_file):
            raise RuntimeError(
                f"Factory reader {reader.GetClassName()} does not support file input."
            )
        return reader

    # Fallback readers for formats not always exposed via vtkImageReader2Factory.
    fallback_reader_names = [
        "vtkXMLImageDataReader",
        "vtkMetaImageReader",
        "vtkNIFTIImageReader",
        "vtkNrrdReader",
        "vtkStructuredPointsReader",
    ]

    for reader_name in fallback_reader_names:
        reader_cls = getattr(vtk, reader_name, None)
        if reader_cls is None:
            continue

        candidate = reader_cls()
        if not _set_reader_filename(candidate, input_file):
            continue

        can_read_file = getattr(candidate, "CanReadFile", None)
        if callable(can_read_file) and can_read_file(input_file) == 0:
            continue

        return candidate

    raise ValueError(
        "Could not determine a VTK reader for input file. "
        "Use a 3D image format supported by your VTK build "
        "(for example: .vti, .mhd/.mha, .nii/.nii.gz, .nrrd, .vtk), "
        "or pass a directory containing a DICOM series."
    )


def _extract_geometry(source_data) -> ImageGeometry:
    """Collect source image geometry and data-array metadata handles."""
    return ImageGeometry(
        global_extent=list(source_data.GetExtent()),
        origin=list(source_data.GetOrigin()),
        spacing=list(source_data.GetSpacing()),
        point_data=source_data.GetPointData(),
        cell_data=source_data.GetCellData(),
    )


def _calculate_axis_intervals(
    global_extent: list[int], nx: int, ny: int, nz: int
) -> tuple[list[tuple[int, int]], list[tuple[int, int]], list[tuple[int, int]]]:
    """Return split intervals for each image axis."""
    min_x, max_x = global_extent[0], global_extent[1]
    min_y, max_y = global_extent[2], global_extent[3]
    min_z, max_z = global_extent[4], global_extent[5]
    return (
        calculate_splits(min_x, max_x, nx),
        calculate_splits(min_y, max_y, ny),
        calculate_splits(min_z, max_z, nz),
    )


def _piece_extent_grid(
    x_intervals: list[tuple[int, int]],
    y_intervals: list[tuple[int, int]],
    z_intervals: list[tuple[int, int]],
) -> list[list[int]]:
    """Build the list of extents for each output piece."""
    extents: list[list[int]] = []
    for z_start, z_end in z_intervals:
        for y_start, y_end in y_intervals:
            for x_start, x_end in x_intervals:
                extents.append([x_start, x_end, y_start, y_end, z_start, z_end])
    return extents


def _write_piece(source_data, extent: list[int], piece_filename: Path) -> None:
    """Extract and write a single VTI sub-volume for the given extent."""
    extract = vtk.vtkExtractVOI()
    extract.SetInputData(source_data)
    extract.SetVOI(extent)
    extract.Update()

    change_info = vtk.vtkImageChangeInformation()
    change_info.SetInputConnection(extract.GetOutputPort())
    change_info.SetOutputExtentStart(extent[0], extent[2], extent[4])
    change_info.Update()

    vti_writer = vtk.vtkXMLImageDataWriter()
    vti_writer.SetFileName(str(piece_filename))
    vti_writer.SetInputConnection(change_info.GetOutputPort())
    if vti_writer.Write() != 1:
        raise RuntimeError(f"Failed to write piece file: {piece_filename}")


def _prepare_output(output_pvti: str) -> tuple[Path, str]:
    """Resolve output path, ensure directory exists, and derive piece basename."""
    output_path = Path(output_pvti).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path, output_path.stem


def _write_piece_grid(
    source_data,
    output_path: Path,
    base_name: str,
    piece_extents: list[list[int]],
) -> None:
    """Write all VTI piece files from precomputed extents."""
    for piece_id, extent in enumerate(piece_extents):
        piece_filename = output_path.with_name(f"{base_name}_{piece_id}.vti")
        _write_piece(source_data, extent, piece_filename)


def split_vti(input_file: str, output_pvti: str, nx: int, ny: int, nz: int) -> None:
    """Split a 3D image into a grid of sub-volumes and write a matching PVTI."""
    if nx <= 0 or ny <= 0 or nz <= 0:
        raise ValueError("nx, ny, and nz must all be positive integers.")

    reader = _build_image_reader(input_file)
    reader.Update()

    source_data = reader.GetOutput()
    _validate_source_data(source_data, input_file)

    geometry = _extract_geometry(source_data)
    x_intervals, y_intervals, z_intervals = _calculate_axis_intervals(
        geometry.global_extent, nx, ny, nz
    )
    piece_extents = _piece_extent_grid(x_intervals, y_intervals, z_intervals)

    total_pieces = nx * ny * nz
    print(f"Splitting grid into {nx}x{ny}x{nz} ({total_pieces} total pieces)...")
    print(f"Source global extent: {geometry.global_extent}")

    output_path, base_name = _prepare_output(output_pvti)
    _write_piece_grid(source_data, output_path, base_name, piece_extents)

    write_pvti_header(
        str(output_path),
        geometry,
        piece_extents,
        base_name,
    )
    print(f"Successfully generated master file: {output_path}")


def create_dummy_vti(filename: str) -> None:
    """Create a small sample 3D VTI file for testing."""
    img = vtk.vtkImageData()
    img.SetExtent(0, 30, 0, 30, 0, 30)
    img.SetOrigin(0, 0, 0)
    img.SetSpacing(1, 1, 1)

    elev = vtk.vtkElevationFilter()
    elev.SetInputData(img)
    elev.SetLowPoint(0, 0, 0)
    elev.SetHighPoint(30, 30, 30)
    elev.Update()

    writer = vtk.vtkXMLImageDataWriter()
    writer.SetFileName(filename)
    writer.SetInputConnection(elev.GetOutputPort())
    if writer.Write() != 1:
        raise RuntimeError(f"Failed to write dummy input file: {filename}")

    print(f"Created sample mock file: {filename}")


def main() -> None:
    """Parse CLI arguments and split the requested 3D volume."""
    parser = argparse.ArgumentParser(
        description="Subdivide a 3D VTK-readable image into an arbitrary parallel block grid."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default="sample_input_3d.vti",
        help="Path to input 3D image file, or a directory containing a DICOM series",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="split_output.pvti",
        help="Path to output master .pvti file",
    )
    parser.add_argument(
        "-nx",
        type=int,
        default=2,
        help="Number of grid subdivisions along the X axis",
    )
    parser.add_argument(
        "-ny",
        type=int,
        default=2,
        help="Number of grid subdivisions along the Y axis",
    )
    parser.add_argument(
        "-nz",
        type=int,
        default=2,
        help="Number of grid subdivisions along the Z axis",
    )

    args = parser.parse_args()

    if not os.path.exists(args.input):
        if args.input == "sample_input_3d.vti":
            create_dummy_vti(args.input)
        else:
            raise FileNotFoundError(f"Input file does not exist: {args.input}")

    split_vti(args.input, args.output, args.nx, args.ny, args.nz)


if __name__ == "__main__":
    main()
