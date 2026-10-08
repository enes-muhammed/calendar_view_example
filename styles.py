"""
styles.py - Açık/Koyu Tema Stilleri
"""

LIGHT_THEME = {
    # Genel
    "bg_primary": "#ffffff",
    "bg_secondary": "#ffffff",  # Notion-like soft gray
    "text_primary": "#37352f",  # Notion dark gray
    "text_secondary": "#787774",
    "border": "#e1e1e0",
    
    # Slim Nav
    "slim_nav_bg": "#202020",
    "slim_nav_hover": "#E5E6E8",
    "slim_nav_selected": "#4E4E4E",
    
    # Sidebar
    "sidebar_bg": "#ffffff",
    "sidebar_text": "#1D1E20",
    "sidebar_hover": "#E5E6E8",
    
    # Right Panel
    "right_panel_bg": "#ffffff",
    "right_panel_border": "#e1e1e0",
    
    # Header
    "header_bg": "#ffffff",
    "header_text": "#37352f",
    
    # Calendar
    "calendar_bg": "#ffffff",
    "grid_line": "#ededeb",
    "grid_line_hour": "#e1e1e0",
    "time_text": "#9d9b97",
    "day_header_text": "#37352f",
    
    # Today indicator
    "today_bg": "#eb5757",
    "today_text": "#ffffff",
    
    # Event
    "event_bg": "rgba(46, 170, 220, 0.2)",
    "event_hover": "rgba(46, 170, 220, 0.3)",
    "event_dragging": "rgba(46, 170, 220, 0.4)",
    "event_border": "transparent",
    "event_text": "#37352f",
    
    # Creating
    "creating_border": "rgba(46, 170, 220, 0.5)",
    "creating_bg": "rgba(46, 170, 220, 0.1)",
}

DARK_THEME = {
    # Genel
    "bg_primary": "#191919",
    "bg_secondary": "#202020",
    "text_primary": "#d4d4d4",
    "text_secondary": "#9b9b9b",
    "border": "#2f2f2f",
    
    # Slim Nav
    "slim_nav_bg": "#202020",
    "slim_nav_icon": "#d4d4d4",
    "slim_nav_selected": "#404040",
    
    # Sidebar
    "sidebar_bg": "#202020",
    "sidebar_text": "#d4d4d4",
    "sidebar_hover": "#2f2f2f",
    
    # Right Panel
    "right_panel_bg": "#191919",
    "right_panel_border": "#2f2f2f",
    
    # Header
    "header_bg": "#191919",
    "header_text": "#d4d4d4",
    
    # Calendar
    "calendar_bg": "#191919",
    "grid_line": "#2f2f2f",
    "grid_line_hour": "#3d3d3d",
    "time_text": "#666666",
    "day_header_text": "#d4d4d4",
    
    # Today indicator
    "today_bg": "#eb5757",
    "today_text": "#ffffff",
    
    # Event
    "event_bg": "rgba(60, 180, 230, 0.25)",
    "event_hover": "rgba(60, 180, 230, 0.35)",
    "event_dragging": "rgba(60, 180, 230, 0.45)",
    "event_border": "transparent",
    "event_text": "#e0e0e0",
    
    # Creating
    "creating_bg": "rgba(46, 170, 220, 0.1)",
}

# Event Renkleri (Background + Border/Strip)
# Design System: Accent Stripe + Surface Tint + Contrast Text
EVENT_COLORS = {
    "blue":   {"bg": "rgba(46, 170, 220, 0.15)", "strip": "#2e90dc", "text": "#206499"},
    "red":    {"bg": "rgba(235, 87, 87, 0.15)",  "strip": "#eb5757", "text": "#bd3e3e"},
    "orange": {"bg": "rgba(242, 153, 74, 0.15)", "strip": "#f2994a", "text": "#d97925"},
    "yellow": {"bg": "rgba(242, 201, 76, 0.15)", "strip": "#f2c94c", "text": "#b38600"}, # Darkened for text
    "green":  {"bg": "rgba(39, 174, 96, 0.15)",  "strip": "#27ae60", "text": "#1e8449"},
    "teal":   {"bg": "rgba(100, 220, 220, 0.15)", "strip": "#4fd2d2", "text": "#2a7b7b"}, # Darkened for text
    "purple": {"bg": "rgba(155, 81, 224, 0.15)", "strip": "#9b51e0", "text": "#7b3dba"},
    "pink":   {"bg": "rgba(255, 100, 150, 0.15)", "strip": "#ff6699", "text": "#d6336c"},
    "gray":   {"bg": "rgba(100, 100, 100, 0.15)", "strip": "#808080", "text": "#505050"},
}

def get_app_stylesheet(theme: dict) -> str:
    """QApplication için genel stylesheet"""
    return f"""
        QMainWindow {{
            background-color: {theme['bg_primary']};
        }}
        QFrame {{
            border: none;
            outline: none;
            background-color: transparent;
            color: transparent;
            border-radius: 12px;
            padding: 0px;
            margin: 0px;
        }}
        QScrollArea {{
            outline: none;
            background-color: transparent;
            color: transparent;
            border-radius: 12px;
            padding: 0px;
            margin: 0px;
        }}
        QScrollArea > QWidget {{ 
            background-color: green;
            border: none;
            outline: none;
            border-radius: 12px;
            padding: 0px;
            margin: 0px;
        }}
        
        QPushButton {{
            background-color: transparent;
            color: {theme['text_primary']};
            border: 1px solid transparent;
            padding: 6px 12px;
            border-radius: 6px;
            text-align: left;
        }}
        
        QPushButton:hover {{
            background-color: {theme['bg_secondary']};
        }}
        
        QPushButton:pressed {{
            background-color: {theme['border']};
        }}
        
        QLineEdit, QTextEdit, QDateTimeEdit, QComboBox {{
            background-color: {theme['bg_primary']};
            color: {theme['text_primary']};
            border: 1px solid {theme['border']};
            padding: 8px;
            border-radius: 6px;
        }}
        
        QLineEdit:focus, QTextEdit:focus {{
            border: 1px solid #2eaadc;
        }}
        
        QDialog {{
            background-color: {theme['bg_primary']};
            color: {theme['text_primary']};
            border-radius: 12px;
        }}
        
        QLabel {{
            color: {theme['text_primary']};
        }}
        
        /* Scrollbar Gizleme */
        QScrollBar:vertical, QScrollBar:horizontal {{
            width: 0px;
            height: 0px;
            border: none;
            background-color: transparent;
            color: transparent;
        }}
    """

def get_sidebar_stylesheet(theme: dict) -> str:
    """Sidebar için stylesheet"""
    return f"""
        QFrame {{
            background-color: {theme['sidebar_bg']};
            border: none;
            border-radius: 6px; 
        }}
        QWidget {{
            border: none;
        }}
        
        QPushButton {{
            text-align: left;
            padding: 8px 12px;
            border: none;
            border-radius: 6px;
            background-color: transparent;
            color: {theme['sidebar_text']};
        }}
        
        QPushButton:hover {{
            background-color: {theme['sidebar_hover']};
        }}
        QLabel {{
            border: none;
        }}
    """

def get_slim_nav_stylesheet(theme: dict) -> str:
    """İnce sol bar için stylesheet"""
    return f"""
        QFrame {{
            background-color: {theme['slim_nav_bg']};
            border-right: 1px solid {theme['border']};
            border-radius: 6px;
        }}
        QWidget {{
            border-radius: 6px;
        }}
        
        QPushButton {{
            background-color: transparent;
            border: none;
            border-radius: 6px;
            padding: 8px;
        }}
        
        QPushButton:hover {{
            background-color: {theme['sidebar_hover']};
        }}
        
        QPushButton[active="true"] {{
            background-color: {theme['slim_nav_selected']};
        }}
    """

def get_right_panel_stylesheet(theme: dict) -> str:
    """Sağ panel için stylesheet"""
    return f"""
        QFrame {{
            background-color: {theme['right_panel_bg']};
            margin: 0px;
            border-left: 1px solid {theme['border']};
        }}
        
        QLabel[header="true"] {{
            font-size: 16px;
            font-weight: bold;
            color: {theme['text_primary']};
            margin-bottom: 10px;
        }}
        
        QLabel {{
            font-size: 12px;
            font-weight: 500;
            color: {theme['text_secondary']};
            margin-top: 4px;
        }}
        
        QLineEdit, QTextEdit, QDateEdit, QTimeEdit {{
            background-color: {theme['bg_primary']};
            border: 1px solid {theme['border']};
            border-radius: 6px;
            padding: 8px;
            font-size: 13px;
            selection-background-color: rgba(46, 170, 220, 0.3);
        }}
        
        QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QTimeEdit:focus {{
            border: 1px solid #2eaadc;
            background-color: {theme['bg_primary']};
        }}
        
        QDateEdit::drop-down, QTimeEdit::drop-down {{
            border: none;
            width: 20px;
        }}
    """

def get_header_stylesheet(theme: dict) -> str:
    """Header için stylesheet"""
    return f"""
        QPushButton {{
            background-color: transparent;
            border: none;
            border-radius: 4px;
            padding: 6px 10px;
            font-weight: 500;
            color: {theme['header_text']};
        }}
        
        QPushButton:hover {{
            background-color: {theme['bg_secondary']};
        }}
        
        QComboBox {{
            border: none;
            background-color: transparent;
            padding: 4px 8px;
            color: {theme['header_text']};
        }}
        
        QComboBox::drop-down {{
            border: none;
        }}
        
        QComboBox:hover {{
            background-color: {theme['bg_secondary']};
            border-radius: 4px;
        }}
    """