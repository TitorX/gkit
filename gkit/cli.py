#!/Users/titor/.pyenv/shims/python
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import fire

import gkit as gk
from gkit.math import *


def loader(*args):
    rs = []
    for fn in args:
        if "re://" in fn:
            fn = re.compile(fn[5:])
            files = filter(
                lambda f: re.search(fn, str(f)) is not None,
                Path(".").rglob("*")
            )
            for fn in list(files):
                rs.append(gk.read_geotiff(str(fn)))
        else:
            rs.append(gk.read_geotiff(fn))

    return rs[0] if len(rs) == 1 else rs


class CLI(object):

    @staticmethod
    def map(formula, out="./", *args, **kwargs):
        for r in map(gk.read_geotiff, args):
            if kwargs.get('print'):
                print(r.filepath)
            res = eval(formula)
            res.save(os.path.join(out, os.path.basename(res.filepath)))

    @staticmethod
    def calc(formula, out='out', *args, **kwargs):
        if not args:
            return

        r = loader(*args)
        if kwargs.get('print'):
            if isinstance(r, list):
                for i in r:
                    print(i.filepath)
            else:
                print(r.filepath)

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
