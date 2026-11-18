"""이스터에그 소품 → models/eggs.glb. 노드 Egg_<id> 하나가 누를 수 있는 물체 하나 (반응은 index.html의 EGGS).

좌표는 진료실과 같다 (책상 윗면 z=0, 바닥 z=-8.05, 뒷벽 앞면 y≈12.95). 글자는 Blender 기본 글꼴이라 영문만,
한국어 표지판은 빈 면(SignFace)에 코드가 그린다.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

PI = math.pi
FLOOR = -8.05
C.reset()
P = C.PALETTE
white, teal, deep, mint, coral = C.plastic("white"), C.plastic("teal"), C.plastic("deep", rough=0.45), C.plastic("mint"), C.plastic("coral")
ink = C.material("ink", P["ink"], rough=0.3, coat=0.6)
paper = C.material("paper", "#FFFFFF", rough=0.75, coat=0.0, sheen=0.2)
metal = C.metal_mat()
FRONT = (PI / 2, 0, 0)  # 글자가 -Y(방 안쪽)를 보게


def egg(name, parts):
    root = C.empty(f"Egg_{name}")
    C.parent(parts, root)
    return root


def label_bottle(name, x, y, z, body_col, cap_col, title, sub="", h=1.3, r=0.34, syrup=False):
    body_m = C.material(f"egg_{name}", body_col, rough=0.25, coat=0.7)
    prof = [(0, 0), (r, 0), (r, h * 0.72), (r * 0.5, h * 0.86), (r * 0.42, h), (0, h)] if syrup else \
           [(0, 0), (r, 0), (r, h * 0.82), (r * 0.62, h * 0.92), (r * 0.62, h), (0, h)]
    body = C.lathe(f"{name}_body", prof, body_m, segs=40)
    body.location = (x, y, z)
    cap = C.cylinder(f"{name}_cap", (x, y, z + h + 0.1), (r * 0.42 if syrup else r * 0.66), 0.2, C.plastic(cap_col) if cap_col in P else C.material(f"cap_{cap_col}", cap_col), bevel=0.03)
    lab = C.lathe(f"{name}_label", [(r + 0.006, z + 0.18), (r + 0.006, z + 0.18 + h * 0.48)], paper, segs=40)
    lab.location = (x, y, 0)
    parts = [body, cap, lab]
    parts.append(C.text(f"{name}_title", title, (x, y - r - 0.012, z + 0.18 + h * 0.31), min(0.15, 0.8 / len(title)), ink, rot=FRONT, extrude=0.004))
    if sub:
        parts.append(C.text(f"{name}_sub", sub, (x, y - r - 0.012, z + 0.18 + h * 0.13), 0.065, C.plastic("deep"), rot=FRONT, extrude=0.003))
    return parts


# ── 약장 아래 칸의 약병 4개 (room.py가 이 자리를 비워 둠) ──────────
CX, SHELF_Y, SHELF_Z = -16.0, 12.2, 2.3
bx = lambda k: CX - 3.0 + k * 0.85
egg("hotfix", label_bottle("hotfix", bx(1), SHELF_Y, SHELF_Z, "#C98A3B", "white", "HOTFIX", "FEVER REDUCER"))
egg("rollback", label_bottle("rollback", bx(3), SHELF_Y, SHELF_Z, "#F6A8A0", "deep", "ROLLBACK", "SYRUP  10ml", h=1.5, syrup=True))
egg("lts", label_bottle("lts", bx(5), SHELF_Y, SHELF_Z, "#F8FBFA", "teal", "LTS", "EXP 2038-01-19"))
rm = label_bottle("rmrf", bx(6.15), SHELF_Y, SHELF_Z, "#2A3B40", "#E5484D", "rm -rf /", "DO NOT TAKE")
sx, sy, sz = bx(6.15), SHELF_Y - 0.36, SHELF_Z + 0.98
bone = C.material("bone", "#F4F1EA", rough=0.6, coat=0.1)
rm += [C.sphere("skull", (sx, sy - 0.02, sz + 0.05), (0.11, 0.05, 0.1), bone, segs=24, rings=12),
       C.rbox("jaw", (sx, sy - 0.02, sz - 0.05), (0.12, 0.05, 0.06), bone, 0.02),
       C.sphere("eyeL", (sx - 0.04, sy - 0.07, sz + 0.05), (0.025, 0.01, 0.028), ink, segs=12, rings=6),
       C.sphere("eyeR", (sx + 0.04, sy - 0.07, sz + 0.05), (0.025, 0.01, 0.028), ink, segs=12, rings=6),
       C.rbox("boneA", (sx, sy + 0.005, sz - 0.02), (0.32, 0.02, 0.035), bone, 0.015, rot=(0, 0.6, 0)),
       C.rbox("boneB", (sx, sy + 0.005, sz - 0.02), (0.32, 0.02, 0.035), bone, 0.015, rot=(0, -0.6, 0))]
egg("rmrf", rm)

# ── 고무 오리 (창틀 위) ─────────────────────────────────
dx, dy, dz = 14.4, 12.35, 1.98
yellow = C.material("duck", "#FFD43B", rough=0.35, coat=0.8, coat_rough=0.1)
beak = C.material("beak", "#F2734A", rough=0.4, coat=0.6)
S = 1.5
duck = [C.sphere("duck_body", (dx, dy, dz + 0.3 * S), (0.42 * S, 0.34 * S, 0.3 * S), yellow, segs=40, rings=20),
        C.sphere("duck_tail", (dx + 0.36 * S, dy, dz + 0.45 * S), (0.12 * S, 0.1 * S, 0.14 * S), yellow, segs=20, rings=10),
        C.sphere("duck_head", (dx - 0.22 * S, dy - 0.02, dz + 0.72 * S), (0.24 * S, 0.24 * S, 0.24 * S), yellow, segs=40, rings=20),
        C.sphere("duck_beak", (dx - 0.36 * S, dy - 0.18 * S, dz + 0.68 * S), (0.13 * S, 0.1 * S, 0.05 * S), beak, segs=20, rings=10)]
from mathutils import Vector  # noqa: E402
hc, hr = Vector((dx - 0.22 * S, dy - 0.02, dz + 0.72 * S)), 0.24 * S
for i, d in enumerate((Vector((-0.62, -0.62, 0.44)), Vector((0.2, -0.86, 0.46)))):  # 머리 양옆 (카메라 쪽으로 조금 돌린)
    d.normalize()
    duck.append(C.sphere(f"duck_eyeW{i}", tuple(hc + d * hr * 0.93), (0.075 * S, 0.075 * S, 0.085 * S), C.plastic("paper"), segs=20, rings=10))
    duck.append(C.sphere(f"duck_eye{i}", tuple(hc + d * (hr * 0.93 + 0.045 * S)), (0.045 * S, 0.045 * S, 0.052 * S), ink, segs=16, rings=8))
    duck.append(C.sphere(f"duck_shine{i}", tuple(hc + d * (hr * 0.93 + 0.08 * S) + Vector((0.012, -0.004, 0.025)) * S), (0.014 * S,) * 3, C.plastic("paper"), segs=8, rings=4))
egg("duck", duck)

# ── MONKEY PATCH 반창고 상자 (책상 뒤쪽 왼편, 예전 스탠드 자리) ──────
mx, my = -7.3, 3.5
box_m = C.material("first_aid", "#FFFFFF", rough=0.4, coat=0.5)
peach = C.material("monkey", "#E0A47A", rough=0.6, coat=0.2)
brown = C.material("monkey_fur", "#8A5A3C", rough=0.7, coat=0.1)
plaster = C.material("plaster", "#F2C9A6", rough=0.7, coat=0.0)
mk = [C.rbox("mp_box", (mx, my, 0.33), (1.6, 0.95, 0.66), box_m, 0.08),
      C.rbox("mp_lid", (mx, my, 0.7), (1.66, 1.0, 0.1), teal, 0.04),
      C.rbox("mp_stripe", (mx, my - 0.476, 0.18), (1.6, 0.01, 0.08), teal, 0.004),
      C.text("mp_title", "MONKEY PATCH", (mx + 0.18, my - 0.482, 0.44), 0.11, ink, rot=FRONT, extrude=0.004),
      C.text("mp_sub", "for runtime wounds", (mx + 0.18, my - 0.482, 0.3), 0.06, C.plastic("deep"), rot=FRONT, extrude=0.003),
      C.sphere("mp_face", (mx - 0.55, my - 0.48, 0.4), (0.15, 0.02, 0.15), brown, segs=24, rings=12),
      C.sphere("mp_muzzle", (mx - 0.55, my - 0.5, 0.37), (0.1, 0.02, 0.08), peach, segs=20, rings=10)]
mk += [C.sphere(f"mp_ear{s}", (mx - 0.55 + s * 0.16, my - 0.48, 0.45), (0.05, 0.02, 0.05), peach, segs=12, rings=6) for s in (-1, 1)]
mk += [C.sphere(f"mp_eye{s}", (mx - 0.55 + s * 0.05, my - 0.505, 0.43), (0.018, 0.008, 0.02), ink, segs=10, rings=5) for s in (-1, 1)]
for i, (dxp, tilt) in enumerate(((-0.25, 0.35), (0.1, -0.2), (0.4, 0.15))):  # 상자 위로 삐져나온 반창고
    mk.append(C.rbox(f"mp_plaster{i}", (mx + dxp, my + 0.1, 0.86), (0.7, 0.22, 0.02), plaster, 0.01, rot=(0.5, 0, tilt)))
    mk.append(C.rbox(f"mp_pad{i}", (mx + dxp, my + 0.1, 0.87), (0.22, 0.16, 0.02), C.material("pad_w", "#FFFFFF", rough=0.8, coat=0.0), 0.008, rot=(0.5, 0, tilt)))
egg("monkey", mk)

# ── 금요일 배포 금지 표지판 (뒷벽, 시계와 창문 사이) ─────────────
gx, gz = 6.6, 6.4
sign = [C.rbox("sign_plate", (gx, 12.9, gz), (2.2, 0.08, 2.2), white, 0.1)]
C.bpy.ops.mesh.primitive_plane_add(size=1, location=(gx, 12.855, gz), rotation=FRONT)
face = C.bpy.context.active_object
face.name = "SignFace"
face.scale = (2.0, 2.0, 1)
face.data.materials.append(C.material("sign_face", "#FFFFFF", rough=0.6, coat=0.1))
sign.append(face)
egg("friday", sign)

# ── 벽시계: 2038년 문제의 순간 03:14:07에 멈춤 (초침만 따로 떨림) ─────
kx, ky, kz = 3.4, 12.9, 8.2
clk = [C.cylinder("WallClock", (kx, ky, kz), 1.2, 0.3, teal, rot=FRONT, bevel=0.08),
       C.cylinder("WallClockFace", (kx, 12.72, kz), 1.0, 0.06, C.material("clockface", "#FFFFFF", rough=0.5, coat=0.3), rot=FRONT)]
ticks = [C.rbox(f"Tk{i}", (kx + 0.85 * math.sin(i * PI / 6), 12.672, kz + 0.85 * math.cos(i * PI / 6)), (0.05, 0.02, 0.16 if i % 3 == 0 else 0.09), ink, 0.01, rot=(0, i * PI / 6, 0)) for i in range(12)]
clk.append(C.join(ticks, "ClockTicks"))


def hand(name, ang, length, width, y, mat):
    return C.rbox(name, (kx + math.sin(ang) * length / 2, y, kz + math.cos(ang) * length / 2), (width, 0.02, length), mat, width / 3, rot=(0, ang, 0))


clk.append(hand("HourHand", (3 + 14 / 60) / 12 * 2 * PI, 0.55, 0.08, 12.655, ink))
clk.append(hand("MinHand", (14 + 7 / 60) / 60 * 2 * PI, 0.82, 0.06, 12.645, ink))
pivot = C.empty("SecondPivot", (kx, 12.63, kz))
sec = C.rbox("SecondHand", (kx + math.sin(7 / 60 * 2 * PI) * 0.4, 12.63, kz + math.cos(7 / 60 * 2 * PI) * 0.4), (0.025, 0.015, 0.95), coral, 0.008, rot=(0, 7 / 60 * 2 * PI, 0))
C.parent([sec], pivot)
clk += [pivot, C.sphere("ClockPin", (kx, 12.61, kz), (0.07, 0.03, 0.07), ink, segs=12, rings=6)]
clk.append(C.text("ClockUTC", "UTC", (kx, 12.67, kz - 0.42), 0.12, C.plastic("deep"), rot=FRONT, extrude=0.003))
egg("clock", clk)

# ── /dev/null 페달 휴지통 (책상 오른쪽 앞 바닥, 높이 ≈60cm) ──────────────
tx, ty = 11.6, -3.4
bn = [C.lathe("bin_body", [(0, 0), (0.78, 0), (0.9, 2.3), (0, 2.3)], white, segs=48),
      C.lathe("bin_lid", [(0.0, 2.3), (0.95, 2.3), (0.95, 2.42), (0.6, 2.62), (0.0, 2.66)], teal, segs=48),
      C.rbox("bin_pedal", (0, -0.85, 0.12), (0.6, 0.4, 0.08), deep, 0.03),
      C.rbox("bin_label", (0, -0.86, 1.45), (1.1, 0.02, 0.4), paper, 0.04, rot=(0.05, 0, 0)),
      C.text("bin_text", "/dev/null", (0, -0.875, 1.45), 0.2, ink, rot=FRONT, extrude=0.005)]
binroot = C.empty("bin_scale")
C.parent(bn, binroot)
binroot.location = (tx, ty, FLOOR)
binroot.scale = (1.7,) * 3
egg("devnull", [binroot])

# ── node_modules 이름표 (큰 화분) ───────────────────────────
px, py = 22.4, -13.0  # room.py 큰 화분과 같은 자리
tag = [C.rbox("nm_card", (px - 0.2, py - 1.86, FLOOR + 2.55), (1.5, 0.03, 0.5), paper, 0.05, rot=(0, 0.12, 0)),
       C.text("nm_text", "node_modules", (px - 0.2, py - 1.885, FLOOR + 2.57), 0.15, ink, rot=(PI / 2, 0.12, 0), extrude=0.004),
       C.text("nm_sub", "WATER: npm install", (px - 0.2, py - 1.885, FLOOR + 2.4), 0.07, C.plastic("deep"), rot=(PI / 2, 0.12, 0), extrude=0.003),
       C.tube("nm_string", C.catmull([(px - 0.85, py - 1.85, FLOOR + 2.8), (px - 1.1, py - 1.7, FLOOR + 3.3), (px - 1.3, py - 1.5, FLOOR + 3.38)], 6), 0.012, ink)]
egg("nodemods", tag)

# ── X-ray 판독기 (뒷벽, IV 옆): 갈비뼈 사이에 '버그' ─────────────────
xx, xz = -10.2, 5.4
film = C.material("film", "#1B2A3A", rough=0.4, coat=0.3)
bone_glow = C.emissive("xray_bone", "#CFE6F2", 1.2)
xr = [C.rbox("xr_box", (xx, 12.9, xz), (3.0, 0.3, 3.8), white, 0.08),
      C.rbox("xr_panel", (xx, 12.74, xz), (2.6, 0.04, 3.3), C.emissive("xray_light", "#EAF6FF", 0.6), 0.03),
      C.rbox("xr_film", (xx, 12.715, xz - 0.05), (2.2, 0.01, 2.9), film, 0.02),
      C.rbox("xr_clip", (xx, 12.7, xz + 1.55), (0.8, 0.06, 0.16), metal, 0.03)]
spine = [C.rbox(f"vert{i}", (xx, 12.705, xz + 1.0 - i * 0.24), (0.16, 0.01, 0.16), bone_glow, 0.03) for i in range(9)]
xr.append(C.join(spine, "xr_spine"))
for side in (-1, 1):
    ribs = []
    for i in range(6):
        z0 = xz + 0.9 - i * 0.3
        pts = [(xx + side * 0.1, 12.705, z0), (xx + side * 0.55, 12.705, z0 + 0.06), (xx + side * 0.85, 12.705, z0 - 0.15), (xx + side * 0.8, 12.705, z0 - 0.45)]
        ribs.append(C.tube(f"rib{side}{i}", C.catmull(pts, 6), 0.03, bone_glow))
    xr.append(C.join(ribs, f"xr_ribs{side}"))
bug_m = C.material("bug", "#E5484D", rough=0.5, coat=0.3)
bx2, bz2 = xx + 0.35, xz + 0.05
xr += [C.sphere("bug_body", (bx2, 12.7, bz2), (0.12, 0.01, 0.17), bug_m, segs=16, rings=8),
       C.sphere("bug_head", (bx2, 12.7, bz2 + 0.2), (0.07, 0.01, 0.07), bug_m, segs=12, rings=6)]
legs = [C.rbox(f"leg{s}{k}", (bx2 + s * 0.17, 12.7, bz2 + 0.08 - k * 0.1), (0.16, 0.008, 0.02), bug_m, 0.005, rot=(0, s * (0.4 - k * 0.4), 0)) for s in (-1, 1) for k in range(3)]
xr.append(C.join(legs, "bug_legs"))
xr.append(C.text("xr_text", "CHEST PA  ·  PROD-01", (xx, 12.705, xz - 1.38), 0.1, C.material("xr_label", "#9FD6CB", rough=0.5, coat=0.0), rot=FRONT, extrude=0.003))
egg("xray", xr)

# ── 학위증 (뒷벽, 박사님 머리 위 왼쪽) ─────────────────────
dx2, dz2 = 6.6, 9.75  # 금지 표지판 위 (박사님 머리에 가리지 않게)
gold = C.material("gold", "#C9A23F", rough=0.35, metal=0.6, coat=0.5)
dip = [C.rbox("dip_frame", (dx2, 12.92, dz2), (3.0, 0.14, 2.3), C.material("dip_wood", "#6B4A35", rough=0.5, coat=0.4), 0.06),
       C.rbox("dip_paper", (dx2, 12.84, dz2), (2.6, 0.04, 1.9), C.material("dip_paper", "#FBF6EA", rough=0.8, coat=0.0), 0.02),
       C.text("dip_t1", "DIPLOMA", (dx2, 12.81, dz2 + 0.6), 0.22, ink, rot=FRONT, extrude=0.003),
       C.text("dip_t2", "Doctor of Patchology", (dx2, 12.81, dz2 + 0.2), 0.14, ink, rot=FRONT, extrude=0.003),
       C.text("dip_t3", "/dev/null University", (dx2, 12.81, dz2 - 0.12), 0.11, C.plastic("deep"), rot=FRONT, extrude=0.003),
       C.cylinder("dip_seal", (dx2 + 0.85, 12.81, dz2 - 0.55), 0.22, 0.03, gold, rot=FRONT),
       C.rbox("dip_ribbonA", (dx2 + 0.78, 12.815, dz2 - 0.85), (0.1, 0.01, 0.35), coral, 0.01, rot=(0, 0.3, 0)),
       C.rbox("dip_ribbonB", (dx2 + 0.92, 12.815, dz2 - 0.85), (0.1, 0.01, 0.35), coral, 0.01, rot=(0, -0.3, 0)),
       C.rbox("dip_sign", (dx2 - 0.6, 12.815, dz2 - 0.6), (0.9, 0.01, 0.02), ink, 0.005)]
egg("diploma", dip)

# ── 진료실 200호 문패 (왼쪽 벽, 문 옆) ───────────────────────
plate = [C.rbox("door_plate", (-24.6, -1.6, FLOOR + 15.2), (0.12, 2.6, 1.3), white, 0.08),
         C.rbox("door_plate_bar", (-24.53, -1.6, FLOOR + 15.75), (0.02, 2.6, 0.2), teal, 0.02),
         C.text("door_plate_t", "ROOM 200", (-24.52, -1.6, FLOOR + 15.15), 0.36, ink, rot=(PI / 2, 0, PI / 2), extrude=0.006),
         C.text("door_plate_ok", "OK", (-24.52, -1.6, FLOOR + 14.72), 0.2, C.plastic("teal"), rot=(PI / 2, 0, PI / 2), extrude=0.005)]
egg("room200", plate)

C.export_glb("eggs.glb")
