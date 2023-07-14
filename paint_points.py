#! /usr/bin/env python

import SimpleITK as sitk


def paint_points(img, points, radius=15, channel=0):
    """ Paint points into an image. """
    chan = []
    if img.GetDepth() == 3:
        for i in range(3):
            chan.append(sitk.VectorIndexSelectionCast(img, i))
    else:
        for i in range(3):
            chan.append(sitk.Image(img))

    point_img = chan[0]*0

    # Set the point pixels
    for pt in points:
        x = int(pt[0])
        y = int(pt[1])
        #print("x,y:", x, y)
        point_img[x-radius:x+radius, y-radius:y+radius] = 255

    #corners_img = sitk.GrayscaleDilate(corners_img, [25,25])

    chan[channel] = sitk.Maximum(chan[channel], point_img)
    result = sitk.Compose(chan[0], chan[1], chan[2])

    return result
