#! /usr/bin/env python

import sys, getopt
import SimpleITK as sitk


verbose = 0
recFlag = False
suffix = ".nii.gz"
min_z = 20
convertFlag = False

def usage():
    print ("")
    print ("dicomseries.py: [options] dicom_directory")
    print ("")
    print ("  -h, --help       This message")
    print ("  -v, --verbose    Increase verbosity level")
    print ("  -r, --recursive  Search directory recursively")
    print ("  -c, --convert    Convert series to volumes")
    print ("  -s string, --suffix string    Output volume suffix")
    print ("  -t int,  --thickness   Min Z thickness for series conversion")


try:
    opts, args= getopt.getopt( sys.argv[1:], "vhrcs:t:",
                              [ "verbose", "help", "recursive", "convert",
                                "suffix=", "thickness="
                              ] )

except getopt.GetoptErr as err:
    print (str(err))
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
    elif o in ("-s", "--suffix"):
        suffix = a
    elif o in ("-t", "--thickness"):
        min_z = int(a)
    else:
        assert False, "unhandled options"

dirname = args[0]

isr = sitk.ImageSeriesReader()

print("\ndicomseries.py\n")

print ("recFlag: ", recFlag)
print ("convertFlag: ", convertFlag)
if verbose:
    if convertFlag:
        print("suffix: ", suffix)
        print("min thickness: ", min_z)

seriesids = isr.GetGDCMSeriesIDs(dirname)

print ("\nSeries IDs")
print (seriesids)
print ("")

for s in seriesids:
    fnames = isr.GetGDCMSeriesFileNames(dirname, s, False, recFlag, False)

    print ("")
    print ("Series file names")
    print (s, len(fnames))
    print (fnames)


    if convertFlag and len(fnames) >= min_z:
        print("Do conversion!")

        isr.SetFileNames(fnames)
        isr.MetaDataDictionaryArrayUpdateOn()
        isr.LoadPrivateTagsOn()
        img = isr.Execute()
        print(img)

        if verbose>1:
            # Dump the meta data dictionary
            print ("\nDumping the meta data dictionary\n")

            keys = isr.GetMetaDataKeys(0)

            for k in keys:
                v = isr.GetMetaData(0,k)
                if len(v)>255:
                    print (k, ": ", v[0:99], " ...")
                else:
                    print (k, ": ", v)

        series_description = isr.GetMetaData(0, "0008|103e");
        if len(series_description):
            outname = dirname + "/" + series_description + suffix
        else:
            outname = dirname + "/" + s + suffix
        print("\nWriting", outname)
        sitk.WriteImage(img, outname)
print ("")

