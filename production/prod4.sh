#!/bin/bash 
#SBATCH --output=prod_4.txt
#SBATCH --time=00:30:00
#SBATCH --job-name=prod4
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=128
#SBATCH --mem=24G
#SBATCH --account=project_2006125
#SBATCH --partition=medium

module load gromacs

istep=step7_4
pstep=step7_3
rest_prefix=step5_input
prod_prefix=step7_production

srun gmx_mpi grompp -f ${prod_prefix}.mdp -o ${istep}.tpr -c ${pstep}.gro -t ${pstep}.cpt -p topol.top -n index.ndx
srun gmx_mpi mdrun -v -deffnm ${istep}