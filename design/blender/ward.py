"""병실 소품 → models/ward.glb (움직이지 않음, 코드가 재질별로 합친다).

진료 침대(종이 시트 롤·베개·발판) · 칸막이 커튼과 천장 레일 · 벽걸이 혈압계 · 휠체어 ·
세면대 세트(거울·비누·손 소독제·종이 타월·장갑 상자) · 의사용 키 체중계.
좌표는 진료실과 같다 (바닥 z=-8.05, 뒷벽 앞면 y≈12.95, 왼쪽 벽 안쪽 x≈-24.8, 천장 z≈17.95).
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

PI = math.pi
FLOOR = -8.05
CEIL = 17.8
C.reset()
P = C.PALETTE
white, teal, deep, mint, coral = C.plastic("white"), C.plastic("teal"), C.plastic("deep", rough=0.45), C.plastic("mint"), C.plastic("coral")
ink = C.material("ink", P["ink"], rough=0.3, coat=0.6)
metal = C.metal_mat()
paper = C.material("paper", "#FFFFFF", rough=0.8, coat=0.0, sheen=0.3)
vinyl = C.material("vinyl", "#3E9E98", rough=0.55, coat=0.3, sheen=0.4)
FRONT = (PI / 2, 0, 0)
objs = []

# ── 진료 침대 (창가, 오른쪽 뒤) ─────────────────────────
bx, by, top = 17.0, 8.7, -2.7
objs.append(C.rbox("BedBase", (bx, by, FLOOR + 2.325), (8.2, 2.8, 4.65), white, 0.12))  # 윗면 = 매트리스 바닥
objs.append(C.rbox("BedBaseStripe", (bx, by - 1.41, FLOOR + 3.6), (8.2, 0.02, 0.18), teal, 0.01))
for i, dx in enumerate((-2.7, 0, 2.7)):  # 아래 서랍
    objs.append(C.rbox(f"BedDrawer{i}", (bx + dx, by - 1.41, FLOOR + 1.6), (2.5, 0.04, 1.8), C.material("drawer", "#F2F8F6", rough=0.45, coat=0.3), 0.05))
    objs.append(C.rbox(f"BedHandle{i}", (bx + dx, by - 1.45, FLOOR + 2.2), (0.8, 0.06, 0.1), deep, 0.03))
objs.append(C.rbox("BedPlinth", (bx, by, FLOOR + 0.12), (8.0, 2.6, 0.24), deep, 0.04))
objs.append(C.rbox("Mattress", (bx - 1.0, by, top - 0.35), (7.0, 3.3, 0.7), vinyl, 0.28))
head = C.rbox("Headrest", (bx + 3.3, by, top - 0.05), (2.4, 3.3, 0.7), vinyl, 0.28, rot=(0, -0.32, 0))
objs.append(head)
objs.append(C.rbox("PaperSheet", (bx - 0.4, by, top + 0.012), (8.0, 2.5, 0.015), paper, 0.005))
objs.append(C.rbox("Pillow", (bx + 3.6, by, top + 0.65), (1.4, 2.4, 0.5), C.material("pillow", "#FFFFFF", rough=0.9, coat=0.0, sheen=0.6), 0.22, rot=(0, -0.32, 0)))
objs.append(C.cylinder("PaperRoll", (bx - 4.75, by, top - 0.2), 0.4, 2.9, paper, rot=(PI / 2, 0, 0)))
objs.append(C.cylinder("RollCore", (bx - 4.75, by, top - 0.2), 0.12, 3.0, C.material("core", "#C9A77A", rough=0.8, coat=0.0), rot=(PI / 2, 0, 0)))
for s in (-1, 1):
    objs.append(C.rbox(f"RollArm{s}", (bx - 4.6, by + s * 1.55, top - 0.5), (0.5, 0.1, 0.9), metal, 0.04))
# 2단 발판
objs.append(C.rbox("StepLow", (bx - 1.5, by - 2.3, FLOOR + 0.6), (2.4, 1.6, 1.2), white, 0.1))
objs.append(C.rbox("StepLowTread", (bx - 1.5, by - 2.3, FLOOR + 1.23), (2.3, 1.5, 0.08), deep, 0.03))
objs.append(C.rbox("StepHigh", (bx - 1.5, by - 1.85, FLOOR + 1.8), (2.4, 0.8, 1.2), white, 0.1))
objs.append(C.rbox("StepHighTread", (bx - 1.5, by - 1.85, FLOOR + 2.43), (2.3, 0.7, 0.08), deep, 0.03))

# ── 칸막이 커튼 + 천장 레일 (침대 왼쪽 끝에 반쯤 걷힘) ───────────
objs.append(C.rbox("CurtainTrack", (17.6, 5.6, CEIL - 0.25), (12.4, 0.18, 0.12), metal, 0.04))
objs.append(C.rbox("CurtainTrackSide", (23.8, 9.3, CEIL - 0.25), (0.18, 7.4, 0.12), metal, 0.04))
curtain_m = C.material("curtain", "#BFE3DA", rough=0.85, coat=0.0, sheen=0.8)
cx0, cx1, nz, nx = 20.6, 23.7, 2, 48  # 벽 쪽으로 걷어 둠 (침대가 보이게)
verts, faces = [], []
for j, z in enumerate((CEIL - 0.6, FLOOR + 1.4)):
    for i in range(nx + 1):
        t = i / nx
        verts.append((cx0 + (cx1 - cx0) * t, 5.6 + 0.28 * math.sin(t * PI * 9), z))
for i in range(nx):
    faces.append((i, i + 1, nx + 2 + i, nx + 1 + i))
cur = C.mesh_obj("Curtain", verts, faces, curtain_m)
C.solidify(cur, 0.04)
objs.append(cur)
objs.append(C.rbox("CurtainHem", (22.15, 5.6, FLOOR + 1.45), (3.2, 0.6, 0.18), C.material("curtain_hem", "#9FD6CB", rough=0.8, coat=0.0), 0.06))
hooks = [C.torus(f"Hook{i}", (cx0 + i * 0.34, 5.6, CEIL - 0.45), 0.08, 0.02, metal, rot=FRONT) for i in range(10)]
objs.append(C.join(hooks, "CurtainHooks"))

# ── 벽걸이 혈압계 (침대 머리 위) ────────────────────────
gx, gz = 21.4, 3.6
objs.append(C.rbox("BPMount", (gx, 12.9, gz - 0.6), (1.4, 0.12, 2.4), white, 0.08))
objs.append(C.cylinder("BPDial", (gx, 12.75, gz), 0.62, 0.22, teal, rot=FRONT, bevel=0.05))
objs.append(C.cylinder("BPFace", (gx, 12.63, gz), 0.52, 0.04, C.material("bpface", "#FFFFFF", rough=0.5, coat=0.4), rot=FRONT))
bp_ticks = [C.rbox(f"BT{i}", (gx + 0.44 * math.sin(-2.4 + i * 0.48), 12.6, gz + 0.44 * math.cos(-2.4 + i * 0.48)), (0.025, 0.015, 0.08), ink, 0.005, rot=(0, -2.4 + i * 0.48, 0)) for i in range(11)]
objs.append(C.join(bp_ticks, "BPTicks"))
objs.append(C.rbox("BPNeedle", (gx + 0.15, 12.58, gz + 0.12), (0.03, 0.015, 0.42), coral, 0.01, rot=(0, 0.9, 0)))
objs.append(C.rbox("BPBasket", (gx, 12.6, gz - 1.45), (1.2, 0.5, 0.6), deep, 0.06))
objs.append(C.rbox("BPCuff", (gx, 12.45, gz - 1.25), (1.0, 0.35, 0.45), C.material("cuff", "#2F5E8E", rough=0.8, coat=0.0, sheen=0.4), 0.12))
objs.append(C.tube("BPHose", C.catmull([(gx, 12.6, gz - 0.55), (gx - 0.5, 12.5, gz - 0.9), (gx - 0.6, 12.4, gz - 1.6), (gx - 0.3, 12.35, gz - 2.2), (gx + 0.3, 12.4, gz - 2.0), (gx + 0.3, 12.45, gz - 1.3)], 8), 0.035, ink))
objs.append(C.sphere("BPBulb", (gx + 0.62, 12.4, gz - 1.9), (0.16, 0.16, 0.24), ink, segs=20, rings=10))

# ── 휠체어 (오른쪽 앞 바닥) ─────────────────────────────
wc = []
wx, wy = 18.6, -5.0
R = 1.45
for s in (-1, 1):
    wc.append(C.torus(f"WheelTire{s}", (0, s * 1.15, R), R, 0.1, ink, rot=FRONT))
    wc.append(C.torus(f"WheelRim{s}", (0, s * 1.22, R), R - 0.18, 0.035, metal, rot=FRONT))
    wc.append(C.cylinder(f"Hub{s}", (0, s * 1.12, R), 0.15, 0.12, metal, rot=FRONT))
    spokes = [C.rbox(f"Spoke{s}{k}", (0, s * 1.13, R), (0.03, 0.02, 2 * R - 0.25), metal, 0.008, rot=(0, k * PI / 6, 0)) for k in range(6)]
    wc.append(C.join(spokes, f"Spokes{s}"))
    wc.append(C.sphere(f"Caster{s}", (-1.9, s * 0.95, 0.32), (0.32, 0.12, 0.32), ink, segs=20, rings=10))
    wc.append(C.tube(f"Frame{s}", C.catmull([(-1.9, s * 0.95, 0.65), (-1.6, s * 1.0, 1.7), (0.0, s * 1.0, 1.75), (0.35, s * 1.0, 3.6), (0.75, s * 1.0, 4.0)], 8), 0.05, metal))
    wc.append(C.cylinder(f"Grip{s}", (0.95, s * 1.0, 4.0), 0.08, 0.5, ink, rot=(0, PI / 2, 0)))
    wc.append(C.rbox(f"Footrest{s}", (-2.2, s * 0.45, 0.7), (0.6, 0.7, 0.08), ink, 0.03))
    wc.append(C.rbox(f"Armrest{s}", (-0.3, s * 1.0, 2.9), (1.6, 0.18, 0.14), ink, 0.06))
wc.append(C.rbox("WcSeat", (-0.4, 0, 1.85), (1.9, 2.0, 0.22), vinyl, 0.08))
wc.append(C.rbox("WcBack", (0.45, 0, 2.9), (0.16, 2.0, 1.9), vinyl, 0.06, rot=(0, -0.18, 0)))
wheel = C.empty("Wheelchair", (0, 0, 0))
C.parent(wc, wheel)
wheel.location = (wx, wy, FLOOR)
wheel.rotation_euler = (0, 0, 2.5)
objs.append(wheel)

# ── 세면대 세트 (왼쪽 벽) ───────────────────────────────
WX = -24.75
sy = 3.0
basin = C.lathe("Basin", [(0.0, -0.6), (0.9, -0.55), (1.25, 0.0), (1.3, 0.12), (1.22, 0.14), (0.85, -0.42), (0.0, -0.46)], white, segs=48)
basin.location = (WX + 1.35, sy, -1.4)
basin.scale = (0.9, 1.3, 1.0)
objs.append(basin)
objs.append(C.rbox("BasinBracket", (WX + 0.25, sy, -2.0), (0.5, 1.6, 1.0), white, 0.06))
objs.append(C.tube("Faucet", C.catmull([(WX + 0.35, sy, -1.1), (WX + 0.4, sy, -0.3), (WX + 0.9, sy, -0.1), (WX + 1.25, sy, -0.45)], 8), 0.07, metal))
objs.append(C.rbox("FaucetLever", (WX + 0.45, sy, -0.15), (0.12, 0.7, 0.08), metal, 0.03))
objs.append(C.rbox("MirrorFrame", (WX + 0.08, sy, 2.6), (0.12, 2.6, 3.2), teal, 0.08))
C.bpy.ops.mesh.primitive_plane_add(size=1, location=(WX + 0.16, sy, 2.6), rotation=(PI / 2, 0, PI / 2))
mirror = C.bpy.context.active_object
mirror.name = "Mirror"
mirror.scale = (2.3, 2.9, 1)
mirror.data.materials.append(C.material("mirror", "#DCEFF0", rough=0.04, metal=1.0, coat=0.0))
objs.append(mirror)
objs.append(C.rbox("SoapBox", (WX + 0.25, sy - 1.9, 0.4), (0.4, 0.7, 1.1), white, 0.06))
objs.append(C.rbox("SoapWindow", (WX + 0.46, sy - 1.9, 0.5), (0.02, 0.4, 0.4), C.glass_mat("#F6A8A0", "soap_window"), 0.02))
objs.append(C.rbox("SoapPush", (WX + 0.48, sy - 1.9, -0.05), (0.12, 0.45, 0.15), teal, 0.04))
objs.append(C.rbox("TowelBox", (WX + 0.35, sy + 2.3, 0.2), (0.7, 1.6, 1.8), white, 0.08))
objs.append(C.rbox("TowelSlot", (WX + 0.71, sy + 2.3, -0.65), (0.02, 1.2, 0.08), ink, 0.01))
objs.append(C.rbox("Towel", (WX + 0.74, sy + 2.3, -0.85), (0.02, 0.9, 0.4), paper, 0.01))
sani = C.lathe("Sanitizer", [(0, 0), (0.22, 0), (0.22, 0.6), (0.1, 0.7), (0.1, 0.8), (0, 0.8)], C.material("sanitizer", "#CFEFE6", rough=0.15, coat=1.0, transmission=0.6), segs=24)
sani.location = (WX + 1.0, sy - 0.75, 0.12)
objs.append(sani)
objs.append(C.cylinder("SaniPump", (WX + 1.0, sy - 0.75, 1.0), 0.06, 0.22, white))
objs.append(C.rbox("SaniNozzle", (WX + 1.12, sy - 0.75, 1.1), (0.24, 0.06, 0.05), white, 0.02))
# 장갑 상자 3개 (벽걸이)
objs.append(C.rbox("GloveRack", (WX + 0.08, sy - 4.2, 1.2), (0.12, 2.6, 3.2), metal, 0.04))
for i, (col, z) in enumerate((("#7FC8E8", 2.3), ("#B9E2D9", 1.2), ("#C7B9EC", 0.1))):
    objs.append(C.rbox(f"GloveBox{i}", (WX + 0.45, sy - 4.2, z), (0.6, 2.2, 0.9), white, 0.05))
    objs.append(C.rbox(f"GloveLabel{i}", (WX + 0.76, sy - 4.2, z), (0.02, 2.2, 0.25), C.material(f"glove_lab{i}", col, rough=0.6, coat=0.0), 0.01))
    objs.append(C.sphere(f"Glove{i}", (WX + 0.8, sy - 4.2, z + 0.35), (0.12, 0.35, 0.22), C.material(f"glove{i}", col, rough=0.5, coat=0.2, sheen=0.5), segs=20, rings=10))

# ── 의사용 키 체중계 (세면대 옆 바닥) ────────────────────
kx, ky = -21.8, -3.5
objs.append(C.rbox("ScalePlate", (kx, ky, FLOOR + 0.3), (2.0, 2.0, 0.6), white, 0.1))
objs.append(C.rbox("ScaleMat", (kx, ky, FLOOR + 0.62), (1.7, 1.7, 0.04), C.material("scale_mat", "#2E7A75", rough=0.85, coat=0.0), 0.02))
objs.append(C.rbox("ScaleColumn", (kx + 0.75, ky, FLOOR + 3.4), (0.3, 0.3, 5.6), white, 0.06))
objs.append(C.rbox("ScaleBeam", (kx + 0.4, ky, FLOOR + 5.6), (1.6, 0.16, 0.35), metal, 0.04))
objs.append(C.rbox("ScalePoise", (kx + 0.1, ky, FLOOR + 5.6), (0.18, 0.24, 0.45), ink, 0.03))
objs.append(C.cylinder("HeightRod", (kx + 0.75, ky, FLOOR + 7.0), 0.05, 2.6, metal))
objs.append(C.rbox("HeightHead", (kx + 0.4, ky, FLOOR + 8.2), (0.8, 0.12, 0.06), metal, 0.02))

root = C.empty("Ward")
C.parent([o for o in objs if o.parent is None], root)
C.export_glb("ward.glb")
