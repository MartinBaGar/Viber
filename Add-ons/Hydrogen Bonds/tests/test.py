import bmesh
import bpy


def clean_workspace():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    bpy.ops.outliner.orphans_purge(
        do_local_ids=True, do_linked_ids=True, do_recursive=True
    )
    print("!!! The workspace has been cleansed !!!")


# Clean workspace
clean_workspace()

# Import the mesh (from your operation)
bpy.context.scene.MN_pdb_code = "1G03"
bpy.ops.mn.import_wwpdb()

# Set up render engine and shading
bpy.context.scene.render.engine = "CYCLES"
bpy.context.scene.cycles.device = "GPU"
bpy.context.space_data.shading.type = "RENDERED"

# Set object as active
obj = bpy.data.objects["1G03"]
bpy.context.view_layer.objects.active = obj

# Switch to Edit Mode
bpy.ops.object.mode_set(mode="EDIT")

# Switch to Vertex select mode
bpy.ops.mesh.select_mode(type="VERT")

# Deselect all vertices in Edit Mode
bpy.ops.mesh.select_all(action="DESELECT")

# Create a BMesh from the active object's mesh
bm = bmesh.from_edit_mesh(obj.data)

# Loop over the vertices and select based on Z coordinate
for vert in bm.verts:
    vert.select = False  # Deselect all vertices initially
    if vert.co.z > 0:  # If the Z-coordinate is above 0, select the vertex
        vert.select = True

# Update the BMesh to reflect changes in the viewport
bmesh.update_edit_mesh(obj.data)
