from setuptools import setup
from geokit import __version__, __author__, __email__


setup(
    name='geokit',
    version=__version__,
    author=__author__,
    author_email=__email__,
    packages=['geokit'],
    package_data={
        'geokit': ['README.rst', 'LICENSE']
    },
    entry_points={'console_scripts': ['geokit = geokit.script:execute']},
    url='https://github.com/TitorX/geokit',
    description='Geokit is a suit of utilites for processing geo-dataset.',
    long_description=open('README.rst').read(),
)
