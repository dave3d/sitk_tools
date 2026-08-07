#! /usr/bin/env python
# /// script
# dependencies = [
#   "vtk",
# ]
# ///

"""Split a VTI file into piece VTI files plus a PVTI manifest."""

# Legacy script retained mostly as-is; complexity and line length are acceptable here.
# pylint: disable=line-too-long,too-many-arguments,too-many-positional-arguments,too-many-locals

import argparse
import os
import vtk


def calculate_splits(min_val, max_val, num_splits):
    """Calculates boundary indices for an axis split into num_splits parts."""
    total_cells = max_val - min_val
    base_size = total_cells // num_splits
    remainder = total_cells % num_splits

    intervals = []
    current_start = min_val

    for i in range(num_splits):
        current_size = base_size + (1 if i < remainder else 0)
        current_end = current_start + current_size
        intervals.append((current_start, current_end))
        current_start = current_end

    return intervals


def write_pvti_header(pvti_filename, global_extent, origin, spacing, scalar_name, piece_extents, base_name):
    """Manually creates the master .pvti XML file linking all .vti pieces together."""
    ext_str = " ".join(map(str, global_extent))
    ori_str = " ".join(map(str, origin))
    spa_str = " ".join(map(str, spacing))

    with open(pvti_filename, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0"?>\n')
        f.write('<VTKFile type="PImageData" version="0.1" byte_order="LittleEndian" header_type="UInt64">\n')
        f.write(f'  <PImageData WholeExtent="{ext_str}" Origin="{ori_str}" Spacing="{spa_str}" GhostLevel="0">\n')
        f.write('    <PPointData>\n')
        f.write(f'      <PDataArray type="Float32" Name="{scalar_name}"/>\n')
        f.write('    </PPointData>\n')
        f.write('    <PCellData>\n')
        f.write('    </PCellData>\n')

        for i, extent in enumerate(piece_extents):
            p_ext_str = " ".join(map(str, extent))
            f.write(f'    <Piece Extent="{p_ext_str}" Source="{base_name}_{i}.vti"/>\n')

        f.write('  </PImageData>\n')
        f.write('</VTKFile>\n')


def split_vti(input_file, output_pvti, nx, ny, nz):
    """Split a VTI image into an nx by ny by nz grid and write PVTI metadata."""
    # 1. Read the source VTI file
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(input_file)
    reader.Update()

    source_data = reader.GetOutput()
    global_extent = list(source_data.GetExtent())
    origin = list(source_data.GetOrigin())
    spacing = list(source_data.GetSpacing())

    scalar_name = "Scalars"
    if source_data.GetPointData().GetScalars():
        scalar_name = source_data.GetPointData().GetScalars().GetName()

    print(f"Source Global Extent: {global_extent}")

    min_x, max_x = global_extent[0], global_extent[1]
    min_y, max_y = global_extent[2], global_extent[3]
    min_z, max_z = global_extent[4], global_extent[5]

    # 2. Calculate the grid sub-intervals for each axis
    x_intervals = calculate_splits(min_x, max_x, nx)
    y_intervals = calculate_splits(min_y, max_y, ny)
    z_intervals = calculate_splits(min_z, max_z, nz)

    total_pieces = nx * ny * nz
    print(f"Splitting grid into {nx}x{ny}x{nz} ({total_pieces} total pieces)...")

    # Base path configuration
    base_path, _ = os.path.splitext(output_pvti)
    base_name = os.path.basename(base_path)

    piece_extents = []
    piece_id = 0

    # 3. Extract and write each sub-volume preserving its real global indexing spatial location
    for k in range(nz):
        z_start, z_end = z_intervals[k]
        for j in range(ny):
            y_start, y_end = y_intervals[j]
            for i in range(nx):
                x_start, x_end = x_intervals[i]
                extent = [x_start, x_end, y_start, y_end, z_start, z_end]
                piece_extents.append(extent)

                # Use vtkExtractVOI to isolate the subset cleanly
                extract = vtk.vtkExtractVOI()
                extract.SetInputData(source_data)
                extract.SetVOI(extent)
                extract.Update()

                # CRITICAL FIX: Explicitly force the underlying image data block to map
                # its internal file extent fields to match the global extent coordinates.
                change_info = vtk.vtkImageChangeInformation()
                change_info.SetInputData(extract.GetOutput())
                change_info.SetOutputExtentStart(x_start, y_start, z_start)
                change_info.Update()

                vti_filename = f"{base_path}_{piece_id}.vti"
                vti_writer = vtk.vtkXMLImageDataWriter()
                vti_writer.SetFileName(vti_filename)
                vti_writer.SetInputData(change_info.GetOutput())
                vti_writer.Write()

                piece_id += 1

    # 4. Generate the master .pvti tracking file
    write_pvti_header(output_pvti, global_extent, origin, spacing, scalar_name, piece_extents, base_name)
    print(f"Successfully generated master file: {output_pvti}")


def create_dummy_vti(filename):
    """Creates a basic 3D grid file if none exists to test the script."""
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
    writer.SetInputData(elev.GetOutput())
    writer.Write()
    print(f"Created sample mock file: {filename}")


def main(argv=None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="sitk-split-vti",
        description="Subdivide a 3D VTI image into an arbitrary parallel block grid."
    )
    parser.add_argument(
        "-i", "--input", type=str, default="sample_input_3d.vti", help="Path to the input .vti file."
    )
    parser.add_argument(
        "-o", "--output", type=str, default="split_output.pvti", help="Path to the output master .pvti file."
    )
    parser.add_argument(
        "-nx", type=int, default=2, help="Number of grid subdivisions along the X axis."
    )
    parser.add_argument(
        "-ny", type=int, default=2, help="Number of grid subdivisions along the Y axis."
    )
    parser.add_argument(
        "-nz", type=int, default=2, help="Number of grid subdivisions along the Z axis."
    )

    args = parser.parse_args(argv)

    if not os.path.exists(args.input) and args.input == "sample_input_3d.vti":
        create_dummy_vti(args.input)

    split_vti(args.input, args.output, args.nx, args.ny, args.nz)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
