import sys
import json

# Try to import bpy. This will only work when run inside Blender.
try:
    import bpy
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False
    print("Warning: 'bpy' not found. This script must be run inside Blender.")

def setup_scene(params):
    if not IN_BLENDER:
        return
        
    job_id = params.get("job_id", "unknown")
    output_filepath = params.get("output_filepath")
    infra_type = params.get("infrastructure_type", "habitat")
    
    # Clear existing mesh objects
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

    # Create dummy lunar terrain (a subdivided plane with displacement)
    bpy.ops.mesh.primitive_plane_add(size=20, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    terrain = bpy.context.active_object
    terrain.name = "LunarTerrain"
    
    # Create the infrastructure object based on the requested type
    if infra_type == "habitat":
        bpy.ops.mesh.primitive_cylinder_add(radius=2, depth=3, location=(0, 0, 1.5))
        obj = bpy.context.active_object
        obj.name = "LunarHabitat"
    elif infra_type == "solar_array":
        bpy.ops.mesh.primitive_cube_add(size=3, location=(0, 0, 0.5))
        obj = bpy.context.active_object
        obj.name = "SolarArray"
        obj.scale = (2, 0.5, 0.1)
    else:
        # Default placeholder
        bpy.ops.mesh.primitive_monkey_add(size=2, location=(0, 0, 1))
        obj = bpy.context.active_object
        obj.name = "UnknownInfra"
        
    # Setup Camera
    if "Camera" not in bpy.data.objects:
        bpy.ops.object.camera_add(location=(10, -10, 8), rotation=(1.1, 0, 0.8))
    camera = bpy.data.objects["Camera"]
    bpy.context.scene.camera = camera
    
    # Setup Lighting (Sun) based on solar_incidence_angle
    if "Light" not in bpy.data.objects:
        bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
    sun = bpy.data.objects["Light"]
    
    # Simple mapping: 0 degrees incidence = straight down.
    incidence = params.get("solar_incidence_angle", 45.0)
    import math
    rad = math.radians(incidence)
    # Rotate the sun to simulate incidence angle
    sun.rotation_euler = (rad, 0, 0)
    sun.data.energy = 5.0
    
    # Render Settings
    bpy.context.scene.render.engine = 'CYCLES' if 'CYCLES' in bpy.context.preferences.addons else 'BLENDER_EEVEE'
    bpy.context.scene.render.filepath = output_filepath
    bpy.context.scene.render.resolution_x = 800
    bpy.context.scene.render.resolution_y = 600
    
    # Render image
    print(f"Rendering job {job_id} to {output_filepath}")
    bpy.ops.render.render(write_still=True)

if __name__ == "__main__":
    # Extract arguments passed after '--'
    try:
        argv = sys.argv
        if "--" in argv:
            args_index = argv.index("--") + 1
            json_args = argv[args_index]
            params = json.loads(json_args)
            setup_scene(params)
        else:
            print("No parameters provided to blender script.")
    except Exception as e:
        print(f"Error executing blender script: {e}")
