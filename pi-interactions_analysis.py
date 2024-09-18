import csv

import MDAnalysis as mda
import numpy as np

# Define paths to topology and trajectory files
topology = "/home/mabagar/MDAnalysis_data/adk_equilibrium/adk4AKE.psf"
trajectory = (
    "/home/mabagar/MDAnalysis_data/adk_equilibrium/1ake_007-nowater-core-dt240ps.dcd"
)

# Load your universe (MD trajectory and topology)
u = mda.Universe(topology, trajectory)

# Select aromatic ring atoms for PHE, TYR, and TRP
phe_ring_atoms = u.select_atoms("resname PHE and name CG CD1 CD2 CE1 CE2 CZ")
tyr_ring_atoms = u.select_atoms("resname TYR and name CG CD1 CD2 CE1 CE2 CZ")
trp_ring_atoms = u.select_atoms(
    "resname TRP and name CG CD1 CD2 NE1 CE2 CE3 CZ2 CZ3 CH2"
)


# Define function to calculate centroid of a set of atoms
def calculate_centroid(atomgroup):
    return atomgroup.positions.mean(axis=0)


# Define function to calculate the normal vector of the ring plane
def calculate_normal(atomgroup):
    positions = atomgroup.positions
    centroid = calculate_centroid(atomgroup)
    centered_positions = positions - centroid

    # Perform SVD to find the normal to the ring plane
    _, _, v = np.linalg.svd(centered_positions)

    # The normal vector is the last column of v
    normal = v[-1]
    return normal


# Define function to calculate the angle between two normal vectors
def angle_between_vectors(v1, v2):
    cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    angle = np.arccos(np.clip(cos_theta, -1.0, 1.0)) * 180 / np.pi  # Convert to degrees
    return angle


# Define function to detect and classify pi-pi interactions
def detect_pi_pi_interactions(
    ring1, ring2, distance_threshold=7.0, angle_threshold=30.0
):
    centroid1 = calculate_centroid(ring1)
    centroid2 = calculate_centroid(ring2)
    normal1 = calculate_normal(ring1)
    normal2 = calculate_normal(ring2)

    # Calculate distance between centroids
    centroid_distance = np.linalg.norm(centroid1 - centroid2)

    # Calculate angle between normal vectors
    angle = angle_between_vectors(normal1, normal2)

    # Classify the interaction
    if centroid_distance < distance_threshold:
        if angle < angle_threshold:
            return "Parallel stacking"
        elif 60 < angle < 120:
            return "T-shaped stacking"
        else:
            return "Tilted stacking"
    return None


# Open a CSV file to write the results
with open("pi_pi_interactions.csv", "w", newline="") as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(["Frame", "Residue1", "Residue2", "Interaction"])

    # Iterate through trajectory frames to detect interactions
    for ts in u.trajectory:
        # Select atoms for the current frame
        phe_ring_atoms_frame = u.select_atoms(
            "resname PHE and name CG CD1 CD2 CE1 CE2 CZ"
        )
        tyr_ring_atoms_frame = u.select_atoms(
            "resname TYR and name CG CD1 CD2 CE1 CE2 CZ"
        )
        trp_ring_atoms_frame = u.select_atoms(
            "resname TRP and name CG CD1 CD2 NE1 CE2 CE3 CZ2 CZ3 CH2"
        )

        # Compare ring atoms for π-π interactions
        interaction_phe_tyr = detect_pi_pi_interactions(
            phe_ring_atoms_frame, tyr_ring_atoms_frame
        )
        if interaction_phe_tyr:
            csvwriter.writerow(
                [
                    ts.frame,
                    phe_ring_atoms_frame.resids[0],
                    tyr_ring_atoms_frame.resids[0],
                    interaction_phe_tyr,
                ]
            )

        interaction_phe_trp = detect_pi_pi_interactions(
            phe_ring_atoms_frame, trp_ring_atoms_frame
        )
        if interaction_phe_trp:
            csvwriter.writerow(
                [
                    ts.frame,
                    phe_ring_atoms_frame.resids[0],
                    trp_ring_atoms_frame.resids[0],
                    interaction_phe_trp,
                ]
            )

        interaction_tyr_trp = detect_pi_pi_interactions(
            tyr_ring_atoms_frame, trp_ring_atoms_frame
        )
        if interaction_tyr_trp:
            csvwriter.writerow(
                [
                    ts.frame,
                    tyr_ring_atoms_frame.resids[0],
                    trp_ring_atoms_frame.resids[0],
                    interaction_tyr_trp,
                ]
            )
