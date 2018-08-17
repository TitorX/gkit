"""Wrapping some math functions from numpy, make it 
work fine with :class:`Raster`.
"""
import warnings

import numpy as np

from .core import Raster


def agg_func(f):
    def func(rasters, axis=0, *args, **kwargs):
        """Wrapped numpy function. Get more information by seeing 
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


mean = agg_func(np.ma.mean)
max = agg_func(np.ma.max)
min = agg_func(np.ma.min)
sum = agg_func(np.ma.sum)
std = agg_func(np.ma.std)
abs = agg_func(np.ma.abs)
