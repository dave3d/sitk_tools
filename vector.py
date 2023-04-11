#! /usr/bin/env python

import math

# Basic vector math routines
#


def add(a, b):
    vlen = min(len(a), len(b))

    c = []
    for i in range(vlen):
        c.append(a[i] + b[i])
    return c


def subtract(a, b):
    vlen = min(len(a), len(b))

    c = []
    for i in range(vlen):
        c.append(a[i] - b[i])
    return c


def dot(a, b):
    vlen = min(len(a), len(b))

    sum = 0.0
    for i in range(vlen):
        sum = sum + (a[i] * b[i])
    return sum


def cross(a, b):
    result = []
    result.append(a[1] * b[2] - b[1] * a[2])
    result.append(-(a[0] * b[2] - b[0] * a[2]))
    result.append(a[0] * b[1] - b[0] * a[1])
    return result


def length(a):
    d2 = dot(a, a)
    return math.sqrt(d2)


def normalize(a):
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

    x = [1.0, 0.0, 0.0]
    y = [0.0, 1.0, 0.0]
    print(x, y)
    print("cross:", cross(x, y))
    print("add:", add(x, y))
    print("subtract:", subtract(x, y))
