"""Reading and writing functions.
"""
import os
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

        r = Raster(
            array, transform, projection,
            nodatavalue=b.GetNoDataValue(),
            **kwargs
        )
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


def read_geotiff(filepath, band=None, **kwargs):
    """Read GeoTIFF file.

    Args:
        filepath (str): GeoTIFF file path.
        band (int): Band number.

    Returns:
        :class:`Raster`
    """
    filepath = filepath if filepath.endswith(".tif") \
        else filepath + ".tif"
    filepath = os.path.abspath(filepath)
    raster = gdal.Open(filepath)

    return read_gdal(raster, band, filepath=filepath, **kwargs)
