import bpy
import numpy as np
import pandas as pd


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


def create_bond_objects(all_bonds, bond_material):
    bonds_collection = bpy.data.collections.new("Bonds")
    bpy.context.scene.collection.children.link(bonds_collection)

    bond_objects = {}
    for couple in all_bonds:
        bond_name = f"Bond_{int(couple[0])}_{int(couple[1])}"
        curve_data = bpy.data.curves.new(name=bond_name, type="CURVE")
        curve_object = bpy.data.objects.new(bond_name, curve_data)
        bonds_collection.objects.link(curve_object)
        curve_data.dimensions = "3D"
        curve_data.bevel_depth = 0.0005
        spline = curve_data.splines.new(type="POLY")
        spline.points.add(1)
        curve_object.data.materials.append(bond_material)
        bond_objects[couple] = curve_object

    return bond_objects


def update_bond_positions(scene):
    frame = scene.frame_current
    couples = frame_dict.get(frame, set())

    for bond, obj in bond_objects.items():
        visible = bond in couples
        obj.hide_viewport = obj.hide_render = not visible
        if visible:
            spline = obj.data.splines[0]
            spline.points[0].co = (*blender_object.data.vertices[int(bond[0])].co, 1)
            spline.points[1].co = (*blender_object.data.vertices[int(bond[1])].co, 1)


# Main script
HB_DATA_FILE = r"\\wsl.localhost\Ubuntu\home\mabagar\etudes\masters\ISDD\M2\Projet_Python\hbonds_results.csv"
hb_data = pd.read_csv(HB_DATA_FILE)

frame_dict = {
    frame: set(map(tuple, group[["Hydrogen", "Acceptor"]].values))
    for frame, group in hb_data.groupby("# Frame")
}

all_bonds = set().union(*frame_dict.values())

blender_object = bpy.data.objects["NewTrajectory"]

bond_material = create_bond_material()
bond_objects = create_bond_objects(all_bonds, bond_material)

# Register the frame change handler
bpy.app.handlers.frame_change_post.append(update_bond_positions)

print("Script execution completed successfully.")
