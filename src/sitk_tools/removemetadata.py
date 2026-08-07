#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "SimpleITK",
# ]
# ///

""" Remove all metadata from an image """

import sys
import getopt
import SimpleITK as sitk


def usage():
    """Print usage"""
    print("")
    print("Usage: sitk-removemetadata [options] <input_file> <output_file>")
    print("")
    print(" -h, --help       This help message")
    print(" -v, --verbose    Verbose")
    print("")


def main(argv=None):
    """CLI entry point."""
    verbose = False

    try:
        opts, args = getopt.getopt(
            argv if argv is not None else sys.argv[1:],
            "hv",
            [
                "help",
                "verbose",
            ],
        )
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        return 1

    for o, _ in opts:
        if o in ("-h", "--help"):
            usage()
            return 0
        if o in ("-v", "--verbose"):
            verbose = True
            continue
        assert False, "unhandled option"

    if len(args) < 2:
        usage()
        return 2

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
