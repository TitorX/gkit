"""Wrapping some math functions from numpy, make it 
work fine with `Raster`.
"""
import numpy as np

from .core import Raster


def agg_func(f):
    def func(r, axis=0):
        return Raster(f(x, axis=axis), x[0].transform, x[0].projection)
    func.__doc__=f.__doc__
    return func


mean = agg_func(np.ma.mean)
max = agg_func(np.ma.max)
min = agg_func(np.ma.min)
sum = agg_func(np.ma.sum)
std = agg_func(np.ma.std)
