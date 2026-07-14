"""
Tests for resample_to_volume.py
"""

import sys
import math
import tempfile
from pathlib import Path

import pytest
import numpy as np
import SimpleITK as sitk

# Make the parent directory importable regardless of how pytest is invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import resample_to_volume as rtv


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_image(
    size=(10, 10, 10),
    spacing=(1.0, 1.0, 1.0),
    origin=(0.0, 0.0, 0.0),
    direction=None,
    fill=1.0,
    pixel_type=sitk.sitkFloat32,
) -> sitk.Image:
    """Create a simple filled 3-D test image."""
    img = sitk.Image(list(size), pixel_type)
    img.SetSpacing(spacing)
    img.SetOrigin(origin)
    if direction is not None:
        img.SetDirection(direction)
    return img + fill


def identity_direction():
    return (1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0)


# ---------------------------------------------------------------------------
# load_image
# ---------------------------------------------------------------------------

class TestLoadImage:
    def test_3d_image_unchanged(self, tmp_path):
        img = make_image(size=(5, 6, 7))
        p = str(tmp_path / "vol.nrrd")
        sitk.WriteImage(img, p)
        loaded = rtv.load_image(p)
        assert loaded.GetDimension() == 3
        assert loaded.GetSize() == (5, 6, 7)

    def test_2d_image_promoted_to_3d(self, tmp_path):
        img2d = sitk.Image(8, 8, sitk.sitkFloat32)
        p = str(tmp_path / "slice.nrrd")
        sitk.WriteImage(img2d, p)
        loaded = rtv.load_image(p)
        assert loaded.GetDimension() == 3
        assert loaded.GetSize()[2] == 1


# ---------------------------------------------------------------------------
# compute_reference_grid
# ---------------------------------------------------------------------------

class TestComputeReferenceGrid:
    def test_single_image_auto_spacing(self):
        img = make_image(size=(10, 10, 10), spacing=(2.0, 2.0, 2.0))
        size, spacing, origin, direction = rtv.compute_reference_grid([img], None)
        assert spacing == (2.0, 2.0, 2.0)
        # Grid should cover at least the input extent.
        for i in range(3):
            assert size[i] >= 10

    def test_auto_spacing_picks_finest(self):
        coarse = make_image(size=(5, 5, 5), spacing=(4.0, 4.0, 4.0))
        fine   = make_image(size=(20, 20, 20), spacing=(1.0, 1.0, 1.0))
        _, spacing, _, _ = rtv.compute_reference_grid([coarse, fine], None)
        assert spacing == (1.0, 1.0, 1.0)

    def test_explicit_spacing_respected(self):
        img = make_image(size=(10, 10, 10), spacing=(1.0, 1.0, 1.0))
        _, spacing, _, _ = rtv.compute_reference_grid([img], [3.0, 3.0, 3.0])
        assert spacing == (3.0, 3.0, 3.0)

    def test_bounding_box_covers_offset_images(self):
        """Two non-overlapping images: grid must cover both."""
        img_a = make_image(size=(5, 5, 5), spacing=(1.0, 1.0, 1.0), origin=(0.0, 0.0, 0.0))
        img_b = make_image(size=(5, 5, 5), spacing=(1.0, 1.0, 1.0), origin=(10.0, 10.0, 10.0))
        size, spacing, origin, _ = rtv.compute_reference_grid([img_a, img_b], [1.0, 1.0, 1.0])
        # Physical extent covered: 0..14 in each axis → need at least 15 voxels.
        for i in range(3):
            assert size[i] >= 15

    def test_direction_taken_from_first_image(self):
        d = identity_direction()
        img = make_image(direction=d)
        _, _, _, direction = rtv.compute_reference_grid([img], None)
        assert direction == d

    def test_size_at_least_one_per_axis(self):
        """Single-voxel image should still produce a valid grid."""
        img = make_image(size=(1, 1, 1), spacing=(1.0, 1.0, 1.0))
        size, _, _, _ = rtv.compute_reference_grid([img], None)
        assert all(s >= 1 for s in size)


# ---------------------------------------------------------------------------
# resample_to_reference
# ---------------------------------------------------------------------------

class TestResampleToReference:
    def test_output_size_matches_requested(self):
        img = make_image(size=(10, 10, 10), spacing=(1.0, 1.0, 1.0), fill=5.0)
        out = rtv.resample_to_reference(
            img,
            size=(20, 20, 20),
            spacing=(0.5, 0.5, 0.5),
            origin=(0.0, 0.0, 0.0),
            direction=identity_direction(),
            interpolator=sitk.sitkLinear,
            default_value=0.0,
        )
        assert out.GetSize() == (20, 20, 20)

    def test_identity_resample_preserves_values(self):
        img = make_image(size=(8, 8, 8), spacing=(1.0, 1.0, 1.0), fill=7.0)
        out = rtv.resample_to_reference(
            img,
            size=(8, 8, 8),
            spacing=(1.0, 1.0, 1.0),
            origin=(0.0, 0.0, 0.0),
            direction=identity_direction(),
            interpolator=sitk.sitkLinear,
            default_value=0.0,
        )
        arr = sitk.GetArrayFromImage(out)
        assert np.allclose(arr, 7.0)

    def test_padding_value_outside_image(self):
        img = make_image(size=(5, 5, 5), spacing=(1.0, 1.0, 1.0),
                         origin=(100.0, 100.0, 100.0), fill=1.0)
        out = rtv.resample_to_reference(
            img,
            size=(10, 10, 10),
            spacing=(1.0, 1.0, 1.0),
            origin=(0.0, 0.0, 0.0),
            direction=identity_direction(),
            interpolator=sitk.sitkLinear,
            default_value=-999.0,
        )
        arr = sitk.GetArrayFromImage(out)
        # The image is far away; most voxels should be the pad value.
        assert np.sum(arr == -999.0) > 0


# ---------------------------------------------------------------------------
# stack_images
# ---------------------------------------------------------------------------

class TestStackImages:
    def _grid(self, size=(10, 10, 10), spacing=(1.0, 1.0, 1.0)):
        return dict(
            size=size,
            spacing=spacing,
            origin=(0.0, 0.0, 0.0),
            direction=identity_direction(),
            interpolator=sitk.sitkLinear,
            default_value=0.0,
        )

    def test_single_image_passthrough(self):
        img = make_image(size=(10, 10, 10), spacing=(1.0, 1.0, 1.0), fill=3.0)
        g = self._grid()
        out = rtv.stack_images([img], **g)
        assert out.GetSize() == g["size"]

    def test_two_images_merged_by_max(self):
        """Non-overlapping images: combined volume should contain both fills."""
        low = make_image(size=(10, 10, 10), spacing=(1.0, 1.0, 1.0),
                         origin=(0.0, 0.0, 0.0), fill=1.0)
        high = make_image(size=(10, 10, 10), spacing=(1.0, 1.0, 1.0),
                          origin=(20.0, 0.0, 0.0), fill=5.0)
        g = dict(
            size=(31, 10, 10),
            spacing=(1.0, 1.0, 1.0),
            origin=(0.0, 0.0, 0.0),
            direction=identity_direction(),
            interpolator=sitk.sitkLinear,
            default_value=0.0,
        )
        out = rtv.stack_images([low, high], **g)
        arr = sitk.GetArrayFromImage(out)
        assert arr.max() == pytest.approx(5.0, abs=0.1)
        assert arr.min() == pytest.approx(0.0, abs=0.1)

    def test_overlapping_max_wins(self):
        """Where images overlap, the higher value should survive."""
        img_low  = make_image(size=(10, 10, 10), spacing=(1.0, 1.0, 1.0), fill=2.0)
        img_high = make_image(size=(10, 10, 10), spacing=(1.0, 1.0, 1.0), fill=9.0)
        g = self._grid()
        out = rtv.stack_images([img_low, img_high], **g)
        arr = sitk.GetArrayFromImage(out)
        assert np.allclose(arr, 9.0)


# ---------------------------------------------------------------------------
# build_spacing
# ---------------------------------------------------------------------------

class TestBuildSpacing:
    def _args(self, spacing=None, x=None, y=None, z=None):
        import argparse
        a = argparse.Namespace(spacing=spacing, x=x, y=y, z=z)
        return a

    def test_none_when_nothing_specified(self):
        assert rtv.build_spacing(self._args()) is None

    def test_isotropic_spacing(self):
        result = rtv.build_spacing(self._args(spacing=2.0))
        assert result == [2.0, 2.0, 2.0]

    def test_per_axis_partial(self):
        result = rtv.build_spacing(self._args(x=1.0, z=3.0))
        assert result == [1.0, None, 3.0]

    def test_isotropic_takes_precedence_over_per_axis(self):
        result = rtv.build_spacing(self._args(spacing=5.0, x=1.0))
        assert result == [5.0, 5.0, 5.0]


# ---------------------------------------------------------------------------
# main (end-to-end via temp files)
# ---------------------------------------------------------------------------

class TestMain:
    def _write_image(self, path, size=(8, 8, 8), spacing=(1.0, 1.0, 1.0),
                     origin=(0.0, 0.0, 0.0), fill=1.0):
        img = make_image(size=size, spacing=spacing, origin=origin, fill=fill)
        sitk.WriteImage(img, str(path))

    def test_single_input_produces_output(self, tmp_path):
        inp = tmp_path / "in.nrrd"
        out = tmp_path / "out.nrrd"
        self._write_image(inp)
        rc = rtv.main([str(inp), str(out)])
        assert rc == 0
        assert out.exists()

    def test_output_is_3d(self, tmp_path):
        inp = tmp_path / "in.nrrd"
        out = tmp_path / "out.nrrd"
        self._write_image(inp)
        rtv.main([str(inp), str(out)])
        result = sitk.ReadImage(str(out))
        assert result.GetDimension() == 3

    def test_explicit_isotropic_spacing(self, tmp_path):
        inp = tmp_path / "in.nrrd"
        out = tmp_path / "out.nrrd"
        self._write_image(inp, spacing=(1.0, 1.0, 1.0))
        rtv.main(["-s", "2.0", str(inp), str(out)])
        result = sitk.ReadImage(str(out))
        sp = result.GetSpacing()
        assert sp == pytest.approx((2.0, 2.0, 2.0))

    def test_two_inputs_merged(self, tmp_path):
        inp1 = tmp_path / "a.nrrd"
        inp2 = tmp_path / "b.nrrd"
        out  = tmp_path / "out.nrrd"
        self._write_image(inp1, origin=(0.0, 0.0, 0.0), fill=1.0)
        self._write_image(inp2, origin=(20.0, 0.0, 0.0), fill=5.0)
        rc = rtv.main([str(inp1), str(inp2), str(out)])
        assert rc == 0
        result = sitk.ReadImage(str(out))
        arr = sitk.GetArrayFromImage(result)
        assert arr.max() == pytest.approx(5.0, abs=0.1)

    def test_nearest_interpolator(self, tmp_path):
        inp = tmp_path / "in.nrrd"
        out = tmp_path / "out.nrrd"
        self._write_image(inp)
        rc = rtv.main(["-i", "nearest", str(inp), str(out)])
        assert rc == 0

    def test_no_inputs_returns_error(self, tmp_path):
        out = tmp_path / "out.nrrd"
        rc = rtv.main([str(out)])
        assert rc == 1

    def test_2d_input_promoted(self, tmp_path):
        img2d = sitk.Image(8, 8, sitk.sitkFloat32)
        img2d = img2d + 1.0
        inp = str(tmp_path / "slice.nrrd")
        out = str(tmp_path / "out.nrrd")
        sitk.WriteImage(img2d, inp)
        rc = rtv.main([inp, out])
        assert rc == 0
        result = sitk.ReadImage(out)
        assert result.GetDimension() == 3
