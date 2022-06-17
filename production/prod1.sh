#!/bin/bash 
#SBATCH --output=prod_1.txt
#SBATCH --time=00:30:00
#SBATCH --job-name=prod1
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=64
#SBATCH --mem=20G
#SBATCH --account=project_2006125
#SBATCH --partition=medium

module load gromacs

istep=step7_1
pstep=step6.6_equilibration
rest_prefix=step5_input
prod_prefix=step7_production

srun gmx_mpi grompp -f ${prod_prefix}.mdp -o ${istep}.tpr -c ${pstep}.gro -p topol.top -n index.ndx
srun gmx_mpi mdrun -v -deffnm ${istep}
