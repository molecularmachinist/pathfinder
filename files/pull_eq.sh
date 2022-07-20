#!/bin/bash
#SBATCH --output=pull_eq_TM.txt
#SBATCH --time=16:00:00
#SBATCH --job-name=pull_eq_TM
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=128
#SBATCH --mem=20G
#SBATCH --account=project_2006125
#SBATCH --partition=medium

#module load gromacs

#gmx_mpi grompp -f pull_eq.mdp -o pull_eq_TM.tpr -c pull170_1.8nm.gro -r pull170_1.8nm.gro -p topol.top -n index.ndx -maxwarn 1
srun gmx_mpi mdrun -v -deffnm pull_eq_TM -px pull_eq_TMx.xvg -pf pull_eq_TMf.xvg 
