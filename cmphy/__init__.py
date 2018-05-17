"""
cmphy

cmphy is a Python interface to the API of the `COMSOL Multiphysics`_
simulation software.

Examples:
    Starting a new COMSOL Multiphysics session is simple:

    >>> ses = Session()
    >>> ses.port
    2036
    >>> mu = ses.mu  # Get a handle to the ModelUtil object.
    >>> model = mu.create(tag="Model1")
    >>> mu.tags()
    ('Model1',)

    The above starts a new COMSOL server (listening to port 2036),
    connects the Python client to the running server and creates an
    empty model.

Notes:
    Documentation is available as docstrings provided with the code
    or online as usage and reference documentation at
    `fellobos.github.io`_.

.. _COMSOL Multiphysics:
   https://www.comsol.com

.. _fellobos.github.io:
   https://fellobos.github.io/cmphy
"""

__version__ = "0.1.0"
