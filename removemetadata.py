#! /usr/bin/env python

""" Remove all metadata from an image """

import sys
import getopt
import SimpleITK as sitk


def usage():
    """ Print usage """
    print("")
    print("Usage:  removemetadata.py [options] input_file output_file")
    print("")
    print(" -h, --help       This help message")
    print(" -v, --verbose    Verbose")
    print("")


if __name__ == "__main__":
    verbose = False

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hv",
            [
                "help",
                "verbose",
            ],
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
        else:
            assert False, "unhandled option"

    if len(args) < 2:
        usage()
        sys.exit(2)

    in_name = args[0]
    out_name = args[1]

    img = sitk.ReadImage(in_name)

    keys = img.GetMetaDataKeys()
    for k in keys:
        if verbose:
            v = img.GetMetaData(k)
            print(k, ":", v)
        img.EraseMetaData(k)

    sitk.WriteImage(img, out_name)
