from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(BASE_DIR, "fonts")

deadline = datetime(2026, 12, 1, 0, 0, tzinfo=timezone.utc)

RED = (218, 41, 28, 255)
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
CREAM = (251, 248, 237, 255)

WIDTH, HEIGHT = 622, 180
COL_SPACING = 150  # 4 columns now, so tighter than the old 175
HEADING_Y = 30
NUMBER_Y = 100
LABEL_Y = 150
FAKE_ITALIC_SHEAR = 0.22

HEADING_FONTS = ["Obviously-BlackItalic.otf", "Avenir-Black.ttf"]
ITALIC_FONTS = ["Obviously-BlackItalic.otf", "Avenir-HeavyOblique.ttf", "Avenir-BlackItalic.ttf"]
UPRIGHT_BLACK_FONTS = ["Obviously-BlackItalic.otf", "Avenir-Heavy.ttf"]


def try_load(candidates, size):
    for name in candidates:
        path = os.path.join(FONT_DIR, name)
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return None


def load_heading_font(size):
    return try_load(HEADING_FONTS, size) or ImageFont.load_default(size)


def load_italic_font(size):
    """Returns (font, needs_fake_italic)."""
    font = try_load(ITALIC_FONTS, size)
    if font:
        return font, False
    font = try_load(UPRIGHT_BLACK_FONTS, size)
    if font:
        return font, True
    return ImageFont.load_default(size), True


def draw_text(img, xy, text, font, fill, fake_italic=False):
    """Draw centered text at xy; optionally shear it to fake an italic."""
    if not fake_italic:
        ImageDraw.Draw(img).text(xy, text, font=font, fill=fill, anchor="mm")
        return

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, text, font=font, fill=fill, anchor="mm")
    k = FAKE_ITALIC_SHEAR
    layer = layer.transform(
        img.size, Image.AFFINE, (1, k, -k * xy[1], 0, 1, 0), resample=Image.BICUBIC
    )
    img.alpha_composite(layer)


def draw_frame(now):
    remaining = max(deadline - now, timedelta(0))

    days = remaining.days
    hours, rem = divmod(remaining.seconds, 3600)
    minutes, seconds = divmod(rem, 60)

    img = Image.new("RGBA", (WIDTH, HEIGHT), BLACK)

    font_heading = load_heading_font(30)
    font_big, big_fake = load_italic_font(76)
    font_small, small_fake = load_italic_font(22)

    # Heading
    draw_text(img, (WIDTH // 2, HEADING_Y), "TIME LEFT TO TRIPLE YOUR GIFT:", font_heading, CREAM)

    # Columns
    columns = [
        ("DAYS", f"{days:02}"),
        ("HOURS", f"{hours:02}"),
        ("MINS", f"{minutes:02}"),
        ("SECS", f"{seconds:02}"),
    ]

    center_x = WIDTH // 2
    offset = (len(columns) - 1) / 2
    for i, (label, value) in enumerate(columns):
        x = int(center_x + (i - offset) * COL_SPACING)
        draw_text(img, (x, NUMBER_Y), value, font_big, CREAM, big_fake)
        draw_text(img, (x, LABEL_Y), label, font_small, CREAM, small_fake)

    return img.convert("RGB")


def generate_assets():
    frames = []

    start_time = datetime.now(timezone.utc)

    # Advance 1 second per frame.
    # 60 frames x 1s = a 1-minute countdown before the GIF loops.
    for i in range(60):
        frame_time = start_time + timedelta(seconds=i)
        frames.append(draw_frame(frame_time))

    # Animated GIF
    frames[0].save(
        "timer-email.gif",
        save_all=True,
        append_images=frames[1:],
        duration=1000,  # 1s per frame
        loop=0,
        optimize=True,
    )

    # Static fallback PNG (first frame)
    frames[0].save("timer-email.png", optimize=True)


if __name__ == "__main__":
    generate_assets()
