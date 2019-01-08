"""Reading and writing functions.
"""
import os
import numpy as np
from osgeo import gdal
from .core import Raster


def read_gdal(ds, band=None, **kwargs):
    """Read raster from :class:`gdal.Dataset`.

    Args:
        ds (gdal.Dataset): Dataset returned by :meth:`gdal.Open`.
        band (int or list): Band number

    Returns:
        :class:`Raster`
    """
    projection = kwargs.get('projection') or ds.GetProjection()
    transform = kwargs.get('transform') or ds.GetGeoTransform()

    if band is None:
        band = list(range(1, ds.RasterCount + 1))
    if isinstance(band, int):
        band = [band]

    rs = []
    for b in band:
        b = ds.GetRasterBand(b)
        array = b.ReadAsArray()
        kwargs.setdefault("nodatavalue", b.GetNoDataValue())
        r = Raster(array, transform, projection, **kwargs)
        del b, ds
        rs.append(r)
    if len(rs) == 1:
        return rs[0]
    else:
        return rs


def read(filepath, band=None, **kwargs):
    """Read rasters from files.

    Args:
        filepath (str): Raster files path.
        band (int or list): Band number.

    Returns:
        :class:`Raster` or a list of :class:`Raster`.
    """

    filepath = os.path.abspath(filepath)
    dataset = gdal.Open(filepath)
    name = dataset.GetDriver().ShortName

    if 'HDF' in name:
        subset = dataset.GetSubDatasets()
        if band is None:
            band = list(range(1, len(subset)+1))
        if isinstance(band, int):
            band = [band]

        rs = [read_gdal(gdal.Open(subset[b-1][0])) for b in band]
        if len(rs) == 1:
            return rs[0]
        else:
            return rs
    else:
        return read_gdal(dataset, band, filepath=filepath, **kwargs)


def save(raster, out_raster_path=None, dtype=None, compress=True):
    """save :class:`Raster` to GeoTIFF file or :class:`gdal.Dataset`.

    Args:
        raster (Raster or a list of Rasters): Save rasters to file. When it's a
            list or tuple of :class:`Raster`, save them all as multi bands
            in one file.
        out_raster_path (str): The output path. If it is ``None``,
            return a :class:`gdal.Dataset`.

        dtype (dtype): Save raster with specified data type.

        compress (int):
            |  Could be following options:
            |  ``compress=True`` (default) Use LZW to compress
            |  ``compress=False`` Do not compress
            |  ``compress='DEFAULT'``
            |  ``compress='PACKBITS'``
            |  ... other algorithms gdal supported

    Returns:
        `None` or `gdal.Dataset`
    """
    if isinstance(raster, Raster):
        raster = [raster]

    dtype = raster[0]._gdal_dtype()
    xsize = raster[0].shape[1]
    ysize = raster[0].shape[0]
    bands = len(raster)

    options = {}
    # Ignore compress option, if use ``MEM`` driver.
    compress = compress if out_raster_path else False
    if compress is True:
        options['COMPRESS'] = 'LZW'
    elif compress is not False:
        options['COMPRESS'] = compress

    options = ["{0}={1}".format(k, v) for k, v in options.items()]

    if out_raster_path:
        driver = gdal.GetDriverByName('GTiff')
        if not out_raster_path.endswith('.tif'):
            out_raster_path += '.tif'
    else:
        driver = gdal.GetDriverByName('MEM')
        out_raster_path = ''

    out_raster = driver.Create(
        out_raster_path, xsize, ysize, bands, dtype, options=options)

    out_raster.SetProjection(raster[0].projection)
    out_raster.SetGeoTransform(raster[0].transform)

    for i, r in enumerate(raster):
        out_band = out_raster.GetRasterBand(i+1)
        r.set_fill_value(r.fill_value)
        out_band.SetNoDataValue(np.float64(r.fill_value))
        out_band.WriteArray(r.filled())
        del out_band

    if driver.ShortName == "MEM":
        return out_raster
    else:
        del out_raster
