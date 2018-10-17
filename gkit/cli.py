#!/Users/titor/.pyenv/shims/python
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import fire

import gkit as gk
from gkit.math import *


def loader(*args):
    for fn in args:
        if "re://" in fn:
            fn = re.compile(fn[5:])
            files = filter(
                lambda f: re.search(fn, str(f)) is not None,
                Path(".").rglob("*")
            )
            for fn in list(files):
                yield gk.read_geotiff(str(fn))
        else:
            yield gk.read_geotiff(fn)


class CLI(object):

    @staticmethod
    def map(formula, out="./", *args, **kwargs):
        if not os.path.exists(out):
            os.makedirs(out)

        for r in loader(*args):
            if kwargs.get('print'):
                print(r.filepath)
            res = eval(formula)
            res.save(os.path.join(out, os.path.basename(r.filepath)))

    @staticmethod
    def calc(formula, out='out', *args, **kwargs):
        if not args:
            return

        r = list(loader(*args))

        if kwargs.get('print'):
            for i in r:
                print(i.filepath)

        if len(r) == 1: r = r[0]

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
