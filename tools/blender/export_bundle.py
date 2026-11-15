"""Pack every prop from both kits into one GLB for a single Roblox upload.

  blender -b --factory-startup --python tools/blender/export_bundle.py

Each prop stays its own mesh (one MeshPart in Studio), laid out on a grid by category so the
imported model is easy to browse. Geometry and vertex colours come straight from the kit .blend files.
"""
import os, sys, json
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_props as bp
import props_more as pm

OUT = bp.OUT
DEST = os.path.join(OUT, "upload", "Sleighbound_WinterProps.glb")

groups = {"Kit1": [n for n, _ in bp.KIT]}
for name, cat, _ in pm.KIT2:
    groups.setdefault(cat, []).append(name)

bpy.ops.wm.read_factory_settings(use_empty=True)
want = {n for names in groups.values() for n in names}
for blend in ("Sleighbound_Props.blend", "Sleighbound_Props_Kit2.blend"):
    with bpy.data.libraries.load(os.path.join(OUT, blend), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in want]
    for ob in dst.objects:
        if ob is not None:
            bpy.context.scene.collection.objects.link(ob)

objs = {o.name: o for o in bpy.context.scene.objects}
missing = sorted(want - set(objs))
assert not missing, f"missing props: {missing}"

layout = {}
z_row = 0.0
for cat, names in groups.items():            # one row per category, along +X; rows go back along +Y
    x = 0.0
    depth = 0.0
    for n in names:
        o = objs[n]
        w, d = o.dimensions.x, o.dimensions.y
        o.location = (x + w / 2, z_row + d / 2, 0)
        layout[n] = {"category": cat, "size": [round(v, 2) for v in o.dimensions]}
        x += w + 3.0
        depth = max(depth, d)
    z_row += depth + 6.0

bpy.ops.object.select_all(action="DESELECT")
for o in objs.values():
    o.select_set(True)
os.makedirs(os.path.dirname(DEST), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=DEST, export_format="GLB", use_selection=True, export_apply=True,
                          export_yup=True, export_normals=True, export_vertex_color="ACTIVE",
                          export_draco_mesh_compression_enable=False)
with open(os.path.join(OUT, "upload", "bundle_layout.json"), "w") as f:
    json.dump(layout, f, indent=1)
print(f"[bundle] {len(objs)} props -> {DEST} ({os.path.getsize(DEST) // 1024} KB)")
