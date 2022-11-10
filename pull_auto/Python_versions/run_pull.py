#!/usr/bin/env python3

import subprocess
import string
import config as cfg
import write_batch as wb

init = cfg.start

def bash_command(cmd):
    subprocess.Popen(cmd, shell=True, executable='/bin/bash')

def run_pull(iter: int, K: int, domain: string, sign: int):
    file_name = 'pull_' + str(domain) + str(iter) + '_' + str(K)
    mdp_file = 'pull_' + str(domain) + '.mdp'

    lines = open(mdp_file, 'r').readlines()
    lines[-1] = "pull_coord1_k = " + str(K) 
    init = init + 1.5*sign
    lines[-2] = "pull_coord1_init = " + str(init)
    open(mdp_file, 'w').writelines(lines)

    bash_command("gmx_mpi grompp -f pull_{}.mdp -o pull_{}.tpr -c {} -r {} -p topol.top -n {} -maxwarn 1".format(domain, file_name, cfg.gro, cfg.gro, cfg.ndx))
    wb.write_batch(file_name)
    bash_command("sbatch {}.sh".format(file_name))