=================
The API interface
=================

This page gives a good introduction in how to get started with the
core functionality that is provided by cmphy.

Before you begin, make sure that cmphy is :doc:`installed <install>`
properly on your system.

To use the Python interface to the COMSOL Multiphysics API you first
have to create a :ref:`connection <connection-capabilities>` to
COMSOL.

.. _connection-capabilities:

Connection capabilities
-----------------------

Starting and connecting to a COMSOL Multiphysics session is simple.
The :class:`Session <cmphy.session.Session>` object enables you to
start a new instance of a COMSOL Multiphysics server and to connect
to that session:

.. code-block:: python

    >>> ses = Session()
    >>> ses.port
    2036
    >>> mu = ses.mu  # Get a handle to the ModelUtil object.
    >>> model = mu.create(tag="Model1")
    >>> mu.tags()
    ('Model1',)

The above starts a new COMSOL server (listening to port 2036), connects
the Python client to the running server and creates an empty model.

The session object holds a handle to the ModelUtil COM-object which
provides an interface to the COMSOL API.

    >>> mu
    <win32com.gen_py.ComsolCom 5.3.IModelUtil instance at 0x130251184>
