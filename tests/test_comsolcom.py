import os
import types

import pytest
import pythoncom
import pywintypes

from cmphy import _comsolcom
from cmphy import config
from cmphy import error


@pytest.mark.parametrize("version", ["1.0.99", ""])
def test_invalid_version(version):
    with pytest.raises(error.VersionError):
        _comsolcom.ComsolUtil(version, rebuild=False)


def test_com_error_is_catched():
    version = config.VERSION
    cu = _comsolcom.ComsolUtil(version, rebuild=True)

    with pytest.raises(error.APIError):
        cu.StartComsolServer()

    cu.StartComsolServer(False)
    mu = _comsolcom.ModelUtil(version)
    mu.Connect()

    with pytest.raises(error.APIError):
        mu.Model("Unknown Model")

    model = mu.create("Model1")
    param = model.param()

    with pytest.raises(error.APIError):
        param.get("Unknown Parameter")

    mu.Disconnect()


def test_existing_makepy_support_is_reused():
    version = config.VERSION

    cu = _comsolcom.ComsolUtil(version, rebuild=True)

    idispatch = cu._oleobj_.QueryInterface(pythoncom.IID_IDispatch)
    filepath = _comsolcom._get_generated_filepath(idispatch)
    mtime = os.path.getmtime(filepath)

    cu = _comsolcom.ComsolUtil(version, rebuild=False)

    assert mtime == os.path.getmtime(filepath)


def test_custom_attribute_access():
    version = config.VERSION
    cu = _comsolcom.ComsolUtil(version, rebuild=True)

    assert type(cu.StartComsolServer) is types.FunctionType
    assert type(cu.CLSID) is pywintypes.IIDType
    assert type(cu.coclass_clsid) is pywintypes.IIDType
    assert type(cu._get_good_object_) is types.MethodType
    assert type(cu.__dict__) is dict
