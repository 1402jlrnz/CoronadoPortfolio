import bpy
import math

# Target the sun object
sun = bpy.context.scene.objects.get("The Sun")

if sun is None:
    print("Error: Object 'sun' not found")
else:
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 250

    # The sun's axial tilt is 7.25 degrees
    sun.rotation_mode = 'XYZ'
    sun.rotation_euler[0] = math.radians(7.25) 

    for frame in range(1, 251):
        scene.frame_set(frame)
        
        # Spin on Z-axis with a 0.8 speed multiplier
        sun.rotation_euler[2] = math.radians(frame * 0.8)  
        sun.keyframe_insert(data_path="rotation_euler", index=2)