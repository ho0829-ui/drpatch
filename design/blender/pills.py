"""자주 쓰는 패키지의 특별한 알약 → models/pills.glb (노드 이름 Pill_<패키지>).

실제 로고는 쓰지 않는다: 패키지 대표색 투톤 + 이니셜 각인 + 모양(캡슐·캐플릿·정제·연질캡슐) + 일반 기호로 구분.
모두 X축으로 눕혀 길이 약 1, 가운데 원점. 목록에 없는 패키지는 capsule.glb(일반 캡슐)를 쓴다.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

PI = math.pi
# 이름: (모양, 주 색, 보조 색, 각인, 기호)
POPULAR = {
    # 기존 10종 (변경 없음)
    "python": ("capsule", "#3776AB", "#FFD43B", "PY", None),
    "requests": ("capsule", "#2C5D8F", "#F3F6F6", "RQ", None),
    "urllib3": ("capsule", "#5B6CC0", "#F3F6F6", "U3", None),
    "django": ("caplet", "#0C4B33", "#44B78B", "DJ", None),
    "flask": ("caplet", "#1E1E1E", "#F3F6F6", "FL", None),
    "numpy": ("tablet", "#4D77CF", "#9CD3E6", "NP", None),
    "pandas": ("tablet", "#150458", "#E70488", "PD", None),
    "pytest": ("tablet", "#0A9EDC", "#F3F6F6", "PT", None),
    "pyyaml": ("softgel", "#E6B84F", "#7A5A1E", "YM", None),
    "jinja2": ("softgel", "#7A2333", "#F3D7DC", "J2", None),
    # 새 특별 알약 10종 (일반 기호 각인, 실제 로고 금지)
    "fastapi": ("caplet", "#009688", "#E6F7F5", "FA", "bolt"),
    "pydantic": ("tablet", "#C2185B", "#FCE4EC", "PC", "check"),
    "starlette": ("tablet", "#3949AB", "#D1C4E9", "ST", "star"),
    "uvicorn": ("capsule", "#6A3D9A", "#F3E8FF", "UV", "horn"),
    "scipy": ("softgel", "#1E6B7B", "#CBEFF4", "SP", "wave"),
    "matplotlib": ("caplet", "#2F5D62", "#DFEEEA", "MP", "bars"),
    "pillow": ("softgel_flat", "#8D6E63", "#EFEBE9", "PL", "pillow"),
    "celery": ("capsule", "#558B2F", "#DCEDC8", "CL", "leaf"),
    "cryptography": ("tablet", "#37474F", "#CFD8DC", "CR", "lock"),
    "certifi": ("tablet", "#00695C", "#B2DFDB", "CF", "seal"),
}


def mat(key, color, **kw):
    return C.material(f"pill_{key}_{color}", color, rough=0.32, coat=0.7, coat_rough=0.15, **kw)


# ── 일반 기호 함수 (실제 로고 금지, 기본 도형으로만 구성) ──────
def prism(name, pts, at, depth, m, scale=1.0, rot=0.0):
    """평평한 다각형(XY)을 위로 뽑은 기둥. 기호를 또렷한 윤곽으로 새길 때 쓴다."""
    import bmesh
    x0, y0, z0 = at
    cs, sn = math.cos(rot), math.sin(rot)
    me = C.bpy.data.meshes.new(name)
    bm = bmesh.new()

    def tr(px, py):
        px, py = px * scale, py * scale
        return (x0 + px * cs - py * sn, y0 + px * sn + py * cs)

    bot = [bm.verts.new((*tr(px, py), z0)) for px, py in pts]
    top = [bm.verts.new((*tr(px, py), z0 + depth)) for px, py in pts]
    bm.faces.new(list(reversed(bot)))
    bm.faces.new(top)
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    ob = C.bpy.data.objects.new(name, me)
    C.bpy.context.collection.objects.link(ob)
    me.materials.append(m)
    return ob


# 번개: 꺾인 지그재그 한 줄기 (원·방패 테두리 없이)
BOLT = [(0.10, 0.50), (-0.20, 0.02), (-0.02, 0.02), (-0.12, -0.50), (0.22, 0.08), (0.03, 0.08)]


def symbol_bolt(key, color, at):
    """번개 기호."""
    x, y, z = at
    return [prism(f"{key}_sym", BOLT, (x, y, z - 0.006), 0.024, mat(key, color), scale=0.36, rot=-0.15)]


def symbol_check(key, color, at):
    """체크 표시 ✓."""
    x, y, z = at
    m = mat(key, color)
    a = C.rbox(f"{key}_sym_a", (x - 0.045, y - 0.012, z), (0.085, 0.032, 0.024), m, 0.006, rot=(0, 0, -0.78))
    b = C.rbox(f"{key}_sym_b", (x + 0.035, y + 0.015, z), (0.145, 0.032, 0.024), m, 0.006, rot=(0, 0, 0.78))
    return [C.join([a, b], f"{key}_sym")]


def symbol_star(key, color, at):
    """5각 작은 별."""
    x, y, z = at
    m = mat(key, color)
    parts = []
    for k in range(5):
        ang = PI / 2 + k * (2 * PI / 5)
        rx = x + math.cos(ang) * 0.048
        ry = y + math.sin(ang) * 0.048
        parts.append(C.rbox(f"{key}_sym_{k}", (rx, ry, z), (0.095, 0.028, 0.022), m, 0.006, rot=(0, 0, ang)))
    hub = C.cylinder(f"{key}_sym_hub", (x, y, z), 0.04, 0.024, m, verts=24)
    parts.append(hub)
    return [C.join(parts, f"{key}_sym")]


def symbol_horn(key, color, at, groove=None):
    """휘어진 뿔 + 가로 홈 3줄 (윤곽으로 읽히게 평평한 기둥으로)."""
    # 캡슐 윗면은 길이(X) 방향으로 평평하므로 뿔을 X축으로 눕힌다 (Y로 세우면 뒤쪽이 겉면 아래로 묻힘).
    # 로컬 좌표: 밑동 (0, -0.09) → 끝 (0.06, 0.09), rot=+90°로 끝이 -X(캡슐 끝) 쪽을 향함
    x, y, z = at
    n = 10
    rot = PI / 2

    def spine(t):
        return 0.06 * t * t, -0.09 + 0.18 * t, 0.045 * (1 - t) ** 0.8 + 0.004

    right, left = [], []
    for i in range(n + 1):
        cx, cy, w = spine(i / n)
        right.append((cx + w, cy))
        left.append((cx - w, cy))
    pts = right + list(reversed(left))
    parts = [prism(f"{key}_sym_horn", pts, (x, y, z - 0.012), 0.03, mat(key, color), rot=rot)]
    gm = mat(key, groove or color)
    for k, t in enumerate((0.2, 0.42, 0.64)):
        cx, cy, w = spine(t)
        bar = [(cx - w - 0.004, cy - 0.008), (cx + w + 0.004, cy + 0.004), (cx + w + 0.004, cy + 0.014), (cx - w - 0.004, cy + 0.002)]
        parts.append(prism(f"{key}_sym_g{k}", bar, (x, y, z + 0.016), 0.006, gm, rot=rot))
    return [C.join(parts, f"{key}_sym")]


def symbol_wave(key, color, at, surf=None):
    """사인 물결 기호. surf(x, y)가 있으면 알약 겉면을 따라 붙인다."""
    x, y, z = at
    m = mat(key, color)
    pts = []
    for i in range(21):
        t = (i / 20) * 2 - 1  # -1..1
        px, py = x + t * 0.13, y + math.sin(t * PI * 1.5) * 0.045
        pz = (surf(px, py) + 0.006) if surf else z + 0.006
        pts.append((px, py, pz))
    return [C.tube(f"{key}_sym", pts, 0.017, m, sides=8)]


def symbol_bars(key, color, at):
    """막대 그래프 3개."""
    x, y, z = at
    m = mat(key, color)
    b1 = C.rbox(f"{key}_sym_1", (x - 0.075, y - 0.035, z), (0.042, 0.08, 0.024), m, 0.006)
    b2 = C.rbox(f"{key}_sym_2", (x, y - 0.005, z), (0.042, 0.14, 0.024), m, 0.006)
    b3 = C.rbox(f"{key}_sym_3", (x + 0.075, y - 0.02, z), (0.042, 0.11, 0.024), m, 0.006)
    base = C.rbox(f"{key}_sym_base", (x, y - 0.082, z), (0.21, 0.02, 0.022), m, 0.004)
    return [C.join([b1, b2, b3, base], f"{key}_sym")]


def symbol_pillow(key, color, at):
    """베개 홈(쿠션 십자 누빔 + 단추)."""
    x, y, z = at
    m = mat(key, color)
    d1 = C.rbox(f"{key}_sym_d1", (x, y, z), (0.14, 0.022, 0.018), m, 0.005, rot=(0, 0, PI / 4))
    d2 = C.rbox(f"{key}_sym_d2", (x, y, z), (0.14, 0.022, 0.018), m, 0.005, rot=(0, 0, -PI / 4))
    btn = C.cylinder(f"{key}_sym_btn", (x, y, z + 0.006), 0.032, 0.02, m, verts=24)
    return [C.join([d1, d2, btn], f"{key}_sym")]


def symbol_leaf(key, color, at):
    """작은 잎 기호."""
    x, y, z = at
    m = mat(key, color)
    lf = C.leaf(f"{key}_sym_lf", 0.17, 0.062, 0.012, m, segs=18)
    lf.location = (x - 0.05, y - 0.07, z + 0.004)
    lf.rotation_euler = (0, 0, -0.45)
    stem = C.rbox(f"{key}_sym_st", (x - 0.06, y - 0.08, z + 0.004), (0.05, 0.018, 0.016), m, 0.004, rot=(0, 0, 1.1))
    return [C.join([lf, stem], f"{key}_sym")]


def symbol_lock(key, color, at):
    """자물쇠 기호."""
    x, y, z = at
    m = mat(key, color)
    body = C.rbox(f"{key}_sym_body", (x, y - 0.032, z), (0.13, 0.095, 0.024), m, 0.014)
    pts = []
    for i in range(17):
        ang = PI * i / 16  # 0..PI 반원 고리
        pts.append((x + math.cos(ang) * 0.044, y + 0.012 + math.sin(ang) * 0.052, z))
    shackle = C.tube(f"{key}_sym_shackle", pts, 0.014, m, sides=10)
    return [C.join([body, shackle], f"{key}_sym")]


def symbol_seal(key, color, at):
    """리본 도장 기호."""
    x, y, z = at
    m = mat(key, color)
    disc = C.cylinder(f"{key}_sym_disc", (x, y + 0.022, z), 0.062, 0.022, m, verts=24)
    rim = C.torus(f"{key}_sym_rim", (x, y + 0.022, z + 0.004), 0.064, 0.011, m, segs=(24, 6))
    t1 = C.rbox(f"{key}_sym_t1", (x - 0.032, y - 0.055, z - 0.002), (0.032, 0.085, 0.018), m, 0.005, rot=(0, 0, -0.28))
    t2 = C.rbox(f"{key}_sym_t2", (x + 0.032, y - 0.055, z - 0.002), (0.032, 0.085, 0.018), m, 0.005, rot=(0, 0, 0.28))
    return [C.join([disc, rim, t1, t2], f"{key}_sym")]


SYMBOLS = {
    "bolt": symbol_bolt,
    "check": symbol_check,
    "star": symbol_star,
    "horn": symbol_horn,
    "wave": symbol_wave,
    "bars": symbol_bars,
    "pillow": symbol_pillow,
    "leaf": symbol_leaf,
    "lock": symbol_lock,
    "seal": symbol_seal,
}


# ── 알약 기본 모양 4종 (+ 납작 연질캡슐) ──────────────────────
# 새 10종(기호 있음)은 분할 수를 낮춰 용량을 아낀다. 기존 10종은 예전 값 그대로.
def res(sym, old, new):
    return new if sym else old


def capsule(key, c1, c2, letters, sym=None):
    r, half = 0.26, 0.23
    r2 = r + 0.012
    seg = res(sym, 48, 32)
    a = C.lathe(f"{key}_a", C.hemi(r, -half, up=False) + [(r, 0.0), (0.0, 0.0)], mat(key, c1), segs=seg)
    b = C.lathe(f"{key}_b", [(0.0, -0.05), (r2, -0.05), (r2, half)] + C.hemi(r2, half, up=True)[1:], mat(key, c2), segs=seg)
    lip = C.torus(f"{key}_lip", (0, 0, -0.05), r2, 0.01, mat(key, c2), segs=res(sym, (64, 16), (40, 6)))
    objs = [a, b, lip]
    C.apply_rot(objs, (0, PI / 2, 0))
    t = C.text(f"{key}_txt", letters, (0.26, 0, r2 + 0.004), 0.24, mat(key, c1), extrude=0.016)
    if not sym:
        return objs + [t]
    at = (-0.15, 0, r + 0.004)  # 왼쪽 반쪽 원기둥 부분 (끝 반구에 걸치지 않게)
    extra = symbol_horn(key, c2, at, groove=c1) if sym == "horn" else SYMBOLS[sym](key, c2, at)
    return objs + [t] + extra


def caplet(key, c1, c2, letters, sym=None):
    body = C.rbox(f"{key}_body", (0, 0, 0), (1.0, 0.48, 0.34), mat(key, c1), 0.165)
    score = C.rbox(f"{key}_score", (0, 0, 0.166), (0.03, 0.26, 0.012), mat(key, c2), 0.004)
    t1 = C.text(f"{key}_txt", letters, (-0.23, 0, 0.176), 0.28, mat(key, c2), extrude=0.016)
    if sym:
        right = SYMBOLS[sym](key, c2, (0.25, 0, 0.174))
    else:
        right = [C.text(f"{key}_txt2", "Rx", (0.26, 0, 0.176), 0.18, mat(key, c2), extrude=0.014)]
    return [body, score, t1] + right


def tablet(key, c1, c2, letters, sym=None):
    body = C.lathe(f"{key}_body", [(0.0, -0.15), (0.3, -0.12), (0.42, -0.06), (0.45, 0.0), (0.42, 0.06), (0.3, 0.12), (0.0, 0.15)], mat(key, c1), segs=56)
    body.scale = (1.05, 1.05, 1.0)
    band = C.torus(f"{key}_band", (0, 0, 0), 0.468, 0.022, mat(key, c2), segs=res(sym, (64, 16), (48, 8)))
    if sym:
        t = C.text(f"{key}_txt", letters, (0, -0.13, 0.146), 0.23, mat(key, c2), extrude=0.015)
        extra = SYMBOLS[sym](key, c2, (0, 0.13, 0.146))
        return [body, band, t] + extra
    score = C.rbox(f"{key}_score", (0, -0.3, 0.128), (0.4, 0.025, 0.02), mat(key, c2), 0.008)
    t = C.text(f"{key}_txt", letters, (0, 0.04, 0.156), 0.3, mat(key, c2), extrude=0.016)
    return [body, band, score, t]


def softgel(key, c1, c2, letters, sym=None):
    sx, sy, sz = 0.52, 0.3, 0.26
    gel = C.sphere(f"{key}_gel", (0, 0, 0), (sx, sy, sz), C.material(f"gel_{key}", c1, rough=0.08, coat=1.0, coat_rough=0.05, transmission=0.55), segs=res(sym, 48, 36), rings=res(sym, 24, 18))
    core = C.sphere(f"{key}_core", (0, 0, -0.02), (0.38, 0.2, 0.16), mat(key, c1), segs=res(sym, 32, 20), rings=res(sym, 16, 10))
    seam = C.torus(f"{key}_seam", (0, 0, 0), 1.0, 0.012, mat(key, c2), segs=res(sym, (64, 16), (48, 6)))
    seam.scale = (sx, sy, 1.0)
    if sym:
        def surf(px, py):  # 타원체 윗면 높이
            return sz * math.sqrt(max(0.0, 1 - (px / sx) ** 2 - (py / sy) ** 2))

        # 글자는 왼쪽, 기호는 오른쪽 — 위아래로 쌓으면 좁은 폭에서 겹친다
        t = C.text(f"{key}_txt", letters, (-0.17, 0, surf(-0.17, 0) - 0.006), 0.2, mat(key, c2), extrude=0.016)
        if sym == "wave":
            extra = symbol_wave(key, c2, (0.17, 0, 0), surf=surf)
        else:
            extra = SYMBOLS[sym](key, c2, (0.17, 0, surf(0.17, 0)))
        return [gel, core, seam, t] + extra
    t = C.text(f"{key}_txt", letters, (0, 0, 0.264), 0.22, mat(key, c2), extrude=0.014)
    return [gel, core, seam, t]


def softgel_flat(key, c1, c2, letters, sym=None):
    """납작 연질캡슐 (pillow 등 쿠션형)."""
    gel = C.sphere(f"{key}_gel", (0, 0, 0), (0.50, 0.36, 0.19), C.material(f"gel_{key}", c1, rough=0.1, coat=1.0, coat_rough=0.06, transmission=0.52), segs=36, rings=18)
    core = C.sphere(f"{key}_core", (0, 0, -0.015), (0.37, 0.25, 0.12), mat(key, c1), segs=20, rings=10)
    seam = C.torus(f"{key}_seam", (0, 0, 0), 1.0, 0.012, mat(key, c2), segs=(48, 6))
    seam.scale = (0.50, 0.36, 1.0)
    t = C.text(f"{key}_txt", letters, (-0.17, 0, 0.186), 0.20, mat(key, c2), extrude=0.014)
    extra = SYMBOLS[sym](key, c2, (0.16, 0, 0.186)) if sym else []
    return [gel, core, seam, t] + extra


SHAPES = {
    "capsule": capsule,
    "caplet": caplet,
    "tablet": tablet,
    "softgel": softgel,
    "softgel_flat": softgel_flat,
}

C.reset()
for i, (key, (shape, c1, c2, letters, sym)) in enumerate(POPULAR.items()):
    parts = SHAPES[shape](key, c1, c2, letters, sym)
    root = C.empty(f"Pill_{key}")
    C.parent(parts, root)
    col = i % 10
    row = i // 10
    root.location = (col * 1.6, -row * 1.8, 0)

C.export_glb("pills.glb")
C.render_preview("pills.png", cam_loc=(7.2, -13.5, 11.8), target=(7.2, -0.9, 0), lens=35, size=(1800, 900), floor_z=-0.3)
