import bpy
import math
import os
 
# ═══════════════════════════════════════════════════════
#  ★  USER CONFIG — only edit these two lines  ★
SOLAR_FOLDER = r"C:\solar"
PLANET_NAME  = "mars"
# ═══════════════════════════════════════════════════════
 
# Planet presets — axial tilt (degrees) and relative size
PLANET_DATA = {
    "mercury": {"tilt": 0.03,  "radius": 1.2, "spin_speed": 0.3},
    "venus":   {"tilt": 177.4, "radius": 1.8, "spin_speed": 0.1},
    "earth":   {"tilt": 23.5,  "radius": 2.0, "spin_speed": 1.0},
    "mars":    {"tilt": 25.2,  "radius": 1.6, "spin_speed": 0.9},
    "jupiter": {"tilt": 3.1,   "radius": 3.5, "spin_speed": 2.4},
    "saturn":  {"tilt": 26.7,  "radius": 3.0, "spin_speed": 2.2},
    "uranus":  {"tilt": 97.8,  "radius": 2.4, "spin_speed": 1.4},
    "neptune": {"tilt": 28.3,  "radius": 2.3, "spin_speed": 1.5},
}
DEFAULT_PRESET = {"tilt": 0.0, "radius": 2.0, "spin_speed": 1.0}
 
ROTATION_FRAMES = 200   # frames for one full spin
ANIM_END        = 400
 
 
# ───────────────────────────────────────────────────────
#  AUTO-DETECT TEXTURES
# ───────────────────────────────────────────────────────
SUPPORTED = {".jpg", ".jpeg", ".png", ".exr", ".hdr"}
 
def find_texture(folder, planet):
    """Find the planet surface texture by matching the planet name in filename."""
    best = None
    for f in os.listdir(folder):
        name, ext = os.path.splitext(f.lower())
        if ext not in SUPPORTED:
            continue
        if planet.lower() in name:
            full = os.path.join(folder, f)
            # prefer files that also have 'bg', 'texture', 'surface', 'map'
            if any(k in name for k in ("bg", "texture", "surface", "map", "color", "albedo")):
                return full
            best = full
    return best
 
 
def find_background(folder):
    """Find the starfield / space background texture."""
    keywords = ("star", "space", "sky", "cosmos", "galaxy", "universe", "nebula", "bg_space")
    for f in os.listdir(folder):
        name, ext = os.path.splitext(f.lower())
        if ext not in SUPPORTED:
            continue
        if any(k in name for k in keywords):
            return os.path.join(folder, f)
    return None
 
 
# ───────────────────────────────────────────────────────
#  SCENE SETUP
# ───────────────────────────────────────────────────────
def clean_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
 
 
def make_planet(name, preset, texture_path):
    radius = preset["radius"]
    tilt   = math.radians(preset["tilt"])
 
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius, segments=128, ring_count=64, location=(0, 0, 0)
    )
    planet = bpy.context.active_object
    planet.name = name.capitalize()
    bpy.ops.object.shade_smooth()
 
    # Apply axial tilt on X
    planet.rotation_euler[0] = tilt
 
    # ── Material ──────────────────────────────────────
    mat = bpy.data.materials.new(f"{name.capitalize()}_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
 
    tex_coord = nodes.new("ShaderNodeTexCoord");  tex_coord.location = (-800, 0)
    mapping   = nodes.new("ShaderNodeMapping");   mapping.location   = (-600, 0)
    img_tex   = nodes.new("ShaderNodeTexImage");  img_tex.location   = (-300, 0)
    bsdf      = nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (100, 0)
    out       = nodes.new("ShaderNodeOutputMaterial"); out.location  = (400, 0)
 
    if texture_path and os.path.exists(texture_path):
        img_tex.image = bpy.data.images.load(texture_path)
        print(f"  ✓ Planet texture  : {texture_path}")
    else:
        print(f"  ⚠ No texture found for '{name}' — using default grey")
 
    bsdf.inputs["Roughness"].default_value = 0.85
    bsdf.inputs["Metallic"].default_value  = 0.0
    try:
        bsdf.inputs["Specular IOR Level"].default_value = 0.1
    except KeyError:
        pass  # older Blender uses "Specular"
 
    links.new(tex_coord.outputs["UV"],   mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], img_tex.inputs["Vector"])
    links.new(img_tex.outputs["Color"],  bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"],      out.inputs["Surface"])
 
    planet.data.materials.append(mat)
    return planet
 
 
def set_background(bg_path):
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()
 
    env   = nodes.new("ShaderNodeTexEnvironment"); env.location = (-300, 0)
    bg    = nodes.new("ShaderNodeBackground");     bg.location  = (50, 0)
    out   = nodes.new("ShaderNodeOutputWorld");    out.location = (300, 0)
 
    if bg_path and os.path.exists(bg_path):
        env.image = bpy.data.images.load(bg_path)
        print(f"  ✓ Background      : {bg_path}")
    else:
        print("  ⚠ No background found — world stays black")
 
    bg.inputs["Strength"].default_value = 1.0
    links.new(env.outputs["Color"],        bg.inputs["Color"])
    links.new(bg.outputs["Background"],    out.inputs["Surface"])
 
 
def add_lights():
    bpy.ops.object.light_add(type='SUN', location=(6, -6, 6))
    sun = bpy.context.active_object
    sun.name = "Sun_Key"
    sun.data.energy = 3.0
    sun.data.angle  = math.radians(5)
 
    bpy.ops.object.light_add(type='AREA', location=(-5, 4, 3))
    fill = bpy.context.active_object
    fill.name = "Fill"
    fill.data.energy = 0.4
    fill.data.size   = 8.0
 
 
def add_camera(radius):
    dist = radius * 3.5
    bpy.ops.object.camera_add(location=(0, -dist, dist * 0.25))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.rotation_euler = (math.radians(75), 0, 0)
    bpy.context.scene.camera = cam
 
 
def animate(planet, preset):
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end   = ANIM_END
 
    # Driver: smooth infinite Z-rotation (no fcurves needed)
    if planet.animation_data is None:
        planet.animation_data_create()
 
    speed = preset["spin_speed"]
    drv = planet.driver_add("rotation_euler", 2).driver
    drv.type       = 'SCRIPTED'
    drv.expression = f"frame / {ROTATION_FRAMES} * 6.28318530 * {speed}"
    print(f"  ✓ Rotation driver : 1 spin / {ROTATION_FRAMES} frames  (speed ×{speed})")
 
 
def setup_render(res_x=1920, res_y=1080):
    scene = bpy.context.scene
    scene.render.engine        = 'CYCLES'
    scene.cycles.samples       = 128
    scene.render.resolution_x  = res_x
    scene.render.resolution_y  = res_y
    scene.render.film_transparent = False
 
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.refresh_devices()
        for d in prefs.devices:
            d.use = True
        scene.cycles.device = 'GPU'
        print("  ✓ Render          : Cycles GPU")
    except Exception:
        scene.cycles.device = 'CPU'
        print("  ℹ Render          : Cycles CPU")
 
 
# ───────────────────────────────────────────────────────
#  MAIN
# ───────────────────────────────────────────────────────
def build_planet(folder, planet_name):
    print(f"\n{'═'*52}")
    print(f"  AUTO PLANET — {planet_name.upper()}")
    print(f"  Folder: {folder}")
    print(f"{'═'*52}")
 
    if not os.path.isdir(folder):
        print(f"  ✗ Folder not found: {folder}")
        return
 
    # Auto-detect textures
    tex_path = find_texture(folder, planet_name)
    bg_path  = find_background(folder)
 
    preset = PLANET_DATA.get(planet_name.lower(), DEFAULT_PRESET)
    print(f"  Preset  : tilt={preset['tilt']}°  radius={preset['radius']}  speed=×{preset['spin_speed']}")
 
    clean_scene()
    planet = make_planet(planet_name, preset, tex_path)
    set_background(bg_path)
    add_lights()
    add_camera(preset["radius"])
    animate(planet, preset)
    setup_render()
 
    bpy.context.view_layer.objects.active = planet
    planet.select_set(True)
 
    print(f"\n  ✅ Done! '{planet.name}' is ready.")
    print(f"     → Press SPACE to preview")
    print(f"     → Ctrl+F12 to render animation")
    print(f"{'═'*52}\n")
 
 
# ── RUN ───────────────────────────────────────────────
build_planet(SOLAR_FOLDER, PLANET_NAME)