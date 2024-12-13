# Welcome MD Wizard !!!

Look at this spell :

![](./resources/vid/movie.mp4)

To use this extension you will need:

- A few python libraries (tested only for the following versions):

    - MDAnalysis 2.6.1
    - PROLIF 2.0.3
    - Pandas 2.1.2

- Molecular Dynamics data (MDAnalysis compatible):

    - Topology
    - Trajectory

- The Molecular Nodes extension from the amazing BradyOJohnston.

- A JSON file containting indices of interacting atoms per interaction type and per frame.

## Prepare the data in a JSON format

{
    "<Interaction_Type>": {
        "<Frame_Number>": [
            {
                "Ligand": [vertex_indices],
                "Protein": [vertex_indices]
            }
        ]
    }
}

You can follow the provided notebook the generate both data and structure easily.

## Install the extension

At the current state, you only need the `__init__.py` file and register it as an add-on.

## In-Blender useage

The extension pannel is visible in the layout screen. You just need to load the JSON file and click the XXX button and the objects will be created automatically. As frame-hanlders are used to assign the coordinates to each interaction object, you will need to change the frame to make the bonds appear.

For some reasons not identified yet, the coordinates updates can break leabing the objects at their last state. To repair that you just need to select your Molecular Nodes object to make it active and then just click the XXX button and that's it !

## Customization

For now customization is limited if you don't want to modify the code directly. You will only be able to modify the shader used to represent the interactions.
