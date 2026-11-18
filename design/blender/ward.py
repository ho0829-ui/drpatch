"""병실 소품 → models/ward.glb (움직이지 않음, 코드가 재질별로 합친다).

크기 기준: 책상 높이 8단위 = 75cm → 1단위 ≈ 9.4cm. 실제 병원 가구 크기에 맞춘다.
좌표는 진료실과 같다 (바닥 z=-8.05, 뒷벽 앞면 y≈12.95, 왼쪽 벽 안쪽 x≈-24.8, 오른쪽 벽 안쪽 x≈24.8, 천장 z≈17.95).
코드가 찾는 이름: TVFace (대기 번호 모니터 화면, 글자는 코드가 그림)
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
steel = C.material("steel", "#D7DFE0", rough=0.22, metal=0.9, coat=0.4)
paper = C.material("paper", "#FFFFFF", rough=0.8, coat=0.0, sheen=0.3)
vinyl = C.material("vinyl", "#3E9E98", rough=0.55, coat=0.3, sheen=0.4)
seat_coral = C.material("seat_coral", "#F2734A", rough=0.45, coat=0.5)
FRONT = (PI / 2, 0, 0)
objs = []


def group(name, parts, loc, rot_z=0.0, scale=1.0):
    g = C.empty(name)
    C.parent(parts, g)
    g.location = loc
    g.rotation_euler = (0, 0, rot_z)
    g.scale = (scale,) * 3
    objs.append(g)
    return g


# ── 진료 침대: 오른쪽 벽을 따라 (길이 190cm=20, 폭 70cm=7.4, 높이 75cm=8) ──────────
L, W, H = 20.0, 7.4, 8.0
bed = [C.rbox("BedBase", (0, 0, 3.2), (W - 0.6, L - 1.4, 6.4), white, 0.25),
       C.rbox("BedPlinth", (0, 0, 0.2), (W - 0.9, L - 1.8, 0.4), deep, 0.06),
       C.rbox("BedStripe", (-(W - 0.6) / 2 - 0.01, 0, 5.4), (0.04, L - 1.4, 0.3), teal, 0.02)]
for i, yy in enumerate((-5.6, 0, 5.6)):
    bed.append(C.rbox(f"BedDrawer{i}", (-(W - 0.6) / 2 - 0.02, yy, 2.6), (0.06, 5.0, 3.6), C.material("drawer", "#F2F8F6", rough=0.45, coat=0.3), 0.08))
    bed.append(C.rbox(f"BedHandle{i}", (-(W - 0.6) / 2 - 0.1, yy, 3.9), (0.12, 1.8, 0.22), deep, 0.06))
bed.append(C.rbox("Mattress", (0, -2.2, H - 0.75), (W, L - 5.4, 1.5), vinyl, 0.6))
bed.append(C.rbox("Headrest", (0, 6.6, H - 0.2), (W, 5.6, 1.5), vinyl, 0.6, rot=(0.38, 0, 0)))
bed.append(C.rbox("PaperSheet", (0, -1.0, H + 0.02), (W - 2.2, L - 3.0, 0.02), paper, 0.006))
bed.append(C.rbox("Pillow", (0, 7.4, H + 1.4), (W - 1.8, 2.8, 1.0), C.material("pillow", "#FFFFFF", rough=0.9, coat=0.0, sheen=0.6), 0.45, rot=(0.38, 0, 0)))
bed.append(C.cylinder("PaperRoll", (0, -L / 2 + 0.2, H - 0.5), 0.85, W - 1.2, paper, rot=(0, PI / 2, 0)))
bed.append(C.cylinder("RollCore", (0, -L / 2 + 0.2, H - 0.5), 0.25, W - 1.0, C.material("core", "#C9A77A", rough=0.8, coat=0.0), rot=(0, PI / 2, 0)))
for s in (-1, 1):
    bed.append(C.rbox(f"RollArm{s}", (s * (W / 2 - 0.4), -L / 2 + 0.5, H - 1.0), (0.2, 1.0, 1.8), steel, 0.06))
group("ExamBed", bed, (20.6, 1.6, FLOOR))
step = [C.rbox("StepLow", (0, 0, 1.1), (4.2, 3.2, 2.2), white, 0.15), C.rbox("StepLowTread", (0, 0, 2.24), (4.0, 3.0, 0.1), deep, 0.04),
        C.rbox("StepHigh", (0.9, 0, 3.3), (2.4, 3.2, 2.2), white, 0.15), C.rbox("StepHighTread", (0.9, 0, 4.44), (2.2, 3.0, 0.1), deep, 0.04)]
group("Step", step, (14.4, 0.2, FLOOR))
gas = [C.rbox("GasRail", (0, 0, 0), (8.0, 0.4, 1.6), white, 0.12), C.rbox("GasStripe", (0, -0.21, 0.55), (8.0, 0.02, 0.18), teal, 0.02)]
for i, col in enumerate(("#3E9E98", "#F8FBFA", "#F5C518")):
    gas.append(C.cylinder(f"Outlet{i}", (-2.4 + i * 2.4, -0.25, -0.15), 0.45, 0.2, C.material(f"outlet{i}", col, rough=0.4, coat=0.5), rot=FRONT, bevel=0.05))
    gas.append(C.cylinder(f"OutletHole{i}", (-2.4 + i * 2.4, -0.36, -0.15), 0.15, 0.06, ink, rot=FRONT))
group("GasPanel", gas, (20.6, 12.7, 2.8))
lamp = [C.rbox("LampWall", (0, 0, 0), (1.0, 0.3, 1.6), white, 0.1),
        C.tube("LampArmA", C.catmull([(0, -0.2, 0.4), (0, -2.0, 1.4), (0, -3.8, 1.2)], 8), 0.12, steel),
        C.tube("LampArmB", C.catmull([(0, -3.8, 1.2), (0, -5.0, 0.4), (0, -5.6, -0.6)], 8), 0.1, steel)]
head = C.lathe("ExamLampHead", [(0.0, 0.5), (0.4, 0.5), (1.2, 0.0), (1.25, -0.15), (0.0, -0.1)], white, segs=48)
head.location = (0, -5.8, -0.9)
lamp += [head, C.cylinder("ExamLampGlow", (0, -5.8, -1.05), 1.0, 0.05, C.emissive("lamp_glow", "#FFF7E6", 2.5))]
group("ExamLamp", lamp, (17.4, 12.8, 9.0))
objs.append(C.rbox("CurtainTrack", (16.3, 1.6, CEIL - 0.25), (0.18, 20.5, 0.12), metal, 0.04))
objs.append(C.rbox("CurtainTrackEnd", (20.5, -8.7, CEIL - 0.25), (8.4, 0.18, 0.12), metal, 0.04))
curtain_m = C.material("curtain", "#BFE3DA", rough=0.85, coat=0.0, sheen=0.8)
y0, y1, nx = 8.0, 12.3, 48
verts, faces = [], []
for z in (CEIL - 0.6, FLOOR + 1.6):
    for i in range(nx + 1):
        t = i / nx
        verts.append((16.3 + 0.3 * math.sin(t * PI * 11), y0 + (y1 - y0) * t, z))
for i in range(nx):
    faces.append((i, i + 1, nx + 2 + i, nx + 1 + i))
cur = C.mesh_obj("Curtain", verts, faces, curtain_m)
C.solidify(cur, 0.04)
objs.append(cur)
objs.append(C.join([C.torus(f"Hook{i}", (16.3, y0 + i * 0.45, CEIL - 0.45), 0.08, 0.02, metal, rot=(PI / 2, 0, PI / 2)) for i in range(10)], "CurtainHooks"))
stool = [C.cylinder("StoolSeat", (0, 0, 5.0), 1.7, 0.7, vinyl, bevel=0.3), C.cylinder("StoolPost", (0, 0, 2.6), 0.18, 4.4, steel)]
for k in range(5):
    a = k * 2 * PI / 5
    stool.append(C.rbox(f"StoolLeg{k}", (0.9 * math.cos(a), 0.9 * math.sin(a), 0.5), (1.9, 0.3, 0.2), ink, 0.08, rot=(0, 0, a)))
    stool.append(C.sphere(f"StoolCaster{k}", (1.8 * math.cos(a), 1.8 * math.sin(a), 0.22), (0.22, 0.22, 0.22), ink, segs=16, rings=8))
group("Stool", stool, (14.2, -8.6, FLOOR))  # 휴지통(11.6,-3.4)과 안 겹치게

# ── 벽걸이 혈압계 (침대 머리 위) ────────────────────────
bp = [C.rbox("BPMount", (0, 0.05, -1.0), (2.2, 0.18, 4.0), white, 0.12),
      C.cylinder("BPDial", (0, -0.15, 0), 1.0, 0.34, teal, rot=FRONT, bevel=0.08),
      C.cylinder("BPFace", (0, -0.34, 0), 0.84, 0.05, C.material("bpface", "#FFFFFF", rough=0.5, coat=0.4), rot=FRONT)]
bp.append(C.join([C.rbox(f"BT{i}", (0.7 * math.sin(-2.4 + i * 0.48), -0.38, 0.7 * math.cos(-2.4 + i * 0.48)), (0.04, 0.02, 0.13), ink, 0.008, rot=(0, -2.4 + i * 0.48, 0)) for i in range(11)], "BPTicks"))
bp += [C.rbox("BPNeedle", (0.24, -0.4, 0.2), (0.05, 0.02, 0.68), coral, 0.015, rot=(0, 0.9, 0)),
       C.rbox("BPBasket", (0, -0.35, -2.4), (2.0, 0.8, 1.0), deep, 0.1),
       C.rbox("BPCuff", (0, -0.55, -2.05), (1.7, 0.55, 0.75), C.material("cuff", "#2F5E8E", rough=0.8, coat=0.0, sheen=0.4), 0.2),
       C.tube("BPHose", C.catmull([(0, -0.3, -0.9), (-0.8, -0.45, -1.5), (-1.0, -0.6, -2.7), (-0.5, -0.65, -3.6), (0.5, -0.6, -3.3), (0.5, -0.5, -2.2)], 8), 0.06, ink),
       C.sphere("BPBulb", (1.0, -0.6, -3.1), (0.26, 0.26, 0.38), ink, segs=20, rings=10)]
group("BPMonitor", bp, (23.8, 12.85, 5.6))

# ── 대기 번호 모니터 (오른쪽 벽) ────────────────────────
tv = [C.rbox("TVBody", (0, 0, 0), (0.45, 9.0, 5.2), ink, 0.15), C.rbox("TVMount", (0.4, 0, 0), (0.5, 2.0, 1.6), steel, 0.08)]
C.bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.24, 0, 0), rotation=(PI / 2, 0, -PI / 2))
face = C.bpy.context.active_object
face.name = "TVFace"
face.scale = (8.5, 4.7, 1)
face.data.materials.append(C.emissive("tv_face", "#0F3A3A", 0.8))
tv.append(face)
group("WaitingTV", tv, (24.5, -6.0, 6.8))

# ── 휠체어 (오른쪽 앞 바닥, 실제 크기: 바퀴 지름 60cm) ─────────────────
wc = []
R = 1.45
for s in (-1, 1):
    wc += [C.torus(f"WheelTire{s}", (0, s * 1.15, R), R, 0.1, ink, rot=FRONT),
           C.torus(f"WheelRim{s}", (0, s * 1.22, R), R - 0.18, 0.035, metal, rot=FRONT),
           C.cylinder(f"Hub{s}", (0, s * 1.12, R), 0.15, 0.12, metal, rot=FRONT),
           C.join([C.rbox(f"Spoke{s}{k}", (0, s * 1.13, R), (0.03, 0.02, 2 * R - 0.25), metal, 0.008, rot=(0, k * PI / 6, 0)) for k in range(6)], f"Spokes{s}"),
           C.sphere(f"Caster{s}", (-1.9, s * 0.95, 0.32), (0.32, 0.12, 0.32), ink, segs=20, rings=10),
           C.tube(f"Frame{s}", C.catmull([(-1.9, s * 0.95, 0.65), (-1.6, s * 1.0, 1.7), (0.0, s * 1.0, 1.75), (0.35, s * 1.0, 3.6), (0.75, s * 1.0, 4.0)], 8), 0.05, metal),
           C.cylinder(f"Grip{s}", (0.95, s * 1.0, 4.0), 0.08, 0.5, ink, rot=(0, PI / 2, 0)),
           C.rbox(f"Footrest{s}", (-2.2, s * 0.45, 0.7), (0.6, 0.7, 0.08), ink, 0.03),
           C.rbox(f"Armrest{s}", (-0.3, s * 1.0, 2.9), (1.6, 0.18, 0.14), ink, 0.06)]
wc += [C.rbox("WcSeat", (-0.4, 0, 1.85), (1.9, 2.0, 0.22), vinyl, 0.08), C.rbox("WcBack", (0.45, 0, 2.9), (0.16, 2.0, 1.9), vinyl, 0.06, rot=(0, -0.18, 0))]
group("Wheelchair", wc, (13.0, -15.0, FLOOR), rot_z=2.3, scale=2.1)

# ── 왼쪽 벽: 세면대 세트 (세면대 높이 ≈85cm) ──────────────────────
sk = []
basin = C.lathe("Basin", [(0.0, -0.6), (0.9, -0.55), (1.25, 0.0), (1.3, 0.12), (1.22, 0.14), (0.85, -0.42), (0.0, -0.46)], white, segs=48)
basin.location = (1.35, 0, 6.65)
basin.scale = (0.9, 1.3, 1.0)
sk += [basin, C.rbox("BasinBracket", (0.25, 0, 6.05), (0.5, 1.6, 1.0), white, 0.06),
       C.tube("Faucet", C.catmull([(0.35, 0, 6.95), (0.4, 0, 7.75), (0.9, 0, 7.95), (1.25, 0, 7.6)], 8), 0.07, metal),
       C.rbox("FaucetLever", (0.45, 0, 7.9), (0.12, 0.7, 0.08), metal, 0.03),
       C.tube("SinkPipe", C.catmull([(1.3, 0, 6.1), (1.3, 0, 5.2), (0.8, 0, 4.7), (0.05, 0, 4.7)], 8), 0.09, metal),
       C.rbox("MirrorFrame", (0.08, 0, 10.65), (0.12, 2.6, 3.2), teal, 0.08)]
C.bpy.ops.mesh.primitive_plane_add(size=1, location=(0.16, 0, 10.65), rotation=(PI / 2, 0, PI / 2))
mirror = C.bpy.context.active_object
mirror.name = "Mirror"
mirror.scale = (2.3, 2.9, 1)
mirror.data.materials.append(C.material("mirror", "#E6F4F4", rough=0.18, metal=0.35, coat=1.0, coat_rough=0.02))  # 완전 금속이면 반사할 빛이 없어 까맣게 보임
sk += [mirror,
       C.rbox("SoapBox", (0.25, -1.9, 8.45), (0.4, 0.7, 1.1), white, 0.06),
       C.rbox("SoapWindow", (0.46, -1.9, 8.55), (0.02, 0.4, 0.4), C.material("soap_window", "#F6A8A0", rough=0.2, coat=0.8), 0.02),
       C.rbox("SoapPush", (0.48, -1.9, 8.0), (0.12, 0.45, 0.15), teal, 0.04),
       C.rbox("TowelBox", (0.35, 2.3, 8.25), (0.7, 1.6, 1.8), white, 0.08),
       C.rbox("TowelSlot", (0.71, 2.3, 7.4), (0.02, 1.2, 0.08), ink, 0.01),
       C.rbox("Towel", (0.74, 2.3, 7.2), (0.02, 0.9, 0.4), paper, 0.01)]
sani = C.lathe("Sanitizer", [(0, 0), (0.22, 0), (0.22, 0.6), (0.1, 0.7), (0.1, 0.8), (0, 0.8)], C.material("sanitizer", "#CFEFE6", rough=0.15, coat=1.0, transmission=0.6), segs=24)
sani.location = (1.0, -0.75, 6.79)
sk += [sani, C.cylinder("SaniPump", (1.0, -0.75, 7.67), 0.06, 0.22, white), C.rbox("SaniNozzle", (1.12, -0.75, 7.77), (0.24, 0.06, 0.05), white, 0.02),
       C.rbox("GloveRack", (0.08, -4.2, 9.25), (0.12, 2.6, 3.2), metal, 0.04)]
for i, (col, z) in enumerate((("#7FC8E8", 10.35), ("#B9E2D9", 9.25), ("#C7B9EC", 8.15))):
    sk += [C.rbox(f"GloveBox{i}", (0.45, -4.2, z), (0.6, 2.2, 0.9), white, 0.05),
           C.rbox(f"GloveLabel{i}", (0.76, -4.2, z), (0.02, 2.2, 0.25), C.material(f"glove_lab{i}", col, rough=0.6, coat=0.0), 0.01),
           C.sphere(f"Glove{i}", (0.8, -4.2, z + 0.35), (0.12, 0.35, 0.22), C.material(f"glove{i}", col, rough=0.5, coat=0.2, sheen=0.5), segs=20, rings=10)]
group("SinkSet", sk, (-24.75, 6.2, FLOOR), scale=1.3)

# ── 키 체중계: 왼쪽 뒤 구석, 기둥은 뒷벽에 붙고 저울대가 방 쪽(앞)으로 ─────────
sc = [C.rbox("ScalePlate", (0, 0, 0.55), (4.2, 4.2, 1.1), white, 0.2),
      C.rbox("ScaleMat", (0, 0, 1.12), (3.6, 3.6, 0.05), C.material("scale_mat", "#2E7A75", rough=0.85, coat=0.0), 0.03),
      C.rbox("ScaleColumn", (0, 2.0, 7.0), (0.6, 0.6, 13.0), white, 0.12),
      C.rbox("ScaleBeamBox", (0, 1.4, 11.2), (1.0, 1.4, 1.0), white, 0.12),
      C.rbox("ScaleBeam", (0, -0.2, 11.2), (0.3, 3.4, 0.55), steel, 0.06),
      C.rbox("ScalePoise", (0, -1.0, 11.2), (0.42, 0.34, 0.75), ink, 0.05),
      C.rbox("ScaleBeamTip", (0, -1.95, 11.2), (0.36, 0.2, 0.36), coral, 0.05),
      C.cylinder("HeightRod", (0, 2.0, 16.2), 0.1, 6.0, steel),
      C.rbox("HeightHead", (0, 0.9, 18.9), (0.18, 2.2, 0.12), steel, 0.04)]
group("HeightScale", sc, (-22.0, 10.0, FLOOR))

# ── 처치 카트 (책상 왼쪽, 바퀴 달린 2단 스테인리스) ────────────────────
ct = [C.rbox("CartTop", (0, 0, 8.2), (5.2, 3.4, 0.25), steel, 0.08), C.rbox("CartRail", (0, 0, 8.45), (5.3, 3.5, 0.3), steel, 0.12),
      C.rbox("CartTopIn", (0, 0, 8.47), (5.0, 3.2, 0.32), C.material("cart_in", "#E9EEEE", rough=0.3, metal=0.6), 0.08),
      C.rbox("CartMid", (0, 0, 4.4), (5.2, 3.4, 0.2), steel, 0.06), C.rbox("CartDrawer", (0, -1.71, 6.6), (4.8, 0.06, 1.6), white, 0.08),
      C.rbox("CartDrawerHandle", (0, -1.8, 6.9), (1.8, 0.12, 0.18), deep, 0.05)]
for sx in (-1, 1):
    for sy in (-1, 1):
        ct += [C.cylinder(f"CartLeg{sx}{sy}", (sx * 2.45, sy * 1.55, 4.3), 0.1, 7.8, steel),
               C.sphere(f"CartWheel{sx}{sy}", (sx * 2.45, sy * 1.55, 0.3), (0.3, 0.3, 0.3), ink, segs=16, rings=8)]
alc = C.lathe("Alcohol", [(0, 0), (0.42, 0), (0.42, 1.4), (0.22, 1.6), (0.22, 1.85), (0, 1.85)], C.material("alcohol", "#E3F3EE", rough=0.15, coat=1.0, transmission=0.6), segs=24)
alc.location = (-1.6, 0.6, 8.65)
cotton = C.lathe("CottonJar", [(0, 0), (0.6, 0), (0.6, 1.1), (0, 1.1)], C.glass_mat("#F4FBF9", "jar_glass2"), segs=32)
cotton.location = (-0.2, 0.7, 8.65)
ct += [alc, C.cylinder("AlcCap", (-1.6, 0.6, 10.6), 0.24, 0.2, teal), cotton, C.cylinder("CottonLid", (-0.2, 0.7, 9.8), 0.64, 0.12, steel)]
ct += [C.sphere(f"Cotton{i}", (-0.2 + 0.25 * math.cos(i * 2.1), 0.7 + 0.25 * math.sin(i * 2.1), 9.0 + (i % 3) * 0.22), (0.24, 0.24, 0.2), paper, segs=12, rings=6) for i in range(7)]
ct += [C.rbox("GauzeBox", (1.3, 0.6, 9.25), (1.6, 1.2, 1.2), white, 0.06), C.rbox("GauzeStripe", (1.3, -0.015, 9.45), (1.6, 0.02, 0.2), teal, 0.01),
       C.rbox("KidneyTray", (0.4, -0.9, 8.72), (2.4, 1.0, 0.12), steel, 0.3)]
syr = [C.lathe("SyringeBody", [(0, 0), (0.08, 0), (0.08, 0.9), (0, 0.9)], C.material("syringe", "#F4FBF9", rough=0.1, coat=1.0, transmission=0.5), segs=16),
       C.cylinder("Plunger", (0, 0, 1.05), 0.04, 0.5, white), C.cylinder("NeedleCap", (0, 0, -0.2), 0.04, 0.4, teal)]
C.select_only(syr)
C.bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
C.apply_rot(syr, (0, PI / 2, 0.2))
for o in syr:
    o.location = (0.2, -0.9, 8.86)
ct += syr
ct += [C.rbox("SharpsBin", (1.4, 0.4, 5.5), (1.6, 1.4, 2.0), C.material("sharps", "#F2734A", rough=0.5, coat=0.3), 0.1),
       C.rbox("SharpsLid", (1.4, 0.4, 6.6), (1.7, 1.5, 0.25), white, 0.06),
       C.rbox("BoxA", (-1.2, 0.3, 5.0), (2.0, 2.2, 1.0), C.material("box_mint", "#B9E2D9", rough=0.7, coat=0.0), 0.04),
       C.rbox("BoxB", (-1.2, 0.3, 5.9), (1.6, 1.8, 0.8), white, 0.04)]
group("Cart", ct, (-13.6, 1.0, FLOOR))

# ── 왼쪽 벽 앞쪽: 진료실 문 + 비상구 표시 + 소화기 + 대기 의자 ───────────────
dr = [C.rbox("DoorFrame", (0, 0, 10.6), (0.5, 10.4, 21.2), white, 0.12),
      C.rbox("DoorPanel", (0.2, 0, 10.4), (0.25, 9.2, 20.6), C.material("door_teal", "#2F8A84", rough=0.5, coat=0.4), 0.1),
      C.rbox("DoorWindowFrame", (0.34, 1.6, 15.4), (0.06, 2.6, 4.2), white, 0.06)]
C.bpy.ops.mesh.primitive_plane_add(size=1, location=(0.38, 1.6, 15.4), rotation=(PI / 2, 0, PI / 2))
dwin = C.bpy.context.active_object
dwin.name = "DoorWindow"
dwin.scale = (2.2, 3.8, 1)
dwin.data.materials.append(C.emissive("door_glass", "#DDF1F6", 0.8))
dr += [dwin, C.rbox("DoorKick", (0.34, 0, 1.0), (0.04, 9.0, 1.8), steel, 0.04),
       C.rbox("DoorHandleBase", (0.36, -3.6, 9.4), (0.1, 0.5, 1.6), steel, 0.05),
       C.rbox("DoorHandle", (0.65, -3.3, 9.4), (0.3, 1.4, 0.24), steel, 0.08),
       C.rbox("ExitSign", (0.4, 0, 22.6), (0.3, 3.4, 1.2), C.emissive("exit_green", "#2BB673", 1.2), 0.08),
       C.text("ExitText", "EXIT", (0.57, 0, 22.6), 0.7, C.plastic("paper"), rot=(PI / 2, 0, PI / 2), extrude=0.01)]
group("Door", dr, (-24.75, -8.6, FLOOR))
ext = [C.lathe("Extinguisher", [(0, 0), (0.6, 0), (0.62, 3.6), (0.4, 4.1), (0.2, 4.3), (0, 4.3)], C.material("ext_red", "#D9443F", rough=0.35, coat=0.8), segs=32),
       C.rbox("ExtHandle", (0, 0, 4.6), (1.0, 0.25, 0.25), ink, 0.06), C.tube("ExtHose", C.catmull([(0.2, 0, 4.4), (0.8, 0, 4.0), (0.75, 0, 2.6)], 6), 0.08, ink),
       C.rbox("ExtLabel", (0, -0.6, 2.2), (0.8, 0.04, 1.2), paper, 0.04)]
group("Extinguisher", ext, (-23.4, -1.6, FLOOR + 1.0))
objs.append(C.rbox("ExtBracket", (-24.6, -1.6, FLOOR + 4.0), (0.3, 1.0, 0.4), steel, 0.05))
chairs = [C.rbox("BenchBeam", (0, 0, 3.6), (1.0, 15.0, 0.4), steel, 0.1)]
for i in range(3):
    yy = -5.0 + i * 5.0
    chairs += [C.rbox(f"ChairSeat{i}", (0, yy, 4.3), (4.2, 4.2, 0.5), seat_coral, 0.25),
               C.rbox(f"ChairBack{i}", (-1.9, yy, 7.0), (0.45, 4.2, 4.4), seat_coral, 0.22, rot=(0, -0.12, 0))]
for yy in (-7.0, 7.0):
    chairs += [C.rbox(f"BenchLeg{yy}", (0, yy, 1.8), (2.8, 0.4, 3.6), steel, 0.12), C.rbox(f"BenchFoot{yy}", (0, yy, 0.1), (3.6, 0.6, 0.2), ink, 0.06)]
group("WaitingChairs", chairs, (-22.2, -24.0, FLOOR))

root = C.empty("Ward")
C.parent([o for o in objs if o.parent is None], root)
C.export_glb("ward.glb")
