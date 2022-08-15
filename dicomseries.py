#! /usr/bin/env python

import sys, getopt
import SimpleITK as sitk

#
#  Scan a directory for DICOM series.
#
#  Can also covert all series to other formats with
#  the '--convert' flag.
#

verbose = 0
recFlag = False
suffix = ".nrrd"
min_z = 20
convertFlag = False
name_src = 1
dictFlag = False

# tags of interest
dicom_tags = [
    "0008|0020",  # acquisition date
    "0008|0030",  # study time
    "0008|103e",  # series description
    "0010|0010",  # patient name
    "0010|0020",  # patient ID
]


def usage():
    print("")
    print("dicomseries.py: [options] dicom_directory")
    print("")
    print("  -h, --help       This message")
    print("  -v, --verbose    Increase verbosity level")
    print("  -r, --recursive  Search directory recursively")
    print("  -c, --convert    Convert series to volumes")
    print("  -d, --dict       Dump the metadata dictionary")
    print("  -s string, --suffix string    Output volume suffix")
    print("  -t int,  --thickness   Min Z thickness for series conversion")
    print(
        "  -n source,  --name source   Source of the output name (seriesid or description)"
    )


try:
    opts, args = getopt.getopt(
        sys.argv[1:],
        "vhrcds:t:n:",
        [
            "verbose",
            "help",
            "recursive",
            "convert",
            "dict",
            "suffix=",
            "thickness=",
            "name=",
        ],
    )

except getopt.GetoptErr as err:
    print(str(err))
    usage()
    sys.exit(1)

for o, a in opts:
    if o in ("-v", "--verbose"):
        verbose = verbose + 1
    elif o in ("-h", "--help"):
        usage()
        sys.exit()
    elif o in ("-r", "--recursive"):
        recFlag = True
    elif o in ("-c", "--convert"):
        convertFlag = True
    elif o in ("-d", "--dict"):
        dictFlag = True
    elif o in ("-s", "--suffix"):
        suffix = a
    elif o in ("-t", "--thickness"):
        min_z = int(a)
    elif o in ("-n", "--name"):
        if a.startswith("desc"):
            name_src = 1
        if a.startswith("series"):
            name_src = 2

    else:
        assert False, "unhandled options"

dirname = args[0]


isr = sitk.ImageSeriesReader()

print("\ndicomseries.py\n")

print("recFlag: ", recFlag)
print("convertFlag: ", convertFlag)
print("suffix: ", suffix)
print("min thickness: ", min_z)

for dirname in args:
    print("\nDirectory: ", dirname)
    seriesids = isr.GetGDCMSeriesIDs(dirname)

    print("\nSeries IDs")
    print(seriesids)
    print("")

    for s in seriesids:
        fnames = isr.GetGDCMSeriesFileNames(dirname, s, False, recFlag, False)

        print("")
        print("Series file names")
        print(s, len(fnames))
        print(fnames)

        if convertFlag and len(fnames) >= min_z:
            print("Do conversion!")

            isr.SetFileNames(fnames)
            isr.MetaDataDictionaryArrayUpdateOn()
            isr.LoadPrivateTagsOn()
            img = isr.Execute()
            print(img)

            if verbose > 1 or dictFlag:
                # Dump the meta data dictionary
                print("\nDumping the meta data dictionary\n")

                keys = isr.GetMetaDataKeys(0)

                for k in keys:
                    v = isr.GetMetaData(0, k)
                    if len(v) > 255:
                        print(k, ": ", v[0:99], " ...")
                    else:
                        print(k, ": ", v)

            series_description = isr.GetMetaData(0, "0008|103e")
            ac_date = isr.GetMetaData(0, "0008|0020")
            if len(series_description) and name_src == 1:
                sd = series_description.rstrip()
                d = sd.maketrans(" /", "_-", "*")
                name = sd.translate(d)
                if ac_date:
                    name = ac_date + "-" + name
                outname = dirname + "/" + name + suffix
            else:
                outname = dirname + "/" + s + suffix

            # copy the dicom tags of interest
            for k in dicom_tags:
                v = isr.GetMetaData(0, k)
                print(k, v)
                if len(v):
                    img.SetMetaData(k, v)

            print("\nWriting", outname)
            sitk.WriteImage(img, outname, useCompression=True)

        else:
            if dictFlag and len(fnames) > min_z:
                print("Metadata Dictionary")
                # dump the dictionary of the first file in the series
                img1 = sitk.ReadImage(fnames[0])
                keys = img1.GetMetaDataKeys()
                for k in keys:
                    v = img1.GetMetaData(k)
                    if len(v) > 255:
                        print(k, ": ", v[0:99], " ...")
                    else:
                        print(k, ": ", v)
    print("")
