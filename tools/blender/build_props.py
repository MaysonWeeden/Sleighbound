"""Sleighbound low-poly winter prop kit.

Run headless:
  blender -b --factory-startup --python tools/blender/build_props.py

Kit rules (one look for every prop):
  - faceted low-poly: flat shading, hard props get one real 1-segment chamfer
  - vertex colours, one white material per mesh (MeshPart.Color = white in Studio)
  - 1 Blender unit = 1 stud, origin bottom-centre (rocks sink 15 % into the ground)
  - palette from the game's Candy theme
"""
import os, sys, math, json, random
import bpy, bmesh
from mathutils import Vector, Matrix, noise

SKILL = r"C:\Users\weede\.claude\plugins\cache\lihfolk\lihfolk\2.5.0\skills\roblox-blender-modeling\scripts"
sys.path.append(SKILL)
import lihfolk_bpy as lf
import lihfolk_curves as lc

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "assets", "props")
GLB = os.path.join(OUT, "glb")
PREV = os.path.join(OUT, "previews")

# ---------------------------------------------------------------- palette (sRGB hex)
P = {
    "red": "#E8344E", "red_dark": "#B8243C", "white": "#FFF6F0",
    "mint": "#46D6B0", "mint_dark": "#2FA98A", "gold": "#FFC840", "gold_dark": "#D99A20",
    "purple": "#8C7CFF", "purple_dark": "#6A58D8", "pink": "#FF82C4", "pink_dark": "#E0559F",
    "pine": "#2E8A5E", "pine_dark": "#1F6B4F", "pine_under": "#174A38",
    "snow": "#F4F9FF", "snow_shade": "#CFE0F5",
    "frost": "#DCEEFF", "frost_dark": "#A9C9EE",
    "rock": "#5E6A7D", "rock_dark": "#4A5466", "rock_light": "#7A8799",
    "trunk": "#6B4630", "trunk_dark": "#523424",
    "sack": "#C8283E", "sack_dark": "#9A1E30", "sack_light": "#E04A5C",
    "burlap": "#C79A62", "burlap_dark": "#9C7448", "burlap_light": "#DDB47E",
}


# ---------------------------------------------------------------- small helpers
def mesh_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def colour(ob, c):
    """Paint a part (hex = flat colour, callable(info) = per face) and give it the shared material."""
    fn = (lambda i, c=c: c) if isinstance(c, str) else c
    lc.paint(ob, fn)
    lc.vertex_color_material(ob)
    return ob


def box(name, size, center, bevel=0.05):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) + Vector(center)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=1, profile=0.5,
                        affect="EDGES", clamp_overlap=True)
    return mesh_obj(name, bm)


def ico(name, r, center, subdiv=2, scale=(1, 1, 1), freq=0.9, amp=0.16, seed=0):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    off = Vector((seed * 13.1, seed * 7.7, seed * 3.3))
    for v in bm.verts:
        n = noise.noise(v.co / r * freq + off)
        p = v.co * (1 + amp * n)
        v.co = Vector((p.x * scale[0], p.y * scale[1], p.z * scale[2])) + Vector(center)
    return mesh_obj(name, bm)


def mirror_copy(ob, name):
    c = ob.copy(); c.data = ob.data.copy(); c.name = name
    bpy.context.scene.collection.objects.link(c)
    lc.deform(c, lambda p: Vector((-p.x, p.y, p.z)))
    return c


def join(name, parts):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name; ob.data.name = name
    ca = ob.data.color_attributes
    ca.active_color = ca["Col"]; ca.render_color_index = ca.active_color_index
    return ob


def ramp(c0, c1, t):
    a, b = lc.hex_rgb(c0), lc.hex_rgb(c1)
    t = min(max(t, 0.0), 1.0)
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


# ---------------------------------------------------------------- candy cane
def candy_cane(name, H, R, drop, r, segments, pitch, col_a=None, col_b=None):
    col_a, col_b = col_a or P["red"], col_b or P["white"]
    path = [(0, 0, 0), (0, 0, H)]
    for k in range(1, 25):
        a = math.pi - math.pi * k / 24
        path.append((R + R * math.cos(a), 0, H + R * math.sin(a)))
    path.append((2 * R, 0, H - drop))
    L = H + math.pi * R + drop
    twist = L / pitch * 360.0
    ob = lc.sweep(name, path, profile=lc.circle(8), radius=r, twist=(0, twist), up=(0, 1, 0),
                  segments=segments, cls="medium")
    side = segments * 8

    def fn(i):
        if i.index >= side:                      # end caps
            return col_b
        j = int(i.uv.x * 8 + 1e-6) % 8
        return col_a if j in (0, 1, 4, 5) else col_b
    colour(ob, fn)
    return ob, "medium" if H > 4 else "small", None


# ---------------------------------------------------------------- present
def present(name, w, d, h, body, body_dark, ribbon):
    s = min(w, d)
    parts = []
    lid_h = h * 0.22
    parts.append(colour(box(name + "_body", (w, d, h - lid_h), (0, 0, (h - lid_h) / 2), 0.05), body_dark))
    parts.append(colour(box(name + "_lid", (w + 0.14, d + 0.14, lid_h), (0, 0, h - lid_h / 2), 0.05), body))
    rb = max(0.22, s * 0.16)
    top = h + 0.05
    parts.append(colour(box(name + "_ribX", (w + 0.2, rb, top), (0, 0, top / 2), 0.03), ribbon))
    parts.append(colour(box(name + "_ribY", (rb, d + 0.2, top + 0.02), (0, 0, (top + 0.02) / 2), 0.03), ribbon))
    k = 0.26 * s
    knot_z = top + k * 0.35
    parts.append(colour(box(name + "_knot", (k, k * 0.9, k * 0.8), (0, 0, knot_z), 0.03), ribbon))
    rx, rz, tube, tilt = 0.32 * s, 0.2 * s, 0.075 * s, math.radians(28)
    cx, cz = rx * 0.95, knot_z + rz * 0.45
    loop = []
    for n in range(16):
        a = 2 * math.pi * n / 16
        x, z = rx * math.cos(a), rz * math.sin(a)
        loop.append((cx + x * math.cos(tilt) - z * math.sin(tilt), 0, cz + x * math.sin(tilt) + z * math.cos(tilt)))
    right = lc.sweep(name + "_bowR", loop, profile=lc.circle(6), radius=tube, closed=True,
                     up=(0, 1, 0), segments=12, cls="small")
    colour(right, ribbon)
    parts += [right, mirror_copy(right, name + "_bowL")]
    return join(name, parts), "small", "X"


# ---------------------------------------------------------------- sack
def sack(name, height, main, dark, light, rope, seed):
    k = height / 3.2
    steps = 12
    prof = [(0, 0), (0.95, 0.02), (1.32, 0.25), (1.48, 0.75), (1.44, 1.3), (1.26, 1.8), (0.92, 2.25),
            (0.5, 2.56), (0.46, 2.68), (0.78, 2.9), (1.0, 3.2), (0.5, 3.1), (0, 3.0)]
    prof = [(r * k, z * k) for r, z in prof]
    ob = lc.lathe(name + "_bag", prof, steps=steps, cls="small")
    off = Vector((seed * 5.3, seed * 2.1, 0))

    def shape(p):
        rr = math.hypot(p.x, p.y)
        if rr < 1e-6:
            return p
        t = p.z / (3.2 * k)
        j = int(round(math.atan2(p.y, p.x) / (2 * math.pi) * steps)) % steps
        f = 1.0
        if 0.5 < t < 0.8:                                  # fabric folds gathering into the neck
            f *= 1 + (0.07 if j % 2 else -0.05) * min(1.0, (t - 0.5) / 0.15)
        if t > 0.97:                                       # crinkled tuft above the rope
            f *= 1.2 if j % 2 == 0 else 0.7
            p = Vector((p.x, p.y, p.z - (0.22 * k if j % 2 else 0.0)))
        w = max(0.0, min(1.0, (0.72 - t) / 0.2)) * min(1.0, t / 0.08)   # lumps on the belly only
        f *= 1 + 0.14 * w * noise.noise(Vector((p.x, p.y, p.z)) * (0.9 / k) + off)
        lean = 0.12 * k * t * t
        return Vector((p.x * f + lean, p.y * f, p.z))
    lc.deform(ob, shape)

    def fn(i):
        t = i.center.z / (3.2 * k)
        if t < 0.1:
            return dark
        if t > 0.84:
            return light
        return main if i.normal.z > -0.25 else dark
    colour(ob, fn)
    neck_z, neck_r = 2.62 * k, 0.5 * k
    lean_neck = 0.12 * k * (2.62 / 3.2) ** 2
    ring = [(lean_neck + neck_r * math.cos(2 * math.pi * n / 16), neck_r * math.sin(2 * math.pi * n / 16), neck_z)
            for n in range(16)]
    tie = lc.sweep(name + "_rope", ring, profile=lc.circle(6), radius=0.1 * k, closed=True, up=(0, 0, 1),
                   segments=12, cls="small")
    colour(tie, rope)
    return join(name, [ob, tie]), "small", None


# ---------------------------------------------------------------- snowy pine
def pine(name, height, tiers, base_r, seed, trunk_frac=0.14, heavy=False, extra=None):
    """heavy: snow streaks down the green skirts. extra(tiers) -> more parts; tiers = [(z_base, radius, height)]."""
    rnd = random.Random(seed)
    parts = []
    info = []
    trunk_h = height * trunk_frac + 0.6
    rb = base_r * 0.16
    tr = lc.lathe(name + "_trunk", [(rb * 1.35, 0), (rb, trunk_h * 0.25), (rb * 0.75, trunk_h)], steps=6, cls="tree")
    parts.append(colour(tr, lambda i: P["trunk_dark"] if i.center.z < trunk_h * 0.2 else P["trunk"]))
    crown = height - height * trunk_frac
    z0 = height * trunk_frac
    spacing = crown / (tiers + 0.6)
    steps = 10
    for t in range(tiers):
        u = t / max(tiers - 1, 1)
        r = base_r * (1 - 0.62 * u)
        th = spacing * 1.75 if t < tiers - 1 else spacing * 2.1
        zb = z0 + t * spacing
        info.append((zb, r, th))
        prof = [(0, zb), (r, zb + 0.12), (r * 0.66, zb + th * 0.34), (r * 0.3, zb + th * 0.68), (0, zb + th)]
        tier = lc.lathe(f"{name}_tier{t}", prof, steps=steps, cls="tree")
        rot = Matrix.Rotation(math.radians(rnd.uniform(0, 36)), 3, "Z")
        jit = [rnd.uniform(-1, 1) for _ in range(steps * 3)]

        def shape(p, zb=zb, th=th, rot=rot, jit=jit):
            rr = math.hypot(p.x, p.y)
            if rr > 1e-6:
                a = math.atan2(p.y, p.x)
                j = int(round(a / (2 * math.pi) * steps)) % steps
                ring = min(2, max(0, int(round((p.z - zb) / th * 3))))
                f = 1 + 0.07 * jit[ring * steps + j]
                p = Vector((p.x * f, p.y * f, p.z))
                if abs(p.z - (zb + th * 0.34)) < th * 0.05:          # jagged snow line
                    p.z += th * (0.07 if j % 2 else -0.05)
                if abs(p.z - (zb + 0.12)) < 0.05:                    # droopy rim
                    p.z -= th * 0.06 * (jit[j] * 0.5 + 0.5)
            return rot @ p
        lc.deform(tier, shape)
        shade = 1 - 0.35 * (1 - u)

        def fn(i, shade=shade):
            band = i.index // steps
            if band == 0:
                return P["pine_under"]
            if band == 1:
                if heavy and i.index % 3 == 0:
                    return P["snow_shade"]
                return ramp(P["pine_dark"], P["pine"], shade)
            if band == 2:
                return P["snow_shade"] if i.normal.z < 0.45 else P["snow"]
            return P["snow"]
        parts.append(colour(tier, fn))
    if extra:
        parts += extra(info)
    return join(name, parts), "tree", None


# ---------------------------------------------------------------- frosted round tree
def frosted_tree(name, seed):
    parts = []
    tr = lc.lathe(name + "_trunk", [(0.7, 0), (0.45, 1.0), (0.34, 4.2)], steps=6, cls="tree")
    parts.append(colour(tr, lambda i: P["trunk_dark"] if i.center.z < 0.5 else P["trunk"]))
    clumps = [((0, 0, 5.2), 2.3, (1, 1, 0.8)), ((1.6, 0.6, 4.2), 1.6, (1, 1, 0.78)),
              ((-1.5, -0.5, 4.3), 1.7, (1, 1, 0.78)), ((0.3, -1.4, 4.6), 1.4, (1, 1, 0.8)),
              ((-0.2, 0.3, 6.8), 1.4, (1, 1, 0.9))]
    for n, (c, r, sc) in enumerate(clumps):
        cl = ico(f"{name}_clump{n}", r, c, subdiv=2, scale=sc, amp=0.16, seed=seed + n)
        cz = c[2]

        def fn(i, cz=cz, r=r):
            if i.normal.z > 0.3 and i.center.z > cz - 0.15 * r:
                return P["snow"]
            if i.normal.z < -0.35:
                return P["frost_dark"]
            return P["frost"]
        parts.append(colour(cl, fn))
    return join(name, parts), "tree", None


# ---------------------------------------------------------------- snowy rock
def rock_part(name, r, center, scale, seed):
    ob = ico(name, r, center, subdiv=3, scale=scale, freq=0.6, amp=0.32, seed=seed)
    cz = center[2]
    lc.deform(ob, lambda p, cz=cz: Vector((p.x, p.y, cz + (p.z - cz) * (0.45 if p.z < cz else 1.0))))
    off = Vector((seed * 3.7, seed * 1.9, 0.5))

    def fn(i):
        if i.normal.z > 0.72:
            return P["snow"]
        if i.normal.z > 0.6:
            return P["snow_shade"]
        n = noise.noise(i.center * 0.8 + off)
        return P["rock_light"] if n > 0.25 else (P["rock_dark"] if n < -0.2 or i.normal.z < -0.3 else P["rock"])
    return colour(ob, fn)


def rock(name, specs):
    parts = [rock_part(f"{name}_{n}", *s) for n, s in enumerate(specs)]
    ob = join(name, parts) if len(parts) > 1 else parts[0]
    ob.name = name
    return ob, "rock", None


# ---------------------------------------------------------------- kit
KIT = [
    ("CandyCane_Large", lambda: candy_cane("CandyCane_Large", 7.0, 1.15, 0.7, 0.4, 56, 3.0)),
    ("CandyCane_Small", lambda: candy_cane("CandyCane_Small", 2.6, 0.48, 0.3, 0.17, 32, 1.3)),
    ("Present_Small", lambda: present("Present_Small", 1.4, 1.4, 1.2, P["red"], P["red_dark"], P["gold"])),
    ("Present_Medium", lambda: present("Present_Medium", 2.2, 2.2, 1.8, P["mint"], P["mint_dark"], P["red"])),
    ("Present_Large", lambda: present("Present_Large", 3.2, 2.6, 2.4, P["purple"], P["purple_dark"], P["gold"])),
    ("Present_Tall", lambda: present("Present_Tall", 1.6, 1.6, 2.8, P["gold"], P["gold_dark"], P["red"])),
    ("Present_Flat", lambda: present("Present_Flat", 2.6, 1.8, 0.9, P["pink"], P["pink_dark"], P["white"])),
    ("Sack_Small", lambda: sack("Sack_Small", 2.0, P["burlap"], P["burlap_dark"], P["burlap_light"], P["red"], 1)),
    ("Sack_Medium", lambda: sack("Sack_Medium", 3.0, P["sack"], P["sack_dark"], P["sack_light"], P["gold"], 2)),
    ("Sack_Large", lambda: sack("Sack_Large", 4.5, P["sack"], P["sack_dark"], P["sack_light"], P["gold"], 3)),
    ("Pine_Tall", lambda: pine("Pine_Tall", 16.0, 5, 4.2, 11)),
    ("Pine_Medium", lambda: pine("Pine_Medium", 10.0, 4, 3.2, 12)),
    ("Pine_Small", lambda: pine("Pine_Small", 6.0, 3, 2.3, 13)),
    ("Tree_Frosted", lambda: frosted_tree("Tree_Frosted", 21)),
    ("Rock_Small", lambda: rock("Rock_Small", [(1.0, (0, 0, 0), (1.2, 1.0, 0.8), 31)])),
    ("Rock_Medium", lambda: rock("Rock_Medium", [(2.0, (0, 0, 0), (1.3, 1.0, 0.75), 32)])),
    ("Rock_Cluster", lambda: rock("Rock_Cluster", [(2.6, (0, 0, 0), (1.25, 1.0, 0.8), 33),
                                                   (1.4, (3.0, 1.2, -0.5), (1.1, 1.0, 0.85), 34)])),
]


SINK = ("Rock", "SnowPile", "Ice")   # origin 15 % up so these sit into the snow


def build(kit=None, tag=None):
    """kit = [(name, make)] (first kit, classic lineup) or [(name, category, make)] (grid lineup per category).
    tag names the report / .blend / lineup files of an extra kit."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    lf.setup_scene()
    s = bpy.context.scene
    s.view_settings.view_transform = "Standard"
    os.makedirs(GLB, exist_ok=True); os.makedirs(PREV, exist_ok=True)
    kit = kit or KIT
    report = {}
    built = []
    cats = {}
    for entry in kit:
        name, make = entry[0], entry[-1]
        ob, cls, sym = make()
        ob.name = name
        lf.finish(ob, style="faceted")
        if len(entry) == 3:
            cats.setdefault(entry[1], []).append(ob)
        if name.startswith(SINK):
            bpy.context.view_layer.update()
            pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
            lo = min(p.z for p in pts); hi = max(p.z for p in pts)
            cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
            cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
            lf.set_origin(ob, "point", at=(cx, cy, lo + 0.15 * (hi - lo)))
        else:
            lf.set_origin(ob, "bottom")
        passed, fails, r = lf.gate(ob, cls, symmetric=sym)
        report[name] = {"passed": passed, "fails": fails, "tris": r["tris"], "class": cls,
                        "budget_note": r["budget_note"], "size_studs": r["dimensions"]}
        print(f"[kit] {name:22s} tris={r['tris']:5d} {cls:6s} {'PASS' if passed else 'FAIL'} {fails}")
        lf.render_review(ob, PREV, size=512)
        lf.export_glb(ob, os.path.join(GLB, name + ".glb"))
        built.append(ob)
    if cats:
        for cat, obs in cats.items():
            grid_shot(obs, built, os.path.join(PREV, f"_{tag}_{cat}.png"))
        grid_shot(built, built, os.path.join(PREV, f"_{tag}_All.png"))
    else:
        lineup(built)
    suffix = f"_{tag}" if tag else ""
    with open(os.path.join(OUT, f"props_report{suffix}.json"), "w") as f:
        json.dump(report, f, indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"Sleighbound_Props{suffix}.blend"))


def _shot_setup():
    s = bpy.context.scene
    sh = s.display.shading
    s.render.engine = "BLENDER_WORKBENCH"
    s.render.resolution_x, s.render.resolution_y = 1920, 1080
    sh.light = "STUDIO"; sh.color_type = "VERTEX"; sh.show_cavity = True; sh.show_object_outline = True
    sh.show_shadows = True
    if s.world is None:
        s.world = bpy.data.worlds.new("LF_World")
    s.world.color = (0.62, 0.74, 0.9)
    s.view_settings.exposure = 0.6
    return s


def grid_shot(obs, everything, path):
    """Rows of props, tallest at the back, framed by an orthographic camera looking down at 35 degrees."""
    s = _shot_setup()
    obs = sorted(obs, key=lambda o: -o.dimensions.z)
    area = sum(max(o.dimensions.x, 1) * max(o.dimensions.y, 1) for o in obs)
    row_w = max(24.0, math.sqrt(area) * 2.4)
    gap = 1.5
    rows, cur, w = [], [], 0.0
    for o in obs:
        if cur and w + o.dimensions.x > row_w:
            rows.append(cur); cur, w = [], 0.0
        cur.append(o); w += o.dimensions.x + gap
    rows.append(cur)
    y = 0.0
    for row in rows:                     # first row (tallest) furthest from the camera
        depth = max(o.dimensions.y for o in row)
        widths = [o.dimensions.x for o in row]
        x = -(sum(widths) + gap * (len(row) - 1)) / 2
        for o, wd in zip(row, widths):
            o.location = (x + wd / 2, y, 0)
            x += wd + gap
        y -= depth + gap
    for o in everything:
        o.hide_render = o not in obs
    ground = bpy.data.objects.get("LF_Ground")
    if ground is None:
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=200)
        ground = colour(mesh_obj("LF_Ground", bm), "#E6EEF8")
    cam = bpy.data.objects.get("GridCam")
    if cam is None:
        cd = bpy.data.cameras.new("GridCam"); cd.type = "ORTHO"
        cam = bpy.data.objects.new("GridCam", cd); s.collection.objects.link(cam)
    s.camera = cam
    fwd = Vector((0, 1, -0.7)).normalized()
    rot = fwd.to_track_quat("-Z", "Y")
    right, up = rot @ Vector((1, 0, 0)), rot @ Vector((0, 1, 0))
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
    rs = [p.dot(right) for p in pts]; us = [p.dot(up) for p in pts]
    ctr = right * (min(rs) + max(rs)) / 2 + up * (min(us) + max(us)) / 2
    aspect = s.render.resolution_x / s.render.resolution_y
    cam.data.ortho_scale = max(max(rs) - min(rs), (max(us) - min(us)) * aspect) * 1.08
    cam.location = ctr - fwd * 300
    cam.rotation_euler = rot.to_euler()
    cam.data.clip_end = 1000
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in everything:
        o.hide_render = False


def lineup(obs):
    """Hero shot of the whole kit: small props in front, trees and rocks behind."""
    s = bpy.context.scene
    front = [o for o in obs if not o.name.startswith(("Pine", "Tree", "Rock"))]
    back = [o for o in obs if o.name.startswith(("Pine", "Tree", "Rock"))]
    for row, y in ((back, 6.0), (front, -4.0)):
        widths = [o.dimensions.x for o in row]
        gap = 1.2
        x = -(sum(widths) + gap * (len(row) - 1)) / 2
        for o, w in zip(row, widths):
            o.location = (x + w / 2, y, 0)
            x += w + gap
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60)
    ground = mesh_obj("LF_Ground", bm)
    colour(ground, "#E6EEF8")
    sh = s.display.shading
    s.render.engine = "BLENDER_WORKBENCH"
    s.render.resolution_x, s.render.resolution_y = 1920, 1080
    sh.light = "STUDIO"; sh.color_type = "VERTEX"; sh.show_cavity = True; sh.show_object_outline = True
    sh.show_shadows = True
    if s.world is None:
        s.world = bpy.data.worlds.new("LF_World")
    s.world.color = (0.62, 0.74, 0.9)
    s.view_settings.exposure = 0.6
    cam_data = bpy.data.cameras.new("LineupCam"); cam_data.lens = 35
    cam = bpy.data.objects.new("LineupCam", cam_data); s.collection.objects.link(cam); s.camera = cam
    cam.location = (0, -46, 17)
    cam.rotation_euler = (Vector((0, 1.5, 4.5)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    s.render.filepath = os.path.join(PREV, "_Kit_Lineup.png")
    bpy.ops.render.render(write_still=True)
    # close-up of the small props
    cam.location = (0, -24, 7)
    cam.rotation_euler = (Vector((0, -4, 1.6)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    s.render.filepath = os.path.join(PREV, "_Kit_SmallProps.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    build()
