bl_info = {
    "name": "Hydrogen Bond Visualizer",
    "author": "Martin Bari Garnier",
    "version": (1, 0),
    "blender": (4, 2, 1),
    "location": "View3D > Sidebar > HBond Visualizer",
    "description": "Visualizes hydrogen bonds from CSV data",
    "category": "Animation",
}

import bpy
import pandas as pd
from bpy.props import PointerProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup


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


class HBondVisualizerProperties(PropertyGroup):
    csv_file: StringProperty(
        name="CSV File",
        description="Path to the CSV file containing hydrogen bond data",
        default="",
        maxlen=1024,
        subtype="FILE_PATH",
    )


class OBJECT_OT_hbond_visualizer(Operator):
    bl_idname = "object.hbond_visualizer"
    bl_label = "Visualize H-Bonds"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        global frame_dict, bond_objects, blender_object

        scene = context.scene
        hbond_props = scene.hbond_visualizer

        # Read CSV file
        hb_data = pd.read_csv(hbond_props.csv_file)

        frame_dict = {
            frame: set(map(tuple, group[["Hydrogen", "Acceptor"]].values))
            for frame, group in hb_data.groupby("# Frame")
        }

        all_bonds = set().union(*frame_dict.values())

        blender_object = context.active_object

        bond_material = create_bond_material()
        bond_objects = create_bond_objects(all_bonds, bond_material)

        # Register the frame change handler
        bpy.app.handlers.frame_change_post.append(update_bond_positions)

        self.report({"INFO"}, "H-Bond visualization setup complete")
        return {"FINISHED"}


class VIEW3D_PT_hbond_visualizer(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "HBond Visualizer"
    bl_label = "H-Bond Visualizer"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        hbond_props = scene.hbond_visualizer

        layout.prop(hbond_props, "csv_file")
        layout.operator("object.hbond_visualizer")


classes = (
    HBondVisualizerProperties,
    OBJECT_OT_hbond_visualizer,
    VIEW3D_PT_hbond_visualizer,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.hbond_visualizer = PointerProperty(type=HBondVisualizerProperties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.hbond_visualizer


if __name__ == "__main__":
    register()
