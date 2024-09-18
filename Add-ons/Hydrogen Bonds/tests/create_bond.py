import math

import bpy
from mathutils import Vector


# Function to create a cylinder between two objects
def add_bond_between_objects(obj1_name, obj2_name, bond_radius=0.05):
    # Get the objects by their names
    obj1 = bpy.data.objects[obj1_name]
    obj2 = bpy.data.objects[obj2_name]

    # Calculate the distance and direction between the two objects
    loc1 = obj1.location
    loc2 = obj2.location
    direction = loc2 - loc1
    distance = direction.length

    # Create a cylinder
    bpy.ops.mesh.primitive_cylinder_add(
        radius=bond_radius, depth=distance, location=(0, 0, 0)
    )
    bond = bpy.context.object

    # Position the cylinder between the two objects
    bond.location = (loc1 + loc2) / 2

    # Align the cylinder to point from obj1 to obj2
    bond.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()


# Example usage: Add a bond between "Sphere1" and "Sphere2"
add_bond_between_objects("Sphere1", "Sphere2", bond_radius=0.1)
