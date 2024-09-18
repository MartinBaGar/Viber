import bpy
import pandas as pd
from mathutils import Vector


def create_bond_material(color=(1, 1, 1, 1)):
    mat = bpy.data.materials.new(name="BondMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    node_emission = nodes.new(type="ShaderNodeEmission")
    node_emission.inputs[0].default_value = color
    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    mat.node_tree.links.new(node_emission.outputs[0], node_output.inputs[0])
    return mat


def create_bond_mesh(bond_radius=0.001):
    bpy.ops.mesh.primitive_cylinder_add(radius=bond_radius, depth=1)
    bond_mesh = bpy.context.active_object.data
    bpy.ops.object.delete()
    return bond_mesh


def main():
    # Read the CSV file
    HB_DATA_FILE = r"\\wsl.localhost\Ubuntu\home\mabagar\etudes\masters\ISDD\M2\Projet_Python\hbonds_results.csv"
    hb_data = pd.read_csv(HB_DATA_FILE)

    # Get the Blender object containing the vertices
    blender_object_name = "NewTrajectory"
    blender_object = bpy.data.objects[blender_object_name]

    if blender_object.type != "MESH":
        print(f"{blender_object_name} is not a mesh object.")
        return

    # Create a single bond mesh and material to be instanced
    bond_mesh = create_bond_mesh()
    bond_material = create_bond_material(
        color=(0, 1, 1, 0.8)
    )  # Cyan color with some transparency

    # Create a parent object for all bonds
    bonds_parent = bpy.data.objects.new("Bonds", None)
    bpy.context.scene.collection.objects.link(bonds_parent)

    # Create a dictionary to store unique bonds
    unique_bonds = {}

    # First pass: create unique bond objects
    total_rows = len(hb_data)
    for index, row in hb_data.iterrows():
        if index % 1000 == 0:
            print(f"Processing row {index + 1}/{total_rows}")

        frame = int(row["# Frame"])
        hydrogen_index = int(row["Hydrogen"]) - 1
        acceptor_index = int(row["Acceptor"]) - 1
        bond_key = (hydrogen_index, acceptor_index)

        if bond_key not in unique_bonds:
            bond_obj = bpy.data.objects.new(
                f"Bond_{hydrogen_index+1}_{acceptor_index+1}", bond_mesh
            )
            bond_obj.parent = bonds_parent
            bpy.context.scene.collection.objects.link(bond_obj)
            if bond_obj.data.materials:
                bond_obj.data.materials[0] = bond_material
            else:
                bond_obj.data.materials.append(bond_material)
            unique_bonds[bond_key] = bond_obj

    # Second pass: update bond properties for each frame
    max_frame = int(hb_data["# Frame"].max())
    for frame in range(max_frame + 1):
        if frame % 100 == 0:
            print(f"Processing frame {frame + 1}/{max_frame + 1}")

        frame_data = hb_data[hb_data["# Frame"] == frame]

        for bond_obj in unique_bonds.values():
            # Hide the bond by default
            bond_obj.hide_viewport = True
            bond_obj.hide_render = True
            bond_obj.keyframe_insert(data_path="hide_viewport", frame=frame)
            bond_obj.keyframe_insert(data_path="hide_render", frame=frame)

        for _, row in frame_data.iterrows():
            hydrogen_index = int(row["Hydrogen"]) - 1
            acceptor_index = int(row["Acceptor"]) - 1
            bond_key = (hydrogen_index, acceptor_index)
            bond_obj = unique_bonds[bond_key]

            try:
                # Get vertex locations
                hydrogen_vertex = blender_object.data.vertices[hydrogen_index + 1].co
                acceptor_vertex = blender_object.data.vertices[acceptor_index + 1].co

                # Update bond position and scale
                direction = acceptor_vertex - hydrogen_vertex
                bond_obj.location = (hydrogen_vertex + acceptor_vertex) / 2
                bond_obj.scale = (1, 1, direction.length)
                bond_obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()

                # Make the bond visible for this frame
                bond_obj.hide_viewport = False
                bond_obj.hide_render = False
                bond_obj.keyframe_insert(data_path="hide_viewport", frame=frame)
                bond_obj.keyframe_insert(data_path="hide_render", frame=frame)
                bond_obj.keyframe_insert(data_path="location", frame=frame)
                bond_obj.keyframe_insert(data_path="scale", frame=frame)
                bond_obj.keyframe_insert(data_path="rotation_euler", frame=frame)
            except IndexError:
                print(
                    f"Warning: Vertex index out of range for bond {hydrogen_index+1}-{acceptor_index+1} in frame {frame}"
                )

    print(f"Created {len(unique_bonds)} unique bond objects.")


# Directly call the main function
main()
