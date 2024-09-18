import warnings

import MDAnalysis as mda
import numpy as np
from MDAnalysis.analysis.hydrogenbonds.hbond_analysis import HydrogenBondAnalysis as HBA

# Suppress specific deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="MDAnalysis")

topology_file = "/home/mabagar/MDAnalysis_data/adk_equilibrium/adk4AKE.psf"
trajectory_file = (
    "/home/mabagar/MDAnalysis_data/adk_equilibrium/1ake_007-nowater-core-dt240ps.dcd"
)

u = mda.Universe(topology_file, trajectory_file)

hbonds = HBA(universe=u)
hbonds.run(start=0, stop=len(u.trajectory))  # Ensure the analysis is run

results = hbonds.results.hbonds

# Save the results to a CSV file
np.savetxt(
    "hbonds_results.csv",
    results,
    fmt="%10.5f",
    delimiter=",",
    header="Frame,Donor,Hydrogen,Acceptor,Distance,Angle",
)
