#!/bin/bash
#SBATCH --output=step7.txt
#SBATCH --time=26:00:00
#SBATCH --job-name=step7
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=64
#SBATCH --mem=12G
#SBATCH --account=project_2006125
#SBATCH --partition=medium

module load gromacs


srun gmx_mpi grompp -f step7_production.mdp -o step7.tpr -c step6.6_equilibration.gro -p topol.top -n index.ndx -maxwarn 1
srun gmx_mpi mdrun -v -deffnm step7
