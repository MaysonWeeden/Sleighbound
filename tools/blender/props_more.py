"""Sleighbound winter kit 2: sweets, decorations, street props, snow and nature, toys.

Run headless (same look and rules as build_props.py):
  blender -b --factory-startup --python tools/blender/props_more.py
"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix, noise
import build_props as bp
from build_props import P, colour, box, ico, join, mesh_obj, ramp, lc

P.update({
    "brown": "#B8733A", "brown_light": "#D08A4A", "brown_dark": "#8E5527",
    "cocoa": "#5A3220", "orange": "#FF8A2A", "coal": "#2A2A33",
    "blue": "#3C8DFF", "blue_dark": "#2A63C8", "green": "#3CC46B", "green_dark": "#24934C",
    "glow": "#FFE38A", "iron": "#3B3F4A", "wood": "#A0663A", "wood_dark": "#7A4A28", "wood_light": "#D9A86E",
    "cream": "#FFF1DC", "ice": "#9FE3F7", "ice_light": "#DDF8FF", "holly": "#1F6B3F", "holly_light": "#2E8A55",
    "berry": "#D81E3A", "lantern_red": "#C8283E",
})


# ---------------------------------------------------------------- helpers
def rot(axis, deg):
    return Matrix.Rotation(math.radians(deg), 3, axis)


def xf(ob, R=None, loc=(0, 0, 0), scale=1.0):
    R = R or Matrix.Identity(3); L = Vector(loc)
    return lc.deform(ob, lambda p: R @ (p * scale) + L)


def cyl(name, r, h, steps=8, r2=None, z0=0.0):
    return lc.lathe(name, [(r, z0), (r if r2 is None else r2, z0 + h)], steps=steps, cls="medium")


def ball(name, r, c, subdiv=2, amp=0.0, seed=0):
    return ico(name, r, c, subdiv=subdiv, amp=amp, seed=seed)


def ring(name, R, tube, c, plane="XZ", segs=16, prof=6):
    pts = []
    for n in range(segs):
        a = 2 * math.pi * n / segs
        ca, sa = R * math.cos(a), R * math.sin(a)
        pts.append({"XZ": (c[0] + ca, c[1], c[2] + sa), "XY": (c[0] + ca, c[1] + sa, c[2]),
                    "YZ": (c[0], c[1] + ca, c[2] + sa)}[plane])
    up = {"XZ": (0, 1, 0), "XY": (0, 0, 1), "YZ": (1, 0, 0)}[plane]
    return lc.sweep(name, pts, profile=lc.circle(prof), radius=tube, closed=True, up=up, segments=segs, cls="medium")


def stripes(segments, n=8, a=None, b=None, pattern=(0, 1, 4, 5)):
    a, b = a or P["red"], b or P["white"]
    side = segments * n

    def fn(i):
        if i.index >= side:
            return b
        return a if int(i.uv.x * n + 1e-6) % n in pattern else b
    return fn


def rod(name, p0, p1, r, pitch, a=None, b=None, segs=None):
    """Straight candy-striped rod from p0 to p1."""
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    segs = segs or max(6, int(L / pitch * 8))
    d = (p1 - p0).normalized()
    up = (0, 1, 0) if abs(d.z) > 0.9 else (0, 0, 1)
    ob = lc.sweep(name, [p0, p1], profile=lc.circle(8), radius=r, twist=(0, L / pitch * 360), up=up,
                  segments=segs, cls="medium")
    return colour(ob, stripes(segs, a=a, b=b))


def mirror_x(ob, name, x0=0.0):
    c = ob.copy(); c.data = ob.data.copy(); c.name = name
    bpy.context.scene.collection.objects.link(c)
    return lc.deform(c, lambda p: Vector((2 * x0 - p.x, p.y, p.z)))


def bow(name, s, c, color, tails=True):
    """Ribbon bow in the XZ plane at c: two loops, a knot and two tails."""
    X, Y, Z = c
    rx, rz, tube, tilt = 0.32 * s, 0.2 * s, 0.075 * s, math.radians(28)
    cx, cz = rx * 0.95, rz * 0.45
    pts = []
    for n in range(16):
        a = 2 * math.pi * n / 16
        x, z = rx * math.cos(a), rz * math.sin(a)
        pts.append((X + cx + x * math.cos(tilt) - z * math.sin(tilt), Y, Z + cz + x * math.sin(tilt) + z * math.cos(tilt)))
    right = colour(lc.sweep(name + "_R", pts, profile=lc.circle(6), radius=tube, closed=True, up=(0, 1, 0),
                            segments=12, cls="small"), color)
    k = 0.26 * s
    parts = [right, mirror_x(right, name + "_L", X), colour(box(name + "_knot", (k, k * 0.9, k * 0.8), (X, Y, Z), 0.03), color)]
    if tails:
        for side in (1, -1):
            t = box(f"{name}_tail{side}", (0.12 * s, 0.06 * s, 0.42 * s), (0, 0, -0.21 * s), 0.0)
            xf(t, rot("Y", 25 * side), (X + 0.06 * s * side, Y, Z - 0.05 * s))
            parts.append(colour(t, color))
    return parts


def snow_cap(name, size, c, seed=0):
    """Lumpy flattened snow blob."""
    ob = ico(name, 1.0, (0, 0, 0), subdiv=2, amp=0.12, seed=seed)
    xf(ob, None, c)
    lc.deform(ob, lambda p: Vector((c[0] + (p.x - c[0]) * size[0], c[1] + (p.y - c[1]) * size[1], c[2] + (p.z - c[2]) * size[2])))
    return colour(ob, lambda i: P["snow"] if i.normal.z > -0.2 else P["snow_shade"])


def sphere_lathe(name, R, z0=0.0, rings=9, steps=14):
    prof = [(R * math.sin(math.pi * k / (rings - 1)), z0 + R - R * math.cos(math.pi * k / (rings - 1))) for k in range(rings)]
    prof[0] = (0, prof[0][1]); prof[-1] = (0, prof[-1][1])
    return lc.lathe(name, prof, steps=steps, cls="medium")


def star_slab(name, R, depth, col, col_side):
    pts = []
    for k, ang in enumerate((90, 54, 18, -18, -54, -90)):
        r = R if k % 2 == 0 else R * 0.45
        pts.append((r * math.cos(math.radians(ang)), r * math.sin(math.radians(ang))))
    ob = lc.extrude_outline(name, lc.mirror_outline(pts), depth, bevel=0.12 * R, bevel_segs=1, cls="small")
    colour(ob, lambda i: col if abs(i.normal.z) > 0.9 else col_side)
    return xf(ob, rot("X", 90))                    # stands up, faces -Y


def tint(c, t):
    return ramp(c, "#FFFFFF", t)


# ---------------------------------------------------------------- sweets
def lollipop(name, a, b, R=1.3):
    t = 0.28 * R
    rs = (0.15, 0.3, 0.45, 0.6, 0.75, 0.88)
    face = [(r * R, -t * (1 - 0.35 * max(0, r - 0.6) / 0.28)) for r in rs]
    prof = [(0, -t)] + face + [(0.97 * R, -t * 0.45), (R, 0), (0.97 * R, t * 0.45)] + \
           [(x, -z) for x, z in reversed(face)] + [(0, t)]
    disc = lc.lathe(name + "_disc", prof, steps=28, cls="medium")

    def fn(i):
        c = i.center
        if abs(i.normal.z) < 0.6:
            return a
        rr = math.hypot(c.x, c.y) / R
        ang = math.atan2(c.y, c.x) / (2 * math.pi)
        return a if int(math.floor(ang * 3 + rr * 2.0 + 10)) % 2 == 0 else b
    colour(disc, fn)
    stick_h = 2.6 * R
    xf(disc, rot("X", 90), (0, 0, stick_h + R * 0.95))
    stick = colour(cyl(name + "_stick", 0.1 * R, stick_h + R * 0.4, steps=6), P["white"])
    return join(name, [disc, stick]), "small", None


def peppermint(name, R=1.5):
    t = 0.3 * R
    prof = [(0, 0), (0.3 * R, 0), (0.65 * R, 0.02 * R), (0.92 * R, t * 0.25), (R, t), (0.92 * R, 2 * t - t * 0.25),
            (0.65 * R, 2 * t - 0.02 * R), (0.3 * R, 2 * t), (0, 2 * t)]
    ob = lc.lathe(name, prof, steps=24, cls="medium")

    def fn(i):
        c = i.center
        rr = math.hypot(c.x, c.y) / R
        if abs(i.normal.z) < 0.5 or rr < 0.2:
            return P["white"]
        ang = math.atan2(c.y, c.x) / (2 * math.pi) + 0.5
        return P["red"] if int(ang * 8 + rr * 0.6) % 2 == 0 else P["white"]
    return colour(ob, fn), "small", None


def gumdrop(name, col, seed):
    ob = lc.lathe(name, [(0, 0), (1.0, 0), (1.03, 0.2), (0.92, 0.7), (0.62, 1.05), (0, 1.16)], steps=12, cls="small")
    off = Vector((seed, seed * 2, 0))
    colour(ob, lambda i: tint(col, 0.35) if noise.noise(i.center * 3 + off) > 0.3 else col)
    return xf(ob, None, (0, 0, 0), 1.2), "small", None


def gingerbread(name):
    half = [(0, 3.1), (0.35, 3.05), (0.58, 2.85), (0.62, 2.55), (0.5, 2.25), (0.32, 2.1), (0.95, 1.95), (1.2, 1.8),
            (1.22, 1.55), (1.0, 1.45), (0.6, 1.55), (0.62, 0.9), (0.85, 0.2), (0.85, 0.0), (0.45, 0.0),
            (0.3, 0.6), (0, 0.75)]
    body = lc.extrude_outline(name + "_body", lc.mirror_outline(half), 0.4, bevel=0.1, cls="small")
    colour(body, lambda i: P["brown_light"] if abs(i.normal.z) > 0.9 else P["brown_dark"])
    parts = [body]
    for n, (y, c) in enumerate(((1.85, P["red"]), (1.5, P["green"]), (1.15, P["red"]))):
        parts.append(colour(ball(f"{name}_btn{n}", 0.13, (0, y, 0.2), subdiv=1), c))
    for sx in (-1, 1):
        parts.append(colour(ball(f"{name}_eye{sx}", 0.09, (0.2 * sx, 2.68, 0.2), subdiv=1), P["white"]))
        for n, y in enumerate((1.62, 1.72)):           # icing zigzags on the wrists
            parts.append(colour(box(f"{name}_ice{sx}{n}", (0.06, 0.32, 0.05), (1.02 * sx, y, 0.21), 0.0), P["white"]))
    smile = [(0.2 * math.cos(math.radians(a)), 2.48 + 0.12 * math.sin(math.radians(a)), 0.21) for a in range(200, 341, 20)]
    parts.append(colour(lc.sweep(name + "_smile", smile, profile=lc.circle(5), radius=0.04, segments=7, cls="tiny"),
                        P["white"]))
    ob = join(name, parts)
    return xf(ob, rot("X", 90), (0, 0, 0), 1.3), "small", None


def cookie(name, icing, seed):
    rnd = random.Random(seed)
    base = colour(lc.lathe(name + "_base", [(0, 0), (0.95, 0), (1.0, 0.12), (0.95, 0.3), (0, 0.32)], steps=14, cls="small"),
                  lambda i: P["brown_light"] if i.normal.z > 0.5 else P["brown"])
    top = colour(lc.lathe(name + "_icing", [(0, 0.28), (0.82, 0.28), (0.86, 0.36), (0, 0.42)], steps=14, cls="small"), icing)
    parts = [base, top]
    for n in range(7):
        a, r = rnd.uniform(0, 2 * math.pi), rnd.uniform(0.1, 0.65)
        sp = box(f"{name}_spr{n}", (0.2, 0.06, 0.06), (0, 0, 0), 0.0)
        xf(sp, rot("Z", rnd.uniform(0, 180)), (r * math.cos(a), r * math.sin(a), 0.42 - 0.07 * r / 0.86))
        parts.append(colour(sp, (P["red"], P["green"], P["gold"], P["blue"])[n % 4]))
    ob = join(name, parts)
    return xf(ob, None, (0, 0, 0), 1.6), "small", None


def hot_cocoa(name):
    mug = lc.lathe(name + "_mug", [(0, 0), (0.78, 0), (0.85, 0.1), (0.86, 0.6), (0.86, 0.8), (0.86, 1.45), (0.8, 1.55),
                                   (0.72, 1.5), (0.7, 1.38), (0, 1.38)], steps=14, cls="small")

    def fn(i):
        c = i.center
        if c.z > 1.36 and i.normal.z > 0.8 and math.hypot(c.x, c.y) < 0.71:
            return P["cocoa"]
        if 0.6 < c.z < 0.8:
            return P["white"]
        return P["red"]
    parts = [colour(mug, fn), colour(ring(name + "_handle", 0.36, 0.11, (0.92, 0, 0.8), "XZ", 14, 6), P["red"])]
    for n, (x, y, a) in enumerate(((0.2, 0.12, 20), (-0.25, 0.18, -15), (0.02, -0.28, 40))):
        m = box(f"{name}_mallow{n}", (0.28, 0.28, 0.24), (0, 0, 0), 0.04)
        parts.append(colour(xf(m, rot("Z", a), (x, y, 1.42)), P["white"]))
    ob = join(name, parts)
    return xf(ob, None, (0, 0, 0), 1.5), "small", None


# ---------------------------------------------------------------- decorations
def ornament(name, col, accent, R):
    b = sphere_lathe(name + "_ball", R)
    colour(b, lambda i: accent if abs(i.center.z - R) < 0.17 * R else (tint(col, 0.25) if i.normal.z > 0.7 else col))
    cap_h = 0.28 * R
    cap = colour(cyl(name + "_cap", 0.26 * R, cap_h, steps=10, z0=2 * R - 0.1 * R), P["gold"])
    top = 2 * R - 0.1 * R + cap_h
    loop = colour(ring(name + "_loop", 0.14 * R, 0.045 * R, (0, 0, top + 0.1 * R), "XZ", 10, 5), P["gold"])
    cls = "medium" if R > 1.5 else "small"
    return join(name, [b, cap, loop]), cls, None


def star_topper(name, R=1.6):
    star = star_slab(name + "_star", R, 0.5, P["gold"], P["gold_dark"])
    xf(star, None, (0, 0, 1.0 + 0.45 * R - 0.15))
    pole = colour(cyl(name + "_pole", 0.12, 1.1, steps=6, z0=0.15), P["gold_dark"])
    base = colour(lc.lathe(name + "_base", [(0.6, 0), (0.6, 0.12), (0.4, 0.22), (0, 0.24)], steps=10, cls="small"), P["gold_dark"])
    return join(name, [star, pole, base]), "small", None


def bell(name):
    body = lc.lathe(name + "_bell", [(0, 0.25), (0.95, 0.0), (1.05, 0.12), (0.82, 0.4), (0.62, 0.9), (0.56, 1.35),
                                     (0.44, 1.62), (0, 1.7)], steps=14, cls="small")
    colour(body, lambda i: P["gold_dark"] if i.center.z < 0.2 or i.normal.z < -0.5 else P["gold"])
    clap = colour(ball(name + "_clapper", 0.2, (0, 0, 0.1), subdiv=1), P["gold_dark"])
    parts = [body, clap] + bow(name + "_bow", 1.6, (0, 0, 1.78), P["red"], tails=False)
    ob = join(name, parts)
    return xf(ob, None, (0, 0, 0), 1.5), "small", None


def wreath(name):
    R, tube = 1.25, 0.42
    cz = R + tube
    t = ring(name + "_ring", R, tube, (0, 0, cz), "XZ", 20, 8)

    def bump(p):
        a = math.atan2(p.z - cz, p.x)
        c = Vector((R * math.cos(a), 0, cz + R * math.sin(a)))
        d = (p - c)
        return p + d.normalized() * 0.1 * noise.noise(p * 2.2) if d.length > 1e-6 else p
    lc.deform(t, bump)
    colour(t, lambda i: P["snow"] if (i.normal.z > 0.7 and noise.noise(i.center * 3) > 0.25)
           else (P["holly_light"] if noise.noise(i.center * 2.5 + Vector((5, 1, 0))) > 0 else P["holly"]))
    parts = [t]
    for n in range(9):
        a = 2 * math.pi * n / 9 + 0.3
        parts.append(colour(ball(f"{name}_berry{n}", 0.13, (R * math.cos(a), -tube * 0.95, cz + R * math.sin(a)), subdiv=1),
                            P["berry"]))
    parts += bow(name + "_bow", 1.7, (0, -tube * 0.95, cz - R), P["red"])
    return join(name, parts), "medium", None


def stocking(name):
    outline = [(0, 3.2), (0, 0.8), (0.25, 0.25), (0.8, 0.0), (1.8, 0.0), (2.15, 0.3), (2.1, 0.7), (1.7, 0.95),
               (1.2, 1.1), (1.2, 3.2)]
    sock = lc.extrude_outline(name + "_sock", outline, 0.7, bevel=0.15, cls="small")

    colour(sock, lambda i: P["red"] if abs(i.normal.z) > 0.9 else P["red_dark"])
    cuff = colour(box(name + "_cuff", (1.55, 0.75, 0.95), (0.6, 3.05, 0), 0.1), P["white"])
    band = colour(box(name + "_band", (1.36, 0.32, 0.82), (0.6, 1.85, 0), 0.04), P["green"])
    hook = colour(ring(name + "_hook", 0.18, 0.05, (0.15, 3.5, 0), "XY", 10, 5), P["gold"])
    ob = join(name, [sock, cuff, band, hook])
    return xf(ob, rot("X", 90), (-1.07, 0, 0), 1.2), "small", None


def candle(name):
    holder = colour(lc.lathe(name + "_holder", [(0, 0), (0.75, 0), (0.8, 0.12), (0.45, 0.2), (0.42, 0.32), (0, 0.32)],
                             steps=12, cls="small"), P["gold"])
    wax = colour(lc.lathe(name + "_wax", [(0.33, 0.28), (0.33, 1.2), (0.33, 1.85), (0.28, 2.0), (0, 2.02)], steps=10,
                          cls="small"), lambda i: P["white"] if i.center.z > 1.8 else P["red"])
    wick = colour(cyl(name + "_wick", 0.03, 0.15, steps=4, z0=1.98), P["coal"])
    flame = colour(lc.lathe(name + "_flame", [(0, 2.1), (0.12, 2.2), (0.14, 2.34), (0.07, 2.52), (0, 2.68)], steps=8,
                            cls="tiny"), lambda i: P["orange"] if i.center.z < 2.3 else P["glow"])
    ob = join(name, [holder, wax, wick, flame])
    return xf(ob, None, (0, 0, 0), 1.3), "small", None


def decorated_tree(name):
    rnd = random.Random(41)
    cols = (P["red"], P["gold"], P["blue"], P["purple"])

    def extra(tiers):
        parts = []
        for t, (zb, r, th) in enumerate(tiers):
            n = 7 - t
            for k in range(n):
                a = 2 * math.pi * k / n + rnd.uniform(0, 0.5)
                c = (0.9 * r * math.cos(a), 0.9 * r * math.sin(a), zb - 0.05)
                parts.append(colour(ball(f"{name}_orn{t}_{k}", 0.42, c, subdiv=2), cols[(k + t) % 4]))
        zb, r, th = tiers[-1]
        star = star_slab(name + "_star", 0.8, 0.35, P["gold"], P["gold_dark"])
        parts.append(xf(star, None, (0, 0, zb + th + 0.2)))
        return parts
    return bp.pine(name, 12.0, 4, 3.6, 42, extra=extra)


def present_round(name, col, dark, ribbon):
    body = colour(cyl(name + "_body", 1.0, 1.0, steps=14), dark)
    lid = colour(cyl(name + "_lid", 1.08, 0.38, steps=14, z0=0.98), col)
    parts = [body, lid]
    for n, size in enumerate(((2.24, 0.26, 1.42), (0.26, 2.24, 1.44))):
        parts.append(colour(box(f"{name}_rib{n}", size, (0, 0, size[2] / 2), 0.03), ribbon))
    parts += bow(name + "_bow", 1.5, (0, 0, 1.55), ribbon)
    return join(name, parts), "small", None


def present_stack(name):
    specs = [((2.6, 2.6, 1.8), P["red"], P["red_dark"], P["gold"], 0, 0.0),
             ((1.9, 1.9, 1.4), P["mint"], P["mint_dark"], P["red"], 20, 1.85),
             ((1.2, 1.2, 1.0), P["purple"], P["purple_dark"], P["gold"], -15, 3.3)]
    parts = []
    for n, (size, c, d, rb, yaw, z) in enumerate(specs):
        ob, _, _ = bp.present(f"{name}_p{n}", *size, c, d, rb)
        parts.append(xf(ob, rot("Z", yaw), (0, 0, z)))
    return join(name, parts), "medium", None


# ---------------------------------------------------------------- street props
def lantern_parts(name, z0, s=1.0, handle=False):
    parts = []
    parts.append(colour(box(name + "_plate", (1.4 * s, 1.4 * s, 0.2 * s), (0, 0, z0 + 0.1 * s), 0.04 * s), P["iron"]))
    parts.append(colour(box(name + "_glass", (1.0 * s, 1.0 * s, 1.4 * s), (0, 0, z0 + 0.9 * s), 0.0), P["glow"]))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(colour(box(f"{name}_post{sx}{sy}", (0.16 * s, 0.16 * s, 1.5 * s),
                                    (0.52 * s * sx, 0.52 * s * sy, z0 + 0.92 * s), 0.02 * s), P["iron"]))
    zr = z0 + 1.65 * s
    roof = lc.lathe(name + "_roof", [(0.95 * s, zr), (0, zr + 0.8 * s)], steps=4, cls="small")
    xf(roof, rot("Z", 45))
    parts.append(colour(roof, lambda i: P["snow"] if i.center.z > zr + 0.42 * s else P["lantern_red"]))
    parts.append(colour(box(name + "_rim", (1.5 * s, 1.5 * s, 0.14 * s), (0, 0, zr), 0.03 * s), P["iron"]))
    parts.append(colour(ball(name + "_finial", 0.17 * s, (0, 0, zr + 0.85 * s), subdiv=1), P["gold"]))
    if handle:
        parts.append(colour(ring(name + "_handle", 0.32 * s, 0.06 * s, (0, 0, zr + 1.05 * s), "XZ", 12, 5), P["iron"]))
    return parts


def lamp_post(name):
    base = colour(lc.lathe(name + "_base", [(1.0, 0), (1.0, 0.4), (0.62, 0.62), (0.45, 1.3), (0, 1.32)], steps=10,
                           cls="small"), P["pine_dark"])
    pole = rod(name + "_pole", (0, 0, 1.1), (0, 0, 8.6), 0.28, 2.6)
    collar = colour(lc.lathe(name + "_collar", [(0.4, 8.4), (0.5, 8.55), (0.5, 8.75), (0, 8.8)], steps=10, cls="small"),
                    P["gold"])
    parts = [base, pole, collar] + lantern_parts(name + "_lamp", 8.75)
    return join(name, parts), "medium", None


def lantern(name):
    return join(name, lantern_parts(name, 0.0, 1.2, handle=True)), "small", None


def bench(name):
    parts = []
    for sx in (-1, 1):
        x = 2.6 * sx
        parts.append(colour(box(f"{name}_legF{sx}", (0.25, 0.25, 1.6), (x, -0.55, 0.8), 0.04), P["iron"]))
        parts.append(colour(box(f"{name}_legB{sx}", (0.25, 0.25, 3.1), (x, 0.65, 1.55), 0.04), P["iron"]))
        parts.append(colour(box(f"{name}_sup{sx}", (0.22, 1.6, 0.22), (x, 0.05, 1.45), 0.03), P["iron"]))
    for n, y in enumerate((-0.6, -0.1, 0.4)):
        parts.append(colour(box(f"{name}_seat{n}", (6.0, 0.44, 0.18), (0, y, 1.65), 0.04),
                            P["wood"] if n % 2 == 0 else P["wood_dark"]))
    for n, z in enumerate((2.3, 2.85)):
        b = box(f"{name}_back{n}", (6.0, 0.16, 0.42), (0, 0, 0), 0.04)
        parts.append(colour(xf(b, rot("X", -10), (0, 0.72, z)), P["wood"] if n else P["wood_dark"]))
    parts.append(snow_cap(name + "_snowSeat", (2.7, 0.65, 0.16), (0, -0.1, 1.76), 1))
    parts.append(snow_cap(name + "_snowBack", (2.8, 0.18, 0.12), (0, 0.74, 3.08), 2))
    return join(name, parts), "small", None


def fence_picket(name):
    parts = []
    for n, z in enumerate((1.1, 2.4)):
        parts.append(colour(box(f"{name}_rail{n}", (8.0, 0.22, 0.36), (0, 0.18, z), 0.04), P["cream"]))
    xs = [-3.45 + 1.15 * k for k in range(7)]
    for k, x in enumerate(xs):
        h = 2.9 + (0.15 if k % 2 else 0)
        parts.append(colour(box(f"{name}_pick{k}", (0.6, 0.18, h), (x, 0, h / 2), 0.04),
                            P["white"] if k % 2 else P["cream"]))
        cap = lc.lathe(f"{name}_tip{k}", [(0.42, h), (0, h + 0.42)], steps=4, cls="tiny")
        lc.deform(cap, lambda p, x=x: Vector((x + p.x * 0.72, p.y * 0.22, p.z)))
        xf(cap, None)
        parts.append(colour(cap, P["snow"]))
    parts.append(snow_cap(name + "_snow", (3.9, 0.2, 0.1), (0, 0.18, 2.62), 3))
    return join(name, parts), "small", None


def fence_candy(name):
    parts = []
    for k, x in enumerate((-4, 0, 4)):
        parts.append(rod(f"{name}_post{k}", (x, 0, 0), (x, 0, 3.4), 0.26, 1.6))
        parts.append(colour(ball(f"{name}_top{k}", 0.36, (x, 0, 3.5), subdiv=2), P["red"]))
    for n, z in enumerate((1.2, 2.45)):
        parts.append(rod(f"{name}_rail{n}", (-4, 0, z), (4, 0, z), 0.14, 2.4, a=P["mint"]))
    return join(name, parts), "medium", None


def signpost(name):
    parts = [colour(box(name + "_post", (0.4, 0.4, 6.0), (0, 0, 3.0), 0.05), P["wood_dark"])]
    arrow = [(-1.6, -0.45), (1.2, -0.45), (1.75, 0), (1.2, 0.45), (-1.6, 0.45)]
    for n, (z, col, flip, yaw) in enumerate(((4.9, P["red"], 1, 0), (3.85, P["green"], -1, 12))):
        b = lc.extrude_outline(f"{name}_board{n}", [(x * flip, y) for x, y in arrow], 0.22, bevel=0.06, cls="small")
        colour(b, lambda i, col=col: col if abs(i.normal.z) > 0.9 else P["cream"])
        xf(b, rot("X", 90))
        xf(b, rot("Z", yaw), (0.6 * flip, 0, z))
        parts.append(b)
        parts.append(snow_cap(f"{name}_bsnow{n}", (1.3, 0.13, 0.08), (0.45 * flip, 0, z + 0.47), 4 + n))
    parts.append(snow_cap(name + "_topsnow", (0.32, 0.32, 0.14), (0, 0, 6.02), 6))
    return join(name, parts), "small", None


def mailbox(name):
    outline = [(-0.6, 0), (0.6, 0)] + [(0.6 * math.cos(math.radians(a)), 0.8 + 0.6 * math.sin(math.radians(a)))
                                        for a in range(0, 181, 30)] + [(-0.6, 0.0)]
    outline = outline[:-1]
    body = lc.extrude_outline(name + "_box", outline, 1.5, bevel=0.06, cls="small")
    colour(body, P["red"])
    xf(body, Matrix(((1, 0, 0), (0, 0, 1), (0, 1, 0))), (0, 0, 3.0))    # profile in XZ, extruded along Y
    parts = [body, colour(box(name + "_post", (0.35, 0.35, 3.1), (0, 0, 1.55), 0.04), P["iron"]),
             colour(box(name + "_slot", (0.62, 0.06, 0.12), (0, -0.76, 3.95), 0.0), P["coal"]),
             colour(box(name + "_flagpole", (0.08, 0.08, 0.9), (0.66, 0.2, 3.7), 0.0), P["iron"]),
             colour(box(name + "_flag", (0.06, 0.5, 0.3), (0.66, 0.0, 4.0), 0.02), P["gold"]),
             colour(box(name + "_letter", (0.5, 0.04, 0.32), (0, -0.78, 4.1), 0.0), P["white"]),
             snow_cap(name + "_snow", (0.45, 0.65, 0.12), (0, 0, 4.4), 7)]
    return join(name, parts), "small", None


def sled(name):
    parts = []
    path = [(-1.7, 0, 0.12), (1.3, 0, 0.12)]
    for k in range(1, 9):
        a = -math.pi / 2 + math.pi * k / 8 * 0.9
        path.append((1.3 + 0.45 * math.cos(a), 0, 0.57 + 0.45 * math.sin(a)))
    for sy in (-0.75, 0.75):
        r = lc.sweep(f"{name}_runner{sy}", [(x, sy, z) for x, _, z in path], profile=lc.circle(6), radius=0.1,
                     up=(0, 1, 0), max_turn_deg=20, cls="small")
        parts.append(colour(r, P["red"]))
        for k, x in enumerate((-1.3, 0.0, 1.0)):
            parts.append(colour(box(f"{name}_strut{sy}{k}", (0.12, 0.12, 0.5), (x, sy, 0.4), 0.0), P["gold"]))
    for k, x in enumerate((-1.25, -0.55, 0.15, 0.85)):
        parts.append(colour(box(f"{name}_slat{k}", (0.58, 1.8, 0.14), (x, 0, 0.7), 0.03),
                            P["wood"] if k % 2 == 0 else P["wood_light"]))
    for sy in (-0.82, 0.82):
        parts.append(colour(box(f"{name}_side{sy}", (2.6, 0.12, 0.22), (-0.2, sy, 0.86), 0.03), P["wood_dark"]))
    return join(name, parts), "small", None


def firewood(name):
    rnd = random.Random(7)
    parts = []
    for row, (n, z) in enumerate(((3, 0.42), (2, 1.15), (1, 1.88))):
        for k in range(n):
            x = (k - (n - 1) / 2) * 0.9
            L = rnd.uniform(2.7, 3.2)
            log = lc.lathe(f"{name}_log{row}{k}", [(0.42, -L / 2), (0.44, 0), (0.42, L / 2)], steps=8, cls="small")
            xf(log, rot("Z", rnd.uniform(-6, 6)) @ rot("X", 90), (x, 0, z))
            parts.append(colour(log, lambda i: P["wood_light"] if abs(i.normal.y) > 0.8 else
                                (P["snow"] if i.normal.z > 0.75 and i.center.z > 2.0 else
                                 (P["trunk_dark"] if noise.noise(i.center * 3) > 0.2 else P["trunk"]))))
    return join(name, parts), "small", None


# ---------------------------------------------------------------- snow and nature
def snowman(name, scale=1.0, beanie=False):
    parts = []
    balls = [(1.4, 1.3), (1.0, 3.35), (0.72, 4.65)]
    for n, (r, z) in enumerate(balls):
        b = ico(f"{name}_ball{n}", r, (0, 0, z), subdiv=2, amp=0.05, seed=50 + n)
        parts.append(colour(b, lambda i: P["snow_shade"] if i.normal.z < -0.3 else P["snow"]))
    hr, hz = balls[2][0], balls[2][1]
    mr, mz = balls[1][0], balls[1][1]
    for sx in (-1, 1):
        d = Vector((0.33 * sx, -0.88, 0.25)).normalized()
        parts.append(colour(ball(f"{name}_eye{sx}", 0.09, Vector((0, 0, hz)) + d * hr * 0.96, subdiv=1), P["coal"]))
    nose = lc.lathe(name + "_nose", [(0.13, 0), (0, 0.75)], steps=6, cls="tiny")
    parts.append(colour(xf(nose, rot("X", 90), (0, -hr * 0.85, hz)), P["orange"]))
    for n, dz in enumerate((0.3, 0.0, -0.3)):
        d = Vector((0, -0.95, dz)).normalized()
        parts.append(colour(ball(f"{name}_btn{n}", 0.1, Vector((0, 0, mz)) + d * mr * 0.97, subdiv=1), P["coal"]))
    parts.append(colour(ring(name + "_scarf", 0.6, 0.17, (0, 0, mz + 0.78), "XY", 14, 6), P["red"]))
    tail = box(name + "_tail", (0.32, 0.12, 0.85), (0, 0, -0.42), 0.03)
    parts.append(colour(xf(tail, rot("X", 12), (0.3, -0.62, mz + 0.8)), P["red"]))
    for sx in (-1, 1):
        arm = lc.sweep(f"{name}_arm{sx}", [(0.85 * sx, 0, mz + 0.1), (1.7 * sx, 0, mz + 0.55), (2.2 * sx, 0, mz + 1.1)],
                       profile=lc.circle(5), radius=(0.08, 0.04), up=(0, 1, 0), segments=4, cls="tiny")
        twig = lc.sweep(f"{name}_twig{sx}", [(1.7 * sx, 0, mz + 0.55), (2.15 * sx, -0.1, mz + 0.6)],
                        profile=lc.circle(4), radius=(0.05, 0.03), up=(0, 0, 1), segments=2, cls="tiny")
        parts += [colour(arm, P["trunk"]), colour(twig, P["trunk"])]
    top = hz + hr * 0.86
    if beanie:
        hat = lc.lathe(name + "_beanie", [(0.62, top - 0.05), (0.56, top + 0.3), (0, top + 0.9)], steps=10, cls="small")
        parts += [colour(hat, P["green"]),
                  colour(ring(name + "_rim", 0.6, 0.11, (0, 0, top), "XY", 12, 5), P["white"]),
                  colour(ball(name + "_pom", 0.2, (0, 0, top + 0.95), subdiv=2), P["white"])]
    else:
        parts += [colour(cyl(name + "_brim", 0.78, 0.08, steps=12, z0=top - 0.02), P["coal"]),
                  colour(cyl(name + "_crown", 0.48, 0.8, steps=12, z0=top), P["coal"]),
                  colour(cyl(name + "_band", 0.5, 0.15, steps=12, z0=top + 0.075), P["red"])]
    ob = join(name, parts)
    return xf(ob, None, (0, 0, 0), scale), ("medium" if scale > 0.8 else "small"), None


def snow_pile(name, r, seed):
    ob = ico(name, r, (0, 0, 0), subdiv=3, scale=(1.3, 1.0, 0.38), amp=0.22, seed=seed)
    return colour(ob, lambda i: P["snow"] if i.normal.z > 0.2 else P["snow_shade"]), "rock", None


def snowball_pile(name):
    pos = [(-0.48, -0.28, 0.45), (0.48, -0.28, 0.45), (0, 0.55, 0.45), (0, 0.0, 1.18)]
    parts = [colour(ico(f"{name}_b{n}", 0.47, p, subdiv=2, amp=0.04, seed=60 + n),
                    lambda i: P["snow"] if i.normal.z > -0.2 else P["snow_shade"]) for n, p in enumerate(pos)]
    return join(name, parts), "small", None


def holly_bush(name, seed):
    rnd = random.Random(seed)
    clumps = [((0, 0, 0.9), 1.1), ((0.95, 0.3, 0.7), 0.85), ((-0.9, -0.2, 0.72), 0.8)]
    parts = []
    for n, (c, r) in enumerate(clumps):
        cl = ico(f"{name}_c{n}", r, c, subdiv=2, scale=(1, 1, 0.85), amp=0.18, seed=seed + n)
        colour(cl, lambda i: P["snow"] if i.normal.z > 0.78 else
               (P["holly_light"] if noise.noise(i.center * 2.4) > 0 else P["holly"]))
        parts.append(cl)
        for k in range(4):
            a = rnd.uniform(0, 2 * math.pi); e = rnd.uniform(0.1, 0.7)
            d = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e) * 0.85))
            base = Vector(c) + d * r * 0.95
            for j in range(3):
                off = Vector((rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12), rnd.uniform(-0.05, 0.1)))
                parts.append(colour(ball(f"{name}_b{n}{k}{j}", 0.1, base + off, subdiv=1), P["berry"]))
    return join(name, parts), "medium", None


def bare_tree(name, seed):
    rnd = random.Random(seed)
    trunk_pts = [Vector((0, 0, 0)), Vector((0.2, 0, 2.5)), Vector((0, 0.15, 5.0)), Vector((-0.25, 0, 7.2))]
    trunk = lc.sweep(name + "_trunk", trunk_pts, profile=lc.circle(7), radius=(0.6, 0.12), up=(1, 0, 0), segments=8,
                     cls="tree")
    parts = [trunk]

    def on_trunk(t):
        f = t * 3; k = min(int(f), 2); u = f - k
        return trunk_pts[k].lerp(trunk_pts[k + 1], u)
    for n in range(8):
        t = 0.3 + 0.08 * n + rnd.uniform(-0.03, 0.03)
        a = n * 2.4 + rnd.uniform(-0.3, 0.3)
        d = Vector((math.cos(a), math.sin(a), 0))
        L = 2.6 * (1.1 - t) + 0.8
        s = on_trunk(t)
        pts = [s, s + d * L * 0.5 + Vector((0, 0, 0.7)), s + d * L + Vector((0, 0, 1.7))]
        br = lc.sweep(f"{name}_br{n}", pts, profile=lc.circle(5), radius=(0.22 * (1.1 - t) + 0.05, 0), up=(0, 0, 1),
                      segments=5, cls="tree")
        parts.append(br)
        tw = pts[1] + (pts[2] - pts[1]) * 0.3
        d2 = Vector((math.cos(a + 0.9), math.sin(a + 0.9), 0))
        parts.append(lc.sweep(f"{name}_tw{n}", [tw, tw + d2 * 0.7 * L * 0.4 + Vector((0, 0, 0.6))], profile=lc.circle(4),
                              radius=(0.08, 0), up=(0, 0, 1), segments=3, cls="tree"))
    for p in parts:
        colour(p, lambda i: P["snow"] if i.normal.z > 0.55 else
               (P["trunk_dark"] if noise.noise(i.center * 1.7) > 0.15 else P["trunk"]))
    return join(name, parts), "tree", None


def ice_chunks(name, seed):
    rnd = random.Random(seed)
    parts = []
    for n, (c, r, h) in enumerate((((0, 0, 0.6), 0.75, 1.9), ((0.9, 0.3, 0.4), 0.55, 1.4), ((-0.7, 0.4, 0.35), 0.5, 1.2),
                                   ((0.2, -0.75, 0.3), 0.45, 1.0))):
        ch = ico(f"{name}_c{n}", r, (0, 0, 0), subdiv=1, scale=(1, 1, h), amp=0.25, seed=seed + n)
        xf(ch, rot("X", rnd.uniform(-14, 14)) @ rot("Y", rnd.uniform(-14, 14)), c)
        parts.append(colour(ch, lambda i: P["ice_light"] if i.normal.z > 0.5 else P["ice"]))
    return join(name, parts), "small", None


def log_snowy(name):
    log = lc.lathe(name + "_log", [(0.62, -2.0), (0.66, -0.6), (0.6, 0.8), (0.62, 2.0)], steps=9, cls="small")
    xf(log, rot("Z", 90) @ rot("X", 90), (0, 0, 0.6))
    colour(log, lambda i: P["wood_light"] if abs(i.normal.x) > 0.8 else
           (P["snow"] if i.normal.z > 0.6 else (P["trunk_dark"] if noise.noise(i.center * 2) > 0.2 else P["trunk"])))
    stub = lc.sweep(name + "_stub", [(0.6, 0, 1.0), (0.9, -0.1, 1.7)], profile=lc.circle(5), radius=(0.18, 0.1),
                    up=(0, 1, 0), segments=2, cls="tiny")
    colour(stub, lambda i: P["snow"] if i.normal.z > 0.8 else P["trunk"])
    return join(name, [log, stub]), "small", None


# ---------------------------------------------------------------- toys
def toy_drum(name):
    body = lc.lathe(name + "_body", [(0, 0.2), (1.0, 0.2), (1.0, 1.6), (0, 1.6)], steps=16, cls="small")
    zig = [(1.02 * math.cos(2 * math.pi * k / 16), 1.02 * math.sin(2 * math.pi * k / 16), 0.32 if k % 2 else 1.48)
           for k in range(16)]
    cord = lc.sweep(name + "_cord", zig, profile=lc.circle(5), radius=0.05, closed=True, up=(0, 0, 1), segments=32,
                    cls="small")
    parts = [colour(body, lambda i: P["cream"] if i.normal.z > 0.9 else P["red"]), colour(cord, P["gold"]),
             colour(cyl(name + "_rimB", 1.08, 0.24, steps=16), P["white"]),
             colour(cyl(name + "_rimT", 1.08, 0.22, steps=16, z0=1.5), P["white"])]
    for n, yaw in enumerate((20, -25)):
        st = colour(cyl(f"{name}_stick{n}", 0.06, 2.0, steps=6), P["wood_light"])
        tip = colour(ball(f"{name}_tip{n}", 0.13, (0, 0, 2.0), subdiv=1), P["red"])
        s = join(f"{name}_s{n}", [st, tip])
        parts.append(xf(s, rot("Z", yaw) @ rot("Y", 78), (-0.7 + 0.15 * n, 0.25 - 0.4 * n, 1.82)))
    return join(name, parts), "small", None


def toy_blocks(name):
    cols = [P["red"], P["blue"], P["green"], P["gold"], P["purple"], P["pink"]]

    def block(n, c, yaw, shift):
        b = box(f"{name}_b{n}", (1.2, 1.2, 1.2), (0, 0, 0), 0.1)
        perm = cols[shift:] + cols[:shift]

        def fn(i):
            v = i.normal; ax = max(range(3), key=lambda k: abs(v[k]))
            if abs(v[ax]) < 0.97:                      # chamfers: plain wood edge
                return P["cream"]
            return perm[ax * 2 + (0 if v[ax] > 0 else 1)]
        colour(b, fn)
        return xf(b, rot("Z", yaw), c)
    parts = [block(0, (-0.78, 0, 0.6), 6, 0), block(1, (0.78, 0.1, 0.6), -8, 2), block(2, (0, 0.05, 1.8), 33, 4)]
    return join(name, parts), "small", None


# ---------------------------------------------------------------- kit 2
KIT2 = [
    # sweets
    ("Lollipop_Red", "Sweets", lambda: lollipop("Lollipop_Red", P["red"], P["white"])),
    ("Lollipop_Mint", "Sweets", lambda: lollipop("Lollipop_Mint", P["mint"], P["white"], 1.0)),
    ("Lollipop_Rainbow", "Sweets", lambda: lollipop("Lollipop_Rainbow", P["purple"], P["pink"], 1.6)),
    ("Peppermint", "Sweets", lambda: peppermint("Peppermint")),
    ("Gumdrop_Red", "Sweets", lambda: gumdrop("Gumdrop_Red", P["red"], 1)),
    ("Gumdrop_Green", "Sweets", lambda: gumdrop("Gumdrop_Green", P["green"], 2)),
    ("Gumdrop_Purple", "Sweets", lambda: gumdrop("Gumdrop_Purple", P["purple"], 3)),
    ("Gingerbread_Man", "Sweets", lambda: gingerbread("Gingerbread_Man")),
    ("Cookie_Pink", "Sweets", lambda: cookie("Cookie_Pink", P["pink"], 1)),
    ("Cookie_White", "Sweets", lambda: cookie("Cookie_White", P["white"], 2)),
    ("HotCocoa", "Sweets", lambda: hot_cocoa("HotCocoa")),
    ("CandyCane_Mint", "Sweets", lambda: bp.candy_cane("CandyCane_Mint", 4.5, 0.75, 0.5, 0.27, 44, 2.2,
                                                       P["mint"], P["white"])),
    # decorations
    ("Ornament_Red", "Decor", lambda: ornament("Ornament_Red", P["red"], P["gold"], 0.75)),
    ("Ornament_Blue", "Decor", lambda: ornament("Ornament_Blue", P["blue"], P["white"], 0.75)),
    ("Ornament_Green", "Decor", lambda: ornament("Ornament_Green", P["green"], P["gold"], 0.75)),
    ("Ornament_Giant", "Decor", lambda: ornament("Ornament_Giant", P["purple"], P["gold"], 2.5)),
    ("Star_Topper", "Decor", lambda: star_topper("Star_Topper")),
    ("Bell_Gold", "Decor", lambda: bell("Bell_Gold")),
    ("Wreath", "Decor", lambda: wreath("Wreath")),
    ("Stocking", "Decor", lambda: stocking("Stocking")),
    ("Candle", "Decor", lambda: candle("Candle")),
    ("ChristmasTree_Decorated", "Decor", lambda: decorated_tree("ChristmasTree_Decorated")),
    ("Present_Round", "Decor", lambda: present_round("Present_Round", P["blue"], P["blue_dark"], P["white"])),
    ("Present_Stack", "Decor", lambda: present_stack("Present_Stack")),
    # street
    ("LampPost_Candy", "Street", lambda: lamp_post("LampPost_Candy")),
    ("Lantern", "Street", lambda: lantern("Lantern")),
    ("Bench_Snowy", "Street", lambda: bench("Bench_Snowy")),
    ("Fence_Picket", "Street", lambda: fence_picket("Fence_Picket")),
    ("Fence_CandyCane", "Street", lambda: fence_candy("Fence_CandyCane")),
    ("Signpost", "Street", lambda: signpost("Signpost")),
    ("Mailbox_Santa", "Street", lambda: mailbox("Mailbox_Santa")),
    ("Sled", "Street", lambda: sled("Sled")),
    ("Firewood_Stack", "Street", lambda: firewood("Firewood_Stack")),
    # snow and nature
    ("Snowman", "Nature", lambda: snowman("Snowman")),
    ("Snowman_Small", "Nature", lambda: snowman("Snowman_Small", 0.55, beanie=True)),
    ("SnowPile_Small", "Nature", lambda: snow_pile("SnowPile_Small", 1.4, 71)),
    ("SnowPile_Large", "Nature", lambda: snow_pile("SnowPile_Large", 3.0, 72)),
    ("Snowball_Pile", "Nature", lambda: snowball_pile("Snowball_Pile")),
    ("Bush_Holly", "Nature", lambda: holly_bush("Bush_Holly", 80)),
    ("Tree_Bare", "Nature", lambda: bare_tree("Tree_Bare", 90)),
    ("Pine_Heavy", "Nature", lambda: bp.pine("Pine_Heavy", 13.0, 4, 3.8, 14, heavy=True)),
    ("Ice_Chunks", "Nature", lambda: ice_chunks("Ice_Chunks", 100)),
    ("Log_Snowy", "Nature", lambda: log_snowy("Log_Snowy")),
    ("Rock_Tall", "Nature", lambda: bp.rock("Rock_Tall", [(1.4, (0, 0, 0), (0.9, 0.85, 1.9), 35)])),
    ("Rock_Flat", "Nature", lambda: bp.rock("Rock_Flat", [(2.4, (0, 0, 0), (1.4, 1.2, 0.4), 36)])),
    # toys
    ("Toy_Drum", "Toys", lambda: toy_drum("Toy_Drum")),
    ("Toy_Blocks", "Toys", lambda: toy_blocks("Toy_Blocks")),
]

if __name__ == "__main__":
    bp.build(KIT2, tag="Kit2")
