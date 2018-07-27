Geokit
--------

Geokit is a suit of utilites for processing geo-dataset.

Until now, it's only support to manipulate GeoTIFF dataset and a part of 
interaction between raster and vector dataset.


Usage
------

import package and read dataset

.. code-block:: python

    import geokit as geo

    # It will read the first layer from dataset.
    raster = geo.read_geotiff("lst.tif")

    # You could also specific point out which layer you want to load.    
    raster = geo.read_geotiff("lst.tif", 2)


plot raster

.. code-block:: python

    raster.plot()

The plot:

.. image:: docs/images/lst_plot.png

raster calculator

.. code-block:: python

    # Use raster like common numpy masked array.
    new = (raster - 273.15)**3 /4 


save to file

.. code-block:: python

    raster.save("out_file.tif")

