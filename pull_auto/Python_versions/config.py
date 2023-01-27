#!/usr/bin/env python3
"""
User modifies
"""

############# Remote Options #############
# remote directory
remote_dir = "/scratch/project_2006125/vanilja/pathfinder"
# remote name
remote_name = "mahti"
# run multiple copies of simulations?
run_multiple = False

############# Input Files #############
ndx = "index.ndx"
topol = "topol.top"
mdp = "pull_TK.mdp"
gro = "step7.gro"
maxwarn = 1


############# Domain Info #############
num_of_domains = 1

TM = {
    "name": "TM",
    "direction": "pull",
    "start": 9.6,
    "target": 8.6,
    "K_max": 50,
}

TK = {
    "name": "TK",
    "direction": "pull",
    "start": 4.3,
    "target": 5.3,
    "K_max": 50,
}

domains=[TK]


