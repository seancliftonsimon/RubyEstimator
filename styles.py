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
    
    # Button Colors (Complementary Blue)
    BUTTON_PRIMARY = "#3b82f6"  # Lighter blue
    BUTTON_DARK = "#2563eb"
    BUTTON_HOVER = "#60a5fa"
    BUTTON_SHADOW = "rgba(59, 130, 246, 0.3)"
    
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
    
    # Gradient Definitions - Simplified for professional look
    RUBY_GRADIENT = "linear-gradient(180deg, #990C41 0%, #7a0a34 100%)"
    RUBY_GRADIENT_HOVER = "linear-gradient(180deg, #7a0a34 0%, #990C41 100%)"


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
    """Generate CSS for data tables with clean headers (no gradient)."""
    return f"""
    /* Both st.dataframe and st.table styling */
    .stDataFrame table,
    table {{
        border-collapse: collapse !important;
        width: 100% !important;
        margin: 1rem 0 !important;
        background: {Colors.WHITE} !important;
        border-radius: {BorderRadius.LG} !important;
        overflow: hidden !important;
        box-shadow: {Shadows.MD} !important;
    }}
    
    /* Table headers - clean gray background, no gradient */
    .stDataFrame th,
    table th {{
        background: {Colors.GRAY_100} !important;
        color: {Colors.GRAY_800} !important;
        padding: 1rem !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        text-align: center !important;
        border: none !important;
    }}
    
    .stDataFrame th *,
    table th * {{
        color: {Colors.GRAY_800} !important;
        text-align: center !important;
    }}
    
    .stDataFrame thead tr th,
    table thead tr th {{
        text-align: center !important;
    }}
    
    .stDataFrame td,
    table td {{
        padding: 0.875rem 1rem !important;
        border-bottom: 1px solid {Colors.GRAY_200} !important;
        vertical-align: middle !important;
        border-left: none !important;
        border-right: none !important;
        font-size: 1rem !important;
    }}
    
    .stDataFrame tr:nth-child(even),
    table tbody tr:nth-child(even) {{
        background: {Colors.GRAY_50} !important;
    }}
    
    .stDataFrame tr:hover,
    table tbody tr:hover {{
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
        background: {Colors.GRAY_50} !important;
        border: 3px solid {Colors.RUBY_BORDER_STRONG} !important;
        border-radius: {BorderRadius.LG} !important;
        padding: 0.75rem !important;
        font-size: 1rem !important;
        color: {Colors.GRAY_800} !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.06) !important;
    }}
    
    .stTextInput input:focus,
    [data-testid="stTextInput"] input:focus,
    input[type="text"]:focus {{
        background: {Colors.WHITE} !important;
        border-color: {Colors.RUBY_PRIMARY} !important;
        box-shadow: 0 0 0 4px {Colors.RUBY_LIGHT}, inset 0 2px 4px rgba(0, 0, 0, 0.06) !important;
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
    /* ========== GOOGLE FONTS IMPORT ========== */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap');
    
    /* ========== PROFESSIONAL FONT FAMILY ========== */
    body, p, h1, h2, h3, h4, h5, h6, span, div, label, input, button, textarea, select {{
        font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
    }}
    
    /* Exclude icon fonts from font override */
    .material-icons, [class*="icon"], svg, svg * {{
        font-family: inherit !important;
    }}
    
    /* ========== FORCE LIGHT MODE WITH PROFESSIONAL BACKGROUND ========== */
    .stApp {{
        background-color: #f8fafc !important; /* Slate 50 */
        color: {Colors.GRAY_800} !important;
    }}
    
    [data-testid="stAppViewContainer"] {{
        background-color: #f8fafc !important;
    }}
    
    [data-testid="stHeader"] {{
        background: {Colors.WHITE} !important;
        border-bottom: 3px solid {Colors.RUBY_PRIMARY} !important;
        padding: 0 !important;
        min-height: 0 !important;
        height: 0 !important;
        display: none !important;
    }}
    
    /* Hide Streamlit header elements to reduce top spacing */
    [data-testid="stHeader"] > div:first-child {{
        padding: 0 !important;
        margin: 0 !important;
    }}
    
    /* Minimize top padding on main content area */
    [data-testid="stAppViewContainer"] > div:first-child {{
        padding-top: 0 !important;
    }}
    
    .main .block-container {{
        padding-top: 0 !important;
        padding-bottom: 0.5rem !important;
        max-width: 95% !important;
        margin-top: -9rem !important; /* Further reduce top spacing */
    }}
    
    /* Hide the sidebar collapsed control to "get rid of the side on the left entirely" */
    [data-testid="stSidebarCollapsedControl"] {{
        display: none !important;
    }}
    
    .main {{
        background: transparent !important;
        color: {Colors.GRAY_800} !important;
    }}
    
    /* Force all text elements to be dark - but NOT in buttons, tables, or special headers */
    p:not(button p):not(.stButton p), 
    span:not(button span):not(.stButton span), 
    div:not(button div):not(.stButton div):not(.section-header):not(.section-header *), 
    label, h1, h2, h3, h4, h5, h6 {{
        color: {Colors.GRAY_800} !important;
    }}
    
    /* Exception: main title uses ruby color */
    .main-title {{
        color: {Colors.RUBY_PRIMARY} !important;
    }}
    
    .main-title * {{
        color: {Colors.RUBY_PRIMARY} !important;
    }}
    
    /* Exception: section headers use white text on red background */
    .section-header {{
        color: {Colors.WHITE} !important;
    }}
    
    .section-header * {{
        color: {Colors.WHITE} !important;
    }}
    
    /* Force input backgrounds to be white */
    input, textarea, select {{
        background: {Colors.WHITE} !important;
        color: {Colors.GRAY_800} !important;
    }}
    
    /* ========== TYPOGRAPHY ========== */
    .main-title {{
        font-family: 'Montserrat', 'Segoe UI', sans-serif !important;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.25rem;
        margin-top: 0.15rem;
        color: {Colors.RUBY_PRIMARY} !important;
        text-shadow: 0 4px 8px {Colors.RUBY_SHADOW_STRONG};
        letter-spacing: 0.05em;
        position: relative;
    }}
    
    .subtitle {{
        font-family: 'Montserrat', 'Segoe UI', sans-serif !important;
        font-size: 1.1rem;
        font-weight: 500;
        font-style: italic;
        text-align: center;
        margin-bottom: 1.5rem;
        margin-top: 0.75rem;
        padding: 0.75rem 0;
        color: {Colors.GRAY_600} !important;
    }}
    
    .main-title * {{
        font-family: 'Montserrat', 'Segoe UI', sans-serif !important;
        color: {Colors.RUBY_PRIMARY} !important;
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
        font-family: 'Montserrat', 'Segoe UI', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: {Colors.WHITE} !important;
        background-color: {Colors.RUBY_PRIMARY} !important;
        background: {Colors.RUBY_PRIMARY} !important;
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
        padding: 0.75rem 1rem !important;
        border-radius: {BorderRadius.MD} !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
        border: none !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    .section-header,
    .section-header * {{
        font-family: 'Montserrat', 'Segoe UI', sans-serif !important;
        color: {Colors.WHITE} !important;
        text-shadow: none !important;
    }}
    
    div.section-header {{
        color: {Colors.WHITE} !important;
    }}
    
    .subsection-header {{
        font-family: 'Montserrat', 'Segoe UI', sans-serif !important;
        font-size: 1.2rem;
        font-weight: 600;
        color: {Colors.RUBY_PRIMARY};
        margin-bottom: 0.5rem;
        margin-top: 0.5rem;
        padding: 0.5rem 0.75rem;
        border-left: 4px solid {Colors.RUBY_PRIMARY};
        background: {Colors.RUBY_LIGHT};
        border-radius: 0 {BorderRadius.MD} {BorderRadius.MD} 0;
    }}
    
    /* ========== CARDS & CONTAINERS ========== */
    .main-section-card {{
        background: {Colors.WHITE};
        border-radius: {BorderRadius.LG};
        border: 1px solid {Colors.GRAY_200};
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: all 0.2s ease;
    }}
    
    .main-section-card:hover {{
        border-color: {Colors.RUBY_BORDER_MEDIUM};
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
        transform: translateY(-1px);
    }}
    
    /* ========== BUTTONS - TARGETED FOR APP CONTENT ONLY ========== */
    /* Only target buttons within the main content area, not Streamlit's UI chrome */
    /* Professional blue button */
    .stButton button,
    .stButton > button,
    button[kind="primary"],
    button[kind="secondary"],
    .stFormSubmitButton button,
    .stFormSubmitButton > button {{
        background: #2563eb !important; /* Blue 600 */
        color: {Colors.WHITE} !important;
        border: none !important;
        outline: none !important;
        border-radius: {BorderRadius.MD} !important;
        padding: 0.625rem 1.25rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        letter-spacing: 0.3px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06) !important;
        text-shadow: none !important;
        cursor: pointer !important;
        text-transform: none !important; /* Removed uppercase */
        min-height: 42px !important;
    }}
    
    .stButton button:hover,
    .stButton > button:hover,
    .stFormSubmitButton button:hover {{
        background: #1d4ed8 !important; /* Blue 700 */
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        color: {Colors.WHITE} !important;
    }}
    
    .stButton button:focus,
    .stButton > button:focus,
    .stFormSubmitButton button:focus {{
        outline: none !important;
        border: none !important;
        box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.3) !important;
    }}
    
    /* Ensure all button text and children are white */
    .stButton button *,
    .stButton > button *,
    .stFormSubmitButton button *,
    .stButton button span,
    .stButton button p,
    .stButton button div {{
        color: {Colors.WHITE} !important;
        background: transparent !important;
        font-weight: 700 !important;
    }}
    
    /* Admin button styling - teal background (ONLY teal element) - positioned bottom left */
    button[key="admin_toggle_btn"],
    .stButton button[key="admin_toggle_btn"] {{
        background: {Colors.ADMIN_BUTTON} !important;
        background-color: {Colors.ADMIN_BUTTON} !important;
        border-color: {Colors.ADMIN_BUTTON} !important;
        color: {Colors.WHITE} !important;
        position: fixed !important;
        bottom: 1rem !important;
        left: 1rem !important;
        z-index: 999 !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 1rem !important;
        min-height: auto !important;
    }}
    
    button[key="admin_toggle_btn"]:hover,
    .stButton button[key="admin_toggle_btn"]:hover {{
        background: {Colors.ADMIN_BUTTON_HOVER} !important;
        background-color: {Colors.ADMIN_BUTTON_HOVER} !important;
        border-color: {Colors.ADMIN_BUTTON_HOVER} !important;
        color: {Colors.WHITE} !important;
    }}
    
    button[key="admin_toggle_btn"] *,
    .stButton button[key="admin_toggle_btn"] * {{
        color: {Colors.WHITE} !important;
    }}
    
    .stButton > button:active,
    .stFormSubmitButton button:active {{
        background: {Colors.BUTTON_DARK} !important;
        border-color: {Colors.BUTTON_DARK} !important;
        transform: translateY(0) !important;
    }}
    
    /* ========== INPUT FIELDS ========== */
    /* Input field labels - make them bigger */
    .stTextInput > label,
    [data-testid="stTextInput"] > label,
    label[data-testid="stWidgetLabel"] {{
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: {Colors.GRAY_800} !important;
        margin-bottom: 0.5rem !important;
    }}
    
    {generate_input_css()}
    
    /* ========== SELECTBOX (DROPDOWN) STYLING ========== */
    /* Hide dropdown arrows (SVG icons) */
    .stSelectbox [data-baseweb="select"] svg,
    [data-testid="stSelectbox"] [data-baseweb="select"] svg,
    .stSelectbox [data-baseweb="select"] > div > svg,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div > svg {{
        display: none !important;
    }}
    
    /* Hide any Material-Icons \"keyboard\" text that can leak through as plain text inside selectboxes */
    [data-testid="stSelectbox"] span[class*="keyboard"],
    [data-testid="stSelectbox"] span[aria-label*="keyboard"],
    [data-testid="stSelectbox"] [class*="material-icons"],
    [data-testid="stSelectbox"] [aria-label*="keyboard_arrow"] {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }}
    
    /* Make the select control look like a clickable input */
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {{
        border: 3px solid {Colors.RUBY_BORDER_STRONG} !important;
        background: {Colors.WHITE} !important;
        border-radius: {BorderRadius.LG} !important;
        padding: 0.4rem 0.75rem !important;
        cursor: pointer !important;
        color: {Colors.GRAY_800} !important;
    }}
    
    [data-testid="stSelectbox"] [data-baseweb="select"] > div:hover {{
        border-color: {Colors.RUBY_PRIMARY} !important;
    }}
    
    /* Ensure all text inside the select control is readable (no white-on-white) */
    [data-testid="stSelectbox"] [data-baseweb="select"] * {{
        color: {Colors.GRAY_800} !important;
        background-color: transparent !important;
    }}
    
    /* Reduce spacing between text input and selectbox */
    .stSelectbox,
    [data-testid="stSelectbox"] {{
        margin-top: -0.5rem !important;
        padding-top: 0 !important;
    }}
    
    /* Reduce bottom margin of text input to minimize spacing before dropdown */
    .stTextInput,
    [data-testid="stTextInput"] {{
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }}
    
    /* Target the container div that wraps text input to reduce spacing */
    .stTextInput > div,
    [data-testid="stTextInput"] > div {{
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }}
    
    /* Target the container div that wraps selectbox to reduce spacing */
    .stSelectbox > div,
    [data-testid="stSelectbox"] > div {{
        margin-top: 0 !important;
        padding-top: 0 !important;
    }}
    
    /* Hide help text (e.g., "press enter to submit") below text inputs */
    .stTextInput > div > small,
    [data-testid="stTextInput"] > div > small,
    .stTextInput small,
    [data-testid="stTextInput"] small {{
        display: none !important;
    }}
    
    /* Reduce spacing for selectbox labels (hidden labels still take space) */
    .stSelectbox > label,
    [data-testid="stSelectbox"] > label {{
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
        height: 0 !important;
        min-height: 0 !important;
        display: none !important;
    }}
    
    /* Fix text selection highlight - override white background */
    ::selection {{
        background: rgba(153, 12, 65, 0.2) !important;
        color: {Colors.GRAY_800} !important;
    }}
    
    ::-moz-selection {{
        background: rgba(153, 12, 65, 0.2) !important;
        color: {Colors.GRAY_800} !important;
    }}
    
    /* Apply selection styles to input and selectbox elements */
    input::selection,
    select::selection,
    textarea::selection,
    [data-baseweb="select"] input::selection {{
        background: rgba(153, 12, 65, 0.2) !important;
        color: {Colors.GRAY_800} !important;
    }}
    
    input::-moz-selection,
    select::-moz-selection,
    textarea::-moz-selection,
    [data-baseweb="select"] input::-moz-selection {{
        background: rgba(153, 12, 65, 0.2) !important;
        color: {Colors.GRAY_800} !important;
    }}
    
    /* Global safety: hide any remaining keyboard-arrow Material icon artifacts */
    *[aria-label*="keyboard_arrow"] {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }}
    
    /* ========== TABLES ========== */
    {generate_table_css()}
    
    /* ========== CONFIDENCE BADGES ========== */
    {generate_confidence_badge_css()}
    
    /* ========== FORMS ========== */
    .stForm {{
        background: {Colors.WHITE};
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: {BorderRadius.LG};
        border: 3px solid {Colors.RUBY_BORDER_STRONG};
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12), 0 4px 8px rgba(0, 0, 0, 0.08) !important;
        transition: all 0.3s ease;
    }}
    
    .stForm:hover {{
        border-color: {Colors.RUBY_PRIMARY};
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15), 0 6px 12px rgba(153, 12, 65, 0.2) !important;
    }}
    
    /* ========== MESSAGES ========== */
    .success-message {{
        background: linear-gradient(135deg, {Colors.SUCCESS_LIGHT} 0%, rgba(22, 163, 74, 0.15) 100%);
        padding: 1rem 1.5rem;
        border-radius: {BorderRadius.LG};
        border: 2px solid {Colors.SUCCESS_BORDER};
        border-left: 6px solid {Colors.SUCCESS_BORDER};
        margin: 1rem 0;
        color: {Colors.SUCCESS};
        font-weight: 500;
        box-shadow: {Shadows.SM};
    }}
    
    .warning-message {{
        background: linear-gradient(135deg, {Colors.WARNING_LIGHT} 0%, rgba(217, 119, 6, 0.15) 100%);
        padding: 1rem 1.5rem;
        border-radius: {BorderRadius.LG};
        border: 2px solid {Colors.WARNING_BORDER};
        border-left: 6px solid {Colors.WARNING_BORDER};
        margin: 1rem 0;
        color: {Colors.WARNING};
        font-weight: 500;
        box-shadow: {Shadows.SM};
    }}
    
    .error-message {{
        background: linear-gradient(135deg, {Colors.ERROR_LIGHT} 0%, rgba(220, 38, 38, 0.15) 100%);
        padding: 1rem 1.5rem;
        border-radius: {BorderRadius.LG};
        border: 2px solid {Colors.ERROR_BORDER};
        border-left: 6px solid {Colors.ERROR_BORDER};
        margin: 1rem 0;
        color: {Colors.ERROR};
        font-weight: 500;
        box-shadow: {Shadows.SM};
    }}
    
    /* ========== EXPANDERS ========== */
    [data-testid="stExpander"] {{
        position: relative !important;
        z-index: 1 !important;
        margin-top: 1rem !important;
        margin-bottom: 1rem !important;
    }}
    
    .streamlit-expanderHeader {{
        background: linear-gradient(135deg, {Colors.RUBY_LIGHT} 0%, {Colors.GRAY_50} 100%) !important;
        border: 2px solid {Colors.RUBY_BORDER_MEDIUM} !important;
        border-radius: {BorderRadius.LG} !important;
        padding: 1rem !important;
        font-weight: 600 !important;
        color: {Colors.RUBY_PRIMARY} !important;
        transition: all 0.3s ease !important;
        position: relative !important;
        z-index: 2 !important;
    }}
    
    .streamlit-expanderHeader:hover {{
        background: linear-gradient(135deg, {Colors.RUBY_BORDER} 0%, {Colors.RUBY_LIGHT} 100%) !important;
        border-color: {Colors.RUBY_BORDER_STRONG} !important;
        box-shadow: {Shadows.SM} !important;
    }}
    
    /* Fix expander icon rendering */
    [data-testid="stExpander"] details summary {{
        list-style-type: none !important;
    }}
    
    [data-testid="stExpander"] details summary::-webkit-details-marker {{
        display: none !important;
    }}
    
    [data-testid="stExpander"] svg {{
        display: inline-block !important;
        width: 1.5rem !important;
        height: 1.5rem !important;
        vertical-align: middle !important;
        fill: {Colors.RUBY_PRIMARY} !important;
    }}
    
    .streamlit-expanderHeader svg {{
        display: inline-block !important;
        width: 1.5rem !important;
        height: 1.5rem !important;
        vertical-align: middle !important;
        fill: {Colors.RUBY_PRIMARY} !important;
    }}
    
    /* Hide Material Icons font rendering but keep expander label visible */
    [data-testid="stExpander"] *[style*="Material Icons"],
    [data-testid="stExpander"] *[style*="Material-Icons"],
    [data-testid="stExpander"] *[class*="material"]:not([data-testid]),
    .streamlit-expanderHeader .material-icons {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }}
    
    /* Only hide keyboard shortcut spans (not the label text) - including on hover */
    [data-testid="stExpander"] details summary span[class*="keyboard"],
    [data-testid="stExpander"] details summary span[aria-label*="keyboard"],
    [data-testid="stExpander"] details summary:hover span[class*="keyboard"],
    [data-testid="stExpander"] details summary:hover span[aria-label*="keyboard"],
    [data-testid="stExpander"] details summary *[class*="keyboard"],
    [data-testid="stExpander"] details summary *[aria-label*="keyboard"],
    [data-testid="stExpander"] details summary *[data-testid*="keyboard"],
    [data-testid="stExpander"] details summary:hover *[class*="keyboard"],
    [data-testid="stExpander"] details summary:hover *[aria-label*="keyboard"],
    [data-testid="stExpander"] details summary:hover *[data-testid*="keyboard"] {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
        font-size: 0 !important;
        line-height: 0 !important;
    }}
    
    /* Hide pseudo-elements on keyboard-related elements only */
    [data-testid="stExpander"] details summary *[class*="keyboard"]::after,
    [data-testid="stExpander"] details summary *[class*="keyboard"]::before,
    [data-testid="stExpander"] details summary *[aria-label*="keyboard"]::after,
    [data-testid="stExpander"] details summary *[aria-label*="keyboard"]::before {{
        content: none !important;
    }}
    
    /* Disable tooltips on hover but keep text visible */
    [data-testid="stExpander"] details summary[title]:hover::after,
    [data-testid="stExpander"] details summary[title]:hover::before,
    [data-testid="stExpander"] details summary *[title]:hover::after,
    [data-testid="stExpander"] details summary *[title]:hover::before,
    [data-testid="stExpander"] [title]:hover::after {{
        display: none !important;
        content: none !important;
        visibility: hidden !important;
    }}
    
    /* Remove title tooltips completely */
    [data-testid="stExpander"] details summary[title],
    [data-testid="stExpander"] details summary *[title] {{
        pointer-events: auto !important;
    }}
    
    /* Hide Material Icons keyboard arrow on hover */
    [data-testid="stExpander"] details summary:hover .material-icons,
    [data-testid="stExpander"] details summary:hover *[class*="material-icons"] {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }}
    
    /* Ensure expander label text is visible */
    [data-testid="stExpander"] details summary {{
        color: {Colors.RUBY_PRIMARY} !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }}
    
    .streamlit-expanderHeader {{
        overflow: visible !important;
    }}
    
    .streamlit-expanderContent {{
        background: {Colors.WHITE} !important;
        border: 2px solid {Colors.RUBY_BORDER_MEDIUM} !important;
        border-top: none !important;
        border-radius: 0 0 {BorderRadius.LG} {BorderRadius.LG} !important;
        padding: 1rem !important;
        position: relative !important;
        z-index: 2 !important;
        max-height: 400px !important;
        overflow-y: auto !important;
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
    /* ========== FORCE LIGHT MODE FOR ADMIN ========== */
    .stApp {{
        background: {Colors.ADMIN_BG} !important;
    }}
    
    [data-testid="stAppViewContainer"] {{
        background: {Colors.ADMIN_BG} !important;
    }}
    
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
        font-family: 'Montserrat', 'Segoe UI', sans-serif !important;
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
    if value < 0:
        # For negative values, place the negative sign before the dollar sign
        if show_cents:
            return f"-${abs(value):,.2f}"
        return f"-${abs(value):,.0f}"
    else:
        # For positive values, normal formatting
        if show_cents:
            return f"${value:,.2f}"
        return f"${value:,.0f}"


def format_weight(value: float) -> str:
    """Format weight value."""
    return f"{value:,.1f} lbs"


def format_percentage(value: float) -> str:
    """Format as percentage."""
    return f"{value:.0%}"

