from functools import reduce
from osgeo import ogr
import numpy as np

from .raster import Raster


def split_by_shp(raster, shp_path, by=None, overall=False):
    """Split rasters into several parties by polygons from shapefile.

    Args:
        raster (Raster or list of Raster): One or more rasters.
        shp_path (str): Shapefile path.
        by (str): Field name, used to group polygons.(default=FID)
        overall (bool): Use whole area(combine all polygons) as a result.
            (default=False)

    Returns:
        dict
    """
    raster = [raster] if isinstance(raster, Raster) else list(raster)
    shp = ogr.Open(shp_path)
    layer = shp.GetLayer()
    result = {}
    if overall:
        r = [r.clip_by_layer(layer) for r in raster]
        if len(r) == 1:
            r = r[0]
        result["overall"] = r

    # Group features by field values.
    shp_features = {}
    for feature in layer:
        shp_features.setdefault(feature[by] if by else feature.GetFID(), [])
        shp_features[feature[by] if by else feature.GetFID()].append(feature)

    for key, feature in shp_features.items():
        r = [r.clip_by_feature(feature) for r in raster]
        if len(r) == 1:
            r = r[0]
        result[key] = r

    return result


def zonal_apply(raster, shp, func, by=None, overall=False,
                args=(), kwargs={}):
    """Apply a function to each zone.

    Args:
        raster (Raster or list of Raster): One or more rasters.
        shp_path (str): Shapefile path.
        func (function): Function to apply to each zone.
        by (str): Field name, used to group polygons.(default=FID)
        overall (bool): Use whole area(combine all polygons) as a result.
            (default=False)

    Returns:
        dict
    """
    splited = split_by_shp(raster, shp, by, overall)
    result = {}
    for i, rs in splited.items():
        rs = [rs] if isinstance(rs, Raster) else rs
        result[i] = func(*rs, *args, **kwargs)
    return result


def uniform_mask(*args, ignore_invalid=True,
                 return_mask=False, inplace=False):
    if ignore_invalid:
        masks = [x.mask for x in args]
    else:
        args = [np.ma.masked_invalid(x) for x in args]
        masks = [x.mask for x in args]
    mask = reduce(lambda x, y: x | y, masks)
    if return_mask:
        return mask

    if not inplace:
        args = [i.copy() for i in args]
    for x in args:
        x.mask = mask
    return args
