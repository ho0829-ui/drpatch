"""진료실: 바닥·벽(벽 띠·징두리판)·창문(블라인드)·약장·시력표 액자·벽시계·박사님 의자·큰 화분 → models/room.glb

좌표는 책상과 같다: 책상 윗면 z=0, 바닥 z=-8.05, 박사님 자리 y=+7, 뒷벽 y=+13.
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
wall = C.material("wall", "#CBEAE2", rough=0.85, coat=0.0, sheen=0.1)
lower = C.material("wall_lower", "#E4F3EF", rough=0.7, coat=0.1)
groove = C.material("groove", "#C9E4DD", rough=0.7, coat=0.0)
floor_m = C.material("floor", "#A9D8CD", rough=0.35, coat=0.5, coat_rough=0.3)
seam = C.material("floor_seam", "#98CDBF", rough=0.5, coat=0.0)
metal = C.metal_mat()
objs = []

# 바닥 + 타일 이음새
objs.append(C.rbox("Floor", (0, -14.5, FLOOR - 0.1), (50.4, 55, 0.2), floor_m, 0.02))
lines = [C.rbox(f"FX{i}", (-24 + i * 3, -14.6, FLOOR + 0.012), (0.05, 54.6, 0.006), seam, 0.001) for i in range(17)]
lines += [C.rbox(f"FY{i}", (0, -41 + i * 3, FLOOR + 0.012), (49.6, 0.05, 0.006), seam, 0.001) for i in range(18)]
objs.append(C.join(lines, "FloorSeams"))

# 벽: 뒤·양옆. 아래는 연한 징두리판 + 세로 홈, 가운데 청록 벽 띠, 맨 아래 걸레받이
H = 26
for name, loc, size in (("BackWall", (0, 13.2, FLOOR + H / 2), (50, 0.4, H)),
                        ("LeftWall", (-25, -14.5, FLOOR + H / 2), (0.4, 55, H)),
                        ("RightWall", (25, -14.5, FLOOR + H / 2), (0.4, 55, H))):
    objs.append(C.rbox(name, loc, size, wall, 0.02))
objs.append(C.rbox("Wainscot", (0, 12.97, FLOOR + 2.8), (49.46, 0.08, 5.6), lower, 0.01))
grooves = [C.rbox(f"G{i}", (-24.5 + i * 1.4, 12.92, FLOOR + 2.8), (0.05, 0.03, 5.4), groove, 0.005) for i in range(36)]
objs.append(C.join(grooves, "WainscotGrooves"))
for side, x in (("L", -24.78), ("R", 24.78)):
    # 옆벽 띠는 방 앞쪽 끝(y=-42)부터 뒷벽 띠 바로 앞(y=12.9)까지 — 모서리에서 뒷벽 띠와 겹치지 않게
    span, mid = 12.9 + 42, (12.9 - 42) / 2
    objs.append(C.rbox(f"Wainscot{side}", (x, mid, FLOOR + 2.8), (0.08, span, 5.6), lower, 0.01))
    objs.append(C.rbox(f"Rail{side}", (x, mid, FLOOR + 5.7), (0.3, span, 0.4), teal, 0.05))
    objs.append(C.rbox(f"Base{side}", (x, mid, FLOOR + 0.25), (0.25, span, 0.5), deep, 0.04))
objs.append(C.rbox("Rail", (0, 12.85, FLOOR + 5.7), (49.4, 0.3, 0.4), teal, 0.05))
objs.append(C.rbox("Baseboard", (0, 12.88, FLOOR + 0.25), (49.5, 0.25, 0.5), deep, 0.04))
# 천장 + 조명 판
objs.append(C.rbox("Ceiling", (0, -14.5, FLOOR + H), (50.4, 55, 0.3), C.material("ceiling", "#F4FAF8", rough=0.9, coat=0.0), 0.02))
for k, yy in enumerate((6, -6, -18)):
    objs.append(C.rbox(f"CeilLight{k}", (0, yy, FLOOR + H - 0.2), (8, 3, 0.1), C.emissive("ceil_light", "#FFFFFF", 2.0), 0.03))
objs.append(C.rbox("Crown", (0, 12.9, FLOOR + H - 0.3), (49.5, 0.3, 0.3), white, 0.06))

# 창문 (뒷벽 오른쪽) + 블라인드
wx, wz, ww, wh = 12.5, 5.2, 7.6, 6.0
objs.append(C.rbox("WindowFrame", (wx, 12.92, wz), (ww + 0.6, 0.3, wh + 0.6), white, 0.08))
C.bpy.ops.mesh.primitive_plane_add(size=1, location=(wx, 12.75, wz), rotation=(PI / 2, 0, 0))
glass = C.bpy.context.active_object
glass.name = "WindowSky"
glass.scale = (ww, wh, 1)
glass.data.materials.append(C.emissive("sky", "#E3F6FF", 1.6))
objs.append(glass)
for i, z in enumerate((wz - wh / 2 + 0.05, wz, wz + wh / 2 - 0.05)):
    objs.append(C.rbox(f"WinH{i}", (wx, 12.72, z), (ww, 0.18, 0.16), white, 0.04))
objs.append(C.rbox("WinV", (wx, 12.72, wz), (0.16, 0.18, wh), white, 0.04))
objs.append(C.rbox("Sill", (wx, 12.5, wz - wh / 2 - 0.35), (ww + 1.2, 0.9, 0.25), white, 0.06))
slats = [C.rbox(f"Slat{i}", (wx, 12.6, wz + wh / 2 - 0.35 - i * 0.32), (ww - 0.2, 0.05, 0.2), C.material("slat", "#F4FAF8", rough=0.5, coat=0.2), 0.02, rot=(0.5, 0, 0)) for i in range(8)]
objs.append(C.join(slats, "Blinds"))
objs.append(C.rbox("BlindRail", (wx, 12.6, wz + wh / 2 - 0.1), (ww, 0.25, 0.22), white, 0.04))
cord_m = C.material("cord", "#F4FAF8", rough=0.7, coat=0.0)
objs.append(C.tube("BlindCord", C.catmull([(wx + ww / 2 - 0.5, 12.5, wz + wh / 2 - 0.2), (wx + ww / 2 - 0.48, 12.47, wz + 1.0), (wx + ww / 2 - 0.5, 12.45, wz + 0.2)], 6), 0.018, cord_m))
objs.append(C.lathe("BlindTassel", [(0.0, -0.32), (0.07, -0.3), (0.05, 0.0), (0.0, 0.02)], teal, segs=16))
objs[-1].location = (wx + ww / 2 - 0.5, 12.45, wz + 0.18)
# 창틀 위 작은 화분
objs.append(C.lathe("SillPot", [(0, 0), (0.35, 0), (0.42, 0.55), (0, 0.55)], coral))
objs[-1].location = (wx - 2.5, 12.5, wz - wh / 2 - 0.22)
lm = C.material("leafA", "#5DAE8B", rough=0.45, coat=0.4)
for k in range(5):
    lf = C.leaf(f"SillLeaf{k}", 0.6, 0.22, 0.1, lm)
    lf.location = (wx - 2.5, 12.5, wz - wh / 2 + 0.33)
    lf.rotation_euler = (0.5, 0, k * 2 * PI / 5)
    objs.append(lf)

# 약장 (뒷벽 왼쪽): 아래 수납장 + 위 유리 진열장
cx = -16.0
objs.append(C.rbox("CabinetLow", (cx, 11.7, FLOOR + 2.9), (7.2, 2.4, 5.8), white, 0.08))
for i, dx in enumerate((-1.8, 1.8)):
    objs.append(C.rbox(f"Door{i}", (cx + dx, 10.48, FLOOR + 2.7), (3.4, 0.06, 5.0), C.material("door", "#F2F8F6", rough=0.45, coat=0.3), 0.05))
    objs.append(C.rbox(f"Handle{i}", (cx + dx * 0.15, 10.4, FLOOR + 4.2), (0.12, 0.12, 0.9), teal, 0.05))
objs.append(C.rbox("Counter", (cx, 11.6, FLOOR + 5.95), (7.6, 2.7, 0.3), deep, 0.06))
# 위 진열장은 앞이 뚫린 틀 (꽉 찬 상자면 안의 약병이 앞판에 가려 안 보인다)
objs.append(C.rbox("CabinetBack", (cx, 12.92, 4.6), (7.2, 0.1, 5.4), C.material("cab_back", "#E4F3EF", rough=0.7, coat=0.1), 0.02))
for name, loc, size in (("CabinetTop", (cx, 12.25, 7.24), (7.2, 1.5, 0.12)), ("CabinetBottom", (cx, 12.25, 1.96), (7.2, 1.5, 0.12)),
                        ("CabinetL", (cx - 3.54, 12.25, 4.6), (0.12, 1.5, 5.4)), ("CabinetR", (cx + 3.54, 12.25, 4.6), (0.12, 1.5, 5.4))):
    objs.append(C.rbox(name, loc, size, white, 0.04))
C.bpy.ops.mesh.primitive_plane_add(size=1, location=(cx, 11.48, 4.6), rotation=(PI / 2, 0, 0))
cab_glass = C.bpy.context.active_object
cab_glass.name = "CabinetGlass"
cab_glass.scale = (6.6, 4.8, 1)
cab_glass.data.materials.append(C.glass_mat("#EAF7F4", "cab_glass"))
objs.append(cab_glass)
objs.append(C.rbox("CabinetMullion", (cx, 11.46, 4.6), (0.12, 0.1, 4.8), white, 0.03))
bottle_cols = ["#C98A3B", "#FFFFFF", "#3E9E98", "#F2734A", "#B9E2D9", "#C98A3B", "#1F6F6B", "#FFFFFF"]
for row, z in enumerate((2.3, 4.6)):
    objs.append(C.rbox(f"Shelf{row}", (cx, 12.2, z - 0.05), (6.8, 1.3, 0.1), white, 0.02))
    for k in range(8):
        if row == 0 and k in (1, 3, 5, 6):
            continue  # 이스터에그 약병 자리 (eggs.py)
        h = 0.9 + 0.35 * ((k * 7 + row * 3) % 3)
        r = 0.28 + 0.06 * ((k + row) % 2)
        col = bottle_cols[(k + row * 3) % len(bottle_cols)]
        b = C.lathe(f"Med{row}{k}", [(0, 0), (r, 0), (r, h * 0.8), (r * 0.55, h * 0.9), (r * 0.55, h), (0, h)],
                    C.material(f"med_{col}", col, rough=0.25, coat=0.6, transmission=0.3 if col == "#C98A3B" else 0.0), segs=24)
        b.location = (cx - 3.0 + k * 0.85, 12.2, z)
        objs.append(b)
        objs.append(C.cylinder(f"MedCap{row}{k}", (cx - 3.0 + k * 0.85, 12.2, z + h + 0.08), r * 0.6, 0.16, white if col != "#FFFFFF" else teal))
# 카운터 위 설압자 통
jar_x = cx + 2.4
objs.append(C.lathe("DepressorJar", [(0, 0), (0.45, 0), (0.45, 1.2), (0, 1.2)], C.glass_mat("#F0FAF7", "jar_glass")))
objs[-1].location = (jar_x, 11.4, FLOOR + 6.1)
for k in range(7):
    a = k * 2 * PI / 7
    objs.append(C.rbox(f"Stick{k}", (jar_x + 0.2 * math.cos(a), 11.4 + 0.2 * math.sin(a), FLOOR + 6.1 + 1.0), (0.14, 0.03, 1.7), C.material("stick", "#E8D4AE", rough=0.8, coat=0.0), 0.02, rot=(0.12 * math.sin(a), 0.12 * math.cos(a), a)))

# 시력표 액자 (숨은 글자: DR PATCH SUDO)
fx, fz = -6.5, 5.6
objs.append(C.rbox("ChartFrame", (fx, 12.95, fz), (3.2, 0.2, 4.4), deep, 0.06))
objs.append(C.rbox("ChartPaper", (fx, 12.83, fz), (2.8, 0.06, 4.0), C.material("poster", "#FFFFFF", rough=0.8, coat=0.0), 0.02))
for i, (row, size) in enumerate((("D", 0.7), ("R P", 0.46), ("A T C", 0.34), ("H S U", 0.26), ("D O P A", 0.2), ("T C H D R", 0.15))):
    objs.append(C.text(f"Eye{i}", row, (fx, 12.79, fz + 1.45 - i * 0.58 + (0.1 if i == 0 else 0)), size, ink, rot=(PI / 2, 0, 0), extrude=0.005))
# 두 번째 액자: 서버 해부도 (랙 그림)
gx, gz = -2.6, 6.2
objs.append(C.rbox("RackFrame", (gx, 12.95, gz), (2.6, 0.2, 3.2), deep, 0.06))
objs.append(C.rbox("RackPaper", (gx, 12.83, gz), (2.2, 0.06, 2.8), C.material("poster2", "#EAF6F3", rough=0.8, coat=0.0), 0.02))
for i in range(5):
    objs.append(C.rbox(f"RackU{i}", (gx, 12.79, gz + 0.9 - i * 0.42), (1.4, 0.04, 0.3), teal if i != 2 else coral, 0.04))
    objs.append(C.sphere(f"RackLed{i}", (gx - 0.5, 12.76, gz + 0.9 - i * 0.42), (0.05, 0.02, 0.05), mint, segs=12, rings=6))
objs.append(C.text("RackTitle", "SERVER", (gx, 12.79, gz - 1.15), 0.2, ink, rot=(PI / 2, 0, 0), extrude=0.005))

# 벽시계는 이스터에그(03:14:07에 멈춤)라 eggs.py로 옮김

# 박사님 의자 (y=+7 자리 뒤) — 등받이만 어깨 너머로 보인다
chair = C.material("chair", "#2F8A84", rough=0.6, coat=0.2, sheen=0.5)
objs.append(C.rbox("ChairBack", (0, 9.7, -0.6), (4.6, 0.7, 4.4), chair, 0.35))
objs.append(C.rbox("ChairSeat", (0, 7.4, -3.0), (4.6, 4.0, 0.7), chair, 0.3))
objs.append(C.rbox("ChairSpine", (0, 9.6, -3.2), (0.4, 0.4, 2.0), metal, 0.1))
objs.append(C.cylinder("ChairPost", (0, 7.4, -5.4), 0.22, 4.2, metal))
for k in range(5):
    a = k * 2 * PI / 5
    objs.append(C.rbox(f"ChairLeg{k}", (1.0 * math.cos(a), 7.4 + 1.0 * math.sin(a), FLOOR + 0.55), (2.0, 0.3, 0.2), ink, 0.08, rot=(0, 0, a)))
    objs.append(C.sphere(f"Caster{k}", (2.0 * math.cos(a), 7.4 + 2.0 * math.sin(a), FLOOR + 0.22), (0.22, 0.22, 0.22), ink, segs=16, rings=8))

# 큰 화분 (오른쪽 앞 바닥)
pxx, pyy = 22.4, -13.0  # 오른쪽 앞 구석 (침대는 오른쪽 벽을 따라 놓임)
objs.append(C.lathe("FloorPot", [(0, 0), (1.3, 0), (1.7, 3.2), (1.8, 3.4), (0, 3.4)], white))
objs[-1].location = (pxx, pyy, FLOOR)
objs.append(C.lathe("FloorPotBand", [(1.66, 2.6), (1.72, 2.6), (1.74, 3.0), (1.68, 3.0)], teal))
objs[-1].location = (pxx, pyy, FLOOR)
for ring, (count, length, width, tilt, col) in enumerate(((7, 4.2, 0.9, 0.55, "#4F9E7E"), (6, 3.6, 0.8, 0.3, "#69B592"), (4, 3.0, 0.7, 0.15, "#8ACBA8"))):
    lmat = C.material(f"bigleaf{ring}", col, rough=0.45, coat=0.4, sheen=0.3)
    for k in range(count):
        lf = C.leaf(f"BigLeaf{ring}_{k}", length, width, 0.8, lmat)
        lf.location = (pxx, pyy, FLOOR + 3.3)
        lf.rotation_euler = (1.4 - tilt * 1.5, 0, k * 2 * PI / count + ring * 0.5)
        objs.append(lf)

root = C.empty("Room")
C.parent([o for o in objs if o.parent is None], root)
C.export_glb("room.glb")
