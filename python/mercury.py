import bpy
import math

# Target the mercury object
mercury = bpy.context.scene.objects.get("mercury")  

if mercury is None:
    print("Error: Object 'Mercury' not found")
else:
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 250

    mercury.rotation_mode = 'XYZ'

    # Mercury has ~0° tilt
    mercury.rotation_euler[0] = 0  

    for frame in range(1, 251):
        scene.frame_set(frame)
        
        # Spin ONLY on Z-axis
        mercury.rotation_euler[2] = math.radians(frame * 0.5)
        mercury.keyframe_insert(data_path="rotation_euler", index=2)s