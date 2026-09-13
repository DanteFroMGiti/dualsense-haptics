"""Desktop-only single-instance guard (not vendored to the Deck plugin -
Decky's own plugin lifecycle already prevents that kind of duplication).

A launch races to bind a fixed-name QLocalServer. If another instance is
already listening, this process asks it to raise its window (unless it was
itself an unattended --tray autostart launch) and exits instead of leaving a
second copy running - main.py calls this before touching the controller so a
duplicate launch never fights the first one over exclusive hardware access.
"""
import os

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

_SERVER_NAME = f"dualsense-haptics-single-instance-{os.getuid()}"


class SingleInstanceGuard(QObject):
    show_requested = Signal()

    def __init__(self):
        super().__init__()
        self._server = None

    def try_acquire(self, request_show=True, timeout_ms=200):
        """Returns True if this process should keep running. Returns False
        (and, unless this was an unattended launch, asks the running
        instance to raise its window) if another instance already holds
        the lock."""
        if self._connect_to_running(request_show, timeout_ms):
            return False

        # No live server answered - either nothing is running, or a crash
        # (SIGKILL) left a stale socket file behind. removeServer() is Qt's
        # documented way to clear exactly that case; it's only reached here
        # because the connect attempt above already found nobody home.
        QLocalServer.removeServer(_SERVER_NAME)
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_new_connection)
        if self._server.listen(_SERVER_NAME):
            return True

        # Lost a startup race to another instance binding first between our
        # failed connect and our listen() - defer to whichever one won.
        if self._connect_to_running(request_show, timeout_ms):
            return False
        # Extremely unlikely (permissions, platform quirk): fail open rather
        # than ever refuse to start the app over this.
        return True

    def release(self):
        if self._server is not None:
            self._server.close()
            self._server = None

    def _connect_to_running(self, request_show, timeout_ms):
        socket = QLocalSocket()
        socket.connectToServer(_SERVER_NAME)
        if not socket.waitForConnected(timeout_ms):
            return False
        if request_show:
            socket.write(b"show")
            socket.waitForBytesWritten(timeout_ms)
        socket.disconnectFromServer()
        return True

    def _on_new_connection(self):
        conn = self._server.nextPendingConnection()
        if conn is None:
            return
        conn.readyRead.connect(lambda: self._on_ready_read(conn))
        conn.disconnected.connect(conn.deleteLater)

    def _on_ready_read(self, conn):
        if bytes(conn.readAll()) == b"show":
            self.show_requested.emit()
