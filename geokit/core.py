# coding=utf-8
import numpy as np
from numpy.ma import MaskedArray
from osgeo import gdal, osr, ogr


# numpy数据类型到gdal数据类型的映射关系
TYPE = {
    np.dtype(np.int8): gdal.GDT_Byte,
    np.dtype(np.uint8): gdal.GDT_Byte,
    np.dtype(np.int16): gdal.GDT_Int16,
    np.dtype(np.uint16): gdal.GDT_UInt16,
    np.dtype(np.int32): gdal.GDT_Int32,
    np.dtype(np.uint32): gdal.GDT_UInt32,
    np.dtype(np.float32): gdal.GDT_Float32,
    np.dtype(np.float64): gdal.GDT_Float64,
    np.dtype(np.complex64): gdal.GDT_CFloat32,
    np.dtype(np.complex128): gdal.GDT_CFloat64,
}


class Raster(MaskedArray):
    """
    """
    def __new__(cls, array, transform, projection=None, a_srs="EPSG:4326",
                nodatavalue=None, mask=None):
        """
        """

        if projection is None:
            name, code = a_srs.split(":")
            name = name.upper()
            code = int(code)

            srs = osr.SpatialReference()
            if name.startswith("EPSG"):
                srs.ImportFromEPSG(code)
            elif name.startswith("ESRI"):
                srs.ImportFromESRI(code)

            projection = srs.ExportToWkt()

            del srs

        _raster_meta = {
            'projection': projection,
            'transform': transform,
        }

        if mask is not None:
            array = MaskedArray(array, mask=mask)

        if nodatavalue is not None:
            array = np.ma.masked_equal(array, nodatavalue)

        obj = super(Raster, cls).__new__(
            cls, array, fill_value=nodatavalue
        )

        setattr(obj, '_raster_meta', _raster_meta)
        return obj

    @property
    def projection(self):
        return self._raster_meta['projection']

    @projection.setter
    def projection(self, value):
        self._raster_meta['projection'] = value

    @property
    def transform(self):
        return self._raster_meta['transform']

    @transform.setter
    def transform(self, value):
        self._raster_meta['transform'] = value

    def _gdal_dtype(self):
        if self.dtype in TYPE:
            dtype = TYPE[self.dtype]
            return dtype
        else:
            raise 'Cannot convert {} into gdal.'.format(self.dtype)

    def get_point(self, x, y):
        """获取距离给定(x, y)坐标最近的点值

        Args:
            x (int): 纵轴
            y (int): 横轴
        """
        origin_x = self._raster_meta['transform'][3]
        origin_y = self._raster_meta['transform'][0]
        pixel_x = self._raster_meta['transform'][5]
        pixel_y = self._raster_meta['transform'][1]

        return self[
            int((x - origin_x) / pixel_x),
            int((y - origin_y) / pixel_y)
        ]

    def _update_from(self, obj):
        self.__dict__.update(
            {"_raster_meta": getattr(obj, '_raster_meta', None)})
        super(Raster, self)._update_from(obj)
        return

    def save(self, out_raster_path=None, dtype=None, compress=True):
        """将Raster对象输出存储为GeoTIFF文件或gdal.Dataset对象

        Args:
            out_raster_path (str):
                输出文件路径，若为None则返回gdal.Dataset对象

            dtype (dtype): 输出时所使用的数据类型
                默认为目前所使用的数据类型进行存储，
                通过dtype转换为指定的数据类型进行存储

            compress (int):
                |  存储时进行压缩, 有以下几种选项
                |  compress=True(default) 使用LZW算法进行压缩
                |  compress=False 不进行压缩
                |  compress='DEFAULT' 使用gdal默认算法进行压缩
                |  compress='PACKBITS' 使用gdal的PACKBITS算法进行压缩
                |  ... 或其他gdal支持的压缩算法

        Returns:
            None or gdal.Dataset
        """
        raster = self

        # 查找与numpy数据类型对应的gdal数据类型
        dtype = self._gdal_dtype()

        options = {}
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
            out_raster_path,
            raster.shape[1], raster.shape[0], 1, dtype, options=options)

        out_raster.SetProjection(raster.projection)
        out_raster.SetGeoTransform(raster.transform)
        out_band = out_raster.GetRasterBand(1)
        out_band.SetNoDataValue(np.float64(raster.fill_value))
        out_band.WriteArray(raster.filled())

        if driver.ShortName == "MEM":
            return out_raster
        else:
            del out_band, out_raster

    def zonal_apply(self, func, shp_path):
        """"""
        mem_shp_driver = ogr.GetDriverByName("Memory")

        shp = ogr.Open(shp_path)

        fid = []
        result = []
        for feature in shp.GetLayer():
            tmp_shp = mem_shp_driver.CreateDataSource("")
            srs = osr.SpatialReference()
            srs.ImportFromWkt(self._raster_meta['projection'])
            tmp_layer = tmp_shp.CreateLayer("tmp", srs)
            tmp_layer.CreateFeature(feature.Clone())

            tmp_raster = self._clip(tmp_layer)
            fid.append(feature.GetFID())
            result.append(func(tmp_raster))

        return fid, result

    def clip(self, shp_path):
        """根据给定的shapefile剪切栅格"""
        shp = ogr.Open(shp_path)
        return self._clip(shp.GetLayer())

    def _clip(self, layer):
        """根据给定的layer剪切栅格"""
        # TODO 转换layer投影到栅格投影
        mem_raster_driver = gdal.GetDriverByName("MEM")

        tmp_raster = mem_raster_driver.Create(
            "", self.shape[1], self.shape[0], 1, gdal.GDT_Byte)
        tmp_raster.SetProjection(self._raster_meta['projection'])
        tmp_raster.SetGeoTransform(self._raster_meta['transform'])
        tmp_raster.GetRasterBand(1).SetNoDataValue(0)
        tmp_raster.GetRasterBand(1).Fill(0)

        gdal.RasterizeLayer(tmp_raster, [1], layer, burn_values=[1])

        mask = np.ma.masked_equal(
            tmp_raster.ReadAsArray(), 0).mask

        return np.ma.masked_array(self, mask)

    def reproject(self, x_count, y_count,
                  transform=None, projection=None, method=gdal.GRA_Bilinear):
        """重投影/重采样

        Args:
            x_count (int): RasterXSize 目标数据一行的像素点数
            y_count (int): RasterYSize 目标数据一列的像素点数
            transform (list): 默认使用原栅格数据的transform
            projection: 默认使用原栅格数据的projection
            method (int): 
                |  重投影/采样时所使用的算法
                |  gdal.GRA_Bilinear (default)
                |  gdal.GRA_Average
                |  gdal.GRA_Cubic
                |  gdal.GRA_CubicSpline
                |  gdal.GRA_Lanczos
                |  gdal.GRA_NearestNeighbour

        Returns:
            Raster对象
        """
        mem_raster_driver = gdal.GetDriverByName("MEM")
        tmp_raster = mem_raster_driver.Create(
            "", x_count, y_count, 1, self._gdal_dtype()
        )

        if transform is None:
            transform = self.transform

        if projection is None:
            projection = self.projection

        tmp_raster.SetProjection(projection)
        tmp_raster.SetGeoTransform(transform)
        tmp_band = tmp_raster.GetRasterBand(1)
        tmp_band.SetNoDataValue(np.float64(self.fill_value))
        tmp_band.Fill(self.fill_value)

        gdal.ReprojectImage(
            self.save(), tmp_raster,
            self.projection, projection, method)

        array = tmp_band.ReadAsArray()

        del tmp_band, tmp_raster
        return Raster(
            array, transform,
            projection, nodatavalue=self.fill_value)

    def plot(self, ax=None, cmap_name='seismic', if_show=False):
        """使用matplotlib绘制预览图

        Args:
            ax: 给定绘图的目标Axes，若为None则在当前默认Axes上进行绘制

            cmap_name (str): 图像所使用的color map名，可参考:
                https://matplotlib.org/examples/color/colormaps_reference.html

            if_show (bool):
                绘制后是否调用plt.show()进行显示，默认为False,绘制后不进行任何动作
        """
        import matplotlib.pylab as plt
        from matplotlib.ticker import FuncFormatter

        if ax is None:
            ax = plt.gca()
        plt.sca(ax)

        plt.imshow(self, cmap=plt.get_cmap(cmap_name))

        def ticker(origin, pixel_size):
            def _ticker(t, pos):
                return round(origin + t * pixel_size, 3)
            return _ticker

        ax.xaxis.set_major_formatter(FuncFormatter(
            ticker(
                self._raster_meta['transform'][0],
                self._raster_meta['transform'][1]
            )
        ))
        ax.yaxis.set_major_formatter(FuncFormatter(
            ticker(
                self._raster_meta['transform'][3],
                self._raster_meta['transform'][5]
            )
        ))

        plt.colorbar()

        if if_show:
            plt.show()

    def show(self, **kwargs):
        """self.plot方法的快捷方式，直接调用plt.show显示绘制的图像进行简单的预览查看
        """
        self.plot(**kwargs, if_show=True)
