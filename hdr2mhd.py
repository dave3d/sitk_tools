#! /usr/bin/env python

import sys

#  Script to read a mouse scan header file and produce MetaIO header file
#
#  I think the scans are in a variant of Analyze or Nifti files.
#  They have '.hdr' file and a '.img' file.  Unlike Analyze or Nifti,
#  the header files are text.


def parseHdrFile(hdr_name):

    with open(hdr_name) as f_in:
        lines = f_in.read().splitlines()

    fields = {}
    for line in lines:
        words = line.split(' ', maxsplit=1)
        if words[0] == "file_name":
            parts = words[1].split('\\')
            img_name = parts[-1]
            fields['file_name'] = img_name

        elif words[0] == 'data_type':
            # Data type (integer)
            #   0 - Unknown data type
            #   1 - Byte (8-bits) data type
            #   2 - 2-byte integer - Intel style
            #   3 - 4-byte integer - Intel style
            #   4 - 4-byte float - Intel style
            #   5 - 4-byte float - Sun style
            #   6 - 2-byte integer - Sun style
            #   7 - 4-byte integer - Sun style

            data_type = int(words[1])
            fields['data_type'] = data_type

        elif words[0] == 'number_of_dimensions':
            fields['number_of_dimensions'] = int(words[1])
        elif words[0] == 'x_dimension':
            fields[words[0]] = int(words[1])
        elif words[0] == 'y_dimension':
            fields[words[0]] = int(words[1])
        elif words[0] == 'z_dimension':
            fields[words[0]] = int(words[1])

        elif words[0] == 'pixel_size_x':
            fields[words[0]] = float(words[1])
        elif words[0] == 'pixel_size_y':
            fields[words[0]] = float(words[1])
        elif words[0] == 'pixel_size_z':
            fields[words[0]] = float(words[1])

        elif words[0] == 'study_identifier':
            fields[words[0]] = words[1]

    return fields


def writeMhdFile(mhd_name, fields):
    with open(mhd_name, 'w') as f_out:

        print("ObjectType = Image", file=f_out)
        print("NDims =", fields['number_of_dimensions'], file=f_out)
        print("BinaryData = True", file=f_out)
        print("BinaryDataByteOrderMSB =", fields['data_type'] > 4, file=f_out)
        print("CompressedData = False", file=f_out)

        # To be fixed later
        print("TransformMatrix = 1 0 0 0 1 0 0 0 1", file=f_out)
        print("Offset = 0 0 0", file=f_out)
        print("CenterOfRotation = 0 0 0", file=f_out)

        print("ElementSpacing =", fields['pixel_size_x'],
              fields['pixel_size_y'], fields['pixel_size_z'], file=f_out)
        print("DimSize =", fields['x_dimension'], fields['y_dimension'],
              fields['z_dimension'], file=f_out)

        dt = fields['data_type']

        if dt == 1:
            print("ElementType = MET_UCHAR", file=f_out)
        elif (dt == 2) or (dt == 6):
            print("ElementType = MET_SHORT", file=f_out)
        elif (dt == 3) or (dt == 7):
            print("ElementType = MET_INT", file=f_out)
        elif (dt == 4) or (dt == 5):
            print("ElementType = MET_FLOAT", file=f_out)

        print("ElementDataFile =", fields['file_name'], file=f_out)


def usage():
    print("hdr2vol.py input_file.hdr [output_file.mhd]")

if __name__ == "__main__":

    try:
        hdr_name = sys.argv[1]
    except BaseException:
        usage()
        sys.exit(1)

    try:
        mhd_name = sys.argv[2]
    except BaseException:
        if hdr_name.endswith(".hdr"):
            mhd_name = hdr_name.replace(".hdr", ".mhd")
        else:
            mhd_name = hdr_name + ".mhd"


    fields = parseHdrFile(hdr_name)
    print(fields)

    writeMhdFile(mhd_name, fields)
