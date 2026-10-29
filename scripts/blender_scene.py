"""Original procedural 3D particle illustration, not a diffusion model or a physics simulator.

Run with Blender's Python: blender -b --threads 2 --python scripts/blender_scene.py -- ...
The output clip can be imported into a motion scene in the studio.
"""

import argparse
import math
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import bpy
from mathutils import Vector


def material(name, color, metallic=0.0, roughness=0.4):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1)
    result.use_nodes = True
    node = result.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value = (*color, 1)
    node.inputs["Metallic"].default_value = metallic
    node.inputs["Roughness"].default_value = roughness
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--frames", type=int, default=60)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--samples", type=int, default=32)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    if not (
        2 <= args.frames <= 600
        and 16 <= args.width <= 3840
        and 16 <= args.height <= 3840
    ):
        raise ValueError("Template output exceeds supported bounds")
    if args.width % 2 or args.height % 2:
        raise ValueError("H264 dimensions must be even")
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = args.samples
    # Portable CPU builds may omit OpenImageDenoise; use real samples, no unsupported denoiser.
    scene.cycles.use_denoising = False
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    scene.render.fps = args.fps
    scene.world.color = (0.15, 0.18, 0.21)
    scene.view_settings.view_transform = "AgX"
    blue = material("Water-blue illustration", (0.16, 0.49, 0.77), 0.25)
    warm = material("Accent", (0.85, 0.48, 0.19), 0.2)
    floor = material("Floor", (0.04, 0.09, 0.12), 0.15, 0.65)
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -2))
    bpy.context.object.data.materials.append(floor)
    rng = random.Random(42)
    particles = []
    for i in range(24):
        center = Vector(
            (rng.uniform(-1.7, 1.7), rng.uniform(-1.5, 1.5), rng.uniform(-1.3, 1.8))
        )
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=20, ring_count=12, radius=0.15, location=center
        )
        sphere = bpy.context.object
        sphere.name = f"Illustrative particle {i + 1}"
        sphere.data.materials.append(warm if i % 5 == 0 else blue)
        for polygon in sphere.data.polygons:
            polygon.use_smooth = True
        particles.append((sphere, center, rng.random() * math.tau))
    bpy.ops.object.light_add(type="AREA", location=(2, -4, 7))
    bpy.context.object.data.energy = 1300
    bpy.context.object.data.shape = "DISK"
    bpy.context.object.data.size = 6
    bpy.ops.object.light_add(type="AREA", location=(-4, 2, 2))
    bpy.context.object.data.energy = 900
    bpy.context.object.data.size = 4
    bpy.ops.object.camera_add(location=(5.5, -8, 4))
    camera = bpy.context.object
    camera.rotation_euler = (
        (Vector((0, 0, 0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    )
    camera.data.lens = 48
    scene.camera = camera
    scene.render.image_settings.file_format = "PNG"
    with tempfile.TemporaryDirectory(prefix="whiteboard-3d-") as tmp:
        root = Path(tmp)
        for frame in range(args.frames):
            t = frame / max(1, args.frames - 1)
            for sphere, center, phase in particles:
                sphere.location = center + Vector(
                    (
                        math.sin(t * math.tau + phase) * 0.25,
                        math.cos(t * math.tau + phase) * 0.2,
                        math.sin(t * math.tau * 0.5 + phase) * 0.2,
                    )
                )
            scene.render.filepath = str(root / f"frame-{frame:05d}.png")
            bpy.ops.render.render(write_still=True)
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-framerate",
                str(args.fps),
                "-i",
                str(root / "frame-%05d.png"),
                "-c:v",
                "libx264",
                "-crf",
                "16",
                "-pix_fmt",
                "yuv420p",
                "-threads",
                "2",
                "-movflags",
                "+faststart",
                str(args.output),
            ],
            check=True,
        )
    print(f"Original 3D illustration rendered: {args.output.name}", flush=True)


if __name__ == "__main__":
    main()
