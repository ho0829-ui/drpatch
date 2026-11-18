"""자주 쓰는 패키지의 특별한 알약 → models/pills.glb (노드 이름 Pill_<패키지>).

실제 로고는 쓰지 않는다: 패키지 대표색 투톤 + 이니셜 각인 + 모양(캡슐·캐플릿·정제·연질캡슐)으로만 구분.
모두 X축으로 눕혀 길이 약 1, 가운데 원점. 목록에 없는 패키지는 capsule.glb(일반 캡슐)를 쓴다.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

PI = math.pi
# 이름: (모양, 주 색, 보조 색, 각인)
POPULAR = {
    "python": ("capsule", "#3776AB", "#FFD43B", "PY"),
    "requests": ("capsule", "#2C5D8F", "#F3F6F6", "RQ"),
    "urllib3": ("capsule", "#5B6CC0", "#F3F6F6", "U3"),
    "django": ("caplet", "#0C4B33", "#44B78B", "DJ"),
    "flask": ("caplet", "#1E1E1E", "#F3F6F6", "FL"),
    "numpy": ("tablet", "#4D77CF", "#9CD3E6", "NP"),
    "pandas": ("tablet", "#150458", "#E70488", "PD"),
    "pytest": ("tablet", "#0A9EDC", "#F3F6F6", "PT"),
    "pyyaml": ("softgel", "#E6B84F", "#7A5A1E", "YM"),
    "jinja2": ("softgel", "#7A2333", "#F3D7DC", "J2"),
}


def mat(key, color, **kw):
    return C.material(f"pill_{key}_{color}", color, rough=0.32, coat=0.7, coat_rough=0.15, **kw)


def capsule(key, c1, c2, letters):
    r, half = 0.26, 0.23
    r2 = r + 0.012
    a = C.lathe(f"{key}_a", C.hemi(r, -half, up=False) + [(r, 0.0), (0.0, 0.0)], mat(key, c1), segs=48)
    b = C.lathe(f"{key}_b", [(0.0, -0.05), (r2, -0.05), (r2, half)] + C.hemi(r2, half, up=True)[1:], mat(key, c2), segs=48)
    lip = C.torus(f"{key}_lip", (0, 0, -0.05), r2, 0.01, mat(key, c2))
    objs = [a, b, lip]
    C.apply_rot(objs, (0, PI / 2, 0))
    t = C.text(f"{key}_txt", letters, (0.26, 0, r2 + 0.004), 0.24, mat(key, c1), extrude=0.016)
    return objs + [t]


def caplet(key, c1, c2, letters):
    body = C.rbox(f"{key}_body", (0, 0, 0), (1.0, 0.48, 0.34), mat(key, c1), 0.165)
    score = C.rbox(f"{key}_score", (0, 0, 0.166), (0.03, 0.26, 0.012), mat(key, c2), 0.004)
    t1 = C.text(f"{key}_txt", letters, (-0.23, 0, 0.176), 0.28, mat(key, c2), extrude=0.016)
    t2 = C.text(f"{key}_txt2", "Rx", (0.26, 0, 0.176), 0.18, mat(key, c2), extrude=0.014)
    return [body, score, t1, t2]


def tablet(key, c1, c2, letters):
    body = C.lathe(f"{key}_body", [(0.0, -0.15), (0.3, -0.12), (0.42, -0.06), (0.45, 0.0), (0.42, 0.06), (0.3, 0.12), (0.0, 0.15)], mat(key, c1), segs=56)
    body.scale = (1.05, 1.05, 1.0)
    band = C.torus(f"{key}_band", (0, 0, 0), 0.468, 0.022, mat(key, c2))
    score = C.rbox(f"{key}_score", (0, -0.3, 0.128), (0.4, 0.025, 0.02), mat(key, c2), 0.008)
    t = C.text(f"{key}_txt", letters, (0, 0.04, 0.156), 0.3, mat(key, c2), extrude=0.016)
    return [body, band, score, t]


def softgel(key, c1, c2, letters):
    gel = C.sphere(f"{key}_gel", (0, 0, 0), (0.52, 0.3, 0.26), C.material(f"gel_{key}", c1, rough=0.08, coat=1.0, coat_rough=0.05, transmission=0.55), segs=48, rings=24)
    core = C.sphere(f"{key}_core", (0, 0, -0.02), (0.38, 0.2, 0.16), mat(key, c1), segs=32, rings=16)
    seam = C.torus(f"{key}_seam", (0, 0, 0), 1.0, 0.012, mat(key, c2))
    seam.scale = (0.52, 0.3, 1.0)
    t = C.text(f"{key}_txt", letters, (0, 0, 0.264), 0.22, mat(key, c2), extrude=0.014)
    return [gel, core, seam, t]


SHAPES = {"capsule": capsule, "caplet": caplet, "tablet": tablet, "softgel": softgel}

C.reset()
for i, (key, (shape, c1, c2, letters)) in enumerate(POPULAR.items()):
    parts = SHAPES[shape](key, c1, c2, letters)
    root = C.empty(f"Pill_{key}")
    C.parent(parts, root)
    root.location = (i * 1.6, 0, 0)

C.export_glb("pills.glb")
C.render_preview("pills.png", cam_loc=(7.2, -9.5, 8.5), target=(7.2, 0, 0), lens=40, size=(1800, 700), floor_z=-0.3)
