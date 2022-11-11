#!/usr/bin/env python3
"""
User modifies
"""

############# Remote Options #############
# remote directory
remote_dir = "/scratch/project_2006125/vanilja/pathfinder"
# remote name
remote_name = "mahti"


############# Input Files #############
ndx = "index.ndx"
topol = "topol.top"
mdp = "pull_TM.mdp"
gro = "step5_input.gro"


############# Domain Info #############
num_of_domains = 1

TM = {
    "name": "TM",
    "direction": "pull",
    "start": 9.6,
    "target": 8.6,
    "K_max": 50,
}

domains=[TM]
