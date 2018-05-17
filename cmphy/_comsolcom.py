"""
This module provides a ComsolCom interface with enhanced features.
"""

import functools
import inspect
import logging
import os

import pythoncom
import win32com.client

from . import error

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def ComsolUtil(version, rebuild):
    """
    Create an enhanced ComsolUtil COM-object.

    Args:
        version (str): The COMSOL version string, e.g. "5.3".
        rebuild (bool): Wether to regenerate the Python source code
            (makepy support) for the corresponding COM type library.

    Returns:
        IComsolUtil: A handle to the ComsolUtil COM-object.
    """
    progid = _build_progid(objtype="comsolutil", version=version)
    try:
        cu = win32com.client.Dispatch(dispatch=progid)
    except pythoncom.com_error:
        raise error.VersionError(
            "Couldn't find COM interface of COMSOL version {!r}. Please "
            "check if the requested version of COMSOL is installed."
            .format(version)
        )
    else:
        if rebuild or _raises_com_error(cu):
            _generate_custom_makepy_support(
                idispatch=cu._oleobj_.QueryInterface(pythoncom.IID_IDispatch)
            )
            cu = win32com.client.Dispatch(dispatch=progid)
        return cu


def _build_progid(objtype, version):
    """
    Build a ProgID that is known by the ComsolCom interface.

    Args:
        objtype (str): The type of the ComsolCom COM-object.
        version (str): The COMSOL version string, e.g. "5.3".

    Returns:
        str: A ProgId known by the ComsolCom interface.
    """
    progid = "comsolcom.{objtype}.{version}".format(
        objtype=objtype,
        version=version.replace(".", "")
    )
    return progid


def _raises_com_error(cu):
    """
    Return True if ComsolUtil raises com_error exceptions.

    Args:
        cu (IComsolUtil): A handle to the ComsolUtil COM-object.

    Returns:
        bool: True if ComsolUtil raises com_error exceptions, False
            otherwise.
    """
    try:
        cu.StartComsolServer()  # error: usegraphics parameter is missing
    except pythoncom.com_error:
        return True
    except error.APIError:
        return False


def _generate_custom_makepy_support(idispatch):
    """
    Generate custom makepy support for the ComsolCom interface.

    Args:
        idispatch (PyIDispatch): The IDispatch interface of the COM
            object.
    """
    module = _generate_typelib_support(idispatch)
    for name, obj in module.__dict__.items():
        if _is_makepy_generated_public_class(name, obj):
            obj.__getattribute__ = __getattribute__


def _generate_typelib_support(idispatch):
    """
    Generate type library support (Python source code) for the IDispatch
    based COM object.

    Args:
        idispatch (PyIDispatch): The IDispatch interface of the COM
            object.
    """
    typelib = _get_typelib(idispatch)
    module = win32com.client.gencache.MakeModuleForTypelibInterface(typelib)
    return module


def _get_typelib(idispatch):
    """
    Return the type library for the given IDispatch interface.

    Args:
        idispatch (PyIDispatch): The IDispatch interface of the COM
            object.

    Returns:
        PyITypeLib: The type library for the given IDispatch object.
    """
    info = idispatch.GetTypeInfo()
    typelib, index = info.GetContainingTypeLib()
    return typelib


def _is_makepy_generated_public_class(name, obj):
    """
    Return True if the object is a makepy generated public class.

    Args:
        name (str): The name of the object.
        obj: The object to test.

    Returns:
        bool: True if the object is a makepy generated public class,
            False otherwise.
    """
    return (not name.startswith("_")
            and inspect.isclass(obj)
            and issubclass(obj, win32com.client.DispatchBaseClass)
            and not name == "DispatchBaseClass")


def __getattribute__(self, name):
    """
    Perform custom attribute access if the attribute is public and callable.

    Args:
        name (str): The name of the attribute.
    """
    attr = object.__getattribute__(self, name)
    if not name.startswith("_") and callable(attr):
        return _intercept_method_call(attr)
    else:
        return attr


def _intercept_method_call(method):
    """
    Intercept a ComsolCom class method call.

    Args:
        method (method): A bound method of a ComsolCom API class.

    Returns:
        method: The wrapped method object.
    """
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        try:
            retval = method(*args, **kwargs)
        except pythoncom.com_error as e:
            raise error.APIError(e)
        else:
            log.debug(
                "Called API function {name}, args={args}, kwargs={kwargs}, "
                "retval={retval}".format(
                    name="{cls}.{meth}".format(
                        cls=method.__self__.__class__.__name__,
                        meth=method.__name__,
                    ),
                    args=args,
                    kwargs=kwargs,
                    retval=retval,
                )
            )
            return retval
    return wrapper


def ModelUtil(version):
    """
    Create an enhanced ModelUtil COM-object.

    Args:
        version (str): The COMSOL version string, e.g. "5.3".

    Returns:
        IModelUtil: A handle to the ModelUtil COM-object.
    """
    progid = _build_progid(objtype="modelutil", version=version)
    mu = win32com.client.Dispatch(dispatch=progid)
    return mu


def _get_generated_filepath(idispatch):
    """
    Return the path of the Python support file which is generated for the
    type library of the given IDispatch interface.

    Args:
        idispatch (PyIDispatch): The IDispatch interface of the COM
            object.

    Returns:
        filepath (str): Absolute filepath of the Python support file.
    """
    typelib = _get_typelib(idispatch)
    clsid, lcid, _, major, minor, _ = typelib.GetLibAttr()
    path = win32com.client.gencache.GetGeneratePath()
    filename = win32com.client.gencache.GetGeneratedFileName(
        clsid, lcid, major, minor
    )
    return os.path.join(path, filename + ".py")
