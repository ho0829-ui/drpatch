"""DR.PATCH 3D 소품 공용 도구 (Blender 5.x).

모든 소품이 같은 팔레트·재질·모양 규칙을 쓰게 해서 통일감을 낸다 (docs/design.md).
실행: blender -b --factory-startup -P design/blender/<소품>.py
결과: prototype/drpatch-desk/models/<소품>.glb + design/blender/previews/<소품>.png
"""

import math
import os

import bpy
import bmesh
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS = os.path.join(ROOT, "prototype", "drpatch-desk", "models")
PREVIEWS = os.path.join(ROOT, "design", "blender", "previews")

# 병원 청록 팔레트 (docs/design.md)
PALETTE = {
    "white": "#F8FBFA", "paper": "#FFFFFF", "bg": "#EAF6F3", "mint": "#B9E2D9",
    "teal": "#3E9E98", "deep": "#1F6F6B", "ink": "#16313A", "coral": "#F2734A",
    "blush": "#F6A8A0", "metal": "#DDE5E6",
}


def srgb(hex_color: str, alpha: float = 1.0):
    h = hex_color.lstrip("#")
    lin = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        lin.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*lin, alpha)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


# ── 재질 ────────────────────────────────────────────────
def _bsdf(m):
    nt = m.node_tree
    node = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if node is None:
        node = nt.nodes.new("ShaderNodeBsdfPrincipled")
        out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None) or nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(node.outputs[0], out.inputs[0])
    return node


def _set(node, names, value):
    for n in names:
        if n in node.inputs:
            node.inputs[n].default_value = value
            return


def material(name, color, rough=0.38, metal=0.0, coat=0.5, coat_rough=0.22, transmission=0.0, sheen=0.15):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    b = _bsdf(m)
    _set(b, ["Base Color"], srgb(color))
    _set(b, ["Roughness"], rough)
    _set(b, ["Metallic"], metal)
    _set(b, ["Coat Weight", "Clearcoat"], coat)
    _set(b, ["Coat Roughness", "Clearcoat Roughness"], coat_rough)
    _set(b, ["Transmission Weight", "Transmission"], transmission)
    _set(b, ["Sheen Weight", "Sheen"], sheen)
    m.diffuse_color = srgb(color)
    return m


def plastic(key, **kw):
    """기본 말랑 플라스틱: 반광 + 얇은 코팅."""
    return material(f"plastic_{key}", PALETTE[key], **kw)


def metal_mat():
    return material("metal", PALETTE["metal"], rough=0.18, metal=1.0, coat=0.0)


def glass_mat(tint="#FFFFFF", name="glass"):
    return material(name, tint, rough=0.05, transmission=1.0, coat=1.0, coat_rough=0.05, sheen=0.0)


# ── 도형 ────────────────────────────────────────────────
def _link(ob):
    bpy.context.collection.objects.link(ob)
    return ob


def mesh_obj(name, verts, faces, mat=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    if mat:
        me.materials.append(mat)
    return _link(bpy.data.objects.new(name, me))


def recalc_normals(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()


def lathe(name, profile, mat=None, segs=64, a0=0.0, a1=2 * math.pi):
    """profile: 아래→위 (반지름, z) 목록. r=0이면 극점. a0~a1만 돌리면 열린 껍질(가운 등)."""
    full = abs((a1 - a0) - 2 * math.pi) < 1e-6
    n = segs if full else segs + 1
    verts, rings = [], []
    for r, z in profile:
        if r < 1e-6:
            rings.append([len(verts)])
            verts.append((0.0, 0.0, z))
            continue
        ring = []
        for j in range(n):
            a = a0 + (a1 - a0) * j / segs
            ring.append(len(verts))
            verts.append((r * math.cos(a), r * math.sin(a), z))
        rings.append(ring)
    faces = []
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1 and len(B) == 1:
            continue
        for j in range(segs):
            j2 = (j + 1) % n if full else j + 1
            if len(A) == 1:
                faces.append((A[0], B[j2], B[j]))
            elif len(B) == 1:
                faces.append((A[j], A[j2], B[0]))
            else:
                faces.append((A[j], A[j2], B[j2], B[j]))
    return mesh_obj(name, verts, faces, mat)


def hemi(r, z0, up, steps=16):
    """반구 단면 (z0에서 시작해 위/아래 극점까지)."""
    pts = []
    for i in range(steps + 1):
        a = (math.pi / 2) * i / steps
        pts.append((r * math.cos(a), z0 + (r * math.sin(a) if up else -r * math.sin(a))))
    return pts if up else pts[::-1]


def catmull(ctrl, per=10):
    """제어점 사이를 부드럽게 잇는다."""
    pts = [Vector(c) for c in ctrl]
    out = []
    for i in range(len(pts) - 1):
        p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1])
    return out


def tube(name, pts, radius, mat=None, sides=16, caps=True):
    pts = [Vector(p) for p in pts]
    verts, faces, prev = [], [], None
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        nrm = t.orthogonal().normalized() if prev is None else (prev - t * prev.dot(t)).normalized()
        b = t.cross(nrm)
        prev = nrm
        for k in range(sides):
            a = 2 * math.pi * k / sides
            verts.append(p + (nrm * math.cos(a) + b * math.sin(a)) * radius)
    s = sides
    for i in range(len(pts) - 1):
        for k in range(s):
            faces.append((i * s + k, i * s + (k + 1) % s, (i + 1) * s + (k + 1) % s, (i + 1) * s + k))
    if caps:
        for end, base in ((pts[0], 0), (pts[-1], (len(pts) - 1) * s)):
            c = len(verts)
            verts.append(end)
            for k in range(s):
                faces.append((c, base + (k + 1) % s, base + k))
    ob = mesh_obj(name, verts, faces, mat)
    recalc_normals(ob)
    return ob


def _active():
    return bpy.context.active_object


def sphere(name, loc, scale, mat, segs=48, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=1, location=loc)
    ob = _active()
    ob.name = name
    ob.scale = scale
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat)
    return ob


def cylinder(name, loc, radius, depth, mat, rot=(0, 0, 0), verts=64, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot)
    ob = _active()
    ob.name = name
    ob.data.materials.append(mat)
    if bevel:
        add_bevel(ob, bevel)
    bpy.ops.object.shade_smooth()
    return ob


def torus(name, loc, major, minor, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=64, minor_segments=16,
                                     location=loc, rotation=rot)
    ob = _active()
    ob.name = name
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat)
    return ob


def rbox(name, loc, size, mat, radius=0.03, rot=(0, 0, 0)):
    """모서리가 둥근 상자 (bevel 모디파이어, 내보낼 때 적용)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = _active()
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    add_bevel(ob, radius)
    bpy.ops.object.shade_smooth()
    return ob


def add_bevel(ob, width, segments=5):
    mod = ob.modifiers.new("bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    return mod


def solidify(ob, thickness):
    mod = ob.modifiers.new("solidify", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = 1
    return mod


def text(name, body, loc, size, mat, rot=(0, 0, 0), extrude=0.004):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    ob = _active()
    ob.name = name
    ob.data.body = body
    ob.data.size = size
    ob.data.extrude = extrude
    ob.data.align_x = "CENTER"
    ob.data.align_y = "CENTER"
    bpy.ops.object.convert(target="MESH")
    ob = _active()
    ob.name = name
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


def empty(name, loc=(0, 0, 0)):
    ob = bpy.data.objects.new(name, None)
    ob.location = loc
    return _link(ob)


def parent(children, par):
    bpy.context.view_layer.update()
    inv = par.matrix_world.inverted()
    for c in children:
        c.parent = par
        c.matrix_parent_inverse = inv


# ── 내보내기·미리보기 ────────────────────────────────────
def export_glb(filename):
    os.makedirs(MODELS, exist_ok=True)
    path = os.path.join(MODELS, filename)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", export_apply=True, export_yup=True,
                              export_cameras=False, export_lights=False)
    print("EXPORTED", path, os.path.getsize(path))
    return path


def render_preview(filename, cam_loc, target, lens=55, size=(900, 900), floor_z=0.0, fov=None):
    """미리보기 이미지: 민트 바탕 + 부드러운 조명. 내보내기가 끝난 뒤에 호출한다 (바닥·조명은 모델에 안 들어감)."""
    os.makedirs(PREVIEWS, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.film_transparent = False
    try:
        scene.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    world = bpy.data.worlds.new("world")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = srgb(PALETTE["mint"])
    bg.inputs[1].default_value = 0.55

    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, floor_z))
    _active().data.materials.append(material("floor", "#CDE9E1", rough=0.8, coat=0.0, sheen=0.0))

    def light(name, loc, energy, size_, color="#FFFFFF"):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy, ld.size = energy, size_
        ld.color = srgb(color)[:3]
        ob = _link(bpy.data.objects.new(name, ld))
        ob.location = loc
        ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

    light("key", (-3.5, -4.5, 6), 420, 4)
    light("fill", (4.5, -3, 3), 140, 5, "#EAF6F3")
    light("rim", (1.5, 5, 5), 380, 3)

    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    if fov:
        cd.sensor_fit = "VERTICAL"
        cd.lens_unit = "FOV"
        cd.angle = math.radians(fov)
    cam = _link(bpy.data.objects.new("cam", cd))
    cam.location = cam_loc
    cam.rotation_euler = (Vector(target) - Vector(cam_loc)).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.filepath = os.path.join(PREVIEWS, filename)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath)


# ── 여러 물체 다루기 ─────────────────────────────────────
def select_only(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def apply_rot(objs, rot):
    """회전을 메시에 굳힌다 (내보낸 뒤 코드가 회전을 0부터 쓰도록)."""
    for o in objs:
        o.rotation_euler = rot
    select_only(objs)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)


def join(objs, name):
    """작은 조각 여러 개(점선, 눈금, 홈)를 한 메시로 합친다 (모디파이어는 먼저 적용)."""
    for o in objs:
        select_only([o])
        for m in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
    select_only(objs)
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = name
    return ob


def capsule_profile(r, half):
    """세운 캡슐 단면 (아래 극점 → 위 극점)."""
    return hemi(r, -half, up=False) + hemi(r, half, up=True)


def roots():
    return [o for o in bpy.context.scene.objects if o.parent is None]


# ── 이미지 재질 (나무결 등) ──────────────────────────────
def wood_material(name="wood", w=1024, h=512, seed=4):
    """밝은 나무결 이미지를 만들어 재질에 붙인다 (glb 안에 같이 들어감)."""
    import numpy as np
    rng = np.random.default_rng(seed)
    x = np.linspace(0, 1, w)[None, :]
    y = np.linspace(0, 1, h)[:, None]
    p = rng.uniform(0, 6.28, 6)
    rings = np.sin(2 * np.pi * (y * 26 + 0.55 * np.sin(2 * np.pi * x * 1.3 + p[0]) + 0.22 * np.sin(2 * np.pi * x * 4.7 + p[1])
                                + 0.12 * np.sin(2 * np.pi * y * 3.1 + p[2])))
    grain = 0.5 + 0.5 * rings
    streak = rng.normal(0, 1, (h, w))
    k = np.ones(40) / 40
    streak = np.apply_along_axis(lambda r: np.convolve(r, k, mode="same"), 1, streak)
    light = np.array([0.86, 0.74, 0.56])
    dark = np.array([0.74, 0.58, 0.40])
    t = (grain ** 0.8)[..., None]
    col = dark * (1 - t) + light * t + streak[..., None] * 0.05
    col = np.clip(col, 0, 1)
    rgba = np.concatenate([col, np.ones((h, w, 1))], axis=2)[::-1].astype(np.float32)
    img = bpy.data.images.new(name, w, h)
    img.pixels.foreach_set(rgba.ravel())
    path = os.path.join(PREVIEWS, f"_{name}.png")
    os.makedirs(PREVIEWS, exist_ok=True)
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    img.pack()
    m = bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    b = _bsdf(m)
    tex = m.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = img
    m.node_tree.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    _set(b, ["Roughness"], 0.45)
    _set(b, ["Coat Weight", "Clearcoat"], 0.35)
    _set(b, ["Coat Roughness", "Clearcoat Roughness"], 0.3)
    return m


def emissive(name, color, strength=1.0):
    m = material(name, color, rough=0.4, coat=0.0, sheen=0.0)
    b = _bsdf(m)
    _set(b, ["Emission Color", "Emission"], srgb(color))
    _set(b, ["Emission Strength"], strength)
    return m


def leaf(name, length, width, bend, mat, segs=24):
    """끝이 뾰족하고 위로 휘는 잎 하나 (+Y 방향으로 뻗음)."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=12, radius=1)
    ob = bpy.context.active_object
    ob.name = name
    for v in ob.data.vertices:
        t = (v.co.y + 1) / 2  # 0: 밑동, 1: 끝
        v.co.x *= width * (1 - 0.85 * t ** 1.6) * (0.6 + 0.4 * min(1, t * 4))
        v.co.z *= width * 0.35 * (1 - 0.7 * t)
        v.co.y = t * length
        v.co.z += bend * t * t
    ob.data.update()
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat)
    return ob
