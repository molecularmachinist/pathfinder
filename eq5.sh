#!/bin/bash 
#SBATCH --output=eq_5.txt
#SBATCH --time=00:40:00
#SBATCH --job-name=eq5
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=128
#SBATCH --mem=24G
#SBATCH --account=project_2006125
#SBATCH --partition=medium

module load gromacs

istep=step6.5_equilibration
pstep=step6.4_equilibration
rest_prefix=step5_input

srun gmx_mpi grompp -f ${istep}.mdp -o ${istep}.tpr -c ${pstep}.gro -r ${rest_prefix}.gro -p topol.top -n index.ndx
srun gmx_mpi mdrun -v -deffnm ${istep} -dlb yes
