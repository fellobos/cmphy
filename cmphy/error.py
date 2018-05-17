"""
This module contains the COMSOL exception classes.
"""


class COMSOLError(Exception):
    """
    Base class for all COMSOL exceptions.
    """


class VersionError(COMSOLError):
    """
    Raised when the requested COMSOL version was not found on the system.
    """


class ConnectionError(COMSOLError):
    """
    Raised when a connection attempt to COMSOL failed.
    """


class TimeoutError(ConnectionError):
    """
    Raised when a connection attempt to COMSOL was aborted due to timeout.
    """


class AlreadyConnectedError(ConnectionError):
    """
    Raised when the Python client is already connected to the server.
    """


class APIError(COMSOLError):

    """
    Raised when a COMSOL API function raises a com_error exception.

    Args:
        com_error (pywintypes.com_error): A COM exception raised by the
            ComsolCom interface.
    """

    def __init__(self, e):
        self._strerror = e.strerror.rstrip(".")
        self._excepinfo = e.excepinfo

    def __str__(self):
        return "{}: {}".format(self._strerror, self._excepinfo)
