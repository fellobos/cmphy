# cmphy

cmphy is a Python interface to the API of the [COMSOL Multiphysics][1]
simulation software.

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

## Installation

Clone the public repository to get a local copy of the source:

    $ git clone git://github.com/fellobos/cmphy.git

Once you have it, you can embed cmphy in your own Python package, or
install it into your site-packages easily:

    $ cd cmphy
    $ python setup.py install

## Documentation

cmphy has usage and reference documentation available at
[fellobos.github.io][2].

[1]: https://www.comsol.com
[2]: https://fellobos.github.io/cmphy
