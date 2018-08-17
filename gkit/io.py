"""Reading and writing functions.
"""
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


def read_geotiff(raster_path, layer_num=1, **kwargs):
    """Read GeoTIFF file.

    Args:
        raster_path (str): GeoTIFF file path.
        layer_num (int): Layer number wanted to loaded.

    Returns:
        :class:`Raster`
    """
    raster_path = raster_path if raster_path.endswith(".tif") \
        else raster_path + ".tif"
    raster = gdal.Open(raster_path)

    return read_gdal(raster, layer_num, **kwargs)
