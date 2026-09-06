"""Built-in presets: ready-made parameter sets for the haptics engine.

Display text (label/description) lives in i18n.py, keyed off each preset id
as `preset_<id>_label` / `preset_<id>_desc` (and `trigger_<id>_label` /
`trigger_<id>_desc` for trigger presets) - this module only holds data.
"""
import copy

PRESETS = {
    "balanced": {
        "params": {
            "master_gain": 1.0,
            "bass_cutoff_hz": 90, "treble_cutoff_hz": 500,
            "bass": {"attack": 0.95, "release": 0.5, "lo": 0.010, "hi": 0.12, "gamma": 1.3},
            "treble": {"attack": 0.95, "release": 0.55, "lo": 0.003, "hi": 0.045, "gamma": 0.7},
            "bass_ceiling": {"attack_s": 0.08, "release_s": 2.5},
            "treble_ceiling": {"attack_s": 0.05, "release_s": 2.0},
        },
    },
    "cinema": {
        "params": {
            "master_gain": 1.1,
            "bass_cutoff_hz": 90, "treble_cutoff_hz": 500,
            "bass": {"attack": 0.95, "release": 0.45, "lo": 0.020, "hi": 0.16, "gamma": 1.6},
            "treble": {"attack": 0.9, "release": 0.5, "lo": 0.006, "hi": 0.08, "gamma": 1.0},
            "bass_ceiling": {"attack_s": 0.10, "release_s": 3.0},
            "treble_ceiling": {"attack_s": 0.08, "release_s": 2.5},
        },
    },
    "music": {
        "params": {
            "master_gain": 1.2,
            "bass_cutoff_hz": 90, "treble_cutoff_hz": 500,
            "bass": {"attack": 0.97, "release": 0.6, "lo": 0.008, "hi": 0.10, "gamma": 1.1},
            "treble": {"attack": 0.97, "release": 0.6, "lo": 0.0025, "hi": 0.04, "gamma": 0.8},
            "bass_ceiling": {"attack_s": 0.06, "release_s": 1.5},
            "treble_ceiling": {"attack_s": 0.04, "release_s": 1.2},
        },
    },
    "voice": {
        "params": {
            "master_gain": 1.0,
            "bass_cutoff_hz": 90, "treble_cutoff_hz": 500,
            "bass": {"attack": 0.95, "release": 0.5, "lo": 0.025, "hi": 0.22, "gamma": 1.8},
            "treble": {"attack": 0.95, "release": 0.55, "lo": 0.003, "hi": 0.045, "gamma": 0.7},
            "bass_ceiling": {"attack_s": 0.08, "release_s": 2.5},
            "treble_ceiling": {"attack_s": 0.05, "release_s": 2.0},
        },
    },
    "max": {
        "params": {
            "master_gain": 1.3,
            "bass_cutoff_hz": 90, "treble_cutoff_hz": 500,
            "bass": {"attack": 0.97, "release": 0.6, "lo": 0.004, "hi": 0.05, "gamma": 0.8},
            "treble": {"attack": 0.97, "release": 0.65, "lo": 0.0015, "hi": 0.02, "gamma": 0.6},
            "bass_ceiling": {"attack_s": 0.3, "release_s": 1.0},
            "treble_ceiling": {"attack_s": 0.3, "release_s": 1.0},
        },
    },
}

PRESET_ORDER = ["balanced", "cinema", "music", "voice", "max"]


def preset_params(preset_id):
    return copy.deepcopy(PRESETS[preset_id]["params"])


# Adaptive trigger presets, as (mode, values) - run through the same
# dualsensectl argument builder as the custom trigger editor
# (triggers.build_custom_args). See TRIGGER_EFFECT_PARAMS below for what
# each mode's fields mean and their valid ranges (from dualsensectl's own
# validation in main.c).
TRIGGER_PRESETS = {
    "soft": {"mode": "feedback", "values": {"position": 2, "strength": 3}},
    # Free travel, then a hard wall right before full pull. Uses "bow" (not
    # "feedback") so the firmware itself renders a real mechanical snap when
    # you push through it - start/end are kept one zone apart so the ramp
    # into the wall is as short as possible, closest to "feedback"'s feel.
    "hard_wall": {"mode": "bow", "values": {"start": 7, "end": 8, "strength": 8, "snap": 8}},
    "weapon": {"mode": "weapon", "values": {"start": 3, "end": 6, "strength": 6}},
    "bow": {"mode": "bow", "values": {"start": 2, "end": 7, "strength": 6, "snap": 8}},
    # Full pull range and max on/off contrast (0/7, firmware's own ceiling
    # for strength) so it crackles for the whole time the trigger is held,
    # not just a slice of it - frequency is the app's own (uncapped by
    # firmware) ceiling, see TRIGGER_EFFECT_PARAMS["machine"].
    "machine": {"mode": "machine", "values": {"start": 1, "end": 9, "strength_a": 0, "strength_b": 7,
                                               "frequency": 20, "period": 2}},
    "clicker": {"mode": "vibration", "values": {"position": 1, "amplitude": 6, "frequency": 3}},
    "gallop": {"mode": "galloping", "values": {"start": 1, "end": 8, "first_foot": 3, "second_foot": 5,
                                                "frequency": 5}},
    # Both confirmed against real hardware: same "vibration" effect as
    # clicker/gallop, both at max frequency but opposite ends of amplitude -
    # max amplitude reads as a rapid, powerful burst (automatic fire), low
    # amplitude blurs into a smooth, weak, steady buzz (idling engine).
    "strong_click": {"mode": "vibration", "values": {"position": 1, "amplitude": 8, "frequency": 15}},
    "engine_hum": {"mode": "vibration", "values": {"position": 1, "amplitude": 2, "frequency": 15}},
}

TRIGGER_PRESET_ORDER = ["soft", "hard_wall", "weapon", "bow", "machine", "clicker", "gallop",
                         "strong_click", "engine_hum"]

# Presets whose own most-relevant parameter(s) get an inline slider right on
# their card, so tuning them doesn't need the separate custom trigger
# builder below - each key must exist in that preset's mode entry in
# TRIGGER_EFFECT_PARAMS. Order here is the order the sliders are shown in.
TRIGGER_PRESET_QUICK_PARAMS = {
    "hard_wall": ["strength", "snap"],
    "bow": ["strength", "snap"],
    "machine": ["frequency"],
    "clicker": ["amplitude", "frequency"],
}

# Presets built on the "bow" effect, whose mechanical snap can optionally be
# layered with a one-shot vibration click fired the instant it happens (the
# firmware can't combine a static resistance/snap effect with a vibration
# pulse in one HID report - see triggers.start_snap_click). Value is
# whether the checkbox defaults to on.
TRIGGER_PRESET_SNAP_CLICK = {"hard_wall": True, "bow": True}

# Custom trigger effect builder: raw dualsensectl parameters per effect
# mode, as (key, lo, hi, default). Ranges are copied from dualsensectl's own
# validation (main.c command_trigger_*), not guessed - e.g. "end"-style
# params there must exceed their paired "start", which the UI doesn't
# enforce live but triggers.build_custom_args() auto-corrects on apply.
TRIGGER_EFFECT_ORDER = ["off", "feedback", "weapon", "bow", "machine", "galloping", "vibration",
                         "feedback_raw", "vibration_raw"]

TRIGGER_EFFECT_PARAMS = {
    "off": [],
    "feedback": [
        ("position", 0, 9, 2),
        ("strength", 1, 8, 3),
    ],
    "weapon": [
        ("start", 2, 7, 3),
        ("end", 3, 8, 6),
        ("strength", 1, 8, 6),
    ],
    "bow": [
        ("start", 1, 8, 2),
        ("end", 2, 8, 7),
        ("strength", 1, 8, 6),
        ("snap", 1, 8, 8),
    ],
    "machine": [
        ("start", 1, 8, 2),
        ("end", 2, 9, 8),
        ("strength_a", 0, 7, 1),
        ("strength_b", 0, 7, 7),
        # dualsensectl/the firmware only require frequency > 0 - no upper
        # bound - unlike every other mode's frequency field, which we cap at
        # 15 to match community convention. Raised here specifically so the
        # Machine Gun preset/card can go faster than that.
        ("frequency", 1, 40, 4),
        ("period", 0, 15, 2),
    ],
    "galloping": [
        ("start", 0, 8, 1),
        ("end", 1, 9, 8),
        ("first_foot", 0, 6, 3),
        ("second_foot", 1, 7, 5),
        ("frequency", 1, 15, 5),
    ],
    "vibration": [
        ("position", 0, 9, 1),
        ("amplitude", 1, 8, 6),
        ("frequency", 1, 15, 3),
    ],
    # feedback-raw: per-zone resistance strength, one slider per zone along
    # the pull (z0 = start, z9 = fully pulled), 0 = no resistance at that
    # zone. dualsensectl's feedback-raw has no frequency/amplitude parameter
    # at all - it's a static resistance shape, not a vibrating effect.
    "feedback_raw": [(f"s{i}", 0, 8, 0) for i in range(10)],
    # vibration-raw: same per-zone array, but as buzz amplitude rather than
    # static resistance, plus the one shared frequency all zones vibrate at.
    "vibration_raw": [(f"a{i}", 0, 8, 0) for i in range(10)] + [("frequency", 1, 15, 5)],
}

# dualsensectl's CLI spells these with a hyphen ("feedback-raw"), which isn't
# a valid Python identifier/dict-key-as-mode-name elsewhere in this app - map
# the internal snake_case mode id to the literal CLI argument on apply.
TRIGGER_RAW_CLI_NAME = {"feedback_raw": "feedback-raw", "vibration_raw": "vibration-raw"}

# A feedback-raw resistance zone reads as a "hard" section - fair game for a
# layered one-shot click (see triggers.start_snap_click) - once its own
# strength is at least this fraction of the slider's max (8).
FEEDBACK_RAW_WALL_THRESHOLD = 6


def wall_zones_from_feedback_raw(values):
    """The set of zone indices (0-9) a multi-stage feedback-raw shape treats
    as a hard obstacle, i.e. candidates for a snap click - any zone at or
    above FEEDBACK_RAW_WALL_THRESHOLD."""
    return {i for i in range(10) if values.get(f"s{i}", 0) >= FEEDBACK_RAW_WALL_THRESHOLD}
