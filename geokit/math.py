# coding=utf-8
import numpy as np

from .core import Raster


"""
对numpy中的数学函数进行封装，使其可以正确的作用于Raster对象
"""

def mean(x, axis=0):
    return Raster(np.ma.mean(x, axis=axis), x[0].transform, x[0].projection)

def max(x, axis=0):
    return Raster(np.ma.max(x, axis=axis), x[0].transform, x[0].projection)

def min(x, axis=0):
    return Raster(np.ma.min(x, axis=axis), x[0].transform, x[0].projection)

def sum(x, axis=0):
    return Raster(np.ma.sum(x, axis=axis), x[0].transform, x[0].projection)

def std(x, axis=0):
    return Raster(np.ma.std(x, axis=axis), x[0].transform, x[0].projection)
