#! /usr/bin/env python

""" Landmark registration using SimpleITK. """

import sys
import argparse
import SimpleITK as sitk
import paint_points


#
# Landmark registration
#
# lmreg.py --fixed fixed_img --moving moving_img [--result new_moving_img] \
#          fixed_points moving_points [output_transform.tfm]


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
    with open(filename, "r", encoding='utf-8') as f:
        lines = f.readlines()
        if len(lines) != 6:
            print(filename, "seems wonky")
            return None

        for i in range(2, 6):
            l = lines[i]
            words = l.split(" ")
            x = float(words[0])
            y = float(words[1])
            p = [x, y]
            if len(words) > 2:
                print(len(words), words)
                z = float(words[2])
                p.append(z)
            # print(x, y)
            pts.append(p)

    return pts


def compute_transform(fix_pts, mov_pts, threeD=False):
    """Do the actual landmark registration."""

    landmark_initializer = sitk.LandmarkBasedTransformInitializerFilter()
    flist = flatten_point_list(fix_pts)
    # print(flist)

    landmark_initializer.SetFixedLandmarks(flist)
    landmark_initializer.SetMovingLandmarks(flatten_point_list(mov_pts))

    if threeD:
        transform = sitk.AffineTransform(3)
    else:
        transform = sitk.AffineTransform(2)

    # Compute the transform.
    output_tform = landmark_initializer.Execute(transform)

    print("\n", output_tform)
    return output_tform


def create_overlay(fix_pts, mov_pts, tfm, fix_img, mov_res_img):
    """ Create an overlay image of the fixed and moving points. """
    transformed_pts = []
    inv_tfm = tfm.GetInverse()
    for p in mov_pts:
        transformed_pts.append(inv_tfm.TransformPoint(p))

    # print("Transformed points:", transformed_pts)

    chan = []
    for i in range(3):
        x = sitk.VectorIndexSelectionCast(fix_img, i, sitk.sitkFloat32)
        y = sitk.VectorIndexSelectionCast(mov_res_img, i, sitk.sitkFloat32)
        z = (x + y) * 0.5
        chan.append(sitk.Cast(z, sitk.sitkUInt8))

    sum_img = sitk.Compose(chan[0], chan[1], chan[2])
    # print(sum_img)

    # print(fix_pts)
    sum_img = paint_points.paint_points(sum_img, fix_pts, channel=0)
    # print(tformed_pts)
    sum_img = paint_points.paint_points(sum_img, transformed_pts, channel=1)
    return sum_img


def remove_any_suffix(x):
    """ Remove any suffix from a file name. """
    i = x.rfind(".")
    if i == -1:
        return x
    return x[0:i]


def parseargs():
    """ Parse the command line arguments. """
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
        "--overlay",
        "-o",
        action="store",
        dest="overlay",
        default="",
        help="Overlay image",
    )

    parser.add_argument(
        "--three",
        "-t",
        action="store_true",
        default=False,
        dest="three",
        help="Three dimensional transform",
    )

    parser.add_argument(
        "--show",
        "-s",
        action="store_true",
        default=False,
        dest="show",
        help="Show images",
    )
    return parser.parse_args()


def usage():
    """Print usage information."""
    print("lmreg.py [options] fixed.pts moving.pts [output.tform]")


def make_points_3d(pts):
    """Make sure all points are 3D."""
    new_pts = []
    for p in pts:
        if len(p) == 2:
            p.append(0.0)
        new_pts.append(p)
    return new_pts


if __name__ == "__main__":
    args = parseargs()

    print(args)

    fixed_pts = read_points(args.fixed_pts)
    moving_pts = read_points(args.moving_pts)

    if args.three:
        fixed_pts = make_points_3d(fixed_pts)
        moving_pts = make_points_3d(moving_pts)

    print("fixed points", fixed_pts)
    print("moving points", moving_pts)

    output_transform = compute_transform(fixed_pts, moving_pts, args.three)

    if len(args.output_tfm) == 0:
        output_tfm_name = remove_any_suffix(args.moving_pts) + ".tfm"
    else:
        output_tfm_name = args.output_tfm

    print("Writing output transform", output_tfm_name)
    sitk.WriteTransform(output_transform, output_tfm_name)

    tformed_pts = []
    inv_tform = output_transform.GetInverse()
    for pt in moving_pts:
        tformed_pts.append(inv_tform.TransformPoint(pt))
    print("Transformed points:", tformed_pts)

    if not args.three:
        try:
            fixed_img = sitk.ReadImage(args.fixed_img)
            moving_img = sitk.ReadImage(args.moving_img)
            output_img = sitk.Resample(
                moving_img, fixed_img, transform=output_transform
            )

            base_name = remove_any_suffix(args.moving_img)

            if args.result == "":
                result_name = base_name + "-reg.png"
            else:
                result_name = args.result

            print("Writing resample moving image:", result_name)
            sitk.WriteImage(output_img, result_name)
        except RuntimeError:
            print("No image resampling done")
            sys.exit()

        sum_image = create_overlay(
            fixed_pts, moving_pts, output_transform, fixed_img, output_img
        )

        if args.overlay != "":
            overlay_name = args.overlay
        else:
            overlay_name = base_name + "-overlay.png"
        sitk.WriteImage(sum_image, overlay_name)

        if args.show:
            sitk.Show(sum_image, "sum")
            sitk.Show(fixed_img, "fixed")
            sitk.Show(moving_img, "moving")
            sitk.Show(output_img, "output")
