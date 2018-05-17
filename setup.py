from setuptools import find_packages, setup

from cmphy import __version__


setup(
    name="cmphy",
    version=__version__,
    description="A Python interface to the COMSOL Multiphysics API",
    url="https://github.com/fellobos/cmphy",
    author="Florian Boesl",
    author_email="f.boesl@aol.com",
    platforms=["win32"],  # or more specific, e.g. "win32", "cygwin", "osx"
    packages=find_packages(),
    zip_safe=False,
)
