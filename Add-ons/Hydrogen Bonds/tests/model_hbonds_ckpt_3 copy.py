def update_bond_properties(hb_data, unique_bonds, blender_object):
    max_frame = int(hb_data["# Frame"].max())

    # Iterate over each frame starting from 0
    for frame in range(0, max_frame + 1):
        if frame % 100 == 0:
            print(f"Processing frame {frame}/{max_frame}")

        # Get data for the current frame
        frame_data = hb_data[hb_data["# Frame"] == frame]

        # Hide all bonds by default at the start of each frame
        if not frame_data.empty:
            # Only proceed with updates if there are bonds in the frame data
            for bond_obj in unique_bonds.values():
                bond_obj.hide_viewport = True
                bond_obj.hide_render = True
                bond_obj.keyframe_insert(data_path="hide_viewport", frame=frame)
                bond_obj.keyframe_insert(data_path="hide_render", frame=frame)

            # Update bond properties for the current frame
            for _, row in frame_data.iterrows():
                hydrogen_index = int(row["Hydrogen"]) - 1
                acceptor_index = int(row["Acceptor"]) - 1
                bond_key = (hydrogen_index, acceptor_index)

                if bond_key in unique_bonds:
                    bond_obj = unique_bonds[bond_key]

                    # Check if the vertices exist
                    if hydrogen_index >= len(
                        blender_object.data.vertices
                    ) or acceptor_index >= len(blender_object.data.vertices):
                        print(
                            f"Skipping bond {hydrogen_index+1}-{acceptor_index+1}: Vertex index out of range."
                        )
                        continue

                    # Get the global positions of the hydrogen and acceptor atoms
                    hydrogen_vertex = (
                        blender_object.matrix_world
                        @ blender_object.data.vertices[hydrogen_index + 1].co
                    )
                    acceptor_vertex = (
                        blender_object.matrix_world
                        @ blender_object.data.vertices[acceptor_index + 1].co
                    )

                    # Unhide the bond and insert keyframes for visibility
                    bond_obj.hide_viewport = False
                    bond_obj.hide_render = False
                    bond_obj.keyframe_insert(data_path="hide_viewport", frame=frame)
                    bond_obj.keyframe_insert(data_path="hide_render", frame=frame)

                    # Modify the bond vertices in object mode
                    bond_mesh = bond_obj.data
                    num_vertices = len(bond_mesh.vertices)

                    # Move the vertices of one circular edge to the hydrogen vertex
                    for i in range(num_vertices // 2):
                        bond_mesh.vertices[i].co = hydrogen_vertex

                    # Move the vertices of the other circular edge to the acceptor vertex
                    for i in range(num_vertices // 2, num_vertices):
                        bond_mesh.vertices[i].co = acceptor_vertex

                    # Update the mesh (no keyframes for vertices)
                    bond_mesh.update()

                else:
                    print(
                        f"Warning: Bond {hydrogen_index+1}-{acceptor_index+1} not found for frame {frame}"
                    )
