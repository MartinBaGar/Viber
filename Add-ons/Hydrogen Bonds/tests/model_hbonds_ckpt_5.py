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


def create_bond_objects(frame, blender_object, bond_material):
    bonds_collection = bpy.data.collections.new("Bonds")
    bpy.data.collections["MolecularNodes"].children.link(bonds_collection)
    modeled_couples = []
    previous_couples = []
    diff_current = None
    diff_prev = None
    for frame, couples in frame_dict.items():
        diff_current = list(set(couples) - set(previous_couples))
        diff_prev = list(set(previous_couples) - set(couples))
        for couple in couples:
            bond_name = f"Bond_{int(couple[0])}_{int(couple[1])}"
            if couple not in modeled_couples:
                modeled_couples.append(couple)
                curve_data = bpy.data.curves.new(name=bond_name, type="CURVE")
                curve_object = bpy.data.objects.new(bond_name, curve_data)
                bonds_collection.objects.link(curve_object)

                # Set the curve settings
                curve_data.dimensions = "3D"
                curve_data.resolution_u = 0
                curve_data.bevel_depth = 0.0005

                # Create a new spline in the curve
                spline = curve_data.splines.new(type="POLY")
                spline.points.add(1)

                if curve_object.data.materials:
                    curve_object.data.materials[0] = bond_material
                else:
                    curve_object.data.materials.append(bond_material)
            spline.points[0].co = (
                *blender_object.data.vertices[int(couple[0])].co,
                1,
            )
            spline.points[1].co = (
                *blender_object.data.vertices[int(couple[1])].co,
                1,
            )
        previous_couples = frame_dict[frame]


# Main script
HB_DATA_FILE = r"\\wsl.localhost\Ubuntu\home\mabagar\etudes\masters\ISDD\M2\Projet_Python\hbonds_results.csv"
hb_data = pd.read_csv(HB_DATA_FILE)
grouped = hb_data.groupby("# Frame")

frame_dict = {}
for frame, group in grouped:
    unique_pairs = group[["Hydrogen", "Acceptor"]].drop_duplicates()
    pairs_list = list(unique_pairs.itertuples(index=False, name=None))
    frame_dict[frame] = pairs_list

unique_bonds_set = set()

for key, value in frame_dict.items():
    unique_bonds_set.update(value)

blender_object_name = "NewTrajectory"
blender_object = bpy.data.objects[blender_object_name]

bond_material = create_bond_material()
unique_bonds = create_bond_objects(frame_dict, blender_object, bond_material)
print("Done")
