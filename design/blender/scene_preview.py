"""진료실 합성 미리보기: 내보낸 .glb를 시제품과 같은 자리에 놓고 시제품 카메라로 렌더한다 (비율·배치·통일감 확인용).

배치 숫자는 prototype/drpatch-desk/index.html의 LAYOUT과 같게 유지한다 (Blender 좌표: x, y=-(three z), z=(three y)).
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import common as C  # noqa: E402

C.reset()


def place(name, loc, rot_z=0.0, scale=1.0, node=None):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.gltf(filepath=os.path.join(C.MODELS, f"{name}.glb"))
    objs = list(bpy.context.selected_objects)
    roots = [o for o in objs if o.parent is None]
    if node:  # pills.glb 안의 한 알만 남긴다
        keep = next(o for o in objs if o.name.startswith(node))
        for o in objs:
            if o is not keep and keep not in o.children_recursive and o not in keep.children_recursive:
                bpy.data.objects.remove(o)
        keep.parent = None
        roots = [keep]
    for r in roots:
        r.location = loc
        r.rotation_euler.z += rot_z
        r.scale = (scale,) * 3
    return objs


SLOT = (1.4, 1.24)
SEV = {"critical": "#E5484D", "high": "#F59E0B", "moderate": "#F5C518", "low": "#3B82F6", "unknown": "#A3AEB0"}
ROUNDS = [["python", "urllib3", "requests", "pyyaml"], ["django", "jinja2", "flask", "numpy"], ["pandas", "pytest", None, None]]
SEVS = [["high", "critical", "critical", "critical"], ["high", "moderate", "low", "unknown"], ["moderate", "low", "moderate", "low"]]

place("room", (0, 0, 0))
place("desk", (0, 0, 0))
# 블리스터: 패드 위에 2열로 (뒷줄 1·2회차, 앞줄 3회차)
pack_w = 1.2 + 2 * SLOT[0]
for r, (names, sevs) in enumerate(zip(ROUNDS, SEVS)):
    px = -2.4 + (r % 2) * (pack_w + 0.5) - (0 if r < 2 else 0)
    py = 0.55 if r < 2 else -2.4
    place("blister_end", (px, py, 0))
    for k, (nm, sv) in enumerate(zip(names, sevs)):
        cx = px + 0.6 + SLOT[0] / 2 + (k % 2) * SLOT[0]
        cy = py + (SLOT[1] / 2 if k < 2 else -SLOT[1] / 2)
        objs = place("blister_cell", (cx, cy, 0))
        for o in objs:
            if o.type == "MESH" and o.active_material and o.active_material.name.startswith("foil_well"):
                m = o.active_material.copy()
                m.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = C.srgb(SEV[sv])
                o.active_material = m
        if nm:
            place("pills", (cx, cy, 0.27), node=f"Pill_{nm}")
        else:
            place("capsule", (cx, cy, 0.27))
place("bottle", (-5.9, 1.9, 0))
place("tray", (-5.4, -2.6, 0))
place("chart", (6.6, 0.6, 0), rot_z=-0.1)
place("stamp", (7.7, -2.4, 0))
place("iv", (-11.5, 7.2, -8.05), scale=3.2)
S = 3.0
doc = place("doctor", (0, 7.0, -2.6 - 0.14 * S), scale=S)
for o in doc:
    if o.name.startswith("Arm"):
        o.rotation_euler.x -= 0.95

C.render_preview("clinic.png", cam_loc=(0, -17, 10), target=(0, 0, 0.8), size=(1600, 1000), floor_z=-8.2, fov=36)
