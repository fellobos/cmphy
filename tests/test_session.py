import os

import pytest

from cmphy import config
from cmphy import error
from cmphy import session


def test_get_root_dir():
    version = config.VERSION
    for version in [version, float(version)]:
        root_dir = session._get_root_dir(version)
        assert os.path.isdir(root_dir)

    with pytest.raises(error.VersionError):
        root_dir = session._get_root_dir(version="1.0.99")

    with pytest.raises(error.VersionError):
        root_dir = session._get_root_dir(version="")


class TestSession:

    def test_server_only_session(self):
        ses = session.Session()

        assert hasattr(ses._cu, "StartComsolServer")
        assert ses._version in ses._cu.get_version()
        assert ses._port == ses._cu.get_port()

        assert hasattr(ses.mu, "tags")
        with pytest.raises(AttributeError):
            ses.mu = None

        assert ses._server.is_running()
        assert ses._server.name() == "comsolmphserver.exe"

        model = ses.mu.create("Model1")
        assert model.get_tag() in ses.mu.tags()
        assert model_is_ready_for_use(model)

        ses.shutdown()

        assert not ses._server.is_running()

    def test_session_with_desktop(self):
        modulepath = os.path.dirname(__file__)
        filepaths = [
            os.path.join(modulepath, "models", filename)
            for filename in ["session-1.mph", "session-2.mph"]
        ]

        ses = session.Session()
        model = ses.mu.load(tag="Session1", filename=filepaths[0])
        assert model.get_tag() in ses.mu.tags()
        assert model_is_ready_for_use(model)

        # ------------------ Launch an empty COMSOL desktop ------------------

        model = ses.launch()

        assert ses._desktop.is_running()
        assert ses._model is not None
        assert model.getFilePath() == ""
        assert ses._mphfile is None

        tag = model.get_tag()
        assert tag in ses.mu.tags()
        assert model_is_ready_for_use(model)

        ses._terminate_desktop()

        assert not ses._desktop.is_running()
        assert tag not in ses.mu.tags()

        # --- Launch two COMSOL desktops (sequentially) with opened models ---

        for filepath in filepaths:
            model = ses.launch(filepath)

            assert model.getFilePath() == filepath
            lockfile = ses._mphfile + ".lock"
            assert os.path.isfile(lockfile)

            tag = model.get_tag()
            assert tag in ses.mu.tags()
            assert model_is_ready_for_use(model)

            ses._terminate_desktop()

            assert not ses._desktop.is_running()
            assert not os.path.isfile(lockfile)
            assert tag not in ses.mu.tags()

        # -------------- Again, launch an empty COMSOL desktop --------------

        model = ses.launch()

        tag = model.get_tag()
        assert tag in ses.mu.tags()
        assert model_is_ready_for_use(model)

        assert model.getFilePath() == ""

        ses.shutdown()

        assert not ses._desktop.is_running()
        assert not ses._server.is_running()

    def test_multiple_connections(self):
        ses = session.Session()

        with pytest.raises(error.AlreadyConnectedError):
            session.Session()

        ses.shutdown()
        ses = session.Session()

        assert ses._server.is_running()

        ses.shutdown()

    def test_connection_attempt_timed_out(self):
        ses = session.Session(timeout=1)

        with pytest.raises(error.TimeoutError):
            ses.launch()

        assert not ses._desktop.is_running()


def model_is_ready_for_use(model):
    try:
        name, value = "length", "1[cm]"
        model.param().set(name, value)
        assert model.param().get(name) == value
        model.param().remove(name)
    except error.APIError:
        return False
    else:
        return True
