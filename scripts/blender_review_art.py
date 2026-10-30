"""Original, deterministic studio illustrations; run with Blender, no external assets.

blender -b --threads 2 --python scripts/blender_review_art.py -- --output-dir /path
These are explanatory illustrations, not cloth/fluid/thermodynamic simulations.
"""

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


def material(name, color, roughness=0.55, metallic=0):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    node = result.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value = (*color, 1)
    node.inputs["Roughness"].default_value = roughness
    node.inputs["Metallic"].default_value = metallic
    return result


def curve(name, points, mat, radius=0.014):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = radius
    data.bevel_resolution = 3
    spline = data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, xyz in zip(spline.points, points, strict=True):
        point.co = (*xyz, 1)
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def cube(name, location, scale, mat, bevel=0.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    modifier = obj.modifiers.new("Soft manufactured edges", "BEVEL")
    modifier.width = bevel
    modifier.segments = 4
    obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return obj


def sphere(name, location, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def setup(width, height, samples, threads):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.seed = 20261030
    scene.cycles.use_denoising = False
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.render.threads_mode = "FIXED"
    scene.render.threads = threads
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (
        0.78,
        0.72,
        0.60,
        1,
    )
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.45
    floor = material("Warm ivory cyclorama", (0.93, 0.86, 0.70), 0.82)
    bpy.ops.mesh.primitive_plane_add(size=200)
    bpy.context.object.data.materials.append(floor)
    for position, energy, size in [
        ((-3, -4, 7), 850, 5),
        ((4, -1, 4), 550, 4),
        ((0, 3, 5), 700, 3),
    ]:
        bpy.ops.object.light_add(type="AREA", location=position)
        lamp = bpy.context.object
        lamp.data.energy, lamp.data.size = energy, size
        lamp.rotation_euler = (
            (Vector((0, 0, 1.5)) - lamp.location).to_track_quat("-Z", "Y").to_euler()
        )
    bpy.ops.object.camera_add(location=(3.0, -9, 3.7))
    camera = bpy.context.object
    camera.rotation_euler = (
        (Vector((0, 0, 1.85)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    )
    camera.data.type, camera.data.ortho_scale = "ORTHO", 4.65
    scene.camera = camera
    return scene


def cloth_y(x, z):
    return 0.06 * math.sin(x * 10 + z * 2) + 0.035 * math.sin(z * 11 - x * 3)


def shirt(wet):
    fabric = material("Same blue cotton, both states", (0.055, 0.34, 0.50), 0.83)
    nodes = fabric.node_tree.nodes
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 230
    noise.inputs["Detail"].default_value = 2
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.20
    bump.inputs["Distance"].default_value = 0.009
    fabric.node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    fabric.node_tree.links.new(
        bump.outputs["Normal"], nodes["Principled BSDF"].inputs["Normal"]
    )
    outline = [
        (-0.68, 0.6),
        (0.68, 0.6),
        (0.68, 2.20),
        (1.03, 2.02),
        (1.30, 2.60),
        (0.58, 3.13),
        (0.28, 3.13),
        (0.20, 2.96),
        (0, 2.89),
        (-0.20, 2.96),
        (-0.28, 3.13),
        (-0.58, 3.13),
        (-1.30, 2.60),
        (-1.03, 2.02),
        (-0.68, 2.20),
    ]
    mesh = bpy.data.meshes.new("Original shirt silhouette")
    mesh.from_pydata([(x, 0, z) for x, z in outline], [], [list(range(len(outline)))])
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=10, use_grid_fill=True)
    for vertex in bm.verts:
        vertex.co.y = cloth_y(vertex.co.x, vertex.co.z)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Cotton shirt with physical thickness", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(fabric)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    smooth = obj.modifiers.new("Soft continuous folds", "SUBSURF")
    smooth.levels = 2
    solid = obj.modifiers.new("Cloth thickness", "SOLIDIFY")
    solid.thickness = 0.025
    seam = material("Cotton stitched edge", (0.21, 0.54, 0.63), 0.9)
    for z in [0.65, 0.70]:
        curve(
            "Double hem seam",
            [(x / 100, cloth_y(x / 100, z) - 0.025, z) for x in range(-65, 66, 2)],
            seam,
            0.009,
        )
    for sign in [-1, 1]:
        for n in range(17):
            z = 0.82 + n * 0.073
            curve(
                "Individual side stitch",
                [
                    (sign * 0.63, cloth_y(sign * 0.63, z) - 0.025, z),
                    (sign * 0.63, cloth_y(sign * 0.63, z + 0.028) - 0.025, z + 0.028),
                ],
                seam,
                0.006,
            )
    neck = [(x, cloth_y(x, z) - 0.035, z) for x, z in outline[6:11]]
    curve("Ribbed collar", neck, seam, 0.035)
    curve(
        "Pocket outline",
        [
            (x, cloth_y(x, z) - 0.05, z)
            for x, z in [
                (0.12, 2.37),
                (0.51, 2.37),
                (0.50, 1.96),
                (0.31, 1.88),
                (0.13, 1.97),
                (0.12, 2.37),
            ]
        ],
        seam,
        0.012,
    )
    wood = material("Beech clothespins", (0.66, 0.36, 0.12), 0.63)
    rope = material("Braided line", (0.44, 0.33, 0.19), 0.85)
    steel = material("Clothespin springs", (0.28, 0.30, 0.32), 0.28, 0.75)
    curve(
        "Clothesline", [(-2, 0.12, 3.27), (0, 0.10, 3.20), (2, 0.12, 3.27)], rope, 0.018
    )
    for x in [-0.48, 0.48]:
        for y in [-0.10, 0.13]:
            pin = cube(
                "Wooden clothespin half", (x, y, 3.18), (0.11, 0.065, 0.40), wood, 0.018
            )
            pin.rotation_euler.y = -0.07
        sphere("Metal spring", (x, -0.14, 3.18), (0.058, 0.025, 0.058), steel)
    if wet:
        water = material(
            "Water drops on fabric, not airborne vapour", (0.08, 0.36, 0.52), 0.15, 0.16
        )
        for x, z, size in [
            (-0.38, 1.55, 0.040),
            (0.24, 1.15, 0.034),
            (-0.11, 2.14, 0.030),
            (0.43, 0.93, 0.027),
            (-0.46, 0.80, 0.032),
        ]:
            sphere(
                "Surface droplet",
                (x, cloth_y(x, z) - 0.055, z),
                (size, size * 0.65, size * 1.45),
                water,
            )


def cup():
    ceramic = material("Glazed teal ceramic", (0.055, 0.35, 0.39), 0.24)
    rim = material("Cream ceramic rim", (0.96, 0.89, 0.72), 0.30)
    water = material("Still water illustration", (0.035, 0.28, 0.36), 0.09)
    node = water.node_tree.nodes.get("Principled BSDF")
    node.inputs["IOR"].default_value = 1.333
    node.inputs["Transmission Weight"].default_value = 0.22
    # A lathed wall has an actual open interior; no disk across the mug opening.
    profile = [
        (0, 0.06),
        (0.73, 0.06),
        (0.85, 0.14),
        (0.85, 1.33),
        (0.82, 1.39),
        (0.75, 1.35),
        (0.75, 0.21),
        (0, 0.21),
    ]
    segments = 128
    vertices = [
        (
            r * math.cos(i * math.tau / segments),
            r * math.sin(i * math.tau / segments),
            z,
        )
        for r, z in profile
        for i in range(segments)
    ]
    faces = [
        (
            j * segments + i,
            j * segments + (i + 1) % segments,
            (j + 1) * segments + (i + 1) % segments,
            (j + 1) * segments + i,
        )
        for j in range(len(profile) - 1)
        for i in range(segments)
    ]
    mesh = bpy.data.meshes.new("Hollow ceramic wall")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Open mug with visible inner wall", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(ceramic)
    obj.data.materials.append(rim)
    for face in mesh.polygons:
        face.use_smooth = True
        face.material_index = 1 if face.index // segments >= 3 else 0
    modifier = obj.modifiers.new("Rounded ceramic lip", "BEVEL")
    modifier.width, modifier.segments = 0.015, 3
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=128, radius=0.746, depth=0.04, location=(0, 0, 1.16)
    )
    bpy.context.object.name = "Water surface below the rim, no boiling bubbles"
    bpy.context.object.data.materials.append(water)
    points = [
        (0.73 + 0.60 * math.sin(a), 0, 0.78 + 0.50 * math.cos(a))
        for a in [i * math.pi / 64 for i in range(65)]
    ]
    curve("Curved ceramic handle", points, ceramic, 0.115)
    # Thermometer is a schematic, intentionally no numeric temperature claim.
    glass = material("Thermometer ivory housing", (0.92, 0.87, 0.73), 0.28)
    red = material("Thermometer coral scale", (0.74, 0.20, 0.12), 0.38)
    dark = material("Scale marks", (0.07, 0.16, 0.16), 0.65)
    cube("Thermometer", (-1.23, 0, 1.17), (0.20, 0.12, 1.75), glass, 0.09)
    curve(
        "Low thermometer reading",
        [(-1.23, -0.09, 0.45), (-1.23, -0.09, 1.03)],
        red,
        0.025,
    )
    sphere("Thermometer bulb", (-1.23, -0.10, 0.40), (0.12, 0.07, 0.12), red)
    for i in range(9):
        z = 0.64 + i * 0.14
        curve(
            "Unnumbered scale tick",
            [(-1.17, -0.075, z), (-1.12, -0.075, z)],
            dark,
            0.007,
        )
    scene = bpy.context.scene
    scene.camera.location = (3.0, -8, 5.8)
    scene.camera.rotation_euler = (
        (Vector((0, 0, 1.1)) - scene.camera.location)
        .to_track_quat("-Z", "Y")
        .to_euler()
    )
    scene.camera.data.ortho_scale = 4.3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--height", type=int, default=1400)
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--cpu-threads", type=int, choices=[1, 2, 3, 4], default=2)
    parser.add_argument("--only", choices=["wet", "dry", "cup", "all"], default="all")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    if not (
        320 <= args.width <= 3840
        and 320 <= args.height <= 3840
        and 8 <= args.samples <= 256
    ):
        raise ValueError("Illustration output exceeds supported bounds")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for name in ["wet", "dry", "cup"] if args.only == "all" else [args.only]:
        started = time.monotonic()
        scene = setup(args.width, args.height, args.samples, args.cpu_threads)
        cup() if name == "cup" else shirt(name == "wet")
        scene.render.filepath = str((args.output_dir / f"{name}.png").resolve())
        bpy.ops.render.render(write_still=True)
        records.append(
            {
                "asset": f"{name}.png",
                "seconds": round(time.monotonic() - started, 3),
                "width": args.width,
                "height": args.height,
                "samples": args.samples,
                "engine": "Cycles CPU",
                "cpu_threads": args.cpu_threads,
                "script_sha256": hashlib.sha256(
                    Path(__file__).read_bytes()
                ).hexdigest(),
                "seed": 20261030,
                "source": "Original procedural geometry; no external assets or physics simulation",
            }
        )
        # Keep completed asset evidence if a later expensive scene is interrupted.
        (args.output_dir / f"provenance-{name}.json").write_text(
            json.dumps([records[-1]], indent=2) + "\n"
        )
    (args.output_dir / f"provenance-{args.only}.json").write_text(
        json.dumps(records, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
