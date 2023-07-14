#! /usr/bin/env python

import SimpleITK as sitk
import sys
import argparse


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
            print(filename,"seems wonky")
            return None

        for i in range(2, 6):
            l = lines[i]
            words = l.split(' ')
            x = float(words[0])
            y = float(words[1])
            #print(x, y)
            pts.append([x, y])

    return pts


def compute_transform(fixed_pts, moving_pts):
    """Do the actual landmark registration."""

    landmark_initializer = sitk.LandmarkBasedTransformInitializerFilter()
    flist = flatten_point_list(fixed_pts)
    print(flist)
    landmark_initializer.SetFixedLandmarks(flist)
    landmark_initializer.SetMovingLandmarks(flatten_point_list(moving_pts))

    transform = sitk.AffineTransform(2)

    # Compute the transform.
    output_transform = landmark_initializer.Execute(transform)

    print(output_transform)
    return output_transform


def parseargs():
    parser = argparse.ArgumentParser()

    parser.add_argument("fixed_pts")
    parser.add_argument("moving_pts")
    parser.add_argument("output_tfm")
    parser.add_argument( "--fixed", "-f", action="store", dest="fixed_img", default="",
        help="Fixed image file")
    parser.add_argument( "--moving", "-m", action="store", dest="moving_img", default="",
        help="Moving image file")
    parser.add_argument( "--result", "-r", action="store", dest="result", default="lmout.png",
        help="Resampled moving image file")


    args = parser.parse_args()
    return args

def usage():
    print("lmreg.py [options] fixed.pts moving.pts output.tform")

if __name__ == '__main__':

    args = parseargs()

    print(args)

    fixed_pts = read_points(args.fixed_pts)
    print("fixed points", fixed_pts)
    moving_pts = read_points(args.moving_pts)
    print("moving points", moving_pts)

    output_transform = compute_transform(fixed_pts, moving_pts)

    print("Writing output transform", args.output_tfm)
    sitk.WriteTransform(output_transform, args.output_tfm)

    try:
        fixed_img = sitk.ReadImage(args.fixed_img)
        moving_img = sitk.ReadImage(args.moving_img)
        output_img = sitk.Resample( moving_img, fixed_img, transform=output_transform )
        print("Writing resample moving image:", args.result)
        sitk.WriteImage(output_img, args.result)
    except BaseException:
        print("No image resampling done")
        sys.exit()



    rf = sitk.VectorIndexSelectionCast(fixed_img, 0, sitk.sitkUInt16)
    gf = sitk.VectorIndexSelectionCast(fixed_img, 1, sitk.sitkUInt16)
    bf = sitk.VectorIndexSelectionCast(fixed_img, 2, sitk.sitkUInt16)

    rm = sitk.VectorIndexSelectionCast(output_img, 0, sitk.sitkUInt16)
    gm = sitk.VectorIndexSelectionCast(output_img, 1, sitk.sitkUInt16)
    bm = sitk.VectorIndexSelectionCast(output_img, 2, sitk.sitkUInt16)

    sum_img = rf+gf+bf + rm+gm+bm

    sitk.WriteImage(sum_img, "sum.png")
#    sitk.Show(sum_img, "sum")
#    sitk.Show(fixed_img, "fixed")
#    sitk.Show(moving_img, "moving")
#    sitk.Show(output_img, "output")
