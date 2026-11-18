"""DR.PATCH 책상 소품 → prototype/drpatch-desk/models/*.glb

좌표: Blender Z가 위, 정면(카메라 쪽)이 -Y. glTF로 나가면 Three.js에서 Y가 위, 정면이 +Z.
코드가 찾아 쓰는 이름 (바꾸면 index.html도 같이 고칠 것):
  capsule  : CapCur(현재 버전 반쪽, 재질 cap_cur), CapTgt(목표 버전 반쪽, 재질 cap_tgt)
  blister_cell : Well(알약 홈, 재질 foil_well — 코드가 위험도 색으로 칠함), Dome(투명 덮개)
  blister_end  : Label(회차 라벨 자리, 글자는 코드가 그림)
  tray     : 곡반 (안전한 패키지)
  iv       : Liquid(바닥 기준 원점, 높이 비율로 줄임), Drop(떨어지는 방울)
  bottle   : Lid(뚜껑, 바닥 가운데 원점)
  chart    : Paper(기록 글자는 코드가 그림)
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from mathutils import Matrix  # noqa: E402

P = C.PALETTE
PI = math.pi


def mats():
    return {
        "white": C.plastic("white"), "teal": C.plastic("teal"), "deep": C.plastic("deep", rough=0.45),
        "mint": C.plastic("mint"), "coral": C.plastic("coral"), "ink": C.material("ink", P["ink"], rough=0.3, coat=0.6),
        "paper": C.material("paper", "#FFFFFF", rough=0.75, coat=0.0, sheen=0.2), "metal": C.metal_mat(),
        "glass": C.glass_mat("#F4FBF9"), "faint": C.material("faint", "#8DB5AF", rough=0.5, coat=0.0),
    }


def finish(name, objs):
    root = C.empty(name)
    C.parent([o for o in objs if o.parent is None and o is not root], root)
    return root


# ── 캡슐 (패키지 하나) ──────────────────────────────────
def capsule():
    m = mats()
    r, half = 0.26, 0.23
    cur = C.lathe("CapCur", C.hemi(r, -half, up=False) + [(r, 0.0), (0.0, 0.0)], C.material("cap_cur", P["teal"]), segs=48)
    tgt_m = C.material("cap_tgt", P["white"])
    r2 = r + 0.012
    tgt = C.lathe("CapTgt", [(0.0, -0.05), (r2, -0.05), (r2, half)] + C.hemi(r2, half, up=True)[1:], tgt_m, segs=48)
    lip = C.torus("CapLip", (0, 0, -0.05), r2, 0.01, tgt_m)
    shine = C.sphere("CapShine", (0.0, -0.14, half + 0.1), (0.05, 0.02, 0.16), m["paper"], segs=16, rings=8)
    objs = [cur, tgt, lip, shine]
    C.apply_rot(objs, (0, PI / 2, 0))  # 눕힌다: CapCur 왼쪽(-X), CapTgt 오른쪽(+X)
    for o in objs:
        o.location = (0, 0, 0)
    C.select_only(objs)
    bpy_ops = C.bpy.ops.object
    bpy_ops.transform_apply(location=True, rotation=True, scale=True)
    return finish("Capsule", objs)


# ── 블리스터 부품 (코드가 회차의 칸 수 N에 맞춰 이어 붙인다) ──────────
CELL_W, CELL_D, END_W = 1.4, 1.24, 1.2


def blister_cell():
    """칸 하나: 은박 타일 + 알약 홈(Well, 위험도 색은 코드가 칠함) + 투명 덮개(Dome)."""
    m = mats()
    foil = C.material("foil", "#E9EEEE", rough=0.24, metal=0.8, coat=0.6)
    objs = [C.rbox("CellFoil", (0, 0, 0.07), (CELL_W, CELL_D, 0.14), foil, 0.035)]
    # 홈은 은박 위로 1mm 띄운다 (맞닿는 면이 서로 깜빡이지 않게). 투명 덮개는 따로 놀아서 뺐다.
    objs.append(C.sphere("Well", (0, 0, 0.148), (0.62, 0.4, 0.006), C.material("foil_well", "#C9D3D4", rough=0.3, metal=0.6, coat=0.3), segs=48, rings=12))
    return finish("Cell", objs)


def blister_end():
    """판 왼쪽 끝: 회차 라벨(Label, 글자는 코드가 그림) + 절취선."""
    m = mats()
    foil = C.material("foil", "#E9EEEE", rough=0.24, metal=0.8, coat=0.6)
    objs = [C.rbox("EndFoil", (0, 0, 0.07), (END_W, 2 * CELL_D, 0.14), foil, 0.035)]
    C.bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.04, 0, 0.146))
    label = C.bpy.context.active_object
    label.name = "Label"
    label.scale = (1.0, 2.3, 1)
    C.select_only([label])
    C.bpy.ops.object.transform_apply(scale=True)
    label.data.materials.append(C.material("label", P["ink"], rough=0.6, coat=0.2))
    objs.append(label)
    dots = [C.sphere(f"Perf{i}", (END_W / 2 - 0.05, -1.15 + i * 0.115, 0.148), (0.018, 0.018, 0.005), m["faint"], segs=8, rings=4) for i in range(21)]
    objs.append(C.join(dots, "Perforation"))
    return finish("BlisterEnd", objs)


# ── 수액 거치대 + 수액 팩 ───────────────────────────────
def iv():
    m = mats()
    objs = [C.cylinder("Hub", (0, 0, 0.26), 0.2, 0.2, m["deep"], bevel=0.04)]
    for k in range(5):
        a = k * 2 * PI / 5 + 0.3
        objs.append(C.rbox(f"Leg{k}", (0.52 * math.cos(a), 0.52 * math.sin(a), 0.2), (0.95, 0.14, 0.08), m["white"], 0.035, rot=(0, 0.12, a)))
        objs.append(C.sphere(f"Wheel{k}", (0.98 * math.cos(a), 0.98 * math.sin(a), 0.1), (0.1, 0.1, 0.1), m["ink"], segs=24, rings=12))
    objs.append(C.cylinder("Pole", (0, 0, 2.2), 0.055, 3.8, m["metal"]))
    objs.append(C.cylinder("PoleClamp", (0, 0, 1.6), 0.1, 0.16, m["teal"], bevel=0.03))
    objs.append(C.sphere("PoleKnob", (0.14, 0, 1.6), (0.06, 0.06, 0.06), m["teal"], segs=16, rings=8))
    objs.append(C.cylinder("PoleCap", (0, 0, 4.12), 0.08, 0.06, m["teal"], bevel=0.02))
    objs.append(C.tube("Arm", C.catmull([(0, 0, 4.1), (0.5, 0, 4.12), (1.05, 0, 4.1)], 6), 0.04, m["metal"]))
    objs.append(C.tube("Hook", C.catmull([(1.05, 0, 4.1), (1.05, 0, 3.98), (1.0, 0, 3.92), (0.96, 0, 3.98)], 6), 0.022, m["metal"]))
    bag_from = len(objs)  # 여기부터 수액 팩 부품 → 걸이 기준으로 줄인다
    objs.append(C.rbox("Hanger", (1.05, 0, 3.86), (0.5, 0.06, 0.18), m["white"], 0.03))
    objs.append(C.rbox("Bag", (1.05, 0, 2.9), (1.3, 0.42, 1.9), C.glass_mat("#F2FBF8", "bag"), 0.2))
    liquid = C.rbox("Liquid", (1.05, 0, 2.87), (1.1, 0.28, 1.6), C.material("liquid", "#6CC6B4", rough=0.12, transmission=0.55, coat=1.0), 0.12)
    liquid.data.transform(Matrix.Translation((0, 0, 0.8)))  # 원점을 바닥으로 → 코드가 높이 비율만 바꾼다
    liquid.location.z -= 0.8
    objs.append(liquid)
    ticks = []
    for i in range(7):
        w = 0.22 if i % 2 == 0 else 0.13
        ticks.append(C.rbox(f"Tick{i}", (0.55 + w / 2, -0.215, 2.25 + i * 0.2), (w, 0.01, 0.025), m["deep"], 0.005))
    objs.append(C.join(ticks, "Ticks"))
    objs.append(C.rbox("Sticker", (1.25, -0.216, 3.2), (0.62, 0.012, 0.42), m["paper"], 0.03))
    objs.append(C.rbox("StickerStripe", (1.25, -0.224, 3.36), (0.62, 0.006, 0.07), m["teal"], 0.01))
    objs.append(C.text("StickerText", "DR.PATCH", (1.25, -0.23, 3.18), 0.13, m["ink"], rot=(PI / 2, 0, 0)))
    objs.append(C.text("StickerSub", "DRIP 500", (1.25, -0.23, 3.06), 0.07, m["deep"], rot=(PI / 2, 0, 0)))
    objs.append(C.cylinder("Port", (1.05, 0, 1.9), 0.06, 0.14, m["white"]))
    objs.append(C.cylinder("Chamber", (1.05, 0, 1.64), 0.11, 0.38, m["glass"]))
    objs.append(C.cylinder("ChamberCap", (1.05, 0, 1.43), 0.08, 0.06, m["white"]))
    objs.append(C.sphere("Drop", (1.05, 0, 1.76), (0.045, 0.045, 0.055), C.material("drop", "#6CC6B4", rough=0.1, coat=1.0), segs=16, rings=8))
    BAG_S = 0.6  # 수액 팩은 거치대보다 작게 (500ml 팩 비율)
    bag = C.empty("BagGroup", (1.05, 0, 3.86))
    C.parent(objs[bag_from:], bag)
    bag.scale = (BAG_S,) * 3
    objs = objs[:bag_from] + [bag]
    cz = 3.86 + (1.40 - 3.86) * BAG_S  # 줄어든 점적통 아래 끝
    # 관은 거치대에 감아 둔다 (장식용 — 어디에도 꽂지 않음)
    tube_pts = C.catmull([(1.05, 0, cz), (1.0, -0.05, cz - 0.55), (0.6, -0.12, cz - 0.95), (0.18, -0.12, cz - 1.05), (0.12, 0.12, cz - 1.0), (0.25, 0.2, cz - 0.9)], 8)
    objs.append(C.tube("Line", tube_pts, 0.022, C.material("line", "#E2F2EE", rough=0.2, transmission=0.4)))
    objs.append(C.rbox("RollerClamp", (0.62, -0.12, cz - 0.95), (0.24, 0.13, 0.12), m["teal"], 0.03))
    return finish("IV", objs)


# ── 약병 (접수된 패키지가 담김) ─────────────────────────
def bottle():
    m = mats()
    body = C.lathe("BottleBody", [(0.0, 0.0), (1.1, 0.0), (1.2, 0.08), (1.2, 1.9), (1.12, 2.06), (1.0, 2.16), (1.0, 2.26)],
                   C.glass_mat("#D2F0E8", "bottle_glass"))
    base = C.lathe("BottleBase", [(0.0, 0.0), (1.12, 0.0), (1.18, 0.05), (1.18, 0.1), (0.0, 0.1)], m["white"])
    lab = C.lathe("BottleLabel", [(1.212, 0.32), (1.212, 0.95)], m["paper"])
    stripe = C.lathe("BottleStripe", [(1.226, 0.86), (1.226, 0.95)], m["teal"])
    t1 = C.text("BottleText", "DR.PATCH", (0, -1.235, 0.66), 0.22, m["ink"], rot=(PI / 2, 0, 0))
    t2 = C.text("BottleSub", "Rx  requirements.txt", (0, -1.235, 0.46), 0.09, m["deep"], rot=(PI / 2, 0, 0))
    lid = C.empty("Lid", (0, 0, 2.2))
    shell = C.lathe("LidShell", [(0.0, 2.2), (1.1, 2.2), (1.13, 2.24), (1.13, 2.6), (1.07, 2.68), (0.0, 2.7)], m["teal"])
    grips = [C.rbox(f"Grip{i}", (1.14 * math.cos(i * 2 * PI / 40), 1.14 * math.sin(i * 2 * PI / 40), 2.42), (0.035, 0.07, 0.3), m["deep"], 0.012, rot=(0, 0, i * 2 * PI / 40))
             for i in range(40)]
    grip = C.join(grips, "LidGrip")
    ring = C.torus("LidRing", (0, 0, 2.69), 0.8, 0.025, m["deep"])
    C.parent([shell, grip, ring], lid)
    return finish("Bottle", [body, base, lab, stripe, t1, t2, lid])


# ── 진료 차트 (클립보드) ────────────────────────────────
def chart():
    m = mats()
    objs = [C.rbox("Board", (0, 0, 0.05), (2.6, 3.3, 0.1), m["deep"], 0.08)]
    objs.append(C.rbox("Sheets", (0.02, -0.12, 0.105), (2.3, 2.92, 0.03), C.material("sheets", "#EEF5F3", rough=0.8, coat=0.0), 0.01))
    C.bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -0.1, 0.127))
    paper = C.bpy.context.active_object
    paper.name = "Paper"
    paper.scale = (2.25, 2.86, 1)
    C.select_only([paper])
    C.bpy.ops.object.transform_apply(scale=True)
    paper.data.materials.append(C.material("chart_paper", "#FFFFFF", rough=0.85, coat=0.0, sheen=0.0))
    objs.append(paper)
    objs.append(C.rbox("Clip", (0, 1.45, 0.17), (1.0, 0.42, 0.12), m["metal"], 0.05))
    objs.append(C.tube("ClipLever", C.catmull([(-0.35, 1.3, 0.24), (0, 1.22, 0.32), (0.35, 1.3, 0.24)], 6), 0.03, m["metal"]))
    objs.append(C.rbox("ClipPad", (0, 1.32, 0.23), (0.8, 0.08, 0.04), m["coral"], 0.015))
    return finish("Chart", objs)


# ── 도장 ────────────────────────────────────────────────
def stamp():
    m = mats()
    objs = [C.cylinder("StampPad", (0, 0, 0.025), 0.44, 0.05, m["ink"], bevel=0.015)]
    objs.append(C.lathe("StampBody", [(0.0, 0.05), (0.46, 0.05), (0.47, 0.2), (0.44, 0.26), (0.26, 0.36), (0.15, 0.5), (0.14, 0.72), (0.0, 0.72)], m["coral"]))
    objs.append(C.torus("StampBand", (0, 0, 0.23), 0.46, 0.03, m["white"]))
    objs.append(C.sphere("StampKnob", (0, 0, 0.92), (0.3, 0.3, 0.27), m["coral"], segs=32, rings=16))
    objs.append(C.sphere("StampShine", (-0.1, -0.16, 1.04), (0.07, 0.04, 0.05), m["paper"], segs=12, rings=6))
    return finish("Stamp", objs)


# ── 진짜 책상: 나무 상판 + 흰 프레임 + 데스크 패드 + 고정 소품 ─────────
# 상판 윗면 z=0, 크기 18×9 (x: -9~9, y: -4.5~4.5). 사용자(환자)는 -Y 쪽, 박사님은 +Y 쪽에 앉는다.
DESK_W, DESK_D, LEG = 18.0, 9.0, 7.6


def desk():
    m = mats()
    wood = C.wood_material("wood")
    objs = [C.rbox("DeskTop", (0, 0, -0.225), (DESK_W, DESK_D, 0.45), wood, 0.08)]
    frame = C.material("frame", "#F7FAF9", rough=0.45, coat=0.4)
    objs.append(C.rbox("Apron", (0, 0, -0.62), (DESK_W - 0.6, DESK_D - 0.6, 0.35), frame, 0.04))
    objs.append(C.rbox("FrontPanel", (0, -DESK_D / 2 + 0.45, -0.45 - 3.6), (DESK_W - 1.6, 0.25, 6.6), frame, 0.06))
    objs.append(C.rbox("PanelRail", (0, -DESK_D / 2 + 0.3, -2.4), (DESK_W - 1.8, 0.08, 0.28), m["teal"], 0.03))
    objs.append(C.rbox("PanelBase", (0, -DESK_D / 2 + 0.3, -7.6), (DESK_W - 1.8, 0.08, 0.4), m["deep"], 0.03))
    for sx in (-1, 1):
        for sy in (-1, 1):
            objs.append(C.rbox(f"Leg{sx}{sy}", (sx * (DESK_W / 2 - 0.55), sy * (DESK_D / 2 - 0.55), -0.45 - LEG / 2), (0.6, 0.6, LEG), frame, 0.08))
            objs.append(C.cylinder(f"Foot{sx}{sy}", (sx * (DESK_W / 2 - 0.55), sy * (DESK_D / 2 - 0.55), -0.45 - LEG - 0.06), 0.32, 0.12, m["deep"], bevel=0.03))
    # 데스크 패드 (블리스터를 놓는 자리)
    objs.append(C.rbox("Pad", (0.6, -0.9, 0.033), (10.4, 5.0, 0.05), C.material("pad", "#2E7A75", rough=0.7, coat=0.15, sheen=0.4), 0.04))
    stitch = [C.rbox(f"St{i}", (0.6 - 5.0 + i * 0.25, -0.9 + s * 2.3, 0.062), (0.12, 0.025, 0.006), C.material("stitch", "#9FD6CB", rough=0.8, coat=0.0), 0.004)
              for s in (-1, 1) for i in range(41)]
    objs.append(C.join(stitch, "PadStitch"))
    # 명패 (환자 쪽을 봄)
    plate = C.mesh_obj("NamePlate", [(-1.4, -0.3, 0), (1.4, -0.3, 0), (1.4, 0.3, 0), (-1.4, 0.3, 0), (-1.4, 0.05, 0.6), (1.4, 0.05, 0.6)],
                       [(0, 1, 5, 4), (3, 4, 5, 2), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)], m["white"], smooth=False)
    C.add_bevel(plate, 0.03, 3)
    plate.location = (4.4, -3.7, 0)
    objs.append(plate)
    face_rot = (math.atan2(0.6, 0.35), 0, 0)
    objs.append(C.text("PlateText", "DR. PATCH", (4.4, -3.84, 0.36), 0.32, m["deep"], rot=face_rot, extrude=0.01))
    objs.append(C.text("PlateSub", "SERVER MEDICINE", (4.4, -3.92, 0.17), 0.13, m["teal"], rot=face_rot, extrude=0.006))
    # 펜꽂이
    cup = C.lathe("PenCup", [(0.0, 0.0), (0.42, 0.0), (0.45, 0.85), (0.4, 0.85), (0.37, 0.08), (0.0, 0.08)], m["teal"])
    cup.location = (-4.2, 3.9, 0)
    objs.append(cup)
    for i, (col, dx, tilt) in enumerate((("coral", -0.12, 0.25), ("ink", 0.08, -0.15), ("white", 0.15, 0.3))):
        objs.append(C.cylinder(f"CupPen{i}", (-4.2 + dx, 3.9 + dx * 0.5, 0.95), 0.04, 1.1, m[col], rot=(tilt, -tilt * 0.6, 0), bevel=0.01))
    # 메모지 · 체온계
    objs.append(C.rbox("Memo", (4.6, 3.5, 0.12), (1.3, 1.3, 0.24), m["paper"], 0.03, rot=(0, 0, -0.15)))
    objs.append(C.rbox("Sticky1", (4.65, 3.45, 0.25), (1.0, 1.0, 0.02), m["mint"], 0.01, rot=(0, 0, -0.05)))
    objs.append(C.rbox("Sticky2", (5.0, 3.1, 0.27), (0.7, 0.7, 0.02), C.material("sticky_coral", "#FFC7B5", rough=0.8, coat=0.0), 0.01, rot=(0, 0, 0.25)))
    # 볼펜 (머그컵 왼쪽): 실제 비율 — 길이 1.6(≈14cm) · 지름 0.11(≈1cm). 클립이 위를 보게 눕힌다
    chrome = C.material("chrome", "#E9EEF0", rough=0.1, metal=1.0, coat=0.0)
    rubber = C.material("rubber", "#2E7A75", rough=0.75, coat=0.0, sheen=0.4)
    gloss = C.material("pen_body", "#FFFFFF", rough=0.15, coat=1.0, coat_rough=0.05)
    r = 0.055
    parts = [
        C.sphere("PenBall", (0, 0, 0.004), (0.008, 0.008, 0.008), chrome, segs=8, rings=4),
        C.lathe("PenTip", [(0.0, 0.0), (0.008, 0.006), (0.016, 0.05), (0.04, 0.17), (r * 0.95, 0.22), (0.0, 0.22)], chrome, segs=32),
        C.lathe("PenGrip", [(0.0, 0.215), (r * 0.98, 0.215), (r * 1.08, 0.26), (r * 1.08, 0.52), (r, 0.56), (0.0, 0.56)], rubber, segs=32),
        C.lathe("PenBody", [(0.0, 0.55), (r, 0.55), (r * 1.02, 0.9), (r * 0.97, 1.36), (0.0, 1.36)], gloss, segs=32),
        C.lathe("PenRing", [(0.0, 1.355), (r * 1.02, 1.355), (r * 1.02, 1.39), (0.0, 1.39)], chrome, segs=32),
        C.lathe("PenCap", [(0.0, 1.385), (r * 0.98, 1.385), (r * 0.98, 1.52), (r * 0.85, 1.55), (0.0, 1.55)], m["teal"], segs=32),
        C.lathe("PenClick", [(0.0, 1.545), (0.03, 1.545), (0.03, 1.62), (0.0, 1.64)], chrome, segs=24),
    ]
    grips = [C.torus(f"GripRib{i}", (0, 0, 0.29 + i * 0.045), r * 1.08, 0.006, rubber) for i in range(6)]
    parts.append(C.join(grips, "GripRibs"))
    # 클립: 뒤캡에서 몸통을 따라 내려오는 얇은 금속 띠 + 끝 구슬 (회전 뒤 위쪽 = 지금의 -X)
    parts.append(C.tube("PenClip", C.catmull([(-r * 0.9, 0, 1.5), (-r - 0.035, 0, 1.44), (-r - 0.03, 0, 1.12), (-r - 0.012, 0, 0.98)], 8), 0.011, chrome))
    parts.append(C.sphere("PenClipBead", (-r - 0.015, 0, 0.975), (0.018, 0.016, 0.022), chrome, segs=12, rings=6))
    C.select_only(parts)
    C.bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)  # 회전 전에 기준점을 모두 원점으로 (각자 기준점으로 돌면 어긋남)
    C.apply_rot(parts, (0, PI / 2, 0))  # 눕힌다 (+X로 뻗음, 클립은 위)
    for o in parts:
        o.location = (6.3, 3.1, r + 0.004)  # 메모지(x≤5.3)와 머그컵(x≥7.55) 사이 빈자리
        o.rotation_euler = (0, 0, 2.55)
    objs += parts
    # 머그컵
    mug = C.lathe("Mug", [(0.0, 0.0), (0.42, 0.0), (0.45, 0.8), (0.4, 0.8), (0.38, 0.08), (0.0, 0.08)], m["coral"])
    mug.location = (8.0, 2.4, 0)
    handle = C.torus("MugHandle", (8.47, 2.4, 0.42), 0.2, 0.05, m["coral"], rot=(PI / 2, 0, 0))
    tea = C.cylinder("Tea", (8.0, 2.4, 0.66), 0.39, 0.02, C.material("tea", "#7A5A44", rough=0.15, coat=1.0))
    objs += [mug, handle, tea]
    # 화분 (앞쪽 왼쪽 모서리): 다육이 잎을 겹겹이
    px, py = -8.0, -3.6
    # 화분은 속이 빈 그릇: 테두리(0.95) 안쪽으로 내려가 바닥(0.84)에서 막힘 → 흙이 그 위(0.86~0.91)에 따로 놓여 면이 겹치지 않는다
    pot = C.lathe("Pot", [(0.0, 0.0), (0.45, 0.0), (0.58, 0.8), (0.62, 0.86), (0.62, 0.95), (0.56, 0.95), (0.53, 0.84), (0.0, 0.84)], m["white"])
    pot.location = (px, py, 0)
    band = C.lathe("PotBand", [(0.54, 0.6), (0.565, 0.6), (0.588, 0.75), (0.563, 0.75)], m["teal"])  # 비스듬한 화분 벽을 따라 붙임
    band.location = (px, py, 0)
    soil_m = C.material("soil", "#4A3F36", rough=0.95, coat=0.0)
    soil = C.cylinder("Soil", (px, py, 0.885), 0.535, 0.05, soil_m)
    crumbs = [C.sphere(f"Crumb{i}", (px + 0.38 * math.cos(i * 2.4), py + 0.38 * math.sin(i * 2.4), 0.915), (0.05, 0.05, 0.025), soil_m, segs=10, rings=6) for i in range(9)]
    objs += [pot, band, soil, C.join(crumbs, "SoilCrumbs")]
    leaves = []
    for ring, (count, length, width, tilt, col) in enumerate(((8, 0.75, 0.26, 0.55, "#4F9E7E"), (6, 0.6, 0.24, 0.85, "#69B592"), (4, 0.42, 0.2, 1.15, "#8ACBA8"))):
        lm = C.material(f"leaf{ring}", col, rough=0.45, coat=0.45, sheen=0.3)
        for k in range(count):
            a = k * 2 * PI / count + ring * 0.4
            lf = C.leaf(f"Leaf{ring}_{k}", length, width, 0.12, lm)
            # 밑동을 링마다 높이고 바깥으로 벌려, 잎끼리 같은 자리에서 겹쳐 깜빡이지 않게
            lf.location = (px + 0.06 * (2 - ring) * math.cos(a), py + 0.06 * (2 - ring) * math.sin(a), 0.93 + ring * 0.09)
            lf.rotation_euler = (tilt * 0.6, 0, a)
            leaves.append(lf)
    objs += leaves
    return finish("Desk", objs)


def tray():
    """곡반(트레이): 패치가 필요 없는 안전한 패키지를 담는다."""
    m = mats()
    dish = C.lathe("Dish", [(0.0, 0.03), (0.78, 0.03), (0.96, 0.12), (1.04, 0.24), (1.12, 0.27)], C.material("steel", "#D7DFE0", rough=0.22, metal=0.9, coat=0.4), segs=64)
    dish.scale = (1.75, 1.0, 1.0)
    C.solidify(dish, 0.03)
    objs = [dish]
    objs.append(C.rbox("TrayTag", (0, -1.08, 0.2), (0.9, 0.04, 0.22), m["paper"], 0.02))
    objs.append(C.text("TrayText", "OK", (0, -1.11, 0.2), 0.14, m["deep"], rot=(PI / 2, 0, 0)))
    return finish("Tray", objs)


BUILDERS = {"capsule": capsule, "blister_cell": blister_cell, "blister_end": blister_end, "tray": tray, "iv": iv, "bottle": bottle, "chart": chart, "stamp": stamp, "desk": desk}

if __name__ == "__main__":
    only = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(BUILDERS)
    for name in only:
        C.reset()
        BUILDERS[name]()
        C.export_glb(f"{name}.glb")
