"""Tests for config.py: default state, save/load roundtrip, and - most
importantly - the legacy-format migrations, which only ever run on real
users' old config files and so are exactly the code nobody exercises when
developing against a fresh checkout."""
import json

import pytest

import config
from haptics_engine import DEFAULT_CONFIG


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")
    return tmp_path


def _write_raw(data):
    config.CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False))


class TestMergeDefaults:
    def test_fills_missing_keys_with_deep_copies(self):
        cfg = {}
        config._merge_defaults(cfg, DEFAULT_CONFIG)
        assert cfg["bass"] == DEFAULT_CONFIG["bass"]
        cfg["bass"]["gamma"] = 999
        assert DEFAULT_CONFIG["bass"]["gamma"] != 999

    def test_keeps_existing_values(self):
        cfg = {"master_gain": 2.5, "bass": {"gamma": 3.0}}
        config._merge_defaults(cfg, DEFAULT_CONFIG)
        assert cfg["master_gain"] == 2.5
        assert cfg["bass"]["gamma"] == 3.0
        # sibling keys inside the nested dict still get filled in
        assert cfg["bass"]["attack"] == DEFAULT_CONFIG["bass"]["attack"]


class TestDefaultState:
    def test_no_file_yields_balanced_preset(self):
        state = config.load_state()
        assert state["active_ref"] == "preset:balanced"
        assert state["profiles"] == {}
        assert state["trigger_auto_reconnect"] is True
        assert state["theme"] == "system"

    def test_app_audio_binding_defaults(self):
        state = config.load_state()
        assert state["app_audio_binding_enabled"] is False
        assert state["app_audio_binding_apps"] == []
        assert state["app_audio_binding_selected"] is None

    def test_active_carries_full_engine_schema(self):
        # preset params only define DSP fields; the merge must add the rest
        # (button_haptics, direct_audio, ...) so the engine never KeyErrors
        state = config.load_state()
        assert set(DEFAULT_CONFIG) <= set(state["active"])

    def test_unreadable_json_falls_back_to_defaults(self):
        config.CONFIG_FILE.write_text("{not json")
        state = config.load_state()
        assert state["active_ref"] == "preset:balanced"


class TestRoundtrip:
    def test_save_then_load_preserves_state(self):
        state = config.load_state()
        state["active"]["master_gain"] = 1.7
        state["active_ref"] = "custom"
        state["profiles"]["Мой"] = dict(state["active"])
        state["trigger_preset_left"] = "bow"
        state["trigger_custom_right"] = {"mode": "vibration", "params": {"position": 1}}
        state["theme"] = "dark"
        state["language"] = "ru"
        config.save_state(state)

        loaded = config.load_state()
        assert loaded["active"]["master_gain"] == 1.7
        assert loaded["active_ref"] == "custom"
        assert "Мой" in loaded["profiles"]
        assert loaded["trigger_preset_left"] == "bow"
        assert loaded["trigger_preset_right"] is None
        assert loaded["trigger_custom_right"] == {"mode": "vibration", "params": {"position": 1}}
        assert loaded["theme"] == "dark"
        assert loaded["language"] == "ru"

    def test_loaded_profiles_get_missing_defaults_filled(self):
        state = config.load_state()
        state["profiles"]["old"] = {"master_gain": 0.5}  # pre-button_haptics profile
        config.save_state(state)
        loaded = config.load_state()
        assert loaded["profiles"]["old"]["master_gain"] == 0.5
        assert "button_haptics" in loaded["profiles"]["old"]

    def test_app_audio_binding_apps_round_trip(self):
        state = config.load_state()
        state["app_audio_binding_apps"].append("firefox")
        state["app_audio_binding_selected"] = "firefox"
        config.save_state(state)
        loaded = config.load_state()
        assert loaded["app_audio_binding_apps"] == ["firefox"]
        assert loaded["app_audio_binding_selected"] == "firefox"


class TestLegacyMigrations:
    def test_flat_params_become_a_named_profile(self):
        # the original pre-presets format: engine params at the top level
        _write_raw({"master_gain": 1.4, "bass": {"gamma": 2.0}})
        state = config.load_state()
        assert state["active"]["master_gain"] == 1.4
        assert state["active_ref"] == "profile:Мои настройки"
        assert state["profiles"]["Мои настройки"]["master_gain"] == 1.4
        # and the migrated params still get the full schema merged in
        assert "direct_audio" in state["active"]

    def test_single_button_haptic_becomes_multi_button_entry(self):
        _write_raw({
            "active": {"button_haptic": {"button_code": 304, "enabled": True, "strength": 0.6}},
            "active_ref": "custom",
        })
        state = config.load_state()
        assert "button_haptic" not in state["active"]
        assert state["active"]["button_haptics"]["304"] == {"enabled": True, "strength": 0.6}

    def test_button_haptic_without_code_is_dropped(self):
        _write_raw({"active": {"button_haptic": {"button_code": None, "enabled": True}},
                    "active_ref": "custom"})
        state = config.load_state()
        assert state["active"]["button_haptics"] == {}

    def test_single_trigger_preset_applies_to_both_sides(self):
        _write_raw({"active": {}, "trigger_preset": "weapon"})
        state = config.load_state()
        assert state["trigger_preset_left"] == "weapon"
        assert state["trigger_preset_right"] == "weapon"

    def test_per_side_trigger_presets_pass_through(self):
        _write_raw({"active": {}, "trigger_preset_left": "soft", "trigger_preset_right": None})
        state = config.load_state()
        assert state["trigger_preset_left"] == "soft"
        assert state["trigger_preset_right"] is None

    def test_app_audio_binding_original_format_is_migrated(self):
        # The original format, before profiles were dropped from this
        # feature entirely: adding an app meant picking which profile it
        # switched to (a known-apps list plus each profile's own bound_apps
        # list) - migration carries all of that forward into the flat list,
        # picking one of the previously-bound apps as the initial selection.
        _write_raw({
            "active": {}, "active_ref": "custom",
            "app_audio_binding_known_apps": ["vlc"],
            "profiles": {"Movie": {"bound_apps": ["mpv"]}},
        })
        state = config.load_state()
        assert sorted(state["app_audio_binding_apps"]) == ["mpv", "vlc"]
        assert state["app_audio_binding_selected"] == "mpv"

    def test_app_audio_binding_second_format_is_migrated(self):
        # Before "only one active at a time" was enforced: a dict of app ->
        # {"enabled": bool}, where more than one could independently be on.
        _write_raw({
            "active": {}, "active_ref": "custom",
            "app_audio_binding_apps": {"vlc": {"enabled": False}, "mpv": {"enabled": True}},
        })
        state = config.load_state()
        assert sorted(state["app_audio_binding_apps"]) == ["mpv", "vlc"]
        assert state["app_audio_binding_selected"] == "mpv"

    def test_app_audio_binding_current_format_is_used_as_is(self):
        _write_raw({
            "active": {}, "active_ref": "custom",
            "app_audio_binding_apps": ["vlc"], "app_audio_binding_selected": "vlc",
        })
        state = config.load_state()
        assert state["app_audio_binding_apps"] == ["vlc"]
        assert state["app_audio_binding_selected"] == "vlc"

    def test_led_visualizer_is_migrated_to_the_led_preset_system(self):
        # Before the LED preset system existed: a lone, always-audio-
        # reactive "led_visualizer" dict - values must carry over as the
        # new "immersive" preset's own config, not get overwritten by
        # fresh defaults.
        _write_raw({
            "active": {"led_visualizer": {"enabled": True, "attack": 0.3, "release": 0.2,
                                           "gamma": 2.1, "bass_priority": 0.9}},
            "active_ref": "custom",
        })
        state = config.load_state()
        assert "led_visualizer" not in state["active"]
        led = state["active"]["led"]
        assert led["enabled"] is True
        assert led["preset"] == "immersive"
        assert led["immersive"]["attack"] == 0.3
        assert led["immersive"]["release"] == 0.2
        assert led["immersive"]["gamma"] == 2.1
        assert led["immersive"]["bass_priority"] == 0.9
        # a key the old led_visualizer format never had (added after this
        # migration existed) still gets backfilled by _merge_defaults
        assert led["immersive"]["bass_color"] == [255, 0, 0]
        # every other preset's defaults still get backfilled by _merge_defaults
        assert "static" in led and "rainbow" in led

    def test_led_new_format_is_left_untouched(self):
        _write_raw({
            "active": {"led": {"enabled": True, "preset": "rainbow", "rainbow": {"interval_s": 10.0}}},
            "active_ref": "custom",
        })
        state = config.load_state()
        assert state["active"]["led"]["preset"] == "rainbow"
        assert state["active"]["led"]["rainbow"]["interval_s"] == 10.0

    def test_led_visualizer_is_migrated_per_profile(self):
        _write_raw({
            "active": {}, "active_ref": "custom",
            "profiles": {"Old": {"led_visualizer": {"enabled": True, "attack": 0.4}}},
        })
        state = config.load_state()
        led = state["profiles"]["Old"]["led"]
        assert led["preset"] == "immersive"
        assert led["immersive"]["attack"] == 0.4
        assert "led_visualizer" not in state["profiles"]["Old"]
