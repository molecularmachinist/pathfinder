#!/usr/bin/env python3

import subprocess
import string
import config as cfg

global init
init = cfg.domains[0]["start"]


def bash_command(cmd):
    subprocess.Popen(cmd, shell=True, executable='/bin/bash', stdin=None, stdout=None, stderr=None)

def run_pull(iter: int, K: int, domain: string, sign: int):
    file_name = 'pull_' + str(domain) + str(iter) + '_' + str(K)
    mdp_file = 'pull_' + str(domain) + '.mdp'
    batch = 'sbatch.sh'

    lines = open(mdp_file, 'r').readlines()
    lines[-1] = "\npull_coord1_k = " + str(K) 
    global init
    init = init + 1.5*sign
    lines[-2] = "pull_coord1_init = " + str(init)
    open(mdp_file, 'w').writelines(lines)

    bash_command("gmx_mpi grompp -f pull_{}.mdp -o pull_{}.tpr -c {} -r {} -p topol.top -n {} -maxwarn 1".format(domain, file_name, cfg.gro, cfg.gro, cfg.ndx))
    write_sbatch(file_name, batch)
    bash_command("sbatch {}".format(batch))
    print("Running {} with K = {}".format(file_name, K))
    return

def write_sbatch(file_name: string, sbatch: string):
    # remove last line from sbatch.sh
    command = 'srun gmx_mpi mdrun -v -deffnm {} -pf {}f.xvg -px {}x.xvg'.format(file_name, file_name, file_name)
    # delete last line in sbatch.sh
    with open(sbatch, 'r') as f:
        lines = f.readlines()
    with open(sbatch, 'w') as f:
        for line in lines[:-1]:
            f.write(line)
    # add command into the end of sbatch.sh
    with open(sbatch, 'a') as f:
        f.write(command)
    return



## For testing
iter = 1
K = 50
domain = 'TM'
sign = 1
# move sbatch.sh, config.py and run_pull.py to mahti

run_pull(iter, K, domain, sign)