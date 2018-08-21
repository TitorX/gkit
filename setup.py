from setuptools import setup
from gkit import __version__, __author__, __email__


setup(
    name='gkit',
    version=__version__,
    author=__author__,
    author_email=__email__,
    packages=['gkit'],
    package_data={
        'gkit': ['README.rst', 'LICENSE']
    },
    entry_points={'console_scripts': [
        'gk = gkit.cli:main'
    ]},
    url='https://github.com/TitorX/gkit',
    description='Gkit is a suit of utilites for processing geo-dataset.',
    long_description=open('README.rst').read(),
)
