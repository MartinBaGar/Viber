bl_info = {
    "name": "Viber",
    "author": "Martin Bari Garnier",
    "version": (1, 0),
    "blender": (4, 2, 1),
    "location": "View3D > Sidebar > Viber",
    "description": "Visualize interactions from JSON data",
    "category": "Animation",
}

import json

import bpy
from bpy.props import PointerProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup
from mathutils import Vector


def create_bond_material(interaction_type):
    material_name = f"{interaction_type}_Material"
    mat = bpy.data.materials.get(material_name)
    if mat is None:
        mat = bpy.data.materials.new(name=material_name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        nodes.clear()

        # Common nodes
        texture_coord = nodes.new(type="ShaderNodeTexCoord")
        color_ramp = nodes.new(type="ShaderNodeValToRGB")
        wave_texture = nodes.new(type="ShaderNodeTexWave")
        principled_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
        output_node = nodes.new(type="ShaderNodeOutputMaterial")

        # Node positioning
        texture_coord.location = (-400, 0)
        wave_texture.location = (-200, 0)
        color_ramp.location = (0, 0)
        principled_bsdf.location = (200, 0)
        output_node.location = (400, 0)

        links = mat.node_tree.links
        links.new(texture_coord.outputs["UV"], wave_texture.inputs["Vector"])
        links.new(wave_texture.outputs["Fac"], color_ramp.inputs["Fac"])
        links.new(color_ramp.outputs["Color"], principled_bsdf.inputs["Alpha"])
        links.new(principled_bsdf.outputs["BSDF"], output_node.inputs["Surface"])

        # Customize based on interaction type
        if interaction_type == "Hydrogen":
            principled_bsdf.inputs["Base Color"].default_value = (0, 1, 0, 1)  # Green
            wave_texture.inputs[1].default_value = 10  # Tighter wave pattern
        elif interaction_type == "Salt_Bridge":
            principled_bsdf.inputs["Base Color"].default_value = (
                1,
                0.5,
                0,
                1,
            )  # Orange
            wave_texture.inputs[1].default_value = 5  # Moderate wave pattern
        elif interaction_type == "PiStacking":
            principled_bsdf.inputs["Base Color"].default_value = (0, 0, 1, 1)  # Blue
            wave_texture.inputs[1].default_value = 15  # Very tight wave pattern
        elif interaction_type == "CationPi":
            principled_bsdf.inputs["Base Color"].default_value = (
                0.5,
                0,
                0.5,
                1,
            )  # Purple
            wave_texture.inputs[1].default_value = 7  # Slightly denser wave pattern

        # Common wave texture settings
        wave_texture.wave_type = "BANDS"
        wave_texture.bands_direction = "X"
        wave_texture.wave_profile = "SIN"

        # Color ramp settings
        color_ramp.color_ramp.elements[0].position = 0.0
        color_ramp.color_ramp.elements[0].color = (1, 1, 1, 1)  # White (visible)
        color_ramp.color_ramp.interpolation = "CONSTANT"
        color_ramp.color_ramp.elements[1].position = 0.5
        color_ramp.color_ramp.elements[1].color = (0, 0, 0, 0)  # Transparent

        principled_bsdf.inputs["Alpha"].default_value = 1

        mat.blend_method = "CLIP"
        mat.shadow_method = "CLIP"

    return mat


def calculate_centroid(blender_object, indices):
    """Calculate the centroid of a set of vertex indices."""
    vertices = [blender_object.data.vertices[int(idx)].co for idx in indices]
    return sum(vertices, Vector((0, 0, 0))) / len(vertices)


def create_bond_objects(
    all_bonds, bond_material, interaction_type, blender_object=None
):
    # Ensure Interactions collection exists
    if "Interactions" not in bpy.data.collections:
        bonds_collection = bpy.data.collections.new("Interactions")
        bpy.context.scene.collection.children.link(bonds_collection)

    # Get or create interaction-specific collection
    interaction_collection = bpy.data.collections.get(interaction_type)
    if not interaction_collection:
        interaction_collection = bpy.data.collections.new(interaction_type)
        bpy.data.collections["Interactions"].children.link(interaction_collection)

    bond_objects = {}
    for couple in all_bonds:
        bond_name = f"{interaction_type.lower()[:6]}_{str(couple[0])}_{str(couple[1])}"
        curve_data = bpy.data.curves.new(name=bond_name, type="CURVE")
        curve_object = bpy.data.objects.new(bond_name, curve_data)
        interaction_collection.objects.link(curve_object)
        curve_data.dimensions = "3D"
        # curve_data.bevel_depth = 0.0005
        curve_data.bevel_depth = 0.0025
        spline = curve_data.splines.new(type="POLY")
        spline.points.add(1)
        curve_object.data.materials.append(bond_material)
        bond_objects[couple] = curve_object

    return bond_objects


def update_bond_positions(scene, depsgraph):
    global frame_dict, bond_objects
    interation_props = scene.interation_visualizer
    object_name = interation_props.object_name

    blender_object = bpy.data.objects.get(object_name)
    if not blender_object or not blender_object.data:
        return

    frame = str(scene.frame_current)
    for interaction_type, type_bonds in bond_objects.items():
        couples = frame_dict[interaction_type].get(frame, set())

        for bond, obj in type_bonds.items():
            if obj and obj.data:
                visible = bond in couples
                obj.hide_viewport = obj.hide_render = not visible

                if visible:
                    spline = obj.data.splines[0]

                    # Handle PiStacking differently
                    if interaction_type == "PiStacking":
                        # Calculate centroids for both rings
                        lig_centroid = calculate_centroid(blender_object, bond[0])
                        prot_centroid = calculate_centroid(blender_object, bond[1])

                        spline.points[0].co = (*lig_centroid, 1)
                        spline.points[1].co = (*prot_centroid, 1)
                    else:
                        # Original handling for other interaction types
                        spline.points[0].co = (
                            *blender_object.data.vertices[int(bond[0])].co,
                            1,
                        )
                        spline.points[1].co = (
                            *blender_object.data.vertices[int(bond[1])].co,
                            1,
                        )


class InteractionVisualizerProperties(PropertyGroup):
    json_file: StringProperty(
        name="JSON File",
        description="Path to the JSON file containing data",
        default="",
        maxlen=1024,
        subtype="FILE_PATH",
    )
    object_name: StringProperty(
        name="Blender Object Name",
        description="Name of the Blender object representing the molecule",
        default="",
    )


class OBJECT_OT_interation_visualizer(Operator):
    bl_idname = "object.interation_visualizer"
    bl_label = "Visualize Interactions"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        global frame_dict, bond_objects, blender_object
        scene = context.scene
        interation_props = scene.interation_visualizer
        json_file = interation_props.json_file

        # Store the active object's name in the scene property
        blender_object = context.active_object
        if blender_object:
            interation_props.object_name = blender_object.name

        with open(json_file, "r") as file:
            hb_data = json.load(file)

        frame_dict = {}
        for interaction_type, frames in hb_data.items():
            if interaction_type not in frame_dict:
                frame_dict[interaction_type] = {}

            for frame_key, interactions in frames.items():
                if frame_key not in frame_dict[interaction_type]:
                    frame_dict[interaction_type][frame_key] = set()

                for interaction in interactions:
                    if interaction_type == "PiStacking":
                        frame_dict[interaction_type][frame_key].add(
                            (
                                tuple(interaction["Ligand"]),
                                tuple(interaction["Protein"]),
                            )
                        )
                    else:
                        frame_dict[interaction_type][frame_key].add(
                            (
                                float(interaction["Ligand"]),
                                float(interaction["Protein"]),
                            )
                        )

        bond_objects = {}
        for interaction_type, frames in frame_dict.items():
            all_bonds = set().union(*frame_dict[interaction_type].values())
            bond_material = create_bond_material(interaction_type)
            bond_objects[interaction_type] = create_bond_objects(
                all_bonds, bond_material, interaction_type
            )

            # Register the frame change handler
            bpy.app.handlers.frame_change_post.append(update_bond_positions)

        self.report({"INFO"}, "H-Bond visualization setup complete")
        return {"FINISHED"}


class OBJECT_OT_remake_interaction(Operator):
    bl_idname = "object.remake_interaction"
    bl_label = "Reload Interactions"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if "Interactions" in bpy.data.collections:
            interactions_collection = bpy.data.collections["Interactions"]

            for subcollection in interactions_collection.children:
                for obj in list(subcollection.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)

            for subcollection in list(interactions_collection.children):
                bpy.data.collections.remove(subcollection)

            bpy.data.collections.remove(interactions_collection)

        bpy.ops.object.interation_visualizer()

        self.report({"INFO"}, "Interaction remade")
        return {"FINISHED"}


class VIEW3D_PT_interation_visualizer(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Interaction visualizer"
    bl_label = "Interaction visualizer"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        interation_props = scene.interation_visualizer

        layout.prop(interation_props, "json_file")
        layout.prop(interation_props, "object_name")
        layout.operator("object.interation_visualizer")
        layout.operator("object.remake_interaction")


classes = (
    InteractionVisualizerProperties,
    OBJECT_OT_interation_visualizer,
    OBJECT_OT_remake_interaction,
    VIEW3D_PT_interation_visualizer,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.interation_visualizer = PointerProperty(
        type=InteractionVisualizerProperties
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.interation_visualizer


if __name__ == "__main__":
    register()

