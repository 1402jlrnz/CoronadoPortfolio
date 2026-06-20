import bpy
import math
import os

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────
TEXTURE_DIR    = r"C:\solar"
NEPTUNE_TEX    = "neptune_bg.jpg"
STARS_TEX      = "stars.jpg"
PLANET_RADIUS  = 4.5
TOTAL_FRAMES   = 240
SPIN_DEGREES   = 360

# ─────────────────────────────────────────
# 1. CLEAN SCENE
# ─────────────────────────────────────────
for obj in list(bpy.context.scene.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = TOTAL_FRAMES
scene.render.engine = "BLENDER_EEVEE"

# Color Management for Cinematic Look
scene.view_settings.view_transform = "Filmic"
scene.view_settings.look = "Medium Contrast"

# ─────────────────────────────────────────
# 2. WORLD BACKGROUND (STARS)
# ─────────────────────────────────────────
world = scene.world
if not world:
    world = bpy.data.worlds.new("World")
    scene.world = world
    
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
wn.clear()

w_out = wn.new("ShaderNodeOutputWorld")
w_bg = wn.new("ShaderNodeBackground")

stars_path = os.path.join(TEXTURE_DIR, STARS_TEX)
if os.path.exists(stars_path):
    w_env = wn.new("ShaderNodeTexEnvironment")
    w_env.image = bpy.data.images.load(stars_path)
    wl.new(w_env.outputs["Color"], w_bg.inputs["Color"])
    w_bg.inputs["Strength"].default_value = 0.5
else:
    # Procedural Fallback
    w_noise = wn.new("ShaderNodeTexNoise")
    w_ramp = wn.new("ShaderNodeValToRGB")
    w_noise.inputs["Scale"].default_value = 350.0
    w_noise.inputs["Detail"].default_value = 15.0
    cr = w_ramp.color_ramp
    cr.elements[0].position = 0.55
    cr.elements[0].color = (0.002, 0.002, 0.005, 1.0)
    cr.elements[1].position = 0.65
    cr.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    wl.new(w_noise.outputs["Fac"], w_ramp.inputs["Fac"])
    wl.new(w_ramp.outputs["Color"], w_bg.inputs["Color"])

wl.new(w_bg.outputs["Background"], w_out.inputs["Surface"])

# ─────────────────────────────────────────
# 3. CREATE NEPTUNE
# ─────────────────────────────────────────
bpy.ops.mesh.primitive_uv_sphere_add(
    radius=PLANET_RADIUS, segments=128, ring_count=64, location=(0, 0, 0)
)
neptune = bpy.context.active_object
neptune.name = "Neptune"
bpy.ops.object.shade_smooth()

# ─────────────────────────────────────────
# 4. NEPTUNE MATERIAL
# ─────────────────────────────────────────
mat = bpy.data.materials.new(name="Neptune_Mat")
mat.use_nodes = True
mn = mat.node_tree.nodes
ml = mat.node_tree.links
mn.clear()

m_out = mn.new("ShaderNodeOutputMaterial")
m_bsdf = mn.new("ShaderNodeBsdfPrincipled")
m_bsdf.inputs["Roughness"].default_value = 0.45 # Slight gloss for atmosphere
try: m_bsdf.inputs["Specular"].default_value = 0.2
except KeyError: pass

tex_path = os.path.join(TEXTURE_DIR, NEPTUNE_TEX)
if os.path.exists(tex_path):
    m_tex = mn.new("ShaderNodeTexImage")
    m_tex.image = bpy.data.images.load(tex_path)
    ml.new(m_tex.outputs["Color"], m_bsdf.inputs["Base Color"])
else:
    # Fallback flat blue if texture is missing
    m_bsdf.inputs["Base Color"].default_value = (0.05, 0.15, 0.4, 1.0)
    print(f"⚠️ Texture not found: {tex_path}")

ml.new(m_bsdf.outputs["BSDF"], m_out.inputs["Surface"])
neptune.data.materials.append(mat)

# ─────────────────────────────────────────
# 5. INFINITE SPIN ANIMATION
# ─────────────────────────────────────────
if not neptune.animation_data:
    neptune.animation_data_create()
action = bpy.data.actions.new(name="Neptune_Spin")
neptune.animation_data.action = action

neptune.rotation_euler[2] = 0.0
neptune.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
neptune.rotation_euler[2] = math.radians(SPIN_DEGREES)
neptune.keyframe_insert(data_path="rotation_euler", index=2, frame=TOTAL_FRAMES)

fcurves = []
if hasattr(action, "layers"):
    for layer in action.layers:
        for strip in layer.strips:
            if hasattr(strip, "channelbag"):
                for slot in action.slots:
                    cb = strip.channelbag(slot)
                    if cb and hasattr(cb, "fcurves"):
                        fcurves.extend(cb.fcurves)
elif hasattr(action, "fcurves"):
    fcurves = action.fcurves

for fc in fcurves:
    if fc.data_path == "rotation_euler" and fc.array_index == 2:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        if len(fc.modifiers) == 0:
            fc.modifiers.new('CYCLES')

# ─────────────────────────────────────────
# 6. LIGHTING
# ─────────────────────────────────────────
# Main Sun
bpy.ops.object.light_add(type="SUN", location=(100, -100, 50))
sun = bpy.context.active_object
sun.name = "Sun_Light"
sun.data.energy = 4.5
sun.data.color = (0.95, 0.98, 1.0) # Slightly cool/white sun for outer solar system
sun_track = sun.constraints.new(type='TRACK_TO')
sun_track.target = neptune
sun_track.track_axis = 'TRACK_NEGATIVE_Z'
sun_track.up_axis = 'UP_Y'

# Ambient Fill
bpy.ops.object.light_add(type="AREA", location=(-50, 50, -20))
fill = bpy.context.active_object
fill.name = "Space_Fill"
fill.data.energy = 0.2
fill.data.color = (0.05, 0.1, 0.3)

# ─────────────────────────────────────────
# 7. CAMERA
# ─────────────────────────────────────────
bpy.ops.object.camera_add(location=(14, -18, 5))
cam = bpy.context.active_object
cam.name = "Main_Camera"
cam.data.lens = 50
track = cam.constraints.new(type='TRACK_TO')
track.target = neptune
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'
scene.camera = cam

# Force Camera View
if bpy.context.screen:
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.region_3d.view_perspective = 'CAMERA'
                    break

print("=" * 50)
print("✅ Neptune created successfully!")
print("   - Textures mapped")
print("   - Lighting established")
print("   - Infinite spin applied")
print("=" * 50)