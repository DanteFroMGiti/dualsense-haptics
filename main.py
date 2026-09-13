#!/usr/bin/env python3
import argparse
import sys

from PySide6.QtWidgets import QApplication

from haptics_engine import HapticsEngine
from config import load_state, save_state
from ui import MainWindow, TrayApp, install_press_animations
from single_instance import SingleInstanceGuard
import app_audio_binding
import bt_hid_proxy
import theme
import i18n


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tray", action="store_true", help="start minimized to tray (used by autostart)")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Refuse to run a second copy - it would otherwise fight an already-
    # running instance over exclusive controller access. Checked before any
    # of that hardware setup below.
    guard = SingleInstanceGuard()
    if not guard.try_acquire(request_show=not args.tray):
        return
    app.aboutToQuit.connect(guard.release)

    bt_hid_proxy.recover_stale_lock()

    state = load_state()
    theme.manager.set_preference(state.get("theme", "system"))
    i18n.manager.set_language(state.get("language", i18n.manager.lang))
    app.setStyleSheet(theme.manager.stylesheet())
    install_press_animations(app)

    engine_box = {"engine": None}
    # Desktop-only per-app audio binding (see app_audio_binding.py) - a
    # sibling to `state`, never inside it, so a narrowed capture source can
    # never get deep-copied into a saved profile (config.save_current()
    # only ever copies state["active"]).
    capture_source_box = {"source": None}

    def start_engine():
        if engine_box["engine"] is not None:
            return
        engine = HapticsEngine(state["active"], capture_source_box)
        engine.start()
        engine_box["engine"] = engine

    def stop_engine():
        engine = engine_box["engine"]
        if engine is not None:
            engine.stop()
            engine.join(timeout=2)
            engine_box["engine"] = None

    def save():
        save_state(state)

    start_engine()
    if state.get("app_audio_binding_enabled", False):
        app_audio_binding.start_watching(state, capture_source_box)

    main_window = MainWindow(
        state,
        engine_holder=lambda: engine_box["engine"],
        start_engine_cb=start_engine,
        stop_engine_cb=stop_engine,
        save_cb=save,
        capture_source_box=capture_source_box,
    )

    tray = TrayApp(
        app, main_window,
        start_engine_cb=start_engine,
        stop_engine_cb=stop_engine,
        engine_holder=lambda: engine_box["engine"],
    )
    guard.show_requested.connect(tray._open_window)

    if not args.tray:
        tray._open_window()

    exit_code = app.exec()
    app_audio_binding.stop_watching()
    stop_engine()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
