# coding=utf-8
from osgeo import gdal
from .core import Raster


def load():
    pass


def read_geotiff(in_raster, layer_num=1):
    """载入GeoTIFF文件

    Args:
        in_raster: 已经打开的gdal栅格对象或要加载的栅格数据文件路径
        band_num: 要加载的波段编号，默认为1，加载第一个波段的数据

    Returns:
        Raster对象
    """
    in_raster = in_raster if in_raster.endswith(".tif") \
        else in_raster + ".tif"
    raster = gdal.Open(in_raster)

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