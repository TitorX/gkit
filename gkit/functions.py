from functools import reduce
import numpy as np


def uniform_mask(*args, ignore_invalid=False,
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
