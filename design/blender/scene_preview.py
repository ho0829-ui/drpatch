"""책상 합성 미리보기: 내보낸 .glb를 시제품과 같은 자리에 놓고 시제품 카메라로 렌더한다 (통일감 확인용)."""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import common as C  # noqa: E402

C.reset()


def place(name, loc, rot_z=0.0, scale=1.0):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.gltf(filepath=os.path.join(C.MODELS, f"{name}.glb"))
    roots = [o for o in bpy.context.selected_objects if o.parent is None]
    for r in roots:
        r.location = loc
        r.rotation_mode = "XYZ"
        r.rotation_euler.z += rot_z  # 가져오기가 이미 Z-up으로 바꿔 줌 → 방향만 더한다
        r.scale = (scale, scale, scale)
    return bpy.context.selected_objects


def recolor(objs, part, hex_color):
    for o in objs:
        if o.name.startswith(part) and o.type == "MESH":
            m = o.active_material.copy()
            m.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = C.srgb(hex_color)
            o.active_material = m


SEV = {"critical": "#E5484D", "high": "#F59E0B", "moderate": "#F5C518", "low": "#3B82F6", "unknown": "#A3AEB0"}
ROUND1 = ["high", "critical", "critical", "critical"]
ROUND2 = ["high", "moderate", "low", "unknown"]
SLOTS = [(x, y) for y in (0.62, -0.62) for x in (-0.75, 0.65, 2.05)]

place("desk", (0, 0, 0))
for by, sevs in ((1.75, ROUND1), (-1.75, ROUND2)):
    place("blister", (-0.6, by, 0))
    for (sx, sy), sev in zip(SLOTS, sevs):
        objs = place("capsule", (-0.6 + sx, by + sy, 0.27))
        recolor(objs, "CapCur", SEV[sev])
        recolor(objs, "CapTgt", C.PALETTE["teal"])
place("bottle", (5.5, 2.3, 0))
place("doctor", (5.4, -2.9, 0), rot_z=0.35, scale=1.25)
place("iv", (-6.9, 2.4, 0))
place("chart", (-6.5, -2.5, 0), rot_z=-0.12)
place("stamp", (3.3, -4.1, 0))

C.render_preview("desk.png", cam_loc=(0, -11.2, 17.5), target=(-0.2, -0.2, 0.9), size=(1600, 1000), floor_z=-0.62, fov=36)
