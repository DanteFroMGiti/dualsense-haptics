"""Config persistence (presets/profiles/active state) and XDG autostart handling."""
import copy
import json
import os
from pathlib import Path

from haptics_engine import DEFAULT_CONFIG
from presets import preset_params
from i18n import detect_system_language

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "dualsense-haptics"
CONFIG_FILE = CONFIG_DIR / "config.json"
AUTOSTART_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "autostart"
AUTOSTART_FILE = AUTOSTART_DIR / "dualsense-haptics.desktop"

APP_DIR = Path(__file__).resolve().parent


def _merge_defaults(cfg, defaults):
    for k, v in defaults.items():
        if k not in cfg:
            cfg[k] = copy.deepcopy(v)
        elif isinstance(v, dict) and isinstance(cfg.get(k), dict):
            _merge_defaults(cfg[k], v)
    return cfg


def _migrate_led_visualizer(cfg):
    """In place: converts the pre-preset-system "led_visualizer" shape (a
    lone, always-audio-reactive dict) into the new "led" preset-system
    shape, carrying the user's own values forward as the "immersive"
    preset. Must run before _merge_defaults(), which would otherwise treat
    "led" as simply missing and fill it with fresh defaults, discarding
    whatever the user actually had. Desktop-only bookkeeping - the Decky
    plugin's own vendored haptics_engine.py tolerates the old shape
    directly at runtime instead (see _resolve_led_config() there), since
    its config isn't touched by this file at all."""
    old = cfg.pop("led_visualizer", None)
    if old is not None and "led" not in cfg:
        cfg["led"] = {"enabled": old.get("enabled", False), "preset": "immersive", "immersive": old}


def _default_state():
    return {
        # preset_params() only carries the DSP fields the presets dict
        # defines (bass/treble/gain) - merge in DEFAULT_CONFIG so fields
        # added later (button_haptics) exist even on a brand new install
        # with no config.json yet.
        "active": _merge_defaults(preset_params("balanced"), DEFAULT_CONFIG),
        "active_ref": "preset:balanced",
        "profiles": {},
        "trigger_preset_left": None,
        "trigger_preset_right": None,
        "trigger_custom_left": None,
        "trigger_custom_right": None,
        "trigger_auto_reconnect": True,
        # Per-side overrides for a preset's own inline "quick" sliders (e.g.
        # Hard Stop's strength/snap) - keyed by preset id, only ever holds
        # entries for presets.TRIGGER_PRESET_QUICK_PARAMS keys.
        "trigger_preset_params_left": {},
        "trigger_preset_params_right": {},
        # Per-side, per-preset "snap click" checkbox (presets.TRIGGER_PRESET_SNAP_CLICK).
        "trigger_snap_click_left": {},
        "trigger_snap_click_right": {},
        # Per-side, per-preset snap click strength (1-8, the click's own
        # vibration amplitude - independent of the preset's "snap"/hardware
        # snap-force quick slider).
        "trigger_snap_click_strength_left": {},
        "trigger_snap_click_strength_right": {},
        # Per-side "snap click on wall zones" checkbox for the custom
        # trigger builder's feedback-raw mode.
        "trigger_custom_snap_click_left": False,
        "trigger_custom_snap_click_right": False,
        # Desktop-only per-app audio binding (see app_audio_binding.py).
        # Master toggle defaults off - creates a virtual PipeWire sink, so
        # it's opt-in. Purely narrows which audio the engine listens to;
        # unrelated to (and never touches) presets/profiles.
        "app_audio_binding_enabled": False,
        # App names (application.process.binary) the user has added on the
        # "App Sound" page.
        "app_audio_binding_apps": [],
        # At most one of the above, or None for Global - mutually exclusive
        # by construction (the UI uses a radio-button group), so mixing
        # multiple audio sources is never possible. While the selected
        # app is producing sound, capture narrows to it; otherwise (nothing
        # selected, or it isn't currently making sound) capture stays on
        # the full system ("Global").
        "app_audio_binding_selected": None,
        "theme": "system",
        "language": detect_system_language(),
        "sidebar_collapsed": False,
    }


def load_state():
    """Returns {"active": {...engine params...}, "active_ref": str, "profiles": {name: params}}."""
    if not CONFIG_FILE.exists():
        return _default_state()
    try:
        raw = json.loads(CONFIG_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return _default_state()

    if "active" not in raw:
        # Old flat-params format from before presets/profiles existed - keep it
        # as a user profile so nothing from prior tuning gets lost.
        _migrate_led_visualizer(raw)
        old_params = _merge_defaults(raw, DEFAULT_CONFIG)
        state = _default_state()
        state["active"] = old_params
        state["active_ref"] = "profile:Мои настройки"
        state["profiles"] = {"Мои настройки": copy.deepcopy(old_params)}
        return state

    state = _default_state()
    raw_active = raw.get("active", {})
    _migrate_led_visualizer(raw_active)
    state["active"] = _merge_defaults(raw_active, DEFAULT_CONFIG)

    old_bh = state["active"].pop("button_haptic", None)
    if old_bh and old_bh.get("button_code") is not None:
        # Old single-button format - carry it over as one entry in the new
        # multi-button dict.
        state["active"]["button_haptics"][str(old_bh["button_code"])] = {
            "enabled": old_bh.get("enabled", False),
            "strength": old_bh.get("strength", 0.4),
        }

    state["active_ref"] = raw.get("active_ref", "custom")
    state["profiles"] = raw.get("profiles", {})
    if "trigger_preset" in raw:
        # Old single-preset-for-both-sides format - carry it over to both.
        state["trigger_preset_left"] = raw["trigger_preset"]
        state["trigger_preset_right"] = raw["trigger_preset"]
    else:
        state["trigger_preset_left"] = raw.get("trigger_preset_left")
        state["trigger_preset_right"] = raw.get("trigger_preset_right")
    state["trigger_custom_left"] = raw.get("trigger_custom_left")
    state["trigger_custom_right"] = raw.get("trigger_custom_right")
    state["trigger_auto_reconnect"] = raw.get("trigger_auto_reconnect", True)
    state["trigger_preset_params_left"] = raw.get("trigger_preset_params_left", {})
    state["trigger_preset_params_right"] = raw.get("trigger_preset_params_right", {})
    state["trigger_snap_click_left"] = raw.get("trigger_snap_click_left", {})
    state["trigger_snap_click_right"] = raw.get("trigger_snap_click_right", {})
    state["trigger_snap_click_strength_left"] = raw.get("trigger_snap_click_strength_left", {})
    state["trigger_snap_click_strength_right"] = raw.get("trigger_snap_click_strength_right", {})
    state["trigger_custom_snap_click_left"] = raw.get("trigger_custom_snap_click_left", False)
    state["trigger_custom_snap_click_right"] = raw.get("trigger_custom_snap_click_right", False)
    state["app_audio_binding_enabled"] = raw.get("app_audio_binding_enabled", False)
    raw_apps = raw.get("app_audio_binding_apps")
    if isinstance(raw_apps, list):
        state["app_audio_binding_apps"] = raw_apps
        state["app_audio_binding_selected"] = raw.get("app_audio_binding_selected")
    elif isinstance(raw_apps, dict):
        # Migrate from this feature's second format: a dict of app ->
        # {"enabled": bool}, before "only one active at a time" was
        # enforced (multiple apps could independently be "enabled"). Picks
        # whichever was enabled first as the initial single selection;
        # every app carries forward into the new plain list either way.
        state["app_audio_binding_apps"] = list(raw_apps)
        state["app_audio_binding_selected"] = next(
            (name for name, cfg in raw_apps.items() if cfg.get("enabled")), None)
    else:
        # Migrate from this feature's original format (a known-apps list
        # plus a per-profile bound_apps list, back when adding an app meant
        # picking which profile it activated) - carries forward whatever the
        # user already set up rather than dropping it.
        names = set(raw.get("app_audio_binding_known_apps", []))
        selected = None
        for params in raw.get("profiles", {}).values():
            for name in params.get("bound_apps", []):
                names.add(name)
                selected = selected or name
        state["app_audio_binding_apps"] = sorted(names)
        state["app_audio_binding_selected"] = selected
    state["theme"] = raw.get("theme", "system")
    state["language"] = raw.get("language", detect_system_language())
    state["sidebar_collapsed"] = raw.get("sidebar_collapsed", False)
    for name, params in state["profiles"].items():
        _migrate_led_visualizer(params)
        _merge_defaults(params, DEFAULT_CONFIG)
    return state


def save_state(state):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def is_autostart_enabled():
    return AUTOSTART_FILE.exists()


def set_autostart(enabled):
    if enabled:
        AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
        installed_bin = Path("/usr/bin/dualsense-haptics")
        exec_line = "dualsense-haptics --tray" if installed_bin.exists() else f'python3 "{APP_DIR / "main.py"}" --tray'
        entry = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=DualSense Haptics\n"
            f"Exec={exec_line}\n"
            "Icon=input-gaming\n"
            "X-GNOME-Autostart-enabled=true\n"
            "NoDisplay=false\n"
            "Terminal=false\n"
        )
        AUTOSTART_FILE.write_text(entry)
    else:
        if AUTOSTART_FILE.exists():
            AUTOSTART_FILE.unlink()
