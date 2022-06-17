#!/bin/bash 
#SBATCH --output=eq_3.txt
#SBATCH --time=00:20:00
#SBATCH --job-name=eq3
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=128
#SBATCH --mem=24G
#SBATCH --account=project_2006125
#SBATCH --partition=medium

module load gromacs

istep=step6.3_equilibration
pstep=step6.2_equilibration
rest_prefix=step5_input

srun gmx_mpi grompp -f ${istep}.mdp -o ${istep}.tpr -c ${pstep}.gro -r ${rest_prefix}.gro -p topol.top -n index.ndx
srun gmx_mpi mdrun -v -deffnm ${istep} -dlb yes
