"""Pack built models into one GLB for a single Roblox upload.

  blender -b --factory-startup --python tools/blender/export_buildings_bundle.py -- buildings
  blender -b --factory-startup --python tools/blender/export_buildings_bundle.py -- town

Each model becomes an Empty (a Model in Studio) holding its module meshes, so modules stay lined up.
Models are laid out in rows (fronts facing -Y) with 12-stud gaps.
"""
import os, sys, json
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_buildings as bb

which = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "buildings"
if which == "town":
    import build_town as bt
    R = bt.OUT
    rows = [(list(bt.ROADS), 0.0), (list(bt.STALLS) + list(bt.SHEDS) + ["Igloo"], 50.0),
            (["ClockTower", "TreePlaza", "IceRink"], 90.0),
            (["Hydrant", "StopSign", "TrafficLight", "BusStop", "PhoneBooth"] + list(bt.CARS), 135.0)]
    dest = "Sleighbound_Town.glb"
else:
    R = bb.OUT
    apts = [n for n in bb.APARTMENTS if not n.startswith(("Shop_", "PostOffice"))]
    rows = [(list(bb.HOUSES), 0.0), ([n for n in bb.APARTMENTS if n not in apts], 50.0), (apts, 100.0)]
    dest = "Sleighbound_Buildings.glb"
DEST = os.path.join(bb.ROOT, "assets", "props", "upload", dest)   # approved upload folder

bpy.ops.wm.read_factory_settings(use_empty=True)
layout = {}
for names, y in rows:
    x = 0.0
    for name in names:
        rep = json.load(open(os.path.join(R, name, f"{name}_report.json")))
        mods = list(rep["modules"])
        with bpy.data.libraries.load(os.path.join(R, name, f"{name}.blend"), link=False) as (src, dst):
            dst.objects = [n for n in src.objects if n in mods]
        root = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.objects.link(root)
        w = rep["size"][0]
        root.location = (x + w / 2, y, 0)
        for ob in dst.objects:
            bpy.context.scene.collection.objects.link(ob)
            ob.parent = root
        layout[name] = {"modules": mods, "x": round(x + w / 2, 2), "y": y, "size": rep["size"]}
        x += w + 12.0

bpy.ops.object.select_all(action="SELECT")
os.makedirs(os.path.dirname(DEST), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=DEST, export_format="GLB", use_selection=True, export_apply=True,
                          export_yup=True, export_normals=True, export_vertex_color="ACTIVE",
                          export_draco_mesh_compression_enable=False)
with open(DEST.replace(".glb", "_layout.json"), "w") as f:
    json.dump(layout, f, indent=1)
n_mesh = sum(1 for o in bpy.context.scene.objects if o.type == "MESH")
print(f"[bundle] {len(layout)} models, {n_mesh} module meshes -> {DEST} ({os.path.getsize(DEST) // 1024} KB)")
