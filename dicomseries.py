# pylint: disable=wrong-import-position,line-too-long
#!/usr/bin/env python3
"""Compatibility shim for running root-level dicomseries.py."""

from pathlib import Path
import sys
import warnings

_SRC = Path(__file__).resolve().parent / "src"
if _SRC.exists():
    sys.path.insert(0, str(_SRC))

warnings.warn(
    "Running root-level dicomseries.py is deprecated. Use python -m sitk_tools.dicomseries.",
    DeprecationWarning,
    stacklevel=2,
)

from sitk_tools.dicomseries import main


if __name__ == "__main__":
    raise SystemExit(main())
