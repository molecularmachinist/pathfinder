#!/bin/bash
#SBATCH --output=eq_1.txt
#SBATCH --time=00:20:00
#SBATCH --job-name=eq1
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=128
#SBATCH --mem=24G
##SBATCH --cpus-per-task=2
#SBATCH --account=project_2006125
#SBATCH --partition=medium

module load gromacs

istep=step6.1_equilibration
pstep=step6.0_minimization
rest_prefix=step5_input

srun gmx_mpi grompp -f ${istep}.mdp -o ${istep}.tpr -c ${pstep}.gro -r ${rest_prefix}.gro -p topol.top -n index.ndx 
srun gmx_mpi mdrun -v -deffnm ${istep} -dlb yes
