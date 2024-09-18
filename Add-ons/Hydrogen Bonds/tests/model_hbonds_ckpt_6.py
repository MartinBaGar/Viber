import bpy
import pandas as pd
from mathutils import Vector


def create_bond_material():
    print("Creating bond material...")
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
    print("Bond material created.")
    return mat


def create_bond_objects(frame_dict, blender_object, bond_material):
    print("Creating bond objects...")
    bonds_collection = bpy.data.collections.new("Bonds")
    bpy.data.collections["MolecularNodes"].children.link(bonds_collection)
    all_bonds = set()
    for couples in frame_dict.values():
        all_bonds.update(couples)

    bond_objects = {}
    total_bonds = len(all_bonds)
    for i, couple in enumerate(all_bonds, 1):
        bond_name = f"Bond_{int(couple[0])}_{int(couple[1])}"
        curve_data = bpy.data.curves.new(name=bond_name, type="CURVE")
        curve_object = bpy.data.objects.new(bond_name, curve_data)
        bonds_collection.objects.link(curve_object)

        curve_data.dimensions = "3D"
        curve_data.resolution_u = 0
        curve_data.bevel_depth = 0.0005

        spline = curve_data.splines.new(type="POLY")
        spline.points.add(1)

        if curve_object.data.materials:
            curve_object.data.materials[0] = bond_material
        else:
            curve_object.data.materials.append(bond_material)

        bond_objects[couple] = curve_object

        if i % 100 == 0 or i == total_bonds:
            print(f"Created {i}/{total_bonds} bond objects...")

    print("All bond objects created.")
    return bond_objects


def update_bond_animation(frame_dict, bond_objects, blender_object):
    print("Updating bond animation...")
    total_frames = len(frame_dict)
    for i, (frame, couples) in enumerate(frame_dict.items(), 1):
        bpy.context.scene.frame_set(int(frame))
        for bond, obj in bond_objects.items():
            if bond in couples:
                obj.hide_viewport = False
                obj.hide_render = False

                spline = obj.data.splines[0]
                spline.points[0].co = (
                    *blender_object.data.vertices[int(bond[0])].co,
                    1,
                )
                spline.points[1].co = (
                    *blender_object.data.vertices[int(bond[1])].co,
                    1,
                )

                spline.points[0].keyframe_insert(data_path="co")
                spline.points[1].keyframe_insert(data_path="co")
                obj.keyframe_insert(data_path="hide_viewport")
                obj.keyframe_insert(data_path="hide_render")
            else:
                obj.hide_viewport = True
                obj.hide_render = True
                obj.keyframe_insert(data_path="hide_viewport")
                obj.keyframe_insert(data_path="hide_render")

        if i % 10 == 0 or i == total_frames:
            print(f"Processed {i}/{total_frames} frames...")

    print("Bond animation update complete.")


# Main script
print("Starting script execution...")

HB_DATA_FILE = r"\\wsl.localhost\Ubuntu\home\mabagar\etudes\masters\ISDD\M2\Projet_Python\hbonds_results.csv"
print(f"Reading CSV file: {HB_DATA_FILE}")
hb_data = pd.read_csv(HB_DATA_FILE)
print("CSV file read successfully.")

print("Processing data...")
grouped = hb_data.groupby("# Frame")
frame_dict = {}
for frame, group in grouped:
    unique_pairs = group[["Hydrogen", "Acceptor"]].drop_duplicates()
    pairs_list = list(unique_pairs.itertuples(index=False, name=None))
    frame_dict[frame] = pairs_list
print("Data processing complete.")

blender_object_name = "NewTrajectory"
print(f"Using Blender object: {blender_object_name}")
blender_object = bpy.data.objects[blender_object_name]

bond_material = create_bond_material()
bond_objects = create_bond_objects(frame_dict, blender_object, bond_material)
update_bond_animation(frame_dict, bond_objects, blender_object)

print("Script execution completed successfully.")
