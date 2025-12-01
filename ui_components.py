"""UI Components and Icon Utilities for AI Pair Engineer."""

import streamlit as st
from typing import Optional


def load_font_awesome() -> None:
    """Load Font Awesome icon library and custom fonts."""
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"
          integrity="sha512-DTOQO9RWCH3ppGqcWaEA1BIZOC6xxalwEsw9c2QQeAIftl+Vegovlnee1c9QX4TctnWMn13TZye+giMm8e2LwA=="
          crossorigin="anonymous" referrerpolicy="no-referrer" />
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)


def icon(name: str, size: str = "1em", color: Optional[str] = None, class_name: str = "") -> str:
    """Generate Font Awesome icon HTML."""
    style = f"font-size: {size};"
    if color:
        style += f" color: {color};"
    return f'<i class="fas fa-{name} {class_name}" style="{style}"></i>'


class Icons:
    """Icon constants using Font Awesome."""

    ROBOT = "robot"
    CODE = "code"
    TERMINAL = "terminal"
    SHIELD = "shield-halved"
    GEAR = "gear"
    FILE = "file-code"
    HISTORY = "clock-rotate-left"
    DOLLAR = "dollar-sign"
    REFRESH = "arrows-rotate"
    TRASH = "trash"
    COPY = "copy"
    CHECK = "check-circle"
    EXCLAMATION = "exclamation-triangle"
    INFO = "circle-info"
    XMARK = "xmark-circle"
    SEARCH = "magnifying-glass"
    FLASK = "flask"
    REFACTOR = "code-branch"
    SECURITY = "shield-halved"
    REVIEW = "clipboard-check"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    CLEAR = "eraser"
    ANALYZE = "play"
    SETTINGS = "sliders"
    MOON = "moon"
    SUN = "sun"
    SUCCESS = "check-circle"
    ERROR = "circle-xmark"
    WARNING = "triangle-exclamation"
    LOADING = "spinner"
    BOLT = "bolt"
    CHART = "chart-line"
    BUG = "bug"
    LOCK = "lock"
    KEY = "key"
    SERVER = "server"
    DATABASE = "database"
    CLOUD = "cloud"
    ROCKET = "rocket"
    FIRE = "fire"
    STAR = "star"
    BRAIN = "brain"
    FOLDER = "folder-open"
    PROJECT = "folder-tree"


def render_icon_text(icon_name: str, text: str, size: str = "1em") -> str:
    """Render icon with text."""
    return f'{icon(icon_name, size)} {text}'


def render_status_badge(status: str, text: str) -> str:
    """Render a status badge with icon."""
    status_config = {
        "success": (Icons.SUCCESS, "#7ee787"),
        "error": (Icons.ERROR, "#f85149"),
        "warning": (Icons.WARNING, "#d29922"),
        "info": (Icons.INFO, "#58a6ff"),
    }
    icon_name, color = status_config.get(status, (Icons.INFO, "#58a6ff"))
    return f'''
    <span style="
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        background: {color}15;
        color: {color};
        border: 1px solid {color}30;
    ">
        {icon(icon_name, "0.9em", color)}
        {text}
    </span>
    '''


def render_metric_card(label: str, value: str, icon_name: str, color: str = "#58a6ff") -> str:
    """Render a custom metric card."""
    return f'''
    <div style="
        background: linear-gradient(135deg, {color}10 0%, {color}05 100%);
        border: 1px solid {color}30;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    ">
        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">
            {icon(icon_name, "1.5rem", color)}
        </div>
        <div style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.5rem;
            font-weight: 700;
            color: {color};
        ">{value}</div>
        <div style="
            font-size: 0.75rem;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 0.25rem;
        ">{label}</div>
    </div>
    '''


def render_code_stats(lines: int, chars: int) -> str:
    """Render code statistics."""
    return f'''
    <div style="
        display: flex;
        gap: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        color: #8b949e;
    ">
        <span>{icon("align-left", "0.9em", "#58a6ff")} <strong style="color: #e6edf3;">{lines:,}</strong> lines</span>
        <span>{icon("text-width", "0.9em", "#a371f7")} <strong style="color: #e6edf3;">{chars:,}</strong> chars</span>
    </div>
    '''
