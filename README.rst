Geokit
--------

Geokit is a suit of utilites for processing geo-dataset.

Until now, it's only support to manipulate GeoTIFF dataset and a part of 
interaction between raster and vector dataset.


Example
--------

Here is examples of some basic features that Geokit provides.

.. code-block:: python

    import geokit as geo

    # Read the first layer(band) from .tif.
    r = geo.read_geotiff("lst.tif")

    # You could also specific point out which layer(band) you want to load.
    r = geo.read_geotiff("lst.tif", 2)

    # Open an interactive window display raster using matplotlib(call plt.show).
    r.show()

    # Only draw raster without calling plt.show to continue
    # modify figure.
    import matplotlib.pylab as plt
    r.plot()
    plt.xlabel("Lon")
    plt.ylabel("Lat")
    plt.title("LST(C)")
    plt.savefig("lst_plot.png")

The picture:

.. image:: docs/imgs/lst_plot.png
    :align: center

.. code-block:: python

    # Doing operation like common numpy masked array.
    tmp = (r - 273.15)**3 / 4
    tmp = np.cos(r)
    tmp = np.abs(r)
    tmp = np.sqrt(r)

    print(r.shape)
    print(r.mean())
    print(r.max())
    print(r.min())

    # Save to file
    r.save("out_file.tif")

    # Create a raster from numpy array
    import numpy as np
    x, y = np.mgrid[-1:1:100j, -2:2:200j]
    array = np.sqrt(x**2 + y**2)

    print(array.shape)
    # output: (100, 200)

    transform = [-100, 0.1, 0, 0, 0, -0.1]

    raster = geo.Raster(array, transform)
    raster.show()

The output picture:

.. image:: docs/imgs/array_plot.png
