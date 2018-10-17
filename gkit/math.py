"""Wrapping some math functions from numpy, make it
work fine with :class:`Raster`.
"""
import warnings

import numpy as np

from .core import Raster


def agg_func(f):
    """Aggregation functions wrapper."""
    def func(rasters, axis=0, *args, **kwargs):
        """Wrapped numpy functions. Get more information by seeing
        the corresponding item in ``numpy.ma``.
        """
        projections = set(map(lambda r: r.projection, rasters))
        if len(projections) != 1:
            warnings.warn("Rasters has different projections.")
        transforms = set(map(lambda r: r.transform, rasters))
        if len(transforms) != 1:
            warnings.warn("Rasters has different transforms.")

        array = f(rasters, axis=axis, *args, **kwargs)
        return Raster(array, rasters[0].transform, rasters[0].projection)
    return func


max = agg_func(np.ma.max)
min = agg_func(np.ma.min)
median = agg_func(np.ma.median)
count = agg_func(np.ma.count)
mean = agg_func(np.ma.mean)
sum = agg_func(np.ma.sum)
std = agg_func(np.ma.std)


def ufunc(f):
    """Universal functions wrapper."""
    def func(rasters, *args, **kwargs):
        """Wrapped numpy functions. Get more information by seeing
        the corresponding item in ``numpy.ma``.
        """
        if isinstance(rasters, (list, tuple)):
            return list(map(lambda r: f(r, *args, **kwargs), rasters))
        else:
            return f(rasters, *args, **kwargs)
    return func


sin = ufunc(np.ma.sin)
sinh = ufunc(np.ma.sinh)
cos = ufunc(np.ma.cos)
cosh = ufunc(np.ma.cosh)
tan = ufunc(np.ma.tan)
tanh = ufunc(np.ma.tanh)

radians = ufunc(np.radians)

log = ufunc(np.ma.log)
log2 = ufunc(np.ma.log2)
log10 = ufunc(np.ma.log10)

exp = ufunc(np.ma.exp)

abs = ufunc(np.ma.abs)
