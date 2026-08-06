"""Command-line entry point for sitk_tools."""

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m sitk_tools",
        description="SimpleITK utility collection. Use submodules as entry points.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List package modules intended for direct execution.",
    )
    args = parser.parse_args()

    if args.list:
        print("bound_obj")
        print("compareimages")
        print("dicomseries")
        print("dictdump")
        print("extract_objects")
        print("extract_subimages")
        print("hdr2mhd")
        print("histo")
        print("lmreg")
        print("merge_slices")
        print("mkdicom")
        print("nifti2vti")
        print("query_vol")
        print("radial_slices")
        print("removemetadata")
        print("resample_to_volume")
        print("resizeVol")
        print("show")
        print("sitk_test")
        print("split_vti")
        print("split_vti_fixed")
        print("split_vtk_volume")
        print("vector")
        print("vti_sitk")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
