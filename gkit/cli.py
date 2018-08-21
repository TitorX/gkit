#!/Users/titor/.pyenv/shims/python
import os

import fire

import gkit as gk
from gkit.math import *


class CLI(object):

    def exec(self, formula, out=None, *args, **kwargs):
        pass

    def reproject(self, formula, out=None, *args, **kwargs):
        pass

    def resample(self, formula, out=None, *args, **kwargs):
        pass

    def clipbyshp(self, formula, out=None, *args, **kwargs):
        pass

    @staticmethod
    def map(formula, out="./", *args, **kwargs):
        for r in map(gk.read_geotiff, args):
            res = eval(formula)
            res.save(os.path.join(out, os.path.basename(res.filepath)))

    @staticmethod
    def calc(formula, out='out', *args, **kwargs):
        if not args:
            return

        r = list(map(gk.read_geotiff, args))
        r = r[0] if len(r) == 1 else r

        res = eval(formula)
        res.save(out)

    @staticmethod
    def show(raster):
        """Display raster file."""
        gk.read_geotiff(raster).show()


def main():
    fire.Fire(CLI)


if __name__ == '__main__':
    main()
