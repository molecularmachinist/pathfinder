#!/bin/bash
#SBATCH --output=pull170.txt
#SBATCH --time=16:00:00
#SBATCH --job-name=pull170
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=128
#SBATCH --mem=20G
#SBATCH --account=project_2006125
#SBATCH --partition=medium


#srun gmx_mpi grompp -f pull.mdp -c pull_eq_TK.gro -p topol.top -r pull_eq_TK.gro -n index.ndx -o pull170.tpr -maxwarn 1
srun gmx_mpi mdrun -v -deffnm pull170 -pf pull170f.xvg -px pull170x.xvg -dlb yes -tunepme yes
