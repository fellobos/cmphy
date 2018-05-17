=================================
Welcome to cmphy's documentation!
=================================

This site covers cmphy's usage and API documentation.

cmphy is a Python interface to the API of the `COMSOL Multiphysics
<https://www.comsol.com>`_ simulation software.

Starting a new COMSOL Multiphysics session is simple:

    >>> ses = Session()
    >>> ses.port
    2036
    >>> mu = ses.mu  # Get a handle to the ModelUtil object.
    >>> model = mu.create(tag="Model1")
    >>> mu.tags()
    ('Model1',)

The above starts a new COMSOL server (listening to port 2036), connects
the Python client to the running server and creates an empty model.

Usage documentation
-------------------

The following list contains all major sections of cmphy's non-API
documentation.

.. toctree::
    :maxdepth: 2

    usage/install
    usage/interface

API documentation
-----------------

If you are looking for information on a specific function, class or
method, this part of the documentation is for you.

.. toctree::
    :maxdepth: 2

    api/core

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
