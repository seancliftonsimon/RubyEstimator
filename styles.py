"""
Centralized styling system for Ruby GEM application.
Provides color constants, theme definitions, and CSS generation functions.
"""

from typing import Dict, Optional


# ============================================================================
# COLOR SYSTEM
# ============================================================================

class Colors:
    """Centralized color constants for Ruby GEM application."""
    
    # Primary Brand Colors (Ruby)
    RUBY_PRIMARY = "#990C41"
    RUBY_DARK = "#7a0a34"
    RUBY_HOVER = "#c00e4f"
    RUBY_LIGHT = "rgba(153, 12, 65, 0.1)"
    RUBY_BORDER = "rgba(153, 12, 65, 0.18)"
    RUBY_BORDER_MEDIUM = "rgba(153, 12, 65, 0.2)"
    RUBY_BORDER_STRONG = "rgba(153, 12, 65, 0.35)"
    RUBY_SHADOW = "rgba(153, 12, 65, 0.08)"
    RUBY_SHADOW_MEDIUM = "rgba(153, 12, 65, 0.15)"
    RUBY_SHADOW_STRONG = "rgba(153, 12, 65, 0.25)"
    
    # Semantic Colors
    SUCCESS = "#16a34a"  # Green for profit, positive values
    SUCCESS_LIGHT = "rgba(22, 163, 74, 0.1)"
    SUCCESS_BORDER = "#16a34a"
    
    ERROR = "#dc2626"  # Red for costs, negative values, errors
    ERROR_LIGHT = "rgba(220, 38, 38, 0.08)"
    ERROR_BORDER = "#dc2626"
    
    WARNING = "#d97706"  # Amber for medium confidence, caution
    WARNING_LIGHT = "rgba(217, 119, 6, 0.1)"
    WARNING_BORDER = "#d97706"
    
    INFO = "#64748b"  # Blue-gray for informational content
    INFO_LIGHT = "rgba(100, 116, 139, 0.1)"
    INFO_BORDER = "#64748b"
    
    # Neutral Colors
    WHITE = "#ffffff"
    GRAY_50 = "#f8fafc"
    GRAY_100 = "#f1f5f9"
    GRAY_200 = "#e2e8f0"
    GRAY_300 = "#cbd5e1"
    GRAY_400 = "#94a3b8"
    GRAY_500 = "#64748b"
    GRAY_600 = "#475569"
    GRAY_700 = "#334155"
    GRAY_800 = "#1e293b"
    GRAY_900 = "#0f172a"
    
    # Mode-Specific Colors
    ADMIN_BG = "#f1f5f9"  # Slate background for admin mode
    ADMIN_BUTTON = "#14b8a6"  # Teal for admin button (only teal usage)
    ADMIN_BUTTON_HOVER = "#0d9488"
    
    # Gradient Definitions
    RUBY_GRADIENT = "linear-gradient(135deg, #990C41 0%, #c00e4f 100%)"
    RUBY_GRADIENT_HOVER = "linear-gradient(135deg, #7a0a34 0%, #990C41 100%)"


class Spacing:
    """Spacing constants for consistent layout."""
    XS = "0.25rem"
    SM = "0.5rem"
    MD = "0.75rem"
    LG = "1rem"
    XL = "1.5rem"
    XXL = "2rem"


class BorderRadius:
    """Border radius constants."""
    SM = "4px"
    MD = "6px"
    LG = "8px"
    XL = "12px"


class Shadows:
    """Shadow definitions for depth."""
    SM = f"0 2px 4px {Colors.RUBY_SHADOW}"
    MD = f"0 4px 12px {Colors.RUBY_SHADOW}"
    LG = f"0 8px 24px {Colors.RUBY_SHADOW_MEDIUM}"
    HOVER = f"0 6px 20px {Colors.RUBY_SHADOW_STRONG}"


# ============================================================================
# CSS GENERATION FUNCTIONS
# ============================================================================

def generate_metric_box_css(
    background: str,
    border_color: str,
    text_color: str,
    border_left_width: str = "4px"
) -> str:
    """Generate CSS for metric display boxes."""
    return f"""
    background: {background};
    border: 1px solid {Colors.GRAY_200};
    border-left: {border_left_width} solid {border_color};
    border-radius: {BorderRadius.XL};
    padding: {Spacing.XL};
    box-shadow: {Shadows.MD};
    transition: all 0.2s ease;
    """


def generate_button_css(
    background: str,
    text_color: str = Colors.WHITE,
    hover_background: Optional[str] = None
) -> str:
    """Generate CSS for buttons."""
    hover_bg = hover_background or Colors.RUBY_DARK
    return f"""
    background: {background};
    color: {text_color};
    border: none;
    border-radius: {BorderRadius.LG};
    padding: {Spacing.MD} {Spacing.XXL};
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.3s ease;
    box-shadow: {Shadows.MD};
    cursor: pointer;
    """


def generate_table_css() -> str:
    """Generate CSS for data tables with ruby gradient headers."""
    return f"""
    .stDataFrame table {{
        border-collapse: collapse !important;
        width: 100% !important;
        margin: 1rem 0 !important;
        background: {Colors.WHITE} !important;
        border-radius: {BorderRadius.LG} !important;
        overflow: hidden !important;
        box-shadow: {Shadows.MD} !important;
    }}
    
    .stDataFrame th {{
        background: {Colors.RUBY_GRADIENT} !important;
        color: {Colors.WHITE} !important;
        padding: 1rem !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        text-align: left !important;
        border: none !important;
    }}
    
    .stDataFrame td {{
        padding: 0.875rem 1rem !important;
        border-bottom: 1px solid {Colors.GRAY_200} !important;
        vertical-align: middle !important;
        border-left: none !important;
        border-right: none !important;
        font-size: 1rem !important;
    }}
    
    .stDataFrame tr:nth-child(even) {{
        background: {Colors.GRAY_50} !important;
    }}
    
    .stDataFrame tr:hover {{
        background: {Colors.GRAY_100} !important;
        box-shadow: {Shadows.SM} !important;
    }}
    """


def generate_input_css() -> str:
    """Generate CSS for text input fields."""
    return f"""
    .stTextInput > div > div > input,
    [data-testid="stTextInput"] > div > div > input,
    input[type="text"] {{
        background: {Colors.WHITE} !important;
        border: 2px solid {Colors.RUBY_BORDER_MEDIUM} !important;
        border-radius: {BorderRadius.LG} !important;
        padding: {Spacing.MD} !important;
        font-size: 1rem !important;
        color: {Colors.GRAY_800} !important;
        transition: all 0.3s ease !important;
        box-shadow: {Shadows.SM} !important;
    }}
    
    .stTextInput input:focus,
    [data-testid="stTextInput"] input:focus,
    input[type="text"]:focus {{
        border-color: {Colors.RUBY_PRIMARY} !important;
        box-shadow: 0 0 0 3px {Colors.RUBY_LIGHT} !important;
        outline: none !important;
    }}
    """


def generate_confidence_badge_css() -> str:
    """Generate CSS for confidence badges (conditional display)."""
    return f"""
    .confidence-badge {{
        display: inline-block;
        padding: 0.375rem 0.75rem;
        border-radius: {BorderRadius.SM};
        font-size: 0.875rem;
        font-weight: 600;
        margin-left: 0.5rem;
        transition: all 0.2s ease;
    }}
    
    .confidence-badge:hover {{
        transform: translateY(-1px);
        box-shadow: {Shadows.SM};
    }}
    
    .confidence-medium {{
        background: {Colors.WARNING_LIGHT};
        border: 1px solid {Colors.WARNING_BORDER};
        color: {Colors.WARNING};
    }}
    
    .confidence-low {{
        background: {Colors.ERROR_LIGHT};
        border: 1px solid {Colors.ERROR_BORDER};
        color: {Colors.ERROR};
    }}
    """


def get_semantic_colors(value: float, value_type: str = "profit") -> Dict[str, str]:
    """
    Get semantic colors based on value type.
    
    Args:
        value: The numeric value to style
        value_type: Type of value - "profit", "cost", "info"
    
    Returns:
        Dictionary with background, border, and text colors
    """
    if value_type == "profit":
        if value >= 0:
            return {
                "background": Colors.SUCCESS_LIGHT,
                "border": Colors.SUCCESS_BORDER,
                "text": Colors.SUCCESS
            }
        else:
            return {
                "background": Colors.ERROR_LIGHT,
                "border": Colors.ERROR_BORDER,
                "text": Colors.ERROR
            }
    elif value_type == "cost":
        return {
            "background": Colors.ERROR_LIGHT,
            "border": Colors.ERROR_BORDER,
            "text": Colors.ERROR
        }
    else:  # info/neutral
        return {
            "background": Colors.GRAY_50,
            "border": Colors.GRAY_300,
            "text": Colors.GRAY_700
        }


def should_show_confidence_badge(confidence_score: float) -> bool:
    """Determine if confidence badge should be shown (only for medium/low)."""
    return confidence_score < 0.8


def get_confidence_badge_type(confidence_score: float) -> str:
    """Get badge type based on confidence score."""
    if confidence_score >= 0.8:
        return "high"  # Won't be shown
    elif confidence_score >= 0.6:
        return "medium"
    else:
        return "low"


# ============================================================================
# MAIN CSS GENERATOR
# ============================================================================

def generate_main_app_css() -> str:
    """Generate the complete CSS for the main application."""
    return f"""
<style>
    /* ========== GLOBAL STYLES ========== */
    .main {{
        background: {Colors.WHITE};
        color: {Colors.GRAY_800};
    }}
    
    /* ========== ADMIN BUTTON - Only Teal Element ========== */
    button[key="admin_toggle_btn"],
    button[data-testid*="admin"] {{
        background: {Colors.ADMIN_BUTTON} !important;
        border-color: {Colors.ADMIN_BUTTON} !important;
    }}
    
    button[key="admin_toggle_btn"]:hover,
    button[data-testid*="admin"]:hover {{
        background: {Colors.ADMIN_BUTTON_HOVER} !important;
        border-color: {Colors.ADMIN_BUTTON_HOVER} !important;
    }}
    
    /* ========== TYPOGRAPHY ========== */
    .main-title {{
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
        margin-top: 0.5rem;
        color: {Colors.RUBY_PRIMARY};
        text-shadow: 0 4px 8px {Colors.RUBY_SHADOW_STRONG};
        letter-spacing: 0.05em;
        position: relative;
    }}
    
    .main-title::after {{
        content: '';
        position: absolute;
        bottom: -8px;
        left: 50%;
        transform: translateX(-50%);
        width: 120px;
        height: 4px;
        background: {Colors.RUBY_GRADIENT};
        border-radius: 2px;
        box-shadow: 0 2px 8px {Colors.RUBY_SHADOW_STRONG};
    }}
    
    .section-header {{
        font-size: 1.5rem;
        font-weight: 600;
        color: {Colors.RUBY_PRIMARY};
        margin-bottom: 0.5rem;
        padding-bottom: 0.25rem;
        border-bottom: 2px solid {Colors.RUBY_PRIMARY};
        text-shadow: 0 1px 2px {Colors.RUBY_SHADOW};
    }}
    
    .subsection-header {{
        font-size: 1.2rem;
        font-weight: 500;
        color: {Colors.RUBY_HOVER};
        margin-bottom: 0.25rem;
        text-shadow: 0 1px 2px {Colors.RUBY_SHADOW};
    }}
    
    /* ========== CARDS & CONTAINERS ========== */
    .main-section-card {{
        background: {Colors.WHITE};
        backdrop-filter: blur(10px);
        border-radius: {BorderRadius.XL};
        border: 1px solid {Colors.RUBY_BORDER};
        box-shadow: {Shadows.MD};
        padding: 0.5rem;
        margin-bottom: 0.5rem;
    }}
    
    /* ========== BUTTONS ========== */
    .stButton > button {{
        background: {Colors.RUBY_GRADIENT} !important;
        color: {Colors.WHITE} !important;
        border: none !important;
        border-radius: {BorderRadius.LG} !important;
        padding: {Spacing.MD} {Spacing.XXL} !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: {Shadows.MD} !important;
    }}
    
    .stButton > button:hover {{
        background: {Colors.RUBY_GRADIENT_HOVER} !important;
        transform: translateY(-2px) !important;
        box-shadow: {Shadows.HOVER} !important;
    }}
    
    /* ========== INPUT FIELDS ========== */
    {generate_input_css()}
    
    /* ========== TABLES ========== */
    {generate_table_css()}
    
    /* ========== CONFIDENCE BADGES ========== */
    {generate_confidence_badge_css()}
    
    /* ========== FORMS ========== */
    .stForm {{
        background: {Colors.WHITE};
        backdrop-filter: blur(10px);
        padding: 0.5rem;
        border-radius: {BorderRadius.LG};
        border: 1px solid {Colors.RUBY_BORDER};
        box-shadow: {Shadows.MD};
    }}
    
    /* ========== MESSAGES ========== */
    .success-message {{
        background: {Colors.SUCCESS_LIGHT};
        padding: 1rem;
        border-radius: {BorderRadius.LG};
        border-left: 4px solid {Colors.SUCCESS_BORDER};
        margin: 1rem 0;
        color: {Colors.SUCCESS};
    }}
    
    .warning-message {{
        background: {Colors.WARNING_LIGHT};
        padding: 1rem;
        border-radius: {BorderRadius.LG};
        border-left: 4px solid {Colors.WARNING_BORDER};
        margin: 1rem 0;
        color: {Colors.WARNING};
    }}
    
    .error-message {{
        background: {Colors.ERROR_LIGHT};
        padding: 1rem;
        border-radius: {BorderRadius.LG};
        border-left: 4px solid {Colors.ERROR_BORDER};
        margin: 1rem 0;
        color: {Colors.ERROR};
    }}
    
    /* ========== EXPANDERS ========== */
    .streamlit-expanderHeader {{
        background: {Colors.GRAY_50} !important;
        border: 1px solid {Colors.GRAY_200} !important;
        border-radius: {BorderRadius.LG} !important;
        padding: 1rem !important;
        font-weight: 600 !important;
        color: {Colors.GRAY_700} !important;
    }}
    
    .streamlit-expanderContent {{
        background: {Colors.WHITE} !important;
        border: 1px solid {Colors.GRAY_200} !important;
        border-top: none !important;
        border-radius: 0 0 {BorderRadius.LG} {BorderRadius.LG} !important;
        padding: 1rem !important;
    }}
    
    /* ========== RESPONSIVE DESIGN ========== */
    @media (max-width: 768px) {{
        .main-title {{
            font-size: 2rem !important;
        }}
        
        .section-header {{
            font-size: 1.25rem !important;
        }}
        
        .stDataFrame table {{
            font-size: 0.875rem !important;
        }}
        
        .stDataFrame th,
        .stDataFrame td {{
            padding: 0.5rem !important;
        }}
    }}
</style>
"""


def generate_admin_mode_css() -> str:
    """Generate CSS specific to admin mode with distinct styling."""
    return f"""
<style>
    /* ========== ADMIN MODE SPECIFIC ========== */
    .admin-mode-container {{
        background: {Colors.ADMIN_BG};
        border-radius: {BorderRadius.XL};
        padding: {Spacing.XL};
        margin: {Spacing.LG} 0;
        border: 2px solid {Colors.GRAY_300};
        box-shadow: {Shadows.LG};
    }}
    
    .admin-mode-header {{
        background: {Colors.GRAY_700};
        color: {Colors.WHITE};
        padding: {Spacing.LG};
        border-radius: {BorderRadius.LG};
        margin-bottom: {Spacing.LG};
        font-size: 1.25rem;
        font-weight: 600;
        text-align: center;
        box-shadow: {Shadows.MD};
    }}
    
    /* Admin button - only teal element */
    button[data-testid*="admin"],
    .admin-button {{
        background: {Colors.ADMIN_BUTTON} !important;
        color: {Colors.WHITE} !important;
    }}
    
    button[data-testid*="admin"]:hover,
    .admin-button:hover {{
        background: {Colors.ADMIN_BUTTON_HOVER} !important;
    }}
    
    /* Admin number inputs - keep readable (no ruby background) */
    [data-testid="stNumberInput"] button {{
        display: none !important;
    }}
    
    [data-testid="stNumberInput"] input {{
        padding-right: 0.5rem !important;
        background: {Colors.WHITE} !important;
        border: 2px solid {Colors.GRAY_300} !important;
        color: {Colors.GRAY_800} !important;
    }}
</style>
"""


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_currency(value: float, show_cents: bool = True) -> str:
    """Format value as currency."""
    if show_cents:
        return f"${value:,.2f}"
    return f"${value:,.0f}"


def format_weight(value: float) -> str:
    """Format weight value."""
    return f"{value:,.1f} lbs"


def format_percentage(value: float) -> str:
    """Format as percentage."""
    return f"{value:.0%}"

