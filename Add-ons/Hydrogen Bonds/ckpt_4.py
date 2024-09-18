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
    material_name = "HydrogenBond_Material"
    mat = bpy.data.materials.get(material_name)
    if mat is None:
        mat = bpy.data.materials.new(name=material_name)
        mat.use_nodes = True
        
        # Clear default nodes
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        # Add necessary nodes
        texture_coord = nodes.new(type="ShaderNodeTexCoord")
        color_ramp = nodes.new(type="ShaderNodeValToRGB")
        wave_texture = nodes.new(type="ShaderNodeTexWave")
        principled_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
        output_node = nodes.new(type="ShaderNodeOutputMaterial")
        
        # Set node locations
        texture_coord.location = (-400, 0)
        wave_texture.location = (-200, 0)
        color_ramp.location = (0, 0)
        principled_bsdf.location = (200, 0)
        output_node.location = (400, 0)
        
        # Connect nodes
        links = mat.node_tree.links
        links.new(texture_coord.outputs["UV"], wave_texture.inputs["Vector"])
        links.new(wave_texture.outputs["Fac"], color_ramp.inputs["Fac"])
        links.new(color_ramp.outputs["Color"], principled_bsdf.inputs["Alpha"])
        links.new(principled_bsdf.outputs["BSDF"], output_node.inputs["Surface"])
        
        # Set up wave texture for dashed line effect
        wave_texture.wave_type = "BANDS"
        wave_texture.bands_direction = "X"
        wave_texture.wave_profile = "SIN"
        wave_texture.inputs[1].default_value = 2 # Adjust the scale
        
        # Set up color ramp for sharp transitions
        color_ramp.color_ramp.elements[0].position = 0.0
        color_ramp.color_ramp.elements[0].color = (1, 1, 1, 1)  # White (visible)
        color_ramp.color_ramp.interpolation = "CONSTANT"
        color_ramp.color_ramp.elements[1].position = 0.5
        color_ramp.color_ramp.elements[1].color = (0, 0, 0, 0)  # Transparent
        
        # Set up principled BSDF
        principled_bsdf.inputs["Base Color"].default_value = (1, 0, 0, 1)  # Red color
        principled_bsdf.inputs["Alpha"].default_value = 1
        
        # Set material properties
        mat.blend_method = 'CLIP'
        mat.shadow_method = 'CLIP'
        # mat.alpha_threshold = 0.5
    
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
