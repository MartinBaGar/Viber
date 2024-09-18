import math

import bpy
import pandas as pd
from mathutils import Vector


def create_bond_material():
    material_name = "SharedBondMaterial"
    mat = bpy.data.materials.get(material_name)
    if mat is None:
        mat = bpy.data.materials.new(name=material_name)
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (
            1,
            0,
            0,
            1,
        )  # Red color
    return mat


def create_bond_mesh(bond_radius=0.00075):  # Increased radius for visibility
    bpy.ops.mesh.primitive_cylinder_add(
        radius=bond_radius, depth=1, vertices=16
    )  # Increased vertices for smoother cylinder
    bond_mesh = bpy.context.active_object.data
    bpy.ops.object.delete()
    return bond_mesh


def create_bond_objects(hb_data, bond_mesh, blender_object, bond_material):
    bonds_collection = bpy.data.collections.new("Bonds")
    bpy.data.collections["MolecularNodes"].children.link(bonds_collection)
    unique_bonds = {}
    total_rows = len(hb_data)
    for index, row in hb_data.iterrows():
        if index % 1000 == 0:
            print(f"Processing row {index + 1}/{total_rows}")
        hydrogen_index = int(row["Hydrogen"]) - 1
        acceptor_index = int(row["Acceptor"]) - 1
        bond_key = (hydrogen_index, acceptor_index)
        if bond_key not in unique_bonds:
            bond_obj = bpy.data.objects.new(
                f"Bond_{hydrogen_index+1}_{acceptor_index+1}", bond_mesh.copy()
            )
            bonds_collection.objects.link(bond_obj)
            if bond_obj.data.materials:
                bond_obj.data.materials[0] = bond_material
            else:
                bond_obj.data.materials.append(bond_material)
            unique_bonds[bond_key] = bond_obj
            bond_obj["hydrogen_index"] = hydrogen_index
            bond_obj["acceptor_index"] = acceptor_index
    return unique_bonds


def update_bond_geometry(bond_obj, hydrogen_vertex, acceptor_vertex):
    direction = acceptor_vertex - hydrogen_vertex
    length = direction.length
    center = (hydrogen_vertex + acceptor_vertex) / 2

    bond_obj.location = center
    bond_obj.scale = (1, 1, length)
    bond_obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()


def update_bond_properties(hb_data, unique_bonds, blender_object):
    max_frame = int(hb_data["# Frame"].max())

    def frame_change_handler(scene):
        current_frame = scene.frame_current
        print(f"Current frame: {current_frame}")
        frame_data = hb_data[hb_data["# Frame"] == current_frame]

        for bond_obj in unique_bonds.values():
            bond_obj.hide_viewport = True
            bond_obj.hide_render = True

        for _, row in frame_data.iterrows():
            hydrogen_index = int(row["Hydrogen"]) - 1
            acceptor_index = int(row["Acceptor"]) - 1
            bond_key = (hydrogen_index, acceptor_index)
            if bond_key in unique_bonds:
                bond_obj = unique_bonds[bond_key]
                bond_obj.hide_viewport = False
                bond_obj.hide_render = False
                hydrogen_vertex = blender_object.data.vertices[hydrogen_index + 1].co
                acceptor_vertex = blender_object.data.vertices[acceptor_index + 1].co
                update_bond_geometry(bond_obj, hydrogen_vertex, acceptor_vertex)
                print(
                    f"Bond {bond_key}: Viewport hidden = {bond_obj.hide_viewport}, Render hidden = {bond_obj.hide_render}"
                )
            else:
                print(
                    f"Warning: Bond {hydrogen_index+1}-{acceptor_index+1} not found for frame {current_frame}"
                )

        # Ensure the view layer is updated
        scene.view_layers[0].update()

    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_pre.append(frame_change_handler)


# Main script
HB_DATA_FILE = r"\\wsl.localhost\Ubuntu\home\mabagar\etudes\masters\ISDD\M2\Projet_Python\hbonds_results.csv"
hb_data = pd.read_csv(HB_DATA_FILE)

blender_object_name = "NewTrajectory"
blender_object = bpy.data.objects[blender_object_name]
if blender_object.type != "MESH":
    print(f"{blender_object_name} is not a mesh object.")

bond_material = create_bond_material()
bond_mesh = create_bond_mesh()
unique_bonds = create_bond_objects(hb_data, bond_mesh, blender_object, bond_material)
update_bond_properties(hb_data, unique_bonds, blender_object)

print(f"Created {len(unique_bonds)} unique bond objects.")

# Force viewport update
bpy.context.view_layer.update()

# Set the first frame as active to trigger the frame_change_handler
bpy.context.scene.frame_set(bpy.context.scene.frame_start)
