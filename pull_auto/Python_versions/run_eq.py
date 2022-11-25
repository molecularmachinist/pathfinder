#!/usr/bin/env python3

import numpy as np
import subprocess
import string
from analyze import *
from write_batch import write_batch as wb
import config as cfg
import time

def bash_command(cmd):
    subprocess.Popen(cmd, shell=True, executable='/bin/bash')

#Function for running equilibrations
#Equilibrations require 2 coordinates, one flat bottom and one flat bottom high
#Function needs to insert a range (+-0.25nm) into pull coord init parameters
def run_eq(domain: string, iter: int):
    file_name = 'pull_eq_' + str(domain) + str(iter)
    mdp_file = 'pull_eq.mdp'

    #delete last 2 lines of mdp file
    lines = open(mdp_file, 'r').readlines()
    del lines[-2:]

    # get init from config.py
    global init
    current_coord = init
    range_high = current_coord + 0.25
    range_low = current_coord - 0.25

    #insert new lines into mdp file
    lines.append("pull_coord1_init = " + str(range_high))
    lines.append("\npull_coord2_init = " + str(range_low))
    open(mdp_file, 'w').writelines(lines)

    bash_command("gmx_mpi grompp -f pull_eq_{}.mdp -o pull_eq_{}.tpr -c {} -r {} -p topol.top -n {} -maxwarn 1".format(domain, file_name, cfg.gro, cfg.gro, cfg.ndx))
    wb.write_batch(file_name)
    bash_command("sbatch {}".format(file_name))
    print("Equilibration {} submitted".format(file_name))

    ##waiting

    command="gmx_mpi rms -s {}.tpr -f {}.xtc -o {}_rmsd.xvg -tu ns".format(file_name, file_name, file_name)
    subprocess.run([command], input="4 4", text=True, shell=True, executable='/bin/bash')

    rmsd_xvg_file = file_name + '_rmsd.xvg'
    # from analyze.py use function analyze
    result=analyze(rmsd_xvg_file, domain)
    print("Result: ", result)
    if result == 0:
        print("Running equilibration again with longer wall time")
        wb.wall_time()
        run_eq(domain, iter)
    else:
        print("Equilibration was successful")


## Testing

# First see if mdp file modification works
domain_dict=cfg.domains[0]
global init
init = domain_dict['start']
#works

# next rmsd file 
# needs pull_eq_TK2.tpr and pull_eq_TK2.xtc
# works

# next analyze

run_eq('TK', 2)