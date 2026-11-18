"""닥터 패치: 흰색·청록 캡슐 몸 + 짧은 흰 가운 + 청진기 + 반사경 + 동그란 안경.

움직일 부분은 따로 이름을 붙인다 (Three.js에서 찾아 쓴다):
  DrPatch(바닥 기준) > Body(몸 전체, 숨쉬기·끄덕임) > EyeL, EyeR(깜빡임), ArmL, ArmR(어깨 기준 회전)
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

C.reset()

R, L = 0.72, 0.42          # 캡슐 반지름, 원통 절반 길이
R2 = R + 0.016             # 위쪽 반쪽은 살짝 커서 아래쪽을 덮는다 (진짜 캡슐처럼)
BOTTOM = -L - R            # 몸 맨 아래

white, teal, deep = C.plastic("white"), C.plastic("teal"), C.plastic("deep", rough=0.45)
ink = C.material("ink", C.PALETTE["ink"], rough=0.25, coat=0.8)
coat_m = C.material("coat", "#FFFFFF", rough=0.6, coat=0.1, sheen=0.5)
mint, coral, blush = C.plastic("mint"), C.plastic("coral"), C.material("blush", C.PALETTE["blush"], rough=0.6, coat=0.0)
metal = C.metal_mat()

parts = []

# ── 캡슐 몸 ─────────────────────────────────────────────
bottom = C.lathe("BodyBottom", C.hemi(R, -L, up=False) + [(R, 0.02)] + [(0.0, 0.02)], teal)
top = C.lathe("BodyTop", [(0.0, -0.08), (R2, -0.08)] + [(R2, L)] + C.hemi(R2, L, up=True)[1:], white)
lip = C.torus("BodyLip", (0, 0, -0.08), R2, 0.018, white)
parts += [bottom, top, lip]

# ── 얼굴 (정면 = -Y) ────────────────────────────────────
def on_surface(x, z, out=0.0, r=R2):
    return (x, -math.sqrt(max(r * r - x * x, 0)) - out, z)

eye_z = 0.26
eyes = []
for side, x in (("L", -0.23), ("R", 0.23)):
    e = C.sphere(f"Eye{side}", on_surface(x, eye_z, -0.01), (0.075, 0.04, 0.1), ink, segs=32, rings=16)
    hl = C.sphere(f"EyeShine{side}", (x + 0.025, on_surface(x, eye_z)[1] - 0.035, eye_z + 0.04), (0.022, 0.012, 0.022), C.plastic("paper"), segs=16, rings=8)
    C.parent([hl], e)
    eyes.append(e)
    parts.append(e)
    # 동그란 안경
    ring = C.torus(f"Lens{side}", on_surface(x, eye_z, 0.05), 0.15, 0.017, ink, rot=(math.pi / 2, 0, 0))
    parts.append(ring)
bridge = C.tube("Bridge", C.catmull([on_surface(-0.08, eye_z + 0.02, 0.06), on_surface(0, eye_z + 0.05, 0.07), on_surface(0.08, eye_z + 0.02, 0.06)], 6), 0.014, ink)
parts.append(bridge)
for x in (-0.38, 0.38):  # 안경다리: 머리 옆을 따라 뒤로
    s = 1 if x > 0 else -1
    pts = [on_surface(x, eye_z, 0.04)]
    for a in (35, 60, 85):
        ang = math.radians(a)
        pts.append((s * (R2 + 0.02) * math.sin(math.radians(30) + ang * 0.7), -(R2 + 0.02) * math.cos(math.radians(30) + ang * 0.7), eye_z))
    parts.append(C.tube(f"Temple{'R' if s > 0 else 'L'}", C.catmull(pts, 6), 0.013, ink))

for x in (-0.43, 0.43):  # 볼
    parts.append(C.sphere(f"Cheek{x:+.0f}", on_surface(x, 0.08, -0.02), (0.1, 0.03, 0.065), blush, segs=24, rings=12))

smile = [on_surface(x, 0.09 + 3.2 * x * x, 0.004) for x in (-0.085, -0.045, 0, 0.045, 0.085)]
parts.append(C.tube("Mouth", C.catmull(smile, 6), 0.017, ink))

# ── 반사경 머리띠 ───────────────────────────────────────
band_z = L + 0.2
band_r = math.sqrt(R2 ** 2 - 0.2 ** 2) + 0.02
parts.append(C.torus("HeadBand", (0, 0, band_z), band_r, 0.045, deep))
ang = math.radians(-60)
mpos = ((band_r + 0.06) * math.cos(ang), (band_r + 0.06) * math.sin(ang), band_z + 0.1)
mirror = C.cylinder("Mirror", mpos, 0.2, 0.035, metal, rot=(math.radians(70), 0, math.radians(30)), bevel=0.01)
mrim = C.torus("MirrorRim", mpos, 0.2, 0.025, deep, rot=(math.radians(70), 0, math.radians(30)))
mhole = C.cylinder("MirrorHole", mpos, 0.045, 0.045, ink, rot=(math.radians(70), 0, math.radians(30)))
parts += [mirror, mrim, mhole]

# ── 짧은 흰 가운 (앞이 열려 청록 몸이 보임) ────────────────
gap = math.radians(22)
front = -math.pi / 2
coat = C.lathe("Coat", [(R + 0.075, -0.86), (R + 0.06, -0.5), (R + 0.04, -0.1), (R + 0.035, 0.04)], coat_m,
               segs=72, a0=front + gap, a1=front - gap + 2 * math.pi)
C.solidify(coat, 0.03)
C.add_bevel(coat, 0.012, 3)
parts.append(coat)
for s in (-1, 1):  # 옷깃: 가운 앞섶에서 바깥으로 접힌 삼각형
    a_edge = front + s * gap
    a_tip = front + s * (gap + math.radians(22))
    def P(a, r, z):
        return (r * math.cos(a), r * math.sin(a), z)
    v = [P(a_edge, R + 0.07, 0.05), P(a_edge, R + 0.065, -0.3), P(a_tip, R + 0.085, -0.02)]
    lapel = C.mesh_obj(f"Lapel{'R' if s > 0 else 'L'}", v, [(0, 1, 2) if s > 0 else (0, 2, 1)], coat_m)
    C.solidify(lapel, 0.025)
    C.add_bevel(lapel, 0.008, 2)
    parts.append(lapel)

# 가슴 주머니 + 펜 (보는 사람 기준 왼쪽)
pa = math.radians(-128)
pr = R + 0.11
pocket = C.rbox("Pocket", (pr * math.cos(pa), pr * math.sin(pa), -0.42), (0.27, 0.035, 0.22), coat_m, 0.015, rot=(0, 0, pa + math.pi / 2))
pen = C.cylinder("Pen", (pr * math.cos(pa) + 0.05, pr * math.sin(pa) + 0.005, -0.25), 0.026, 0.28, teal, bevel=0.008)
pen_cap = C.cylinder("PenCap", (pr * math.cos(pa) + 0.05, pr * math.sin(pa) + 0.005, -0.13), 0.03, 0.08, coral, bevel=0.01)
# 이름표 (반대쪽)
ba = math.radians(-52)
badge = C.rbox("Badge", ((pr - 0.01) * math.cos(ba), (pr - 0.01) * math.sin(ba), -0.48), (0.22, 0.03, 0.13), C.plastic("paper"), 0.012, rot=(0, 0, ba + math.pi / 2))
stripe = C.rbox("BadgeStripe", ((pr + 0.006) * math.cos(ba), (pr + 0.006) * math.sin(ba), -0.44), (0.22, 0.012, 0.035), teal, 0.005, rot=(0, 0, ba + math.pi / 2))
parts += [pocket, pen, pen_cap, badge, stripe]

# ── 청진기 (목에 걸고 앞으로 늘어뜨림) ────────────────────
SR = R + 0.13
def ring_pt(deg, z, r=SR):
    a = math.radians(deg)
    return (r * math.cos(a), r * math.sin(a), z)
steth = [(-0.05, -SR - 0.02, -0.5), (-0.2, -SR + 0.02, -0.22), ring_pt(-125, 0.02), ring_pt(-165, 0.1), ring_pt(150, 0.13),
         ring_pt(90, 0.14), ring_pt(30, 0.13), ring_pt(-15, 0.1), ring_pt(-55, 0.02), (0.2, -SR + 0.02, -0.22), (0.05, -SR - 0.02, -0.5)]
parts.append(C.tube("StethTube", C.catmull(steth, 8), 0.028, deep))
chest = C.cylinder("StethChest", (0, -SR - 0.06, -0.6), 0.12, 0.06, metal, rot=(math.pi / 2, 0, 0), bevel=0.015)
chest_rim = C.torus("StethRim", (0, -SR - 0.07, -0.6), 0.12, 0.022, teal, rot=(math.pi / 2, 0, 0))
neck = C.cylinder("StethNeck", (0, -SR - 0.04, -0.52), 0.03, 0.08, metal, bevel=0.01)
parts += [chest, chest_rim, neck]

# ── 팔 (어깨 기준) · 발 ────────────────────────────────
arms = []
for side, s in (("L", -1), ("R", 1)):
    shoulder = (s * (R + 0.02), -0.05, -0.12)
    arm = C.empty(f"Arm{side}", shoulder)
    sleeve = C.lathe(f"Sleeve{side}", C.hemi(0.14, -0.36, up=False) + [(0.14, 0.0)] + [(0.0, 0.0)], coat_m, segs=32)
    sleeve.location = shoulder
    cuff = C.torus(f"Cuff{side}", (shoulder[0], shoulder[1], shoulder[2] - 0.36), 0.135, 0.03, teal)
    hand = C.sphere(f"Hand{side}", (shoulder[0], shoulder[1], shoulder[2] - 0.47), (0.13, 0.13, 0.13), mint, segs=32, rings=16)
    C.parent([sleeve, cuff, hand], arm)
    arm.rotation_euler = (0.15, s * -0.42, 0)
    arms.append(arm)
    parts.append(arm)

feet = [C.sphere(f"Foot{s}", (s * 0.3, -0.12, BOTTOM - 0.01), (0.22, 0.3, 0.13), deep, segs=32, rings=16) for s in (-1, 1)]

# ── 계층: DrPatch(바닥) > Body > 나머지 ──────────────────
ground = BOTTOM - 0.14
root = C.empty("DrPatch", (0, 0, ground))
body = C.empty("Body", (0, 0, BOTTOM))
C.parent([p for p in parts if p.parent is None], body)
C.parent([body] + feet, root)
root.location = (0, 0, 0)

C.export_glb("doctor.glb")
C.render_preview("doctor.png", cam_loc=(1.6, -6.6, 2.6), target=(0, 0, 1.2), lens=60)
