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


def update_bond(spline, hydrogen_index, acceptor_index):
    spline.points[0].co = (
        *blender_object.data.vertices[hydrogen_index + 1].co,
        1,
    )
    spline.points[1].co = (
        *blender_object.data.vertices[acceptor_index + 1].co,
        1,
    )


def create_bond_objects(hb_data, blender_object, bond_material):
    bonds_collection = bpy.data.collections.new("Bonds")
    bpy.data.collections["MolecularNodes"].children.link(bonds_collection)
    unique_bonds = {}
    frame_bonds = {}
    for index, row in hb_data.iterrows():
        if index % 1000 == 0:
            print(f"Processing row {index + 1}/{len(hb_data)}")

        hydrogen_index = int(row["Hydrogen"]) - 1
        acceptor_index = int(row["Acceptor"]) - 1
        bond_name = f"Bond_{hydrogen_index+1}_{acceptor_index+1}"
        bond_key = (hydrogen_index, acceptor_index)
        frame_bonds.get(row["# Frame"], bond_key)

        if bond_key not in unique_bonds:
            curve_data = bpy.data.curves.new(name=bond_name, type="CURVE")
            curve_object = bpy.data.objects.new(bond_name, curve_data)
            bonds_collection.objects.link(curve_object)

            # Set the curve settings
            curve_data.dimensions = "3D"
            curve_data.resolution_u = 0
            curve_data.bevel_depth = 0.0005

            # Create a new spline in the curve
            spline = curve_data.splines.new(type="POLY")
            spline.points.add(1)  # Add one point (the first one is created by default)

            # Set the coordinates of the two points
            spline.points[0].co = (
                *blender_object.data.vertices[hydrogen_index + 1].co,
                1,
            )
            spline.points[1].co = (
                *blender_object.data.vertices[acceptor_index + 1].co,
                1,
            )

            if curve_object.data.materials:
                curve_object.data.materials[0] = bond_material
            else:
                curve_object.data.materials.append(bond_material)
            unique_bonds[bond_key] = curve_object

        else:
            update_bond(spline, hydrogen_index, acceptor_index)

    return unique_bonds


# Main script
HB_DATA_FILE = r"\\wsl.localhost\Ubuntu\home\mabagar\etudes\masters\ISDD\M2\Projet_Python\hbonds_results.csv"
hb_data = pd.read_csv(HB_DATA_FILE)
grouped = hb_data.groupby("# Frame")

frame_dict = {}
for frame, group in grouped:
    unique_pairs = group[["Hydrogen", "Acceptor"]].drop_duplicates()
    pairs_list = list(unique_pairs.itertuples(index=False, name=None))
    frame_dict[frame] = pairs_list

blender_object_name = "NewTrajectory"
blender_object = bpy.data.objects[blender_object_name]

bond_material = create_bond_material()
unique_bonds = create_bond_objects(frame_dict, blender_object, bond_material)
print("Done")
