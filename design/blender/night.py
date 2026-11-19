"""야간 당직 진료실(숨은 것 16/16)에서만 보이는 소품 → models/night.glb

  NightCap  : 박사님 수면 모자. 원점 = 모자 밑동 가운데(머리 꼭대기에 얹는 점). 코드가 박사님 몸(Body)에 붙인다.
  Roster    : 뒷벽 야간 근무표 (창문 오른쪽, 진료등 왼쪽 빈 벽). 진료실 좌표에 바로 놓는다.
    RosterPaper : 글자를 코드가 그리는 빈 종이 면 (회차 라벨·진료 기록과 같은 방식)

달은 따로 만들지 않고 창문 밤하늘 그림(코드)에 그린다 — 창은 평평한 판이라 같은 모습이고 겹침 깜빡임이 없다.
실제 로고 없음. 팔레트는 common.py 그대로 + 밤 남색 하나.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

PI = math.pi
C.reset()

navy = C.material("night_navy", "#24406B", rough=0.75, coat=0.0, sheen=0.6)
cream = C.material("night_cream", "#F4EFE2", rough=0.8, coat=0.0, sheen=0.7)
white = C.plastic("white")
teal = C.plastic("teal")
deep = C.plastic("deep", rough=0.45)
paper = C.material("roster_paper", C.PALETTE["paper"], rough=0.9, coat=0.0)
pin = C.plastic("coral")

# ── 수면 모자 ─────────────────────────────────────────
# 밑동 반지름은 박사님 머리(캡슐 반지름 0.72)보다 조금 작게 얹고, 끝은 옆으로 처지게 휜다.
cap_parts = []
band = C.torus("CapBand", (0, 0, 0.04), 0.5, 0.075, cream, segs=(48, 10))
cap_parts.append(band)

# 휘어진 원뿔: 위로 갈수록 가늘어지며 +X 쪽으로 처진다 (고리를 겹쳐 쌓아 만든 몸통)
ring_pts = []
N = 14
for i in range(N + 1):
    t = i / N
    r = 0.5 * (1 - t) ** 0.85 + 0.03
    x = 0.85 * t ** 2.0
    z = 0.06 + 1.35 * t - 0.55 * t ** 3
    ring_pts.append((x, z, r))

import bmesh  # noqa: E402

me = C.bpy.data.meshes.new("CapBodyMesh")
bm = bmesh.new()
SEG = 28
rings = []
for x, z, r in ring_pts:
    ring = []
    for k in range(SEG):
        a = 2 * PI * k / SEG
        ring.append(bm.verts.new((x + r * math.cos(a), r * math.sin(a), z)))
    rings.append(ring)
for i in range(len(rings) - 1):
    for k in range(SEG):
        k2 = (k + 1) % SEG
        bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
bm.faces.new(list(reversed(rings[0])))
bm.faces.new(rings[-1])
bm.normal_update()
bm.to_mesh(me)
bm.free()
cap_body = C.bpy.data.objects.new("CapBody", me)
C.bpy.context.collection.objects.link(cap_body)
me.materials.append(navy)
for p in me.polygons:
    p.use_smooth = True
cap_parts.append(cap_body)

# 별 무늬 대신 크림색 줄무늬 두 줄 (모자 몸통을 따라)
for j, t in enumerate((0.32, 0.6)):
    i = int(t * N)
    x, z, r = ring_pts[i]
    cap_parts.append(C.torus(f"CapStripe{j}", (x, 0, z), r + 0.012, 0.022, cream, segs=(36, 6)))

tip_x, tip_z, _ = ring_pts[-1]
cap_parts.append(C.sphere("CapPom", (tip_x + 0.04, 0, tip_z - 0.04), (0.13, 0.13, 0.13), cream, segs=20, rings=10))

cap = C.empty("NightCap")
C.parent(cap_parts, cap)

# ── 야간 근무표 (뒷벽) ──────────────────────────────────
RX, RY, RZ = 18.6, 12.86, 5.7   # 창문(오른쪽 끝 x≈16.3)과 진료등(x≈20.9) 사이 빈 벽, 벽면 y≈12.9
board = C.rbox("RosterBoard", (RX, RY, RZ), (2.2, 0.08, 2.9), deep, 0.06)
paper_plane = C.rbox("RosterPaper", (RX, RY - 0.05, RZ - 0.12), (1.9, 0.01, 2.45), paper, 0.0)
clip = C.rbox("RosterClip", (RX, RY - 0.08, RZ + 1.28), (0.8, 0.06, 0.26), C.material("roster_clip", C.PALETTE["metal"], rough=0.3, metal=0.8), 0.04)
pin_l = C.sphere("RosterPin", (RX, RY - 0.12, RZ + 1.5), (0.08, 0.08, 0.08), pin, segs=16, rings=8)
roster = C.empty("Roster")
C.parent([board, paper_plane, clip, pin_l], roster)

C.export_glb("night.glb")
C.render_preview("night.png", cam_loc=(3.0, -6.0, 3.0), target=(0.2, 0, 0.6), lens=50, size=(900, 700), floor_z=0.0)
