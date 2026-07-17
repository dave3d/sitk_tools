"""
Tests for resample_to_volume.py
"""
# pylint: disable=missing-function-docstring,missing-class-docstring

import argparse
from pathlib import Path

import pytest
import numpy as np
import SimpleITK as sitk

import resample_to_volume as rtv


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_image(  # pylint: disable=too-many-arguments,too-many-positional-arguments
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
        size, spacing, _, _ = rtv.compute_reference_grid([img], None)
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
        size, _, _, _ = rtv.compute_reference_grid([img_a, img_b], [1.0, 1.0, 1.0])
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
        return {
            "size": size,
            "spacing": spacing,
            "origin": (0.0, 0.0, 0.0),
            "direction": identity_direction(),
            "interpolator": sitk.sitkLinear,
            "default_value": 0.0,
        }

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
        g = {
            "size": (31, 10, 10),
            "spacing": (1.0, 1.0, 1.0),
            "origin": (0.0, 0.0, 0.0),
            "direction": identity_direction(),
            "interpolator": sitk.sitkLinear,
            "default_value": 0.0,
        }
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


# ---------------------------------------------------------------------------
# load_image – thickness parameter
# ---------------------------------------------------------------------------

class TestLoadImageThickness:
    def test_thickness_sets_z_spacing_for_2d(self, tmp_path):
        img2d = sitk.Image(8, 8, sitk.sitkFloat32)
        p = str(tmp_path / "slice.nrrd")
        sitk.WriteImage(img2d, p)
        loaded = rtv.load_image(p, thickness=3.5)
        assert loaded.GetSpacing()[2] == pytest.approx(3.5)

    def test_thickness_ignored_for_3d(self, tmp_path):
        img3d = make_image(size=(5, 5, 5), spacing=(1.0, 1.0, 2.0))
        p = str(tmp_path / "vol.nrrd")
        sitk.WriteImage(img3d, p)
        loaded = rtv.load_image(p, thickness=9.9)
        assert loaded.GetSpacing()[2] == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# _dicom_3d_geometry
# ---------------------------------------------------------------------------

class TestDicom3dGeometry:  # pylint: disable=protected-access
    def _img_with_tags(self, ipp=None, iop=None):
        img = sitk.Image(8, 8, sitk.sitkFloat32)
        if ipp is not None:
            img.SetMetaData("0020|0032", "\\".join(str(v) for v in ipp))
        if iop is not None:
            img.SetMetaData("0020|0037", "\\".join(str(v) for v in iop))
        return img

    def test_reads_ipp_as_origin(self):
        img = self._img_with_tags(ipp=(10.0, 20.0, 30.0))
        origin3d, _ = rtv._dicom_3d_geometry(img)
        assert origin3d == pytest.approx((10.0, 20.0, 30.0))

    def test_identity_iop_gives_identity_direction(self):
        img = self._img_with_tags(
            ipp=(0.0, 0.0, 0.0),
            iop=(1.0, 0.0, 0.0, 0.0, 1.0, 0.0),
        )
        _, direction3d = rtv._dicom_3d_geometry(img)
        assert direction3d == pytest.approx(
            (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
        )

    def test_nonidentity_iop_columns_are_physical_axis_directions(self):
        """Direction matrix columns must be the physical directions of image axes."""
        # row_cos = physical Z, col_cos = physical X → normal = physical Y
        img = self._img_with_tags(
            ipp=(0.0, 0.0, 0.0),
            iop=(0.0, 0.0, 1.0, 1.0, 0.0, 0.0),
        )
        _, d3d = rtv._dicom_3d_geometry(img)
        d = np.array(d3d).reshape(3, 3)
        assert d[:, 0] == pytest.approx([0.0, 0.0, 1.0], abs=1e-6)  # col 0 = row_cos
        assert d[:, 1] == pytest.approx([1.0, 0.0, 0.0], abs=1e-6)  # col 1 = col_cos
        assert d[:, 2] == pytest.approx([0.0, 1.0, 0.0], abs=1e-6)  # col 2 = normal

    def test_fallback_origin_when_ipp_absent(self):
        img = sitk.Image(8, 8, sitk.sitkFloat32)
        img.SetOrigin((5.0, 7.0))
        origin3d, _ = rtv._dicom_3d_geometry(img)
        assert origin3d == pytest.approx((5.0, 7.0, 0.0))

    def test_fallback_direction_when_iop_absent(self):
        img = sitk.Image(8, 8, sitk.sitkFloat32)
        img.SetMetaData("0020|0032", "0\\0\\0")
        _, direction3d = rtv._dicom_3d_geometry(img)
        assert direction3d == pytest.approx(
            (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
        )


# ---------------------------------------------------------------------------
# _covered_z_planes
# ---------------------------------------------------------------------------

class TestCoveredZPlanes:  # pylint: disable=protected-access
    def _grid(self, nz=20, sz=1.0):
        return {
            "size": (8, 8, nz),
            "spacing": (1.0, 1.0, sz),
            "origin": (0.0, 0.0, 0.0),
            "direction": identity_direction(),
        }

    def _slice_at_z(self, z):
        return make_image(size=(8, 8, 1), spacing=(1.0, 1.0, 1.0),
                          origin=(0.0, 0.0, z))

    def test_single_slice_at_origin(self):
        covered = rtv._covered_z_planes([self._slice_at_z(0.0)], **self._grid())
        assert covered == [0]

    def test_slice_maps_to_correct_plane(self):
        covered = rtv._covered_z_planes([self._slice_at_z(7.0)], **self._grid())
        assert covered == [7]

    def test_multiple_slices_all_present(self):
        slices = [self._slice_at_z(z) for z in (0.0, 5.0, 10.0)]
        covered = rtv._covered_z_planes(slices, **self._grid())
        assert covered == [0, 5, 10]

    def test_out_of_bounds_slice_excluded(self):
        covered = rtv._covered_z_planes([self._slice_at_z(100.0)], **self._grid())
        assert covered == []

    def test_result_is_sorted(self):
        slices = [self._slice_at_z(z) for z in (10.0, 0.0, 5.0)]
        covered = rtv._covered_z_planes(slices, **self._grid())
        assert covered == sorted(covered)

    def test_non_unit_z_spacing(self):
        covered = rtv._covered_z_planes(
            [self._slice_at_z(5.0)], **self._grid(sz=2.5)
        )
        assert covered == [2]   # 5.0 / 2.5 = 2


# ---------------------------------------------------------------------------
# fill_slice_gaps
# ---------------------------------------------------------------------------

class TestFillSliceGaps:
    def _vol(self, nz=5, ny=4, nx=4):
        img = sitk.Image(nx, ny, nz, sitk.sitkFloat32)
        img.SetSpacing((1.0, 1.0, 1.0))
        return img

    def _set_plane(self, img, k, value):
        arr = sitk.GetArrayFromImage(img).astype(np.float32)
        arr[k] = value
        result = sitk.GetImageFromArray(arr)
        result.CopyInformation(img)
        return result

    def test_empty_covered_returns_volume_unchanged(self):
        vol = self._set_plane(self._vol(), 2, 5.0)
        result = rtv.fill_slice_gaps(vol, [], 0.0)
        arr = sitk.GetArrayFromImage(result)
        assert arr[2, 0, 0] == pytest.approx(5.0)

    def test_all_planes_covered_values_unchanged(self):
        vol = self._vol(nz=3)
        for k, v in enumerate((1.0, 2.0, 3.0)):
            vol = self._set_plane(vol, k, v)
        result = rtv.fill_slice_gaps(vol, [0, 1, 2], 0.0)
        arr = sitk.GetArrayFromImage(result)
        assert arr[0, 0, 0] == pytest.approx(1.0)
        assert arr[1, 0, 0] == pytest.approx(2.0)
        assert arr[2, 0, 0] == pytest.approx(3.0)

    def test_midpoint_interpolation(self):
        """Plane 1 gaps between val=0 at k=0 and val=2 at k=2 → expects 1."""
        vol = self._vol(nz=3)
        vol = self._set_plane(vol, 0, 0.0)
        vol = self._set_plane(vol, 2, 2.0)
        result = rtv.fill_slice_gaps(vol, [0, 2], 0.0)
        arr = sitk.GetArrayFromImage(result)
        assert arr[1, 0, 0] == pytest.approx(1.0)

    def test_weighted_interpolation_across_four_gaps(self):
        """Planes 1-3 between k=0 (val=0) and k=4 (val=4) must be 1, 2, 3."""
        vol = self._vol(nz=5)
        vol = self._set_plane(vol, 0, 0.0)
        vol = self._set_plane(vol, 4, 4.0)
        result = rtv.fill_slice_gaps(vol, [0, 4], 0.0)
        arr = sitk.GetArrayFromImage(result)
        assert arr[1, 0, 0] == pytest.approx(1.0)
        assert arr[2, 0, 0] == pytest.approx(2.0)
        assert arr[3, 0, 0] == pytest.approx(3.0)

    def test_extrapolation_below_copies_nearest(self):
        """Planes before the first covered plane duplicate it (no extrapolation)."""
        vol = self._vol(nz=5)
        vol = self._set_plane(vol, 3, 7.0)
        vol = self._set_plane(vol, 4, 9.0)
        result = rtv.fill_slice_gaps(vol, [3, 4], 0.0)
        arr = sitk.GetArrayFromImage(result)
        for k in (0, 1, 2):
            assert arr[k, 0, 0] == pytest.approx(7.0)

    def test_extrapolation_above_copies_nearest(self):
        """Planes after the last covered plane duplicate it."""
        vol = self._vol(nz=5)
        vol = self._set_plane(vol, 0, 3.0)
        vol = self._set_plane(vol, 1, 5.0)
        result = rtv.fill_slice_gaps(vol, [0, 1], 0.0)
        arr = sitk.GetArrayFromImage(result)
        for k in (2, 3, 4):
            assert arr[k, 0, 0] == pytest.approx(5.0)

    def test_covered_planes_not_modified(self):
        vol = self._vol(nz=5)
        vol = self._set_plane(vol, 0, 10.0)
        vol = self._set_plane(vol, 4, 20.0)
        result = rtv.fill_slice_gaps(vol, [0, 4], 0.0)
        arr = sitk.GetArrayFromImage(result)
        assert arr[0, 0, 0] == pytest.approx(10.0)
        assert arr[4, 0, 0] == pytest.approx(20.0)

    def test_metadata_preserved(self):
        vol = self._vol()
        vol.SetSpacing((2.0, 2.0, 3.0))
        vol.SetOrigin((1.0, 2.0, 3.0))
        result = rtv.fill_slice_gaps(vol, [0, 4], 0.0)
        assert result.GetSpacing() == pytest.approx((2.0, 2.0, 3.0))
        assert result.GetOrigin() == pytest.approx((1.0, 2.0, 3.0))


# ---------------------------------------------------------------------------
# Helpers for DICOM tests
# ---------------------------------------------------------------------------

@pytest.fixture
def dicom_series_dir(tmp_path):
    """Write a 3-slice DICOM series at z = 0, 5, 10 mm.

    Uses KeepOriginalImageUIDOn so all three files keep the same Series
    Instance UID and are recognised as one series by GetGDCMSeriesIDs.
    """
    series_uid = "1.2.826.0.1.3680043.2.1125.1"
    study_uid  = "1.2.826.0.1.3680043.2.1125.0"

    try:
        for i, z in enumerate([0.0, 5.0, 10.0]):
            img = sitk.Image(8, 8, sitk.sitkUInt16)
            img = img + (i * 50)   # distinct fill per slice
            img.SetMetaData("0008|0016", "1.2.840.10008.5.1.4.1.1.2")
            img.SetMetaData("0008|0018", f"{series_uid}.{i+1:04d}")
            img.SetMetaData("0008|0060", "CT")
            img.SetMetaData("0020|000d", study_uid)
            img.SetMetaData("0020|000e", series_uid)
            img.SetMetaData("0020|0013", str(i + 1))
            img.SetMetaData("0020|0032", f"0.0\\0.0\\{z:.1f}")
            img.SetMetaData("0020|0037", "1.0\\0.0\\0.0\\0.0\\1.0\\0.0")
            img.SetMetaData("0018|0050", "2.0")
            w = sitk.ImageFileWriter()
            w.KeepOriginalImageUIDOn()
            w.SetFileName(str(tmp_path / f"slice{i:04d}.dcm"))
            w.Execute(img)
    except (RuntimeError, OSError) as exc:
        pytest.skip(f"DICOM write unavailable: {exc}")

    return str(tmp_path)


# ---------------------------------------------------------------------------
# load_dicom_slices
# ---------------------------------------------------------------------------

class TestLoadDicomSlices:  # pylint: disable=redefined-outer-name
    def test_returns_correct_slice_count(self, dicom_series_dir):
        slices = rtv.load_dicom_slices(dicom_series_dir)
        assert len(slices) == 3

    def test_slices_are_single_slice_3d(self, dicom_series_dir):
        for s in rtv.load_dicom_slices(dicom_series_dir):
            assert s.GetDimension() == 3
            assert s.GetSize()[2] == 1

    def test_origins_match_ipp_tags(self, dicom_series_dir):
        slices = rtv.load_dicom_slices(dicom_series_dir)
        z_origins = sorted(s.GetOrigin()[2] for s in slices)
        assert z_origins == pytest.approx([0.0, 5.0, 10.0], abs=0.01)

    def test_thickness_from_dicom_tag(self, dicom_series_dir):
        for s in rtv.load_dicom_slices(dicom_series_dir):
            assert s.GetSpacing()[2] == pytest.approx(2.0)

    def test_thickness_override(self, dicom_series_dir):
        for s in rtv.load_dicom_slices(dicom_series_dir, thickness=4.0):
            assert s.GetSpacing()[2] == pytest.approx(4.0)

    def test_raises_for_directory_with_no_dicom(self, tmp_path):
        with pytest.raises(ValueError, match="No DICOM series found"):
            rtv.load_dicom_slices(str(tmp_path))


# ---------------------------------------------------------------------------
# main – DICOM path
# ---------------------------------------------------------------------------

class TestMainDicom:  # pylint: disable=redefined-outer-name
    def test_dicom_dir_produces_3d_output(self, dicom_series_dir, tmp_path):
        out = str(tmp_path / "out.nrrd")
        rc = rtv.main(["-D", dicom_series_dir, "-s", "1.0", out])
        assert rc == 0
        result = sitk.ReadImage(out)
        assert result.GetDimension() == 3

    def test_gap_is_filled_by_interpolation(self, dicom_series_dir, tmp_path):
        """Slices at z=0 (fill=0) and z=10 (fill=100); z=5 plane must be ~50."""
        # Remove the middle slice (z=5) to create an actual gap.
        (Path(dicom_series_dir) / "slice0001.dcm").unlink()

        out = str(tmp_path / "out.nrrd")
        rtv.main(["-D", dicom_series_dir, "-s", "1.0", out])
        arr = sitk.GetArrayFromImage(sitk.ReadImage(out))
        mid = arr.shape[0] // 2
        assert arr[mid, 0, 0] == pytest.approx(50.0, abs=1.0)

    def test_dicom_only_needs_output_positional_arg(self, dicom_series_dir, tmp_path):
        """When -D is given, a single positional arg (output) is enough."""
        out = str(tmp_path / "out.nrrd")
        rc = rtv.main(["-D", dicom_series_dir, out])
        assert rc == 0
