"""
Stellar AI FlightDeck - Modern NASA-Inspired Glassmorphism Design System.
Defines color constants, typography scales, and unified Qt Style Sheets (QSS).
"""

# -----------------------------------------------------------------------------
# Color Palette Constants
# -----------------------------------------------------------------------------
BG_VOID = "#07090E"               # Deep celestial space void
BG_SURFACE = "#0C101A"            # Secondary canvas
BG_SURFACE_ELEVATED = "#131826"   # Slightly elevated panel background
BG_CARD = BG_SURFACE_ELEVATED     # Card background alias

# Translucent Glass Card Backgrounds
GLASS_BG = "rgba(15, 23, 42, 0.70)"
GLASS_BG_HOVER = "rgba(24, 35, 60, 0.85)"
GLASS_BG_ACTIVE = "rgba(30, 44, 76, 0.90)"

# Glass Borders
GLASS_BORDER = "rgba(255, 255, 255, 0.08)"
GLASS_BORDER_HOVER = "rgba(255, 255, 255, 0.18)"
GLASS_BORDER_ACTIVE = "rgba(255, 255, 255, 0.28)"

# Accents & Semantics
ACCENT_AMBER = "#F59E0B"          # Primary Action CTA / Gold Accent
ACCENT_AMBER_HOVER = "#D97706"
ACCENT_AMBER_GLOW = "rgba(245, 158, 11, 0.25)"

ACCENT_CYAN = "#38BDF8"           # Precision AI Accent
ACCENT_CYAN_GLOW = "rgba(56, 189, 248, 0.20)"

ACCENT_PURPLE = "#8B5CF6"         # Secondary Orbital Accent
ACCENT_PURPLE_GLOW = "rgba(139, 92, 246, 0.20)"

STATUS_SUCCESS = "#10B981"        # Step Validated / Mission Success
STATUS_SUCCESS_GLOW = "rgba(16, 185, 129, 0.25)"

STATUS_WARNING = "#F97316"        # Wrong-Order Deviation Alert
STATUS_WARNING_GLOW = "rgba(249, 115, 22, 0.25)"

STATUS_CRITICAL = "#EF4444"       # Skipped Step / Error
STATUS_CRITICAL_GLOW = "rgba(239, 68, 68, 0.25)"
STATUS_ERROR = STATUS_CRITICAL       # Alias for Error state
STATUS_ERROR_GLOW = STATUS_CRITICAL_GLOW

# Typography Colors
TEXT_PRIMARY = "#F8FAFC"          # Polar White
TEXT_SECONDARY = "#94A3B8"        # Starlight Gray
TEXT_MUTED = "#64748B"            # Cosmic Slate
TEXT_DARK = "#07090E"             # Dark text for amber CTA buttons


# -----------------------------------------------------------------------------
# Global Application Qt Style Sheet (QSS)
# -----------------------------------------------------------------------------
GLOBAL_QSS = f"""
/* Base Window & Surface */
QMainWindow, QWidget#centralWidget {{
    background-color: {BG_VOID};
    color: {TEXT_PRIMARY};
    font-family: "Plus Jakarta Sans", "Inter", "Segoe UI", -apple-system, sans-serif;
    font-size: 14px;
}}

/* Tooltips */
QToolTip {{
    background-color: #1E293B;
    color: {TEXT_PRIMARY};
    border: 1px solid {GLASS_BORDER_HOVER};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* Glass Containers & Cards */
QFrame.glassCard, QWidget.glassCard {{
    background-color: {GLASS_BG};
    border: 1px solid {GLASS_BORDER};
    border-radius: 16px;
}}

QFrame.glassCardHover:hover {{
    background-color: {GLASS_BG_HOVER};
    border: 1px solid {GLASS_BORDER_HOVER};
}}

QFrame.glassCardElevated {{
    background-color: {BG_SURFACE_ELEVATED};
    border: 1px solid {GLASS_BORDER_ACTIVE};
    border-radius: 16px;
}}

/* Primary CTA Buttons (Warm Amber with Glow) */
QPushButton.primaryBtn {{
    background-color: {ACCENT_AMBER};
    color: {TEXT_DARK};
    font-weight: 700;
    font-size: 14px;
    border: none;
    border-radius: 10px;
    padding: 10px 22px;
}}

QPushButton.primaryBtn:hover {{
    background-color: {ACCENT_AMBER_HOVER};
}}

QPushButton.primaryBtn:pressed {{
    background-color: #B45309;
}}

/* Secondary Glass Buttons */
QPushButton.glassBtn {{
    background-color: rgba(255, 255, 255, 0.05);
    color: {TEXT_PRIMARY};
    font-weight: 600;
    font-size: 13px;
    border: 1px solid {GLASS_BORDER};
    border-radius: 10px;
    padding: 8px 18px;
}}

QPushButton.glassBtn:hover {{
    background-color: rgba(255, 255, 255, 0.10);
    border: 1px solid {GLASS_BORDER_HOVER};
    color: #FFFFFF;
}}

QPushButton.glassBtn:pressed {{
    background-color: rgba(255, 255, 255, 0.03);
}}

/* Danger Button */
QPushButton.dangerBtn {{
    background-color: rgba(239, 68, 68, 0.15);
    color: {STATUS_CRITICAL};
    font-weight: 600;
    font-size: 13px;
    border: 1px solid rgba(239, 68, 68, 0.30);
    border-radius: 10px;
    padding: 8px 18px;
}}

QPushButton.dangerBtn:hover {{
    background-color: rgba(239, 68, 68, 0.25);
    border: 1px solid {STATUS_CRITICAL};
}}

/* Success Button */
QPushButton.successBtn {{
    background-color: rgba(16, 185, 129, 0.15);
    color: {STATUS_SUCCESS};
    font-weight: 600;
    font-size: 13px;
    border: 1px solid rgba(16, 185, 129, 0.30);
    border-radius: 10px;
    padding: 8px 18px;
}}

QPushButton.successBtn:hover {{
    background-color: rgba(16, 185, 129, 0.25);
    border: 1px solid {STATUS_SUCCESS};
}}

/* Navigation Sidebar Buttons */
QPushButton.navBtn {{
    background-color: transparent;
    color: {TEXT_SECONDARY};
    font-weight: 600;
    font-size: 14px;
    text-align: left;
    border: none;
    border-radius: 10px;
    padding: 12px 16px;
}}

QPushButton.navBtn:hover {{
    background-color: rgba(255, 255, 255, 0.05);
    color: {TEXT_PRIMARY};
}}

QPushButton.navBtn:checked, QPushButton.navBtn.active {{
    background-color: rgba(245, 158, 11, 0.12);
    color: {ACCENT_AMBER};
    border-left: 3px solid {ACCENT_AMBER};
}}

/* Form Controls & Inputs */
QComboBox, QSpinBox, QLineEdit {{
    background-color: rgba(15, 23, 42, 0.85);
    color: {TEXT_PRIMARY};
    border: 1px solid {GLASS_BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}}

QComboBox:hover, QLineEdit:hover {{
    border: 1px solid {GLASS_BORDER_HOVER};
}}

QComboBox:focus, QLineEdit:focus {{
    border: 1px solid {ACCENT_AMBER};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: #0F172A;
    color: {TEXT_PRIMARY};
    border: 1px solid {GLASS_BORDER_ACTIVE};
    border-radius: 8px;
    selection-background-color: rgba(245, 158, 11, 0.20);
    selection-color: {ACCENT_AMBER};
    padding: 4px;
}}

/* Ultra-Slim Dark Scrollbars */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: rgba(255, 255, 255, 0.15);
    min-height: 24px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical:hover {{
    background: rgba(255, 255, 255, 0.30);
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
    height: 0px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background: rgba(255, 255, 255, 0.15);
    min-width: 24px;
    border-radius: 3px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    background: none;
    width: 0px;
}}
"""
