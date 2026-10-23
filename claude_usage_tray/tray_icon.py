"""Desenha o ícone da bandeja com Pillow (supersampling para bordas suaves)."""
from PIL import Image, ImageDraw, ImageFont

STYLES = {"ring": "Anel", "battery": "Bateria", "bar": "Barra", "percent": "Porcentagem", "dot": "Ponto"}

GREEN = (48, 209, 88)
YELLOW = (255, 214, 10)
RED = (255, 69, 58)
GRAY = (142, 142, 147)
WHITE = (245, 245, 247)
DARK_TRACK = (99, 99, 102)

CANVAS = 256  # desenha grande e reduz: o PIL não faz antialiasing em arcos


def color_for(percent: float | None) -> tuple[int, int, int]:
    """Cor por nível de uso — usada nos cards do popup e no estilo "ponto"."""
    if percent is None:
        return GRAY
    if percent < 50:
        return GREEN
    if percent < 80:
        return YELLOW
    return RED


def _palette(percent: float | None, mono: bool) -> tuple[tuple, tuple]:
    """(cor do uso, cor do trilho) — colorido e monocromático só diferem na cor do uso."""
    if percent is None:
        return GRAY, DARK_TRACK
    return (WHITE if mono else GREEN), DARK_TRACK


def _font(size: int) -> ImageFont.ImageFont:
    # Windows primeiro; no Linux o Pillow procura o arquivo em /usr/share/fonts.
    for name in ("segoeuib.ttf", "arialbd.ttf", "Ubuntu-B.ttf", "DejaVuSans-Bold.ttf",
                 "LiberationSans-Bold.ttf", "NotoSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _ring(draw, p, fill, track):
    pad, width = 16, 46
    bounds = (pad, pad, CANVAS - pad, CANVAS - pad)
    draw.ellipse(bounds, outline=track, width=width)
    if p:
        draw.arc(bounds, -90, -90 + 360 * p, fill=fill, width=width)


def _battery(draw, p, fill, track):
    left, top, right, bottom, stroke = 6, 64, 222, 192, 16
    draw.rounded_rectangle((left, top, right, bottom), radius=34, outline=track, width=stroke)
    draw.rounded_rectangle((right + 10, 104, right + 30, 152), radius=8, fill=track)
    inset = stroke + 12
    inner_right = left + inset + (right - left - 2 * inset) * p
    if p:
        draw.rounded_rectangle((left + inset, top + inset, max(inner_right, left + inset + 24), bottom - inset),
                               radius=16, fill=fill)


def _bar(draw, p, fill, track):
    left, top, right, bottom = 4, 88, CANVAS - 4, 168
    radius = (bottom - top) // 2
    draw.rounded_rectangle((left, top, right, bottom), radius=radius, fill=track)
    if p:
        draw.rounded_rectangle((left, top, max(left + (right - left) * p, left + 2 * radius), bottom),
                               radius=radius, fill=fill)


def _percent(draw, percent, fill):
    text = "–" if percent is None else f"{min(round(percent), 100)}%"
    size = 170
    while size > 40:
        font = _font(size)
        box = draw.textbbox((0, 0), text, font=font)
        if box[2] - box[0] <= CANVAS - 8:
            break
        size -= 6
    x = (CANVAS - (box[2] - box[0])) / 2 - box[0]
    y = (CANVAS - (box[3] - box[1])) / 2 - box[1]
    draw.text((x, y), text, font=font, fill=fill)


def _dot(draw, percent, mono):
    color = WHITE if mono and percent is not None else color_for(percent)
    r = 76
    draw.ellipse((CANVAS / 2 - r, CANVAS / 2 - r, CANVAS / 2 + r, CANVAS / 2 + r), fill=color)


def render(percent: float | None, style: str = "ring", mono: bool = False, size: int = 64) -> Image.Image:
    img = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    fill, track = _palette(percent, mono)
    p = 0 if percent is None else max(0.0, min(percent, 100)) / 100
    if style == "battery":
        _battery(draw, p, fill, track)
    elif style == "bar":
        _bar(draw, p, fill, track)
    elif style == "percent":
        _percent(draw, percent, fill)
    elif style == "dot":
        _dot(draw, percent, mono)
    else:
        _ring(draw, p, fill, track)
    return img.resize((size, size), Image.LANCZOS)
