#!/usr/bin/env python3

import numpy as np
import subprocess
import string
from analyze import *

def bash_command(cmd):
    subprocess.Popen(cmd, shell=True, executable='/bin/bash')

#Function for running equilibrations
#Equilibrations require 2 coordinates, one flat bottom and one flat bottom high
#Function needs to insert a range (+-0.25nm) into pull coord init parameters
def run_eq(domain: string, iter: int):
    file_name = 'pull_eq_' + str(domain) + str(iter)
    mdp_file = 'pull_eq' + str(domain) + '.mdp'

    #delete last 2 lines of mdp file
    lines = open(mdp_file, 'r').readlines()
    del lines[-2:]

    current_coord = init
    range_high = current_coord + 0.25
    range_low = current_coord - 0.25

    #insert new lines into mdp file
    lines.append("pull_coord1_init = " + str(range_high) + ")")
    lines.append("pull_coord2_init = " + str(range_low) + ")")
    open(mdp_file, 'w').writelines(lines)

    bash_command("gmx_mpi grompp -f pull_eq_{}.mdp -o pull_eq_{}.tpr -c {} -r {} -p topol.top -n {} -maxwarn 1".format(domain, file_name, cfg.gro, cfg.gro, cfg.ndx))
    # write_batch_file(file_name)
    bash_command("sbatch {}.sh".format(file_name))
    print("Equilibration {} submitted".format(file_name))

    ##waiting

    bash_command("gmx_mpi rms -s {}.tpr -f {}.trr -o {}_rmsd.xvg -tu ns".format(file_name, file_name, file_name))
    bash_command("backbone backbone")

    rmsd_xvg_file = file_name + '_rmsd.xvg'
    # from analyze.py use function analyze
    result=analyze(rmsd_xvg_file, domain)
    print("Result: ", result)
    if result == 0:
        print("Running equilibration again with longer wall time")
        ## increase wall time (write batch???)
        run_eq(domain, iter)
    else:
        print("Equilibration was successful")


