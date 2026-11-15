"""Sleighbound buildings: suburban candy houses and downtown apartment blocks, in variants.

  blender -b --factory-startup --python tools/blender/build_buildings.py            (all variants)
  blender -b --factory-startup --python tools/blender/build_buildings.py -- CandyHouse_Pink Apartment_Grey

Built with the LihFolk house method (vault: House Construction Method - Modular Kit Workflow):
modules split by collision / material, one shared bottom-centre origin, gate per module, whole-building
floating-shell scan (must be 0). House frame: front faces -Y, ridge along Y. 1 unit = 1 stud.
Each variant is a dict of parameters; the base variants ("CandyHouse", "Apartment") are the first builds.
"""
import os, sys, math, json, random
import bpy
from mathutils import Vector, Matrix

SKILL = r"C:\Users\weede\.claude\plugins\cache\lihfolk\lihfolk\2.5.0\skills\roblox-blender-modeling\scripts"
sys.path.append(SKILL)
import lihfolk_bpy as lf
import lihfolk_curves as lc
import lihfolk_house as lh

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "assets", "buildings")
H = lc.hex_rgb

SNOW, SNOW_SIDE, SNOW_UNDER = H("#F4F9FF"), H("#DCE6F4"), H("#C9D6E8")
CREAM, CREAM_DARK = H("#FFF1DC"), H("#E2CDB0")
WHITE = H("#FFF6F0")
GLASS = H("#FFD27A")
IRON = H("#2F333C")
GOLD = H("#FFC840")
LIGHTS = [H("#E8344E"), H("#3CC46B"), H("#FFC840"), H("#3C8DFF"), H("#FF82C4")]


def snowy(side, under=None):
    return lh.by_normal(SNOW, side, under or side, up_min=0.5)


def sorted_box(f, lo, hi):
    p0, p1 = f.p(*lo), f.p(*hi)
    return tuple(min(p0[i], p1[i]) for i in range(3)), tuple(max(p0[i], p1[i]) for i in range(3))


def fb(f, b, lo, hi, col):
    """Box in face coordinates (u, z, d)."""
    a, c = sorted_box(f, lo, hi)
    b.box(a, c, col)


# ================================================================ suburban candy house
HOUSES = {
    "CandyHouse": dict(seed=7, hx=11.0, hy=9.0, pitch=38, storeys=1,
                       siding=["#9FE3CF", "#93DAC5", "#A9EAD6"], groove="#5E9C8C", corner="#FFF6F0",
                       roof="#D8364F", roof_under="#9A1E30", shutters=("#FF82C4", "#E0559F"),
                       door=["#E8344E", "#D42C45"], chimney=["#D8364F", "#FFF6F0"], chim_side=1,
                       base="#B9A6A0"),
    "CandyHouse_Pink": dict(seed=17, hx=12.0, hy=9.5, pitch=42, storeys=1,
                            siding=["#FFB3C7", "#FFA6BD", "#FFBFD0"], groove="#C46F86", corner="#FFF6F0",
                            roof="#2E8A55", roof_under="#1F6B3F", shutters=("#46D6B0", "#2FA98A"),
                            door=["#2E8A55", "#24934C"], chimney=["#E8344E", "#FFF6F0"], chim_side=-1,
                            base="#C9B8B0"),
    "CandyHouse_Lavender": dict(seed=27, hx=9.5, hy=8.0, pitch=46, storeys=1,
                                siding=["#C9B8F2", "#BDABEA", "#D3C4F7"], groove="#7E6BB8", corner="#FFF6F0",
                                roof="#3A4E8C", roof_under="#26355F", shutters=("#FFC840", "#D99A20"),
                                door=["#FFC840", "#E8B032"], chimney=["#2E8A55", "#FFF6F0"], chim_side=1,
                                base="#B0A8C0"),
    "CandyHouse_Butter": dict(seed=37, hx=11.5, hy=9.0, pitch=34, storeys=2,
                              siding=["#FFE59A", "#FFDC85", "#FFEAAB"], groove="#C9A24C", corner="#FFF6F0",
                              roof="#B8243C", roof_under="#7E1A2B", shutters=("#E8344E", "#B8243C"),
                              door=["#3C8DFF", "#2A63C8"], chimney=["#E8344E", "#FFF6F0"], chim_side=-1,
                              base="#BFAE98"),
    "CandyHouse_Gingerbread": dict(seed=47, hx=10.5, hy=8.5, pitch=44, storeys=1,
                                   siding=["#B8733A", "#AA6A35", "#C27D43"], groove="#6E4120", corner="#FFFFFF",
                                   roof="#FF82C4", roof_under="#E0559F", shutters=("#FFFFFF", "#F0E6E6"),
                                   door=["#E8344E", "#D42C45"], chimney=["#FF82C4", "#FFFFFF"], chim_side=1,
                                   base="#8E5527"),
    "CandyHouse_Bungalow": dict(seed=57, hx=9.0, hy=7.5, pitch=30, storeys=1,
                                siding=["#A9D4F5", "#9CC9EE", "#B6DDF8"], groove="#5F8DB3", corner="#FFF6F0",
                                roof="#E8344E", roof_under="#9A1E30", shutters=("#FFFFFF", "#E8E0D6"),
                                door=["#FFC840", "#E8B032"], chimney=["#FFF6F0", "#E8344E"], chim_side=1,
                                base="#B0B6C0"),
}


def candy_house(name, v):
    rng = random.Random(v["seed"])
    t, hx, hy = 1.0, v["hx"], v["hy"]
    plinth, storey = 0.8, 12.0
    eave = plinth + storey * v["storeys"]
    pitch = v["pitch"]
    SID = [H(c) for c in v["siding"]]
    GROOVE, CORNER = H(v["groove"]), H(v["corner"])
    ROOF, ROOF_UNDER = H(v["roof"]), H(v["roof_under"])
    SHUT = tuple(H(c) for c in v["shutters"])
    DOOR = [H(c) for c in v["door"]]

    base = lh.MeshBuilder(name + "_Foundation", rng)
    lh.foundation(base, hx, hy, t / 2, height=plinth, margin=0.3, colour=H(v["base"]))

    # ---- opening plan: (name, u, width, z0, z1, shutters), checked before modelling
    door_w, door_h, win_w, win_h = 4.0, 8.0, 2.8, 4.2
    Lh = hx + t / 2
    door_half = lh.opening_footprint(door_w)
    u_front = round((door_half + Lh - 1.0) / 2 + 0.3, 2)
    plan = {k: [] for k in ("-Y", "+Y", "-X", "+X")}
    for s in range(v["storeys"]):
        zw = plinth + s * storey + 3.1
        if s == 0:
            plan["-Y"].append(("door", 0.0, door_w, plinth, plinth + door_h, False))
        else:
            plan["-Y"].append((f"mid{s}", 0.0, win_w, zw, zw + win_h, False))
        for side in (-1, 1):
            plan["-Y"].append((f"f{s}{side}", side * u_front, win_w, zw, zw + win_h, True))
            plan["+Y"].append((f"b{s}{side}", side * round(Lh * 0.48, 2), win_w, zw, zw + win_h, False))
        side_len = 2 * hy + t
        su = [-round(hy * 0.5, 2), round(hy * 0.5, 2)] if side_len > 15 else [0.0]
        for key in ("-X", "+X"):
            for u in su:
                plan[key].append((f"s{s}{u}", u, win_w, zw, zw + win_h, True))
    plan["-Y"].append(("attic", 0.0, 2.6, eave + 1.8, eave + 4.4, False))
    lens = {"-Y": 2 * hx + t, "+Y": 2 * hx + t, "-X": 2 * hy + t, "+X": 2 * hy + t}
    for key, items in plan.items():                     # check each storey's row; drop its shutters if they don't fit
        rows = {}
        for i, it in enumerate(items):
            if it[4] <= eave:
                rows.setdefault(round(plinth + 3.1 if it[0] == "door" else it[3], 2), []).append(i)
        for idxs in rows.values():
            probs = lambda: lh.check_wall_layout(lens[key], [(items[i][0], items[i][1],
                                                              lh.opening_footprint(items[i][2], shutters=items[i][5])) for i in idxs])
            if probs():
                for i in idxs:
                    items[i] = items[i][:5] + (False,)
            assert not probs(), (name, key, probs())
    openings = {k: [(u - w / 2, u + w / 2, z0, z1) for n, u, w, z0, z1, s in vv] for k, vv in plan.items()}

    walls = lh.MeshBuilder(name + "_Walls", rng)
    gable = lh.Gable(hx + t / 2, eave, pitch)
    faces, ops, ch = lh.coursed_walls(walls, hx, hy, thickness=t, z0=plinth, eave_z=eave, course_h=0.9,
                                      block_len=(60, 61), gap=0.07, colours=SID, mortar=GROOVE, quoin=CORNER,
                                      quoin_len=(1.4, 1.4), proud=0.05, gable=gable, openings=openings)
    if v["storeys"] > 1:      # a trim band between the storeys
        for key, f in faces.items():
            half = (2 * hx + t) / 2 if key in ("-Y", "+Y") else (2 * hy + t) / 2
            zb = plinth + storey
            fb(f, walls, (-half - (0.25 if key in ("-Y", "+Y") else 0), zb - 0.3, -0.1),
               (half + (0.25 if key in ("-Y", "+Y") else 0), zb + 0.3, 0.25), snowy(CORNER))

    # The gable courses step under the roof slope and leave see-through notches. Fix: a back infill triangle
    # (behind the attic glass) plus a bargeboard along each slope covering the steps.
    ue = hx + t / 2
    ridge = gable.ridge_z
    for key in ("-Y", "+Y"):
        f = faces[key]
        walls.prism(f.p(-ue + 0.05, eave - 0.05, -t + 0.05), f.p(-ue + 0.05, eave - 0.05, -0.7),
                    f.p(ue - 0.05, eave - 0.05, -t + 0.05), f.p(ue - 0.05, eave - 0.05, -0.7),
                    f.p(0, ridge - 0.08, -t + 0.05), f.p(0, ridge - 0.08, -0.7), GROOVE, tag="infill")
        for s in (-1, 1):
            u0, u1 = s * (ue + 0.4), s * 0.002
            z0t, z1t = gable.under(u0) - 0.01, ridge - 0.01
            vs = [f.p(u, z, d) for d in (-0.15, 0.3) for u, z in ((u0, z0t - 1.15), (u1, z1t - 1.15), (u1, z1t), (u0, z0t))]
            walls.add(vs, [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)],
                      CORNER, tag="barge")

    roof = lh.MeshBuilder(name + "_Roof", rng)
    R = lh.gable_roof(roof, gable, hy + t / 2, thickness=0.9, overhang_x=1.6, overhang_y=1.4, colour=ROOF,
                      underside=ROOF_UNDER, style="slab",
                      snow=dict(thick=1.3, extra_x=0.5, extra_y=0.35, lip=0.5, colours=(SNOW, SNOW_SIDE, SNOW_UNDER)))
    for side in (-1, 1):
        x = side * (R["snow_xe"] - 0.35)
        lh.icicle_row(roof, (x, -R["snow_ye"] + 0.5, 0), (x, R["snow_ye"] - 0.5, 0), int(hy * 1.8), colour=H("#CFF2FF"),
                      z_at=lambda X, Y: R["snow_under"](X), radius=(0.18, 0.25), lengths=(0.6, 0.9, 1.2, 1.6))

    chim = lh.MeshBuilder(name + "_Chimney", rng)
    cx, cy, cs = v["chim_side"] * hx * 0.49, hy * 0.39, 2.4
    lh.chimney(chim, cx, cy, gable.under(abs(cx) + cs / 2 + 0.3) - 0.6, gable.ridge_z + 2.2, size=cs, course_h=0.7,
               colours=[H(c) for c in v["chimney"]], crown=WHITE, flue=H("#3B3F4A"), cap_snow=(SNOW, SNOW_SIDE))

    trim = lh.MeshBuilder(name + "_Trim", rng)
    trim2 = lh.MeshBuilder(name + "_Trim2", rng) if v["storeys"] > 1 else None   # upper storey: keeps each under 10k tris
    glow = lh.MeshBuilder(name + "_Glow", rng)
    wcol = dict(frame=WHITE, mullion=WHITE, glass=GLASS)
    cap = dict(top=SNOW, front=WHITE, under=CREAM_DARK)
    for key, items in plan.items():
        for (n, u, w, z0, z1, shut), (a, b, sz0, sz1) in zip(items, ops[key]):
            if n == "door":
                continue
            tb = trim2 if (trim2 and plinth + storey <= sz0 < eave) else trim
            lh.window(tb, glow, faces[key], u, (sz0 + sz1) / 2, b - a, sz1 - sz0, recess=t / 2, colours=wcol,
                      shutters=SHUT if shut else None, cap=None if n == "attic" else cap, sill_top=SNOW, mullions=True)

    door = lh.MeshBuilder(name + "_Door", rng)
    d0, d1, dz0, dz1 = ops["-Y"][0]
    f = faces["-Y"]
    lh.door(door, f, 0.0, dz0, d1 - d0, dz1 - dz0, recess=0.3, planks=4, colours=DOOR, batten=GOLD, frame=WHITE, knob=GOLD)
    lh.steps(door, f, 0.0, 5.2, z_top=plinth, n=2, run=1.0, colours=[H("#C9B8B0"), H("#B9A6A0")])
    zb = dz1 + 0.55
    cw, chh, out = 6.2, 1.5, 2.2
    col = lambda c, n, co: SNOW if n.z > 0.3 else (WHITE if n.dot(f.out) > 0.5 else ROOF_UNDER)
    door.prism(f.p(-cw / 2, zb, -0.4), f.p(-cw / 2, zb, out), f.p(cw / 2, zb, -0.4), f.p(cw / 2, zb, out),
               f.p(0, zb + chh, -0.4), f.p(0, zb + chh, out), col, tag="canopy")
    for s in (-1, 1):
        a, c = sorted_box(f, (s * 2.6 - 0.15, zb - 1.2, -0.2), (s * 2.6 + 0.15, zb + 0.02, out - 0.4))
        door.box(a, c, WHITE, tag="bracket")
    wz = dz0 + (dz1 - dz0) * 0.72
    for k in range(10):
        a = 2 * math.pi * k / 10
        door.ico(f.p(0.75 * math.cos(a), wz + 0.75 * math.sin(a), 0.1), (0.32, 0.32, 0.32),
                 H("#1F6B3F") if k % 2 else H("#2E8A55"), subdiv=1, tag="wreath")
    door.ico(f.p(0, wz - 0.75, 0.3), (0.26, 0.26, 0.26), H("#D81E3A"), subdiv=1, tag="wreath")

    lights = lh.MeshBuilder(name + "_Lights", rng)
    k = 0
    for side in (-1, 1):
        x = side * (R["xe"] - 0.45)
        n = int(R["ye"] * 1.4)
        for i in range(n):
            y = -R["ye"] + 0.6 + i * (2 * R["ye"] - 1.2) / (n - 1)
            lights.ico((x, y, R["under"](x) - 0.12), (0.22, 0.22, 0.3), LIGHTS[k % 5], subdiv=1, tag="bulb"); k += 1
    n = int(R["xe"] * 1.4)
    for i in range(n):
        x = -R["xe"] + 0.5 + i * (2 * R["xe"] - 1.0) / (n - 1)
        lights.ico((x, -R["ye"] + 0.35, R["under"](x) - 0.12), (0.22, 0.22, 0.3), LIGHTS[k % 5], subdiv=1, tag="bulb"); k += 1

    mods = [b.to_object() for b in (base, walls, roof, chim, trim, trim2, glow, door, lights) if b is not None]
    soft = lambda w: dict(style="soft", bevel_width=w, smooth_angle=60)
    finish = {name + "_Walls": dict(style="faceted"), name + "_Lights": dict(style="faceted"),
              name + "_Glow": dict(style="faceted"), name + "_Roof": soft(0.08), name + "_Chimney": soft(0.06),
              name + "_Trim": soft(0.04), name + "_Trim2": soft(0.04), name + "_Door": soft(0.04),
              name + "_Foundation": soft(0.08)}
    classes = {name + "_Walls": "building", name + "_Roof": "building", name + "_Chimney": "medium",
               name + "_Trim": "building", name + "_Trim2": "building", name + "_Glow": "small", name + "_Door": "medium",
               name + "_Lights": "medium", name + "_Foundation": "small"}
    return mods, finish, classes, (name + "_Foundation",), (name + "_Glow",)


# ================================================================ downtown apartment
APARTMENTS = {
    "Apartment": dict(seed=21, W=32.0, D=22.0, upper=4, brick=["#B5523B", "#A94B36", "#BD5A42"],
                      trim="#FFF1DC", trim_dark="#E2CDB0", awning=("#E8344E", "#FFF6F0"),
                      shop=("#2E8A55", "#1F6B3F"), sign="#FFC840", balconies=[-7.5, 7.5], balc_w=7.0,
                      tower=True, billboard="#E8344E", hut_side=-1, side_cols=[-6.5, -2.2, 2.2, 6.5]),
    "Apartment_Cream": dict(seed=31, W=28.0, D=20.0, upper=4, brick=["#D9B98A", "#CFAE7E", "#E0C296"],
                            trim="#FFFFFF", trim_dark="#E8E0D6", awning=("#2E8A55", "#FFF6F0"),
                            shop=("#B8243C", "#8C1A2D"), sign="#FFFFFF", balconies=[0.0], balc_w=7.0,
                            tower=False, billboard="#2E8A55", hut_side=1),
    "Apartment_Grey": dict(seed=41, W=30.0, D=22.0, upper=6, brick=["#8E95A3", "#858C9A", "#979EAC"],
                           trim="#FFF1DC", trim_dark="#E2CDB0", awning=("#E8344E", "#FFF6F0"),
                           shop=("#26355F", "#1B2747"), sign="#FFC840", balconies=[-10.0, 10.0], balc_w=4.4,
                           tower=True, billboard="#3C8DFF", hut_side=-1),
    "Apartment_Green": dict(seed=51, W=34.0, D=24.0, upper=3, brick=["#3E7D5A", "#367250", "#468863"],
                            trim="#FFF1DC", trim_dark="#E2CDB0", awning=("#FFC840", "#B8243C"),
                            shop=("#B8243C", "#8C1A2D"), sign="#FFC840", balconies=[], balc_w=7.0,
                            tower=True, billboard="#FFC840", hut_side=1),
    "Apartment_Plum": dict(seed=61, W=26.0, D=20.0, upper=5, brick=["#6A58D8", "#5E4DC6", "#7564E0"],
                           trim="#FFF6F0", trim_dark="#E6DCEF", awning=("#FF82C4", "#FFF6F0"),
                           shop=("#D99A20", "#A87515"), sign="#FF82C4", balconies=[-7.5, 7.5], balc_w=4.4,
                           tower=False, billboard="#FF82C4", hut_side=-1),
    "Apartment_Tower": dict(seed=71, W=30.0, D=24.0, upper=8, brick=["#5B6F8C", "#52657F", "#647999"],
                            trim="#FFFFFF", trim_dark="#D6DCE6", awning=("#3C8DFF", "#FFF6F0"),
                            shop=("#26355F", "#1B2747"), sign="#FFFFFF", balconies=[-10.0, 10.0], balc_w=4.4,
                            tower=True, billboard="#E8344E", hut_side=1),
    # corner shops: 2 floors, the rooftop billboard is the shop sign
    "Shop_Candy": dict(seed=81, W=26.0, D=18.0, upper=1, brick=["#FFB3C7", "#FFA6BD", "#FFBFD0"],
                       trim="#FFFFFF", trim_dark="#F0D6DE", awning=("#E8344E", "#FFFFFF"),
                       shop=("#E8344E", "#B8243C"), sign="#FFFFFF", balconies=[], balc_w=4.4,
                       tower=False, billboard="#E8344E", hut_side=1),
    "Shop_Toys": dict(seed=82, W=26.0, D=18.0, upper=1, brick=["#7FB2F0", "#73A6E6", "#8BBDF6"],
                      trim="#FFF6F0", trim_dark="#DCE6F4", awning=("#FFC840", "#3C8DFF"),
                      shop=("#FFC840", "#D99A20"), sign="#E8344E", balconies=[], balc_w=4.4,
                      tower=False, billboard="#FFC840", hut_side=-1),
    "Shop_Bakery": dict(seed=83, W=26.0, D=18.0, upper=1, brick=["#F3DDB4", "#EBD2A6", "#F8E5C2"],
                        trim="#FFFFFF", trim_dark="#E8D8C0", awning=("#8E5527", "#FFF1DC"),
                        shop=("#8E5527", "#6E4120"), sign="#FFC840", balconies=[], balc_w=4.4,
                        tower=False, billboard="#B8733A", hut_side=1),
    "Shop_Cocoa": dict(seed=84, W=26.0, D=18.0, upper=1, brick=["#8E5A3C", "#7E4F34", "#9A6444"],
                       trim="#FFF1DC", trim_dark="#E2CDB0", awning=("#2E8A55", "#FFF1DC"),
                       shop=("#2E8A55", "#1F6B3F"), sign="#FFF1DC", balconies=[], balc_w=4.4,
                       tower=False, billboard="#2E8A55", hut_side=-1),
    # delivery depot: wide, 2 floors, red and navy
    "PostOffice": dict(seed=91, W=38.0, D=24.0, upper=1, brick=["#C23B3B", "#B33434", "#CC4646"],
                       trim="#FFFFFF", trim_dark="#E2CDB0", awning=("#26355F", "#FFFFFF"),
                       shop=("#26355F", "#1B2747"), sign="#FFC840", balconies=[], balc_w=4.4,
                       tower=False, billboard="#26355F", hut_side=1),
}


def spaced(n, step):
    return [round((i - (n - 1) / 2) * step, 3) for i in range(n)]


def apartment(name, v):
    rng = random.Random(v["seed"])
    t, W, D = 1.0, v["W"], v["D"]
    hxo, hyo = W / 2, D / 2
    floors = [0.0] + [13.0 + 11.0 * i for i in range(v["upper"])]
    top = floors[-1] + 11.0
    BRICK = [H(c) for c in v["brick"]]
    TRIM, TRIM_DARK = H(v["trim"]), H(v["trim_dark"])
    SHOP, SHOP_DARK = (H(c) for c in v["shop"])
    AW = tuple(H(c) for c in v["awning"])
    faces = lh.house_faces(hxo - t / 2, hyo - t / 2, t / 2)
    urange = {"-Y": (-hxo, hxo), "+Y": (-hxo, hxo), "-X": (-(hyo - t), hyo - t), "+X": (-(hyo - t), hyo - t)}

    cols_long = spaced(int((W - 7) / 5) + 1, 5.0)
    cols_side = v.get("side_cols") or spaced(int((D - 8.5) / 4.35) + 1, 4.35)
    win_w = 3.0
    sc = hxo - 6.5                                           # shop window centre
    sw = min(8.5, 2 * min(sc - 3.7, (hxo - 1.8) - sc))      # shop window width (3.7: awning clears the door canopy)
    openings = {k: [] for k in faces}
    for fi, fz in enumerate(floors):
        for key in faces:
            cols = cols_long if key in ("-Y", "+Y") else cols_side
            if fi == 0 and key == "-Y":
                openings[key] += [(-sc, sw, 1.0, 9.5, "shop"), (sc, sw, 1.0, 9.5, "shop"), (0.0, 4.4, 0.0, 8.6, "door")]
                continue
            z0 = fz + (3.4 if fi == 0 else 2.8)
            for u in cols:
                openings[key].append((u, win_w, z0, z0 + 5.2, "win"))

    walls = lh.MeshBuilder(name + "_Walls", rng)
    for key, f in faces.items():
        umin, umax = urange[key]
        ops = openings[key]
        cuts = sorted({umin, umax} | {u - w / 2 for u, w, *_ in ops} | {u + w / 2 for u, w, *_ in ops})
        for a, b in zip(cuts, cuts[1:]):
            if b - a < 1e-4:
                continue
            mid = (a + b) / 2
            holes = sorted((z0, z1) for u, w, z0, z1, _ in ops if u - w / 2 - 1e-6 <= mid <= u + w / 2 + 1e-6)
            z = 0.0
            for z0, z1 in holes + [(top, top)]:
                if z0 - z > 1e-3:   # 1 mm apart, or cleanup's merge-by-distance welds neighbours into non-manifold mess
                    f.box(walls, (a + 0.001, z + 0.001, -t), (b - 0.001, z0 - 0.001, 0.0),
                          lh.jitter(rng, rng.choice(BRICK), 0.04), tag="wall")
                z = max(z, z1)

    trim = lh.MeshBuilder(name + "_Trim", rng)
    glow = lh.MeshBuilder(name + "_Glow", rng)
    for key, f in faces.items():
        for u, w, z0, z1, kind in openings[key]:
            glow.box(*sorted_box(f, (u - w / 2 - 0.05, z0 - 0.05, -t / 2 - 0.08), (u + w / 2 + 0.05, z1 + 0.05, -t / 2 + 0.08)),
                     GLASS, tag="glass")
            if kind == "door":
                continue
            if kind == "win":
                fb(f, trim, (u - w / 2 - 0.45, z0 - 0.5, -0.25), (u + w / 2 + 0.45, z0 + 0.02, 0.5), snowy(TRIM, TRIM_DARK))
                fb(f, trim, (u - w / 2 - 0.35, z1 - 0.02, -0.15), (u + w / 2 + 0.35, z1 + 0.7, 0.32), snowy(TRIM))
                fb(f, trim, (u - 0.1, z0 - 0.05, -t / 2 - 0.05), (u + 0.1, z1 + 0.05, 0.12), TRIM)
                fb(f, trim, (u - w / 2 - 0.05, z0 + (z1 - z0) * 0.62 - 0.08, -t / 2 - 0.05),
                   (u + w / 2 + 0.05, z0 + (z1 - z0) * 0.62 + 0.08, 0.1), TRIM)
            else:
                for du in (-w / 2, -w / 6, w / 6, w / 2):
                    fb(f, trim, (u + du - 0.14, z0 - 0.05, -t / 2 - 0.05), (u + du + 0.14, z1 + 0.05, 0.18), SHOP)
                fb(f, trim, (u - w / 2 - 0.05, z0 + 6.0 - 0.12, -t / 2 - 0.05), (u + w / 2 + 0.05, z0 + 6.0 + 0.12, 0.15), SHOP)
                fb(f, trim, (u - w / 2 - 0.4, z0 - 0.4, -0.25), (u + w / 2 + 0.4, z0 + 0.02, 0.45), snowy(SHOP_DARK))
    for zc, h, d in [(z, 0.7, 0.45) for z in floors[1:]] + [(top - 0.6, 1.2, 0.9)]:
        for key, f in faces.items():
            umin, umax = urange[key]
            ext = d if key in ("-Y", "+Y") else 0.0
            fb(f, trim, (umin - ext, zc - h / 2, -0.2), (umax + ext, zc + h / 2, d), snowy(TRIM, TRIM_DARK))
    for sx in (-1, 1):
        for sy in (-1, 1):
            xs = sorted((sx * (hxo - 1.3), sx * (hxo + 0.25))); ys = sorted((sy * (hyo - 1.3), sy * (hyo + 0.25)))
            trim.box((xs[0], ys[0], 0.0), (xs[1], ys[1], top - 1.2), TRIM_DARK, tag="pilaster")

    balc = lh.MeshBuilder(name + "_Balconies", rng)
    f = faces["-Y"]
    bw, dep, rail = v["balc_w"], 2.4, 3.2
    for fz in floors[1:]:
        for uc in v["balconies"]:
            fb(f, balc, (uc - bw / 2, fz - 0.25, -0.3), (uc + bw / 2, fz + 0.35, dep), snowy(TRIM, TRIM_DARK))
            n = max(4, int(bw / 1.05) + 1)
            for i in range(n):
                uu = uc - bw / 2 + 0.15 + i * (bw - 0.3) / (n - 1)
                fb(f, balc, (uu - 0.09, fz + 0.3, dep - 0.28), (uu + 0.09, fz + rail + 0.02, dep - 0.1), IRON)
            for s in (-1, 1):
                uu = uc + s * (bw / 2 - 0.15)
                fb(f, balc, (uu - 0.09, fz + 0.3, 0.6), (uu + 0.09, fz + rail + 0.02, 0.78), IRON)
                fb(f, balc, (uu - 0.1, fz + rail, -0.1), (uu + 0.1, fz + rail + 0.25, dep - 0.08), snowy(IRON))
            fb(f, balc, (uc - bw / 2, fz + rail, dep - 0.32), (uc + bw / 2, fz + rail + 0.25, dep - 0.06), snowy(IRON))
    if not v["balconies"]:      # flower boxes under the first-floor windows instead, so the module is never empty
        fz = floors[1]
        for u in cols_long:
            fb(f, balc, (u - 1.8, fz + 1.7, -0.2), (u + 1.8, fz + 2.3, 0.9), snowy(SHOP))
            for k in range(3):
                balc.ico(f.p(u - 1.0 + k, fz + 2.45, 0.35), (0.35, 0.3, 0.3), H("#1F6B3F"), subdiv=1, tag="holly")

    shop = lh.MeshBuilder(name + "_Shopfront", rng)
    run, drop = 3.4, 1.4
    L = math.hypot(run, drop)
    M3 = Matrix.Rotation(math.atan2(-drop, -run), 3, "X")       # local +Y runs out from the wall and down
    for u0, u1 in ((-sc - sw / 2 - 0.25, -sc + sw / 2 + 0.25), (sc - sw / 2 - 0.25, sc + sw / 2 + 0.25)):
        n = max(5, int(round(u1 - u0)))
        stw = (u1 - u0) / n
        for i in range(n):
            x = u0 + (i + 0.5) * stw
            colr = AW[i % 2]
            shop.obox(Vector((x, -hyo + 0.2 - run / 2, 10.9 - drop / 2)), (stw - 0.02, L + 0.4, 0.18), M3, colr, tag="awning")
            shop.box((x - stw / 2 + 0.01, -hyo - run - 0.12, 8.85), (x + stw / 2 - 0.01, -hyo - run + 0.1, 9.7), colr, tag="valance")
    fb(f, shop, (-3.2, 9.4, -0.3), (3.2, 9.9, 2.8), snowy(SHOP, SHOP_DARK))
    for s in (-1, 1):
        fb(f, shop, (s * 3.0 - 0.12, 7.9, -0.2), (s * 3.0 + 0.12, 9.42, 2.4), IRON)
    fb(f, shop, (-(hxo - 1.4), 11.0, -0.2), (hxo - 1.4, 12.4, 0.3), snowy(SHOP_DARK))
    fb(f, shop, (-(hxo - 1.8), 11.25, 0.29), (hxo - 1.8, 12.15, 0.4), H(v["sign"]))
    lh.door(shop, f, 0.0, 0.0, 4.4, 8.6, recess=0.3, planks=2, colours=[SHOP, SHOP_DARK], batten=GOLD, frame=TRIM, knob=GOLD)

    roof = lh.MeshBuilder(name + "_Roof", rng)
    roof.box((-hxo + t - 0.2, -hyo + t - 0.2, top - 0.7), (hxo - t + 0.2, hyo - t + 0.2, top), snowy(H("#7A7F8C")), tag="slab")
    pt, ph = 0.8, 2.4
    for (x0, y0, x1, y1) in ((-hxo, -hyo, hxo, -hyo + pt), (-hxo, hyo - pt, hxo, hyo),
                             (-hxo, -hyo + pt + 0.01, -hxo + pt, hyo - pt - 0.01), (hxo - pt, -hyo + pt + 0.01, hxo, hyo - pt - 0.01)):
        roof.box((x0, y0, top - 0.05), (x1, y1, top + ph), lh.jitter(rng, BRICK[0], 0.03), tag="parapet")
        roof.box((x0 - 0.15, y0 - 0.15, top + ph - 0.02), (x1 + 0.15, y1 + 0.15, top + ph + 0.4), snowy(TRIM, TRIM_DARK), tag="coping")
    hs = v["hut_side"]
    if v["tower"]:
        tx, ty = -hs * (hxo - 6.0), 3.0
        for sx in (-1, 1):
            for sy in (-1, 1):
                roof.box((tx + sx * 2.2 - 0.25, ty + sy * 2.2 - 0.25, top - 0.05), (tx + sx * 2.2 + 0.25, ty + sy * 2.2 + 0.25, top + 6.0), IRON, tag="leg")
        roof.box((tx - 2.9, ty - 2.9, top + 5.95), (tx + 2.9, ty + 2.9, top + 6.5), IRON, tag="deck")
        roof.cyl((tx, ty, top + 6.45), (tx, ty, top + 12.4), 2.8, 12, snowy(H("#8E5A34"), H("#6B4630")),
                 cap_in=SNOW, cap_out=SNOW, phase=0.0, tag="tank")
        for z in (top + 7.6, top + 10.6):
            roof.cyl((tx, ty, z), (tx, ty, z + 0.3), 2.92, 12, IRON, phase=0.0, tag="hoop")
        roof.cone((tx, ty, top + 12.3), (tx, ty, top + 14.6), 3.15, 12, snowy(H("#3B3F4A")), tag="cap")
    hx0 = hs * (hxo - 3.0)
    hxa, hxb = sorted((hx0, hx0 - hs * 6.0))
    hy0, hy1 = -hyo + 3.5, -hyo + 8.5
    roof.box((hxa, hy0, top - 0.05), (hxb, hy1, top + 7.0), lh.jitter(rng, BRICK[1], 0.03), tag="hut")
    roof.box((hxa - 0.4, hy0 - 0.4, top + 7.0), (hxb + 0.4, hy1 + 0.4, top + 7.6), snowy(TRIM, TRIM_DARK), tag="hutroof")
    hc = (hxa + hxb) / 2
    roof.box((hc - 1.2, hy0 - 0.25, top), (hc + 1.2, hy0 + 0.05, top + 5.6), SHOP_DARK, tag="hutdoor")
    for k in range(3):
        ax = -hs * (k * 3.6 - 1.0)
        ay = -hyo + 4.5 + 0.5 * (k % 2)
        roof.box((ax - 1.2, ay - 0.9, top - 0.05), (ax + 1.2, ay + 0.9, top + 1.6), snowy(H("#B8BEC9"), H("#8F96A3")), tag="ac")
        roof.cyl((ax, ay - 0.95, top + 0.8), (ax, ay - 0.8, top + 0.8), 0.6, 8, IRON, phase=0.0, tag="fan")
    bb = min(7.6, hxo - 6.5) if v["tower"] else min(7.6, hxo - 3.0)
    by = hyo - 4.8
    bx0 = (hs * 1.5) if v["tower"] else 0.0
    for px in (-bb * 0.66, bb * 0.66):
        roof.box((bx0 + px - 0.3, by + 0.4, top - 0.05), (bx0 + px + 0.3, by + 1.0, top + 9.2), IRON, tag="post")
    roof.box((bx0 - bb, by, top + 3.4), (bx0 + bb, by + 0.45, top + 10.0), WHITE, tag="board")
    roof.box((bx0 - bb + 0.6, by - 0.2, top + 3.9), (bx0 + bb - 0.6, by + 0.02, top + 9.5),
             lambda c, n, co: SNOW if n.z > 0.5 else H(v["billboard"]), tag="board")
    roof.box((bx0 - bb - 0.2, by - 0.2, top + 9.95), (bx0 + bb + 0.2, by + 0.7, top + 10.4), snowy(IRON), tag="boardcap")

    lights = lh.MeshBuilder(name + "_Lights", rng)
    k = 0
    n = int(W * 0.9)
    for i in range(n):
        x = -hxo + 0.6 + i * (W - 1.2) / (n - 1)
        lights.ico((x, -hyo - 0.2, top + ph - 0.05), (0.22, 0.22, 0.3), LIGHTS[k % 5], subdiv=1, tag="bulb"); k += 1
    for fz in floors[1:]:
        for uc in v["balconies"]:
            m = max(4, int(bw) )
            for i in range(m):
                x = uc - (bw / 2 - 0.3) + i * (bw - 0.6) / (m - 1)
                lights.ico(f.p(x, fz + 3.1, 2.24), (0.2, 0.2, 0.26), LIGHTS[k % 5], subdiv=1, tag="bulb"); k += 1

    mods = [b.to_object() for b in (walls, trim, glow, balc, shop, roof, lights)]
    finish = {name + "_Walls": dict(style="faceted"), name + "_Roof": dict(style="soft", bevel_width=0.06, smooth_angle=60),
              name + "_Trim": dict(style="faceted"), name + "_Glow": dict(style="faceted"),
              name + "_Balconies": dict(style="faceted"), name + "_Shopfront": dict(style="faceted"),
              name + "_Lights": dict(style="faceted")}
    classes = {name + "_Walls": "building", name + "_Trim": "building", name + "_Glow": "medium",
               name + "_Balconies": "medium", name + "_Shopfront": "building", name + "_Roof": "building",
               name + "_Lights": "medium"}
    return mods, finish, classes, (name + "_Walls",), (name + "_Glow",)


# ================================================================ pipeline
def build(name, maker=None, out_root=OUT):
    """maker(name) -> (mods, finish, classes, base_names, glow); default: the HOUSES / APARTMENTS builders."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    lf.setup_scene()
    bpy.context.scene.view_settings.view_transform = "Standard"
    if maker:
        mods, finish, classes, base_names, glow = maker(name)
    elif name in HOUSES:
        mods, finish, classes, base_names, glow = candy_house(name, HOUSES[name])
    else:
        mods, finish, classes, base_names, glow = apartment(name, APARTMENTS[name])
    out = os.path.join(out_root, name)
    os.makedirs(out, exist_ok=True)
    lh.recentre(mods)
    lh.finish_modules(mods, finish, glow=glow)
    gates = lh.gate_modules(mods, classes)
    scan = lh.floating_shells(mods, base_names=base_names)
    report = {"modules": {}, "floating": scan}
    total, ok_all = 0, True
    for m in mods:
        ok, fails, r = gates[m.name]
        total += r["tris"]; ok_all &= ok
        report["modules"][m.name] = {"passed": ok, "fails": fails, "tris": r["tris"], "size": r["dimensions"]}
        if not ok:
            print(f"[bld]   {m.name:30s} tris={r['tris']:6d} FAIL {fails}")
    pts = [m.matrix_world @ Vector(c) for m in mods for c in m.bound_box]
    size = [round(max(p[i] for p in pts) - min(p[i] for p in pts), 1) for i in range(3)]
    report.update(total_tris=total, size=size)
    print(f"[bld] {name:24s} {'PASS' if ok_all else 'FAIL'} tris={total:6d} size={size} "
          f"floating={scan['floating']} {scan['examples'][:3]}")
    lh.render_preview(mods, os.path.join(out, f"{name}_preview.png"))
    lh.render_preview(mods, os.path.join(out, f"{name}_back.png"), direction=(-1.0, 1.25, 0.6))
    lh.render_preview(mods, os.path.join(out, f"{name}_front.png"), direction=(0.0, -1.0, 0.25))
    lh.export_modules(mods, os.path.join(out, "glb"), combined=name)
    with open(os.path.join(out, f"{name}_report.json"), "w") as fh:
        json.dump(report, fh, indent=2, default=str)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, f"{name}.blend"))


if __name__ == "__main__":
    names = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(HOUSES) + list(APARTMENTS)
    for n in names:
        build(n)
