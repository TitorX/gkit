import numpy as np
from numpy.ma import MaskedArray
from osgeo import gdal, osr, ogr
from scipy.ndimage.filters import generic_filter as gf


# Data type mapping between numpy and gdal.
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


def split_by_shp(rasters, shp, by=None, overall=False):
    rasters = list(rasters)
    shp = ogr.Open(shp)
    result = []
    if overall:
        result.append(['overall', *[r.copy() for r in rasters]])

    for feature in shp.GetLayer():
        result.append([
            feature[by] if by else feature.GetFID(),
            *[r.clip_by_feature(feature) for r in rasters]
        ])
    return np.array(result, dtype=object)


def zonal_apply(rasters, shp, func, by=None, overall=False,
                args=(), kwargs={}):

    splited = split_by_shp(rasters, shp, by, overall)

    result = []
    for i, *r in splited:
        result.append([
            i, func(*r, *args, **kwargs)
        ])
    return np.array(result)


class Raster(MaskedArray):
    """
    """
    def __new__(cls, array, transform, projection=None, a_srs="EPSG:4326",
                nodatavalue=None, mask=None, filepath=None):
        """"""

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
            'transform': tuple(transform),
        }

        array = np.ma.masked_invalid(array)

        if mask is not None:
            array = MaskedArray(array, mask=mask)

        if nodatavalue is not None:
            array = np.ma.masked_equal(array, nodatavalue)

        obj = super(Raster, cls).__new__(
            cls, array, fill_value=nodatavalue
        )

        if filepath is not None:
            filepath = str(filepath)
        setattr(obj, 'filepath', filepath)
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
        self._raster_meta['transform'] = tuple(value)

    @property
    def extent(self):
        """The extent of raster in current coordinates."""
        left = self.transform[0]
        right = left + self.transform[1] * self.shape[1]
        top = self.transform[3]
        bottom = top + self.transform[5] * self.shape[0]
        return [left, right, bottom, top]

    def _gdal_dtype(self):
        if self.dtype in TYPE:
            dtype = TYPE[self.dtype]
            return dtype
        else:
            raise 'Cannot convert {} into gdal.'.format(self.dtype)

    def get_point_value(self, x, y):
        """Get point value by coordinate.

        Args:
            x (int): The X coordinate of the point.
            y (int): The Y coordinate of the point.
        """
        origin_x = self._raster_meta['transform'][3]
        origin_y = self._raster_meta['transform'][0]
        pixel_x = self._raster_meta['transform'][5]
        pixel_y = self._raster_meta['transform'][1]

        res = self[
            int((x - origin_x) / pixel_x),
            int((y - origin_y) / pixel_y)
        ]

        if np.ma.is_masked(res):
            return np.nan
        else:
            return res

    def _update_from(self, obj):
        self.__dict__.update({
            "_raster_meta": getattr(obj, '_raster_meta', None),
            "filepath": getattr(obj, 'filepath', None)
        })
        super(Raster, self)._update_from(obj)
        return

    def set_fill_value(self, value=None):
        """"""
        info = np.iinfo if self.dtype.kind == "i" else np.finfo
        max_value = info(self.dtype).max
        min_value = info(self.dtype).min
        if value is None:
            super(Raster, self).set_fill_value(max_value)
        else:
            value = min(max_value, max(min_value, value))
            super(Raster, self).set_fill_value(value)

    def save(self, out_raster_path=None, dtype=None, compress=True):
        """save :class:`Raster` to GeoTIFF file or :class:`gdal.Dataset`.

        Args:
            out_raster_path (str): The output path. If it is ``None``,
                return :class:`gdal.Dataset`.

            dtype (dtype): Save raster as specified data type.

            compress (int):
                |  Could be following options:
                |  ``compress=True`` (default) Use LZW to compress
                |  ``compress=False`` Do not compress
                |  ``compress='DEFAULT'``
                |  ``compress='PACKBITS'``
                |  ... other algorithms that gdal supported

        Returns:
            `None` or `gdal.Dataset`
        """
        raster = self

        dtype = self._gdal_dtype()

        options = {}
        # Ignore compress option, if ``MEM`` driver are used.
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
            out_raster_path,
            raster.shape[1], raster.shape[0], 1, dtype, options=options)

        out_raster.SetProjection(raster.projection)
        out_raster.SetGeoTransform(raster.transform)
        out_band = out_raster.GetRasterBand(1)
        raster.set_fill_value(raster.fill_value)
        out_band.SetNoDataValue(np.float64(raster.fill_value))
        out_band.WriteArray(raster.filled())

        if driver.ShortName == "MEM":
            return out_raster
        else:
            del out_band, out_raster

    def clip_by_layer(self, layer):
        """Clip raster by layer."""

        # TODO Convert layer's projection into raster's projection when
        # they have different projection.
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

        array = np.ma.masked_array(self, mask)
        return Raster(array, self.transform, self.projection)

    def clip_by_shp(self, shp_path):
        """Clip raster by shapefile."""
        shp = ogr.Open(shp_path)
        return self.clip_by_layer(shp.GetLayer())

    def clip_by_feature(self, feature):
        """Clip raster by a feature."""
        mem_shp_driver = ogr.GetDriverByName("Memory")
        tmp_shp = mem_shp_driver.CreateDataSource("")
        srs = osr.SpatialReference()
        srs.ImportFromWkt(self.projection)
        tmp_layer = tmp_shp.CreateLayer("tmp", srs)
        tmp_layer.CreateFeature(feature.Clone())

        return self.clip_by_layer(tmp_layer)

    def split_by_shp(self, shp, by=None, overall=False):
        return split_by_shp([self], shp, by, overall)

    def zonal_apply(self, shp_path, func, by=None, overall=False,
                    args=(), kwargs={}):
        """"""
        return zonal_apply([self], shp_path, func, by, overall, args, kwargs)

    def reproject(self, x_count=None, y_count=None,
                  transform=None, projection=None, method=gdal.GRA_Bilinear):
        """Reproject/Resample

        Args:
            x_count (int): Row count. (``RasterXSize``)
            y_count (int): Column count. (``RasterYSize``)
            transform (list): Use current transform in default.
            projection: Use current projection in default.
            method (int):
                |  Could be following options:
                |  ``gdal.GRA_Bilinear`` (default)
                |  ``gdal.GRA_Average``
                |  ``gdal.GRA_Cubic``
                |  ``gdal.GRA_CubicSpline``
                |  ``gdal.GRA_Lanczos``
                |  ``gdal.GRA_NearestNeighbour``

        Returns:
            :class:`Raster`
        """
        mem_raster_driver = gdal.GetDriverByName("MEM")
        tmp_raster = mem_raster_driver.Create(
            "", x_count, y_count, 1, self._gdal_dtype()
        )

        x_count = x_count or self.shape[1]
        y_count = y_count or self.shape[0]
        transform = transform or self.transform
        projection = projection or self.projection

        tmp_raster.SetProjection(projection)
        tmp_raster.SetGeoTransform(transform)
        tmp_band = tmp_raster.GetRasterBand(1)
        tmp_band.SetNoDataValue(np.float64(self.fill_value))
        tmp_band.Fill(np.float64(self.fill_value))

        gdal.ReprojectImage(
            self.save(), tmp_raster,
            self.projection, projection, method)

        array = tmp_band.ReadAsArray()

        del tmp_band, tmp_raster
        return Raster(
            array, transform,
            projection, nodatavalue=self.fill_value)

    def resample(self, x_count=None, y_count=None,
                 transform=None, method=None):
        """Alias of :meth:`self.reproject`. The only difference is that
        :meth:`resample` cannot change the projection of raster.
        """
        return self.reproject(x_count, y_count, transform, method=method)

    def plot(self, ax=None, cmap_name='seismic', if_show=False):
        """Use ``matplotlib`` to plot preview picture

        Args:
            ax: The ``Axes`` instance. If it's ``None``, use the current
                ``Axes`` instance.

            cmap_name (str): color map name, reference:
                https://matplotlib.org/examples/color/colormaps_reference.html

            if_show (bool): If call :meth:`plt.show` after ploting.
        """
        import matplotlib.pylab as plt

        if ax is None:
            ax = plt.gca()
        plt.sca(ax)

        plt.imshow(
            self, cmap=plt.get_cmap(cmap_name),
            extent=self.extent
        )

        plt.colorbar(orientation='horizontal')

        if if_show:
            plt.show()

    def show(self, *args, **kwargs):
        """A shortcut of :meth:`self.plot`. Just set ``if_show=True``.
        """
        kwargs['if_show'] = True
        self.plot(*args, **kwargs)

    def rolling(self, function, size=None, footprint=None, mode='reflect',
                cval=0.0):
        """Calculate a 2D filter using the given function.

        At each element the provided function is called. The input values
        within the filter footprint at that element are passed to the function
        as a 1D array of double values.

        Args:
            function (callable, str): Function to apply at each element.
            size (scalar, tuple): See foorprint, below.
                Ignored if footprint is given.
            footprint (array, str):
                |  Either `size` or `footprint` must be defined. `size` gives
                    the shape that is taken from the input array, at every
                    element position, to define the input to the filter
                    function.
                |  `footprint` is a boolean array that specifies (implicitly) a
                    shape, but also which of the elements within this shape
                    will get passed to the filter function.
                |  When `footprint` is given, `size` is ignored.
            mode (str):
                |  The `mode` parameter determines how the input array is
                    extended when the filter overlaps a border. By passing a
                    sequence of modes with length equal to the number of
                    dimensions of the input array, different modes can be
                    specified along each axis. Default value is 'reflect'.
                    The valid values and their behavior is as follows:

                |  'reflect' (`d c b a | a b c d | d c b a`) The input is
                    extended by reflecting about the edge of the last pixel.
                |  'constant' (`k k k k | a b c d | k k k k`) The input is
                    extended by filling all values beyond the edge with the
                    same constant value, defined by the `cval` parameter.
                |  'nearest' (`a a a a | a b c d | d d d d`) The input is
                    extended by replicating the last pixel.
                |  'mirror' (`d c b | a b c d | c b a`) The input is extended
                    by reflecting about the center of the last pixel.
                |  'wrap' (`a b c d | a b c d | a b c d`) The input is extended
                    by wrapping around to the opposite edge.
            cval (scalar): Value to fill past edges of input if `mode` is
                'constant'. Default is 0.0.

        Returns:
            :class:`Raster`
        """
        res = gf(
            self.filled(np.nan), function, size, footprint,
            mode=mode, cval=cval)
        return Raster(res, self.transform, self.projection, mask=self.mask)

    # def __str__(self):
    #     return self.__repr__()
    #
    # def __repr__(self):
    #     # projection_name = osr.SpatialReference(
    #     #     wkt=self.projection).GetAttrValue('geogcs')
    #     return "{}*{}".format(*self.shape)
