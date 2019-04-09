"""Reading and writing functions.
"""
import os
import numpy as np
from osgeo import gdal
from .core import Raster


def read_gdal(ds, band=None, **kwargs):
    """Read raster from :class:`gdal.Dataset`.

    Args:
        ds (gdal.Dataset): :class:`gdal.Dataset`.
        band (int or list):
            |  Band number (read all bands by default)
            |  Should be a int or list to read one or more bands.
            |  Bands are numbered starting from 1.

    Returns:
        :class:`Raster` or a list of :class:`Raster`.
    """
    kwargs.setdefault("projection", ds.GetProjection())
    kwargs.setdefault("transform", ds.GetGeoTransform())

    if band is None:
        band = np.arange(1, ds.RasterCount + 1) or \
            np.arange(1, len(ds.GetSubDatasets()) + 1)
    elif isinstance(band, int):
        band = np.array([band])
    else:
        band = np.array(band)

    assert (band >= 1).all(), "Bands number are starting from 1." \
        "{} contains invalid bands number.".format(band)

    if ds.RasterCount:
        data = []
        for b in band:
            b = ds.GetRasterBand(int(b))
            array = b.ReadAsArray()
            kwargs.setdefault("nodatavalue", b.GetNoDataValue())
            r = Raster(array, **kwargs)
            data.append(r)
    else:
        subset = ds.GetSubDatasets()
        if not len(band):
            band = np.arange(1, len(subset) + 1)
        data = [
            read_gdal(gdal.Open(subset[b-1][0]), 1, **kwargs)
            for b in band
        ]

    if len(data) == 1:
        return data[0]
    else:
        return data


def read(filepath, band=None, **kwargs):
    """Read rasters from file.

    Args:
        filepath (str): Raster file path.
        band (int or list):
            |  Band number (read all bands by default)
            |  Should be a int or list to read one or more bands.
            |  Bands are numbered starting from 1.

    Returns:
        :class:`Raster` or a list of :class:`Raster`.
    """
    ds = gdal.Open(filepath)
    filepath = os.path.abspath(ds.GetFileList()[0])
    return read_gdal(ds, band, filepath=filepath, **kwargs)


def save(raster, out_path=None, driver_name="GTiff",
         compress=False, options=None):
    """save :class:`Raster` to GeoTIFF file or :class:`gdal.Dataset`.

    Args:
        raster (Raster or a list of Rasters): Save rasters to file. When it's a
            list or tuple of :class:`Raster`, save them all as multi bands
            in one file.
        out_path (str): The output path. If it is ``None``,
            return a :class:`gdal.Dataset`.(use MEM driver)
        driver_name (str): Use which driver to save.(default="GTiff")
        compress (int):
            |  Could be following options:
            |  ``compress=True``  Use LZW to compress
            |  ``compress=False`` (default) Do not compress
            |  ``compress='DEFAULT'``
            |  ``compress='PACKBITS'``
            |  ... other algorithms gdal supported

    Returns:
        `None` or `gdal.Dataset`
    """
    if isinstance(raster, Raster):
        raster = [raster]

    dtype = raster[0]._gdal_dtype()
    xsize, ysize = raster[0].shape[1], raster[0].shape[0]
    bands = len(raster)
    projection = raster[0].projection
    transform = raster[0].transform

    options = options or {}
    # Ignore compress option, if use ``MEM`` driver.
    compress = compress if out_path else False
    if compress is True:
        options['COMPRESS'] = 'LZW'
    elif isinstance(compress, str):
        options['COMPRESS'] = compress

    if out_path:
        driver = gdal.GetDriverByName(driver_name)
    else:
        driver = gdal.GetDriverByName('MEM')
        out_path = ''

    options = ["{0}={1}".format(k, v) for k, v in options.items()]
    out_raster = driver.Create(
        out_path, xsize, ysize, bands, dtype, options=options)

    out_raster.SetProjection(projection)
    out_raster.SetGeoTransform(transform)

    for i, r in enumerate(raster):
        out_band = out_raster.GetRasterBand(i+1)
        r.set_fill_value()  # Make sure fill value is correct.
        # Nodata value must be float type.
        out_band.SetNoDataValue(np.float64(r.fill_value))
        out_band.WriteArray(r.filled())
        del out_band

    if driver.ShortName == "MEM":
        return out_raster
    else:
        del out_raster
