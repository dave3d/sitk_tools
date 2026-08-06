#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "SimpleITK",
# ]
# ///

""" Script to merge a bunch of slice images into a volume """
import sys
import glob
import pickle
import SimpleITK as sitk

#
#   Dave's script to merge a bunch of slice images into a volume
#
#   It is intended for 2d mask images produced by nnUNet, so the slice
#   file names are assumed to be in the format "slice*.nii.gz"
#
#   Also, it can use a volume meta-data file produced by the slice_vol.py
#   script.  That is a python pickle file that contains the volume's
#   meta-data in a python dictionary.

# test input
root_dir = "PET-PBI-05/2023-06-21_Kumar_FR1_D1"
sd = root_dir + "/masks"
md_file = root_dir + "/slices/volume.pkl"

out_name = "mask.nii.gz"


def merge_slices(
    slice_dir, metadata_file="", output_name="mask.nii.gz", slice_format="slice*.nii.gz"
):
    """Merge a bunch of slice images into a volume"""

    metadataFlag = False

    if len(metadata_file) > 0:
        try:
            with open(metadata_file, "rb") as fp:
                metadata = pickle.load(fp)
            print(metadata)
            metadataFlag = True
        except OSError:
            print("No metadata file")

    print(slice_dir)

    glob_string = slice_dir + "/" + slice_format
    print("glob format:", glob_string)

    fnames = glob.glob(glob_string)
    fnames.sort()

    if len(fnames) == 0:
        print("Error:  no slice files found.  Exiting.")
        return

    print(fnames)

    # read the slices
    rdr = sitk.ImageSeriesReader()
    rdr.SetFileNames(fnames)
    img = rdr.Execute()

    if metadataFlag:
        # if we have metadata, apply it to the volume
        if "origin" in metadata:
            img.SetOrigin(metadata["origin"])
        if "direction" in metadata:
            img.SetDirection(metadata["direction"])
        if "spacing" in metadata:
            img.SetSpacing(metadata["spacing"])

    print(img)
    sitk.WriteImage(img, slice_dir + "/" + output_name)


def usage():
    """Print usage information."""
    print("Usage: sitk-merge-slices <slice_dir> [metadata_file.pkl] [output_name.nii.gz]")


def main(argv=None):
    """CLI entry point."""
    args = argv if argv is not None else sys.argv[1:]

    if len(args) > 0 and args[0] in ("-h", "--help"):
        usage()
        return 0

    slice_dir = sd
    metadata_file = md_file
    output_name = out_name

    if len(args) > 0:
        slice_dir = args[0]
        if len(args) > 1:
            metadata_file = args[1]
            if len(args) > 2:
                output_name = args[2]
        else:
            metadata_file = ""

    merge_slices(slice_dir, metadata_file, output_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
