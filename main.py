#!/usr/bin/env python3
"""The Breach - a whale made of light breaching over a moonlit night sea.

Purely procedural, deterministic Pillow art for make.fun bounty ai-excited-01.
Writes a single 1024x1024 PNG to /output/entry.png (<1 MiB).
"""
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

W = H = 1024
HORIZON = int(H * 0.56)
rng = random.Random(20261116)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(size, stops):
    """Vertical gradient image from color stops [(y_frac, rgb), ...]."""
    w, h = size
    img = Image.new("RGB", (1, h))
    px = img.load()
    for y in range(h):
        t = y / (h - 1)
        for i in range(len(stops) - 1):
            y0, c0 = stops[i]
            y1, c1 = stops[i + 1]
            if y0 <= t <= y1:
                f = (t - y0) / max(1e-6, (y1 - y0))
                px[0, y] = lerp(c0, c1, f)
                break
        else:
            px[0, y] = stops[-1][1]
    return img.resize((w, h), Image.BILINEAR)


def add_glow(img, layer, strength):
    """Screen-blend a glowing black-background layer onto img."""
    lit = ImageChops.screen(img, layer)
    return Image.blend(img, lit, strength)


def whale_path(t):
    """Parametric whale spine: 0=tail tip, 1=snout. Returns (x, y)."""
    x = 190 + 700 * t
    y = 610 - 330 * math.sin(math.pi * (t ** 0.85)) - 90 * t
    return x, y


def whale_normal(t):
    """Unit normal of the spine at parameter t, pointing to the upper side."""
    e = 0.01
    x0, y0 = whale_path(max(0, t - e))
    x1, y1 = whale_path(min(1, t + e))
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = dy / L, -dx / L
    if ny > 0:
        nx, ny = -nx, -ny
    return nx, ny


def thickness(t):
    return 24 + 78 * math.sin(math.pi * min(1.0, t * 1.08)) ** 0.65


def whale_outline():
    """Closed polygon: top edge tail->snout, rounded snout, bottom edge back."""
    n = 160
    top, bot = [], []
    for i in range(n + 1):
        t = i / n
        x, y = whale_path(t)
        nx, ny = whale_normal(t)
        th = thickness(t)
        top.append((x + nx * th, y + ny * th))
        bot.append((x - nx * th, y - ny * th))
    # rounded snout: arc sweeping from the top side around to the bottom side
    sx, sy = whale_path(1.0)
    nx, ny = whale_normal(1.0)
    tx, ty = -ny, nx  # tangent from top side to bottom side at the head
    r = thickness(1.0) * 0.9
    snout = []
    for a in range(10, 171, 8):
        ang = math.radians(a)
        px = sx + nx * r * math.cos(ang) + tx * r * math.sin(ang)
        py = sy + ny * r * math.cos(ang) + ty * r * math.sin(ang)
        snout.append((px, py))
    return top + snout + bot[::-1], top, bot


def draw_whale_layers():
    """Return (rim, fill, mask) layers for the whale body."""
    body, top, bot = whale_outline()

    rim = Image.new("RGB", (W, H), (0, 0, 0))
    rd = ImageDraw.Draw(rim)
    n = len(top) - 1
    for i in range(n):
        t0 = i / n
        b = 0.5 + 0.5 * math.sin(math.pi * t0)
        c = lerp((70, 150, 255), (190, 240, 255), b)
        rd.line([top[i], top[i + 1]], fill=c, width=5)
        c2 = lerp((50, 110, 220), (110, 190, 255), b)
        rd.line([bot[i], bot[i + 1]], fill=c2, width=3)
    rd.line(body + [body[0]], fill=(60, 120, 230), width=3)

    # body gradient fill: bright moonlit top, deep blue belly
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(body, fill=255)
    ylo = int(min(p[1] for p in body))
    yhi = int(max(p[1] for p in body))
    grad = vgrad((W, yhi - ylo + 1), [
        (0.00, (110, 190, 255)),
        (0.35, (56, 110, 200)),
        (0.75, (30, 60, 130)),
        (1.00, (16, 34, 84)),
    ])
    fill = Image.new("RGB", (W, H), (0, 0, 0))
    fill.paste(grad, (0, ylo))

    # glowing eye
    ex, ey = whale_path(0.9)
    enx, eny = whale_normal(0.9)
    off = thickness(0.9) * 0.45
    ex, ey = ex + enx * off, ey + eny * off
    fd = ImageDraw.Draw(fill)
    fd.ellipse([ex - 6, ey - 6, ex + 6, ey + 6], fill=(210, 240, 255))
    fd.ellipse([ex - 3, ey - 3, ex + 3, ey + 3], fill=(120, 220, 255))

    return rim, fill, mask


def aurora_layer():
    band = Image.new("RGB", (W, H), (0, 0, 0))
    bd = ImageDraw.Draw(band)
    for k, (col, amp, yc, width) in enumerate([
        ((60, 240, 180), 60, 130, 70),
        ((90, 140, 255), 80, 210, 55),
        ((170, 100, 255), 55, 80, 45),
    ]):
        for x in range(0, W, 3):
            yy = yc + amp * math.sin(x / 170 + k * 2.1) + 16 * math.sin(x / 51 + k)
            c = tuple(int(c * (0.65 + 0.35 * math.sin(x / 90 + k))) for c in col)
            bd.line([x, yy, x, yy + width], fill=c)
    return band.filter(ImageFilter.GaussianBlur(16))


def main():
    img = vgrad((W, H), [
        (0.00, (3, 5, 18)),
        (0.35, (9, 15, 42)),
        (0.52, (18, 32, 68)),
        (0.555, (26, 52, 100)),
        (0.60, (14, 28, 62)),
        (0.80, (8, 16, 40)),
        (1.00, (2, 4, 14)),
    ]).convert("RGB")
    draw = ImageDraw.Draw(img)

    # --- stars ---
    for _ in range(320):
        x = rng.randint(0, W - 1)
        y = rng.randint(0, HORIZON - 60)
        b = rng.uniform(0.2, 1.0)
        c = lerp((50, 70, 120), (255, 255, 255), b)
        r = 1 if b < 0.85 else 2
        draw.ellipse([x - r, y - r, x + r, y + r], fill=c)

    # --- aurora ---
    img = add_glow(img, aurora_layer(), 0.7)
    draw = ImageDraw.Draw(img)

    # --- moon with soft halo ---
    mx, my, mr = 780, 140, 54
    halo = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(halo).ellipse(
        [mx - mr, my - mr, mx + mr, my + mr], fill=(255, 248, 225))
    img = add_glow(img, halo.filter(ImageFilter.GaussianBlur(26)), 0.55)
    draw = ImageDraw.Draw(img)
    draw.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(255, 252, 240))

    # --- sea: subtle horizontal swell shading ---
    for y in range(HORIZON, H, 2):
        t = (y - HORIZON) / (H - HORIZON)
        c = lerp((24, 44, 92), (6, 12, 34), t)
        draw.line([0, y, W, y], fill=c)

    # --- moonlight path: shimmering dashes only (no solid wedge) ---
    for _ in range(1500):
        t = rng.random() ** 1.6
        y = HORIZON + t * (H - HORIZON)
        if y < HORIZON + 18:
            continue  # let the glow-beneath-whale own the horizon band
        wcol = 40 + 240 * t
        sx = mx + rng.uniform(-wcol / 2, wcol / 2)
        sw = rng.uniform(4, 8 + 26 * t)
        b = rng.uniform(0.15, 0.95) * (1 - 0.45 * t) * min(1.0, (y - HORIZON) / 120)
        c = lerp((40, 70, 130), (210, 230, 255), b)
        draw.line([sx, y, sx + sw, y], fill=c)

    # --- whale ---
    rim, fill, mask = draw_whale_layers()
    body_glow = ImageChops.screen(rim.filter(ImageFilter.GaussianBlur(14)),
                                  rim.filter(ImageFilter.GaussianBlur(3)))
    img = add_glow(img, body_glow, 0.9)
    img.paste(fill, (0, 0), mask)
    img = add_glow(img, rim.filter(ImageFilter.GaussianBlur(2)), 0.6)
    draw = ImageDraw.Draw(img)

    # --- splash crown where the tail tore the water ---
    tx, ty = whale_path(0)
    crown = Image.new("RGB", (W, H), (0, 0, 0))
    crd = ImageDraw.Draw(crown)
    for _ in range(520):
        ang = rng.uniform(-math.pi * 0.95, -math.pi * 0.05)
        sp = rng.uniform(10, 260)
        px = tx + sp * math.cos(ang) * 1.7
        py = ty + sp * math.sin(ang) * 1.1
        if 0 <= px < W and 0 <= py < HORIZON + 40:
            b = rng.uniform(0.4, 1.0)
            r = rng.choice([1, 1, 2, 2, 3])
            crd.ellipse([px - r, py - r, px + r, py + r],
                        fill=lerp((90, 170, 255), (255, 255, 255), b))
    core = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(core).ellipse(
        [tx - 34, ty - 22, tx + 34, ty + 22], fill=(90, 160, 235))
    img = add_glow(img, crown.filter(ImageFilter.GaussianBlur(1)), 0.9)
    img = add_glow(img, core.filter(ImageFilter.GaussianBlur(10)), 0.7)
    draw = ImageDraw.Draw(img)

    # --- glowing water pouring off the belly, falling toward the sea ---
    for _ in range(150):
        t = rng.uniform(0.15, 0.92)
        x, y = whale_path(t)
        nx, ny = whale_normal(t)
        d = thickness(t) + rng.uniform(2, 20)
        px, py = x - nx * d, y - ny * d
        fall = rng.uniform(10, 150) * min(1.0, py / HORIZON)
        ex, ey = px + fall * 0.4, py + fall
        if ey < H:
            w = rng.choice([1, 1, 2])
            c = lerp((120, 190, 255), (255, 255, 255), rng.uniform(0.4, 1.0))
            draw.line([px, py, ex, ey], fill=c, width=w)

    # --- horizon + glow beneath the whale ---
    draw.line([0, HORIZON, W, HORIZON], fill=(70, 105, 160), width=2)
    under = Image.new("RGB", (W, H), (0, 0, 0))
    ud = ImageDraw.Draw(under)
    for i in range(0, 91, 3):
        t = i / 90
        x, _ = whale_path(t)
        ud.ellipse([x - 34, HORIZON + 8, x + 34, HORIZON + 24],
                   fill=(80, 160, 255))
    img = add_glow(img, under.filter(ImageFilter.GaussianBlur(16)), 0.6)

    os.makedirs("/output", exist_ok=True)
    out = "/output/entry.png"
    img.save(out, optimize=True)
    print("saved", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
