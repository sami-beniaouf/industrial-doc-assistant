"""Small helpers to draw the README diagrams as standalone SVG files.

Icons are embedded as data URIs: GitHub renders SVG files as images, which cannot
load external files.
"""
import base64
from pathlib import Path
from xml.sax.saxutils import escape as e

HERE = Path(__file__).parent
FONT = "Segoe UI, Helvetica, Arial, sans-serif"
INK, MUTED, LINE = "#1d2939", "#475467", "#667085"
COL = {
    "src": ("#f2f4f7", "#98a2b3"), "azure": ("#e8f1fc", "#2e7bcf"), "fabric": ("#e7f6ee", "#23935f"),
    "out": ("#fff5e5", "#d98a12"), "gh": ("#f2f0fb", "#6d4fc2"), "fail": ("#fdecec", "#d64545"),
    "silent": ("#fff6e0", "#c98a00"), "plain": ("#ffffff", "#98a2b3"), "white": ("#ffffff", "#d0d5dd"),
}


ICON_DIR = HERE.parent / "icons"
ICON_FILES = {
    "python": "Python.svg",
    "streamlit": "Streamlit.svg",
    "foundry": "ai-foundry.svg",
    "search": "cognitive-search.svg",
    "openai": "openai-svgrepo-com.svg",
    "pdf": "pdf-svgrepo-com.svg",
}


def icon_uri(name):
    data = (ICON_DIR / ICON_FILES[name]).read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(data).decode()


class Svg:
    def __init__(self, w):
        self.w, self.out, self.markers, self.icons = w, [], {LINE}, set()

    def t(self, x, y, s, size=13, weight="normal", fill=MUTED, anchor="middle"):
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
                        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{e(s)}</text>')

    def rect(self, x, y, w, h, kind, r=12, sw=1.5):
        f, s = COL[kind]
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" '
                        f'fill="{f}" stroke="{s}" stroke-width="{sw}"/>')

    def image(self, name, x, y, size):
        # each icon is embedded once as a symbol, then reused
        self.icons.add(name)
        self.out.append(f'<use href="#icon-{name}" x="{x:.1f}" y="{y:.1f}" width="{size}" height="{size}"/>')

    def zone(self, x, y, w, h, fill, stroke, label=None, lcolor=MUTED, icon=None):
        self.out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="16" '
                        f'fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>')
        if label:
            dx = 0
            if icon:
                self.image(icon, x + 14, y + 10, 20)
                dx = 28
            self.t(x + 14 + dx, y + 25, label, 13, "bold", lcolor, "start")

    def box(self, x, y, w, h, title, lines, kind, tsize=15, lsize=12.5, icon=None, isize=28):
        self.rect(x, y, w, h, kind)
        titles = title if isinstance(title, list) else [title]
        block = len(titles) * 19 + len(lines) * 18 + (4 if lines else -18) + (isize + 8 if icon else 0)
        top = y + (h - block) / 2 + 14
        if icon:
            self.image(icon, x + w / 2 - isize / 2, top - 14, isize)
            top += isize + 8
        for k, tt in enumerate(titles):
            self.t(x + w / 2, top + k * 19, tt, tsize, "bold", INK)
        base = top + (len(titles) - 1) * 19 + 22
        for k, line in enumerate(lines):
            self.t(x + w / 2, base + k * 18, line, lsize)

    def arrow(self, pts, color=LINE, dash=None):
        p = " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.markers.add(color)
        self.out.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="2" '
                        f'marker-end="url(#{self._mid(color)})" stroke-linejoin="round"{d}/>')

    def line(self, x1, y1, x2, y2, color="#eaecf0", sw=1.5):
        self.out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"/>')

    @staticmethod
    def _mid(color):
        return "a" + color.strip("#")

    def save(self, name, h, label):
        markers = "".join(
            f'<marker id="{self._mid(c)}" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" '
            f'refX="8" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="{c}"/></marker>'
            for c in sorted(self.markers))
        markers += "".join(
            f'<symbol id="icon-{n}" viewBox="0 0 1 1"><image href="{icon_uri(n)}" width="1" height="1"/></symbol>'
            for n in sorted(self.icons))
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{h}" '
               f'viewBox="0 0 {self.w} {h}" role="img" aria-label="{e(label)}">\n'
               f'<defs>{markers}</defs>\n<rect width="{self.w}" height="{h}" fill="#ffffff"/>\n'
               + "\n".join(self.out) + "\n</svg>\n")
        (HERE.parent / name).write_text(svg, encoding="utf-8")
