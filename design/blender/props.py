"""DR.PATCH 책상 소품 7종 → prototype/drpatch-desk/models/*.glb

좌표: Blender Z가 위, 정면(카메라 쪽)이 -Y. glTF로 나가면 Three.js에서 Y가 위, 정면이 +Z.
코드가 찾아 쓰는 이름 (바꾸면 index.html도 같이 고칠 것):
  capsule  : CapCur(현재 버전 반쪽, 재질 cap_cur), CapTgt(목표 버전 반쪽, 재질 cap_tgt)
  blister  : Label(회차 라벨 자리, 글자는 코드가 그림), Dome0~5(투명 덮개, 0~2 뒷줄 · 3~5 앞줄)
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


# ── 블리스터 팩 (한 판 = 한 회차) ────────────────────────
SLOTS = [(x, y) for y in (0.62, -0.62) for x in (-0.75, 0.65, 2.05)]


def blister():
    m = mats()
    foil = C.material("foil", "#E3EAEA", rough=0.26, metal=0.8, coat=0.6)
    well_m = C.material("foil_well", "#C3CFD0", rough=0.3, metal=0.7, coat=0.3)
    objs = [C.rbox("Foil", (0, 0, 0.07), (5.4, 2.9, 0.14), foil, 0.06)]
    objs.append(C.rbox("FoilRim", (0, 0, 0.068), (5.48, 2.98, 0.1), C.material("foil_rim", "#CBD6D6", rough=0.3, metal=0.7), 0.06))
    C.bpy.ops.mesh.primitive_plane_add(size=1, location=(-2.05, 0, 0.142))
    label = C.bpy.context.active_object
    label.name = "Label"
    label.scale = (1.1, 2.6, 1)
    C.select_only([label])
    C.bpy.ops.object.transform_apply(scale=True)
    label.data.materials.append(C.material("label", "#16313A", rough=0.6, coat=0.2))
    objs.append(label)
    wells = [C.sphere(f"Well{i}", (x, y, 0.141), (0.66, 0.42, 0.012), well_m, segs=48, rings=12) for i, (x, y) in enumerate(SLOTS)]
    objs.append(C.join(wells, "Wells"))
    dome_m = C.glass_mat("#FFFFFF", "dome")
    for i, (x, y) in enumerate(SLOTS):
        d = C.lathe(f"Dome{i}", C.capsule_profile(0.4, 0.25), dome_m, segs=40)
        C.apply_rot([d], (0, PI / 2, 0))
        d.scale = (1, 1, 0.78)
        C.select_only([d])
        C.bpy.ops.object.transform_apply(scale=True)
        d.location = (x, y, 0.14)
        objs.append(d)
    dots = [C.sphere(f"Perf{i}", (-1.45, -1.3 + i * 0.13, 0.142), (0.02, 0.02, 0.006), well_m, segs=8, rings=4) for i in range(21)]
    dots += [C.sphere(f"PerfH{i}", (-1.3 + i * 0.13, 0.0, 0.142), (0.02, 0.02, 0.006), well_m, segs=8, rings=4) for i in range(30)]
    objs.append(C.join(dots, "Perforation"))
    objs.append(C.text("FoilPrint", "DR.PATCH  ·  PATCH TABLETS", (0.65, -1.33, 0.142), 0.1, m["faint"], extrude=0.002))
    return finish("Blister", objs)


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
    tube_pts = C.catmull([(1.05, 0, 1.4), (1.05, -0.02, 1.0), (0.85, -0.1, 0.55), (0.4, -0.25, 0.3), (0.0, -0.45, 0.25)], 8)
    objs.append(C.tube("Line", tube_pts, 0.022, C.material("line", "#E2F2EE", rough=0.2, transmission=0.4)))
    objs.append(C.rbox("RollerClamp", (1.05, -0.02, 1.05), (0.13, 0.12, 0.24), m["teal"], 0.03))
    return finish("IV", objs)


# ── 약병 (접수된 패키지가 담김) ─────────────────────────
def bottle():
    m = mats()
    body = C.lathe("BottleBody", [(0.0, 0.0), (1.1, 0.0), (1.2, 0.08), (1.2, 1.9), (1.12, 2.06), (1.0, 2.16), (1.0, 2.26)],
                   C.glass_mat("#D2F0E8", "bottle_glass"))
    base = C.lathe("BottleBase", [(0.0, 0.0), (1.12, 0.0), (1.18, 0.05), (1.18, 0.1), (0.0, 0.1)], m["white"])
    lab = C.lathe("BottleLabel", [(1.212, 0.32), (1.212, 0.95)], m["paper"])
    stripe = C.lathe("BottleStripe", [(1.218, 0.86), (1.218, 0.95)], m["teal"])
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
    C.bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -0.1, 0.123))
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


# ── 진료 책상 + 고정 소품 ────────────────────────────────
def desk():
    m = mats()
    objs = [C.rbox("DeskTop", (0, 0, -0.3), (18, 11.5, 0.6), C.material("desk", "#FBFDFC", rough=0.5, coat=0.3), 0.25)]
    objs.append(C.rbox("DeskRail", (0, -5.76, -0.33), (17.4, 0.06, 0.2), m["teal"], 0.03))
    objs.append(C.rbox("MatRim", (-0.6, 0, 0.02), (7.6, 8.0, 0.04), m["deep"], 0.02))
    objs.append(C.rbox("Mat", (-0.6, 0, 0.035), (7.4, 7.8, 0.04), C.material("mat", "#DDF1EB", rough=0.85, coat=0.0, sheen=0.4), 0.02))
    # 펜꽂이
    cup = C.lathe("PenCup", [(0.0, 0.0), (0.42, 0.0), (0.45, 0.85), (0.4, 0.85), (0.37, 0.08), (0.0, 0.08)], m["teal"])
    cup.location = (-4.7, 4.6, 0)
    objs.append(cup)
    for i, (col, dx, tilt) in enumerate((("coral", -0.12, 0.25), ("ink", 0.08, -0.15), ("white", 0.15, 0.3))):
        objs.append(C.cylinder(f"CupPen{i}", (-4.7 + dx, 4.6 + dx * 0.5, 0.95), 0.04, 1.1, m[col], rot=(tilt, -tilt * 0.6, 0), bevel=0.01))
    # 탁상시계
    clock = C.cylinder("Clock", (2.8, 4.7, 0.62), 0.55, 0.3, m["teal"], rot=(math.radians(70), 0, 0), bevel=0.06)
    face = C.cylinder("ClockFace", (2.8, 4.56, 0.67), 0.45, 0.04, m["paper"], rot=(math.radians(70), 0, 0))
    hand1 = C.rbox("ClockHandH", (2.8, 4.535, 0.74), (0.04, 0.02, 0.22), m["ink"], 0.01, rot=(math.radians(-20), 0, 0))
    hand2 = C.rbox("ClockHandM", (2.9, 4.535, 0.66), (0.3, 0.02, 0.03), m["coral"], 0.008, rot=(math.radians(-20), 0, 0.3))
    objs += [clock, face, hand1, hand2]
    objs += [C.sphere(f"ClockFoot{s}", (2.8 + s * 0.32, 4.8, 0.08), (0.09, 0.09, 0.09), m["deep"], segs=16, rings=8) for s in (-1, 1)]
    # 메모지
    objs.append(C.rbox("Memo", (-2.6, 4.8, 0.12), (1.3, 1.3, 0.24), m["paper"], 0.03, rot=(0, 0, 0.18)))
    objs.append(C.rbox("Sticky1", (-2.55, 4.75, 0.25), (1.0, 1.0, 0.02), m["mint"], 0.01, rot=(0, 0, 0.05)))
    objs.append(C.rbox("Sticky2", (-2.2, 4.4, 0.27), (0.7, 0.7, 0.02), C.material("sticky_coral", "#FFC7B5", rough=0.8, coat=0.0), 0.01, rot=(0, 0, -0.2)))
    # 체온계
    th = C.lathe("Thermo", C.capsule_profile(0.08, 0.55), m["white"], segs=24)
    tip = C.lathe("ThermoTip", C.capsule_profile(0.07, 0.08), m["teal"], segs=24)
    tip.location = (0, 0, -0.62)
    disp = C.rbox("ThermoDisp", (0, -0.075, 0.15), (0.09, 0.02, 0.3), m["ink"], 0.01)
    C.apply_rot([th, tip, disp], (0, PI / 2, 0))
    for o in (th, tip, disp):
        o.location = (1.4, -4.7, 0.09)
        o.rotation_euler = (0, 0, 0.5)
    objs += [th, tip, disp]
    # 화분
    pot = C.lathe("Pot", [(0.0, 0.0), (0.4, 0.0), (0.52, 0.7), (0.0, 0.7)], m["white"])
    pot.location = (7.9, 4.6, 0)
    band = C.lathe("PotBand", [(0.5, 0.55), (0.53, 0.55), (0.535, 0.68), (0.5, 0.68)], m["teal"])
    band.location = (7.9, 4.6, 0)
    soil = C.cylinder("Soil", (7.9, 4.6, 0.68), 0.48, 0.04, C.material("soil", "#4E5B55", rough=0.9, coat=0.0))
    leaf_m = C.material("leaf", "#5DAE8B", rough=0.45, coat=0.4)
    leaves = []
    for k in range(6):
        a = k * PI / 3
        lf = C.sphere(f"Leaf{k}", (7.9 + 0.28 * math.cos(a), 4.6 + 0.28 * math.sin(a), 1.05), (0.16, 0.42, 0.07), leaf_m, segs=24, rings=12)
        lf.rotation_euler = (0.9, 0, a + PI / 2)
        leaves.append(lf)
    leaves.append(C.sphere("LeafTop", (7.9, 4.6, 1.2), (0.14, 0.3, 0.08), leaf_m, segs=24, rings=12))
    objs += [pot, band, soil] + leaves
    # 머그컵
    mug = C.lathe("Mug", [(0.0, 0.0), (0.42, 0.0), (0.45, 0.8), (0.4, 0.8), (0.38, 0.08), (0.0, 0.08)], m["coral"])
    mug.location = (8.0, 0.2, 0)
    handle = C.torus("MugHandle", (8.47, 0.2, 0.42), 0.2, 0.05, m["coral"], rot=(PI / 2, 0, 0))
    tea = C.cylinder("Tea", (8.0, 0.2, 0.66), 0.39, 0.02, C.material("tea", "#7A5A44", rough=0.15, coat=1.0))
    objs += [mug, handle, tea]
    return finish("Desk", objs)


BUILDERS = {"capsule": capsule, "blister": blister, "iv": iv, "bottle": bottle, "chart": chart, "stamp": stamp, "desk": desk}

if __name__ == "__main__":
    only = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(BUILDERS)
    for name in only:
        C.reset()
        BUILDERS[name]()
        C.export_glb(f"{name}.glb")
