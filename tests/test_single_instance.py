"""SingleInstanceGuard: a second launch must be refused (and, unless it was
an unattended --tray autostart run, must ask the first to raise its
window) instead of leaving two copies of the app running."""
import time
import uuid

import pytest

QtNetwork = pytest.importorskip('PySide6.QtNetwork')
QtWidgets = pytest.importorskip('PySide6.QtWidgets')


@pytest.fixture
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _pump_until(app, condition, timeout=1.0):
    """The server side's newConnection/readyRead signals are only delivered
    once the event loop actually turns, unlike the client's blocking
    waitForConnected/waitForBytesWritten - poll instead of assuming one
    processEvents() call lands after the client side has already returned."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return False


@pytest.fixture(autouse=True)
def _isolated_server_name(monkeypatch):
    # A fixed, PID-derived server name would collide between parallel test
    # runs (and with a real running instance on the same machine) - give
    # every test its own.
    import single_instance
    monkeypatch.setattr(single_instance, '_SERVER_NAME', f'dualsense-haptics-test-{uuid.uuid4()}')


def test_first_launch_acquires_and_second_is_refused(app):
    import single_instance

    first = single_instance.SingleInstanceGuard()
    assert first.try_acquire() is True

    second = single_instance.SingleInstanceGuard()
    assert second.try_acquire() is False

    first.release()
    second.release()


def test_second_launch_asks_first_to_show_unless_unattended(app):
    import single_instance

    first = single_instance.SingleInstanceGuard()
    assert first.try_acquire() is True
    shown = []
    first.show_requested.connect(lambda: shown.append(True))

    second = single_instance.SingleInstanceGuard()
    assert second.try_acquire(request_show=True) is False
    assert _pump_until(app, lambda: shown)
    assert shown == [True]

    third = single_instance.SingleInstanceGuard()
    assert third.try_acquire(request_show=False) is False
    _pump_until(app, lambda: False, timeout=0.2)  # give a stray signal time to (not) arrive
    assert shown == [True]  # unattended (--tray) relaunch never asked to show

    first.release()
    second.release()
    third.release()


def test_releasing_the_first_lets_a_new_instance_bind(app):
    import single_instance

    first = single_instance.SingleInstanceGuard()
    assert first.try_acquire() is True
    first.release()

    second = single_instance.SingleInstanceGuard()
    assert second.try_acquire() is True
    second.release()


def test_a_crash_leaving_a_stale_socket_file_does_not_block_the_next_launch(app):
    """A SIGKILLed process never runs QLocalServer.close(), so it leaves an
    orphan socket file behind at the same path a clean shutdown would have
    removed (mirrors bt_hid_proxy.recover_stale_lock's crash-recovery intent
    for the unrelated BT HID Proxy lock) - reproduce that exact filesystem
    state directly rather than relying on Python's own GC timing to fake a
    process kill."""
    import single_instance

    probe = QtNetwork.QLocalServer()
    assert probe.listen(single_instance._SERVER_NAME)
    stale_path = probe.fullServerName()
    probe.close()  # a clean close unlinks the file; recreate it as an orphan
    open(stale_path, 'w').close()

    guard = single_instance.SingleInstanceGuard()
    assert guard.try_acquire() is True
    guard.release()
