#! /usr/bin/env python

"""  vector.py -- Basic vector math routines """

import math

# Basic vector math routines
#


def add(a, b):
    """Add two vectors"""
    vlen = min(len(a), len(b))

    c = []
    for i in range(vlen):
        c.append(a[i] + b[i])
    return c


def subtract(a, b):
    """Subtract two vectors"""
    vlen = min(len(a), len(b))

    c = []
    for i in range(vlen):
        c.append(a[i] - b[i])
    return c


def dot(a, b):
    """Dot product of two vectors"""
    vlen = min(len(a), len(b))

    dsum = 0.0
    for i in range(vlen):
        dsum = dsum + (a[i] * b[i])
    return dsum


def cross(a, b):
    """Cross product of two vectors"""
    result = []
    result.append(a[1] * b[2] - b[1] * a[2])
    result.append(-(a[0] * b[2] - b[0] * a[2]))
    result.append(a[0] * b[1] - b[0] * a[1])
    return result


def length(a):
    """Length of a vector"""
    d2 = dot(a, a)
    return math.sqrt(d2)


def normalize(a):
    """Normalize a vector"""
    vlen = length(a)
    if vlen <= 0.0:
        print("Warning: zero length vector")
        return None

    d_inv = 1.0 / vlen
    result = []
    for x in a:
        result.append(x * d_inv)
    return result


def scale(a, b):
    """Scale a vector"""
    result = []
    for x in a:
        result.append(x * b)

    return result


if __name__ == "__main__":
    # test things
    #
    v = [1.0, 2.0, 3.0]
    print(v)
    print("normalize:", normalize(v))
    print()

    x_dir = [1.0, 0.0, 0.0]
    y_dir = [0.0, 1.0, 0.0]
    print(x_dir, y_dir)
    print("cross:", cross(x_dir, y_dir))
    print("add:", add(x_dir, y_dir))
    print("subtract:", subtract(x_dir, y_dir))
