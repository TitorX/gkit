"""Wrapping some math functions from numpy, make it 
work fine with :class:`Raster`.
"""
import numpy as np

from .core import Raster


def agg_func(f):
    def func(r, axis=0, *args, **kwargs):
        """Wrapped numpy function. Get more information by seeing 
        the corresponding item in ``numpy.ma``.
        """
        array = f(r, axis=axis, *args, **kwargs)
        return Raster(array, r[0].transform, r[0].projection)
    return func


mean = agg_func(np.ma.mean)
max = agg_func(np.ma.max)
min = agg_func(np.ma.min)
sum = agg_func(np.ma.sum)
std = agg_func(np.ma.std)
abs = agg_func(np.ma.abs)
