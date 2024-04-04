#! /usr/bin/env python

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
slice_dir = root_dir + "/masks"
metadata_file = root_dir + "/slices/volume.pkl"


def merge_slices(
    slice_dir, metadata_file="", output_name="mask.nii.gz", slice_format="slice*.nii.gz"
):

    metadataFlag = False

    if len(metadata_file) > 0:
        try:
            fp = open(metadata_file, "rb")
            metadata = pickle.load(fp)
            print(metadata)
            metadataFlag = True
        except:
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


if __name__ == "__main__":

    if len(sys.argv) > 1:
        slice_dir = sys.argv[1]

        if len(sys.argv) > 2:
            metadata_file = sys.argv[2]
        else:
            # we have slice directory but no metadata file in the arguments
            metadata_file = ""

    merge_slices(slice_dir, metadata_file)
