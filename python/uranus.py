import bpy
import math
import os

def setup_world_background():
    scene = bpy.context.scene
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
    w_bg.inputs["Strength"].default_value = 1.0

    # Try to load the image first
    img_path = r"C:\solar\stars.jpg"
    if os.path.exists(img_path):
        w_env = wn.new("ShaderNodeTexEnvironment")
        w_env.image = bpy.data.images.load(img_path)
        print("✅ Found stars.jpg! Using image background.")
        
        wl.new(w_env.outputs["Color"], w_bg.inputs["Color"])
    else:
        # Fallback: Generate Procedural Stars
        w_noise = wn.new("ShaderNodeTexNoise")
        w_ramp = wn.new("ShaderNodeValToRGB")
        
        w_noise.inputs["Scale"].default_value = 350.0
        w_noise.inputs["Detail"].default_value = 15.0
        
        cr = w_ramp.color_ramp
        cr.elements.position = 0.55
        cr.elements.color    = (0.002, 0.002, 0.005, 1.0) # Deep space black/blue
        cr.elements.position = 0.65
        cr.elements.color    = (1.0, 1.0, 1.0, 1.0)       # White stars
        
        wl.new(w_noise.outputs["Fac"], w_ramp.inputs["Fac"])
        wl.new(w_ramp.outputs["Color"], w_bg.inputs["Color"])
        print("⚠️ stars.jpg not found. Generated procedural stars instead.")

    wl.new(w_bg.outputs["Background"], w_out.inputs["Surface"])


def apply_infinite_spin():
    obj = bpy.context.active_object

    if not obj:
        print("❌ ERROR: Please select your Uranus model in the 3D viewport first!")
        return

    spin_axis = 2         # 0 = X, 1 = Y, 2 = Z
    degrees = 360         
    frames = 240          

    if not obj.animation_data:
        obj.animation_data_create()
    
    if not obj.animation_data.action:
        action = bpy.data.actions.new(name=f"{obj.name}_InfiniteSpin")
        obj.animation_data.action = action
    else:
        action = obj.animation_data.action

    # Set Keyframes
    obj.rotation_euler[spin_axis] = 0.0
    obj.keyframe_insert(data_path="rotation_euler", index=spin_axis, frame=1)
    
    obj.rotation_euler[spin_axis] = math.radians(degrees)
    obj.keyframe_insert(data_path="rotation_euler", index=spin_axis, frame=frames)

    # Extract F-curves safely (Blender 5.x safe)
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

    # Make the animation Linear and Infinite
    for fc in fcurves:
        if fc.data_path == "rotation_euler" and fc.array_index == spin_axis:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
            if len(fc.modifiers) == 0:
                fc.modifiers.new('CYCLES')
                
    print(f"✅ SUCCESS: Infinite spin applied to '{obj.name}'!")


# ─── RUN THE SCRIPT ───
setup_world_background()
apply_infinite_spin()