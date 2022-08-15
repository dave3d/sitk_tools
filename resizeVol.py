#! /usr/bin/env python

import sys, getopt
import SimpleITK as sitk

#
# A script that linearly resamples a volume to a new size.
# If a new size in any dimension is not specified, the size
# is unchanged.


def resizeVol(vol, newsize):

    size = vol.GetSize()
    dims = len(size)
    if dims < len(newsize):
        newsize = newsize[:dims]
    elif dims > len(newsize):
        # if newsize doesn't have enough dimensions
        # tack on the rest of the dimensions from the input volume
        newsize = newsize + size[dims - 1 :]

    origin = vol.GetOrigin()
    direction = vol.GetDirection()
    spacing = vol.GetSpacing()

    newspacing = []

    for i in range(len(size)):
        newspacing.append(size[i] * spacing[i] / newsize[i])

    vol2 = sitk.Resample(
        vol, newsize, sitk.Transform(), sitk.sitkLinear, origin, newspacing, direction
    )

    return vol2


# Handler for the standalone script
#
if __name__ == "__main__":
    verbose = False
    newsize = [1000000, 1000000, 1000000]

    def usage():
        print("")
        print("resizeVol.py [options] input_volume output_volume")
        print("")
        print(" -x int   New X size")
        print(" -y int   New Y size")
        print(" -z int   New Z size")
        print("")

    try:
        opts, args = getopt.getopt(
            sys.argv[1:], "vhx:y:z:", ["verbose", "help", "x=", "y=", "z="]
        )
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(1)

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-x", "--x"):
            newsize[0] = int(a)
        elif o in ("-y", "--y"):
            newsize[1] = int(a)
        elif o in ("-z", "--z"):
            newsize[2] = int(a)
        else:
            assert False, "unhandled option"

    print(newsize)

    if len(args) < 2:
        usage()
        sys.exit(2)

    inName = args[0]
    outName = args[1]

    if verbose:
        print()
        print("Input file: ", inName)
        print("Output file: ", outName)

    vol = sitk.ReadImage(inName)
    size = vol.GetSize()
    dims = len(size)

    # make the number of dimensions match the input image
    newsize = newsize[:dims]

    for i in range(dims):
        if newsize[i] == 1000000:
            newsize[i] = size[i]

    if verbose:
        print("New size: ", newsize)

    outvol = resizeVol(vol, newsize)

    sitk.WriteImage(outvol, outName)
