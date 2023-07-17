#! /usr/bin/env python

import SimpleITK as sitk
import sys
import argparse
from paint_points import *


#
# Landmark registration
#
# lmreg.py --fixed fixed_img --moving moving_img --result new_moving_img \
#          fixed_points moving_points output_transform.tfm


def flatten_point_list(pts):
    """Flatten a list of points into a 1-d array"""
    new_list = []
    for p in pts:
        for v in p:
            new_list.append(v)
    return new_list


def read_points(filename):
    """Read a points file in Elastix format."""
    pts = []
    with open(filename, "r") as f:
        lines = f.readlines()
        if len(lines) != 6:
            print(filename, "seems wonky")
            return None

        for i in range(2, 6):
            l = lines[i]
            words = l.split(" ")
            x = float(words[0])
            y = float(words[1])
            # print(x, y)
            pts.append([x, y])

    return pts


def compute_transform(fixed_pts, moving_pts):
    """Do the actual landmark registration."""

    landmark_initializer = sitk.LandmarkBasedTransformInitializerFilter()
    flist = flatten_point_list(fixed_pts)
    # print(flist)

    landmark_initializer.SetFixedLandmarks(flist)
    landmark_initializer.SetMovingLandmarks(flatten_point_list(moving_pts))

    transform = sitk.AffineTransform(2)

    # Compute the transform.
    output_transform = landmark_initializer.Execute(transform)

    print("\n", output_transform)
    return output_transform


def create_overlay(fix_pts, mov_pts, tfm, fix_img, mov_res_img):
    tformed_pts = []
    inv_tfm = tfm.GetInverse()
    for pt in mov_pts:
        tformed_pts.append(inv_tfm.TransformPoint(pt))

    # print("Transformed points:", tformed_pts)

    chan = []
    for i in range(3):
        x = sitk.VectorIndexSelectionCast(fix_img, i, sitk.sitkFloat32)
        y = sitk.VectorIndexSelectionCast(mov_res_img, i, sitk.sitkFloat32)
        z = (x + y) * 0.5
        chan.append(sitk.Cast(z, sitk.sitkUInt8))

    sum_img = sitk.Compose(chan[0], chan[1], chan[2])
    # print(sum_img)

    # print(fix_pts)
    sum_img = paint_points(sum_img, fix_pts, channel=0)
    # print(tformed_pts)
    sum_img = paint_points(sum_img, tformed_pts, channel=1)
    return sum_img


def remove_any_suffix(x):
    i = x.rfind(".")
    if i == -1:
        return x
    return x[0:i]


def parseargs():
    parser = argparse.ArgumentParser()

    parser.add_argument("fixed_pts")
    parser.add_argument("moving_pts")
    parser.add_argument(
        "output_tfm",
        nargs="*",
        help="Output transform. By default name derived from moving points file name.",
    )
    parser.add_argument(
        "--fixed",
        "-f",
        action="store",
        dest="fixed_img",
        default="",
        help="Fixed image file",
    )
    parser.add_argument(
        "--moving",
        "-m",
        action="store",
        dest="moving_img",
        default="",
        help="Moving image file",
    )
    parser.add_argument(
        "--result",
        "-r",
        action="store",
        dest="result",
        default="",
        help="Resampled moving image file",
    )

    parser.add_argument(
        "--show",
        "-s",
        action="store_true",
        default=False,
        dest="show",
        help="Show images",
    )

    args = parser.parse_args()
    return args


def usage():
    print("lmreg.py [options] fixed.pts moving.pts [output.tform]")


if __name__ == "__main__":
    args = parseargs()

    print(args)

    fixed_pts = read_points(args.fixed_pts)
    print("fixed points", fixed_pts)
    moving_pts = read_points(args.moving_pts)
    print("moving points", moving_pts)

    output_transform = compute_transform(fixed_pts, moving_pts)

    if len(args.output_tfm) == 0:
        output_tfm_name = remove_any_suffix(args.moving_pts) + ".tfm"
    else:
        output_tfm_name = args.output_tfm

    print("Writing output transform", output_tfm_name)
    sitk.WriteTransform(output_transform, output_tfm_name)

    try:
        fixed_img = sitk.ReadImage(args.fixed_img)
        moving_img = sitk.ReadImage(args.moving_img)
        output_img = sitk.Resample(moving_img, fixed_img, transform=output_transform)

        base_name = remove_any_suffix(args.moving_img)

        if args.result == "":
            result_name = base_name + "-reg.png"
        else:
            result_name = args.result

        print("Writing resample moving image:", result_name)
        sitk.WriteImage(output_img, result_name)
    except BaseException:
        print("No image resampling done")
        sys.exit()

    sum_img = create_overlay(
        fixed_pts, moving_pts, output_transform, fixed_img, output_img
    )

    tformed_pts = []
    inv_tform = output_transform.GetInverse()
    for pt in moving_pts:
        tformed_pts.append(inv_tform.TransformPoint(pt))
    sitk.WriteImage(sum_img, "sum.png")

    print("Transformed points:", tformed_pts)

    if args.show == True:
        sitk.Show(sum_img, "sum")
        sitk.Show(fixed_img, "fixed")
        sitk.Show(moving_img, "moving")
        sitk.Show(output_img, "output")
