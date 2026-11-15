"""Sleighbound town kit: road tiles, market stalls, garage / shed, igloo, clock tower, tree plaza, ice rink and
street props (hydrant, stop sign, traffic light, bus stop, phone booth, cars, delivery van).

  blender -b --factory-startup --python tools/blender/build_town.py            (everything)
  blender -b --factory-startup --python tools/blender/build_town.py -- Igloo Car_Red

Same pipeline and style as build_buildings.py (MeshBuilder modules, gate, floating scan, previews, GLB).
Front faces -Y in Blender (+Z in Studio). 1 unit = 1 stud. Touching boxes in one module overlap or keep 1 mm
apart (cleanup's merge welds exactly-touching corners).
"""
import os, sys, math, random
import bpy
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_buildings as bb
from build_buildings import lh, H, SNOW, SNOW_SIDE, SNOW_UNDER, WHITE, GLASS, IRON, GOLD, LIGHTS, snowy, fb

OUT = os.path.join(bb.ROOT, "assets", "town")
WOOD, WOOD_DARK, CREAM = H("#A0663A"), H("#7A4A28"), H("#FFF1DC")
ASPHALT, PAVE, PAVE_DARK = H("#4A505E"), H("#C9CED8"), H("#A9AFBB")
RED, RED_DARK, GREEN, GREEN_DARK, BLUE = H("#E8344E"), H("#B8243C"), H("#2E8A55"), H("#1F6B3F"), H("#3C8DFF")
ICE = H("#CFF2FF")
TYRE, HUB = H("#2A2A33"), H("#B8BEC9")
WINDOW = H("#9FC7E8")


def pack(name, builders, classes=None, soft=(), glow=(), base=None):
    """MeshBuilders -> the tuple bb.build expects. Modules faceted unless named in soft."""
    mods = [b.to_object() for b in builders]
    fin = {m.name: (dict(style="soft", bevel_width=0.05, smooth_angle=60) if m.name in soft else dict(style="faceted"))
           for m in mods}
    cls = {m.name: (classes or {}).get(m.name, "medium") for m in mods}
    return mods, fin, cls, (base or mods[0].name,), tuple(glow)


def lumps(b, rng, pts, size=(1.0, 0.8, 0.5)):
    """Flat-bottomed snow mounds sitting on z (an ico would poke below the ground and lift the whole model)."""
    for x, y, z in pts:
        s = rng.uniform(0.75, 1.25)
        r, h = (size[0] + size[1]) / 2 * s, size[2] * s * 1.4
        b.cyl((x, y, z - 0.02), (x, y, z + h), r, 7, lh.by_normal(SNOW, SNOW_SIDE), cap_in=SNOW, phase=rng.uniform(0, 1),
              tag="snow", r1=r * 0.45)


def bulbs(b, p0, p1, n, k=0, size=0.22):
    p0, p1 = Vector(p0), Vector(p1)
    for i in range(n):
        b.ico(p0.lerp(p1, i / max(1, n - 1)), (size, size, size * 1.3), LIGHTS[(k + i) % 5], subdiv=1, tag="bulb")
    return k + n


def star(b, c, R, depth, col, axis="Y"):
    """5-point star slab facing -Y (or up for axis Z) centred at c."""
    c = Vector(c)
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        r = R if i % 2 == 0 else R * 0.45
        pts.append((r * math.cos(a), r * math.sin(a)))
    to3 = (lambda x, z, d: c + Vector((x, d, z))) if axis == "Y" else (lambda x, y, d: c + Vector((x, y, d)))
    vs = [to3(x, z, -depth / 2) for x, z in pts] + [to3(x, z, depth / 2) for x, z in pts]
    vs += [to3(0, 0, -depth / 2 - 0.15), to3(0, 0, depth / 2 + 0.15)]
    faces = [(20, i, (i + 1) % 10) for i in range(10)] + [(21, 10 + (i + 1) % 10, 10 + i) for i in range(10)]
    faces += [(i, 10 + i, 10 + (i + 1) % 10, (i + 1) % 10) for i in range(10)]
    b.add(vs, faces, col, tag="star")


# ================================================================ road tiles (32 x 32: 22 road + 5 sidewalk each side)
BANDS = [(-16.0, -11.0), (-11.0, 11.0), (11.0, 16.0)]
ROADS = {"Road_Straight": "NS", "Road_Corner": "NE", "Road_T": "NEW", "Road_Cross": "NESW",
         "Road_Crosswalk": "NS", "Plaza_Tile": ""}


def road_tile(name):
    arms = ROADS[name]
    rng = random.Random(hash(name) % 1000)
    base, marks = lh.MeshBuilder(name + "_Base", rng), lh.MeshBuilder(name + "_Marks", rng)
    cell_road = lambda i, j: (i, j) == (1, 1) and arms or ((i, j) == (1, 2) and "N" in arms) or \
        ((i, j) == (1, 0) and "S" in arms) or ((i, j) == (2, 1) and "E" in arms) or ((i, j) == (0, 1) and "W" in arms)
    for i, (x0, x1) in enumerate(BANDS):
        for j, (y0, y1) in enumerate(BANDS):
            lo, hi = (x0 + 0.001, y0 + 0.001, 0.0), (x1 - 0.001, y1 - 0.001, None)
            if cell_road(i, j):
                base.box(lo, hi[:2] + (0.4,), lh.jitter(rng, ASPHALT, 0.03), tag="road")
            else:
                base.box(lo, hi[:2] + (0.9,), lh.by_normal(PAVE, PAVE_DARK), tag="walk")
    if not arms:      # plaza: red brick inlay ring and centre
        for (a, b_) in ((-9.0, 9.0),):
            for x0, y0, x1, y1 in ((a, a, b_, a + 1.2), (a, b_ - 1.2, b_, b_), (a, a + 1.25, a + 1.2, b_ - 1.25),
                                   (b_ - 1.2, a + 1.25, b_, b_ - 1.25)):
                marks.box((x0, y0, 0.85), (x1, y1, 0.95), H("#C2564A"), tag="inlay")
        marks.cyl((0, 0, 0.85), (0, 0, 0.95), 3.0, 16, H("#C2564A"), phase=0.0, tag="inlay")
    # lane dashes along each arm (not through junctions, not over the crosswalk)
    junction = len(arms) > 2 or arms == "NE"
    for arm, (dx, dy) in (("N", (0, 1)), ("S", (0, -1)), ("E", (1, 0)), ("W", (-1, 0))):
        if arm not in arms:
            continue
        start = 11.5 if junction else 0.5
        s = start
        while s + 2.5 <= 16.0:
            if name == "Road_Crosswalk" and s < 5.0:
                s += 5.0; continue
            a, c = s, s + 2.5
            if dx:
                xs = sorted((dx * a, dx * c)); marks.box((xs[0], -0.2, 0.35), (xs[1], 0.2, 0.45), GOLD, tag="dash")
            else:
                ys = sorted((dy * a, dy * c)); marks.box((-0.2, ys[0], 0.35), (0.2, ys[1], 0.45), GOLD, tag="dash")
            s += 5.0
    if name == "Road_Crosswalk":
        for k in range(8):
            x = -9.6 + k * 2.75
            marks.box((x, -3.5, 0.35), (x + 1.5, 3.5, 0.45), WHITE, tag="zebra")
    if junction:      # stop lines on each open arm
        for arm in arms:
            if arm in "NS":
                y = 11.3 if arm == "N" else -11.3
                marks.box((-10.5 if arm == "S" else 0.4, y - 0.4, 0.35), (-0.4 if arm == "S" else 10.5, y + 0.4, 0.45),
                          WHITE, tag="stop")
            else:
                x = 11.3 if arm == "E" else -11.3
                marks.box((x - 0.4, 0.4 if arm == "E" else -10.5, 0.35), (x + 0.4, 10.5 if arm == "E" else -0.4, 0.45),
                          WHITE, tag="stop")
    # snow banks on the sidewalk's outer corners
    pts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            i, j = (2 if sx > 0 else 0), (2 if sy > 0 else 0)
            if not cell_road(i, j):
                cx, cy = sx * 14.6, sy * 14.6
                pts += [(cx, cy, 0.9), (cx - sx * 1.6, cy, 0.9), (cx, cy - sy * 1.6, 0.9)]
    lumps(marks, rng, pts, (1.1, 1.1, 0.7))
    return pack(name, [base, marks], base=name + "_Base")


# ================================================================ market stall
STALLS = {"Stall_Red": (RED, WHITE, "candy"), "Stall_Green": (GREEN, CREAM, "trees"), "Stall_Blue": (BLUE, WHITE, "toys")}


def stall(name):
    ca, cb, goods = STALLS[name]
    rng = random.Random(len(name))
    s, can, li = (lh.MeshBuilder(name + n, rng) for n in ("_Stall", "_Canopy", "_Lights"))
    W, Dh = 8.0, 2.6
    s.box((-W / 2, -Dh, 0), (W / 2, -Dh + 1.4, 3.4), lh.by_normal(WOOD, WOOD, WOOD_DARK), tag="counter")
    for k in range(4):                       # vertical planks on the counter front
        x = -W / 2 + 0.6 + k * (W - 1.2) / 3
        s.box((x - 0.3, -Dh - 0.12, 0.2), (x + 0.3, -Dh + 0.2, 3.2), WOOD_DARK, tag="plank")
    s.box((-W / 2 - 0.2, -Dh - 0.3, 3.39), (W / 2 + 0.2, -Dh + 1.6, 3.7), snowy(CREAM), tag="top")
    s.box((-W / 2, Dh - 0.3, 0), (W / 2, Dh, 7.6), WOOD, tag="back")
    for sx in (-1, 1):
        s.box((sx * W / 2 - 0.25, -Dh - 0.2, 0), (sx * W / 2 + 0.25, -Dh + 0.3, 7.8), WOOD_DARK, tag="post")
        s.box((sx * W / 2 - 0.25, Dh - 0.4, 0), (sx * W / 2 + 0.25, Dh + 0.05, 9.0), WOOD_DARK, tag="post")
        s.box((sx * W / 2 - 0.15, -Dh + 0.2, 0.0), (sx * W / 2 + 0.05 * sx, Dh - 0.3, 3.0), WOOD, tag="side")
    # goods on the counter
    for k in range(5):
        x = -W / 2 + 0.9 + k * (W - 1.8) / 4
        if goods == "candy":
            s.cyl((x, -Dh + 0.7, 3.65), (x, -Dh + 0.7, 4.6), 0.08, 6, WHITE, tag="stick")
            s.cyl((x, -Dh + 0.6, 4.8), (x, -Dh + 0.8, 4.8), 0.5, 10, (RED, WHITE, GOLD, BLUE, GREEN)[k], phase=0.0, tag="pop")
        elif goods == "trees":
            s.cone((x, -Dh + 0.7, 3.65), (x, -Dh + 0.7, 5.2), 0.6, 7, GREEN_DARK if k % 2 else GREEN, tag="tree")
        else:
            c = (RED, GOLD, BLUE, GREEN, H("#FF82C4"))[k]
            s.box((x - 0.45, -Dh + 0.25, 3.65), (x + 0.45, -Dh + 1.15, 4.5), c, tag="box")
            s.box((x - 0.08, -Dh + 0.2, 3.66), (x + 0.08, -Dh + 1.2, 4.55), WHITE, tag="ribbon")
    # sloped striped canopy: back 9.0 high, front 7.5, overhangs the counter
    run, drop = 2 * Dh + 1.6, 1.5
    L = math.hypot(run, drop)
    M3 = Matrix.Rotation(math.atan2(-drop, -run), 3, "X")
    n = 8
    sw = (W + 1.0) / n
    for i in range(n):
        x = -(W + 1.0) / 2 + (i + 0.5) * sw
        c = ca if i % 2 == 0 else cb
        can.obox(Vector((x, Dh - run / 2 + 0.2, 9.0 - drop / 2 + 0.25)), (sw - 0.02, L + 0.4, 0.22), M3,
                 c, tag="slat")
        can.box((x - sw / 2 + 0.01, Dh - run - 0.3, 6.95), (x + sw / 2 - 0.01, Dh - run - 0.05, 7.75), c, tag="valance")
    can.box((-(W + 1.0) / 2, Dh - run - 0.32, 7.7), ((W + 1.0) / 2, Dh - run + 0.4, 7.95), snowy(WHITE), tag="rail")
    bulbs(li, (-(W + 0.6) / 2, Dh - run - 0.35, 7.0), ((W + 0.6) / 2, Dh - run - 0.35, 7.0), 9)
    return pack(name, [s, can, li], glow=[name + "_Lights"], base=name + "_Stall")


# ================================================================ garage and shed (sided walls, gable roof)
SHEDS = {"Garage": dict(hx=7.0, hy=9.0, eave=9.5, pitch=26, door=(10.0, 7.6, "rollup"), siding=["#E9EEF5", "#DDE3EC", "#F2F5FA"],
                        groove="#8F98A8", roof="#3A4E8C", roof_under="#26355F", trim=RED),
         "Shed": dict(hx=4.0, hy=3.5, eave=7.4, pitch=34, door=(3.6, 6.4, "plank"), siding=["#C23B3B", "#B33434", "#CC4646"],
                      groove="#7E2222", roof="#3B3F4A", roof_under="#2A2A33", trim=WHITE)}


def gable_fill(walls, faces, gable, ue, eave, t, groove, corner):
    """Back infill triangle + bargeboards on both gable walls (stepped courses leave notches under the slope)."""
    ridge = gable.ridge_z
    for key in ("-Y", "+Y"):
        f = faces[key]
        walls.prism(f.p(-ue + 0.05, eave - 0.05, -t + 0.05), f.p(-ue + 0.05, eave - 0.05, -0.7),
                    f.p(ue - 0.05, eave - 0.05, -t + 0.05), f.p(ue - 0.05, eave - 0.05, -0.7),
                    f.p(0, ridge - 0.08, -t + 0.05), f.p(0, ridge - 0.08, -0.7), groove, tag="infill")
        for s in (-1, 1):
            u0, u1 = s * (ue + 0.4), s * 0.002
            z0t, z1t = gable.under(u0) - 0.01, ridge - 0.01
            vs = [f.p(u, z, d) for d in (-0.15, 0.3) for u, z in ((u0, z0t - 1.15), (u1, z1t - 1.15), (u1, z1t), (u0, z0t))]
            walls.add(vs, [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)],
                      corner, tag="barge")


def shed(name):
    v = SHEDS[name]
    rng = random.Random(len(name) * 7)
    t, hx, hy, plinth = 1.0, v["hx"], v["hy"], 0.5
    eave = v["eave"]
    dw, dh, kind = v["door"]
    base = lh.MeshBuilder(name + "_Foundation", rng)
    lh.foundation(base, hx, hy, t / 2, height=plinth, margin=0.3, colour=H("#B0B6C0"))
    walls = lh.MeshBuilder(name + "_Walls", rng)
    gable = lh.Gable(hx + t / 2, eave, v["pitch"])
    openings = {"-Y": [(-dw / 2, dw / 2, plinth, plinth + dh)],
                "+X": [(-1.4, 1.4, plinth + 3.0, plinth + 5.6)] if name == "Garage" else []}
    faces, ops, ch = lh.coursed_walls(walls, hx, hy, thickness=t, z0=plinth, eave_z=eave, course_h=0.9,
                                      block_len=(60, 61), gap=0.07, colours=[H(c) for c in v["siding"]],
                                      mortar=H(v["groove"]), quoin=WHITE, quoin_len=(1.2, 1.2), proud=0.05,
                                      gable=gable, openings=openings)
    gable_fill(walls, faces, gable, hx + t / 2, eave, t, H(v["groove"]), WHITE)
    roof = lh.MeshBuilder(name + "_Roof", rng)
    R = lh.gable_roof(roof, gable, hy + t / 2, thickness=0.8, overhang_x=1.2, overhang_y=1.0, colour=H(v["roof"]),
                      underside=H(v["roof_under"]), style="slab",
                      snow=dict(thick=1.1, extra_x=0.4, extra_y=0.3, lip=0.4, colours=(SNOW, SNOW_SIDE, SNOW_UNDER)))
    for side in (-1, 1):
        x = side * (R["snow_xe"] - 0.3)
        lh.icicle_row(roof, (x, -R["snow_ye"] + 0.5, 0), (x, R["snow_ye"] - 0.5, 0), int(hy * 1.6), colour=H("#CFF2FF"),
                      z_at=lambda X, Y: R["snow_under"](X), radius=(0.16, 0.22), lengths=(0.5, 0.8, 1.1))
    door = lh.MeshBuilder(name + "_Door", rng)
    glow = lh.MeshBuilder(name + "_Glow", rng)
    f = faces["-Y"]
    d0, d1, z0, z1 = ops["-Y"][0]
    if kind == "rollup":
        n = int((z1 - z0) / 0.8)
        for k in range(n):        # overlapping slats, tucked into the jambs so they connect to the walls
            za = z0 + k * (z1 - z0) / n
            dd = 0.02 if k % 2 else 0.0
            fb(f, door, (d0 - 0.15, za, -0.62 + dd), (d1 + 0.15, za + (z1 - z0) / n + 0.04, -0.3 + dd),
               H("#F2F5FA") if k % 2 else H("#DDE3EC"), )
        fb(f, door, (d0 + 1.0, z0 + 0.9, -0.35), (d1 - 1.0, z0 + 1.2, -0.15), IRON)        # handle bar
        for k in range(3):                                                                 # little windows
            u = d0 + (k + 1) * (d1 - d0) / 4
            fb(f, glow, (u - 0.9, z1 - 2.0, -0.32), (u + 0.9, z1 - 1.0, -0.22), GLASS)
    else:
        lh.door(door, f, 0.0, z0, d1 - d0, z1 - z0, recess=0.3, planks=4, colours=[WOOD, WOOD_DARK], batten=WOOD_DARK,
                frame=WHITE, knob=GOLD)
    for s in (-1, 1):                                  # trim frame around the opening
        fb(f, door, (s * (dw / 2 + 0.25) - 0.25, z0, -0.2), (s * (dw / 2 + 0.25) + 0.25, z1 + 0.45, 0.25), v["trim"])
    fb(f, door, (-dw / 2 - 0.55, z1 + 0.01, -0.22), (dw / 2 + 0.55, z1 + 0.5, 0.27), snowy(v["trim"]))
    if name == "Garage":
        lh.window(door, glow, faces["+X"], 0.0, plinth + 4.3, 2.8, 2.6, recess=t / 2, colours=dict(frame=WHITE, glass=GLASS),
                  cap=dict(top=SNOW, front=WHITE, under=H("#E2CDB0")), sill_top=SNOW)
        # driveway apron
        base.box((-dw / 2 - 1.0, -hy - t / 2 - 4.0, 0), (dw / 2 + 1.0, -hy - t / 2 - 0.25, 0.3), lh.by_normal(PAVE, PAVE_DARK), tag="apron")
    else:
        lh.window(door, glow, faces["+X"], 0.0, plinth + 3.6, 1.8, 1.8, recess=t / 2, colours=dict(frame=WHITE, glass=GLASS),
                  shutters=(GREEN, GREEN_DARK), sill_top=SNOW, mullions=False)
    lights = lh.MeshBuilder(name + "_Lights", rng)
    k = bulbs(lights, (-R["xe"] + 0.5, -R["ye"] + 0.35, R["under"](-R["xe"] + 0.5) - 0.12),
              (0, -R["ye"] + 0.35, R["under"](0) - 0.12), max(4, int(R["xe"] * 0.9)))
    bulbs(lights, (0.6, -R["ye"] + 0.35, R["under"](0.6) - 0.12),
          (R["xe"] - 0.5, -R["ye"] + 0.35, R["under"](R["xe"] - 0.5) - 0.12), max(4, int(R["xe"] * 0.9)), k)
    return pack(name, [base, walls, roof, door, glow, lights], soft=[name + "_Roof"],
                classes={name + "_Walls": "building", name + "_Roof": "building"},
                glow=[name + "_Glow", name + "_Lights"], base=name + "_Foundation")


# ================================================================ igloo
def igloo(name):
    rng = random.Random(5)
    R, rings = 7.0, 6
    dome, door = lh.MeshBuilder(name + "_Dome", rng), lh.MeshBuilder(name + "_Door", rng)
    top = math.radians(78)
    phis = [top * k / rings for k in range(rings + 1)]
    for k in range(rings):        # core frustums (the "mortar" between blocks)
        z0, z1 = R * math.sin(phis[k]) * 0.92, R * math.sin(phis[k + 1]) * 0.92
        dome.cyl((0, 0, z0 + (0.0 if k == 0 else -0.02)), (0, 0, z1 + 0.02), (R - 0.35) * math.cos(phis[k]), 16, H("#B7DCEB"),
                 phase=0.0, tag="core", r1=(R - 0.35) * math.cos(phis[k + 1]))
    zt = R * math.sin(top) * 0.92
    dome.cyl((0, 0, zt - 0.05), (0, 0, zt + 0.4), (R - 0.2) * math.cos(top) + 0.3, 12, SNOW, phase=0.0, tag="cap",
             r1=(R - 0.2) * math.cos(top) - 0.3)
    for k in range(rings):
        pm = (phis[k] + phis[k + 1]) / 2
        rr = R * math.cos(pm)
        n = max(5, round(2 * math.pi * rr / 2.4))
        off = (k % 2) * math.pi / n
        for i in range(n):
            a = off + 2 * math.pi * i / n
            radial = Vector((math.cos(pm) * math.cos(a), math.cos(pm) * math.sin(a), math.sin(pm)))
            tang = Vector((-math.sin(a), math.cos(a), 0))
            mer = radial.cross(tang)
            M3 = Matrix((tang, mer, radial)).transposed()
            c = Vector((rr * math.cos(a), rr * math.sin(a), R * math.sin(pm) * 0.92)) - radial * 0.2
            size = (2 * math.pi * rr / n - 0.14, R * (phis[k + 1] - phis[k]) * 0.92 - 0.12, 0.7)
            dome.obox(c, size, M3, lh.by_normal(SNOW, lh.jitter(rng, ICE, 0.03), H("#B7DCEB"), up_min=0.6), tag="block")
    # entrance tunnel on -Y
    y0, y1 = -R - 3.0, -R + 2.0
    door.box((-2.4, y0, 0), (2.4, y1, 3.0), lh.by_normal(SNOW, ICE), tag="tunnel")
    door.cyl((0, y0, 3.0), (0, y1, 3.0), 2.4, 12, lh.by_normal(SNOW, ICE), cap_in=ICE, phase=0.0, tag="arch")
    door.box((-1.4, y0 - 0.06, 0.0), (1.4, y0 + 0.3, 3.4), H("#24324A"), tag="hole")
    door.cyl((0, y0 - 0.06, 3.4), (0, y0 + 0.3, 3.4), 1.4, 10, H("#24324A"), phase=0.0, tag="hole")
    lumps(door, rng, [(-3.0, y0 + 1.0, 0.0), (3.0, y0 + 1.5, 0.0), (-R + 0.3, 2.0, 0.0), (R - 0.5, -1.5, 0.0)], (1.3, 1.1, 0.8))
    return pack(name, [dome, door], classes={name + "_Dome": "building"}, base=name + "_Dome")


# ================================================================ clock tower
def clock_tower(name):
    rng = random.Random(9)
    tw, trim, glow, roof = (lh.MeshBuilder(name + n, rng) for n in ("_Tower", "_Trim", "_Glow", "_Roof"))
    BR = [H("#B5523B"), H("#A94B36"), H("#BD5A42")]
    h = 5.0                                              # half width of the shaft
    tw.box((-h - 1.2, -h - 1.2, 0), (h + 1.2, h + 1.2, 3.0), snowy(H("#B0B6C0"), H("#8F96A3")), tag="plinth")
    zs = [2.95] + [3.0 + 3.2 * k for k in range(1, 11)]
    for z0, z1 in zip(zs, zs[1:]):                       # brick bands, jittered colour
        tw.box((-h, -h, z0), (h, h, z1 + 0.02), lh.jitter(rng, rng.choice(BR), 0.05), tag="brick")
    shaft_top = zs[-1]
    for z in (12.6, 22.2, shaft_top - 0.1):              # stone bands
        trim.box((-h - 0.35, -h - 0.35, z - 0.35), (h + 0.35, h + 0.35, z + 0.35), snowy(CREAM, H("#E2CDB0")), tag="band")
    for sx in (-1, 1):
        for sy in (-1, 1):                               # corner pilasters
            trim.box((sx * h - 0.6 - 0.001 * sx, sy * h - 0.6, 3.0), (sx * h + 0.6, sy * h + 0.6, shaft_top), H("#E2CDB0"), tag="pilaster")
    faces = lh.house_faces(h - 0.5, h - 0.5, 0.5)
    for key, f in faces.items():
        zc = shaft_top - 5.0
        fz = lambda u, z, d: f.p(u, z, d)
        trim.cyl(fz(0, zc, -0.05), fz(0, zc, 0.35), 3.7, 20, CREAM, phase=0.0, tag="rim")
        glow.cyl(fz(0, zc, 0.3), fz(0, zc, 0.45), 3.2, 20, H("#FFF6D8"), phase=0.0, tag="dial")
        for k in range(12):                              # hour ticks
            a = 2 * math.pi * k / 12
            trim.box(*bb.sorted_box(f, (2.65 * math.cos(a) - 0.12, zc + 2.65 * math.sin(a) - 0.12, 0.42),
                                    (2.65 * math.cos(a) + 0.12, zc + 2.65 * math.sin(a) + 0.12, 0.55)), IRON, tag="tick")
        trim.box(*bb.sorted_box(f, (-0.14, zc - 0.1, 0.5), (0.14, zc + 2.3, 0.62)), IRON, tag="hand")
        trim.box(*bb.sorted_box(f, (-0.1, zc - 0.14, 0.58), (1.7, zc + 0.14, 0.7)), IRON, tag="hand")
        trim.cyl(fz(0, zc, 0.45), fz(0, zc, 0.78), 0.3, 8, GOLD, phase=0.0, tag="pin")
        for k, zw in enumerate((6.2, 15.4)):             # windows up the shaft (seated on the wall face, d = 0)
            glow.box(*bb.sorted_box(f, (-0.9, zw, -0.05), (0.9, zw + 3.0, 0.12)), GLASS, tag="win")
            trim.box(*bb.sorted_box(f, (-1.3, zw - 0.45, -0.05), (1.3, zw + 0.02, 0.45)), snowy(CREAM), tag="sill")
            trim.box(*bb.sorted_box(f, (-0.1, zw + 0.01, 0.08), (0.1, zw + 2.99, 0.22)), WHITE, tag="mullion")
            trim.box(*bb.sorted_box(f, (-1.2, zw + 2.98, -0.05), (1.2, zw + 3.5, 0.35)), CREAM, tag="lintel")
    f = faces["-Y"]
    trim.box(*bb.sorted_box(f, (-1.9, 3.0, -0.05), (1.9, 8.99, 0.25)), GREEN_DARK, tag="door")
    trim.box(*bb.sorted_box(f, (-2.3, 9.0, -0.05), (2.3, 9.6, 0.7)), snowy(CREAM), tag="lintel")
    trim.box(*bb.sorted_box(f, (-0.1, 3.05, 0.2), (0.1, 8.9, 0.35)), GOLD, tag="door")
    trim.box(*bb.sorted_box(f, (-2.6, 0.0, -0.05), (2.6, 1.0, 3.6)), snowy(H("#B0B6C0")), tag="step")
    trim.box(*bb.sorted_box(f, (-2.55, 0.99, -0.05), (2.55, 2.0, 2.4)), snowy(H("#B0B6C0")), tag="step")
    # belfry: floor, 4 corner piers, a gold bell, cornice
    zb = shaft_top
    roof.box((-h - 0.6, -h - 0.6, zb - 0.05), (h + 0.6, h + 0.6, zb + 0.6), snowy(CREAM, H("#E2CDB0")), tag="floor")
    for sx in (-1, 1):
        for sy in (-1, 1):
            roof.box((sx * h - 1.0 * sx - 0.9, sy * h - 1.0 * sy - 0.9, zb + 0.55), (sx * h - 1.0 * sx + 0.9, sy * h - 1.0 * sy + 0.9, zb + 7.05),
                     lh.jitter(rng, BR[0], 0.03), tag="pier")
    roof.cyl((0, 0, zb + 7.2), (0, 0, zb + 5.6), 0.15, 6, IRON, phase=0.0, tag="hanger")
    roof.cyl((0, 0, zb + 5.7), (0, 0, zb + 3.0), 0.9, 12, GOLD, phase=0.0, tag="bell", r1=1.8)
    roof.box((-h - 0.8, -h - 0.8, zb + 7.0), (h + 0.8, h + 0.8, zb + 8.0), snowy(CREAM, H("#E2CDB0")), tag="cornice")
    # pyramid spire (explicit verts so its sides line up with the shaft)
    zr, s, tip = zb + 7.95, h + 0.5, zb + 19.0
    roof.cyl((0, 0, zr), (0, 0, tip - 0.5), s * math.sqrt(2), 4, GREEN, cap_in=SNOW, phase=math.pi / 4, tag="spire",
             r1=0.45)
    roof.cyl((0, 0, zr + 0.01), (0, 0, zr + 1.3), s * math.sqrt(2) + 0.25, 4, lh.by_normal(SNOW, SNOW_SIDE), cap_in=SNOW,
             phase=math.pi / 4, tag="snow", r1=(s - 1.0) * math.sqrt(2))
    roof.ico((0, 0, tip), (0.7, 0.7, 0.7), GOLD, subdiv=1, tag="ball")
    roof.cyl((0, 0, tip + 0.1), (0, 0, tip + 3.4), 0.2, 6, GOLD, phase=0.0, tag="rod")   # pokes through the star's spike
    star(roof, (0, 0, tip + 4.0), 1.3, 0.35, GOLD)
    return pack(name, [tw, trim, glow, roof], classes={name + "_Trim": "building", name + "_Tower": "building"},
                soft=[], glow=[name + "_Glow"], base=name + "_Tower")


# ================================================================ town Christmas tree plaza
def tree_plaza(name):
    rng = random.Random(11)
    pl, tr, dec, li, st = (lh.MeshBuilder(name + n, rng) for n in ("_Plaza", "_Tree", "_Decor", "_Lights", "_Star"))
    pl.cyl((0, 0, 0), (0, 0, 0.6), 17.0, 28, lh.by_normal(PAVE, PAVE_DARK), cap_in=PAVE, phase=0.0, tag="plaza")
    pl.cyl((0, 0, 0.4), (0, 0, 0.7), 10.5, 28, H("#C2564A"), phase=0.0, tag="ring")
    pl.cyl((0, 0, 0.5), (0, 0, 1.6), 7.0, 20, snowy(CREAM, H("#E2CDB0")), cap_in=SNOW, phase=0.0, tag="planter")
    tr.cyl((0, 0, 1.5), (0, 0, 6.0), 1.3, 10, WOOD_DARK, phase=0.0, tag="trunk")
    tiers = [(4.5, 7.6, 9.5), (9.0, 6.4, 8.5), (13.0, 5.2, 7.5), (16.8, 4.0, 6.5), (20.2, 2.8, 5.5), (23.2, 1.7, 4.6)]
    for k, (z, r, hgt) in enumerate(tiers):
        g = GREEN if k % 2 else H("#267A49")
        tr.cone((0, 0, z), (0, 0, z + hgt), r, 14, g, tag="tier")
        # snow skirt: a squat frustum just above the tier rim
        tr.cyl((0, 0, z + 0.25), (0, 0, z + 0.9), r * 0.93, 14, lh.by_normal(SNOW, SNOW_SIDE), cap_in=SNOW, phase=0.1, tag="snow",
               r1=r * 0.78)
        n = max(5, int(r * 2.2))
        for i in range(n):
            a = 2 * math.pi * (i + 0.5 * (k % 2)) / n
            rr = r * 0.86
            p = (rr * math.cos(a), rr * math.sin(a), z + 0.2)
            dec.ico(p, (0.5, 0.5, 0.5), (RED, GOLD, BLUE, H("#FF82C4"), WHITE)[(i + k) % 5], subdiv=1, tag="ornament")
    # spiral string of lights
    turns, top_z = 4.5, 26.0
    m = 120
    for i in range(m):
        tt = i / (m - 1)
        z = 5.2 + tt * (top_z - 5.2)
        # radius of the tiers' envelope at this height, bulb sunk a little into the surface so it touches
        r = max([tr_ * (1 - (z - tz) / th) for tz, tr_, th in tiers if tz <= z <= tz + th] + [0.3]) * 0.96
        a = 2 * math.pi * turns * tt
        li.ico((r * math.cos(a), r * math.sin(a), z), (0.28, 0.28, 0.34), LIGHTS[i % 5], subdiv=1, tag="bulb")
    star(st, (0, 0, 28.8), 2.4, 0.7, GOLD)
    st.cyl((0, 0, 26.0), (0, 0, 27.2), 0.35, 8, GOLD, phase=0.0, tag="stem")
    # presents round the planter, candy posts round the rim
    for i in range(8):
        a = 2 * math.pi * i / 8 + 0.2
        r = 8.4
        w = rng.uniform(1.2, 1.9)
        c = (RED, GREEN, BLUE, GOLD, H("#FF82C4"), H("#9B6BFF"), RED, GREEN)[i]
        x, y = r * math.cos(a), r * math.sin(a)
        dec.box((x - w / 2, y - w / 2, 0.69), (x + w / 2, y + w / 2, 0.7 + w), c, tag="present")
        dec.box((x - w / 2 - 0.04, y - 0.15, 0.69), (x + w / 2 + 0.04, y + 0.15, 0.74 + w), WHITE, tag="ribbon")
        dec.box((x - 0.15, y - w / 2 - 0.04, 0.69), (x + 0.15, y + w / 2 + 0.04, 0.74 + w), WHITE, tag="ribbon")
    for i in range(16):
        a = 2 * math.pi * i / 16
        x, y = 16.0 * math.cos(a), 16.0 * math.sin(a)
        if -0.6 < math.sin(a) < -0.2 and abs(math.cos(a)) < 0.5:
            continue
        for k in range(4):
            dec.cyl((x, y, 0.55 + k * 0.75), (x, y, 0.55 + (k + 1) * 0.75 + 0.01), 0.35, 8, RED if k % 2 == 0 else WHITE,
                    phase=0.0, tag="post")
        dec.ico((x, y, 3.7), (0.45, 0.45, 0.45), GOLD, subdiv=1, tag="knob")
    return pack(name, [pl, tr, dec, li, st], classes={name + "_Tree": "building", name + "_Lights": "building"},
                glow=[name + "_Lights", name + "_Star"], base=name + "_Plaza")


# ================================================================ ice rink
def ice_rink(name):
    rng = random.Random(13)
    ice, brd, li = (lh.MeshBuilder(name + n, rng) for n in ("_Ice", "_Boards", "_Lights"))
    X, Y = 22.0, 13.0
    ice.box((-X, -Y, 0), (X, Y, 0.5), lh.by_normal(ICE, H("#A9D8EC")), tag="ice")
    ice.cyl((0, 0, 0.45), (0, 0, 0.56), 3.2, 20, RED, phase=0.0, tag="circle")
    ice.cyl((0, 0, 0.46), (0, 0, 0.58), 2.6, 20, ICE, phase=0.0, tag="circle")
    for x in (-X / 2, 0.0, X / 2):
        ice.box((x - 0.25, -Y + 0.4, 0.45), (x + 0.25, Y - 0.4, 0.55), RED if x == 0 else BLUE, tag="line")
    # boards with an entrance gap at the front centre
    segs = [((-X - 0.5, -Y - 0.5), (-2.5, -Y)), ((2.5, -Y - 0.5), (X + 0.5, -Y)), ((-X - 0.5, Y), (X + 0.5, Y + 0.5)),
            ((-X - 0.5, -Y + 0.01), (-X, Y - 0.01)), ((X, -Y + 0.01), (X + 0.5, Y - 0.01))]
    for (x0, y0), (x1, y1) in segs:
        brd.box((x0, y0, 0.0), (x1, y1, 2.2), WHITE, tag="board")
        brd.box((x0 - 0.12, y0 - 0.12, 2.15), (x1 + 0.12, y1 + 0.12, 2.6), snowy(RED, RED_DARK), tag="rail")
        brd.box((x0 - 0.04, y0 - 0.04, 0.0), (x1 + 0.04, y1 + 0.04, 0.45), BLUE, tag="kick")
    for sx in (-1, 1):                               # entrance posts with candy-striped tops
        brd.box((sx * 2.5 - 0.35, -Y - 0.65, 0), (sx * 2.5 + 0.35, -Y + 0.15, 4.0), RED, tag="gate")
        brd.ico((sx * 2.5, -Y - 0.25, 4.3), (0.5, 0.5, 0.5), GOLD, subdiv=1, tag="gate")
    pts = [(x, s * (Y + 1.3), 0.0) for x in range(-20, 21, 4) for s in (-1, 1) if abs(x) > 4 or s > 0]
    pts += [(s * (X + 1.3), y, 0.0) for y in range(-11, 12, 4) for s in (-1, 1)]
    lumps(brd, rng, pts, (1.4, 1.2, 0.8))
    k = 0
    for (x0, y0), (x1, y1) in segs:
        if abs(x1 - x0) > abs(y1 - y0):
            yy = (y0 + y1) / 2
            k = bulbs(li, (x0 + 0.4, yy, 2.85), (x1 - 0.4, yy, 2.85), max(3, int((x1 - x0) / 1.6)), k)
        else:
            xx = (x0 + x1) / 2
            k = bulbs(li, (xx, y0 + 0.4, 2.85), (xx, y1 - 0.4, 2.85), max(3, int((y1 - y0) / 1.6)), k)
    return pack(name, [ice, brd, li], classes={name + "_Boards": "building"}, glow=[name + "_Lights"], base=name + "_Ice")


# ================================================================ street props
def hydrant(name):
    b = lh.MeshBuilder(name, random.Random(1))
    b.cyl((0, 0, 0), (0, 0, 0.35), 0.75, 10, RED_DARK, phase=0.0, tag="base")
    b.cyl((0, 0, 0.3), (0, 0, 2.0), 0.55, 10, RED, phase=0.0, tag="body")
    b.cyl((0, 0, 1.95), (0, 0, 2.25), 0.68, 10, RED_DARK, phase=0.0, tag="collar")
    b.cyl((0, 0, 2.2), (0, 0, 2.75), 0.55, 10, RED, phase=0.0, tag="dome", r1=0.25)
    b.cyl((0, 0, 2.7), (0, 0, 3.0), 0.18, 6, GOLD, phase=0.0, tag="nut")
    for s in (-1, 1):
        b.cyl((s * 0.45, 0, 1.45), (s * 0.95, 0, 1.45), 0.25, 8, RED, phase=0.0, tag="nozzle")
        b.cyl((s * 0.9, 0, 1.45), (s * 1.05, 0, 1.45), 0.3, 8, GOLD, phase=0.0, tag="cap")
    b.cyl((0, -0.45, 1.2), (0, -0.85, 1.2), 0.32, 8, RED, phase=0.0, tag="nozzle")
    b.cyl((0, -0.8, 1.2), (0, -0.95, 1.2), 0.38, 8, GOLD, phase=0.0, tag="cap")
    b.ico((0.05, 0, 2.62), (0.5, 0.5, 0.28), SNOW, subdiv=1, tag="snow")
    return pack(name, [b])


def stop_sign(name):
    b = lh.MeshBuilder(name, random.Random(2))
    b.cyl((0, 0, 0), (0, 0, 8.6), 0.14, 8, H("#8F96A3"), phase=0.0, tag="post")
    b.cyl((0, 0.05, 7.4), (0, -0.12, 7.4), 1.55, 8, WHITE, phase=math.pi / 8, tag="rim")
    b.cyl((0, -0.1, 7.4), (0, -0.2, 7.4), 1.38, 8, RED, phase=math.pi / 8, tag="face")
    for k, x in enumerate((-0.8, -0.27, 0.27, 0.8)):     # four white "letters" bars
        b.box((x - 0.17, -0.24, 7.1), (x + 0.17, -0.17, 7.7), WHITE, tag="letter")
    b.ico((0, -0.05, 8.95), (0.65, 0.35, 0.22), SNOW, subdiv=1, tag="snow")
    b.ico((0, 0, 0.1), (0.7, 0.7, 0.3), SNOW, subdiv=1, tag="snow")
    return pack(name, [b])


def traffic_light(name):
    rng = random.Random(3)
    b, g = lh.MeshBuilder(name + "_Pole", rng), lh.MeshBuilder(name + "_Glow", rng)
    b.cyl((0, 0, 0), (0, 0, 0.5), 0.6, 8, IRON, phase=0.0, tag="foot")
    b.cyl((0, 0, 0.4), (0, 0, 13.0), 0.3, 8, IRON, phase=0.0, tag="pole")
    b.box((-0.2, -0.25, 12.4), (8.0, 0.25, 12.9), IRON, tag="arm")
    for x in (4.0, 7.4):
        b.box((x - 0.8, -0.6, 8.7), (x + 0.8, 0.6, 12.45), H("#E0B020"), tag="housing")
        b.box((x - 0.95, -0.65, 12.4), (x + 0.95, 0.65, 12.75), snowy(H("#E0B020")), tag="hood")
        for k, c in enumerate((H("#FF3B3B"), H("#FFC840"), H("#3CE07A"))):
            z = 11.7 - k * 1.2
            g.cyl((x, -0.55, z), (x, -0.75, z), 0.42, 10, c, phase=0.0, tag="lamp")
            b.box((x - 0.55, -0.95, z + 0.38), (x + 0.55, -0.55, z + 0.5), IRON, tag="visor")
        b.ico((x, 0, 12.9), (0.9, 0.6, 0.25), SNOW, subdiv=1, tag="snow")
    b.box((-0.45, -0.45, 3.2), (0.45, 0.45, 4.6), H("#E0B020"), tag="button")
    return pack(name, [b, g], glow=[name + "_Glow"], base=name + "_Pole")


def bus_stop(name):
    rng = random.Random(4)
    b, g = lh.MeshBuilder(name + "_Shelter", rng), lh.MeshBuilder(name + "_Glass", rng)
    W, D, Hh = 9.0, 3.6, 7.2
    b.box((-W / 2 - 0.5, -D / 2 - 0.6, 0), (W / 2 + 0.5, D / 2 + 0.3, 0.3), lh.by_normal(PAVE, PAVE_DARK), tag="pad")
    for sx in (-1, 1):
        for y in (-D / 2 + 0.2, D / 2 - 0.2):
            b.box((sx * W / 2 - 0.2, y - 0.2, 0.25), (sx * W / 2 + 0.2, y + 0.2, Hh), GREEN_DARK, tag="post")
    b.box((-W / 2 - 0.6, -D / 2 - 0.6, Hh - 0.05), (W / 2 + 0.6, D / 2 + 0.3, Hh + 0.5), lh.by_normal(SNOW, GREEN, GREEN_DARK), tag="roof")
    b.box((-W / 2 - 0.4, -D / 2 - 0.65, Hh + 0.45), (W / 2 + 0.4, D / 2 + 0.25, Hh + 0.9), lh.by_normal(SNOW, SNOW_SIDE), tag="snow")
    g.box((-W / 2 + 0.2, D / 2 - 0.3, 1.0), (W / 2 - 0.2, D / 2 - 0.1, Hh - 0.4), WINDOW, tag="glass")
    g.box((-W / 2 - 0.1, -D / 2 + 0.4, 1.0), (-W / 2 + 0.1, D / 2 - 0.4, Hh - 0.4), WINDOW, tag="glass")
    b.box((-W / 2 + 0.3, D / 2 - 0.35, 0.8), (W / 2 - 0.3, D / 2 - 0.05, 1.05), GREEN_DARK, tag="rail")
    b.box((-W / 2 + 0.6, 0.2, 1.8), (W / 2 - 0.6, 1.4, 2.15), WOOD, tag="seat")
    for x in (-W / 2 + 1.2, W / 2 - 1.2):
        b.box((x - 0.15, 0.6, 0.25), (x + 0.15, 1.0, 1.85), IRON, tag="leg")
    # sign pole
    b.cyl((W / 2 + 1.2, -D / 2, 0.25), (W / 2 + 1.2, -D / 2, 9.0), 0.12, 6, H("#8F96A3"), phase=0.0, tag="signpost")
    b.box((W / 2 + 0.45, -D / 2 - 0.08, 7.6), (W / 2 + 1.95, -D / 2 + 0.08, 9.1), BLUE, tag="sign")
    b.box((W / 2 + 0.75, -D / 2 - 0.12, 7.95), (W / 2 + 1.65, -D / 2 + 0.12, 8.75), WHITE, tag="sign")
    return pack(name, [b, g], classes={name + "_Shelter": "medium"}, base=name + "_Shelter")


def phone_booth(name):
    rng = random.Random(6)
    b, g = lh.MeshBuilder(name + "_Booth", rng), lh.MeshBuilder(name + "_Glow", rng)
    s, Hh = 1.7, 8.0
    b.box((-s - 0.2, -s - 0.2, 0), (s + 0.2, s + 0.2, 0.4), RED_DARK, tag="base")
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box((sx * s - 0.25, sy * s - 0.25, 0.35), (sx * s + 0.25, sy * s + 0.25, Hh), RED, tag="post")
    for key, f in lh.house_faces(s - 0.15, s - 0.15, 0.15).items():
        fb(f, b, (-s + 0.2, 0.4, -0.35), (s - 0.2, 1.6, 0.0), RED, )          # kick panel
        fb(f, b, (-s + 0.3, 1.61, -0.25), (s - 0.3, Hh - 1.31, -0.12), WINDOW)  # glass (corners kept apart: no welds)
        for z in (3.1, 4.6, 6.0):
            fb(f, b, (-s + 0.2, z - 0.09, -0.15), (s - 0.2, z + 0.09, 0.05), RED)
        fb(f, b, (-0.09, 1.6, -0.15), (0.09, Hh - 1.3, 0.05), RED)
        fb(f, g, (-s + 0.3, Hh - 1.1, -0.05), (s - 0.3, Hh - 0.45, 0.08), WHITE)  # lit "PHONE" strip
        fb(f, b, (-s + 0.2, Hh - 1.3, -0.3), (s - 0.2, Hh - 0.25, 0.0), RED_DARK)
    b.box((-s - 0.35, -s - 0.35, Hh - 0.05), (s + 0.35, s + 0.35, Hh + 0.5), RED, tag="roof")
    b.cyl((0, 0, Hh + 0.45), (0, 0, Hh + 1.3), s + 0.1, 4, RED, phase=math.pi / 4, tag="dome", r1=0.5)
    b.ico((0, 0, Hh + 1.2), (1.2, 1.2, 0.35), SNOW, subdiv=1, tag="snow")
    b.cyl((0, 0, Hh + 1.22), (0, 0, Hh + 1.7), 0.25, 8, GOLD, phase=0.0, tag="crown")
    return pack(name, [b, g], glow=[name + "_Glow"], base=name + "_Booth")


CARS = {"Car_Red": (RED, RED_DARK, "car"), "Car_Blue": (BLUE, H("#2A63C8"), "car"), "Car_Green": (GREEN, GREEN_DARK, "car"),
        "DeliveryVan": (WHITE, H("#DDE3EC"), "van")}


def vehicle(name):
    col, dark, kind = CARS[name]
    rng = random.Random(len(name))
    b, g = lh.MeshBuilder(name + "_Body", rng), lh.MeshBuilder(name + "_Glow", rng)
    W, L = 3.2, (6.0 if kind == "car" else 7.0)
    b.box((-W, -L, 0.9), (W, L, 3.0), lh.by_normal(col, col, dark), tag="body")
    if kind == "car":
        b.add([(-W + 0.3, -1.8, 2.99), (W - 0.3, -1.8, 2.99), (W - 0.3, 3.2, 2.99), (-W + 0.3, 3.2, 2.99),
               (-W + 0.6, -0.8, 5.0), (W - 0.6, -0.8, 5.0), (W - 0.6, 2.6, 5.0), (-W + 0.6, 2.6, 5.0)],
              [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], col, tag="cabin")
        for x in (-W + 0.42, W - 0.42):                    # side windows
            b.box((x - 0.12 if x > 0 else x - 0.06, -0.9, 3.3), (x + 0.06 if x > 0 else x + 0.12, 2.5, 4.6), WINDOW, tag="window")
        b.add([(-W + 0.55, -1.75, 3.2), (W - 0.55, -1.75, 3.2), (W - 0.75, -0.85, 4.75), (-W + 0.75, -0.85, 4.75),
               (-W + 0.55, -1.55, 3.2), (W - 0.55, -1.55, 3.2), (W - 0.75, -0.65, 4.75), (-W + 0.75, -0.65, 4.75)],
              [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], WINDOW, tag="windshield")
        b.ico((0, 0.9, 5.0), (2.1, 1.6, 0.4), SNOW, subdiv=1, tag="snow")
        b.box((-W - 0.05, -L - 0.1, 1.0), (W + 0.05, -L + 0.4, 1.6), H("#B8BEC9"), tag="bumper")
        b.box((-W - 0.05, L - 0.4, 1.0), (W + 0.05, L + 0.1, 1.6), H("#B8BEC9"), tag="bumper")
    else:
        b.box((-W, -L + 3.2, 2.95), (W, L, 7.4), lh.by_normal(SNOW, col, dark), tag="cargo")
        b.add([(-W, -L, 2.99), (W, -L, 2.99), (W, -L + 3.21, 2.99), (-W, -L + 3.21, 2.99),
               (-W, -L + 1.6, 5.8), (W, -L + 1.6, 5.8), (W, -L + 3.21, 5.8), (-W, -L + 3.21, 5.8)],
              [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], RED, tag="cab")
        b.add([(-W + 0.4, -L - 0.04, 3.3), (W - 0.4, -L - 0.04, 3.3), (W - 0.4, -L + 1.45, 5.55), (-W + 0.4, -L + 1.45, 5.55),
               (-W + 0.4, -L + 0.2, 3.3), (W - 0.4, -L + 0.2, 3.3), (W - 0.4, -L + 1.65, 5.55), (-W + 0.4, -L + 1.65, 5.55)],
              [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], WINDOW, tag="windshield")
        for sx in (-1, 1):                                 # side logo: a present
            x = sx * (W + 0.05)
            xs = sorted((x, x - sx * 0.2))
            b.box((xs[0], -0.6, 3.6), (xs[1], 2.6, 6.6), RED, tag="logo")
            xs2 = sorted((x + sx * 0.06, x - sx * 0.1))
            b.box((xs2[0], 0.8, 3.6), (xs2[1], 1.2, 6.6), GOLD, tag="logo")
            b.box((xs2[0], -0.6, 4.9), (xs2[1], 2.6, 5.3), GOLD, tag="logo")
        b.ico((0, 2.0, 7.4), (2.6, 3.6, 0.35), SNOW, subdiv=1, tag="snow")
        b.box((-W - 0.05, -L - 0.1, 1.0), (W + 0.05, -L + 0.4, 1.6), H("#B8BEC9"), tag="bumper")
        b.box((-W - 0.05, L - 0.4, 1.0), (W + 0.05, L + 0.1, 1.6), H("#B8BEC9"), tag="bumper")
    for sx in (-1, 1):
        for y in (-L + 1.8, L - 1.8):
            b.cyl((sx * (W - 0.55), y, 1.15), (sx * (W + 0.25), y, 1.15), 1.15, 12, TYRE, phase=0.0, tag="tyre")
            b.cyl((sx * (W + 0.2), y, 1.15), (sx * (W + 0.35), y, 1.15), 0.55, 8, HUB, phase=0.0, tag="hub")
        g.box((sx * (W - 1.0) - 0.6, -L - 0.12, 2.0), (sx * (W - 1.0) + 0.6, -L + 0.1, 2.7), H("#FFF6D8"), tag="head")
        g.box((sx * (W - 0.8) - 0.5, L - 0.1, 2.0), (sx * (W - 0.8) + 0.5, L + 0.12, 2.6), H("#FF3B3B"), tag="tail")
    return pack(name, [b, g], classes={name + "_Body": "medium"}, glow=[name + "_Glow"], base=name + "_Body")


MAKERS = {**{n: road_tile for n in ROADS}, **{n: stall for n in STALLS}, **{n: shed for n in SHEDS},
          "Igloo": igloo, "ClockTower": clock_tower, "TreePlaza": tree_plaza, "IceRink": ice_rink,
          "Hydrant": hydrant, "StopSign": stop_sign, "TrafficLight": traffic_light, "BusStop": bus_stop,
          "PhoneBooth": phone_booth, **{n: vehicle for n in CARS}}

if __name__ == "__main__":
    names = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(MAKERS)
    for n in names:
        try:
            bb.build(n, maker=MAKERS[n], out_root=OUT)
        except Exception as e:          # keep going; report at the end
            import traceback; traceback.print_exc()
            print(f"[bld] {n:24s} ERROR {e}")
