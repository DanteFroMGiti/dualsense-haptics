"""Tests for bt_hid_proxy.py's LED preset math (compute_led_output() and
its per-preset helpers) - all pure functions of elapsed time (or, for
"battery", a percentage), so fully deterministic and hardware-free."""
import bt_hid_proxy as bt


class TestComputeLedOutputDispatch:
    def test_unknown_preset_is_off(self):
        rgb, mask = bt.compute_led_output({"preset": "nonsense"}, now=0.0)
        assert rgb == (0, 0, 0)
        assert mask == (False,) * 5

    def test_immersive_with_no_audio_is_off(self):
        rgb, mask = bt.compute_led_output({"preset": "immersive"}, now=0.0, audio_led=None)
        assert rgb == (0, 0, 0)
        assert mask == (False,) * 5

    def test_immersive_uses_led_rgb_and_bar(self):
        expected_rgb, expected_lit = bt.led_rgb_and_bar((1.0, 0.0, 0.0, 0.6))
        rgb, mask = bt.compute_led_output({"preset": "immersive"}, now=0.0, audio_led=(1.0, 0.0, 0.0, 0.6))
        assert rgb == expected_rgb
        assert mask == tuple(i < expected_lit for i in range(5))

    def test_immersive_default_colors_match_the_module_constants(self):
        rgb, _ = bt.compute_led_output({"preset": "immersive", "immersive": {}}, now=0.0,
                                        audio_led=(1.0, 0.0, 0.0, 0.0))
        assert rgb == bt.BASS_COLOR

    def test_immersive_custom_bass_color_overrides_the_default(self):
        cfg = {"preset": "immersive", "immersive": {"bass_color": [10, 20, 30]}}
        rgb, _ = bt.compute_led_output(cfg, now=0.0, audio_led=(1.0, 0.0, 0.0, 0.0))
        assert rgb == (10, 20, 30)

    def test_immersive_custom_colors_still_mix_and_duck_like_before(self):
        # Same mixing/ducking algorithm as led_rgb_and_bar() itself, just
        # with substituted colors - cross-check against calling it directly
        # with the same custom colors.
        cfg = {"preset": "immersive",
               "immersive": {"bass_color": [10, 20, 30], "mid_color": [40, 50, 60],
                              "treble_color": [70, 80, 90]}}
        audio_led = (0.8, 0.5, 0.2, 0.6)
        expected_rgb, expected_lit = bt.led_rgb_and_bar(
            audio_led, ([10, 20, 30], [40, 50, 60], [70, 80, 90]))
        rgb, mask = bt.compute_led_output(cfg, now=0.0, audio_led=audio_led)
        assert rgb == expected_rgb
        assert mask == tuple(i < expected_lit for i in range(5))

    def test_immersive_is_not_affected_by_a_brightness_key(self):
        # brightness is deliberately not a thing for Immersive - even if
        # one somehow ended up in its config, it must be ignored.
        cfg = {"preset": "immersive", "immersive": {"brightness": 0.1}}
        rgb, _ = bt.compute_led_output(cfg, now=0.0, audio_led=(1.0, 0.0, 0.0, 0.0))
        assert rgb == bt.BASS_COLOR


class TestBrightness:
    def test_full_brightness_is_unchanged(self):
        rgb, _ = bt.compute_led_output(
            {"preset": "static", "static": {"color": [200, 100, 50], "brightness": 1.0}}, now=0.0)
        assert rgb == (200, 100, 50)

    def test_half_brightness_scales_every_channel(self):
        rgb, _ = bt.compute_led_output(
            {"preset": "static", "static": {"color": [200, 100, 50], "brightness": 0.5}}, now=0.0)
        assert rgb == (100, 50, 25)

    def test_zero_brightness_is_off(self):
        rgb, _ = bt.compute_led_output(
            {"preset": "static", "static": {"color": [200, 100, 50], "brightness": 0.0}}, now=0.0)
        assert rgb == (0, 0, 0)

    def test_missing_brightness_defaults_to_full(self):
        rgb, _ = bt.compute_led_output({"preset": "static", "static": {"color": [200, 100, 50]}}, now=0.0)
        assert rgb == (200, 100, 50)

    def test_out_of_range_brightness_is_clamped(self):
        rgb, _ = bt.compute_led_output(
            {"preset": "static", "static": {"color": [200, 100, 50], "brightness": 5.0}}, now=0.0)
        assert rgb == (200, 100, 50)

    def test_applies_to_rainbow_too(self):
        rgb_full, _ = bt.compute_led_output(
            {"preset": "rainbow", "rainbow": {"interval_s": 6.0, "brightness": 1.0}}, now=0.0)
        rgb_half, _ = bt.compute_led_output(
            {"preset": "rainbow", "rainbow": {"interval_s": 6.0, "brightness": 0.5}}, now=0.0)
        assert rgb_full == (255, 0, 0)
        assert rgb_half == (128, 0, 0)

    def test_applies_to_battery_too(self):
        cfg = {"high_color": [0, 255, 0], "brightness": 0.5}
        rgb, _ = bt.compute_led_output({"preset": "battery", "battery": cfg}, now=0.0, battery_pct=100)
        assert rgb == (0, 128, 0)


class TestStatic:
    def test_fixed_color_all_leds_on(self):
        rgb, mask = bt.compute_led_output({"preset": "static", "static": {"color": [10, 20, 30]}}, now=123.0)
        assert rgb == (10, 20, 30)
        assert mask == (True,) * 5

    def test_defaults_when_no_color_given(self):
        rgb, _ = bt.compute_led_output({"preset": "static", "static": {}}, now=0.0)
        assert rgb == (255, 255, 255)


class TestBreathing:
    def test_dark_at_phase_zero(self):
        cfg = {"preset": "breathing", "breathing": {"color": [255, 0, 0], "interval_s": 2.0}}
        rgb, mask = bt.compute_led_output(cfg, now=0.0)
        assert rgb == (0, 0, 0)
        assert mask == (True,) * 5

    def test_full_brightness_at_half_period(self):
        cfg = {"preset": "breathing", "breathing": {"color": [255, 0, 0], "interval_s": 2.0}}
        rgb, _ = bt.compute_led_output(cfg, now=1.0)  # half of a 2s period
        assert rgb == (255, 0, 0)

    def test_wraps_around_to_dark_at_a_full_period(self):
        cfg = {"preset": "breathing", "breathing": {"color": [255, 0, 0], "interval_s": 2.0}}
        rgb, _ = bt.compute_led_output(cfg, now=2.0)
        assert rgb == (0, 0, 0)


class TestRainbow:
    def test_hue_zero_is_pure_red(self):
        rgb, mask = bt.compute_led_output({"preset": "rainbow", "rainbow": {"interval_s": 6.0}}, now=0.0)
        assert rgb == (255, 0, 0)
        assert mask == (True,) * 5

    def test_wraps_back_to_red_at_a_full_period(self):
        rgb, _ = bt.compute_led_output({"preset": "rainbow", "rainbow": {"interval_s": 6.0}}, now=6.0)
        assert rgb == (255, 0, 0)

    def test_hue_advances_partway_through_the_period(self):
        rgb_start, _ = bt.compute_led_output({"preset": "rainbow", "rainbow": {"interval_s": 6.0}}, now=0.0)
        rgb_mid, _ = bt.compute_led_output({"preset": "rainbow", "rainbow": {"interval_s": 6.0}}, now=3.0)
        assert rgb_mid != rgb_start


class TestWave:
    def test_exactly_one_led_lit_at_any_moment(self):
        cfg = {"preset": "wave", "wave": {"color": [0, 128, 255], "interval_s": 0.8}}
        for now in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7):
            _, mask = bt.compute_led_output(cfg, now=now)
            assert sum(mask) == 1, f"now={now} mask={mask}"

    def test_starts_and_ends_at_position_zero(self):
        cfg = {"preset": "wave", "wave": {"color": [0, 128, 255], "interval_s": 0.8}}
        _, mask_start = bt.compute_led_output(cfg, now=0.0)
        assert mask_start == (True, False, False, False, False)

    def test_reaches_the_far_end_at_the_midpoint(self):
        cfg = {"preset": "wave", "wave": {"color": [0, 128, 255], "interval_s": 0.8}}
        _, mask_mid = bt.compute_led_output(cfg, now=0.4)  # half of 0.8s = the 5th (index-4) step
        assert mask_mid == (False, False, False, False, True)

    def test_color_is_fixed_not_animated(self):
        cfg = {"preset": "wave", "wave": {"color": [0, 128, 255], "interval_s": 0.8}}
        rgb, _ = bt.compute_led_output(cfg, now=0.3)
        assert rgb == (0, 128, 255)


class TestHeartbeat:
    def test_at_rest_between_beats(self):
        cfg = {"preset": "heartbeat", "heartbeat": {"color": [255, 0, 0], "interval_s": 1.2}}
        rgb, _ = bt.compute_led_output(cfg, now=1.0)  # phase ~0.83, past both pulses
        assert rgb == (0, 0, 0)

    def test_first_pulse_peaks_near_its_center(self):
        cfg = {"preset": "heartbeat", "heartbeat": {"color": [255, 0, 0], "interval_s": 1.0}}
        rgb, _ = bt.compute_led_output(cfg, now=0.08)  # exactly the first pulse's center
        assert rgb == (255, 0, 0)

    def test_two_distinct_pulses_separated_by_a_dip(self):
        cfg = {"preset": "heartbeat", "heartbeat": {"color": [255, 0, 0], "interval_s": 1.0}}
        rgb_first, _ = bt.compute_led_output(cfg, now=0.08)
        rgb_between, _ = bt.compute_led_output(cfg, now=0.18)
        rgb_second, _ = bt.compute_led_output(cfg, now=0.28)
        assert rgb_first == (255, 0, 0)
        assert rgb_between == (0, 0, 0)
        assert rgb_second == (255, 0, 0)


class TestBattery:
    def test_low_charge_is_low_color(self):
        cfg = {"low_color": [255, 0, 0], "mid_color": [255, 200, 0], "high_color": [0, 255, 0],
               "low_threshold": 25, "mid_threshold": 60}
        rgb, mask = bt.compute_led_output({"preset": "battery", "battery": cfg}, now=0.0, battery_pct=10)
        assert rgb == (255, 0, 0)
        assert sum(mask) == 1  # a bar sized to ~10% still shows at least one LED

    def test_mid_charge_is_mid_color(self):
        cfg = {"low_color": [255, 0, 0], "mid_color": [255, 200, 0], "high_color": [0, 255, 0],
               "low_threshold": 25, "mid_threshold": 60}
        rgb, _ = bt.compute_led_output({"preset": "battery", "battery": cfg}, now=0.0, battery_pct=40)
        assert rgb == (255, 200, 0)

    def test_high_charge_is_high_color_and_full_bar(self):
        cfg = {"low_color": [255, 0, 0], "mid_color": [255, 200, 0], "high_color": [0, 255, 0],
               "low_threshold": 25, "mid_threshold": 60}
        rgb, mask = bt.compute_led_output({"preset": "battery", "battery": cfg}, now=0.0, battery_pct=100)
        assert rgb == (0, 255, 0)
        assert mask == (True,) * 5

    def test_unknown_battery_percent_assumes_full(self):
        cfg = {"low_color": [255, 0, 0], "mid_color": [255, 200, 0], "high_color": [0, 255, 0],
               "low_threshold": 25, "mid_threshold": 60}
        rgb, _ = bt.compute_led_output({"preset": "battery", "battery": cfg}, now=0.0, battery_pct=None)
        assert rgb == (0, 255, 0)


class TestCustom:
    def test_shows_the_first_color_at_time_zero(self):
        cfg = {"colors": [[255, 0, 0], [0, 255, 0], [0, 0, 255]], "interval_s": 2.0}
        rgb, mask = bt.compute_led_output({"preset": "custom", "custom": cfg}, now=0.0)
        assert rgb == (255, 0, 0)
        assert mask == (True,) * 5

    def test_advances_to_the_next_color_after_one_interval(self):
        cfg = {"colors": [[255, 0, 0], [0, 255, 0], [0, 0, 255]], "interval_s": 2.0}
        rgb, _ = bt.compute_led_output({"preset": "custom", "custom": cfg}, now=2.5)
        assert rgb == (0, 255, 0)

    def test_wraps_back_to_the_first_color(self):
        cfg = {"colors": [[255, 0, 0], [0, 255, 0], [0, 0, 255]], "interval_s": 2.0}
        rgb, _ = bt.compute_led_output({"preset": "custom", "custom": cfg}, now=6.5)  # wraps past all 3
        assert rgb == (255, 0, 0)

    def test_empty_color_list_falls_back_to_white(self):
        rgb, _ = bt.compute_led_output({"preset": "custom", "custom": {"colors": []}}, now=0.0)
        assert rgb == (255, 255, 255)

    def test_zero_fade_is_an_instant_cut(self):
        cfg = {"colors": [[255, 0, 0], [0, 255, 0]], "interval_s": 2.0, "fade_s": 0.0}
        rgb, _ = bt.compute_led_output({"preset": "custom", "custom": cfg}, now=1.999)
        assert rgb == (255, 0, 0)

    def test_holds_solid_before_the_fade_window(self):
        cfg = {"colors": [[255, 0, 0], [0, 255, 0]], "interval_s": 2.0, "fade_s": 0.5}
        rgb, _ = bt.compute_led_output({"preset": "custom", "custom": cfg}, now=1.0)
        assert rgb == (255, 0, 0)

    def test_blends_halfway_through_the_fade_window(self):
        cfg = {"colors": [[255, 0, 0], [0, 255, 0]], "interval_s": 2.0, "fade_s": 1.0}
        # fade window is [1.0, 2.0) - now=1.5 is exactly halfway through it
        rgb, _ = bt.compute_led_output({"preset": "custom", "custom": cfg}, now=1.5)
        assert rgb == (128, 128, 0)

    def test_reaches_the_next_color_at_the_end_of_the_fade_window(self):
        cfg = {"colors": [[255, 0, 0], [0, 255, 0]], "interval_s": 2.0, "fade_s": 1.0}
        rgb, _ = bt.compute_led_output({"preset": "custom", "custom": cfg}, now=1.999)
        assert rgb == (0, 255, 0)

    def test_fade_longer_than_interval_is_clamped_to_a_full_slot_crossfade(self):
        cfg = {"colors": [[255, 0, 0], [0, 255, 0]], "interval_s": 2.0, "fade_s": 10.0}
        rgb, _ = bt.compute_led_output({"preset": "custom", "custom": cfg}, now=0.0)
        assert rgb == (255, 0, 0)  # no hold at all - fading starts immediately
        rgb_mid, _ = bt.compute_led_output({"preset": "custom", "custom": cfg}, now=1.0)
        assert rgb_mid == (128, 128, 0)
