"""Color palettes (dark/light) and QSS generation, with live system-theme
tracking so "System" follows the desktop's color scheme without a restart."""
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QGuiApplication

DARK = {
    "accent": "#168cff",
    "accent_hover": "#49a7ff",
    "accent_ink": "#ffffff",
    "bg": "#07111f",
    "bg_card": "#0f1c2d",
    "bg_sidebar": "#0a1423",
    "fg": "#f3f6ff",
    "fg_dim": "#8fa4c4",
    "good": "#35dc70",
    "warn": "#f4c95d",
    "bad": "#ff6572",
    "border": "#263b57",
    "pressed": "#122b49",
    "hero_start": "#111f31",
    "hero_end": "#071321",
    "selected_start": "#153d75",
    "active_card": "#12345a",
}

LIGHT = {
    "accent": "#087ef0",
    "accent_hover": "#2c95f5",
    "accent_ink": "#ffffff",
    "bg": "#eef4fb",
    "bg_card": "#ffffff",
    "bg_sidebar": "#e5eef9",
    "fg": "#13243b",
    "fg_dim": "#607795",
    "good": "#19a857",
    "warn": "#a3730a",
    "bad": "#c8373d",
    "border": "#c9d8ea",
    "pressed": "#dce9f8",
    "hero_start": "#ffffff",
    "hero_end": "#e9f3ff",
    "selected_start": "#c8e2ff",
    "active_card": "#dcecff",
}

PALETTES = {"dark": DARK, "light": LIGHT}


def system_theme():
    """Best-effort read of the desktop color scheme (Qt >= 6.5). Falls back
    to dark, which matches this app's original look, if unavailable."""
    try:
        scheme = QGuiApplication.styleHints().colorScheme()
        if scheme == Qt.ColorScheme.Light:
            return "light"
        if scheme == Qt.ColorScheme.Dark:
            return "dark"
    except Exception:
        pass
    return "dark"


def resolve(preference):
    if preference == "system":
        return system_theme()
    return preference if preference in PALETTES else "dark"


def build_stylesheet(p):
    return f"""
QWidget {{
    background: {p['bg']}; color: {p['fg']}; font-family: "Inter", "Segoe UI", sans-serif;
    font-size: 13px;
}}
QWidget#appWindow {{ background: {p['bg']}; }}
QWidget#sidebar {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['bg_sidebar']}, stop:0.72 {p['bg_sidebar']}, stop:1 {p['pressed']});
    border-right: 1px solid {p['border']};
}}
QStackedWidget#pageStack, QScrollArea, QScrollArea > QWidget > QWidget {{
    background: transparent; border: none;
}}
QLabel, QSlider, QCheckBox, QProgressBar {{ background: transparent; }}
QGroupBox {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['bg_card']}, stop:1 {p['bg']});
    border: 1px solid {p['border']}; border-radius: 14px;
    margin-top: 16px; padding: 16px; font-weight: 600;
}}
QGroupBox QWidget, QFrame#card QWidget, QFrame#cardActive QWidget,
QFrame#heroCard QWidget, QFrame#metricCard QWidget, QFrame#motorCard QWidget,
QFrame#sectionCard QWidget, QFrame#componentCard QWidget, QFrame#triggerPanel QWidget,
QFrame#presetCard QWidget, QFrame#featuredPreset QWidget, QFrame#triggerColumnHeader QWidget,
QFrame#triggerPresetCard QWidget, QFrame#triggerCustomCard QWidget,
QFrame#vibrationHero QWidget, QFrame#motorBalanceCard QWidget,
QFrame#buttonSideCard QWidget, QFrame#buttonPreviewCard QWidget,
QFrame#buttonProfileCard QWidget, QFrame#profileCard QWidget,
QFrame#profileDetailCard QWidget, QFrame#audioToggleCard QWidget,
QFrame#audioInfoCard QWidget, QFrame#appAudioRow QWidget {{ background: transparent; }}
QGroupBox::title {{
    subcontrol-origin: margin; left: 16px; padding: 0 6px; color: {p['fg']};
    font-size: 14px; font-weight: 700;
}}
QLabel[role="hint"] {{ color: {p['fg_dim']}; font-size: 12px; }}
QLabel[role="value"] {{ color: {p['accent_hover']}; font-weight: 700; min-width: 42px; }}
QLabel[role="h1"] {{ font-size: 28px; font-weight: 800; }}
QLabel[role="h2"] {{ font-size: 14px; font-weight: 700; color: {p['fg']}; }}
QLabel[role="eyebrow"] {{ color: {p['fg_dim']}; font-size: 10px; font-weight: 600; }}
QLabel[role="heroValue"] {{ color: {p['fg']}; font-size: 24px; font-weight: 800; }}
QLabel[role="accentLabel"] {{ color: {p['accent_hover']}; font-size: 12px; font-weight: 800; }}
QLabel[role="componentValue"] {{ color: {p['fg']}; font-size: 17px; font-weight: 800; }}
QLabel[role="profileName"] {{ color: {p['fg']}; font-size: 15px; font-weight: 800; }}
QLabel[role="profileTag"] {{
    color: {p['fg_dim']}; background: {p['hero_end']}; border: 1px solid {p['border']};
    border-radius: 8px; padding: 2px 8px; font-size: 10px; font-weight: 600;
}}
QLabel[role="profileArrow"] {{ color: {p['fg_dim']}; font-size: 26px; font-weight: 500; }}
QLabel[role="profileStar"] {{ color: {p['accent_hover']}; font-size: 24px; }}
QLabel#profileDragHandle {{ color: {p['fg_dim']}; font-size: 20px; font-weight: 700; }}
QLabel[role="audioActive"] {{ color: {p['good']}; font-size: 11px; font-weight: 800; }}
QLabel[role="audioWaiting"] {{ color: {p['warn']}; font-size: 11px; font-weight: 700; }}
QLabel[role="emptyState"] {{ color: {p['fg_dim']}; font-size: 13px; padding: 18px; }}
QLabel[role="presetBadge"] {{
    color: #d9d2ff; background: #5847ca; border: 1px solid #8575ff;
    border-radius: 9px; padding: 3px 8px; font-size: 10px; font-weight: 800;
}}
QLabel#triggerSideBadge, QLabel#triggerHeroBadge {{
    color: #cfe8ff; background: {p['selected_start']}; border: 1px solid {p['accent']};
    border-radius: 10px; font-size: 17px; font-weight: 800;
}}
QLabel#triggerCustomIcon {{
    color: #be8cff; background: #251f52; border: 1px solid #725ada;
    border-radius: 10px; font-size: 22px; font-weight: 800;
}}
QLabel#vibrationProfileIcon {{
    color: #63c4ff; background: #132c68; border: 1px solid #5168ff;
    border-radius: 15px; font-size: 31px; font-weight: 800;
}}
QLabel#vibrationGeneralIcon, QLabel#vibrationBandIcon {{
    color: {p['accent_hover']}; background: {p['pressed']}; border: 1px solid {p['border']};
    border-radius: 11px; font-size: 22px; font-weight: 800;
}}
QLabel#vibrationBandIcon[variant="bass"] {{ color: #a673ff; border-color: #684aa7; }}
QLabel#vibrationBandIcon[variant="treble"] {{ color: #39beff; border-color: #236f9d; }}
QLabel#buttonHapticIcon {{
    color: {p['accent_hover']}; background: {p['pressed']}; border: 1px solid {p['border']};
    border-radius: 10px; font-size: 11px; font-weight: 800;
}}
QLabel#buttonHapticIcon[pressed="true"] {{
    color: #dff5ff; background: {p['selected_start']}; border: 1px solid #67c8ff;
}}
QWidget#buttonHapticRow {{
    background: transparent; border: 1px solid transparent; border-radius: 10px;
}}
QWidget#buttonHapticRow[pressed="true"] {{
    background: qradialgradient(cx:0.12, cy:0.5, radius:0.75,
        stop:0 {p['selected_start']}, stop:1 transparent);
    border: 1px solid {p['accent']};
}}
QFrame#cardDivider {{ background: {p['border']}; color: {p['border']}; border: none; max-height: 1px; }}
QFrame#sectionCard QLabel[role="activeField"] {{
    color: {p['fg']}; background: {p['hero_end']}; border: 1px solid {p['border']};
    border-radius: 8px; padding: 7px 11px; font-size: 15px; font-weight: 700;
}}
QFrame#sectionCard QLabel#dashboardIcon {{
    color: {p['accent_hover']}; background: {p['pressed']}; border-radius: 21px;
    font-size: 22px; font-weight: 800;
}}
QFrame#ledPreview {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['hero_start']}, stop:0.62 {p['bg_card']}, stop:1 {p['hero_end']});
    border: 1px solid {p['border']}; border-radius: 13px;
}}
QLabel[role="status"] {{
    color: {p['good']}; background: {p['bg_card']}; border: 1px solid {p['border']};
    border-radius: 17px; padding: 8px 14px; font-size: 12px; font-weight: 600;
}}
QSlider::groove:horizontal {{ height: 7px; background: {p['border']}; border-radius: 3px; }}
QSlider::handle:horizontal {{
    background: #a7dcff; border: 2px solid {p['accent']}; width: 15px; height: 15px;
    margin: -6px 0; border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{ background: {p['accent_hover']}; }}
QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p['accent']}, stop:1 #63bdff); border-radius: 3px;
}}
QProgressBar, QFrame#motorCard QProgressBar, QFrame#triggerPanel QProgressBar,
QFrame#componentCard QProgressBar {{
    background: {p['border']}; border: none; border-radius: 4px; height: 8px;
    text-align: center; color: transparent;
}}
QProgressBar::chunk, QFrame#motorCard QProgressBar::chunk, QFrame#triggerPanel QProgressBar::chunk,
QFrame#componentCard QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p['accent']}, stop:1 #725cff); border-radius: 4px;
}}
QProgressBar[variant="bass"]::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 #b25cff, stop:1 #7d8dff); }}
QProgressBar[variant="treble"]::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 #2ed8f3, stop:1 #168cff); }}
QCheckBox {{ spacing: 10px; color: {p['fg_dim']}; }}
QCheckBox::indicator {{
    width: 18px; height: 18px; border: 1px solid {p['border']}; border-radius: 5px;
    background: {p['bg_card']};
}}
QCheckBox::indicator:hover {{ border-color: {p['accent']}; }}
QCheckBox::indicator:checked {{ background: {p['accent']}; border-color: {p['accent_hover']}; }}
QRadioButton {{ background: transparent; spacing: 10px; }}
QRadioButton::indicator {{
    width: 16px; height: 16px; border: 1px solid {p['fg_dim']};
    border-radius: 9px; background: {p['bg_card']};
}}
QRadioButton::indicator:checked {{
    background: {p['accent']}; border: 2px solid {p['accent_hover']};
}}
QRadioButton::indicator:hover {{ border-color: {p['accent']}; }}
QComboBox {{
    background: {p['bg_card']}; border: 1px solid {p['border']}; border-radius: 9px;
    padding: 9px 34px 9px 12px; min-height: 18px;
}}
QComboBox:hover {{ border-color: {p['accent']}; }}
QComboBox::drop-down {{
    subcontrol-origin: padding; subcontrol-position: top right; width: 24px;
    border: none; background: transparent;
}}
QComboBox::down-arrow {{
    image: none; width: 0; height: 0;
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 5px solid {p['fg_dim']};
    margin-right: 10px;
}}
QComboBox::down-arrow:on {{ border-top-color: {p['accent']}; }}
QComboBox QAbstractItemView {{
    background: {p['bg_card']}; color: {p['fg']}; border: 1px solid {p['border']};
    selection-background-color: {p['accent']}; selection-color: {p['accent_ink']};
}}
QPushButton {{
    background: {p['bg_card']}; border: 1px solid {p['border']}; border-radius: 9px;
    padding: 10px 18px; font-weight: 600;
}}
QPushButton:hover {{ border-color: {p['accent']}; background: {p['pressed']}; }}
QPushButton:pressed {{ background: {p['pressed']}; }}
QPushButton#danger:hover {{ border-color: {p['bad']}; }}
QPushButton#primary, QFrame#metricCard QPushButton#primary, QFrame#sectionCard QPushButton#primary,
QFrame#profileDetailCard QPushButton#primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p['accent']}, stop:1 #2767ee);
    color: {p['accent_ink']}; border: 1px solid {p['accent_hover']}; font-weight: 700;
}}
QPushButton#primary:hover, QFrame#metricCard QPushButton#primary:hover,
QFrame#sectionCard QPushButton#primary:hover,
QFrame#profileDetailCard QPushButton#primary:hover {{ background: {p['accent_hover']}; }}
QPushButton#primary:pressed, QFrame#metricCard QPushButton#primary:pressed,
QFrame#sectionCard QPushButton#primary:pressed,
QFrame#profileDetailCard QPushButton#primary:pressed {{ background: {p['accent']}; }}
QFrame#profileDetailCard QPushButton#danger {{ color: {p['bad']}; border-color: {p['bad']}; }}
QPushButton#filterChip {{
    background: {p['bg_card']}; color: {p['fg_dim']}; border: 1px solid {p['border']};
    border-radius: 9px; padding: 8px 14px; font-size: 12px;
}}
QPushButton#filterChip:hover {{ color: {p['fg']}; border-color: {p['accent']}; }}
QPushButton#filterChip:checked {{
    color: {p['fg']}; background: {p['selected_start']}; border: 1px solid {p['accent']};
    font-weight: 700;
}}
QToolButton#ledModeButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['hero_start']}, stop:1 {p['hero_end']});
    color: {p['fg_dim']}; border: 1px solid {p['border']}; border-radius: 12px;
    padding: 9px 8px; font-size: 12px; font-weight: 650; text-align: center;
}}
QToolButton#ledModeButton:hover {{
    color: {p['fg']}; border-color: {p['accent']}; background: {p['pressed']};
}}
QToolButton#ledModeButton:checked {{
    color: {p['fg']}; border: 2px solid {p['accent_hover']};
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['selected_start']}, stop:1 {p['active_card']});
}}
QPushButton#navItem {{
    background: transparent; border: 1px solid transparent; border-radius: 9px; text-align: left;
    padding: 11px 14px; font-size: 13px; color: {p['fg_dim']};
}}
QPushButton#navItem:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p['selected_start']}, stop:1 {p['bg_card']});
    border-color: #1c4f91; color: {p['fg']}; font-weight: 700;
}}
QPushButton#navItem:hover {{ color: {p['fg']}; background: {p['bg_card']}; }}
QPushButton#sidebarToggle {{
    background: transparent; border: none; border-radius: 8px; padding: 6px;
}}
QPushButton#sidebarToggle:hover {{ background: {p['bg_card']}; }}
QFrame#heroCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['hero_start']}, stop:0.55 {p['bg_card']}, stop:1 {p['hero_end']});
    border: 1px solid {p['border']}; border-radius: 15px;
}}
QFrame#vibrationHero {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p['hero_start']}, stop:0.52 {p['bg_card']}, stop:1 {p['hero_end']});
    border: 1px solid #6654e6; border-radius: 15px;
}}
QFrame#motorBalanceCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['bg_card']}, stop:1 {p['hero_end']});
    border: 1px solid {p['border']}; border-radius: 14px;
}}
QFrame#buttonSideCard, QFrame#buttonProfileCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['bg_card']}, stop:1 {p['hero_end']});
    border: 1px solid {p['border']}; border-radius: 14px;
}}
QFrame#buttonPreviewCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['hero_start']}, stop:0.56 {p['bg_card']}, stop:1 {p['hero_end']});
    border: 1px solid {p['border']}; border-radius: 15px;
}}
QFrame#profileCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['bg_card']}, stop:1 {p['hero_end']});
    border: 1px solid {p['border']}; border-radius: 13px;
}}
QFrame#profileCard:hover {{ border-color: {p['accent']}; background: {p['pressed']}; }}
QFrame#profileCard[selected="true"] {{
    border: 2px solid {p['accent_hover']}; background: {p['active_card']};
}}
QFrame#profileCard[active="true"] {{ border-color: {p['accent']}; }}
QFrame#profileCard[selected="true"][active="true"] {{ border: 2px solid {p['accent_hover']}; }}
QFrame#profileCard[dropTarget="true"] {{ border: 2px solid {p['accent_hover']}; }}
QFrame#profileCard[dragging="true"] {{ background: {p['pressed']}; border-color: {p['accent']}; }}
QFrame#profileDetailCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['hero_start']}, stop:1 {p['hero_end']});
    border: 1px solid {p['border']}; border-radius: 14px;
}}
QLabel#profileGlyph {{
    color: {p['accent_hover']}; background: {p['pressed']}; border: 1px solid {p['border']};
    border-radius: 13px; font-size: 25px; font-weight: 800;
}}
QFrame#audioToggleCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p['selected_start']}, stop:0.42 {p['bg_card']}, stop:1 {p['hero_end']});
    border: 1px solid {p['border']}; border-radius: 14px;
}}
QFrame#audioInfoCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['hero_start']}, stop:1 {p['hero_end']});
    border: 1px solid {p['border']}; border-radius: 14px;
}}
QFrame#appAudioRow {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['bg_card']}, stop:1 {p['hero_end']});
    border: 1px solid {p['border']}; border-radius: 12px;
}}
QFrame#appAudioRow:hover {{ border-color: {p['accent']}; background: {p['pressed']}; }}
QFrame#appAudioRow[selected="true"] {{
    border: 2px solid {p['accent_hover']}; background: {p['active_card']};
}}
QFrame#appAudioRow[active="true"] {{ border-color: {p['good']}; }}
QFrame#appAudioRow[selected="true"][active="true"] {{ border: 2px solid {p['accent_hover']}; }}
QFrame#appAudioRow[waiting="true"] {{ border-color: {p['warn']}; }}
QLabel#appAudioIcon, QLabel#audioInfoIcon {{
    color: {p['accent_hover']}; background: {p['pressed']}; border: 1px solid {p['border']};
    border-radius: 13px; font-size: 25px; font-weight: 800;
}}
QFrame#card, QFrame#metricCard, QFrame#motorCard, QFrame#sectionCard, QFrame#componentCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['bg_card']}, stop:1 {p['bg']});
    border: 1px solid {p['border']}; border-radius: 14px;
}}
QFrame#presetCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['bg_card']}, stop:1 {p['hero_end']});
    border: 1px solid {p['border']}; border-radius: 13px;
}}
QFrame#presetCard[active="true"] {{ border: 2px solid {p['accent']}; background: {p['active_card']}; }}
QFrame#featuredPreset {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p['hero_start']}, stop:0.55 {p['bg_card']}, stop:1 {p['hero_end']});
    border: 1px solid #6758dc; border-radius: 14px;
}}
QFrame#featuredPreset[active="true"] {{ border: 2px solid {p['accent_hover']}; }}
QFrame#triggerColumnHeader {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p['hero_start']}, stop:1 {p['hero_end']});
    border: 1px solid {p['border']}; border-radius: 13px;
}}
QFrame#triggerPresetCard, QFrame#triggerCustomCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['bg_card']}, stop:1 {p['hero_end']});
    border: 1px solid {p['border']}; border-radius: 13px;
}}
QFrame#triggerPresetCard[active="true"], QFrame#triggerCustomCard[active="true"] {{
    border: 2px solid {p['accent']}; background: {p['active_card']};
}}
QFrame#triggerPanel {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p['hero_start']}, stop:1 {p['hero_end']});
    border: 1px solid {p['border']}; border-radius: 11px;
}}
QFrame#cardActive {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['active_card']}, stop:1 {p['bg_card']});
    border: 1px solid {p['accent']}; border-radius: 14px;
}}
QListWidget {{
    background: {p['bg_card']}; border: 1px solid {p['border']}; border-radius: 12px;
    padding: 7px; outline: none;
}}
QListWidget::item {{ padding: 11px; border-radius: 8px; }}
QListWidget::item:selected {{ background: {p['pressed']}; color: {p['fg']}; }}
QLineEdit {{
    background: {p['bg_card']}; border: 1px solid {p['border']}; border-radius: 9px;
    padding: 10px 12px;
}}
QLineEdit:focus {{ border-color: {p['accent']}; }}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: {p['border']}; border-radius: 5px; min-height: 28px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""


class ThemeManager(QObject):
    """Owns the resolved palette and notifies listeners (`changed`) whenever
    it changes - either the user picked a different preference, or the
    preference is "system" and the desktop's own scheme changed."""

    changed = Signal()

    def __init__(self, preference="system"):
        super().__init__()
        self.preference = preference
        self.name = resolve(preference)
        self.palette = PALETTES[self.name]
        try:
            QGuiApplication.styleHints().colorSchemeChanged.connect(self._on_system_change)
        except Exception:
            pass

    def _on_system_change(self, *_args):
        if self.preference == "system":
            self._recompute()

    def set_preference(self, preference):
        if preference == self.preference:
            return
        self.preference = preference
        self._recompute()

    def _recompute(self):
        self.name = resolve(self.preference)
        self.palette = PALETTES[self.name]
        self.changed.emit()

    def stylesheet(self):
        return build_stylesheet(self.palette)


manager = ThemeManager()
