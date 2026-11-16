#!/usr/bin/env python3
"""Generate /output/entry.png: 'The Breach' — a whale of pure light arcing
over a moonlit sea at the instant its glowing nose tears the water open.
Pure procedural art. Deterministic (fixed seed), no network, Pillow only.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

SIZE = 1024
SS = 2  # supersample factor
RND = random.Random(20261116)

# whale spine control points (fractions of w/h) — nose low-left, back high
P0 = (0.13, 0.60)
P1 = (0.05, 0.30)
P2 = (0.44, 0.10)
P3 = (0.74, 0.30)


def mix(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def bezier(p0, p1, p2, p3, t):
    mt = 1 - t
    return (mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0],
            mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1])


def bez_width(t):
    """Half-width of the body along the spine (in 1024-units)."""
    base = 120 * (math.sin(math.pi * (0.06 + 0.94 * t)) ** 0.85)
    return base * (1.0 - 0.45 * t)


def body_geometry(w, h):
    p0 = (P0[0] * w, P0[1] * h)
    p1 = (P1[0] * w, P1[1] * h)
    p2 = (P2[0] * w, P2[1] * h)
    p3 = (P3[0] * w, P3[1] * h)
    N = 260
    spine = [bezier(p0, p1, p2, p3, i / N) for i in range(N + 1)]
    tangents = []
    for i in range(N + 1):
        a = max(0, i - 1); b = min(N, i + 1)
        tx = spine[b][0] - spine[a][0]; ty = spine[b][1] - spine[a][1]
        n = math.hypot(tx, ty) or 1.0
        tangents.append((tx / n, ty / n))
    S = w / 1024.0
    top, bot = [], []
    for i in range(N + 1):
        t = i / N
        x, y = spine[i]
        tx, ty = tangents[i]
        hw = bez_width(t) * S
        top.append((x - ty * hw, y + tx * hw))
        bot.append((x + ty * hw, y - tx * hw))
    return spine, tangents, top, bot, p0, p3


def sky_gradient(w, h):
    img = Image.new("RGB", (w, h))
    px = img.load()
    top, mid, horizon = (5, 7, 22), (13, 28, 56), (24, 88, 90)
    for y in range(h):
        t = y / (h - 1)
        c = mix(top, mid, t / 0.62) if t < 0.62 else mix(mid, horizon, (t - 0.62) / 0.38)
        for x in range(w):
            px[x, y] = c
    return img


def draw_stars(w, h, horizon_y):
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(560):
        x = RND.uniform(0, w); y = RND.uniform(0, horizon_y * 0.97)
        r = RND.uniform(0.6, 2.2)
        bright = RND.uniform(0.25, 1.0) * (1.0 - 0.55 * y / horizon_y)
        if RND.random() < 0.06:
            r *= 1.8; bright = min(1.0, bright + 0.35)
        a = int(255 * max(0.05, bright))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(230, 240, 255, a))
    return layer


def draw_moon(w, h):
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    mx, my, mr = w * 0.80, h * 0.15, w * 0.042
    for i in range(14):
        rr = mr + i * mr * 0.5
        a = int(26 * (1 - i / 14) ** 2)
        d.ellipse([mx - rr, my - rr, mx + rr, my + rr], fill=(180, 210, 235, a))
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(238, 244, 252, 255))
    for cx, cy, cr in [(-0.3, -0.2, 0.22), (0.25, 0.1, 0.16), (-0.05, 0.35, 0.12)]:
        cxx, cyy = mx + cx * mr, my + cy * mr
        d.ellipse([cxx - cr * mr, cyy - cr * mr, cxx + cr * mr, cyy + cr * mr],
                  fill=(208, 218, 230, 255))
    return layer.filter(ImageFilter.GaussianBlur(SS))


def aurora_ribbons(w, h, horizon_y):
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    palettes = [
        [(60, 255, 170), (120, 255, 200), (40, 200, 230)],
        [(150, 90, 255), (90, 130, 255), (200, 120, 255)],
    ]
    for pi, colors in enumerate(palettes):
        base_y = horizon_y * (0.40 if pi == 0 else 0.24)
        amp = h * (0.10 if pi == 0 else 0.07)
        freq = RND.uniform(1.6, 2.4)
        phase = RND.uniform(0, 6.28)
        tilt = -0.10 if pi == 0 else -0.04
        for s in range(46):
            t = s / 46
            col = colors[s % len(colors)]
            alpha = int(30 * math.sin(t * math.pi) + 8)
            offset = t * h * 0.16
            pts = []
            for x in range(0, w + 12, 12):
                y = (base_y + offset + tilt * x
                     + amp * math.sin(phase + x / w * freq * 2 * math.pi)
                     + amp * 0.4 * math.sin(phase * 1.7 + x / w * 5.1))
                pts.append((x, y))
            d.line(pts, fill=col + (alpha,), width=int((26 - 20 * t) * SS),
                   joint="curve")
    return layer.filter(ImageFilter.GaussianBlur(10 * SS))


def whale(w, h, horizon_y):
    """Luminous whale: smooth gradient body, dark belly, grooves, eye,
    downward-flicking fluke, sweeping pectoral fin."""
    S = w / 1024.0
    spine, tangents, top, bot, p0, p3 = body_geometry(w, h)
    N = len(spine) - 1

    body = Image.new("L", (w, h), 0)
    bd = ImageDraw.Draw(body)
    bd.polygon(top + bot[::-1], fill=255)
    r0 = bez_width(0.0) * S
    bd.ellipse([p0[0] - r0, p0[1] - r0, p0[0] + r0, p0[1] + r0], fill=255)

    # fluke: two curved lobes (tapered bezier strokes) flicking down-right,
    # grown from the tail tip so they stay attached
    tx, ty = tangents[-1]
    nx, ny = -ty, tx
    ex, ey = spine[-1]
    c, s_ = math.cos(math.radians(30)), math.sin(math.radians(30))
    dx = tx * c - ty * s_; dy = tx * s_ + ty * c
    ext, spread = 160 * S, 110 * S
    stemx, stemy = ex + dx * ext * 0.10, ey + dy * ext * 0.10
    for sign in (1, -1):
        lobe_end = (stemx + dx * ext * 0.90 + nx * spread * sign,
                    stemy + dy * ext * 0.90 + ny * spread * sign)
        bend = (stemx + dx * ext * 0.60 + nx * spread * 1.05 * sign,
                stemy + dy * ext * 0.60 + ny * spread * 1.05 * sign)
        lobe = [bezier((stemx, stemy), bend,
                       (lobe_end[0] - dx * 20 * S, lobe_end[1] - dy * 20 * S),
                       lobe_end, i / 40) for i in range(41)]
        lw_ = [26 * S, 48 * S, 34 * S, 8 * S]
        lobe_poly = []
        for i in range(41):
            t = i / 40
            hw = (lw_[0] * (1 - t) ** 3 + 3 * (1 - t) ** 2 * t * lw_[1]
                  + 3 * (1 - t) * t**2 * lw_[2] + t**3 * lw_[3])
            tx2 = lobe[min(40, i + 1)][0] - lobe[max(0, i - 1)][0]
            ty2 = lobe[min(40, i + 1)][1] - lobe[max(0, i - 1)][1]
            n2 = math.hypot(tx2, ty2) or 1
            lobe_poly.append((lobe[i][0] - ty2 / n2 * hw, lobe[i][1] + tx2 / n2 * hw))
        for i in range(40, -1, -1):
            t = i / 40
            hw = ((lw_[0] * (1 - t) ** 3 + 3 * (1 - t) ** 2 * t * lw_[1]
                   + 3 * (1 - t) * t**2 * lw_[2] + t**3 * lw_[3]) * 0.25)
            tx2 = lobe[min(40, i + 1)][0] - lobe[max(0, i - 1)][0]
            ty2 = lobe[min(40, i + 1)][1] - lobe[max(0, i - 1)][1]
            n2 = math.hypot(tx2, ty2) or 1
            lobe_poly.append((lobe[i][0] + ty2 / n2 * hw, lobe[i][1] - tx2 / n2 * hw))
        bd.polygon(lobe_poly, fill=255)

    # small dorsal fin bump on the back
    di = 0.55
    dxp, dyp = spine[int(di * N)]
    dtx, dty = tangents[int(di * N)]
    dnx, dny = -dty, dtx
    hw_d = bez_width(di) * S
    bd.polygon([(dxp + dtx * 16 * S - dnx * hw_d * 0.96, dyp + dty * 16 * S - dny * hw_d * 0.96),
                (dxp - dnx * (hw_d + 42 * S), dyp - dny * (hw_d + 42 * S)),
                (dxp - dtx * 30 * S - dnx * hw_d * 0.9, dyp - dty * 30 * S - dny * hw_d * 0.9)],
               fill=255)

    # pectoral fin: long curved sweep from the lower body, trailing back
    fi = 0.28
    fx, fy = spine[int(fi * N)]
    ftx, fty = tangents[int(fi * N)]
    fnx, fny = -fty, ftx
    fp0 = (fx + fnx * bez_width(fi) * S * 0.8, fy + fny * bez_width(fi) * S * 0.8)
    fp1 = (fp0[0] + fnx * 70 * S + ftx * 110 * S, fp0[1] + fny * 70 * S + fty * 110 * S)
    fp2 = (fp0[0] + fnx * 110 * S + ftx * 240 * S, fp0[1] + fny * 110 * S + fty * 240 * S)
    fp3 = (fp0[0] + fnx * 30 * S + ftx * 380 * S, fp0[1] + fny * 30 * S + fty * 380 * S)
    finc = [bezier(fp0, fp1, fp2, fp3, i / 40) for i in range(41)]
    fw = [10 * S, 26 * S, 18 * S, 6 * S]
    fin_poly = []
    for i in range(41):
        t = i / 40
        hw = (fw[0] * (1 - t) ** 3 + 3 * (1 - t) ** 2 * t * fw[1]
              + 3 * (1 - t) * t**2 * fw[2] + t**3 * fw[3])
        tx2 = finc[min(40, i + 1)][0] - finc[max(0, i - 1)][0]
        ty2 = finc[min(40, i + 1)][1] - finc[max(0, i - 1)][1]
        n2 = math.hypot(tx2, ty2) or 1
        fin_poly.append((finc[i][0] - ty2 / n2 * hw, finc[i][1] + tx2 / n2 * hw))
    for i in range(40, -1, -1):
        t = i / 40
        hw = ((fw[0] * (1 - t) ** 3 + 3 * (1 - t) ** 2 * t * fw[1]
               + 3 * (1 - t) * t**2 * fw[2] + t**3 * fw[3]) * 0.3)
        tx2 = finc[min(40, i + 1)][0] - finc[max(0, i - 1)][0]
        ty2 = finc[min(40, i + 1)][1] - finc[max(0, i - 1)][1]
        n2 = math.hypot(tx2, ty2) or 1
        fin_poly.append((finc[i][0] + ty2 / n2 * hw, finc[i][1] - tx2 / n2 * hw))
    bd.polygon(fin_poly, fill=255)

    # ---- smooth gradient fill: painted at low res along the spine,
    # blurred, upscaled, masked by the body ----
    low = 200
    g = Image.new("RGB", (low, low), (18, 90, 150))
    gd = ImageDraw.Draw(g)
    sc = low / w
    for i in range(0, N + 1, 1):
        t = i / N
        x, y = spine[i]
        tx, ty = tangents[i]
        hw = bez_width(t) * S
        # 0 = back/top edge (hot, glowing) -> 1 = belly (deep teal)
        # flicker of light pulses running along the body
        pulse = 0.5 + 0.5 * math.sin(t * 21 - 1.2)
        hot = mix((255, 250, 235), (90, 200, 255), pulse * 0.45)
        col_back = mix(hot, (30, 110, 185), min(1.0, t * 1.15 + 0.1))
        col_belly = mix((60, 160, 235), (12, 55, 100), 0.65)
        # back stroke (slightly outside the spine, on the top side)
        gd.line([(x * sc - ty * hw * sc, y * sc + tx * hw * sc),
                 (x * sc, y * sc)], fill=col_back, width=3)
        # belly stroke (bottom side)
        gd.line([(x * sc, y * sc),
                 (x * sc + ty * hw * sc, y * sc - tx * hw * sc)],
                fill=col_belly, width=3)
    hx, hy = spine[int(0.06 * N)]
    gd.ellipse([hx * sc - 14, hy * sc - 14, hx * sc + 14, hy * sc + 14],
               fill=(255, 255, 245))
    g = g.filter(ImageFilter.GaussianBlur(6))
    grad = g.resize((w, h), Image.BILINEAR)
    fill = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fill.paste(grad, mask=body)

    # throat grooves: dark curved lines along the belly of the front half
    grooves = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gdr = ImageDraw.Draw(grooves)
    for k in range(1, 5):
        off = 0.45 + 0.11 * k
        pts = []
        for i in range(int(0.03 * N), int(0.48 * N), 4):
            t = i / N
            x, y = spine[i]
            tx, ty = tangents[i]
            hw = bez_width(t) * S
            pts.append((x - ty * hw * off, y + tx * hw * off))
        gdr.line(pts, fill=(8, 40, 75, 140), width=max(1, int(2.0 * S)))
    grooves = grooves.filter(ImageFilter.GaussianBlur(1.5 * SS))

    # eye: set back on the head, upper side, clear of the splash
    eye = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ed = ImageDraw.Draw(eye)
    ei = 0.14
    ex_, ey_ = spine[int(ei * N)]
    etx, ety = tangents[int(ei * N)]
    er = 8 * S
    ecx = ex_ - ety * bez_width(ei) * S * 0.30
    ecy = ey_ + etx * bez_width(ei) * S * 0.30
    ed.ellipse([ecx - er, ecy - er, ecx + er, ecy + er], fill=(8, 30, 55, 255))
    ed.ellipse([ecx - er * 0.45, ecy - er * 0.45, ecx + er * 0.15, ecy + er * 0.15],
               fill=(220, 245, 255, 255))
    mpts = []
    for i in range(0, int(0.20 * N), 3):
        t = i / N
        x, y = spine[i]
        tx, ty = tangents[i]
        hw = bez_width(t) * S * 0.72
        mpts.append((x - ty * hw, y + tx * hw))
    ed.line(mpts, fill=(10, 40, 70, 190), width=max(1, int(2.5 * S)))

    # outer rim light
    edge = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    edge.paste((150, 240, 255, 210), mask=body)
    edge = edge.filter(ImageFilter.GaussianBlur(4.0 * SS))

    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer = Image.alpha_composite(layer, edge)
    layer = Image.alpha_composite(layer, fill)
    layer = Image.alpha_composite(layer, grooves)
    layer = Image.alpha_composite(layer, eye)
    return layer


def splash(w, h, horizon_y):
    """Luminous splash crown where the nose tears the water."""
    S = w / 1024.0
    nx0, ny0 = P0[0] * w, P0[1] * h

    sheets = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheets)
    for k in range(9):
        a0 = math.radians(200 + k * 18 + RND.uniform(-6, 6))
        ln = RND.uniform(140, 300) * S
        bend = RND.uniform(-0.5, 0.9)
        pts = []
        for i in range(26):
            t = i / 25
            r = t * ln
            a = a0 + bend * t
            pts.append((nx0 + r * math.cos(a), ny0 + r * math.sin(a)))
        sd.line(pts, fill=(200, 245, 255, int(120 * math.sin((k + 1) / 10 * math.pi) + 40)),
                width=max(1, int((9 - 6 * (k / 9)) * S)), joint="curve")
    sheets = sheets.filter(ImageFilter.GaussianBlur(1.6 * SS))

    drops = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(drops)
    for _ in range(900):
        a = RND.uniform(math.radians(190), math.radians(345))
        rr = (RND.uniform(0, 1) ** 0.7) * 240 * S
        x = nx0 + rr * math.cos(a); y = ny0 + rr * math.sin(a) * 0.92
        if y > horizon_y * 0.99 or x < 0 or x > w or y < 0:
            continue
        r = RND.uniform(1.0, 3.6) * S
        col = mix((140, 225, 255), (255, 255, 255), RND.random() ** 1.5)
        al = int(220 * (1 - rr / (260 * S)) ** 1.2 + 15)
        dd.ellipse([x - r, y - r, x + r, y + r], fill=col + (min(255, al),))
    drops = drops.filter(ImageFilter.GaussianBlur(0.7 * SS))

    core = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(core)
    for i in range(8):
        r = (30 + i * 22) * S
        a = int(70 * (1 - i / 8) ** 1.6)
        cd.ellipse([nx0 - r, ny0 - r * 0.8, nx0 + r, ny0 + r * 0.8],
                   fill=(190, 240, 255, a))
    core = core.filter(ImageFilter.GaussianBlur(6 * SS))

    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer = Image.alpha_composite(layer, core)
    layer = Image.alpha_composite(layer, sheets)
    layer = Image.alpha_composite(layer, drops)
    return layer


def ocean(w, h, horizon_y):
    """Dark sea with shimmering dash reflections (no banding)."""
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle([0, horizon_y, w, h], fill=(8, 16, 30, 255))
    S = w / 1024.0

    def shimmer(cx, color, spread, density, fade):
        y = horizon_y + 4
        while y < h - 2:
            depth = (y - horizon_y) / (h - horizon_y)
            n = max(1, int(density * (0.4 + depth)))
            for _ in range(n):
                lx = RND.gauss(cx, spread * (0.5 + depth))
                ln = RND.uniform(6, 42) * S * (0.5 + depth)
                al = int(fade * (1 - depth) ** 1.4 * RND.uniform(0.3, 1.0))
                if al > 6:
                    d.line([(lx - ln, y), (lx + ln, y)],
                           fill=color + (al,), width=max(1, int(1.6 * S)))
            y += RND.uniform(3, 9) * S

    # reflected whale glow
    shimmer(P0[0] * w * 0.7 + w * 0.18, (90, 220, 255), w * 0.10, 5, 90)
    # moon glitter path
    shimmer(w * 0.80, (215, 232, 248), w * 0.025, 3, 70)
    layer = layer.filter(ImageFilter.GaussianBlur(0.6 * SS))
    return layer


def vignette(img):
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([-w * 0.18, -h * 0.18, w * 1.18, h * 1.18], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(120 * SS))
    dark = Image.new("RGB", (w, h), (2, 4, 10))
    return Image.composite(img, dark, mask)


def main():
    w = h = SIZE * SS
    horizon_y = int(h * 0.74)

    img = sky_gradient(w, h).convert("RGBA")
    img = Image.alpha_composite(img, draw_stars(w, h, horizon_y))
    img = Image.alpha_composite(img, aurora_ribbons(w, h, horizon_y))
    img = Image.alpha_composite(img, draw_moon(w, h))
    img = Image.alpha_composite(img, ocean(w, h, horizon_y))
    img = Image.alpha_composite(img, whale(w, h, horizon_y))
    img = Image.alpha_composite(img, splash(w, h, horizon_y))

    img = img.convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
    img = vignette(img)

    os.makedirs("/output", exist_ok=True)
    out = "/output/entry.png"
    img.save(out, "PNG", optimize=True)
    try:
        repo = os.path.dirname(os.path.abspath(__file__))
        img.save(os.path.join(repo, "preview.png"), "PNG", optimize=True)
    except OSError:
        pass
    print("wrote", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
