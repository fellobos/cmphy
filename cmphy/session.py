"""
This module provides connection capabilities to COMSOL.
"""

import logging
import os
import subprocess
import time
import winreg

import psutil

from . import _comsolcom
from . import config
from . import error

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class Session:

    """
    Run a COMSOL Multiphysics session in client/server mode.

    Start a COMSOL Multiphysics server and connect the Python client to
    the running server. The `mu` attribute provides a handle to the
    ModelUtil object.

    Exactly one single `Session` instance can be active at the same time.
    An `AlreadyConnectedError` is raised if multiple client connections
    are requested (e.g. a second `Session` is instantiated while the first
    one is still active).

    Args:
        version (str, optional): The COMSOL version to be started.
        timeout (int, optional): The time limit in seconds after which the
            connection attempt to COMSOL is aborted.
        rebuild (bool, optional): Wether to rebuild the Python source code
            for the ComsolCom interface.

    Raises:
        AlreadyConnectedError: If the Python client is already connected
            to the COMSOL server.

    Examples:
        Start a new COMSOL Multiphysics session and create an empty model
        on the server:

        >>> ses = Session()
        >>> ses.port
        2036
        >>> mu = ses.mu  # Get a handle to the ModelUtil object.
        >>> model = mu.create(tag="Model1")
        >>> mu.tags()
        ('Model1',)

        Open a COMSOL Multiphysics file in the desktop and connect the
        desktop to the running server:

        >>> model = ses.launch("tests\\models\\session-1.mph")
        >>> model.getFilePath()
        'E:\\Repos\\cmphy\\tests\\models\\session-1.mph'

        Shutdown the COMSOL session when done:

        >>> ses.shutdown()
    """

    def __init__(self, version=config.VERSION, timeout=config.TIMEOUT,
                 rebuild=False):
        self._version = str(version)
        self._timeout = int(timeout)
        self._rebuild = bool(rebuild)
        self._port = None
        self._server = None
        self._desktop = None
        self._mphfile = None
        self._model = None

        self._cu = _comsolcom.ComsolUtil(self._version, self._rebuild)
        self._mu = _comsolcom.ModelUtil(self._version)

        self._start_server()
        self._connect_client()

    def __del__(self):
        """Shutdown the COMSOL Multiphysics session at garbage collection"""
        self.shutdown()

    @property
    def mu(self):
        """IModelUtil: A handle to the ModelUtil object."""
        return self._mu

    @property
    def port(self):
        """int: The port number of the COMSOL server."""
        return self._port

    def _start_server(self):
        """Start the COMSOL Multiphysics server in non-graphics mode."""
        if self._cu.StartComsolServer(usegraphics=False):
            self._port = int(self._cu.get_port())
            conn = self._get_server_connection()
            self._server = psutil.Process(conn.pid)
            log.info(
                "COMSOL {} server started listening on port {}"
                .format(self._version, self.port)
            )
        else:
            raise error.ConnectionError(
                "Couldn't start COMSOL {} server: {}".format(
                    self._version,
                    self._cu.get_errormessage(),
                )
            )

    def _get_server_connection(self):
        """Get the socket connection that is used by the COMSOL server."""
        for c in psutil.net_connections():
            if (c.laddr.port == self.port and c.status == psutil.CONN_LISTEN):
                log.debug(
                    "Found socket connection listening on port {}, conn={}"
                    .format(self.port, c)
                )
                return c
        else:
            raise error.ConnectionError(
                "Couldn't find socket connection listening on port {}."
                .format(self.port)
            )

    def _connect_client(self):
        """Connect the Python client to the running server."""
        try:
            self.mu.Connect("localhost", self.port)
        except error.APIError:
            self.shutdown()
            raise error.AlreadyConnectedError(
                "The Python client is already connected to the server."
            )
        else:
            log.info(
                "Python client connected to the server using port {}"
                .format(self.port)
            )

    def launch(self, filepath=None):
        """
        Launch a COMSOL desktop that is connected to the running server.

        Open a COMSOL Multiphysics model in 'interactive' mode. This enables
        simultaneous access to the model from both clients (the desktop and
        the Python client).

        If another COMSOL desktop is already connected to the server,
        terminate that process, without saving, and remove the corresponding
        model from the server.

        Args:
            filepath (str, optional): Open the given MPH-file in the COMSOL
                desktop. Start an empty desktop if `filepath` is None.

        Returns:
            Model: The launched COMSOL Multiphysics model.
        """
        self._terminate_desktop()
        otags = set(self.mu.tags())
        self._start_desktop(filepath)
        self._wait_for_desktop(tags=otags)
        return self._model

    def _start_desktop(self, filepath):
        """
        Start a COMSOL desktop that is connected to the running server.

        Args:
            filepath (str, optional): Open the given MPH-file in the COMSOL
                desktop. Start an empty desktop if `filepath` is None.
        """
        options = [
            "mphclient",
            "-server", "localhost",
            "-port", str(self.port),
        ]

        if filepath is None:
            self._mphfile = None
        else:
            self._mphfile = self._validate_mphfile(filepath)
            options.extend(["-open", self._mphfile])

        root_dir = _get_root_dir(self._version)
        cmd = [os.path.join(root_dir, "bin\\win64\\comsol.exe")]
        cmd.extend(options)
        proc = subprocess.Popen(cmd)
        self._desktop = psutil.Process(proc.pid)
        log.debug(
            "Started COMSOL desktop client, pid={}, cmd={}"
            .format(self._desktop.pid, cmd)
        )

    def _validate_mphfile(self, filepath):
        """
        Check if the given filepath points to a valid MPH-file.

        Args:
            filepath (str): Path to the COMSOL Multiphysics file.

        Raises:
            APIError: If the given filepath is not a valid COMSOL
                Multiphysics file.

        Returns:
            str: The normalized, absolute path of the MPH-file.
        """
        tag = self.mu.uniquetag("Model")
        self.mu.load(tag, filepath)  # Valid? Raises error if not!
        self.mu.remove(tag)
        log.debug("MPH-file {!r} is valid".format(filepath))
        return os.path.normpath(os.path.abspath(filepath))

    def _wait_for_desktop(self, tags):
        """
        Wait until the COMSOL desktop is ready for use.

        Args:
            tags (set): The original list of model tags before the desktop
                process was started.

        Returns:
            Model: The launched COMSOL Multiphysics model.
        """
        start_time = time.time()
        while time.time() - start_time < self._timeout:
            time.sleep(1)
            try:
                dtags = set(self.mu.tags()).difference(tags)
                log.debug(
                    "Found {} new model(s) tagged {} on server"
                    .format(len(dtags), dtags)
                )
                if not dtags:  # No new model(s) found.
                    continue
            except error.APIError as e:  # Server is busy.
                log.debug(e._excepinfo[2].rstrip("."))
                continue
            else:
                ftag = None
                if self._mphfile is None:
                    msg = "Expected exactly one new model tag"
                    assert len(dtags) == 1, msg
                    ftag = dtags.pop()
                else:
                    for tag in dtags:
                        try:
                            filepath = self.mu.Model(tag).getFilePath()
                        except error.APIError as e:  # Server is busy.
                            log.debug(e._excepinfo[2].rstrip("."))
                            continue
                        else:
                            if filepath == self._mphfile:
                                ftag = tag
                            else:
                                self.mu.remove(tag)
                                log.debug(
                                    "Removed 'intermediate' model tagged "
                                    "{!r} from server".format(tag)
                                )
                if ftag is not None:
                    time.sleep(3)
                    try:
                        self._model = self.mu.Model(ftag)
                    except error.APIError:  # Strange!? Might happen when an
                        log.debug(          # empty desktop is launched.
                            "Model tagged {!r} no longer exists on server"
                            .format(ftag)
                        )
                        continue
                    else:
                        log.info(
                            "Desktop client connected to the server using "
                            "port {}, tag={!r}, mphfile={!r}"
                            .format(self.port, ftag, self._mphfile)
                        )
                        return self._model
        else:
            self._terminate_desktop()
            raise error.TimeoutError(
                "Couldn't establish a connection to the desktop within {} "
                "seconds. Connection attempt aborted."
                .format(self._timeout)
            )

    def shutdown(self):
        """Shutdown the COMSOL Multiphysics session."""
        self._terminate_desktop()
        self._terminate_server()

    def _terminate_desktop(self):
        """Terminate the COMSOL Multiphysics desktop process."""
        self._terminate_process(self._desktop)
        self._remove_active_model()
        self._remove_lock_file()

    def _terminate_process(self, proc):
        """
        Safely terminate the given COMSOL Multiphysics process.

        Args:
            proc (psutil.Process): The COMSOL process to be terminated.
        """
        try:
            pid = proc.pid
            name = proc.name()
            proc.terminate()
        except (AttributeError, psutil.NoSuchProcess):
            return
        else:
            msg = "COMSOL process {}, pid={}".format(name, pid)
            try:
                proc.wait(timeout=self._timeout)
            except psutil.TimeoutExpired:
                proc.kill()
                log.debug("Killed {}".format(msg))
            else:
                log.debug("Terminated {}".format(msg))

    def _remove_active_model(self):
        """
        Remove the 'active ' model from the COMSOL server.

        It is not possible to launch an empty COMSOL desktop if an 'active'
        model exists on the server. A model becomes 'active' if it gets loaded
        via the COMSOL desktop. Removing the 'active' model from the server
        solves this problem.
        """
        try:
            tag = self._model.get_tag()
        except (AttributeError, error.APIError):
            return
        else:
            self.mu.remove(tag)
            log.debug(
                "Removed 'active' model tagged {!r} from server".format(tag)
            )

    def _remove_lock_file(self):
        """
        Remove the lock file that is created by the COMSOL desktop.

        The lock file remains because the COMSOL desktop process is ended in
        a nonstandard way (termination of desktop process).
        """
        try:
            lockfile = self._mphfile + ".lock"
            os.remove(lockfile)
        except (TypeError, FileNotFoundError, PermissionError):
            return
        else:
            log.debug("Removed lockfile {!r}".format(lockfile))

    def _terminate_server(self):
        """Terminate the COMSOL Multiphysics server process."""
        self._terminate_process(self._server)


def _get_root_dir(version):
    """
    Return the COMSOL root directory.

    Get the root directory for the given COMSOL `version` from the Windows
    registry.

    Args:
        version (str): The COMSOL version string, e.g. "5.3".

    Returns:
        str: The COMSOL root directory.

    Raises:
        ValueError: If the COMSOL root directory couldn't be found.
    """
    try:
        hkey = winreg.OpenKeyEx(
            key=winreg.HKEY_LOCAL_MACHINE,
            sub_key="SOFTWARE\\COMSOL\\COMSOL{}".format(
                str(version).replace(".", "")
            )
        )
    except OSError:
        raise error.VersionError(
            "Couldn't find root directory of COMSOL version {!r}. Please "
            "check if the requested version of COMSOL is installed."
            .format(version)
        )
    else:
        value, __ = winreg.QueryValueEx(hkey, "COMSOLROOT")
        log.debug(
            "Root directory of COMSOL version {} is {!r}"
            .format(version, value)
        )
        return value
