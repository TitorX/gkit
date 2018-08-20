"""Reading and writing functions.
"""
import os
from osgeo import gdal
from .core import Raster


def read_gdal(raster, layer_num=1, **kwargs):
    """Read raster from :class:`gdal.Dataset`.

    Args:
        raster (gdal.Dataset): Returned by :meth:`gdal.Open`.
        layer_num (int): Layer number wanted to loaded.

    Returns:
        :class:`Raster`
    """
    band = raster.GetRasterBand(layer_num)
    projection = kwargs.get('projection') or raster.GetProjection()
    transform = kwargs.get('transform') or raster.GetGeoTransform()
    array = band.ReadAsArray()

    obj = Raster(
        array, transform, projection,
        nodatavalue=band.GetNoDataValue(),
        **kwargs
    )

    del band, raster
    return obj


def read_geotiff(filepath, layer_num=1, **kwargs):
    """Read GeoTIFF file.

    Args:
        filepath (str): GeoTIFF file path.
        layer_num (int): Layer number wanted to loaded.

    Returns:
        :class:`Raster`
    """
    filepath = filepath if filepath.endswith(".tif") \
        else filepath + ".tif"
    filepath = os.path.abspath(filepath)
    raster = gdal.Open(filepath)

    return read_gdal(raster, layer_num, filepath=filepath, **kwargs)
