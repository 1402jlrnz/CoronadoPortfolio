import bpy
import math

# Target the venus object
venus = bpy.context.scene.objects.get("venus")

if venus is None:
    print("Error: Object 'venus' not found")
else:
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 250

    # Venus is technically tilted completely upside down (177.3 degrees), 
    # but for this script, we'll keep it simple and just reverse the Z-spin!
    venus.rotation_mode = 'XYZ'
    venus.rotation_euler[0] = math.radians(2.7)

    for frame in range(1, 251):
        scene.frame_set(frame)
        
        # Notice the NEGATIVE sign here! This makes it spin backward.
        venus.rotation_euler[2] = math.radians(frame * -0.3)  
        venus.keyframe_insert(data_path="rotation_euler", index=2)