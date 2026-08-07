#!/usr/bin/env python3
# pylint: disable=wrong-import-position,line-too-long
"""Compatibility shim for importing root-level paint_points."""

from pathlib import Path
import sys
import warnings

_SRC = Path(__file__).resolve().parent / "src"
if _SRC.exists():
    sys.path.insert(0, str(_SRC))

warnings.warn(
    "Importing root-level paint_points is deprecated. Use sitk_tools.paint_points.",
    FutureWarning,
    stacklevel=2,
)

from sitk_tools.paint_points import *  # pylint: disable=wildcard-import,unused-wildcard-import
