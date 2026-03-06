# sitk_tools

A collection of Python utility scripts for medical image processing built on [SimpleITK](https://simpleitk.org/).

## Requirements

- Python 3.x
- [SimpleITK](https://simpleitk.readthedocs.io/en/master/gettingStarted.html) (`pip install SimpleITK`)
- NumPy (`pip install numpy`) — required by `histo.py`

## Scripts

### `bound_obj.py`
Find the bounding box of an object in a binary image.
```
python bound_obj.py <image> [threshold]
```

### `compareimages.py`
Compare two or more images by computing difference images and printing statistics (mean, min, max, sigma, sum).
```
python compareimages.py <image1> <image2> [image3 ...]
```

### `dicomseries.py`
Scan a directory for DICOM series and optionally convert them to other formats (default: `.nrrd`).
```
python dicomseries.py <directory>
python dicomseries.py --convert --suffix .nrrd --name desc <directory>
```

### `dictdump.py`
Dump the metadata dictionary of one or more image files.
```
python dictdump.py <image> [image2 ...]
```

### `extract_objects.py`
Extract the N largest connected objects from a binary mask image, with optional morphological cleanup.
```
python extract_objects.py <mask_image> [options]
```

### `extract_subimages.py`
Extract separate sub-images from a composite color image, assuming a black background.
```
python extract_subimages.py <image> [image2 ...]
```

### `hdr2mhd.py`
Convert a mouse scan header file (`.hdr` / `.img`) to MetaIO format (`.mhd`).
```
python hdr2mhd.py <header_file.hdr>
```

### `histo.py`
Compute and print the histogram of an image. Defaults to the Hounsfield unit range `[-1000, 2000]` for CT data.
```
python histo.py <image>
```

### `lmreg.py`
Perform landmark-based registration between a fixed and moving image using SimpleITK.
```
python lmreg.py --fixed <fixed_image> --moving <moving_image> \
                <fixed_points> <moving_points> [output_transform.tfm]
```
Point files should be in Elastix format (6-line files with 4 coordinate lines).

### `merge_slices.py`
Merge a directory of 2D slice images (e.g., nnUNet output) into a single 3D volume. Supports an optional pickle metadata file to restore original volume geometry.
```
python merge_slices.py <slice_dir> [metadata.pkl] [output.nii.gz]
```

### `paint_points.py`
Paint a list of 2D points (as filled squares) into a specified color channel of an image. Intended as a utility module imported by other scripts.

### `query_vol.py`
Print detailed information about a volume: size, spacing, origin, direction, physical bounds, and histogram.
```
python query_vol.py <image>
```

### `removemetadata.py`
Strip all metadata from an image and write the clean result to a new file.
```
python removemetadata.py [--verbose] <input_file> <output_file>
```

### `resizeVol.py`
Linearly resample a volume to a new voxel size. Unspecified dimensions are left unchanged.
```
python resizeVol.py <input> <output> <x> <y> <z>
```

### `show.py`
Display one or more images in Fiji/ImageJ via SimpleITK's `Show` function. Supports intensity scaling.
```
python show.py [--scale <factor>] <image> [image2 ...]
```

### `sitk_test.py`
A smoke-test script that prints Python and SimpleITK version information and exercises a few basic filters (Gaussian source, derivative, intensity rescale).

### `vector.py`
Utility library providing basic 3D vector math: `add`, `subtract`, `dot`, `scale`, `normalize`, `cross`, `length`.

## License

See [LICENSE](LICENSE).
