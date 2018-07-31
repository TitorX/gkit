"""Reading and writing functions.
"""
from osgeo import gdal
from .core import Raster


def read_gdal(raster, layer_num=1):
    """read raster from gdal.Dataset

    Args:
        raster (gdal.Dataset): returned by gdal.Open
        layer_num (int): layer number wanted to loaded

    Returns:
        Raster
    """
    band = raster.GetRasterBand(layer_num)
    projection = raster.GetProjection()
    transform = raster.GetGeoTransform()
    array = band.ReadAsArray()

    obj = Raster(
        array, transform, projection,
        nodatavalue=band.GetNoDataValue()
    )

    del band, raster
    return obj


def read_geotiff(raster_path, layer_num=1):
    """read GeoTIFF file

    Args:
        raster_path (str): 已经打开的gdal栅格对象或要加载的栅格数据文件路径
        layer_num (int): layer number wanted to loaded

    Returns:
        Raster
    """
    raster_path = raster_path if raster_path.endswith(".tif") \
        else raster_path + ".tif"
    raster = gdal.Open(raster_path)

    return read_gdal(raster)
