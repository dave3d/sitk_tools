#! /usr/bin/env python

"""  Script to read a mouse scan header file and produce MetaIO header file

  I think the scans are in a variant of Analyze or Nifti files.
  They have '.hdr' file and a '.img' file.  Unlike Analyze or Nifti,
  the header files are text.
"""

import sys
import SimpleITK as sitk


# Data type values(integer)
#   0 - Unknown data type
#   1 - Byte (8-bits) data type
#   2 - 2-byte integer - Intel style
#   3 - 4-byte integer - Intel style
#   4 - 4-byte float - Intel style
#   5 - 4-byte float - Sun style
#   6 - 2-byte integer - Sun style
#   7 - 4-byte integer - Sun style


def parseHdrFile(header_name):
    """Parse the header file and return a dictionary of fields"""
    with open(header_name, "rb") as f_in:
        lines = f_in.read().splitlines()

    fields = {}
    for line in lines:
        words = line.split(" ", maxsplit=1)
        if words[0] == "file_name":
            parts = words[1].split("\\")
            img_name = parts[-1]
            fields["file_name"] = img_name

        elif words[0] in (
            "data_type",
            "number_of_dimensions",
            "x_dimension",
            "y_dimension",
            "z_dimension",
        ):
            fields[words[0]] = int(words[1])

        elif words[0] in ("pixel_size_x", "pixel_size_y", "pixel_size_z"):
            fields[words[0]] = float(words[1])

        elif words[0] == "study_identifier":
            fields[words[0]] = words[1]

        elif words[0] == "image_ref_shift":
            xyz = words[1].split(" ")
            fields["shift"] = xyz

        elif words[0] == "image_ref_rotation":
            xyz = words[1].split(" ")
            fields["rotation"] = xyz

    return fields


def writeMhdFile(metaio_name, fields):
    """Write the MetaIO header file"""
    with open(metaio_name, "wb") as f_out:
        print("ObjectType = Image", file=f_out)
        print("NDims =", fields["number_of_dimensions"], file=f_out)
        print("BinaryData = True", file=f_out)
        print("BinaryDataByteOrderMSB =", fields["data_type"] > 4, file=f_out)
        print("CompressedData = False", file=f_out)

        tmat = [1, 0, 0, 0, 1, 0, 0, 0, 1]
        if "rotation" in fields:
            tform = sitk.Euler3DTransform()
            # convert degrees to radians
            rot = [0.017453292519943295 * float(ang) for ang in fields["rotation"]]
            tform.SetRotation(rot[0], rot[1], rot[2])
            tmat = tform.GetMatrix()

        tform_txt = ""
        for v in tmat:
            tform_txt = tform_txt + f" {v:.6g}"
        print(tform_txt)
        print("TransformMatrix =", tform_txt, file=f_out)

        shift = [0, 0, 0]
        if "shift" in fields:
            shift = fields["shift"]
        print("Offset =", shift[0], shift[1], shift[2], file=f_out)
        print("CenterOfRotation = 0 0 0", file=f_out)

        print(
            "ElementSpacing =",
            fields["pixel_size_x"],
            fields["pixel_size_y"],
            fields["pixel_size_z"],
            file=f_out,
        )
        print(
            "DimSize =",
            fields["x_dimension"],
            fields["y_dimension"],
            fields["z_dimension"],
            file=f_out,
        )

        dt = fields["data_type"]

        if dt == 1:
            print("ElementType = MET_UCHAR", file=f_out)
        elif dt in (2, 6):
            print("ElementType = MET_SHORT", file=f_out)
        elif dt in (3, 7):
            print("ElementType = MET_INT", file=f_out)
        elif dt in (4, 5):
            print("ElementType = MET_FLOAT", file=f_out)

        print("ElementDataFile =", fields["file_name"], file=f_out)


def usage():
    """Print the usage message"""
    print("hdr2vol.py input_file.hdr [output_file.mhd]")


if __name__ == "__main__":
    try:
        hdr_name = sys.argv[1]
    except IndexError:
        usage()
        sys.exit(1)

    try:
        mhd_name = sys.argv[2]
    except IndexError:
        if hdr_name.endswith(".hdr"):
            mhd_name = hdr_name.replace(".hdr", ".mhd")
        else:
            mhd_name = hdr_name + ".mhd"

    hdr_fields = parseHdrFile(hdr_name)
    print(hdr_fields)

    writeMhdFile(mhd_name, hdr_fields)
