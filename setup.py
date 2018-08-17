from setuptools import setup
from geokit import __version__, __author__, __email__


setup(
    name='gkit',
    version=__version__,
    author=__author__,
    author_email=__email__,
    packages=['gkit'],
    package_data={
        'gkit': ['README.rst', 'LICENSE']
    },
    entry_points={'console_scripts': ['gkit = gkit.script:execute']},
    url='https://github.com/TitorX/gkit',
    description='Geokit is a suit of utilites for processing geo-dataset.',
    long_description=open('README.rst').read(),
)
