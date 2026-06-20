import bpy
import math
import os
import random
# ============================================================
# CONFIGURATION
# ============================================================
TEXTURE_DIR = r"C:\solar"
RENDER_ENGINE = "CYCLES"   # or "BLENDER_EEVEE"
RESOLUTION_X = 1920
RESOLUTION_Y = 1080
FRAME_START = 1
FRAME_END = 1500
USE_BLOOM = True
USE_MOTION_BLUR = False

def tex(filename):
    """Return full path to a texture file."""
    return os.path.join(TEXTURE_DIR, filename)

# ============================================================
# SECTION 1 – SCENE SETUP
# ============================================================
def setup_scene():
    # Clear everything robustly
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat, do_unlink=True)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)

    scene = bpy.context.scene
    scene.frame_start = FRAME_START
    scene.frame_end   = FRAME_END

    # Render engine
    scene.render.engine = RENDER_ENGINE
    scene.render.resolution_x = RESOLUTION_X
    scene.render.resolution_y = RESOLUTION_Y
    scene.render.film_transparent = False

    if RENDER_ENGINE == "BLENDER_EEVEE":
        eevee = scene.eevee
        eevee.use_bloom = USE_BLOOM
        eevee.bloom_intensity = 0.5    # Massive bloom for glowing sun and nebula
        eevee.bloom_threshold = 0.8    # Allow softer elements to glow
        eevee.bloom_radius = 6.0       # Spread the glow out wider
        eevee.use_ssr = True
        eevee.use_soft_shadows = True
        eevee.shadow_cube_size = '1024'
        eevee.taa_render_samples = 64
        if USE_MOTION_BLUR:
            eevee.use_motion_blur = True
    else:
        cycles = scene.cycles
        cycles.samples = 128
        if USE_MOTION_BLUR:
            scene.render.use_motion_blur = True
        
        # In Cycles, Bloom must be done via the Compositor using a Glare node
        if USE_BLOOM:
            scene.use_nodes = True
            tree = scene.node_tree
            tree.nodes.clear()
            
            rlayers = tree.nodes.new(type='CompositorNodeRLayers')
            rlayers.location = (0, 0)
            
            glare = tree.nodes.new(type='CompositorNodeGlare')
            glare.location = (300, 0)
            glare.glare_type = 'FOG_GLOW'
            glare.quality = 'HIGH'
            glare.threshold = 0.8
            glare.size = 9  # Max size for glow spread
            
            comp = tree.nodes.new(type='CompositorNodeComposite')
            comp.location = (600, 0)
            
            tree.links.new(rlayers.outputs['Image'], glare.inputs['Image'])
            tree.links.new(glare.outputs['Image'], comp.inputs['Image'])

    # World – starfield
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    wnt = world.node_tree
    wnt.nodes.clear()

    bg_node  = wnt.nodes.new("ShaderNodeBackground")
    out_node = wnt.nodes.new("ShaderNodeOutputWorld")
    out_node.location = (300, 0)

    # 1. Procedural Cosmic Nebula
    noise = wnt.nodes.new("ShaderNodeTexNoise")
    noise.location = (-600, 200)
    noise.inputs["Scale"].default_value = 1.2
    noise.inputs["Detail"].default_value = 15.0
    noise.inputs["Roughness"].default_value = 0.55
    
    ramp = wnt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-400, 200)
    ramp.color_ramp.elements[0].position = 0.4
    ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp.color_ramp.elements[1].position = 0.6
    ramp.color_ramp.elements[1].color = (0.05, 0.005, 0.01, 1.0) # Subtle lowkey purple space dust
    ramp.color_ramp.elements.new(0.85)
    ramp.color_ramp.elements[2].color = (0.15, 0.05, 0.01, 1.0) # Lowkey dark orange dust
    
    wnt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    
    # 2. Base Stars
    stars_path = tex("stars.jpg")
    mix_node = wnt.nodes.new("ShaderNodeMixRGB")
    mix_node.blend_type = 'ADD'
    mix_node.inputs[0].default_value = 1.0
    mix_node.location = (-150, 0)

    if os.path.exists(stars_path):
        tex_coord = wnt.nodes.new("ShaderNodeTexCoord")
        mapping    = wnt.nodes.new("ShaderNodeMapping")
        img_node   = wnt.nodes.new("ShaderNodeTexEnvironment")
        tex_coord.location  = (-800, -200)
        mapping.location    = (-600, -200)
        img_node.location   = (-400, -200)
        try:
            img_node.image = bpy.data.images.load(stars_path)
        except Exception:
            pass
        wnt.links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])
        wnt.links.new(mapping.outputs["Vector"],      img_node.inputs["Vector"])
        wnt.links.new(img_node.outputs["Color"], mix_node.inputs[1])
    else:
        mix_node.inputs[1].default_value = (0.0, 0.0, 0.0, 1.0)

    wnt.links.new(ramp.outputs["Color"], mix_node.inputs[2])
    wnt.links.new(mix_node.outputs["Color"], bg_node.inputs["Color"])
    bg_node.inputs["Strength"].default_value = 0.5

    wnt.links.new(bg_node.outputs["Background"], out_node.inputs["Surface"])
    return scene

# ============================================================
# SECTION 2 – MATERIAL HELPERS
# ============================================================
def make_material_principled(name, texture_path, emission_color=None,
                              emission_strength=0.0, roughness=0.8,
                              metallic=0.0, alpha=1.0, blend_mode=None, bump_path=None):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out   = nodes.new("ShaderNodeOutputMaterial")
    out.location   = (600, 0)
    bsdf  = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location  = (200, 0)
    bsdf.inputs["Roughness"].default_value  = roughness
    bsdf.inputs["Metallic"].default_value   = metallic

    if texture_path and os.path.exists(texture_path):
        coord = nodes.new("ShaderNodeTexCoord")
        coord.location = (-600, 0)
        uvmap = nodes.new("ShaderNodeMapping")
        uvmap.location  = (-400, 0)
        img   = nodes.new("ShaderNodeTexImage")
        img.location    = (-150, 50)
        try:
            img.image = bpy.data.images.load(texture_path, check_existing=True)
        except Exception:
            pass
        links.new(coord.outputs["UV"],     uvmap.inputs["Vector"])
        links.new(uvmap.outputs["Vector"], img.inputs["Vector"])
        links.new(img.outputs["Color"],    bsdf.inputs["Base Color"])

        if alpha < 1.0:
            links.new(img.outputs["Alpha"], bsdf.inputs["Alpha"])
            mat.blend_method  = blend_mode or "BLEND"
            mat.shadow_method = "CLIP"

    if bump_path and os.path.exists(bump_path):
        if not ("coord" in locals() and "uvmap" in locals()):
            coord = nodes.new("ShaderNodeTexCoord")
            coord.location = (-600, 0)
            uvmap = nodes.new("ShaderNodeMapping")
            uvmap.location  = (-400, 0)
        bump_img = nodes.new("ShaderNodeTexImage")
        bump_img.location = (-150, -250)
        bump_node = nodes.new("ShaderNodeBump")
        bump_node.location = (50, -250)
        try:
            bump_img.image = bpy.data.images.load(bump_path, check_existing=True)
            bump_img.image.colorspace_settings.name = 'Non-Color'
        except Exception:
            pass
        links.new(uvmap.outputs["Vector"], bump_img.inputs["Vector"])
        links.new(bump_img.outputs["Color"], bump_node.inputs["Height"])
        links.new(bump_node.outputs["Normal"], bsdf.inputs["Normal"])
        bump_node.inputs["Distance"].default_value = 0.2

    if emission_color and emission_strength > 0:
        bsdf.inputs["Emission Color"].default_value    = (*emission_color, 1)
        bsdf.inputs["Emission Strength"].default_value = emission_strength

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_sun_material():
    mat   = bpy.data.materials.new(name="Sun_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out   = nodes.new("ShaderNodeOutputMaterial")
    out.location   = (600, 0)
    emit  = nodes.new("ShaderNodeEmission")
    emit.location  = (200, 0)
    emit.inputs["Strength"].default_value = 15.0 
    emit.inputs["Color"].default_value    = (1.0, 0.35, 0.02, 1.0) 

    tex_path = tex("sun_bg.jpg")
    if os.path.exists(tex_path):
        coord = nodes.new("ShaderNodeTexCoord")
        coord.location = (-600, 0)
        uvmap = nodes.new("ShaderNodeMapping")
        uvmap.location  = (-400, 0)
        img   = nodes.new("ShaderNodeTexImage")
        img.location    = (-150, 0)
        try:
            img.image = bpy.data.images.load(tex_path, check_existing=True)
        except Exception:
            pass
        mix = nodes.new("ShaderNodeMixRGB")
        mix.location = (-10, 100)
        mix.blend_type = 'MULTIPLY'
        mix.inputs["Fac"].default_value = 0.6
        mix.inputs["Color2"].default_value = (1.0, 0.75, 0.2, 1.0)
        links.new(coord.outputs["UV"],     uvmap.inputs["Vector"])
        links.new(uvmap.outputs["Vector"], img.inputs["Vector"])
        links.new(img.outputs["Color"],    mix.inputs["Color1"])
        links.new(mix.outputs["Color"],    emit.inputs["Color"])

    links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat

def make_earth_atmosphere():
    mat   = bpy.data.materials.new(name="Earth_Atmo")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out   = nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    trans = nodes.new("ShaderNodeBsdfTransparent")
    trans.location = (-100, 100)
    emit  = nodes.new("ShaderNodeEmission")
    emit.location  = (-100, -50)
    emit.inputs["Color"].default_value    = (0.2, 0.5, 1.0, 1.0)
    emit.inputs["Strength"].default_value = 0.3

    fac = nodes.new("ShaderNodeLayerWeight")
    fac.location = (-300, 0)
    fac.inputs["Blend"].default_value = 0.45
    mix = nodes.new("ShaderNodeMixShader")
    mix.location = (400, 0)

    links.new(fac.outputs["Facing"],    mix.inputs["Fac"])
    links.new(trans.outputs["BSDF"],    mix.inputs[1])
    links.new(emit.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"],    out.inputs["Surface"])

    mat.blend_method  = "BLEND"
    mat.shadow_method = "NONE"
    return mat

def make_ring_material(ring_texture=None):
    mat   = bpy.data.materials.new(name="Ring_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out  = nodes.new("ShaderNodeOutputMaterial")
    out.location  = (600, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (200, 0)
    bsdf.inputs["Roughness"].default_value = 0.9
    bsdf.inputs["Alpha"].default_value     = 0.55

    mat.blend_method  = "BLEND"
    mat.shadow_method = "NONE"

    if ring_texture and os.path.exists(ring_texture):
        coord = nodes.new("ShaderNodeTexCoord")
        coord.location = (-600, 0)
        img   = nodes.new("ShaderNodeTexImage")
        img.location    = (-150, 50)
        bw    = nodes.new("ShaderNodeRGBToBW")
        bw.location     = (50, -50)
        try:
            img.image = bpy.data.images.load(ring_texture, check_existing=True)
        except Exception:
            pass
        links.new(coord.outputs["UV"],   img.inputs["Vector"])
        links.new(img.outputs["Color"],  bsdf.inputs["Base Color"])
        links.new(img.outputs["Color"],  bw.inputs["Color"])
        links.new(bw.outputs["Val"],     bsdf.inputs["Alpha"])
    else:
        bsdf.inputs["Base Color"].default_value = (0.85, 0.78, 0.65, 1.0)

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

# ============================================================
# SECTION 3 – OBJECT HELPERS
# ============================================================
def add_uv_sphere(name, radius, location=(0, 0, 0), segments=64, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius, location=location,
        segments=segments, ring_count=rings)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    return obj

def add_flat_ring(name, radius, location=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=128, radius=radius, depth=0.001,
        location=location, rotation=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    return obj

def create_empty(name, location=(0, 0, 0)):
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
    obj = bpy.context.active_object
    obj.name = name
    return obj

def add_point_light(name, location, energy, radius=0.5, color=(1, 0.9, 0.7)):
    bpy.ops.object.light_add(type='POINT', location=location)
    light = bpy.context.active_object
    light.name = name
    light.data.energy       = energy
    light.data.color        = color
    light.data.shadow_soft_size = radius
    return light

def assign_material(obj, mat):
    if obj.data.materials:
        obj.data.materials = mat
    else:
        obj.data.materials.append(mat)

# ============================================================
# SECTION 4 – PLANET DEFINITIONS
# ============================================================
PLANET_DATA = [
    ("Mercury", 0.11,  12,     88,   58,  0.03,  (0.6, 0.5, 0.45, 1), "mercury_bg.jpg"),
    ("Venus",   0.28,  18,    225,  243,  177.4, (0.9, 0.8, 0.5,  1), "venus_bg.jpg"),
    ("Earth",   0.30,  25,    365,    1,   23.4, (0.2, 0.5, 0.9,  1), "earth_bg.jpg"),
    ("Mars",    0.16,  34,    687,   1.03, 25.2, (0.8, 0.4, 0.2,  1), "mars_bg.jpg"),
    ("Jupiter", 3.36,  55,   4333,   0.41, 3.1,  (0.8, 0.7, 0.55, 1), "jupiter_bg.jpg"),
    ("Saturn",  2.83,  80,  10759,   0.45, 26.7, (0.9, 0.85, 0.6, 1), "saturn_bg.jpg"),
    ("Uranus",  1.20, 105,  30688,   0.72, 97.8, (0.5, 0.85, 0.9, 1), "uranus_bg.jpg"),
    ("Neptune", 1.16, 125,  60182,   0.67, 28.3, (0.2, 0.4, 0.9,  1), "neptune_bg.jpg"),
    ("Pluto",   0.05, 150,  90560,   6.39, 122.5, (0.6, 0.5, 0.4,  1), "pluto_bg.jpg"),
]

SUN_RADIUS = 8.0
SPEED_SCALE = 1.5

# ============================================================
# SECTION 5 – BUILD SOLAR SYSTEM
# ============================================================
def build_solar_system():
    planets = {}

    # ----- SUN -----
    sun_obj = add_uv_sphere("Sun", SUN_RADIUS)
    sun_mat = make_sun_material()
    assign_material(sun_obj, sun_mat)
    sun_obj.visible_shadow = False

    sun_light = add_point_light("SunLight", (0, 0, 0), energy=150000, radius=SUN_RADIUS, color=(1.0, 0.95, 0.9))
    sun_light.data.use_shadow = False
    sun_light.data.use_custom_distance = True
    sun_light.data.cutoff_distance     = 600.0

    bpy.ops.object.light_add(type='SUN', rotation=(math.radians(45), math.radians(45), 0))
    fill = bpy.context.active_object
    fill.name = "AmbientFill"
    fill.data.energy = 0.01  
    fill.data.color = (0.3, 0.35, 0.5)
    fill.data.use_shadow = False
    
    bpy.ops.object.light_add(type='SUN', rotation=(math.radians(-45), math.radians(-135), 0))
    fill2 = bpy.context.active_object
    fill2.name = "AmbientFill2"
    fill2.data.energy = 0.03
    fill2.data.color = (0.7, 0.8, 1.0)
    fill2.data.use_shadow = False

    # ----- PLANETS -----
    for (pname, prad, orbit_r, orb_period, rot_period, axial_tilt, base_color, tex_file) in PLANET_DATA:
        pivot = create_empty(f"{pname}_Pivot")
        planet = add_uv_sphere(pname, prad, location=(orbit_r, 0, 0))
        planet.parent = pivot
        planet.rotation_euler.x = math.radians(axial_tilt)

        tpath = tex(tex_file)
        bpath = tex(f"{pname.lower()}_bump_bg.jpg") if pname == "Pluto" else None
        mat = make_material_principled(
            f"{pname}_Mat", tpath,
            roughness=0.85, metallic=0.0,
            bump_path=bpath)
        if not os.path.exists(tpath):
            mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = base_color
        assign_material(planet, mat)

        planets[pname] = {"pivot": pivot, "planet": planet, "orbit_r": orbit_r, "radius": prad}

    # ----- SATURN RINGS -----
    saturn_info = planets["Saturn"]
    sat_obj     = saturn_info["planet"]
    sat_r       = saturn_info["radius"]

    ring_tex_path = tex("saturn_ring_bg.jpg")
    ring = add_flat_ring("Saturn_Ring", radius=sat_r * 2.2, location=(0, 0, 0))
    ring.parent = sat_obj
    ring_mat = make_ring_material(ring_tex_path if os.path.exists(ring_tex_path) else None)
    assign_material(ring, ring_mat)

    # ----- MOON -----
    earth_info = planets["Earth"]
    earth_obj  = earth_info["planet"]
    earth_r    = earth_info["radius"]
    
    moon_radius = earth_r * 0.27
    moon_orbit_r = earth_r * 3.0
    moon_obj = add_uv_sphere("Moon", moon_radius, location=(moon_orbit_r, 0, 0))
    moon_obj.parent = earth_obj
    
    moon_tex_path = tex("moon_bg.jpg")
    moon_mat = make_material_principled("Moon_Mat", moon_tex_path, roughness=0.9, metallic=0.0)
    assign_material(moon_obj, moon_mat)

    # ----- JUPITER MOONS -----
    jup_info = planets["Jupiter"]
    jup_obj  = jup_info["planet"]
    jup_r    = jup_info["radius"]
    
    jup_moons = [
        ("Io", jup_r * 0.025, jup_r * 1.5, "io_bg.jpg"),
        ("Europa", jup_r * 0.02, jup_r * 2.0, "europa_bg.jpg"),
        ("Ganymede", jup_r * 0.035, jup_r * 2.6, "ganymede_bg.jpg"),
        ("Callisto", jup_r * 0.032, jup_r * 3.3, "callisto_bg.jpg")
    ]
    
    for i, (m_name, m_rad, m_dist, m_tex) in enumerate(jup_moons):
        angle = i * (math.pi / 2)
        lx = m_dist * math.cos(angle)
        ly = m_dist * math.sin(angle)
        m_obj = add_uv_sphere(m_name, m_rad, location=(lx, ly, 0))
        m_obj.parent = jup_obj
        
        m_tex_path = tex(m_tex)
        m_mat = make_material_principled(f"{m_name}_Mat", m_tex_path, roughness=0.9, metallic=0.0)
        assign_material(m_obj, m_mat)

    return planets

# ============================================================
# SECTION 5b – ORBIT LINES
# ============================================================
def add_orbit_lines():
    """Draw a faint emissive circle at each planet's orbital radius."""

    mat = bpy.data.materials.new("Orbit_Line_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out  = nodes.new("ShaderNodeOutputMaterial"); out.location  = (400, 0)
    emit = nodes.new("ShaderNodeEmission");        emit.location = (100, 0)
    emit.inputs["Color"].default_value    = (0.4, 0.6, 1.0, 1.0)
    emit.inputs["Strength"].default_value = 0.7  # Below bloom threshold to prevent bright glowing
    
    # We add a Mix Shader to animate opacity
    trans = nodes.new("ShaderNodeBsdfTransparent"); trans.location = (100, 100)
    mix = nodes.new("ShaderNodeMixShader"); mix.location = (250, 50)
    mix.name = "OrbitFadeMix"
    mix.inputs[0].default_value = 1.0 # 0 = transparent, 1 = emission
    
    links.new(trans.outputs["BSDF"], mix.inputs[1])
    links.new(emit.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])

    mat.blend_method  = "BLEND"
    mat.shadow_method = "NONE"

    ORBIT_SEGMENTS = 256

    for (pname, prad, orbit_r, *_rest) in PLANET_DATA:
        curve_data = bpy.data.curves.new(name=f"Orbit_{pname}", type='CURVE')
        curve_data.dimensions          = '3D'
        curve_data.resolution_u        = 12
        curve_data.render_resolution_u = 24
        curve_data.bevel_depth         = 0.014  # Physically thicker so they don't vanish from afar without bloom
        curve_data.use_fill_caps       = True

        spline = curve_data.splines.new('POLY')
        spline.use_cyclic_u = True
        spline.points.add(ORBIT_SEGMENTS - 1)

        for i, pt in enumerate(spline.points):
            angle = (2 * math.pi * i) / ORBIT_SEGMENTS
            pt.co = (
                orbit_r * math.cos(angle),
                orbit_r * math.sin(angle),
                0.0,
                1.0
            )

        orbit_obj = bpy.data.objects.new(f"Orbit_{pname}", curve_data)
        bpy.context.collection.objects.link(orbit_obj)
        orbit_obj.data.materials.append(mat)

# ============================================================
# SECTION 5c – ASTEROID BELT
# ============================================================
def add_asteroid_belt():
    belt_pivot = create_empty("AsteroidBelt_Pivot")

    ast_mat = bpy.data.materials.new("Asteroid_Mat")
    ast_mat.use_nodes = True
    nodes = ast_mat.node_tree.nodes
    links = ast_mat.node_tree.links
    nodes.clear()

    out  = nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (200, 0)
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Metallic"].default_value  = 0.0

    ast_tex_path = tex("asteroid.jpg")
    if os.path.exists(ast_tex_path):
        coord = nodes.new("ShaderNodeTexCoord")
        coord.location = (-600, 0)
        uvmap = nodes.new("ShaderNodeMapping")
        uvmap.location = (-400, 0)
        img = nodes.new("ShaderNodeTexImage")
        img.location = (-150, 50)
        try:
            img.image = bpy.data.images.load(ast_tex_path, check_existing=True)
        except Exception:
            pass
        links.new(coord.outputs["UV"], uvmap.inputs["Vector"])
        links.new(uvmap.outputs["Vector"], img.inputs["Vector"])
        links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (0.32, 0.29, 0.26, 1.0)
        print("  -> WARNING: asteroid.jpg not found, using fallback color")

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    inner_r = 40.0
    outer_r = 52.0
    count = 400

    base_meshes = []
    for i in range(5):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.7)  # was 0.35
        base_obj = bpy.context.active_object
        base_obj.scale = (
            random.uniform(0.6, 1.4),
            random.uniform(0.6, 1.4),
            random.uniform(0.6, 1.4),
        )
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bpy.ops.object.shade_smooth()
        assign_material(base_obj, ast_mat)
        base_meshes.append(base_obj.data)
        bpy.data.objects.remove(base_obj, do_unlink=True)

    for i in range(count):
        angle  = random.uniform(0, 2 * math.pi)
        radius = random.uniform(inner_r, outer_r)
        height = random.uniform(-3.0, 3.0)   # was -1.5..1.5 — thicker belt

        mesh_data = random.choice(base_meshes)
        ast = bpy.data.objects.new(f"Asteroid_{i:04d}", mesh_data)
        bpy.context.collection.objects.link(ast)

        ast.location = (radius * math.cos(angle), radius * math.sin(angle), height)
        s = random.uniform(0.5, 2.0)   # was 0.4..1.6
        ast.scale = (s, s, s)
        ast.rotation_euler = (
            random.uniform(0, math.pi * 2),
            random.uniform(0, math.pi * 2),
            random.uniform(0, math.pi * 2),
        )
        ast.parent = belt_pivot

    belt_pivot.rotation_euler = (0, 0, 0)
    belt_pivot.keyframe_insert(data_path="rotation_euler", frame=1)
    belt_pivot.rotation_euler.z = math.radians(15)
    belt_pivot.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)

    if belt_pivot.animation_data and belt_pivot.animation_data.action:
        for fcurve in belt_pivot.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'LINEAR'

    print(f"  -> Asteroid belt: {count} asteroids placed between r={inner_r} and r={outer_r}")
    return belt_pivot

# ============================================================
# SECTION 5d – EARTH SATELLITE
# ============================================================
def add_earth_satellite(planets):
    earth_info = planets["Earth"]
    earth_obj  = earth_info["planet"]
    earth_r    = earth_info["radius"]

    sat_pivot = create_empty("Satellite_Pivot")
    sat_pivot.parent = earth_obj

    sat_orbit_r = earth_r * 2.5
    body_size   = earth_r * 0.05

    # ── Load satellite from .blend file ──
    sat_blend_path = r"C:\solar\satalite.blend"
    loaded_objects = []
    try:
        with bpy.data.libraries.load(sat_blend_path, link=False) as (data_from, data_to):
            data_to.objects = list(data_from.objects)
            print(f"  -> Found objects in satalite.blend: {data_from.objects}")

        for obj in data_to.objects:
            if obj is not None:
                bpy.context.collection.objects.link(obj)
                loaded_objects.append(obj)

        if loaded_objects:
            # Create a root empty to group all satellite pieces
            sat_root = create_empty("Satellite_Root")
            sat_root.parent = sat_pivot
            sat_root.location = (sat_orbit_r, 0, 0)
            sat_root.scale = (body_size, body_size, body_size)

            # Parent all pieces to the root empty
            for obj in loaded_objects:
                obj.parent = sat_root
                # Keep original offsets so the model stays intact
                obj.matrix_parent_inverse = sat_root.matrix_world.inverted()

            print(f"  -> Satellite loaded: {len(loaded_objects)} piece(s)")

    except Exception as e:
        print(f"WARNING: Could not load satalite.blend — {e}")

    # Fast, inclined orbit around Earth
    deg_per_frame = 6.0
    sat_pivot.rotation_euler = (math.radians(20), 0, 0)
    sat_pivot.keyframe_insert(data_path="rotation_euler", frame=1)
    sat_pivot.rotation_euler.z = math.radians(deg_per_frame * FRAME_END)
    sat_pivot.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)

    if sat_pivot.animation_data and sat_pivot.animation_data.action:
        for fcurve in sat_pivot.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'LINEAR'

    return sat_pivot
# ============================================================
# SECTION 6 – ANIMATION
# ============================================================
def animate_solar_system(planets):
    scene = bpy.context.scene
    scene.frame_set(1)

    for (pname, prad, orbit_r, orb_period, rot_period, axial_tilt, base_color, tex_file) in PLANET_DATA:
        pivot  = planets[pname]["pivot"]
        planet = planets[pname]["planet"]

        deg_per_frame = 360.0 / (orb_period / SPEED_SCALE)
        pivot.rotation_euler = (0, 0, 0)
        pivot.keyframe_insert(data_path="rotation_euler", frame=1)
        total_degrees = deg_per_frame * FRAME_END
        pivot.rotation_euler.z = math.radians(total_degrees)
        pivot.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)

        for fcurve in pivot.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'LINEAR'

        rot_deg_per_frame = 0.5
        planet.rotation_euler = (math.radians(axial_tilt), 0, 0)
        planet.keyframe_insert(data_path="rotation_euler", frame=1)
        planet.rotation_euler = (math.radians(axial_tilt), 0, math.radians(rot_deg_per_frame * FRAME_END))
        planet.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)

        for fcurve in planet.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'LINEAR'

    sun = bpy.data.objects.get("Sun")
    if sun:
        sun.rotation_euler.z = 0
        sun.keyframe_insert(data_path="rotation_euler", frame=1)
        sun.rotation_euler.z = math.radians(360 * 2)
        sun.keyframe_insert(data_path="rotation_euler", frame=FRAME_END)
        for fcurve in sun.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'LINEAR'

# ============================================================
# SECTION 7 – PLANET LABELS
# ============================================================
def add_planet_labels(planets, cam_obj, blocks):
    label_objects = {}
    for (pname, prad, orbit_r, orb_period, rot_period, axial_tilt, base_color, tex_file) in PLANET_DATA:
        planet = planets[pname]["planet"]
        pivot = planets[pname]["pivot"]
        
        label_prad = prad * 2.5 if pname == "Saturn" else prad
        
        billboard_rig = create_empty(f"LabelRig_{pname}", location=(orbit_r, 0, 0))
        billboard_rig.parent = pivot
        
        c_track = billboard_rig.constraints.new(type='TRACK_TO')
        c_track.target = cam_obj
        c_track.track_axis = 'TRACK_Z'
        c_track.up_axis = 'UP_Y'

        bpy.ops.object.text_add(location=(0, 0, 0))
        txt_obj = bpy.context.active_object
        txt_obj.name = f"Label_{pname}"
        txt_obj.parent = billboard_rig
        txt_obj.data.body = pname.upper()  
        txt_obj.data.size = label_prad * 0.35
        txt_obj.data.align_x = 'LEFT'
        txt_obj.data.space_character = 1.4  
        txt_obj.location = (label_prad * 1.3, label_prad * 0.2, 0)
        
        font_path = "C:\\Windows\\Fonts\\orbitron.ttf"
        if not os.path.exists(font_path):
            font_path = "C:\\Windows\\Fonts\\bahnschrift.ttf"
        if not os.path.exists(font_path):
            font_path = "C:\\Windows\\Fonts\\trebucbd.ttf"
            
        if os.path.exists(font_path):
            try:
                fnt = bpy.data.fonts.load(font_path)
                txt_obj.data.font = fnt
            except Exception:
                pass

        lmat = bpy.data.materials.new(f"Label_{pname}_Mat")
        lmat.use_nodes = True
        lmat.blend_method = 'BLEND'
        lmat.show_transparent_back = False
        ln = lmat.node_tree.nodes
        ll = lmat.node_tree.links
        ln.clear()

        lout = ln.new("ShaderNodeOutputMaterial")
        lout.location = (400, 0)

        lemit = ln.new("ShaderNodeEmission")
        lemit.location = (0, 0)
        lemit.inputs["Color"].default_value = (0.85, 0.92, 1.0, 1.0)
        lemit.inputs["Strength"].default_value = 3.0
        ltrans = ln.new("ShaderNodeBsdfTransparent")
        ltrans.location = (0, 100)

        lmix = ln.new("ShaderNodeMixShader")
        lmix.location = (200, 50)
        lmix.inputs[0].default_value = 0.0  

        ll.new(ltrans.outputs["BSDF"], lmix.inputs[1])
        ll.new(lemit.outputs["Emission"], lmix.inputs[2])
        ll.new(lmix.outputs["Shader"], lout.inputs["Surface"])

        txt_obj.data.materials.append(lmat)
        label_objects[pname] = {"obj": txt_obj, "mix_node": lmix}

    for idx, (pname, b_start, b_end) in enumerate(blocks):
        trans_end = b_start if idx == 0 else b_start + 40
        showcase_start = trans_end
        showcase_end = b_end

        fade_in_start = showcase_start
        fade_in_end = showcase_start + 20
        fade_out_start = showcase_end - 20
        fade_out_end = showcase_end

        mix_node = label_objects[pname]["mix_node"]

        mix_node.inputs[0].default_value = 0.0
        mix_node.inputs[0].keyframe_insert(data_path="default_value", frame=1)
        mix_node.inputs[0].keyframe_insert(data_path="default_value", frame=fade_in_start)

        mix_node.inputs[0].default_value = 1.0
        mix_node.inputs[0].keyframe_insert(data_path="default_value", frame=fade_in_end)
        mix_node.inputs[0].keyframe_insert(data_path="default_value", frame=fade_out_start)

        mix_node.inputs[0].default_value = 0.0
        mix_node.inputs[0].keyframe_insert(data_path="default_value", frame=fade_out_end)

        if mix_node.id_data.animation_data and mix_node.id_data.animation_data.action:
            for fcurve in mix_node.id_data.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'BEZIER'

    return label_objects
# ============================================================
# SECTION 8 – CAMERA SYSTEM
# ============================================================
def build_camera_system(planets):
    cam_target = create_empty("CameraTarget")
    cam_pivot  = create_empty("CameraPivot")

    bpy.ops.object.camera_add(location=(0, -15, 0))
    cam_obj = bpy.context.active_object
    cam_obj.name = "MainCamera"
    bpy.context.scene.camera = cam_obj
    cam_obj.parent = cam_pivot

    track = cam_obj.constraints.new(type='TRACK_TO')
    track.target     = cam_target
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis    = 'UP_Y'

    cam_data = cam_obj.data
    cam_data.lens       = 28          # Wide angle – NASA probe feel
    cam_data.clip_start = 0.01
    cam_data.clip_end   = 3000
    cam_data.dof.use_dof = False
    cam_obj.rotation_euler.y = math.radians(2)

    sun_obj = bpy.data.objects.get("Sun")

    c_sun_pivot        = cam_pivot.constraints.new(type='COPY_LOCATION')
    c_sun_pivot.target = sun_obj
    c_sun_pivot.name   = "Copy_Sun"

    c_sun_tgt        = cam_target.constraints.new(type='COPY_LOCATION')
    c_sun_tgt.target = sun_obj
    c_sun_tgt.name   = "Copy_Sun"

    targets = ["Sun"] + [p[0] for p in PLANET_DATA]
    for t_name in targets:
        target_obj = bpy.data.objects.get("Sun") if t_name == "Sun" else planets[t_name]["planet"]

        cp           = cam_pivot.constraints.new(type='COPY_LOCATION')
        cp.target    = target_obj
        cp.name      = f"Copy_{t_name}"
        cp.influence = 0.0

        ct           = cam_target.constraints.new(type='COPY_LOCATION')
        ct.target    = target_obj
        ct.name      = f"Copy_{t_name}"
        ct.influence = 0.0

    def keyframe_influence(target_name, frame, influence):
        for obj in [cam_pivot, cam_target]:
            c = obj.constraints.get(f"Copy_{target_name}")
            if c:
                c.influence = influence
                c.keyframe_insert(data_path="influence", frame=frame)

    # ── SHOT 1: Frames 1-60 – Born from the sun, extremely close ──
    keyframe_influence("Sun", 1, 1.0)
    for p_name in [p[0] for p in PLANET_DATA]:
        keyframe_influence(p_name, 1, 0.0)

    cam_obj.location = (9, 0, 2)           # Almost touching the sun surface
    cam_obj.keyframe_insert(data_path="location", frame=1)

    # ── SHOT 2: Frames 60-150 – Slowly pull back revealing the sun ──
    cam_obj.location = (0, -30, 8)
    cam_obj.keyframe_insert(data_path="location", frame=60)

    # ── SHOT 3: Frames 150-220 – Orbit the sun low and fast ──
    cam_obj.location = (40, -20, 5)
    cam_obj.keyframe_insert(data_path="location", frame=150)

    cam_obj.location = (-30, -40, 10)
    cam_obj.keyframe_insert(data_path="location", frame=220)

    # ── SHOT 4: Frames 220-300 – Pull back to overview before planet tour ──
    cam_obj.location = (0, -180, 120)
    cam_obj.keyframe_insert(data_path="location", frame=300)

    keyframe_influence("Sun", 300, 1.0)
    keyframe_influence("Sun", 301, 0.0)

    # ── PLANET BLOCKS ──
    blocks = [
        ("Mercury", 300,  400),
        ("Venus",   400,  500),
        ("Earth",   500,  640),
        ("Mars",    640,  740),
        ("Jupiter", 740,  920),
        ("Saturn",  920, 1080),
        ("Uranus", 1080, 1180),
        ("Neptune",1180, 1290),
        ("Pluto",  1290, 1390),
    ]

    prev_target    = "Sun"
    prev_end_frame = 300

    for idx, (pname, b_start, b_end) in enumerate(blocks):
        trans_end      = b_start + 25
        showcase_start = trans_end
        showcase_end   = b_end

        keyframe_influence(prev_target, trans_end,     1.0)
        keyframe_influence(prev_target, trans_end + 1, 0.0)
        keyframe_influence(pname, prev_end_frame, 0.0)
        keyframe_influence(pname, trans_end,      1.0)
        keyframe_influence(pname, showcase_end,   1.0)

        prad     = planets[pname]["radius"]
        cam_prad = prad * 2.5 if pname == "Saturn" else prad

        # Each planet gets a 3-point path: dive in → closest pass → pull back
        if pname == "Mercury":
            # Dive straight in from front, skim past surface
            p1 = (0,            -cam_prad * 12, cam_prad * 2)
            p2 = (cam_prad * 1.5, -cam_prad * 2, cam_prad * 0.5)  # Very close pass
            p3 = (-cam_prad * 8,  -cam_prad * 6, cam_prad * 3)

        elif pname == "Venus":
            # Spiral in from above
            p1 = (cam_prad * 8,  -cam_prad * 8,  cam_prad * 8)
            p2 = (cam_prad * 2,  -cam_prad * 3,  cam_prad * 1)
            p3 = (-cam_prad * 6, -cam_prad * 5,  cam_prad * 2)

        elif pname == "Earth":
            # ISS pass – comes in from the dark side
            p1 = (-cam_prad * 4, -cam_prad * 4,  -cam_prad * 2)   # Below equator
            p2 = (cam_prad * 2,  -cam_prad * 3,   cam_prad * 0.5) # Skim surface
            p3 = (cam_prad * 5,  -cam_prad * 9,   cam_prad * 4)   # Pull back to see moon

        elif pname == "Mars":
            # Valles Marineris flyover feel – low and fast
            p1 = (cam_prad * 10, -cam_prad * 4,   cam_prad * 0.3)
            p2 = (cam_prad * 0.5,-cam_prad * 2.5, cam_prad * 0.3) # Extremely low pass
            p3 = (-cam_prad * 7, -cam_prad * 8,   cam_prad * 5)

        elif pname == "Jupiter":
            # Wide arc – too big to get close, show scale
            p1 = (cam_prad * 6,  -cam_prad * 12,  cam_prad * 5)
            p2 = (-cam_prad * 2, -cam_prad * 7,   cam_prad * 1)   # Graze the clouds
            p3 = (cam_prad * 8,  -cam_prad * 10,  cam_prad * 6)

        elif pname == "Saturn":
            # Fly THROUGH the ring plane
            p1 = (cam_prad * 5,  -cam_prad * 10, -cam_prad * 5)   # Far below rings
            p2 = (cam_prad * 1,  -cam_prad * 4,   cam_prad * 0.1) # Skim ring plane
            p3 = (-cam_prad * 3, -cam_prad * 8,   cam_prad * 5)   # Rise above rings

        elif pname == "Uranus":
            # Roll around its weird tilt
            p1 = (cam_prad * 10, -cam_prad * 3,   cam_prad * 2)
            p2 = (cam_prad * 2,  -cam_prad * 5,  -cam_prad * 2)   # Dip below equator
            p3 = (-cam_prad * 6, -cam_prad * 7,   cam_prad * 4)

        elif pname == "Neptune":
            # Voyager 2 tribute – come in from above at steep angle
            p1 = (cam_prad * 2,  -cam_prad * 15,  cam_prad * 10)
            p2 = (cam_prad * 1,  -cam_prad * 4,   cam_prad * 1)
            p3 = (cam_prad * 8,  -cam_prad * 8,   cam_prad * 3)

        elif pname == "Pluto":
            # New Horizons tribute – extremely long approach from darkness
            p1 = (cam_prad * 20, -cam_prad * 20,  cam_prad * 10)  # Far darkness
            p2 = (cam_prad * 3,  -cam_prad * 6,   cam_prad * 2)   # Close reveal
            p3 = (-cam_prad * 5, -cam_prad * 12,  cam_prad * 5)   # Drift away sadly

        else:
            p1 = (-cam_prad * 5, -cam_prad * 8, cam_prad * 4)
            p2 = (cam_prad * 2,  -cam_prad * 3, cam_prad * 1)
            p3 = (cam_prad * 4,  -cam_prad * 6, cam_prad * 2)

        mid_frame = (showcase_start + showcase_end) // 2

        cam_obj.location = p1
        cam_obj.keyframe_insert(data_path="location", frame=showcase_start)

        cam_obj.location = p2
        cam_obj.keyframe_insert(data_path="location", frame=mid_frame)

        cam_obj.location = p3
        cam_obj.keyframe_insert(data_path="location", frame=showcase_end)

        prev_target    = pname
        prev_end_frame = showcase_end

    # ── FINAL SHOT: Frames 1390-1500 – Slow 360 spin around entire system ──
    final_trans_end = 1410
    final_end       = 1500

    keyframe_influence(prev_target, final_trans_end,     1.0)
    keyframe_influence(prev_target, final_trans_end + 1, 0.0)
    keyframe_influence("Sun", 1390,          0.0)
    keyframe_influence("Sun", final_trans_end, 1.0)
    keyframe_influence("Sun", final_end,     1.0)

    # Start angled, rotate around slowly — god's eye view
    cam_obj.location = (250, -50,  160)
    cam_obj.keyframe_insert(data_path="location", frame=final_trans_end)

    cam_obj.location = (50,  -250, 160)    # Quarter turn
    cam_obj.keyframe_insert(data_path="location", frame=final_trans_end + 30)

    cam_obj.location = (-250, -50, 160)    # Half turn
    cam_obj.keyframe_insert(data_path="location", frame=final_trans_end + 60)

    cam_obj.location = (0,   0,   300)     # Straight overhead — grand finale
    cam_obj.keyframe_insert(data_path="location", frame=final_end)

    # ── Interpolation ──
    for obj in [cam_pivot, cam_target, cam_obj]:
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'BEZIER'

    # Stronger shake for the probe feel
    if cam_obj.animation_data and cam_obj.animation_data.action:
        for fcurve in cam_obj.animation_data.action.fcurves:
            if fcurve.data_path == "location":
                mod          = fcurve.modifiers.new(type='NOISE')
                mod.scale    = 60.0
                mod.strength = 0.2

    return cam_obj, blocks
# ============================================================
# MAIN
# ============================================================
def main():
    print("=== Solar System Generator – Blender 3.6 ===")
    print("[1/6] Setting up scene...")
    setup_scene()

    print("[2/6] Building planets and materials...")
    planets = build_solar_system()

    print("[2b/6] Drawing orbit lines...")
    add_orbit_lines()

    print("[2c/6] Adding asteroid belt...")      # ADD THIS
    add_asteroid_belt()                           # ADD THIS

    print("[3/6] Animating orbits and rotations...")
    animate_solar_system(planets)

    print("[4/6] Building camera animation...")
    cam_obj, blocks = build_camera_system(planets)

    print("[4b/6] Adding Earth satellite...")     # ADD THIS
    add_earth_satellite(planets)                  # ADD THIS

    print("[5/6] Adding planet labels...")
    add_planet_labels(planets, cam_obj, blocks)

    print("[6/6] Finalising scene...")
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

    print("=== Done! Press SPACE or render to see the animation. ===")
main()