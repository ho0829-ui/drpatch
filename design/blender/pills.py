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
def symbol_bolt(key, color, at):
    """단순 번개 기호 (원 테두리 없음)."""
    x, y, z = at
    m = mat(key, color)
    a = C.rbox(f"{key}_sym_a", (x - 0.025, y + 0.04, z), (0.12, 0.036, 0.024), m, 0.006, rot=(0, 0, -0.95))
    b = C.rbox(f"{key}_sym_b", (x, y, z), (0.11, 0.032, 0.024), m, 0.006, rot=(0, 0, 0.25))
    c = C.rbox(f"{key}_sym_c", (x + 0.025, y - 0.04, z), (0.12, 0.036, 0.024), m, 0.006, rot=(0, 0, -0.95))
    return [C.join([a, b, c], f"{key}_sym")]


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


def symbol_horn(key, color, at):
    """나선 원뿔(뿔) 기호."""
    x, y, z = at
    m = mat(key, color)
    profile = [(0.0, 0.0), (0.055, 0.0), (0.042, 0.05), (0.028, 0.10), (0.014, 0.15), (0.0, 0.19)]
    cone = C.lathe(f"{key}_sym_cone", profile, m, segs=24)
    cone.location = (x - 0.06, y, z + 0.015)
    cone.rotation_euler = (0, PI / 2, 0)
    rings = []
    for idx, (off, rad) in enumerate([(0.04, 0.046), (0.085, 0.034), (0.13, 0.022)]):
        r = C.torus(f"{key}_sym_r{idx}", (x - 0.06 + off, y, z + 0.015), rad, 0.008, m, rot=(0, PI / 2 - 0.25, 0))
        rings.append(r)
    return [C.join([cone] + rings, f"{key}_sym")]


def symbol_wave(key, color, at):
    """사인 물결 기호."""
    x, y, z = at
    m = mat(key, color)
    pts = []
    for i in range(25):
        t = (i / 24) * 2 - 1  # -1..1
        pts.append((x + t * 0.16, y + math.sin(t * PI * 1.5) * 0.055, z + 0.006))
    return [C.tube(f"{key}_sym", pts, 0.016, m, sides=12)]


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
    rim = C.torus(f"{key}_sym_rim", (x, y + 0.022, z + 0.004), 0.064, 0.011, m)
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
def capsule(key, c1, c2, letters, sym=None):
    r, half = 0.26, 0.23
    r2 = r + 0.012
    a = C.lathe(f"{key}_a", C.hemi(r, -half, up=False) + [(r, 0.0), (0.0, 0.0)], mat(key, c1), segs=48)
    b = C.lathe(f"{key}_b", [(0.0, -0.05), (r2, -0.05), (r2, half)] + C.hemi(r2, half, up=True)[1:], mat(key, c2), segs=48)
    lip = C.torus(f"{key}_lip", (0, 0, -0.05), r2, 0.01, mat(key, c2))
    objs = [a, b, lip]
    C.apply_rot(objs, (0, PI / 2, 0))
    t = C.text(f"{key}_txt", letters, (0.26, 0, r2 + 0.004), 0.24, mat(key, c1), extrude=0.016)
    extra = SYMBOLS[sym](key, c2, (-0.23, 0, r + 0.004)) if sym else []
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
    band = C.torus(f"{key}_band", (0, 0, 0), 0.468, 0.022, mat(key, c2))
    if sym:
        t = C.text(f"{key}_txt", letters, (0, -0.13, 0.146), 0.23, mat(key, c2), extrude=0.015)
        extra = SYMBOLS[sym](key, c2, (0, 0.13, 0.146))
        return [body, band, t] + extra
    score = C.rbox(f"{key}_score", (0, -0.3, 0.128), (0.4, 0.025, 0.02), mat(key, c2), 0.008)
    t = C.text(f"{key}_txt", letters, (0, 0.04, 0.156), 0.3, mat(key, c2), extrude=0.016)
    return [body, band, score, t]


def softgel(key, c1, c2, letters, sym=None):
    gel = C.sphere(f"{key}_gel", (0, 0, 0), (0.52, 0.3, 0.26), C.material(f"gel_{key}", c1, rough=0.08, coat=1.0, coat_rough=0.05, transmission=0.55), segs=48, rings=24)
    core = C.sphere(f"{key}_core", (0, 0, -0.02), (0.38, 0.2, 0.16), mat(key, c1), segs=32, rings=16)
    seam = C.torus(f"{key}_seam", (0, 0, 0), 1.0, 0.012, mat(key, c2))
    seam.scale = (0.52, 0.3, 1.0)
    if sym:
        t = C.text(f"{key}_txt", letters, (0, -0.085, 0.254), 0.19, mat(key, c2), extrude=0.014)
        extra = SYMBOLS[sym](key, c2, (0, 0.075, 0.254))
        return [gel, core, seam, t] + extra
    t = C.text(f"{key}_txt", letters, (0, 0, 0.264), 0.22, mat(key, c2), extrude=0.014)
    return [gel, core, seam, t]


def softgel_flat(key, c1, c2, letters, sym=None):
    """납작 연질캡슐 (pillow 등 쿠션형)."""
    gel = C.sphere(f"{key}_gel", (0, 0, 0), (0.50, 0.36, 0.19), C.material(f"gel_{key}", c1, rough=0.1, coat=1.0, coat_rough=0.06, transmission=0.52), segs=48, rings=24)
    core = C.sphere(f"{key}_core", (0, 0, -0.015), (0.37, 0.25, 0.12), mat(key, c1), segs=32, rings=16)
    seam = C.torus(f"{key}_seam", (0, 0, 0), 1.0, 0.012, mat(key, c2))
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
