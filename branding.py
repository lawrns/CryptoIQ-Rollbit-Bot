"""
CryptoIQ Design Tokens and Tkinter/ttk theming utilities.
This concentrates brand colors, typography, spacing, and ttk styles in one place
so the GUI can be themed consistently and easily tweaked later.
"""
from typing import Tuple
import tkinter as tk
from tkinter import ttk, font as tkfont

def _clamp(n: int) -> int:
    return max(0, min(255, n))

def adjust_brightness(hex_color: str, factor: float) -> str:
    """Return a color brightened (>1) or darkened (<1) by factor."""
    hex_color = hex_color.strip()
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = _clamp(int(r * factor))
    g = _clamp(int(g * factor))
    b = _clamp(int(b * factor))
    return f"#{r:02X}{g:02X}{b:02X}"

# Color tokens (hex)
COLORS = {
    "bg_primary": "#0A0B1E",
    "bg_secondary": "#14162A",
    "border": "#2D3148",
    "text_primary": "#FFFFFF",
    "text_secondary": "#D1D5DB",
    "text_tertiary": "#9CA3AF",
    "accent_green": "#00FFA3",
    "accent_purple": "#A855F7",
    "icon_blue": "#3B82F6",
    "positive": "#22C55E",
    "negative": "#EF4444",
    "shadow": "#000000",  # for reference; ttk has limited shadow support
}

# Spacing/radius
SPACE = 8
RADIUS = 8

# Font tokens (prefer Inter; fallback to platform defaults)
PRIMARY_FONT_CANDIDATES = [
    "Inter", "SF Pro Text", "SF Pro Display", "Segoe UI", "Helvetica", "Arial"
]
# Secondary (mono) for numbers/code-like labels
SECONDARY_FONT_CANDIDATES = [
    "JetBrains Mono", "Menlo", "Consolas", "Courier New"
]

FONTS = {
    # GUI-scaled sizes (pt). H1/H2 slightly reduced for window context.
    "h1": ("", 18, "bold"),
    "h2": ("", 14, "bold"),
    "h3": ("", 12, "semibold"),
    "h4": ("", 11, "medium"),
    "body": ("", 12, "normal"),
    "small": ("", 10, "normal"),
    "button": ("", 12, "bold"),
    "stats": ("", 14, "bold"),
    # Optional: explicit mono/numbers keys use secondary family
    "mono": ("", 12, "normal"),
    "numbers": ("", 12, "bold"),
}


def _pick_font_family(root: tk.Misc, candidates) -> str:
    families = set(tkfont.families(root))
    for name in candidates:
        if name in families:
            return name
    return candidates[-1] if candidates else "Helvetica"


def apply_theme(root: tk.Tk) -> None:
    """Apply CryptoIQ theme to ttk widgets and base window."""
    root.configure(bg=COLORS["bg_primary"])

    # Choose primary and secondary families and patch FONTS tuples
    primary_family = _pick_font_family(root, PRIMARY_FONT_CANDIDATES)
    secondary_family = _pick_font_family(root, SECONDARY_FONT_CANDIDATES)
    for key, spec in list(FONTS.items()):
        fam = primary_family
        if key in ("stats", "mono", "numbers"):
            fam = secondary_family
        FONTS[key] = (fam, spec[1], spec[2])

    # Global default font overrides
    root.option_add("*Font", FONTS["body"])  # default
    root.option_add("*foreground", COLORS["text_primary"])  # tk widgets
    root.option_add("*background", COLORS["bg_primary"])  # tk widgets bg

    style = ttk.Style(root)

    # Use 'clam' for better color control across platforms
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # Base colors
    style.configure("Crypto.TFrame", background=COLORS["bg_primary"])
    style.configure("Crypto.Surface.TFrame", background=COLORS["bg_secondary"], bordercolor=COLORS["border"], relief="flat")
    style.configure("Crypto.TLabelframe", background=COLORS["bg_secondary"], foreground=COLORS["text_primary"], bordercolor=COLORS["border"], relief="flat")
    style.configure("Crypto.TLabelframe.Label", background=COLORS["bg_secondary"], foreground=COLORS["text_secondary"], font=FONTS["h4"])

    # Labels
    style.configure("Crypto.TLabel", background=COLORS["bg_primary"], foreground=COLORS["text_primary"], font=FONTS["body"])
    style.configure("Crypto.Muted.TLabel", background=COLORS["bg_primary"], foreground=COLORS["text_secondary"], font=FONTS["small"])
    style.configure("Crypto.Header.TLabel", background=COLORS["bg_primary"], foreground=COLORS["text_primary"], font=FONTS["h2"])
    style.configure("Crypto.StatusGood.TLabel", background=COLORS["bg_primary"], foreground=COLORS["positive"], font=FONTS["h4"])
    style.configure("Crypto.StatusWarn.TLabel", background=COLORS["bg_primary"], foreground="#F59E0B", font=FONTS["h4"])  # amber
    style.configure("Crypto.StatusBad.TLabel", background=COLORS["bg_primary"], foreground=COLORS["negative"], font=FONTS["h4"])

    # Buttons (primary/secondary/danger/purple) with simple hover/pressed brightening
    def _button_base(style_name: str, bg: str, fg: str = COLORS["bg_primary" ]):
        style.configure(style_name,
                        background=bg, foreground=fg, font=FONTS["button"],
                        bordercolor=COLORS["border"], borderwidth=1, focusthickness=0,
                        padding=(16, 10))
        style.map(style_name,
                  background=[("active", adjust_brightness(bg, 1.08)),
                             ("pressed", adjust_brightness(bg, 0.95))],
                  foreground=[("disabled", COLORS["text_tertiary"])])

    _button_base("Crypto.Primary.TButton", COLORS["accent_green"], COLORS["bg_primary"])  # green CTA
    _button_base("Crypto.Secondary.TButton", COLORS["bg_secondary"], COLORS["accent_green"])  # outline-like
    style.configure("Crypto.Secondary.TButton", bordercolor=COLORS["accent_green"], borderwidth=2)
    _button_base("Crypto.Purple.TButton", COLORS["accent_purple"], COLORS["text_primary"])
    _button_base("Crypto.Danger.TButton", COLORS["negative"], COLORS["text_primary"])
    _button_base("Crypto.Neutral.TButton", COLORS["icon_blue"], COLORS["text_primary"])

    # Entries
    style.configure("Crypto.TEntry", fieldbackground=COLORS["bg_secondary"], background=COLORS["bg_secondary"], foreground=COLORS["text_primary"], bordercolor=COLORS["border"], lightcolor=COLORS["border"], darkcolor=COLORS["border"], padding=8, font=FONTS["mono"])

    # Treeview (positions table) with alternating rows
    alt_row = "#1A1C3B"
    # Treeview row tag foregrounds (row-level coloring)
    style.map("Crypto.Treeview", foreground=[
        ("!disabled", COLORS["text_primary"]),
        ("selected", COLORS["text_primary"])  # keep selected readable
    ])

    style.configure("Crypto.Treeview",
                    background=COLORS["bg_secondary"], fieldbackground=COLORS["bg_secondary"],
                    foreground=COLORS["text_primary"], rowheight=26,
                    bordercolor=COLORS["border"], borderwidth=1,
                    font=FONTS["mono"])
    style.configure("Crypto.Treeview.Heading",
                    background=COLORS["bg_secondary"], foreground=COLORS["text_secondary"],
                    font=FONTS["mono"], bordercolor=COLORS["border"], borderwidth=0)
    style.map("Crypto.Treeview.Heading", background=[("active", COLORS["bg_secondary"])])

    # Alternate row tag colors configured in GUI; this sets defaults
    style.map("Crypto.Treeview", background=[("selected", adjust_brightness(COLORS["bg_secondary"], 1.15))])

# Canvas utilities for gradients and shapes
def draw_vertical_gradient(canvas: tk.Canvas, x: int, y: int, width: int, height: int, start_hex: str, end_hex: str, steps: int = 120) -> None:
    """Draw a vertical gradient on a canvas from start_hex (top) to end_hex (bottom)."""
    # Parse colors
    s = start_hex.lstrip('#')
    e = end_hex.lstrip('#')
    sr, sg, sb = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    er, eg, eb = int(e[0:2], 16), int(e[2:4], 16), int(e[4:6], 16)
    for i in range(steps):
        t = i / max(1, steps - 1)
        r = int(sr + (er - sr) * t)
        g = int(sg + (eg - sg) * t)
        b = int(sb + (eb - sb) * t)
        color = f"#{r:02X}{g:02X}{b:02X}"
        y0 = y + int(height * (i / steps))
        y1 = y + int(height * ((i + 1) / steps))
        canvas.create_rectangle(x, y0, x + width, y1, outline=color, fill=color)


def draw_horizontal_gradient(canvas: tk.Canvas, x: int, y: int, width: int, height: int, start_hex: str, end_hex: str, steps: int = 180) -> None:
    """Draw a horizontal gradient on a canvas from start_hex (left) to end_hex (right)."""
    s = start_hex.lstrip('#')
    e = end_hex.lstrip('#')
    sr, sg, sb = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    er, eg, eb = int(e[0:2], 16), int(e[2:4], 16), int(e[4:6], 16)
    for i in range(steps):
        t = i / max(1, steps - 1)
        r = int(sr + (er - sr) * t)
        g = int(sg + (eg - sg) * t)
        b = int(sb + (eb - sb) * t)
        color = f"#{r:02X}{g:02X}{b:02X}"
        x0 = x + int(width * (i / steps))
        x1 = x + int(width * ((i + 1) / steps))
        canvas.create_rectangle(x0, y, x1, y + height, outline=color, fill=color)


def draw_rounded_rect(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, r: int, fill: str, outline: str = "", width: int = 1):
    """Draw a rounded rectangle and return created item ids as a tuple."""
    r = max(0, min(r, (x2 - x1)//2, (y2 - y1)//2))
    items = []
    # Center
    items.append(canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline=outline, width=width))
    items.append(canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline=outline, width=width))
    # Corners
    items.append(canvas.create_oval(x1, y1, x1 + 2*r, y1 + 2*r, fill=fill, outline=outline, width=width))
    items.append(canvas.create_oval(x2 - 2*r, y1, x2, y1 + 2*r, fill=fill, outline=outline, width=width))
    items.append(canvas.create_oval(x1, y2 - 2*r, x1 + 2*r, y2, fill=fill, outline=outline, width=width))
    items.append(canvas.create_oval(x2 - 2*r, y2 - 2*r, x2, y2, fill=fill, outline=outline, width=width))
    return tuple(items)


def draw_pill(canvas: tk.Canvas, x: int, y: int, text: str, padding_x: int = 12, padding_y: int = 6, bg: str = COLORS["bg_secondary"], fg: str = COLORS["text_primary" ], radius: int = RADIUS, outline: str = "", font=None):
    """Draw a pill-like badge with text; returns (rect_ids, text_id, bbox)."""
    if font is None:
        font = FONTS["small"]
    # Measure text width approximately using tkinter font
    try:
        from tkinter import font as tkfont
        f = tkfont.Font(family=font[0], size=font[1], weight=font[2] if len(font) > 2 else "normal")
        tw = f.measure(text)
        th = f.metrics("linespace")
    except Exception:
        tw, th = len(text) * 7, 14
    w = tw + padding_x * 2
    h = th + padding_y * 2
    rect_ids = draw_rounded_rect(canvas, x, y, x + w, y + h, radius, fill=bg, outline=outline)
    text_id = canvas.create_text(x + w/2, y + h/2, text=text, fill=fg, font=font)
    return rect_ids, text_id, (x, y, x + w, y + h)

class CanvasCard(tk.Frame):
    """A container frame that draws a rounded rectangle background using Canvas.

    Children should be added to `self.content`.
    """
    def __init__(self, parent, padding: int = 16, radius: int = RADIUS,
                 surface_bg: str = COLORS["bg_secondary"], border: str = COLORS["border"], **kwargs):
        super().__init__(parent, bg=COLORS["bg_primary"], **kwargs)
        self.padding = padding
        self.radius = radius
        self.surface_bg = surface_bg
        self.border = border

        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=COLORS["bg_primary"])
        self.canvas.pack(fill="both", expand=True)


# Helper to configure Treeview tags with brand colors
def configure_treeview_tags(tree: tk.Widget) -> None:
    try:
        tree.tag_configure('odd', background="#1A1C3B")
        tree.tag_configure('even', background=COLORS["bg_secondary"])
        tree.tag_configure('dir_up', foreground=COLORS['positive'])
        tree.tag_configure('dir_down', foreground=COLORS['negative'])
        tree.tag_configure('pnl_pos', foreground=COLORS['positive'])
        tree.tag_configure('pnl_neg', foreground=COLORS['negative'])
    except Exception:
        pass

        # Content frame overlays the canvas
        self.content = tk.Frame(self, bg=self.surface_bg)
        self.content.place(x=self.padding, y=self.padding,
                           relwidth=1.0, relheight=1.0,
                           width=-(self.padding * 2), height=-(self.padding * 2))

        self.bind("<Configure>", self._redraw)

    def _redraw(self, event=None):
        self.canvas.delete("all")
        w = max(0, self.winfo_width())
        h = max(0, self.winfo_height())
        # Inset to account for border stroke being on edge
        x1, y1 = 0 + 0, 0 + 0
        x2, y2 = w - 1, h - 1
        draw_rounded_rect(self.canvas, x1, y1, x2, y2, self.radius,
                          fill=self.surface_bg, outline=self.border)




def status_badge(parent: tk.Widget, text: str, fg: str, bg: str = COLORS["bg_secondary"]) -> tk.Label:
    """Create a small pill-like status badge as a tk.Label."""
    lbl = tk.Label(parent, text=text, fg=fg, bg=bg, padx=10, pady=4, font=FONTS["small"])
    return lbl

