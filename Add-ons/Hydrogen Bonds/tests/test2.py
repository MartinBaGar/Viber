import bpy


# Function to calculate the number of vertices in a given mesh object
def count_vertices_in_mesh(object_name):
    # Check if the object exists in the scene
    if object_name in bpy.data.objects:
        obj = bpy.data.objects[object_name]

        # Ensure the object is a mesh
        if obj.type == "MESH":
            # Access the mesh data
            mesh = obj.data
            # Return the number of vertices
            return len(mesh.vertices)
        else:
            print(f"{object_name} is not a mesh object.")
            return None
    else:
        print(f"Object '{object_name}' not found.")
        return None


# Function to select the first 10 vertices in a given mesh object
def select_and_print_first_10_vertices(object_name):
    # Check if the object exists in the scene
    if object_name in bpy.data.objects:
        obj = bpy.data.objects[object_name]

        # Ensure the object is a mesh
        if obj.type == "MESH":
            # Enter Object Mode
            bpy.ops.object.mode_set(mode="OBJECT")

            # Select the first 10 vertices and print their locations
            for i in range(min(10, len(obj.data.vertices))):
                obj.data.vertices[i].select = True
                print(f"Vertex {i} location: {obj.data.vertices[i].co}")

            # Return to Edit Mode to see the selection
            bpy.ops.object.mode_set(mode="EDIT")
        else:
            print(f"{object_name} is not a mesh object.")
    else:
        print(f"Object '{object_name}' not found.")


# Example usage
mesh_name = "NewTrajectory"
vertex_count = count_vertices_in_mesh(mesh_name)

if vertex_count is not None:
    print(f"The mesh '{mesh_name}' has {vertex_count} vertices.")
    select_and_print_first_10_vertices(mesh_name)
else:
    print("Could not calculate the number of vertices.")
