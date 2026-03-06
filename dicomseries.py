#! /usr/bin/env python

"""Scan a directory for DICOM series.

Can also convert all series to other formats with the '--convert' flag.

In conversion mode, the name of the output volume is derived from either the
series description (--name desc) or the series id (--name series).
Series description is the default.

The output volume type is specified with the suffix option. Default is '.nrrd'.
"""

import argparse
import logging
import os

import SimpleITK as sitk

# Tags of interest to copy into output volumes
DICOM_TAGS = [
    "0008|0020",  # acquisition date
    "0008|0030",  # study time
    "0008|103e",  # series description
    "0010|0010",  # patient name
    "0010|0020",  # patient ID
    "0020|000d",  # study instance UID
    "0020|000e",  # series instance UID
]


def get_meta(reader: sitk.ImageSeriesReader, key: str, default: str = "Unknown") -> str:
    """Safely retrieve a metadata value from a series reader."""
    try:
        return reader.GetMetaData(0, key)
    except RuntimeError:
        return default


def sanitize_name(name: str) -> str:
    """Replace spaces and slashes in a name to make it filesystem-safe."""
    name = name.rstrip()
    return name.translate(name.maketrans(" /", "_-", "*"))


def dump_metadata_from_reader(reader: sitk.ImageSeriesReader) -> None:
    """Dump the metadata dictionary from slice 0 of a loaded series reader."""
    logging.info("Dumping the meta data dictionary")
    for k in reader.GetMetaDataKeys(0):
        v = reader.GetMetaData(0, k)
        truncated = v[:99] + " ..." if len(v) > 255 else v
        print(f"  {k}: {truncated}")


def dump_metadata_from_file(fname: str) -> None:
    """Dump the metadata dictionary from a single DICOM file."""
    img = sitk.ReadImage(fname)
    print("Metadata Dictionary")
    for k in img.GetMetaDataKeys():
        v = img.GetMetaData(k)
        truncated = v[:99] + " ..." if len(v) > 255 else v
        print(f"  {k}: {truncated}")


def build_output_name(
    reader: sitk.ImageSeriesReader,
    series_id: str,
    dirname: str,
    suffix: str,
    name_src: int,
) -> str:
    """Derive the output filename from series metadata or series ID."""
    series_description = get_meta(reader, "0008|103e", "UnknownSeries")
    ac_date = get_meta(reader, "0008|0020", "UnknownDate")
    patient_name = get_meta(reader, "0010|0010", "UnknownName")

    if series_description and name_src == 1:
        sd = sanitize_name(series_description)
        pn = sanitize_name(patient_name)
        name = f"{pn}-{ac_date}-{sd}"
    else:
        name = series_id

    return os.path.join(dirname, name + suffix)


def process_series(
    isr: sitk.ImageSeriesReader,
    series_id: str,
    fnames: tuple,
    dirname: str,
    args: argparse.Namespace,
) -> None:
    """Convert a single DICOM series to a volume file."""
    logging.info("Converting series %s (%d files)", series_id, len(fnames))

    isr.SetFileNames(fnames)
    isr.MetaDataDictionaryArrayUpdateOn()
    isr.LoadPrivateTagsOn()
    img = isr.Execute()
    logging.debug("%s", img)

    if args.verbose > 1 or args.dict:
        dump_metadata_from_reader(isr)

    outname = build_output_name(isr, series_id, dirname, args.suffix, args.name_src)

    # Copy the DICOM tags of interest into the output image
    for k in DICOM_TAGS:
        try:
            v = isr.GetMetaData(0, k)
            if v:
                img.SetMetaData(k, v)
                logging.debug("  %s: %s", k, v)
        except RuntimeError:
            logging.debug("  %s: not found", k)

    if os.path.exists(outname):
        logging.warning("%s already exists. Overwriting.", outname)

    print(f"Writing {outname}")
    sitk.WriteImage(img, outname, useCompression=True)


def scan_directory(dirname: str, args: argparse.Namespace) -> None:
    """Scan a single directory for DICOM series and optionally convert them."""
    print(f"\nDirectory: {dirname}")
    isr = sitk.ImageSeriesReader()
    series_ids = isr.GetGDCMSeriesIDs(dirname)

    print(f"\nSeries IDs ({len(series_ids)} found)")
    for s in series_ids:
        print(f"  {s}")
    print()

    for s in series_ids:
        fnames = isr.GetGDCMSeriesFileNames(dirname, s, False, args.recursive, False)
        print(f"\nSeries: {s}  ({len(fnames)} files)")
        logging.debug("  Files: %s", fnames)

        if args.convert and len(fnames) >= args.thickness:
            process_series(isr, s, fnames, dirname, args)
        elif args.dict and len(fnames) >= args.thickness:
            dump_metadata_from_file(fnames[0])


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Scan a directory for DICOM series and optionally convert them."
    )
    parser.add_argument("directories", nargs="+", metavar="dicom_directory",
                        help="One or more directories to scan for DICOM series")
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Increase verbosity level (use -vv for debug)")
    parser.add_argument("-r", "--recursive", action="store_true",
                        help="Search directories recursively")
    parser.add_argument("-c", "--convert", action="store_true",
                        help="Convert series to volumes")
    parser.add_argument("-d", "--dict", action="store_true",
                        help="Dump the metadata dictionary")
    parser.add_argument("-s", "--suffix", default=".nrrd", metavar="string",
                        help="Output volume suffix (default: .nrrd)")
    parser.add_argument("-t", "--thickness", type=int, default=20, metavar="int",
                        help="Minimum Z thickness (slices) for conversion (default: 20)")
    parser.add_argument(
        "-n", "--name", dest="name_src", default="desc",
        choices=["desc", "series"],
        help="Source for output filename: 'desc' (series description) or 'series' (series ID)",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point: parse arguments and scan/convert DICOM series."""
    args = parse_args()

    log_level = logging.WARNING
    if args.verbose == 1:
        log_level = logging.INFO
    elif args.verbose >= 2:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    # Map name choice to an integer for internal use
    args.name_src = 1 if args.name_src == "desc" else 2

    print("\ndicomseries.py\n")
    logging.info("recursive:  %s", args.recursive)
    logging.info("convert:    %s", args.convert)
    logging.info("suffix:     %s", args.suffix)
    logging.info("min thickness: %d", args.thickness)

    for dirname in args.directories:
        scan_directory(dirname, args)

    print()


if __name__ == "__main__":
    main()
