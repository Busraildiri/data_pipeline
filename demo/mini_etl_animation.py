"""LinkedIn için kare formatta Mini ETL Replica GIF'i üretir."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SIZE = 720
FRAME_COUNT = 144
FRAME_DURATION_MS = 75

COLORS = {
    "background": "#07111F",
    "surface": "#0E1D2F",
    "surface_alt": "#12263D",
    "text": "#F5F7FA",
    "muted": "#8FA6BF",
    "mysql": "#29B6F6",
    "postgres": "#9B7BFF",
    "extract": "#4DD0A8",
    "validate": "#FFB74D",
    "silver": "#AFC3D8",
    "gold": "#FFD166",
    "success": "#50D890",
    "danger": "#FF6B7A",
    "line": "#29425F",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


FONTS = {
    "title": font(34, True),
    "subtitle": font(17),
    "node": font(19, True),
    "small": font(14),
    "tiny": font(12),
    "metric": font(27, True),
}


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def ease(value: float) -> float:
    value = clamp(value)
    return value * value * (3 - 2 * value)


def phase(frame: int, start: int, end: int) -> float:
    return ease((frame - start) / max(1, end - start))


def lerp(start: float, end: float, progress: float) -> float:
    return start + (end - start) * progress


def rounded(draw: ImageDraw.ImageDraw, box, fill, radius=18, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def centered_text(draw, center_x, y, text, text_font, fill):
    box = draw.textbbox((0, 0), text, font=text_font)
    draw.text((center_x - (box[2] - box[0]) / 2, y), text, font=text_font, fill=fill)


def node(draw, box, title, detail, accent, active=False):
    x1, y1, x2, y2 = box
    outline = accent if active else COLORS["line"]
    rounded(draw, box, COLORS["surface"], 18, outline, 3 if active else 1)
    draw.rectangle((x1, y1 + 18, x1 + 5, y2 - 18), fill=accent)
    draw.text((x1 + 18, y1 + 17), title, font=FONTS["node"], fill=COLORS["text"])
    draw.text((x1 + 18, y1 + 47), detail, font=FONTS["small"], fill=COLORS["muted"])


def arrow(draw, start, end, progress, color):
    progress = clamp(progress)
    x1, y1 = start
    x2, y2 = end
    current = (lerp(x1, x2, progress), lerp(y1, y2, progress))
    draw.line((start, current), fill=color, width=4)
    if progress > 0.96:
        angle = math.atan2(y2 - y1, x2 - x1)
        length = 12
        left = (x2 - length * math.cos(angle - 0.5), y2 - length * math.sin(angle - 0.5))
        right = (x2 - length * math.cos(angle + 0.5), y2 - length * math.sin(angle + 0.5))
        draw.polygon((end, left, right), fill=color)


def packet(draw, x, y, label, accent, valid=True):
    box = (x - 42, y - 19, x + 42, y + 19)
    rounded(draw, box, COLORS["surface_alt"], 10, accent, 2)
    draw.ellipse((x - 32, y - 4, x - 24, y + 4), fill=COLORS["success"] if valid else COLORS["danger"])
    draw.text((x - 18, y - 8), label, font=FONTS["tiny"], fill=COLORS["text"])


def moving_packet(draw, start, end, progress, label, accent, valid=True, offset=0):
    local = clamp(progress * 1.35 - offset)
    x = lerp(start[0], end[0], ease(local))
    y = lerp(start[1], end[1], ease(local))
    if 0 < local < 1:
        packet(draw, x, y, label, accent, valid)


def metric(draw, box, value, label, accent, progress):
    x1, y1, x2, y2 = box
    rounded(draw, box, COLORS["surface"], 16, COLORS["line"], 1)
    shown = round(value * clamp(progress))
    centered_text(draw, (x1 + x2) / 2, y1 + 14, str(shown), FONTS["metric"], accent)
    centered_text(draw, (x1 + x2) / 2, y1 + 52, label, FONTS["tiny"], COLORS["muted"])


def render_frame(frame: int) -> Image.Image:
    image = Image.new("RGB", (SIZE, SIZE), COLORS["background"])
    draw = ImageDraw.Draw(image)

    draw.text((42, 30), "MINI ETL REPLICA", font=FONTS["title"], fill=COLORS["text"])
    draw.text((43, 75), "Two operational sources. One analytics layer.", font=FONTS["subtitle"], fill=COLORS["muted"])

    mysql_box = (42, 137, 224, 218)
    postgres_box = (42, 254, 224, 335)
    extract_box = (300, 196, 462, 277)
    validate_box = (510, 196, 678, 277)
    silver_box = (278, 380, 486, 471)
    gold_box = (278, 496, 486, 567)

    source_progress = phase(frame, 10, 42)
    validation_progress = phase(frame, 40, 72)
    silver_progress = phase(frame, 68, 98)
    gold_progress = phase(frame, 94, 128)

    node(draw, mysql_box, "Tayna", "MySQL • 4 source tables", COLORS["mysql"], 12 <= frame < 45)
    node(draw, postgres_box, "Misa", "PostgreSQL • 4 tables", COLORS["postgres"], 18 <= frame < 45)
    node(draw, extract_box, "EXTRACT", "Read source tables", COLORS["extract"], 25 <= frame < 55)
    node(draw, validate_box, "VALIDATE", "Schema + lifecycle rules", COLORS["validate"], 48 <= frame < 76)
    node(draw, silver_box, "SILVER", "Unified shipment events", COLORS["silver"], 72 <= frame < 104)
    if frame >= 94:
        node(draw, gold_box, "GOLD", "Views + business metrics", COLORS["gold"], frame < 128)

    arrow(draw, (224, 177), (300, 222), source_progress, COLORS["mysql"])
    arrow(draw, (224, 294), (300, 251), source_progress, COLORS["postgres"])
    arrow(draw, (462, 236), (510, 236), validation_progress, COLORS["extract"])
    arrow(draw, (594, 277), (405, 380), silver_progress, COLORS["silver"])

    moving_packet(draw, (215, 177), (348, 228), source_progress, "ORD-17", COLORS["mysql"], True, 0.00)
    moving_packet(draw, (215, 294), (348, 246), source_progress, "ORD-42", COLORS["postgres"], True, 0.22)
    moving_packet(draw, (452, 224), (493, 224), validation_progress, "VALID", COLORS["success"], True, 0.04)
    moving_packet(draw, (452, 250), (493, 250), validation_progress, "BAD ROW", COLORS["danger"], False, 0.26)

    if 58 <= frame < 92:
        reject = phase(frame, 58, 70)
        draw.line((636, 250, 662, lerp(250, 326, reject)), fill=COLORS["danger"], width=2)
        if frame >= 68:
            draw.text((562, 321), "1 invalid row rejected", font=FONTS["tiny"], fill=COLORS["danger"])

    if frame >= 82:
        rows_progress = phase(frame, 82, 103)
        for index, (owner, color) in enumerate((("tayna_ORD17", COLORS["mysql"]), ("misa_ORD42", COLORS["postgres"]))):
            y = 421 + index * 24
            width = 135 * rows_progress
            draw.rounded_rectangle((312, y, 312 + width, y + 13), radius=6, fill=color)
            if rows_progress > 0.75:
                draw.text((320, y - 1), owner, font=FONTS["tiny"], fill=COLORS["background"])

    gold_y = 588
    if frame >= 96:
        arrow(draw, (382, 471), (382, 496), gold_progress, COLORS["gold"])
        metric(draw, (42, gold_y, 236, 662), 8, "VALID EVENTS", COLORS["success"], gold_progress)
        metric(draw, (263, gold_y, 457, 662), 2, "DATA SOURCES", COLORS["silver"], gold_progress)
        metric(draw, (484, gold_y, 678, 662), 1, "REJECTED ROW", COLORS["danger"], gold_progress)

    if frame >= 122:
        outro = phase(frame, 122, 140)
        message = "RAW DATA  →  TRUSTED INSIGHT"
        box = draw.textbbox((0, 0), message, font=FONTS["subtitle"])
        x = (SIZE - (box[2] - box[0])) / 2
        draw.text((x, 676), message, font=FONTS["subtitle"], fill=COLORS["gold"])
        draw.line((190, 706, lerp(190, 530, outro), 706), fill=COLORS["gold"], width=3)
    elif frame < 96:
        draw.text((42, 663), "Python • pandas • PostgreSQL • MySQL", font=FONTS["small"], fill=COLORS["muted"])

    return image


def build_animation(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    gif_path = output_dir / "mini_etl_replica.gif"
    cover_path = output_dir / "mini_etl_cover.png"

    frames = [render_frame(frame) for frame in range(FRAME_COUNT)]
    frames[-1].save(cover_path, optimize=True)
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"GIF: {gif_path}")
    print(f"Cover: {cover_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "outputs",
    )
    args = parser.parse_args()
    build_animation(args.output_dir)


if __name__ == "__main__":
    main()
