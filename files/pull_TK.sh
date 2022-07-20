#!/bin/bash
#SBATCH --output=pull_TK.txt
#SBATCH --time=24:00:00
#SBATCH --job-name=pullTK
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=128
#SBATCH --mem=20G
#SBATCH --account=project_2006125
#SBATCH --partition=medium


#srun gmx_mpi grompp -f pull_TK.mdp -c step7.gro -p topol.top -r step7.gro -n index_TK.ndx -o pull_TK.tpr -maxwarn 1
srun gmx_mpi mdrun -v -deffnm pull_TK -pf pull_TKf.xvg -px pull_TKx.xvg

