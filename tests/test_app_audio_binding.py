"""Tests for app_audio_binding.py's pure decision logic - purely audio-
source narrowing, with no notion of presets/profiles at all, and at most
one selected app ever (mixing multiple sources is never possible). Anything
that actually shells out to pactl (enumeration, the tap sink/loopback
lifecycle) needs a real PipeWire/Pulse system and isn't exercised here."""
import app_audio_binding as aab


class TestDecide:
    def test_nothing_selected_is_global(self):
        assert aab._decide(None, set()) is False

    def test_selected_app_open_narrows_to_it(self):
        assert aab._decide("mpv", {"mpv"}) is True

    def test_selected_app_not_open_is_global(self):
        assert aab._decide("mpv", set()) is False


class TestBinaryName:
    def test_prefers_process_binary_over_application_name(self):
        si = {"properties": {"application.process.binary": "mpv", "application.name": "mpv media player"}}
        assert aab._binary_name(si) == "mpv"

    def test_falls_back_to_application_name(self):
        si = {"properties": {"application.name": "Firefox"}}
        assert aab._binary_name(si) == "Firefox"

    def test_no_properties_yields_none(self):
        assert aab._binary_name({}) is None
