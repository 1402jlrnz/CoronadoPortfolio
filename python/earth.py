import bpy
import math
import os

# ============================================================
# CONFIGURATION
# ============================================================
TEXTURE_DIR = r"C:\solar"
RENDER_ENGINE = "BLENDER_EEVEE"
RESOLUTION_X = 1920
RESOLUTION_Y = 1080
FRAME_START = 1
FRAME_END = 240

def tex(filename):
    return os.path.join(TEXTURE_DIR, filename)

# ============================================================
# SECTION 1 – SCENE SETUP
# ============================================================
def initialise_environment():
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat, do_unlink=True)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)

    scene = bpy.context.scene
    scene.frame_start = FRAME_START
    scene.frame_end   = FRAME_END

    scene.render.engine       = RENDER_ENGINE
    scene.render.resolution_x = RESOLUTION_X
    scene.render.resolution_y = RESOLUTION_Y
    scene.render.film_transparent = False

    # EEVEE settings
    eevee = scene.eevee
    eevee.use_bloom        = True
    eevee.bloom_intensity  = 0.4
    eevee.bloom_threshold  = 0.8
    eevee.bloom_radius     = 5.0
    eevee.use_ssr          = True
    eevee.use_soft_shadows = True
    eevee.shadow_cube_size = '1024'
    eevee.taa_render_samples = 64

    # World – starfield
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    wnt = world.node_tree
    wnt.nodes.clear()

    bg_node  = wnt.nodes.new("ShaderNodeBackground")
    out_node = wnt.nodes.new("ShaderNodeOutputWorld")
    out_node.location = (300, 0)

    # Procedural nebula layer
    noise = wnt.nodes.new("ShaderNodeTexNoise")
    noise.location = (-600, 200)
    noise.inputs["Scale"].default_value     = 1.2
    noise.inputs["Detail"].default_value    = 15.0
    noise.inputs["Roughness"].default_value = 0.55

    ramp = wnt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-400, 200)
    ramp.color_ramp.elements[0].position = 0.4
    ramp.color_ramp.elements[0].color    = (0.0, 0.0, 0.0, 1.0)
    ramp.color_ramp.elements[1].position = 0.6
    ramp.color_ramp.elements[1].color    = (0.03, 0.003, 0.008, 1.0)
    ramp.color_ramp.elements.new(0.85)
    ramp.color_ramp.elements[2].color    = (0.08, 0.03, 0.01, 1.0)

    wnt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])

    # Stars texture
    stars_path = tex("stars.jpg")
    mix_node = wnt.nodes.new("ShaderNodeMixRGB")
    mix_node.blend_type = 'ADD'
    mix_node.inputs[0].default_value = 1.0
    mix_node.location = (-150, 0)

    if os.path.exists(stars_path):
        tex_coord = wnt.nodes.new("ShaderNodeTexCoord")
        mapping   = wnt.nodes.new("ShaderNodeMapping")
        img_node  = wnt.nodes.new("ShaderNodeTexEnvironment")
        tex_coord.location = (-800, -200)
        mapping.location   = (-600, -200)
        img_node.location  = (-400, -200)
        try:
            img_node.image = bpy.data.images.load(stars_path)
        except Exception:
            pass
        wnt.links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])
        wnt.links.new(mapping.outputs["Vector"],      img_node.inputs["Vector"])
        wnt.links.new(img_node.outputs["Color"],      mix_node.inputs[1])
    else:
        mix_node.inputs[1].default_value = (0.0, 0.0, 0.0, 1.0)

    wnt.links.new(ramp.outputs["Color"],   mix_node.inputs[2])
    wnt.links.new(mix_node.outputs["Color"], bg_node.inputs["Color"])
    bg_node.inputs["Strength"].default_value = 0.6

    wnt.links.new(bg_node.outputs["Background"], out_node.inputs["Surface"])
    return scene

# ============================================================
# SECTION 2 – HELPERS
# ============================================================
def spawn_sphere(name, radius, location=(0, 0, 0), segments=64, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius, location=location,
        segments=segments, ring_count=rings)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    return obj

def spawn_anchor(name, location=(0, 0, 0)):
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
    obj = bpy.context.active_object
    obj.name = name
    return obj

def apply_shader(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

# ============================================================
# SECTION 3 – MATERIALS
# ============================================================
def create_earth_material():
    mat = bpy.data.materials.new(name="Earth_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out  = nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (200, 0)
    bsdf.inputs["Roughness"].default_value = 0.6
    bsdf.inputs["Metallic"].default_value  = 0.0

    earth_path = tex("earth_bg.jpg")
    if os.path.exists(earth_path):
        coord = nodes.new("ShaderNodeTexCoord")
        coord.location = (-600, 0)
        uvmap = nodes.new("ShaderNodeMapping")
        uvmap.location = (-400, 0)
        img = nodes.new("ShaderNodeTexImage")
        img.location = (-150, 50)
        try:
            img.image = bpy.data.images.load(earth_path, check_existing=True)
        except Exception:
            pass
        links.new(coord.outputs["UV"],     uvmap.inputs["Vector"])
        links.new(uvmap.outputs["Vector"], img.inputs["Vector"])
        links.new(img.outputs["Color"],    bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (0.2, 0.5, 0.9, 1.0)
        print("WARNING: earth_bg.jpg not found, using fallback color")

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def create_atmosphere_shader():
    mat = bpy.data.materials.new(name="Earth_Atmosphere")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out   = nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    trans = nodes.new("ShaderNodeBsdfTransparent")
    trans.location = (-100, 100)
    emit  = nodes.new("ShaderNodeEmission")
    emit.location = (-100, -50)
    emit.inputs["Color"].default_value    = (0.2, 0.5, 1.0, 1.0)
    emit.inputs["Strength"].default_value = 0.4

    fac = nodes.new("ShaderNodeLayerWeight")
    fac.location = (-300, 0)
    fac.inputs["Blend"].default_value = 0.4
    mix = nodes.new("ShaderNodeMixShader")
    mix.location = (400, 0)

    links.new(fac.outputs["Facing"],    mix.inputs["Fac"])
    links.new(trans.outputs["BSDF"],    mix.inputs[1])
    links.new(emit.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"],    out.inputs["Surface"])

    mat.blend_method  = "BLEND"
    mat.shadow_method = "NONE"
    return mat

def create_moon_material():
    mat = bpy.data.materials.new(name="Moon_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out  = nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (200, 0)
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Metallic"].default_value  = 0.0

    moon_path = tex("moon.jpg")
    if os.path.exists(moon_path):
        coord = nodes.new("ShaderNodeTexCoord")
        coord.location = (-600, 0)
        uvmap = nodes.new("ShaderNodeMapping")
        uvmap.location = (-400, 0)
        img = nodes.new("ShaderNodeTexImage")
        img.location = (-150, 50)
        try:
            img.image = bpy.data.images.load(moon_path, check_existing=True)
        except Exception:
            pass
        links.new(coord.outputs["UV"],     uvmap.inputs["Vector"])
        links.new(uvmap.outputs["Vector"], img.inputs["Vector"])
        links.new(img.outputs["Color"],    bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (0.5, 0.5, 0.48, 1.0)
        print("WARNING: moon.jpg not found, using fallback color")

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

# ============================================================
# SECTION 4 – BUILD SCENE
# ============================================================
def construct_scene():
    EARTH_RADIUS = 5.0
    MOON_RADIUS  = EARTH_RADIUS * 0.27
    MOON_ORBIT   = EARTH_RADIUS * 6.0

    # Earth
    earth = spawn_sphere("Earth", EARTH_RADIUS)
    earth.rotation_euler.x = math.radians(23.4)
    apply_shader(earth, create_earth_material())

    # Atmosphere glow shell
    atmo = spawn_sphere("Earth_Atmosphere", EARTH_RADIUS * 1.06)
    atmo.parent = earth
    apply_shader(atmo, create_atmosphere_shader())

    # Sun light (key light from the side)
    bpy.ops.object.light_add(type='SUN', location=(100, -50, 80))
    sun_light = bpy.context.active_object
    sun_light.name = "SunLight"
    sun_light.data.energy = 8.0
    sun_light.data.color  = (1.0, 0.97, 0.88)
    sun_light.rotation_euler = (math.radians(30), math.radians(0), math.radians(-45))
    sun_light.data.use_shadow = True
    sun_light.data.shadow_cascade_count = 4
    sun_light.data.shadow_cascade_max_distance = 200.0

    # Dim fill light from opposite side
    bpy.ops.object.light_add(type='SUN', location=(-100, 50, -30))
    fill_light = bpy.context.active_object
    fill_light.name = "FillLight"
    fill_light.data.energy = 0.05
    fill_light.data.color  = (0.4, 0.5, 0.8)
    fill_light.rotation_euler = (math.radians(-40), math.radians(-20), math.radians(150))

    # Moon pivot + moon
    moon_pivot = spawn_anchor("Moon_Pivot")
    moon = spawn_sphere("Moon", MOON_RADIUS, location=(MOON_ORBIT, 0, 0))
    moon.parent = moon_pivot
    apply_shader(moon, create_moon_material())

    # Satellite
    sat_pivot = spawn_anchor("Satellite_Pivot")
    sat_pivot.parent = earth

    sat_orbit_r = EARTH_RADIUS * 1.8
    body_size   = EARTH_RADIUS * 0.04

    sat_blend_path = r"C:\solar\satalite.blend"
    loaded_objects = []
    try:
        with bpy.data.libraries.load(sat_blend_path, link=False) as (data_from, data_to):
            data_to.objects = list(data_from.objects)
            print(f"  -> Found in satalite.blend: {data_from.objects}")
# Remap satellite textures to C:\solar\textures
        sat_texture_dir = r"C:\solar\textures"
        for img in bpy.data.images:
            if not os.path.exists(bpy.path.abspath(img.filepath)):
                filename = os.path.basename(bpy.path.abspath(img.filepath))
                new_path = os.path.join(sat_texture_dir, filename)
                if os.path.exists(new_path):
                    img.filepath = new_path
                    img.reload()
                    print(f"  -> Remapped: {filename}")
                else:
                    print(f"  -> WARNING: Missing texture: {filename}")
        for obj in data_to.objects:
            if obj is not None:
                bpy.context.collection.objects.link(obj)
                loaded_objects.append(obj)

        if loaded_objects:
            sat_root = spawn_anchor("Satellite_Root")
            sat_root.parent   = sat_pivot
            sat_root.location = (sat_orbit_r, 0, 0)
            sat_root.scale    = (body_size, body_size, body_size)

            for obj in loaded_objects:
                obj.parent = sat_root
                obj.matrix_parent_inverse = sat_root.matrix_world.inverted()

            print(f"  -> Satellite loaded: {len(loaded_objects)} piece(s)")

    except Exception as e:
        print(f"WARNING: Could not load satalite.blend — {e}")

    return earth, moon_pivot, moon, sat_pivot, EARTH_RADIUS, MOON_ORBIT

# ============================================================
# SECTION 5 – ANIMATION
# ============================================================
def keyframe_scene(earth, moon_pivot, moon, sat_pivot):
    scene = bpy.context.scene
    scene.frame_set(1)

    # Earth self rotation
    earth.rotation_euler = (math.radians(23.4), 0, 0)
    earth.keyframe_insert(data_path="rotation_euler", frame=1)
    earth.rotation_euler = (math.radians(23.4), 0, math.radians(360 * 3))
    earth.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)
    for fcurve in earth.animation_data.action.fcurves:
        for kf in fcurve.keyframe_points:
            kf.interpolation = 'LINEAR'

    # Moon orbit around Earth
    moon_pivot.rotation_euler = (0, 0, 0)
    moon_pivot.keyframe_insert(data_path="rotation_euler", frame=1)
    moon_pivot.rotation_euler.z = math.radians(360 * 2)
    moon_pivot.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)
    for fcurve in moon_pivot.animation_data.action.fcurves:
        for kf in fcurve.keyframe_points:
            kf.interpolation = 'LINEAR'

    # Satellite fast inclined orbit
    sat_pivot.rotation_euler = (math.radians(28), 0, 0)
    sat_pivot.keyframe_insert(data_path="rotation_euler", frame=1)
    sat_pivot.rotation_euler.z = math.radians(360 * 1)    # 2 full orbits in 10 sec
    sat_pivot.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)
    for fcurve in sat_pivot.animation_data.action.fcurves:
        for kf in fcurve.keyframe_points:
            kf.interpolation = 'LINEAR'

# ============================================================
# SECTION 6 – CAMERA
# ============================================================
def setup_orbit_camera(earth_radius):
    bpy.ops.object.camera_add(location=(0, -28, 10))
    cam = bpy.context.active_object
    cam.name = "MainCamera"
    bpy.context.scene.camera = cam

    # Track to Earth always
    track = cam.constraints.new(type='TRACK_TO')
    track.target     = bpy.data.objects["Earth"]
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis    = 'UP_Y'

    cam.data.lens        = 50
    cam.data.clip_start  = 0.01
    cam.data.clip_end    = 1000
    cam.data.dof.use_dof = False

    return cam

# ============================================================
# MAIN
# ============================================================
def main():
    print("=== Earth Scene Generator ===")

    print("[1/4] Initialising environment...")
    initialise_environment()

    print("[2/4] Constructing scene...")
    earth, moon_pivot, moon, sat_pivot, earth_radius, moon_orbit = construct_scene()

    print("[3/4] Keyframing animation...")
    keyframe_scene(earth, moon_pivot, moon, sat_pivot)

    print("[4/4] Setting up camera...")
    setup_orbit_camera(earth_radius)

    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    print("=== Done! Press SPACE to preview or Ctrl+F12 to render. ===")

main()