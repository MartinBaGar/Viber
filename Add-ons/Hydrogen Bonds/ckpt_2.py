bl_info = {
    "name": "Dashed Hydrogen Bond Visualizer",
    "author": "Martin Bari Garnier (modified)",
    "version": (1, 2),
    "blender": (4, 2, 1),
    "location": "View3D > Sidebar > HBond Visualizer",
    "description": "Visualizes dashed hydrogen bonds from CSV data",
    "category": "Animation",
}

import bpy
import pandas as pd
from bpy.props import PointerProperty, StringProperty, FloatProperty
from bpy.types import Operator, Panel, PropertyGroup
from mathutils import Vector


def create_bond_material():
    material_name = "SharedBondMaterial"
    mat = bpy.data.materials.get(material_name)
    if mat is None:
        mat = bpy.data.materials.new(name=material_name)
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (1, 0, 0, 1)  # Red color
    return mat

def create_dashed_bond(start, end, dash_length, gap_length, name, collection, material):
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.00075
    
    curve_obj = bpy.data.objects.new(name, curve_data)
    collection.objects.link(curve_obj)
    
    distance = (end - start).length
    direction = (end - start).normalized()
    num_dashes = int(distance / (dash_length + gap_length))
    
    current_position = start
    for i in range(num_dashes):
        spline = curve_data.splines.new(type='BEZIER')
        spline.bezier_points.add(1)
        
        spline.bezier_points[0].co = current_position
        spline.bezier_points[0].handle_left = current_position
        spline.bezier_points[0].handle_right = current_position
        
        dash_end = current_position + direction * dash_length
        spline.bezier_points[1].co = dash_end
        spline.bezier_points[1].handle_left = dash_end
        spline.bezier_points[1].handle_right = dash_end
        
        current_position = dash_end + direction * gap_length
    
    curve_obj.data.materials.append(material)
    return curve_obj

def create_bond_objects(all_bonds, bond_material, dash_length, gap_length):
    bonds_collection = bpy.data.collections.new("Hydrogen Bonds")
    bpy.context.scene.collection.children.link(bonds_collection)
    bond_objects = {}
    for couple in all_bonds:
        bond_name = f"Bond_{int(couple[0])}_{int(couple[1])}"
        bond_objects[couple] = create_dashed_bond(Vector(), Vector(), dash_length, gap_length, bond_name, bonds_collection, bond_material)
    return bond_objects

def update_bond_positions(scene):
    frame = scene.frame_current
    couples = frame_dict.get(frame, set())
    for bond, obj in bond_objects.items():
        visible = bond in couples
        obj.hide_viewport = obj.hide_render = not visible
        if visible:
            start = blender_object.data.vertices[int(bond[0])].co
            end = blender_object.data.vertices[int(bond[1])].co
            update_dashed_bond(obj, start, end, scene.hbond_visualizer.dash_length, scene.hbond_visualizer.gap_length)

def update_dashed_bond(bond_obj, start, end, dash_length, gap_length):
    curve_data = bond_obj.data
    curve_data.splines.clear()
    
    distance = (end - start).length
    direction = (end - start).normalized()
    num_dashes = int(distance / (dash_length + gap_length))
    
    current_position = start
    for i in range(num_dashes):
        spline = curve_data.splines.new(type='BEZIER')
        spline.bezier_points.add(1)
        
        spline.bezier_points[0].co = current_position
        spline.bezier_points[0].handle_left = current_position
        spline.bezier_points[0].handle_right = current_position
        
        dash_end = current_position + direction * dash_length
        spline.bezier_points[1].co = dash_end
        spline.bezier_points[1].handle_left = dash_end
        spline.bezier_points[1].handle_right = dash_end
        
        current_position = dash_end + direction * gap_length

class HBondVisualizerProperties(PropertyGroup):
    csv_file: StringProperty(
        name="CSV File",
        description="Path to the CSV file containing hydrogen bond data",
        default="",
        maxlen=1024,
        subtype="FILE_PATH",
    )
    dash_length: FloatProperty(
        name="Dash Length",
        description="Length of each dash in the bond",
        default=0.002,  # Adjusted to be more suitable for the bond radius
        min=0.0001,
        max=0.1,
    )
    gap_length: FloatProperty(
        name="Gap Length",
        description="Length of the gap between dashes",
        default=0.01,  # Adjusted to be more suitable for the bond radius
        min=0.0001,
        max=0.1,
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
        bond_objects = create_bond_objects(all_bonds, bond_material, hbond_props.dash_length, hbond_props.gap_length)
        
        # Register the frame change handler
        bpy.app.handlers.frame_change_post.append(update_bond_positions)
        
        self.report({"INFO"}, "Dashed H-Bond visualization setup complete")
        return {"FINISHED"}

class VIEW3D_PT_hbond_visualizer(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "HBond Visualizer"
    bl_label = "Dashed H-Bond Visualizer"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        hbond_props = scene.hbond_visualizer
        
        layout.prop(hbond_props, "csv_file")
        layout.prop(hbond_props, "dash_length")
        layout.prop(hbond_props, "gap_length")
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