import bpy
import pandas as pd


# Function to add a bond between two objects
def add_bond_between_objects(obj1_name, obj2_name, bond_radius=0.1):
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


# Read the CSV file
HB_DATA_FILE = r"\\wsl.localhost\Ubuntu\home\mabagar\etudes\masters\ISDD\M2\Projet_Python\hb_couples.csv"
hb_data = pd.read_csv(HB_DATA_FILE)

# Get the Blender object containing the vertices
blender_object_name = "NewTrajectory"
blender_object = bpy.data.objects[blender_object_name]

# Ensure the object is a mesh
if blender_object.type == "MESH":
    # Iterate over each row in the CSV file
    for index, row in hb_data.iterrows():
        donor_index = int(row["Donor"])
        acceptor_index = int(row["Acceptor"])

        # Get the vertex locations
        donor_vertex = blender_object.data.vertices[donor_index].co
        acceptor_vertex = blender_object.data.vertices[acceptor_index].co

        # Create a temporary object at each vertex location
        bpy.ops.object.empty_add(location=donor_vertex)
        donor_obj = bpy.context.object
        bpy.ops.object.empty_add(location=acceptor_vertex)
        acceptor_obj = bpy.context.object

        # Add a bond between the donor and acceptor vertices
        add_bond_between_objects(donor_obj.name, acceptor_obj.name, bond_radius=0.001)

        # Remove the temporary objects
        bpy.data.objects.remove(donor_obj)
        bpy.data.objects.remove(acceptor_obj)
else:
    print(f"{blender_object_name} is not a mesh object.")
